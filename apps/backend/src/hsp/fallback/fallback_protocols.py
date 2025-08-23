import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import os # Added this import

logger = logging.getLogger(__name__)

class ProtocolStatus(Enum):
    """协议状态枚举"""
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"

class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class FallbackMessage:
    """备用协议消息格式"""
    id: str
    sender_id: str
    recipient_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: float
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    ttl: Optional[float] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['priority'] = self.priority.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FallbackMessage':
        """从字典创建"""
        if 'priority' in data:
            data['priority'] = MessagePriority(data['priority'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.ttl > self.ttl

class BaseFallbackProtocol(ABC):
    """备用协议基类"""
    
    def __init__(self, protocol_name: str):
        self.protocol_name = protocol_name
        self.status = ProtocolStatus.DISABLED
        self.message_handlers: Dict[str, List[Callable]] = {}
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'last_activity': None
        }
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化协议"""
        pass
    
    @abstractmethod
    async def send_message(self, message: FallbackMessage) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    async def start_listening(self):
        """开始监听消息"""
        pass
    
    @abstractmethod
    async def stop_listening(self):
        """停止监听消息"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    async def handle_message(self, message: FallbackMessage):
        """处理接收到的消息"""
        try:
            # 检查消息是否过期
            if message.is_expired():
                logger.warning(f"丢弃过期消息: {message.id}")
                return
            
            # 更新统计
            self.stats['messages_received'] += 1
            self.stats['last_activity'] = time.time()
            
            # 调用处理器
            handlers = self.message_handlers.get(message.message_type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(message)
                    else:
                        handler(message)
                except Exception as e:
                    logger.error(f"消息处理器错误: {e}")
                    self.stats['errors'] += 1
        
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            self.stats['errors'] += 1

class InMemoryProtocol(BaseFallbackProtocol):
    """内存协议 - 最基础的备用协议"""
    
    def __init__(self):
        super().__init__("in_memory")
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """初始化内存协议"""
        try:
            self.status = ProtocolStatus.ACTIVE
            logger.info("内存协议初始化成功")
            return True
        except Exception as e:
            logger.error(f"内存协议初始化失败: {e}")
            self.status = ProtocolStatus.FAILED
            return False
    
    async def send_message(self, message: FallbackMessage) -> bool:
        """发送消息到内存队列"""
        try:
            await self.message_queue.put(message)
            self.stats['messages_sent'] += 1
            self.stats['last_activity'] = time.time()
            logger.debug(f"消息已发送到内存队列: {message.id}")
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.stats['errors'] += 1
            return False
    
    async def start_listening(self):
        """开始监听消息"""
        if self.running:
            return
        
        self.running = True
        self.listener_task = asyncio.create_task(self._message_listener())
        logger.info("内存协议开始监听")
    
    async def stop_listening(self):
        """停止监听消息"""
        self.running = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("内存协议停止监听")
    
    async def _message_listener(self):
        """消息监听器"""
        while self.running:
            try:
                # 等待消息，设置超时避免无限阻塞
                message = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                await self.handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"消息监听器错误: {e}")
                await asyncio.sleep(1)
    
    async def health_check(self) -> bool:
        """健康检查"""
        return self.status == ProtocolStatus.ACTIVE and self.running

class FileBasedProtocol(BaseFallbackProtocol):
    """基于文件的协议 - 用于跨进程通讯"""
    
    def __init__(self, base_path: str = "data/fallback_comm"):
        super().__init__("file_based")
        self.base_path = base_path
        self.inbox_path = f"{base_path}/inbox"
        self.outbox_path = f"{base_path}/outbox"
        self.running = False
        self.listener_task: Optional[asyncio.Task] = None
        self.node_id = str(uuid.uuid4())[:8]
    
    async def initialize(self) -> bool:
        """初始化文件协议"""
        try:
            import os
            os.makedirs(self.inbox_path, exist_ok=True)
            os.makedirs(self.outbox_path, exist_ok=True)
            
            self.status = ProtocolStatus.ACTIVE
            logger.info(f"文件协议初始化成功，节点ID: {self.node_id}")
            return True
        except Exception as e:
            logger.error(f"文件协议初始化失败: {e}")
            self.status = ProtocolStatus.FAILED
            return False
    
    async def send_message(self, message: FallbackMessage) -> bool:
        """发送消息到文件"""
        try:
            import os
            filename = f"{message.id}_{self.node_id}.json"
            filepath = os.path.join(self.outbox_path, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(message.to_dict(), f, ensure_ascii=False, indent=2)
            
            self.stats['messages_sent'] += 1
            self.stats['last_activity'] = time.time()
            logger.debug(f"消息已写入文件: {filepath}")
            return True
        except Exception as e:
            logger.error(f"写入消息文件失败: {e}")
            self.stats['errors'] += 1
            return False
    
    async def start_listening(self):
        """开始监听文件变化"""
        if self.running:
            return
        
        self.running = True
        self.listener_task = asyncio.create_task(self._file_listener())
        logger.info("文件协议开始监听")
    
    async def stop_listening(self):
        """停止监听文件"""
        self.running = False
        if self.listener_task:
            self.listener_task.cancel()
            try:
                await self.listener_task
            except asyncio.CancelledError:
                pass
        logger.info("文件协议停止监听")
    
    async def _file_listener(self):
        """文件监听器"""
        import os
        processed_files = set()
        
        while self.running:
            try:
                # 扫描收件箱
                if os.path.exists(self.inbox_path):
                    for filename in os.listdir(self.inbox_path):
                        if filename.endswith('.json') and filename not in processed_files:
                            filepath = os.path.join(self.inbox_path, filename)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                
                                message = FallbackMessage.from_dict(data)
                                await self.handle_message(message)
                                
                                # 标记为已处理
                                processed_files.add(filename)
                                
                                # 删除已处理的文件
                                os.remove(filepath)
                                
                            except Exception as e:
                                logger.error(f"处理文件消息失败 {filepath}: {e}")
                
                await asyncio.sleep(0.5)  # 轮询间隔
                
            except Exception as e:
                logger.error(f"文件监听器错误: {e}")
                await asyncio.sleep(1)
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import os
            return (self.status == ProtocolStatus.ACTIVE and 
                   os.path.exists(self.inbox_path) and 
                   os.path.exists(self.outbox_path))
        except:
            return False

class HTTPProtocol(BaseFallbackProtocol):
    """基于 HTTP 的协议"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        super().__init__("http")
        self.host = host
        self.port = port
        self.server = None
        self.session = None
        self.endpoints: Dict[str, str] = {}  # 其他节点的端点
    
    async def initialize(self) -> bool:
        """初始化 HTTP 协议"""
        try:
            import aiohttp
            from aiohttp import web
            
            # 创建 HTTP 会话
            self.session = aiohttp.ClientSession()
            
            # 创建 Web 应用
            app = web.Application()
            app.router.add_post('/message', self._handle_http_message)
            app.router.add_get('/health', self._handle_health_check)
            
            # 启动服务器
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            self.server = runner
            self.status = ProtocolStatus.ACTIVE
            logger.info(f"HTTP 协议服务器启动: http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            logger.error(f"HTTP 协议初始化失败: {e}")
            self.status = ProtocolStatus.FAILED
            return False
    
    async def send_message(self, message: FallbackMessage) -> bool:
        """通过 HTTP 发送消息"""
        try:
            # 根据接收者ID查找端点
            endpoint = self.endpoints.get(message.recipient_id)
            if not endpoint:
                logger.warning(f"未找到接收者端点: {message.recipient_id}")
                return False
            
            url = f"{endpoint}/message"
            async with self.session.post(url, json=message.to_dict()) as response:
                if response.status == 200:
                    self.stats['messages_sent'] += 1
                    self.stats['last_activity'] = time.time()
                    return True
                else:
                    logger.error(f"HTTP 发送失败: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"HTTP 发送消息失败: {e}")
            self.stats['errors'] += 1
            return False
    
    async def _handle_http_message(self, request):
        """处理 HTTP 消息请求"""
        try:
            from aiohttp import web
            data = await request.json()
            message = FallbackMessage.from_dict(data)
            await self.handle_message(message)
            return web.json_response({"status": "ok"})
        except Exception as e:
            logger.error(f"处理 HTTP 消息失败: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def _handle_health_check(self, request):
        """处理健康检查请求"""
        from aiohttp import web
        return web.json_response({
            "status": self.status.value,
            "stats": self.stats
        })
    
    async def start_listening(self):
        """HTTP 协议自动监听"""
        pass  # HTTP 服务器在初始化时已经开始监听
    
    async def stop_listening(self):
        """停止 HTTP 服务器"""
        if self.server:
            await self.server.cleanup()
        if self.session:
            await self.session.close()
    
    async def health_check(self) -> bool:
        """健康检查"""
        return self.status == ProtocolStatus.ACTIVE and self.server is not None
    
    def add_endpoint(self, node_id: str, endpoint: str):
        """添加其他节点的端点"""
        self.endpoints[node_id] = endpoint

class FallbackProtocolManager:
    """备用协议管理器"""
    
    def __init__(self):
        self.protocols: List[BaseFallbackProtocol] = []
        self.active_protocol: Optional[BaseFallbackProtocol] = None
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self.manager_task: Optional[asyncio.Task] = None
        self.health_check_interval = 30  # 健康检查间隔（秒）
    
    def add_protocol(self, protocol: BaseFallbackProtocol, priority: int = 0):
        """添加协议（按优先级排序）"""
        self.protocols.append((priority, protocol))
        self.protocols.sort(key=lambda x: x[0], reverse=True)  # 高优先级在前
    
    async def initialize(self) -> bool:
        """初始化所有协议"""
        success_count = 0
        
        for priority, protocol in self.protocols:
            try:
                if await protocol.initialize():
                    success_count += 1
                    logger.info(f"协议 {protocol.protocol_name} 初始化成功")
                    
                    # 注册通用消息处理器
                    protocol.register_handler("*", self._handle_protocol_message)
                else:
                    logger.warning(f"协议 {protocol.protocol_name} 初始化失败")
            except Exception as e:
                logger.error(f"协议 {protocol.protocol_name} 初始化异常: {e}")
        
        if success_count > 0:
            await self._select_active_protocol()
            return True
        
        logger.error("所有协议初始化失败")
        return False
    
    async def _select_active_protocol(self):
        """选择活跃协议"""
        for priority, protocol in self.protocols:
            if await protocol.health_check():
                if self.active_protocol != protocol:
                    # 切换协议
                    if self.active_protocol:
                        await self.active_protocol.stop_listening()
                    
                    self.active_protocol = protocol
                    await protocol.start_listening()
                    logger.info(f"切换到协议: {protocol.protocol_name}")
                return
        
        logger.error("没有可用的协议")
        self.active_protocol = None
    
    async def send_message(self, 
                          recipient_id: str,
                          message_type: str,
                          payload: Dict[str, Any],
                          priority: MessagePriority = MessagePriority.NORMAL,
                          correlation_id: Optional[str] = None) -> bool:
        """发送消息"""
        message = FallbackMessage(
            id=str(uuid.uuid4()),
            sender_id="system",  # 可以配置
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            timestamp=time.time(),
            priority=priority,
            correlation_id=correlation_id
        )
        
        return await self.send_fallback_message(message)
    
    async def send_fallback_message(self, message: FallbackMessage) -> bool:
        """发送备用消息"""
        if not self.active_protocol:
            await self._select_active_protocol()
        
        if not self.active_protocol:
            logger.error("没有可用的协议发送消息")
            return False
        
        # 尝试发送消息
        success = await self.active_protocol.send_message(message)
        
        if not success and message.retry_count < message.max_retries:
            # 重试机制
            message.retry_count += 1
            await asyncio.sleep(1)  # 等待1秒后重试
            
            # 尝试切换协议
            await self._select_active_protocol()
            if self.active_protocol:
                success = await self.active_protocol.send_message(message)
        
        return success
    
    async def _handle_protocol_message(self, message: FallbackMessage):
        """处理协议消息"""
        # 将消息放入队列供外部处理
        await self.message_queue.put(message)
    
    async def get_message(self, timeout: Optional[float] = None) -> Optional[FallbackMessage]:
        """获取消息"""
        try:
            if timeout:
                return await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
            else:
                return await self.message_queue.get()
        except asyncio.TimeoutError:
            return None
    
    async def start(self):
        """启动管理器"""
        if self.running:
            return
        
        self.running = True
        self.manager_task = asyncio.create_task(self._health_monitor())
        logger.info("备用协议管理器启动")
    
    async def shutdown(self):
        """停止管理器"""
        self.running = False
        
        if self.manager_task:
            self.manager_task.cancel()
            try:
                await self.manager_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有协议
        for priority, protocol in self.protocols:
            try:
                await protocol.stop_listening()
            except Exception as e:
                logger.error(f"停止协议 {protocol.protocol_name} 失败: {e}")
        
        logger.info("备用协议管理器停止")
    
    async def _health_monitor(self):
        """健康监控"""
        while self.running:
            try:
                await self._select_active_protocol()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"健康监控错误: {e}")
                await asyncio.sleep(5)
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态信息"""
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

# 全局实例
_fallback_manager: Optional[FallbackProtocolManager] = None

def get_fallback_manager() -> FallbackProtocolManager:
    """获取全局备用协议管理器"""
    global _fallback_manager
    if _fallback_manager is None:
        _fallback_manager = FallbackProtocolManager()
    return _fallback_manager

async def initialize_fallback_protocols() -> bool:
    """初始化备用协议"""
    manager = get_fallback_manager()
    
    # Determine port based on testing environment
    http_port = 0 if os.environ.get('TESTING') == 'true' else 8765 # Modified line
    print(f"DEBUG: initialize_fallback_protocols - TESTING env var: {os.environ.get('TESTING')}, HTTP Port: {http_port}") # Added debug print
    
    # 添加协议（按优先级）
    manager.add_protocol(InMemoryProtocol(), priority=1)  # 最低优先级
    manager.add_protocol(FileBasedProtocol(), priority=2)  # 中等优先级
    manager.add_protocol(HTTPProtocol(port=http_port), priority=3)  # 最高优先级 # Modified line
    
    # 初始化并启动
    if await manager.initialize():
        await manager.start()
        logger.info("备用协议系统初始化成功")
        return True
    else:
        logger.error("备用协议系统初始化失败")
        return False