"""
MCP (Model Context Protocol) 備用協議系統
當主MCP協議不可用時提供基礎通訊支持
"""

import asyncio
import json
import logging
import os
import time
import uuid
import glob
import socket
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPProtocolStatus(Enum):
    """MCP協議狀態枚舉"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"

class MCPMessagePriority(Enum):
    """MCP消息優先級"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MCPFallbackMessage:
    """MCP備用協議消息格式"""
    id: str
    sender_id: str
    recipient_id: str
    command_name: str
    parameters: Dict[str, Any]
    timestamp: float
    priority: MCPMessagePriority = MCPMessagePriority.NORMAL
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    ttl: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """從字典創建"""
        if 'priority' in data:
            data['priority'] = MCPMessagePriority(data['priority'])
        return cls(**data)

    def is_expired(self) -> bool:
        """檢查消息是否過期"""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl

class BaseMCPFallbackProtocol(ABC):
    """MCP備用協議基類"""

    def __init__(self, protocol_name: str) -> None:
        self.protocol_name = protocol_name
        self.status = MCPProtocolStatus.DISABLED
        self.command_handlers: Dict[str, List[Callable[[Dict[str, Any]], Awaitable[None]]]] = {}
        self.stats: Dict[str, Union[int, float]] = {
            'commands_sent': 0,
            'commands_received': 0,
            'errors': 0,
            'last_activity': 0.0
        }

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化協議"""
        pass

    @abstractmethod
    async def send_command(self, message: MCPFallbackMessage) -> bool:
        """發送命令"""
        pass

    @abstractmethod
    async def start_listening(self):
        """開始監聽命令"""
        pass

    @abstractmethod
    async def stop_listening(self):
        """停止監聽命令"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康檢查"""
        pass

    def register_command_handler(self, command_name: str, handler: Callable[[Dict[str, Any]], Awaitable[None]]):
        """註冊命令處理器"""
        if command_name not in self.command_handlers:
            self.command_handlers[command_name] = []
        self.command_handlers[command_name].append(handler)

    async def handle_command(self, message: MCPFallbackMessage):
        """處理接收到的命令"""
        try:
            if message.is_expired():
                logger.warning(f"丟棄過期命令: {message.id}")
                return

            self.stats['commands_received'] += 1
            self.stats['last_activity'] = time.time()

            handlers = self.command_handlers.get(message.command_name, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message.parameters)
                    else:
                        handler(message.parameters)
                except Exception as e:
                    logger.error(f"命令處理器錯誤: {e}")
                    self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"處理命令失敗: {e}")
            self.stats['errors'] += 1

class MCPInMemoryProtocol(BaseMCPFallbackProtocol):
    """
    MCP內存協議 - 同進程通訊
    """

    def __init__(self) -> None:
        super().__init__("mcp_memory")
        self.command_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """初始化內存協議"""
        try:
            self.status = MCPProtocolStatus.ACTIVE
            logger.info("MCP內存協議初始化成功")
            return True
        except Exception as e:
            logger.error(f"MCP內存協議初始化失敗: {e}")
            self.status = MCPProtocolStatus.FAILED
            return False

    async def send_command(self, message: MCPFallbackMessage) -> bool:
        """發送命令到內存隊列"""
        try:
            await self.command_queue.put(message)
            self.stats['commands_sent'] += 1
            self.stats['last_activity'] = time.time()
            return True
        except Exception as e:
            logger.error(f"發送MCP命令失敗: {e}")
            self.stats['errors'] += 1
            return False

    async def start_listening(self):
        """開始監聽命令"""
        if self.running:
            return

        self.running = True
        self.listener_task = asyncio.create_task(self._command_listener())
        logger.info("MCP內存協議開始監聽")

    async def stop_listening(self):
        """停止監聽命令"""
        self.running = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("MCP內存協議停止監聽")

    async def _command_listener(self):
        """命令監聽器"""
        while self.running:
            try:
                message = await asyncio.wait_for(self.command_queue.get(), timeout=1.0)
                await self.handle_command(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"MCP內存協議監聽器錯誤: {e}")
                await asyncio.sleep(1)

    async def health_check(self) -> bool:
        """健康檢查"""
        return self.status == MCPProtocolStatus.ACTIVE

class MCPFileProtocol(BaseMCPFallbackProtocol):
    """MCP文件協議 - 跨進程通訊"""

    def __init__(self, base_path: str = "data/mcp_fallback_comm") -> None:
        super().__init__("mcp_file")
        self.base_path = Path(base_path)
        self.inbox_path = self.base_path / "inbox"
        self.outbox_path = self.base_path / "outbox"
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None

    async def initialize(self) -> bool:
        """初始化文件協議"""
        try:
            self.inbox_path.mkdir(parents=True, exist_ok=True)
            self.outbox_path.mkdir(parents=True, exist_ok=True)
            self.status = MCPProtocolStatus.ACTIVE
            logger.info(f"MCP文件協議初始化成功: {self.base_path}")
            return True
        except Exception as e:
            logger.error(f"MCP文件協議初始化失敗: {e}")
            self.status = MCPProtocolStatus.FAILED
            return False

    async def send_command(self, message: MCPFallbackMessage) -> bool:
        """發送命令到文件"""
        try:
            filename = f"{message.id}_{int(time.time())}.json"
            filepath = self.outbox_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)
                
            self.stats['commands_sent'] += 1
            self.stats['last_activity'] = time.time()
            return True
        except Exception as e:
            logger.error(f"寫入MCP命令文件失敗: {e}")
            self.stats['errors'] += 1
            return False

    async def start_listening(self):
        """開始監聽文件"""
        if self.running:
            return

        self.running = True
        self.listener_task = asyncio.create_task(self._file_listener())
        logger.info("MCP文件協議開始監聽")

    async def stop_listening(self):
        """停止監聽文件"""
        self.running = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("MCP文件協議停止監聽")

    async def _file_listener(self):
        """文件監聽器"""
        while self.running:
            try:
                files = list(self.inbox_path.glob("*.json"))
                for filepath in files:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            message = MCPFallbackMessage.from_dict(data)
                            await self.handle_command(message)
                        filepath.unlink() # 刪除已處理的文件
                    except Exception as e:
                        logger.error(f"處理MCP文件命令失敗 {filepath}: {e}")
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"MCP文件監聽器錯誤: {e}")
                await asyncio.sleep(1)

    async def health_check(self) -> bool:
        """健康檢查"""
        return self.status == MCPProtocolStatus.ACTIVE and self.inbox_path.exists()

class MCPFallbackManager:
    """MCP備用協議管理器"""

    def __init__(self) -> None:
        self.protocols: List[tuple[int, BaseMCPFallbackProtocol]] = []
        self.active_protocol: Optional[BaseMCPFallbackProtocol] = None
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None

    def add_protocol(self, protocol: BaseMCPFallbackProtocol, priority: int):
        """添加協議"""
        self.protocols.append((priority, protocol))
        self.protocols.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"添加MCP協議: {protocol.protocol_name} (優先級: {priority})")

    async def initialize(self) -> bool:
        """初始化所有協議"""
        success = False
        for _, protocol in self.protocols:
            if await protocol.initialize():
                await protocol.start_listening()
                success = True
        
        if success:
            await self._select_active_protocol()
            self.running = True
            self.monitor_task = asyncio.create_task(self._health_monitor())
            return True
        return False

    async def _select_active_protocol(self):
        """選擇活動協議"""
        for _, protocol in self.protocols:
            if await protocol.health_check():
                if self.active_protocol != protocol:
                    prev = self.active_protocol.protocol_name if self.active_protocol else "None"
                    self.active_protocol = protocol
                    logger.info(f"MCP協議切換: {prev} -> {protocol.protocol_name}")
                return
        self.active_protocol = None

    async def _health_monitor(self):
        """健康狀態監控"""
        while self.running:
            await self._select_active_protocol()
            await asyncio.sleep(30)

    async def send_command(self, message: MCPFallbackMessage) -> bool:
        """通過活動協議發送命令"""
        if self.active_protocol:
            return await self.active_protocol.send_command(message)
        logger.error("沒有活動的MCP協議可用於發送命令")
        return False

    async def stop(self):
        """停止管理器"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
        for _, protocol in self.protocols:
            await protocol.stop_listening()

# 全局MCP備用協議管理器實例
_mcp_fallback_manager: Optional[MCPFallbackManager] = None

def get_mcp_fallback_manager() -> MCPFallbackManager:
    """獲取全局MCP備用協議管理器實例"""
    global _mcp_fallback_manager
    if _mcp_fallback_manager is None:
        _mcp_fallback_manager = MCPFallbackManager()
    return _mcp_fallback_manager

async def initialize_mcp_fallback_protocols() -> bool:
    """初始化MCP備用協議"""
    manager = get_mcp_fallback_manager()
    
    # 默認添加三種常用協議
    manager.add_protocol(MCPInMemoryProtocol(), priority=1)
    manager.add_protocol(MCPFileProtocol(), priority=2)
    # HTTP 協議暫時省略，因為需要 aiohttp 依賴
    
    return await manager.initialize()
