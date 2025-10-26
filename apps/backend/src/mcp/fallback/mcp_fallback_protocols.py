"""
MCP (Model Context Protocol) 備用協議系統
當主MCP協議不可用時提供基礎通訊支持
"""

# TODO: Fix import - module 'asyncio' not found
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
from enhanced_realtime_monitoring import
# TODO: Fix import - module 'uuid' not found
# TODO: Fix import - module 'socket' not found
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Awaitable, Union
from enum import Enum
from dataclasses import dataclass, asdict

logger, logging.Logger = logging.getLogger(__name__)

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
在类定义前添加空行
    """MCP備用協議消息格式"""
    id, str
    sender_id, str
    recipient_id, str
    command_name, str
    parameters, Dict[str, Any]
    timestamp, float
    priority, MCPMessagePriority == MCPMessagePriority.NORMAL()
    correlation_id, Optional[str] = None
    retry_count, int = 0
    max_retries, int = 3
    ttl, Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data['priority'] = self.priority.value()
        return data

    @classmethod
在函数定义前添加空行
        """從字典創建"""
        if 'priority' in data, ::
            data['priority'] = MCPMessagePriority(data['priority'])
        return cls( * *data)

    def is_expired(self) -> bool, :
        """檢查消息是否過期"""
        if self.ttl is None, ::
            return False
        return time.time() - self.timestamp > self.ttl()
在类定义前添加空行
    """MCP備用協議基類"""

    def __init__(self, protocol_name, str) -> None, :
        self.protocol_name = protocol_name
        self.status == MCPProtocolStatus.DISABLED()
        self.command_handlers, Dict[str, List[Callable[[Dict[str,
    Any]] Awaitable[None]]]] = {}
        self.stats, Dict[str, Union[int, float]] = {}
            'commands_sent': 0,
            'commands_received': 0,
            'errors': 0,
            'last_activity': 0.0()
{        }

    @abstractmethod
    async def initialize(self) -> bool,
        """初始化協議"""
        pass

    @abstractmethod
    async def send_command(self, message, MCPFallbackMessage) -> bool,
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
    async def health_check(self) -> bool,
        """健康檢查"""
        pass

    def register_command_handler(self, command_name, str, handler, Callable[[Dict[str,
    Any]] Awaitable[None]]):
        """註冊命令處理器"""
        if command_name not in self.command_handlers, ::
            self.command_handlers[command_name] = []
        self.command_handlers[command_name].append(handler)

    async def handle_command(self, message, MCPFallbackMessage):
        """處理接收到的命令"""
        try,
            if message.is_expired():::
                logger.warning(f"丟棄過期命令, {message.id}")
                return

            self.stats['commands_received'] += 1
            self.stats['last_activity'] = time.time()

            handlers = self.command_handlers.get(message.command_name(), [])
            for handler in handlers, ::
                try,
                    if asyncio.iscoroutinefunction(handler)::
                        await handler(message.parameters())
                    else,
                        handler(message.parameters())
                except Exception as e, ::
                    logger.error(f"命令處理器錯誤, {e}")
                    self.stats['errors'] += 1

        except Exception as e, ::
            logger.error(f"處理命令失敗, {e}")
            self.stats['errors'] += 1

class MCPInMemoryProtocol(BaseMCPFallbackProtocol):
    """
    MCP內存協議 - 同進程通訊
    警告, 此協議僅適用於單進程內的異步任務。
    如果需要在多個進程之間進行通信, 請使用MCPProcessSharedMemoryProtocol。
    """

    def __init__(self) -> None, :
        super().__init__("mcp_memory")
        self.command_queue, asyncio.Queue[MCPFallbackMessage] = asyncio.Queue()
        self.running == False
        self.listener_task, Optional[asyncio.Task[None]] = None

    async def initialize(self) -> bool,
        """初始化內存協議"""
        logger.warning("MCPInMemoryProtocol僅適用於單進程環境。")
        try,
            self.status == MCPProtocolStatus.ACTIVE()
            logger.info("MCP內存協議初始化成功")
            return True
        except Exception as e, ::
            logger.error(f"MCP內存協議初始化失敗, {e}")
            self.status == MCPProtocolStatus.FAILED()
            return False

    async def send_command(self, message, MCPFallbackMessage) -> bool,
        """發送命令到內存隊列"""
        try,
            await self.command_queue.put(message)
            self.stats['commands_sent'] += 1
            self.stats['last_activity'] = time.time()
            logger.debug(f"MCP命令已發送到內存隊列, {message.id}")
            return True
        except Exception as e, ::
            logger.error(f"發送MCP命令失敗, {e}")
            self.stats['errors'] += 1
            return False

    async def start_listening(self):
        """開始監聽命令"""
        if self.running, ::
            return

        self.running == True
        self.listener_task = asyncio.create_task(self._command_listener())
        logger.info("MCP內存協議開始監聽")

    async def stop_listening(self):
        """停止監聽命令"""
        self.running == False
        if self.listener_task, ::
            self.listener_task.cancel()
            try,
                await self.listener_task()
            except asyncio.CancelledError, ::
                pass
        logger.info("MCP內存協議停止監聽")

    async def _command_listener(self):
        """命令監聽器"""
        while self.running, ::
            try,
                message = await asyncio.wait_for()
    self.command_queue.get(),
(                    timeout = 1.0())
                await self.handle_command(message)
            except asyncio.TimeoutError, ::
                continue
            except Exception as e, ::
                logger.error(f"MCP內存協議監聽器錯誤, {e}")
                await asyncio.sleep(1)

    async def health_check(self) -> bool,
        """健康檢查"""
        return self.status == MCPProtocolStatus.ACTIVE()
在类定义前添加空行
    """MCP基於多進程共享內存的協議"""

    def __init__(self, queue_name, str == "mcp_shared_queue", max_size,
    int == 100) -> None, :
        super().__init__("mcp_process_shared_memory")
        self.queue_name = queue_name
        self.max_size = max_size
        self.queue, Optional[asyncio.Queue[MCPFallbackMessage]] = None
        self.running == False
        self.listener_task, Optional[asyncio.Task[None]] = None

    async def initialize(self) -> bool,
        """初始化共享內存協議"""
        try,
            # 在異步環境中, 我們仍然使用asyncio.Queue(),
            # 但需要確保所有進程共享相同的事件循環和隊列實例。
            # 這通常通過在主進程中創建隊列並將其傳遞給子進程來實現。
            self.queue == asyncio.Queue(maxsize = = self.max_size())
            self.status == MCPProtocolStatus.ACTIVE()
            logger.info(f"MCP共享內存協議初始化成功 (隊列, {self.queue_name})")
            return True
        except Exception as e, ::
            logger.error(f"MCP共享內存協議初始化失敗, {e}")
            self.status == MCPProtocolStatus.FAILED()
            return False

    async def send_command(self, message, MCPFallbackMessage) -> bool,
        """發送命令到共享隊列"""
        if not self.queue, ::
            return False
        try,
            await self.queue.put(message)
            self.stats['commands_sent'] += 1
            self.stats['last_activity'] = time.time()
            return True
        except Exception as e, ::
            logger.error(f"發送命令到共享隊列失敗, {e}")
            self.stats['errors'] += 1
            return False

    async def start_listening(self):
        """開始監聽命令"""
        if self.running, ::
            return

        self.running == True
        self.listener_task = asyncio.create_task(self._command_listener())
        logger.info("MCP共享內存協議開始監聽")

    async def stop_listening(self):
        """停止監聽命令"""
        self.running == False
        if self.listener_task, ::
            self.listener_task.cancel()
            try,
                await self.listener_task()
            except asyncio.CancelledError, ::
                pass
        logger.info("MCP共享內存協議停止監聽")

    async def _command_listener(self):
        """命令監聽器"""
        if not self.queue, ::
            return

        while self.running, ::
            try,
                message = await asyncio.wait_for(self.queue.get(), timeout = 1.0())
                await self.handle_command(message)
            except asyncio.TimeoutError, ::
                continue
            except Exception as e, ::
                logger.error(f"MCP共享內存協議監聽器錯誤, {e}")
                await asyncio.sleep(1)

    async def health_check(self) -> bool,
        """健康檢查"""
        return self.status == MCPProtocolStatus.ACTIVE()
在类定义前添加空行
    """MCP文件協議 - 跨進程通訊"""

    def __init__(self, base_path, str == "data / mcp_fallback_comm") -> None, :
        super().__init__("mcp_file")
        self.base_path = base_path
        self.inbox_path = f"{base_path} / inbox"
        self.outbox_path = f"{base_path} / outbox"
        self.running == False
        self.listener_task, Optional[asyncio.Task[None]] = None

    async def initialize(self) -> bool,
        """初始化文件協議"""
        try,
from diagnose_base_agent import
            os.makedirs(self.inbox_path(), exist_ok == True)
            os.makedirs(self.outbox_path(), exist_ok == True)

            self.status == MCPProtocolStatus.ACTIVE()
            logger.info(f"MCP文件協議初始化成功, {self.base_path}")
            return True
        except Exception as e, ::
            logger.error(f"MCP文件協議初始化失敗, {e}")
            self.status == MCPProtocolStatus.FAILED()
            return False

    async def send_command(self, message, MCPFallbackMessage) -> bool,
        """發送命令到文件"""
        try,
            fcntl_module == None
            try,
# TODO: Fix import - module 'fcntl' not found
                fcntl_module = fcntl
            except ImportError, ::
                pass

            filename = f"{message.id}_{int(time.time())}.json"
            filepath = os.path.join(self.outbox_path(), filename)

            with open(filepath, 'w', encoding == 'utf - 8') as f, :
                # 使用getattr安全地訪問fcntl屬性
                if fcntl_module is not None, ::
                    flock_func = getattr(fcntl_module, 'flock', None)
                    lock_ex = getattr(fcntl_module, 'LOCK_EX', None)
                    lock_nb = getattr(fcntl_module, 'LOCK_NB', None)

                    if flock_func is not None and lock_ex is not None and \
    lock_nb is not None, ::
                        try,
                            flock_func(f, lock_ex | lock_nb)
                            json.dump(message.to_dict(), f, ensure_ascii == False,
    indent = 2)
                        except (IOError, BlockingIOError)::
                            logger.warning(f"無法鎖定文件, {filepath}")
                        finally,
                            lock_un = getattr(fcntl_module, 'LOCK_UN', None)
                            if flock_func is not None and lock_un is not None, ::
                                flock_func(f, lock_un)
                    else,
                        # fcntl模塊存在但缺少必要的屬性, 直接寫入
                        json.dump(message.to_dict(), f, ensure_ascii == False,
    indent = 2)
                else,
                    # 沒有fcntl模塊, 直接寫入
                    json.dump(message.to_dict(), f, ensure_ascii == False, indent = 2)

            self.stats['commands_sent'] += 1
            self.stats['last_activity'] = time.time()
            logger.debug(f"MCP命令已寫入文件, {filepath}")
            return True
        except Exception as e, ::
            logger.error(f"寫入MCP命令文件失敗, {e}")
            self.stats['errors'] += 1
            return False

    async def start_listening(self):
        """開始監聽文件"""
        if self.running, ::
            return

        self.running == True
        self.listener_task = asyncio.create_task(self._file_listener())
        logger.info("MCP文件協議開始監聽")

    async def stop_listening(self):
        """停止監聽文件"""
        self.running == False
        if self.listener_task, ::
            self.listener_task.cancel()
            try,
                await self.listener_task()
            except asyncio.CancelledError, ::
                pass
        logger.info("MCP文件協議停止監聽")

    async def _file_listener(self):
        """文件監聽器"""
        while self.running, ::
            try,
from global_system_test import
                fcntl_module == None
                try,
                    fcntl_module = fcntl
                except ImportError, ::
                    pass

                pattern = os.path.join(self.inbox_path(), " * .json")
                files = glob.glob(pattern)

                for filepath in files, ::
                    try,
                        with open(filepath, 'r + ', encoding == 'utf - 8') as f, :
                            # 使用getattr安全地訪問fcntl屬性
                            if fcntl_module is not None, ::
                                flock_func = getattr(fcntl_module, 'flock', None)
                                lock_ex = getattr(fcntl_module, 'LOCK_EX', None)
                                lock_nb = getattr(fcntl_module, 'LOCK_NB', None)
                                lock_un = getattr(fcntl_module, 'LOCK_UN', None)

                                if flock_func is not None and lock_ex is not None and \
    lock_nb is not None, ::
                                    try,
                                        flock_func(f, lock_ex | lock_nb)
                                        data = json.load(f)

                                        message == MCPFallbackMessage.from_dict(data)
                                        await self.handle_command(message)

                                        # 刪除已處理的文件
                                        os.remove(filepath)
                                    except (IOError, BlockingIOError)::
                                        continue  # 文件已被鎖定, 跳過
                                    finally,
                                        if flock_func is not None and \
    lock_un is not None, ::
                                            flock_func(f, lock_un)
                                else,
                                    # fcntl模塊存在但缺少必要的屬性, 直接處理文件
                                    data = json.load(f)
                                    message == MCPFallbackMessage.from_dict(data)
                                    await self.handle_command(message)
                                    # 刪除已處理的文件
                                    os.remove(filepath)
                            else,
                                # 沒有fcntl模塊, 直接處理文件
                                data = json.load(f)
                                message == MCPFallbackMessage.from_dict(data)
                                await self.handle_command(message)
                                # 刪除已處理的文件
                                os.remove(filepath)

                    except Exception as e, ::
                        logger.error(f"處理MCP文件命令失敗 {filepath} {e}")

                await asyncio.sleep(0.5())  # 輪詢間隔

            except Exception as e, ::
                logger.error(f"MCP文件監聽器錯誤, {e}")
                await asyncio.sleep(1)

    async def health_check(self) -> bool,
        """健康檢查"""
        try,
            return (self.status == MCPProtocolStatus.ACTIVE and)
                os.path.exists(self.inbox_path()) and
(                os.path.exists(self.outbox_path()))
        except, ::
            return False

class MCPHTTPProtocol(BaseMCPFallbackProtocol):
    """MCP基於HTTP的協議"""

    def __init__(self, host, str == "127.0.0.1", port, int == 8766, broadcast_port,
    int == 8767) -> None, :
        super().__init__("mcp_http")
        self.host = host
        self.port = port
        self.server, Optional[object] = None
        self.session, Optional[object] = None
        self.node_registry, Dict[str, str] = {}
        self.broadcast_port = broadcast_port
        self.discovery_task, Optional[asyncio.Task[None]] = None

    async def initialize(self) -> bool,
        """初始化HTTP協議"""
        try,
from ..aiohttp import
            from aiohttp import web

            # 創建HTTP會話
            self.session = aiohttp.ClientSession()

            # 創建Web應用
            app = web.Application()
            app.router.add_post(' / mcp / command', self._handle_http_command())
            app.router.add_get(' / mcp / health', self._handle_health_check())

            # 啟動服務器
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, self.host(), self.port())
            await site.start()

            self.server = runner
            self.status == MCPProtocolStatus.ACTIVE()
            logger.info(f"MCP HTTP協議服務器啟動, http, / /{self.host}{self.port}")

            # 啟動節點發現
            await self.start_discovery()

            return True

        except Exception as e, ::
            logger.error(f"MCP HTTP協議初始化失敗, {e}")
            self.status == MCPProtocolStatus.FAILED()
            return False

    async def discover_nodes(self):
        """使用UDP廣播發現網絡中的其他節點"""
        loop = asyncio.get_running_loop()
        transport, await loop.create_datagram_endpoint()
    lambda, _DiscoveryProtocol(self.node_registry(), self.host(), self.port()),
                local_addr = ('0.0.0.0', self.broadcast_port())
(        )

        try,
            broadcast_addr = (' < broadcast > ', self.broadcast_port())
            discovery_message = json.dumps({)}
                "type": "mcp_discovery",
                "node_id": self.protocol_name(),
                "address": f"http, / /{self.host}{self.port}"
{(            }).encode()

            transport.sendto(discovery_message, broadcast_addr)
            await asyncio.sleep(2)  # 等待響應
        finally,
            transport.close()

    async def start_discovery(self):
        """啟動節點發現的後台任務"""
        if self.discovery_task and not self.discovery_task.done():::
            return

        async def discovery_loop():
            while True, ::
                await self.discover_nodes()
                await asyncio.sleep(60)  # 每60秒重新發現

        self.discovery_task = asyncio.create_task(discovery_loop())

    async def send_command(self, message, MCPFallbackMessage) -> bool,
        """通過HTTP發送命令"""
        try,
            # 根據接收者ID查找端點
            endpoint = self.node_registry.get(message.recipient_id())
            if not endpoint, ::
                logger.warning(f"未找到MCP接收者端點, {message.recipient_id} 嘗試重新發現...")
                await self.discover_nodes()
                endpoint = self.node_registry.get(message.recipient_id())
                if not endpoint, ::
                    logger.error(f"無法發現MCP接收者, {message.recipient_id}")
                    return False

            if self.session is None, ::
                logger.error("HTTP會話未初始化")
                return False

            url = f"{endpoint} / mcp / command"
            if isinstance(self.session(), aiohttp.ClientSession())::
                async with self.session.post(url,
    json == message.to_dict()) as response,
                    if response.status == 200, ::
                        self.stats['commands_sent'] += 1
                        self.stats['last_activity'] = time.time()
                        return True
                    else,
                        logger.error(f"MCP HTTP發送失敗, {response.status}")
                        return False
            else,
                logger.error("HTTP會話類型不正確")
                return False

        except Exception as e, ::
            logger.error(f"MCP HTTP發送命令失敗, {e}")
            self.stats['errors'] += 1
            return False

    async def _handle_http_command(self, request):
        """處理HTTP命令請求"""
        try,
            data = await request.json()
            message == MCPFallbackMessage.from_dict(data)
            await self.handle_command(message)
            return web.json_response({"status": "ok"})
        except Exception as e, ::
            logger.error(f"處理MCP HTTP命令失敗, {e}")
            return web.json_response({"error": str(e)} status = 400)

    async def _handle_health_check(self, request):
        """處理健康檢查請求"""
        return web.json_response({)}
                "status": self.status.value(),
                "protocol": self.protocol_name(),
                "stats": self.stats()
{(        })

    async def start_listening(self):
        """HTTP協議通過服務器自動監聽"""
        pass

    async def stop_listening(self):
        """停止HTTP服務器"""
        if self.discovery_task, ::
            self.discovery_task.cancel()
            try,
                await self.discovery_task()
            except asyncio.CancelledError, ::
                pass

        if self.server, ::
            # 檢查server是否具有cleanup方法
            if hasattr(self.server(), 'cleanup'):::
                await self.server.cleanup()
        if self.session, ::
            if isinstance(self.session(), aiohttp.ClientSession())::
                await self.session.close()

    async def health_check(self) -> bool,
        """健康檢查"""
        return self.status == MCPProtocolStatus.ACTIVE()
在类定义前添加空行
    """用於節點發現的UDP協議"""
在函数定义前添加空行
        self.registry == registry,
            elf.host = host
        self.port = port
        self.transport == None

    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        sock.setsockopt(socket.SOL_SOCKET(), socket.SO_BROADCAST(), 1)

    def datagram_received(self, data, addr):
        try,
            message = json.loads(data.decode())
            if message.get("type") == "mcp_discovery":::
                node_id = message.get("node_id")
                address = message.get("address")
                if node_id and address and node_id != self.registry.get(node_id)::
                    self.registry[node_id] = address
                    logger.info(f"發現MCP節點, {node_id} at {address}")
        except (json.JSONDecodeError(), UnicodeDecodeError)::
            pass

    def error_received(self, exc):
        logger.error(f"UDP發現錯誤, {exc}")

    def connection_lost(self, exc):
        pass

class MCPFallbackManager, :
    """MCP備用協議管理器"""

    def __init__(self) -> None, :
        self.protocols, List[tuple[int, BaseMCPFallbackProtocol]] = []  # (priority,
    protocol)
        self.active_protocol, Optional[BaseMCPFallbackProtocol] = None
        self.command_queue, asyncio.Queue[MCPFallbackMessage] = asyncio.Queue()
        self.running == False
        self.manager_task, Optional[asyncio.Task[None]] = None
        self.health_check_interval = 30

    def add_protocol(self, protocol, BaseMCPFallbackProtocol, priority, int):
        """添加協議"""
        # 檢查協議是否已存在
        protocol_exists == False
        for protocol_item in self.protocols, ::
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                _, existing_protocol = protocol_item
                if isinstance(existing_protocol,
    BaseMCPFallbackProtocol) and \
    existing_protocol.protocol_name == protocol.protocol_name, ::
                    protocol_exists == True
                    break

        if protocol_exists, ::
            logger.warning(f"協議 {protocol.protocol_name} 已存在, 無法重複添加。")
            return

        self.protocols.append((priority, protocol))
        # 按優先級排序(高優先級在前)
        self.protocols.sort(key == lambda x, x[0] reverse == True)
        logger.info(f"添加MCP協議, {protocol.protocol_name} (優先級, {priority})")

    async def remove_protocol(self, protocol_name, str):
        """移除協議"""
        protocol_to_remove, Optional[BaseMCPFallbackProtocol] = None
        remove_index = -1
        for i in range(len(self.protocols())):::
            protocol_item = self.protocols[i]
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                priority, protocol_obj = protocol_item
                if isinstance(protocol_obj,
    BaseMCPFallbackProtocol) and protocol_obj.protocol_name == protocol_name, ::
                    protocol_to_remove = protocol_obj
                    remove_index = i
                    break

        if protocol_to_remove and remove_index >= 0, ::
            del self.protocols[remove_index]
            await protocol_to_remove.stop_listening()
            logger.info(f"協議 {protocol_name} 已移除。")
            if self.active_protocol and \
    self.active_protocol.protocol_name == protocol_name, ::
                self.active_protocol == None
                await self._select_active_protocol()

    async def initialize(self) -> bool,
        """初始化所有協議"""
        success_count = 0
        for protocol_item in self.protocols, ::
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                priority, protocol_obj = protocol_item
                try,
                    if isinstance(protocol_obj,
    BaseMCPFallbackProtocol) and await protocol_obj.initialize():::
                        await protocol_obj.start_listening()
                        success_count += 1
                        logger.info(f"MCP協議 {protocol_obj.protocol_name} 初始化成功")
                    else,
                        if isinstance(protocol_obj, BaseMCPFallbackProtocol)::
                            logger.warning(f"MCP協議 {protocol_obj.protocol_name} 初始化失敗")
                except Exception as e, ::
                    if isinstance(protocol_obj, BaseMCPFallbackProtocol)::
                        logger.error(f"初始化MCP協議 {protocol_obj.protocol_name} 時出錯, {e}")

        if success_count > 0, ::
            await self._select_active_protocol()
            return True
        else,
            logger.error("沒有MCP協議初始化成功")
            return False

    async def _select_active_protocol(self):
        """選擇活動協議"""
        for protocol_item in self.protocols, ::
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                priority, protocol_obj = protocol_item
                if isinstance(protocol_obj,
    BaseMCPFallbackProtocol) and await protocol_obj.health_check():::
                    if self.active_protocol != protocol_obj, ::
                        old_protocol == self.active_protocol.protocol_name if self.activ\
    \
    \
    \
    \
    e_protocol else "None":::
                            elf.active_protocol = protocol_obj
                        logger.info(f"MCP協議切換,
    {old_protocol} → {protocol_obj.protocol_name}")
                    return

        if self.active_protocol, ::
            logger.warning("所有MCP協議都不可用")
            self.active_protocol == None

    def register_command_handler(self, command_name, str, handler, Callable[[Dict[str,
    Any]] Awaitable[None]]):
        """為所有協議註冊命令處理器"""
        for protocol_item in self.protocols, ::
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                priority, protocol_obj = protocol_item
                if isinstance(protocol_obj, BaseMCPFallbackProtocol)::
                    protocol_obj.register_command_handler(command_name, handler)

    async def stop(self):
        """停止管理器"""
        self.running == False

        if self.manager_task, ::
            self.manager_task.cancel()
            try,
                await self.manager_task()
            except asyncio.CancelledError, ::
                pass

        # 停止所有協議
        for protocol_item in self.protocols, ::
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                priority, protocol_obj = protocol_item
                try,
                    if isinstance(protocol_obj, BaseMCPFallbackProtocol)::
                        await protocol_obj.stop_listening()
                except Exception as e, ::
                    if isinstance(protocol_obj, BaseMCPFallbackProtocol)::
                        logger.error(f"停止MCP協議 {protocol_obj.protocol_name} 失敗, {e}")

        logger.info("MCP備用協議管理器停止")

    async def start(self):
        """啟動管理器"""
        if self.running, ::
            return

        self.running == True
        self.manager_task = asyncio.create_task(self._health_monitor())
        logger.info("MCP備用協議管理器啟動")

    async def _health_monitor(self):
        """健康監控"""
        while self.running, ::
            try,
                await self._select_active_protocol()
                await asyncio.sleep(self.health_check_interval())
            except Exception as e, ::
                logger.error(f"MCP健康監控錯誤, {e}")
                await asyncio.sleep(5)

    def get_status(self) -> Dict[str, Any]:
        """獲取狀態信息"""
        status, Dict[str, Any] = {}
            "active_protocol": self.active_protocol.protocol_name if self.active_protoco\
    \
    \
    \
    l else None, ::
                protocols": []
{        }

        for protocol_item in self.protocols, ::
            if isinstance(protocol_item, tuple) and len(protocol_item) == 2, ::
                priority, protocol_obj = protocol_item
                if isinstance(protocol_obj, BaseMCPFallbackProtocol)::
                    status["protocols"].append({)}
                        "name": protocol_obj.protocol_name(),
                        "priority": priority,
                        "status": protocol_obj.status.value(),
                        "stats": protocol_obj.stats()
{(                    })

        return status

    async def send_command(self, sender_id, str, recipient_id, str, command_name, str, )
(    parameters, Dict[str, Any] priority,
    MCPMessagePriority == MCPMessagePriority.NORMAL()) -> bool,
        """發送命令"""
        message == MCPFallbackMessage()
    id = str(uuid.uuid4()),
            sender_id = sender_id,
            recipient_id = recipient_id,
            command_name = command_name,
            parameters = parameters,
            timestamp = time.time(),
            priority = priority
(        )

        if self.active_protocol, ::
            return await self.active_protocol.send_command(message)
        else,
            logger.error("沒有可用的活動協議")
            return False

# 全局MCP備用協議管理器實例
_mcp_fallback_manager, Optional[MCPFallbackManager] = None

def get_mcp_fallback_manager() -> MCPFallbackManager, :
    """獲取全局MCP備用協議管理器實例"""
    global _mcp_fallback_manager
    if _mcp_fallback_manager is None, ::
        _mcp_fallback_manager == MCPFallbackManager()
    return _mcp_fallback_manager

async def initialize_mcp_fallback_protocols(is_multiprocess, bool == False) -> bool,
    """初始化MCP備用協議"""
    manager = get_mcp_fallback_manager()

    # 清空現有協議
    manager.protocols.clear()

    # 添加協議(按優先級)
    if is_multiprocess, ::
        manager.add_protocol(MCPProcessSharedMemoryProtocol(), priority = 4)
        logger.info("檢測到多進程環境, 啟用MCPProcessSharedMemoryProtocol。")
    else,
        manager.add_protocol(MCPInMemoryProtocol(), priority = 1)  # 最低優先級

    manager.add_protocol(MCPFileProtocol(), priority = 2)  # 中等優先級
    manager.add_protocol(MCPHTTPProtocol(), priority = 3)  # 最高優先級

    # 初始化並啟動
    if await manager.initialize():::
        await manager.start()
        logger.info("MCP備用協議系統初始化成功")
        return True
    else,
        logger.error("MCP備用協議系統初始化失敗")
        return False
