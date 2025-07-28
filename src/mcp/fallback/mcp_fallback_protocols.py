"""
MCP (Model Context Protocol) 備用協議系統
當主MCP協議不可用時提供基礎通訊支持
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

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
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPFallbackMessage':
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
    
    def __init__(self, protocol_name: str):
        self.protocol_name = protocol_name
        self.status = MCPProtocolStatus.DISABLED
        self.command_handlers: Dict[str, List[Callable]] = {}
        self.stats = {
            'commands_sent': 0,
            'commands_received': 0,
            'errors': 0,
            'last_activity': None
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
    
    def register_command_handler(self, command_name: str, handler: Callable):
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
    """MCP內存協議 - 同進程通訊"""
    
    def __init__(self):
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
            logger.debug(f"MCP命令已發送到內存隊列: {message.id}")
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
                message = await asyncio.wait_for(
                    self.command_queue.get(), 
                    timeout=1.0
                )
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
    
    def __init__(self, base_path: str = "data/mcp_fallback_comm"):
        super().__init__("mcp_file")
        self.base_path = base_path
        self.inbox_path = f"{base_path}/inbox"
        self.outbox_path = f"{base_path}/outbox"
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """初始化文件協議"""
        try:
            import os
            os.makedirs(self.inbox_path, exist_ok=True)
            os.makedirs(self.outbox_path, exist_ok=True)
            
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
            import os
            filename = f"{message.id}_{int(time.time())}.json"
            filepath = os.path.join(self.outbox_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)
            
            self.stats['commands_sent'] += 1
            self.stats['last_activity'] = time.time()
            logger.debug(f"MCP命令已寫入文件: {filepath}")
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
                import os
                import glob
                
                pattern = os.path.join(self.inbox_path, "*.json")
                files = glob.glob(pattern)
                
                for filepath in files:
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        message = MCPFallbackMessage.from_dict(data)
                        await self.handle_command(message)
                        
                        # 刪除已處理的文件
                        os.remove(filepath)
                        
                    except Exception as e:
                        logger.error(f"處理MCP文件命令失敗 {filepath}: {e}")
                
                await asyncio.sleep(0.5)  # 輪詢間隔
                
            except Exception as e:
                logger.error(f"MCP文件監聽器錯誤: {e}")
                await asyncio.sleep(1)
    
    async def health_check(self) -> bool:
        """健康檢查"""
        try:
            import os
            return (self.status == MCPProtocolStatus.ACTIVE and 
                   os.path.exists(self.inbox_path) and 
                   os.path.exists(self.outbox_path))
        except:
            return False

class MCPHTTPProtocol(BaseMCPFallbackProtocol):
    """MCP基於HTTP的協議"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8766):
        super().__init__("mcp_http")
        self.host = host
        self.port = port
        self.server = None
        self.session = None
        self.endpoints: Dict[str, str] = {}  # 其他節點的端點
    
    async def initialize(self) -> bool:
        """初始化HTTP協議"""
        try:
            import aiohttp
            from aiohttp import web
            
            # 創建HTTP會話
            self.session = aiohttp.ClientSession()
            
            # 創建Web應用
            app = web.Application()
            app.router.add_post('/mcp/command', self._handle_http_command)
            app.router.add_get('/mcp/health', self._handle_health_check)
            
            # 啟動服務器
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            self.server = runner
            self.status = MCPProtocolStatus.ACTIVE
            logger.info(f"MCP HTTP協議服務器啟動: http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"MCP HTTP協議初始化失敗: {e}")
            self.status = MCPProtocolStatus.FAILED
            return False
    
    async def send_command(self, message: MCPFallbackMessage) -> bool:
        """通過HTTP發送命令"""
        try:
            # 根據接收者ID查找端點
            endpoint = self.endpoints.get(message.recipient_id)
            if not endpoint:
                logger.warning(f"未找到MCP接收者端點: {message.recipient_id}")
                return False
            
            url = f"{endpoint}/mcp/command"
            async with self.session.post(url, json=message.to_dict()) as response:
                if response.status == 200:
                    self.stats['commands_sent'] += 1
                    self.stats['last_activity'] = time.time()
                    return True
                else:
                    logger.error(f"MCP HTTP發送失敗: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"MCP HTTP發送命令失敗: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _handle_http_command(self, request):
        """處理HTTP命令請求"""
        try:
            from aiohttp import web
            data = await request.json()
            message = MCPFallbackMessage.from_dict(data)
            await self.handle_command(message)
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error(f"處理MCP HTTP命令失敗: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def _handle_health_check(self, request):
        """處理健康檢查請求"""
        from aiohttp import web
        return web.json_response({
            "status": self.status.value,
            "protocol": self.protocol_name,
            "stats": self.stats
        })
    
    async def start_listening(self):
        """HTTP協議通過服務器自動監聽"""
        pass
    
    async def stop_listening(self):
        """停止HTTP服務器"""
        if self.server:
            await self.server.cleanup()
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """健康檢查"""
        return self.status == MCPProtocolStatus.ACTIVE

class MCPFallbackManager:
    """MCP備用協議管理器"""
    
    def __init__(self):
        self.protocols: List[tuple[int, BaseMCPFallbackProtocol]] = []  # (priority, protocol)
        self.active_protocol: Optional[BaseMCPFallbackProtocol] = None
        self.command_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.manager_task: Optional[asyncio.Task] = None
        self.health_check_interval = 30
    
    def add_protocol(self, protocol: BaseMCPFallbackProtocol, priority: int):
        """添加協議"""
        self.protocols.append((priority, protocol))
        # 按優先級排序（高優先級在前）
        self.protocols.sort(key=lambda x: x[0], reverse=True)
        logger.info(f"添加MCP協議: {protocol.protocol_name} (優先級: {priority})")
    
    async def initialize(self) -> bool:
        """初始化所有協議"""
        success_count = 0
        for priority, protocol in self.protocols:
            try:
                if await protocol.initialize():
                    await protocol.start_listening()
                    success_count += 1
                    logger.info(f"MCP協議 {protocol.protocol_name} 初始化成功")
                else:
                    logger.warning(f"MCP協議 {protocol.protocol_name} 初始化失敗")
            except Exception as e:
                logger.error(f"初始化MCP協議 {protocol.protocol_name} 時出錯: {e}")
        
        if success_count > 0:
            await self._select_active_protocol()
            return True
        else:
            logger.error("沒有MCP協議初始化成功")
            return False
    
    async def _select_active_protocol(self):
        """選擇活動協議"""
        for priority, protocol in self.protocols:
            if await protocol.health_check():
                if self.active_protocol != protocol:
                    old_protocol = self.active_protocol.protocol_name if self.active_protocol else "None"
                    self.active_protocol = protocol
                    logger.info(f"MCP協議切換: {old_protocol} → {protocol.protocol_name}")
                return
        
        if self.active_protocol:
            logger.warning("所有MCP協議都不可用")
            self.active_protocol = None
    
    def register_command_handler(self, command_name: str, handler: Callable):
        """為所有協議註冊命令處理器"""
        for priority, protocol in self.protocols:
            protocol.register_command_handler(command_name, handler)
    
    async def send_command(self, sender_id: str, recipient_id: str, command_name: str, 
                          parameters: Dict[str, Any], priority: MCPMessagePriority = MCPMessagePriority.NORMAL) -> bool:
        """發送命令"""
        message = MCPFallbackMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient_id,
            command_name=command_name,
            parameters=parameters,
            timestamp=time.time(),
            priority=priority
        )
        
        return await self.send_fallback_command(message)
    
    async def send_fallback_command(self, message: MCPFallbackMessage) -> bool:
        """發送備用命令"""
        if not self.active_protocol:
            await self._select_active_protocol()
        
        if not self.active_protocol:
            logger.error("沒有可用的MCP協議發送命令")
            return False
        
        # 嘗試發送命令
        success = await self.active_protocol.send_command(message)
        
        if not success and message.retry_count < message.max_retries:
            # 重試機制
            message.retry_count += 1
            await asyncio.sleep(1)  # 等待1秒後重試
            
            # 嘗試切換協議
            await self._select_active_protocol()
            if self.active_protocol:
                success = await self.active_protocol.send_command(message)
        
        return success
    
    async def start(self):
        """啟動管理器"""
        if self.running:
            return
        
        self.running = True
        self.manager_task = asyncio.create_task(self._health_monitor())
        logger.info("MCP備用協議管理器啟動")
    
    async def stop(self):
        """停止管理器"""
        self.running = False
        
        if self.manager_task:
            self.manager_task.cancel()
            try:
                await self.manager_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有協議
        for priority, protocol in self.protocols:
            try:
                await protocol.stop_listening()
            except Exception as e:
                logger.error(f"停止MCP協議 {protocol.protocol_name} 失敗: {e}")
        
        logger.info("MCP備用協議管理器停止")
    
    async def _health_monitor(self):
        """健康監控"""
        while self.running:
            try:
                await self._select_active_protocol()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"MCP健康監控錯誤: {e}")
                await asyncio.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """獲取狀態信息"""
        status = {
            "active_protocol": self.active_protocol.protocol_name if self.active_protocol else None,
            "protocols": []
        }
        
        for priority, protocol in self.protocols:
            status["protocols"].append({
                "name": protocol.protocol_name,
                "priority": priority,
                "status": protocol.status.value,
                "stats": protocol.stats
            })
        
        return status

# 全局實例
_mcp_fallback_manager: Optional[MCPFallbackManager] = None

def get_mcp_fallback_manager() -> MCPFallbackManager:
    """獲取全局MCP備用協議管理器"""
    global _mcp_fallback_manager
    if _mcp_fallback_manager is None:
        _mcp_fallback_manager = MCPFallbackManager()
    return _mcp_fallback_manager

async def initialize_mcp_fallback_protocols() -> bool:
    """初始化MCP備用協議"""
    manager = get_mcp_fallback_manager()
    
    # 添加協議（按優先級）
    manager.add_protocol(MCPInMemoryProtocol(), priority=1)  # 最低優先級
    manager.add_protocol(MCPFileProtocol(), priority=2)  # 中等優先級
    manager.add_protocol(MCPHTTPProtocol(), priority=3)  # 最高優先級
    
    # 初始化並啟動
    if await manager.initialize():
        await manager.start()
        logger.info("MCP備用協議系統初始化成功")
        return True
    else:
        logger.error("MCP備用協議系統初始化失敗")
        return False