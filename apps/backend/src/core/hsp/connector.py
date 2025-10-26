from diagnose_base_agent import
from pathlib import Path
from ...hsp.types import
    HSPMessageEnvelope, HSPFactPayload, HSPTaskRequestPayload,
    HSPTaskResultPayload, HSPCapabilityAdvertisementPayload,
    HSPAcknowledgementPayload, HSPQoSParameters, HSPOpinionPayload
()
from .versioning import
from .extensibility import
from .advanced_performance_optimizer import
from .security import
from .performance_optimizer import
from .utils.fallback_config_loader import
from ..shared.network_resilience import
from ..shared.error import
from unittest.mock import MagicMock, AsyncMock  # Added for mock_mode, :
from .bridge.message_bridge import
from .bridge.data_aligner import
from .internal.internal_bus import
from .external.external_connector import
from typing_extensions import Literal  # 添加Literal类型导入
from typing import Callable, Dict, Any, Optional, List  # Added Optional, List
# TODO: Fix import - module 'asyncio' not found
from datetime import datetime, timezone  # 添加datetime模块导入
# TODO: Fix import - module 'uuid' not found
from enhanced_realtime_monitoring import
from tests.test_json_fix import
from tests.tools.test_tool_dispatcher_logging import
# 修复导入路径 - 使用正确的模块路径

# 定义logger
logger, Any = logging.getLogger(__name__)

# Define the base path for schemas, ensuring cross - platform compatibility,::
CHEMA_BASE_PATH == Path(__file__).resolve().parent.parent.parent / "schemas"


def get_schema_uri(schema_name, str) -> str, :
    """Constructs a file URI for a given schema name."""::
    schema_path == SCHEMA_BASE_PATH / schema_name,
    if not schema_path.is_file():::
        # Fallback for when running in a different environment (like tests)::
        # This makes the path relative to the current working directory
        # In a real - world scenario, a more robust solution might be needed
        # like using an environment variable or a configuration setting.
        project_root == Path.cwd()
        schema_path == project_root / "apps" / "backend" / "schemas" / schema_name,
        if not schema_path.is_file():::
            # As a last resort, return a placeholder if the file isn't found, :
            # This prevents crashes but signals a configuration issue.:
            logger.warning(f"Schema file not found, {schema_name}. Path was,
    {schema_path}")
            return f"file, / //{schema_name}_not_found"
    return schema_path.as_uri()


class HSPConnector, :
在函数定义前添加空行
(    mock_mqtt_client, Optional[MagicMock] = None, internal_bus, Optional[InternalBus] = None, message_bridge, Optional[MessageBridge] = None, enable_fallback, bool == True, * * kwargs) -> None,
        self.ai_id = ai_id
        self.mock_mode = mock_mode
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.enable_fallback = enable_fallback
        self.fallback_manager == None
        self.fallback_initialized == False
        self.logger = logging.getLogger(__name__)
        self.hsp_available == False  # Track HSP availability
        self._is_connected, bool == False  # Initialize instance variable

        # 性能优化参数
        self.message_cache, Dict[str, Any] = {}  # 消息缓存
        self.cache_ttl = 300  # 缓存有效期(秒)
        self.batch_send_enabled == True  # 批量发送
        self.batch_size = 10  # 批量大小
        self.message_batch, List[Dict[str, Any]] = []  # 消息批处理队列
        self.last_batch_send = time.time()  # 上次批量发送时间

        # 性能优化器
        self.performance_optimizer == HSPPerformanceOptimizer()
        self.performance_enhancer == HSPPerformanceEnhancer(self.performance_optimizer()\
    )

        # 安全管理器
        self.security_manager == HSPSecurityManager()
        self.security_context == HSPSecurityContext(self.security_manager())

        # 高级性能优化器
        self.advanced_performance_optimizer == HSPAdvancedPerformanceOptimizer()
        self.advanced_performance_enhancer == HSPAdvancedPerformanceEnhancer(self.advanc\
    ed_performance_optimizer())

        # 扩展管理器
        self.extension_manager == HSPExtensionManager()
        self.message_registry == HSPMessageRegistry()

        # 版本管理器
        self.version_manager == HSPVersionManager()
        self.version_converter == HSPVersionConverter(self.version_manager())

        if self.mock_mode, ::
            self.logger.info("HSPConnector, Initializing in mock mode.")
            self.logger.debug(f"HSPConnector.__init__ - ai_id, {ai_id} mock_mode,
    {mock_mode}")
            self.external_connector == = MagicMock(spec = = ExternalConnector)
            self.external_connector.ai_id = ai_id  # Ensure mock has ai_id
            self.external_connector.connect.return_value == True
            self.external_connector.disconnect.return_value == True
            self.external_connector.subscribe.return_value == True
            self.external_connector.unsubscribe.return_value == True
            self.external_connector.publish == = AsyncMock(return_value = = True)  # Explicitly set return value for publish,:
            # Explicitly mock mqtt_client and its publish method,
            if mock_mqtt_client, ::
                self.external_connector.mqtt_client = mock_mqtt_client
            else,
                mock_mqtt_client_instance == MagicMock()
                mock_mqtt_client_instance.publish == = AsyncMock(return_value = = True)
                self.external_connector.mqtt_client = mock_mqtt_client_instance

            self.is_connected == True  # Considered connected in mock mode
            self.hsp_available == True  # Mock mode considers HSP available
        else,
            self.external_connector == ExternalConnector()
                ai_id = ai_id,
                broker_address = broker_address,,
(    broker_port = broker_port)
            self.is_connected == False  # Actual connection status
            self.hsp_available == False

        if internal_bus is None, ::
            self.internal_bus == InternalBus()
        else,
            self.internal_bus = internal_bus

        self.data_aligner == DataAligner()  # DataAligner can be unique per connector

        if message_bridge is None, ::
            self.message_bridge == MessageBridge()
    self.external_connector(),
                self.internal_bus(),
(                self.data_aligner())
        else,
            self.message_bridge = message_bridge

        # Callbacks for different message types, ::
        self._fact_callbacks = []
        self._capability_advertisement_callbacks = []
        self._task_request_callbacks = []
        self._task_result_callbacks = []
        self._acknowledgement_callbacks == []  # New for incoming ACKs, ::
        self._connect_callbacks = []
        self._disconnect_callbacks = []

        self._pending_acks, Dict[str,
    asyncio.Future[Any]] = {}  # New To track messages awaiting ACK
        self._message_retry_counts, Dict[str, int] = {}  # New To track retry counts for messages, :
        self.ack_timeout_sec == 10  # New Default timeout for ACK, :
        self.max_ack_retries == 3  # New Max retries for messages requiring ACK, :
        self.retry_policy == RetryPolicy()
    max_attempts = self.max_ack_retries(),
            backoff_factor = 2,
(            max_delay = 60)  # Initialize retry policy
        self.circuit_breaker == = CircuitBreaker(failure_threshold = = 5, recovery_timeout = 300)  # Initialize circuit breaker
        # New Callback to get capabilities,
        self._capability_provider_callback,
    Optional[Callable[[] List[HSPCapabilityAdvertisementPayload]]] = None

        # Initialize fallback protocols if enabled, :
        # Moved to connect method to ensure event loop is running

        # Register internal message bridge handler for external messages, :
        # 先应用高级性能增强, 再应用基础性能增强
        enhanced_handler = self.advanced_performance_enhancer.enhance_receive()
(    self.message_bridge.handle_external_message())
        callback = self.performance_enhancer.enhance_receive(enhanced_handler)
        # 确保callback是正确的类型,
        if callable(callback)::
            self.external_connector.on_message_callback == callback  # type, ignore

        # Subscribe to internal bus messages that need to go external
        self.internal_bus.subscribe("hsp.internal.message",
    self._handle_internal_message())

        # Subscribe to internal bus messages that are results from external
        self.internal_bus.subscribe("hsp.external.fact",
    self._dispatch_fact_to_callbacks_sync())
        self.internal_bus.subscribe()
    "hsp.external.capability_advertisement", ,
(    self._dispatch_capability_advertisement_to_callbacks_sync())
        self.internal_bus.subscribe("hsp.external.task_request",
    self._dispatch_task_request_to_callbacks_sync())
        self.internal_bus.subscribe("hsp.external.task_result",
    self._dispatch_task_result_to_callbacks_sync())
        self.internal_bus.subscribe("hsp.external.acknowledgement", )
(    self._dispatch_acknowledgement_to_callbacks_sync())  # New subscription

    def _handle_internal_message(self, message, Any) -> None, :
        """处理内部消息的同步包装器"""
        asyncio.create_task(self.message_bridge.handle_internal_message(message))

    def _dispatch_fact_to_callbacks_sync(self, message, Any) -> None, :
        """同步包装器用于分发事实消息到回调"""
        asyncio.create_task(self._dispatch_fact_to_callbacks(message))

    def _dispatch_capability_advertisement_to_callbacks_sync(self, message, Any) -> None, :
        """同步包装器用于分发能力广告消息到回调"""
        asyncio.create_task(self._dispatch_capability_advertisement_to_callbacks(message\
    ))

    def _dispatch_task_request_to_callbacks_sync(self, message, Any) -> None, :
        """同步包装器用于分发任务请求消息到回调"""
        asyncio.create_task(self._dispatch_task_request_to_callbacks(message))

    def _dispatch_task_result_to_callbacks_sync(self, message, Any) -> None, :
        """同步包装器用于分发任务结果消息到回调"""
        asyncio.create_task(self._dispatch_task_result_to_callbacks(message))

    def _dispatch_acknowledgement_to_callbacks_sync(self, message, Any) -> None, :
        """同步包装器用于分发确认消息到回调"""
        asyncio.create_task(self._dispatch_acknowledgement_to_callbacks(message))

    async def _dispatch_fact_to_callbacks(self, message, Any) -> None,
        """异步分发事实消息到回调"""
        for callback in self._fact_callbacks, ::
            try,
                if asyncio.iscoroutinefunction(callback)::
                    await callback(message)
                else,
                    callback(message)
            except Exception as e, ::
                self.logger.error(f"Error in fact callback, {e}")

    async def _dispatch_capability_advertisement_to_callbacks(self, message,
    Any) -> None,
        """异步分发能力广告消息到回调"""
        for callback in self._capability_advertisement_callbacks, ::
            try,
                if asyncio.iscoroutinefunction(callback)::
                    await callback(message)
                else,
                    callback(message)
            except Exception as e, ::
                self.logger.error(f"Error in capability advertisement callback, {e}")

    async def _dispatch_task_request_to_callbacks(self, message, Any) -> None,
        """异步分发任务请求消息到回调"""
        for callback in self._task_request_callbacks, ::
            try,
                if asyncio.iscoroutinefunction(callback)::
                    await callback(message)
                else,
                    callback(message)
            except Exception as e, ::
                self.logger.error(f"Error in task request callback, {e}")

    async def _dispatch_task_result_to_callbacks(self, message, Any) -> None,
        """异步分发任务结果消息到回调"""
        for callback in self._task_result_callbacks, ::
            try,
                if asyncio.iscoroutinefunction(callback)::
                    await callback(message)
                else,
                    callback(message)
            except Exception as e, ::
                self.logger.error(f"Error in task result callback, {e}")

    async def _dispatch_acknowledgement_to_callbacks(self, message, Any) -> None,
        """异步分发确认消息到回调"""
        for callback in self._acknowledgement_callbacks, ::
            try,
                if asyncio.iscoroutinefunction(callback)::
                    await callback(message)
                else,
                    callback(message)
            except Exception as e, ::
                self.logger.error(f"Error in acknowledgement callback, {e}")

    # - - - Test compatibility properties - - -
    @property
在函数定义前添加空行
        """Default QoS level for test compatibility."""::
        return 1

    @property
在函数定义前添加空行
        """Provides access to the underlying MQTT client for test compatibility."""::
        return self.external_connector.mqtt_client()
    @mqtt_client.setter()
在函数定义前添加空行
        """Allows tests to set the mock MQTT client."""
        self.external_connector.mqtt_client = value

    @property
在函数定义前添加空行
        """Provides access to subscribed topics for test compatibility."""::
        return getattr(self.external_connector(), 'subscribed_topics', set())

    @property
在函数定义前添加空行
        """Provides message callback for test compatibility."""::
        # Tests expect signature on_message(client, topic, payload, qos, properties)
        # MessageBridge.handle_external_message expects handle_external_message(topic,
    message)
        async def test_compatible_on_message(client, topic, payload, qos,
    properties) -> None,
            topic_str == topic.decode() if isinstance(topic, (bytes, bytearray)) else topic, :
            payload_str == payload.decode() if isinstance(payload, (bytes, bytearray)) else payload, :
            # 直接调用回调函数而不是创建任务,
            if self.external_connector.on_message_callback, ::
                await self.external_connector.on_message_callback(topic_str,
    payload_str)
        return test_compatible_on_message


    @on_message.setter()
在函数定义前添加空行
        """Allows setting message callback for test compatibility."""::
        # Wrap a test - provided callback (client, topic, payload, qos, properties)
        async def wrapper(topic, str, message, str):
            await callback(None, topic, message, 1, None)
        self.external_connector.on_message_callback == wrapper  # type, ignore

    def register_on_fact_callback(self, callback):
        """注册事实消息回调"""
        self._fact_callbacks.append(callback)

    def register_on_capability_advertisement_callback(self, callback):
        """注册能力广告消息回调"""
        self._capability_advertisement_callbacks.append(callback)

    def register_on_task_request_callback(self, callback):
        """注册任务请求消息回调"""
        self._task_request_callbacks.append(callback)

    def register_on_task_result_callback(self, callback):
        """注册任务结果消息回调"""
        self._task_result_callbacks.append(callback)

    def register_on_acknowledgement_callback(self, callback):
        """注册确认消息回调"""
        self._acknowledgement_callbacks.append(callback)

    def register_on_connect_callback(self, callback):
        """注册连接回调"""
        self._connect_callbacks.append(callback)

    def register_on_disconnect_callback(self, callback):
        """注册断开连接回调"""
        self._disconnect_callbacks.append(callback)

    # - - - Backward compatibility methods - - -
在函数定义前添加空行
        """Backward compatibility method for registering fact callbacks."""::
        self.register_on_fact_callback(callback)

    def on_command_received(self, callback):
        """Backward compatibility method for registering command callbacks (maps to task\
    _request)."""::
        self.register_on_task_request_callback(callback)

    def on_connect_callback(self, callback):
        """Backward compatibility method for registering connect callbacks."""::
        self.register_on_connect_callback(callback)

    def on_disconnect_callback(self, callback):
        """Backward compatibility method for registering disconnect callbacks."""::
        self.register_on_disconnect_callback(callback)

    async def mqtt_subscribe(self, topic, str, qos, int == 1):
        """Direct MQTT subscription for test compatibility.""":::
        if self.mock_mode, ::
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector(), 'subscribed_topics'):::
                self.external_connector.subscribed_topics = set()
            self.external_connector.subscribed_topics.add(topic)
        else,
            # In real mode, use the external connector
            return await self.external_connector.mqtt_subscribe(topic, qos)




















        """Direct MQTT subscription for test compatibility.""":::
        if self.mock_mode, ::
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector(), 'subscribed_topics'):::
                self.external_connector.subscribed_topics = set()
            self.external_connector.subscribed_topics.add(topic)
            # Also call the mock subscribe method
            if hasattr(self.external_connector(), 'subscribe'):::
                await self.external_connector.subscribe(topic, qos)
        else,
            if hasattr(self.external_connector(), 'subscribe'):::
                await self.external_connector.subscribe(topic, qos)

    async def close(self):
        """Disconnects the external connector and cleans up resources."""
        self.logger.info("HSPConnector, Disconnecting external connector...")
        if self.external_connector and hasattr(self.external_connector(),
    'disconnect'):::
            try,
                await self.external_connector.disconnect()
                self.logger.info("HSPConnector, External connector disconnected.")
            except Exception as e, ::
                self.logger.error(f"HSPConnector,
    Error during external connector disconnect, {e}")

        if self.fallback_manager, ::
            try,
                # 修复：确保正确调用shutdown方法(不是异步方法)
                if hasattr(self.fallback_manager(),
    'shutdown') and callable(self.fallback_manager.shutdown())::
                    self.fallback_manager.shutdown()
                self.logger.info("HSPConnector, Fallback manager shut down.")
            except Exception as e, ::
                self.logger.error(f"HSPConnector,
    Error during fallback manager shutdown, {e}")

        self.is_connected == False
        self.hsp_available == False

    async def disconnect(self):
        if self.mock_mode, ::
            self.logger.info("HSPConnector, Mock disconnect successful.")
            self.is_connected == False
        else,
            try,
                await self.external_connector.disconnect()
            except Exception as e, ::
                self.logger.warning(f"HSPConnector,
    external disconnect raised (likely already closed) {e}")
            finally,
                # Reflect underlying state or force false
                try,
                    self.is_connected = bool(getattr(self.external_connector(),
    'is_connected', False))
                except Exception, ::
                    self.is_connected == False

        if self.fallback_manager and self.fallback_initialized, ::
            try,
                # 修复：确保正确调用shutdown方法(不是异步方法)
                if hasattr(self.fallback_manager(),
    'shutdown') and callable(self.fallback_manager.shutdown())::
                    self.fallback_manager.shutdown()
            except Exception as e, ::
                self.logger.warning(f"HSPConnector, fallback shutdown error, {e}")
            finally,
                self.fallback_initialized == False

        for callback in self._disconnect_callbacks, ::
            try,
                await callback()
            except Exception as e, ::
                self.logger.warning(f"HSPConnector, disconnect callback error, {e}")

    async def _initialize_protocols_with_config(self, config, Dict[str, Any]) -> bool,
        """
        Initializes the individual fallback protocols based on the provided configuratio\
    n.
        """
        try,
from .fallback.fallback_protocols import

            protocols_config = config.get("protocols", {})

            # Initialize in - memory protocol
            memory_config = protocols_config.get("memory", {})
            if memory_config.get("enabled", True) and self.fallback_manager, ::
                memory_protocol == InMemoryProtocol()
                priority = memory_config.get("priority", 1)
                self.fallback_manager.add_protocol(memory_protocol, priority = priority)
                self.logger.debug(f"Added memory protocol with priority {priority}")

            # Initialize file - based protocol
            file_config = protocols_config.get("file", {})
            if file_config.get("enabled", True) and self.fallback_manager, ::
                base_path = file_config.get("base_path", "data / fallback_comm")
                file_protocol == FileBasedProtocol(base_path = base_path)
                priority = file_config.get("priority", 2)
                self.fallback_manager.add_protocol(file_protocol, priority = priority)
                self.logger.debug(f"Added file protocol with priority {priority}")

            # Initialize HTTP protocol
            http_config = protocols_config.get("http", {})
            if http_config.get("enabled", True) and self.fallback_manager, ::
                host = http_config.get("host", "127.0.0.1")
                # Check TESTING env var here as well
                port == 0 if os.environ.get('TESTING') == 'true' else http_config.get("p\
    ort", 8765)::
                http_protocol == HTTPProtocol(host = host, port = port)
                priority = http_config.get("priority", 3)
                self.fallback_manager.add_protocol(http_protocol, priority = priority)
                self.logger.debug(f"Added HTTP protocol with priority {priority}")

            # Initialize and start the fallback manager,
            if self.fallback_manager, ::
                # 修复：确保正确调用initialize和start方法(不是异步方法)
                if (hasattr(self.fallback_manager(), 'initialize') and, :)
                    callable(self.fallback_manager.initialize()) and
                    hasattr(self.fallback_manager(), 'start') and,
(                    callable(self.fallback_manager.start())):




















                    # Continue with the rest of the logic
                    init_result == self.fallback_manager.initialize():
                    if init_result, ::
                        self.fallback_manager.start()
                        return True
                    else,
                        return False
                else,
                    return False
            else,
                return False

        except Exception as e, ::
            self.logger.error(f"Error initializing protocols with config, {e}")
            return False

    def get_communication_status(self) -> Dict[str, Any]:
        """
        Returns the current communication status.
        """
        status = {}
            "hsp_available": self.hsp_available(),
            "is_connected": self.is_connected(),
            "fallback_enabled": self.enable_fallback(),
            "fallback_initialized": self.fallback_initialized()
{        }

        if self.fallback_manager, ::
            # 修复：确保正确调用get_status方法(不是异步方法)
            if hasattr(self.fallback_manager(),
    'get_status') and callable(self.fallback_manager.get_status())::
                status["fallback_status"] = self.fallback_manager.get_status()

        return status

    async def health_check(self) -> Dict[str, Any]
        """健康检查"""
        health = {}
            "hsp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False
{        }

        # 检查HSP健康状态
        if self.hsp_available and self.is_connected, ::
            try,
                # 可以添加实际的健康检查逻辑
                health["hsp_healthy"] = True
            except, ::
                health["hsp_healthy"] = False
                self.hsp_available == False

        # 检查fallback健康状态
        if self.fallback_manager, ::
            try,
                # 修复：确保正确调用get_status方法(不是异步方法)
                if hasattr(self.fallback_manager(),
    'get_status') and callable(self.fallback_manager.get_status())::
                    fallback_status = self.fallback_manager.get_status()
                    health["fallback_healthy"] = fallback_status.get("active_protocol") \
    is not None
            except, ::
                health["fallback_healthy"] = False

        health["overall_healthy"] = health["hsp_healthy"] or health["fallback_healthy"]
        return health

    # 添加subscribe方法以解决测试中的AttributeError
    async def subscribe(self, topic, str, qos, int == 1):
        """
        Subscribe to a topic.

        Args,
            topic, The topic to subscribe to
            qos, Quality of Service level (default, 1)
        """
        if self.mock_mode, ::
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector(), 'subscribed_topics'):::
                self.external_connector.subscribed_topics = set()
            self.external_connector.subscribed_topics.add(topic)
            # Also call the mock subscribe method
            if hasattr(self.external_connector(), 'subscribe'):::
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe())::
                    await self.external_connector.subscribe(topic, qos)
                else,
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)
        else,

            if hasattr(self.external_connector(), 'subscribe'):::
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe())::
                    await self.external_connector.subscribe(topic, qos)
                else,
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)

    async def publish_opinion(self, opinion_payload, HSPOpinionPayload, topic,
    Optional[str] = None) -> bool,
        """
        Publishes an opinion to the HSP network.

        Args,
            opinion_payload, The opinion to publish.
            topic, The topic to publish to. If None, uses the standard opinion topic.

        Returns, bool True if the opinion was published successfully,
    False otherwise.:::
            ""
        try,
            # Create the HSP message envelope
            envelope, HSPMessageEnvelope = self._create_envelope()
                message_type == "HSP, Opinion", ,
    payload = dict(opinion_payload),
                payload_schema_uri = get_schema_uri("HSP_Opinion_v0.1.schema.json")
(            )

            # Use the standard opinion topic if not provided, ::
                f topic is None,
                topic = f"hsp / knowledge / opinions / {self.ai_id}"

            # Publish the message
            success = await self.publish_message(topic, envelope)

            if success, ::
                self.logger.info(f"Opinion {opinion_payload.get('id')} published success\
    fully.")
            else,
                self.logger.error(f"Failed to publish opinion {opinion_payload.get('id')\
    }.")

            return success

        except Exception as e, ::
            self.logger.error(f"Error publishing opinion, {e}", exc_info == True)
            return False

    async def subscribe_to_facts(self, callback, Callable[..., Any]):
        # Subscribe to fact messages
        self.register_on_fact_callback(callback)

        # Subscribe to the fact topic
        topic = f"hsp / knowledge / facts / #"
        await self.subscribe(topic)

    async def subscribe_to_opinions(self, callback, Callable[..., Any]):
        # Register the callback for opinion messages, ::
        # Note, We'll treat opinions as a special type of fact for now, :
        self.register_on_fact_callback(callback)

        # Subscribe to the opinion topic
        topic = f"hsp / knowledge / opinions / #"
        await self.subscribe(topic)

    def get_connector_status(self) -> Dict[str, Any]:
        # Get the connector status
        return self.get_communication_status()

    async def _dispatch_task_result_to_callbacks(self, message, Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching task result to {len(self._task_result_callbacks(\
    ))} callbacks. Message, {message}")

        # 安全验证
        is_valid,
    validated_message = self.security_context.authenticate_and_process_message(message)
        if not is_valid, ::
            self.logger.warning(f"消息安全验证失败, {message.get('message_id', 'unknown')}")
            return

        # 使用验证后的消息
        payload = validated_message.get("payload")
        sender_ai_id = validated_message.get("sender_ai_id")

        if payload and sender_ai_id, ::
            result_payload == HSPTaskResultPayload( * *payload)
            for callback in self._task_result_callbacks, ::
                self.logger.debug(f"Calling on_task_result_callback, {callback}")
                if asyncio.iscoroutinefunction(callback)::
                    await callback(result_payload, sender_ai_id, validated_message)
                else,
                    callback(result_payload, sender_ai_id, validated_message)

            # Check if ACK is required and send it, ::
                os_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack"):::
                ack_payload, HSPAcknowledgementPayload = {}
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc()).isoformat(),
                    "target_message_id": message.get("message_id", "")
{                }
                ack_envelope, HSPMessageEnvelope = {}
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4()),
                    "correlation_id": message.get("message_id"),
    # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id(),
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc()).isoformat(),
                    "message_type": "HSP, Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"}
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schem\
    a.json"),
                    "payload": dict(ack_payload)
{                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1,
                    ck_topic = f"hsp / acks / {sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos = 1)

    async def _dispatch_acknowledgement_to_callbacks(self, message, Dict[str, Any]):
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(f"Dispatching acknowledgement to {len(self._acknowledgement_ca\
    llbacks())} callbacks. Message, {message}")

        # 安全验证
        is_valid,
    validated_message = self.security_context.authenticate_and_process_message(message)
        if not is_valid, ::
            self.logger.warning(f"消息安全验证失败, {message.get('message_id', 'unknown')}")
            return

        # 使用验证后的消息
        payload = validated_message.get("payload")
        sender_ai_id = validated_message.get("sender_ai_id")

        if payload and sender_ai_id, ::
            ack_payload == HSPAcknowledgementPayload( * *payload)  # type ignore
            target_message_id = ack_payload.get("target_message_id")
            correlation_id = validated_message.get("correlation_id")

            # Resolve pending ACK if any, ::
                f correlation_id and correlation_id in self._pending_acks,
                ack_future = self._pending_acks[correlation_id]
                if not ack_future.done():::
                    ack_future.set_result(ack_payload)
                    self.logger.debug(f"Resolved pending ACK for correlation_id,
    {correlation_id}"):::
                        or callback in self._acknowledgement_callbacks,
                self.logger.debug(f"Calling on_acknowledgement_callback, {callback}")
                if asyncio.iscoroutinefunction(callback)::
                    await callback(ack_payload, sender_ai_id, validated_message)
                else,
                    callback(ack_payload, sender_ai_id, validated_message)

    async def _handle_fact_message(self, fact_message, Dict[str, Any]):
        """
        Handle a fact message.

        Args,
                fact_message, The fact message to handle.
        """
        # Dispatch the fact message to callbacks
        await self._dispatch_fact_to_callbacks(fact_message)

    async def _handle_opinion_message(self, opinion_message, Dict[str, Any]):
        """
        Handle an opinion message.

        Args,
                opinion_message, The opinion message to handle.
        """
        # Dispatch the opinion message to callbacks (treated as facts for now)::
= await self._dispatch_fact_to_callbacks(opinion_message)

    def _create_envelope(:)
        self,
        message_type, str,
        payload, Dict[str, Any]
        payload_schema_uri, Optional[str] = None,
        recipient_ai_id, str = "all",
        communication_pattern, Literal[]
            "publish", "request", "response",
            "stream_data", "stream_ack",
            "acknowledgement", "negative_acknowledgement",
            "broadcast", "multicast", "unicast",
            "notification", "event", "command",
            "query", "reply"
[        ] = "publish", ,
    qos_parameters, Optional[HSPQoSParameters] = None
(    ) -> HSPMessageEnvelope,
        """
        Creates an HSP message envelope with standard fields.:
            rgs,
            message_type, The type of message (e.g., "HSP, Fact").
            payload, The message payload.
            payload_schema_uri, URI to the payload schema.
            recipient_ai_id, The recipient AI ID (default, "all").
            communication_pattern, The communication pattern (default, "publish").
            qos_parameters, Quality of service parameters.

        Returns,
            HSPMessageEnvelope, The created envelope.
        """
        envelope, HSPMessageEnvelope = {}
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": None,
            "sender_ai_id": self.ai_id(),
            "recipient_ai_id": recipient_ai_id,
            "timestamp_sent": datetime.now(timezone.utc()).isoformat(),
            "message_type": message_type,
            "protocol_version": self.version_manager.current_version(),
            "communication_pattern": communication_pattern,
            "security_parameters": None,
            "qos_parameters": qos_parameters or {"requires_ack": False,
    "priority": "medium"}
            "routing_info": None,
            "payload_schema_uri": payload_schema_uri,
            "payload": payload
{        }

        # 应用安全处理
        try,
            secured_envelope = self.security_context.secure_message(dict(envelope),
    self.ai_id())
            # 确保返回类型正确
            return envelope
        except Exception as e, ::
            self.logger.error(f"安全处理消息失败, {e}")
            return envelope

    async def _raw_publish_message(self, topic, str, envelope, HSPMessageEnvelope, qos,
    int == 1) -> bool,
        """原始发布消息方法"""
        try,
            # 将信封转换为JSON字符串
            payload = json.dumps(envelope, ensure_ascii == False)
            # 发布消息
            await self.external_connector.publish(topic, payload, qos)
            return True
        except Exception as e, ::
            self.logger.error(f"Error in _raw_publish_message, {e}")
            return False

    async def publish_message(self, topic, str, envelope, HSPMessageEnvelope, qos,
    int == 1) -> bool,
        self.logger.info(f"HSPConnector,
    publish_message called. self.external_connector.publish is {type(self.external_connector.publish())}")

        message_id = envelope.get("message_id")
        correlation_id == envelope.get("correlation_id") or message_id # Use message_id if correlation_id is not set, ::
            os_params = envelope.get("qos_parameters") or {}
        requires_ack = qos_params.get("requires_ack", False)

        # 性能优化：优化消息路由
        optimized_message = await self.performance_optimizer.optimize_message_routing(di\
    ct(envelope))  # type ignore

        # 性能优化：检查消息缓存
        if not requires_ack, ::
            cached_result = self._get_cached_message(message_id)
            if cached_result is not None, ::
                self.logger.debug(f"使用缓存结果发送消息, {message_id}")
                return cached_result

        # 性能优化：批量发送
        if self.batch_send_enabled and not requires_ack, ::
            # 将消息添加到批处理队列
            self.message_batch.append({)}
                'topic': topic,
                'envelope': envelope,
                'qos': qos
{(            })
            # 尝试批量发送
            await self._batch_send_messages()
            # 缓存结果
            self._cache_message(message_id, True)
            return True

        # Initialize retry count for this message if it's new, ::
            f correlation_id not in self._message_retry_counts,
            self._message_retry_counts[correlation_id] = 0

        # Apply Circuit Breaker and Retry Policy to the raw publish attempt
        # This ensures that external_connector.publish attempts are resilient
        try,
            # The decorated function will handle retries and circuit breaking for the direct publish, ::
= await self.circuit_breaker(self.retry_policy(self._raw_publish_message()))(topic,
    envelope, qos)
            self.logger.debug(f"Message {correlation_id} published via HSP (decorated)."\
    )

            if requires_ack, ::
                ack_future = asyncio.Future()
                self._pending_acks[correlation_id] = ack_future
                try,
                    await asyncio.wait_for(ack_future, timeout = self.ack_timeout_sec())
                    self.logger.info(f"ACK received for message {correlation_id}.")::
                    # Clear retry count on success,
                    if correlation_id in self._message_retry_counts, ::
                        del self._message_retry_counts[correlation_id]
                    # 缓存结果
                    self._cache_message(message_id, True)
                    return True
                except asyncio.TimeoutError, ::
                    self.logger.warning(f"ACK timeout for message {correlation_id}. Tryi\
    ng fallback if enabled."):::
                    # Try fallback first before retrying,
                    if self.enable_fallback and self.fallback_manager, ::
                        fallback_success = await self._send_via_fallback(topic,
    dict(envelope), qos)
                        if fallback_success, ::
                            self.logger.info(f"Message {correlation_id} sent via fallbac\
    k after ACK timeout.")
                            # Clear retry count on success
                            if correlation_id in self._message_retry_counts, ::
                                del self._message_retry_counts[correlation_id]
                            # 缓存结果
                            self._cache_message(message_id, True)
                            return True
                        else,
                            self.logger.error(f"Fallback also failed for message {correl\
    ation_id} after ACK timeout.")::
                    # Implement retry logic based on max_ack_retries for HSP attempts, ::
                        etry_count = self._message_retry_counts.get(correlation_id, 0)
                    if retry_count < self.max_ack_retries, ::
                        self._message_retry_counts[correlation_id] = retry_count + 1
                        self.logger.info(f"Retrying message {correlation_id} (attempt {retry_count + 1} / {self.max_ack_retries}) after ACK timeout.")
                        # Exponential backoff before retry,
= await asyncio.sleep(2 ** retry_count)
                        return await self.publish_message(topic, envelope, qos)
                    else,
                        self.logger.error(f"Max retries exceeded for message {correlatio\
    n_id} after ACK timeout.")::
                        # 缓存结果
                        self._cache_message(message_id, False)
                        return False,
            else,
                # Clear retry count on success for non - ACK messages,::
                    f correlation_id in self._message_retry_counts,
                    del self._message_retry_counts[correlation_id]
                # 缓存结果
                self._cache_message(message_id, True)
                return True
        except Exception as e, ::
            self.logger.error(f"Error publishing message {correlation_id} {e}")
            # Implement retry logic based on max_ack_retries for general errors, ::
                etry_count = self._message_retry_counts.get(correlation_id, 0)
            if retry_count < self.max_ack_retries, ::
                self._message_retry_counts[correlation_id] = retry_count + 1
                self.logger.info(f"Retrying message {correlation_id} (attempt {retry_count + 1} / {self.max_ack_retries}) after error.")
                # Exponential backoff before retry,
= await asyncio.sleep(2 ** retry_count)
                return await self.publish_message(topic, envelope, qos)
            else,
                self.logger.error(f"Max retries exceeded for message {correlation_id} af\
    ter error.")::
                # 缓存结果
                self._cache_message(message_id, False)
                return False

    async def publish_fact(self, fact_payload, HSPFactPayload, topic,
    Optional[str] = None) -> bool,
        """
        Publishes a fact to the HSP network.

        Args,
            fact_payload, The fact to publish.

        Returns, bool True if the fact was published successfully, False otherwise.:::
            ""
        try,
            # Create the HSP message envelope
            envelope, HSPMessageEnvelope = self._create_envelope()
                message_type == "HSP, Fact", ,
    payload = dict(fact_payload),
                payload_schema_uri = get_schema_uri("HSP_Fact_v0.1.schema.json")
(            )

            # Use the standard fact topic if not provided, ::
                f topic is None,
                topic = f"hsp / knowledge / facts / {self.ai_id}"

            # Publish the message
            success = await self.publish_message(topic, envelope)

            if success, ::
                self.logger.info(f"Fact {fact_payload.get('id')} published successfully.\
    ")
            else,
                self.logger.error(f"Failed to publish fact {fact_payload.get('id')}.")

            return success

        except Exception as e, ::
            self.logger.error(f"Error publishing fact, {e}", exc_info == True)
            return False

    async def send_task_request(self, payload, HSPTaskRequestPayload,
    target_ai_id_or_topic, str, qos, int == 1) -> Optional[str]
        correlation_id = str(uuid.uuid4())
        envelope, HSPMessageEnvelope = {}
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "sender_ai_id": self.ai_id(),
            "recipient_ai_id": payload.get("target_ai_id") or target_ai_id_or_topic if payload.get("target_ai_id") is not None else target_ai_id_or_topic, ::
                timestamp_sent": datetime.now(timezone.utc()).isoformat(),
            "message_type": "HSP, TaskRequest_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "request",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": True, "priority": "high"}
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_TaskRequest_v0.1.schema.json"),
            "payload": dict(payload)
{        }
        # The topic for task requests is usually hsp / requests / {recipient_ai_id}:
        # If target_ai_id_or_topic is a topic, use it directly.
        # Otherwise, construct the topic.:
        mqtt_topic == target_ai_id_or_topic if " / " in target_ai_id_or_topic else f"hsp / requests / {target_ai_id_or_topic}":::
            uccess = await self.publish_message(mqtt_topic, envelope, qos)
        return correlation_id if success else None, ::
            sync def send_task_result(self, payload, HSPTaskResultPayload,
    target_ai_id_or_topic, str, correlation_id, str, qos, int == 1) -> bool,
        envelope, HSPMessageEnvelope = {}
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": correlation_id,
            "sender_ai_id": self.ai_id(),
            "recipient_ai_id": payload.get("requester_ai_id", target_ai_id_or_topic),
            "timestamp_sent": datetime.now(timezone.utc()).isoformat(),
            "message_type": "HSP, TaskResult_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "response",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "high"}
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_TaskResult_v0.1.schema.json"),
            "payload": dict(payload)
{        }
        mqtt_topic == target_ai_id_or_topic if " / " in target_ai_id_or_topic else f"hsp / results / {target_ai_id_or_topic}":::
            return await self.publish_message(mqtt_topic, envelope, qos)

    async def publish_capability_advertisement(self, cap_payload,
    HSPCapabilityAdvertisementPayload, qos, int == 1):
        topic == f"hsp / capabilities / advertisements / {self.ai_id}" # Specific topic for this AI's capabilities,::
            nvelope, HSPMessageEnvelope = {}
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4()),
            "correlation_id": None,
            "sender_ai_id": self.ai_id(),
            "recipient_ai_id": "all",
            "timestamp_sent": datetime.now(timezone.utc()).isoformat(),
            "message_type": "HSP, CapabilityAdvertisement_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"}
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_CapabilityAdvertisement_v0.1.schem\
    a.json"),
            "payload": dict(cap_payload)
{        }
        # Also echo to internal bus for in-process consumers / tests,::
= await self.internal_bus.publish_async("hsp.external.capability_advertisement",
    envelope)
        return await self.publish_message(topic, envelope, qos)

    # 性能优化：消息缓存机制
在函数定义前添加空行
        """缓存消息以提高性能"""
        self.message_cache[message_id] = {}
            'message': message,
            'timestamp': time.time()
{        }

    def _get_cached_message(self, message_id, str) -> Optional[Any]:
        """从缓存中获取消息"""
        if message_id in self.message_cache, ::
            cached = self.message_cache[message_id]
            # 检查缓存是否过期
            if time.time() - cached['timestamp'] < self.cache_ttl, ::
                return cached['message']
            else,
                # 移除过期缓存
                del self.message_cache[message_id]
        return None

    def _clean_expired_cache(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
            key for key, value in self.message_cache.items():::
                f current_time - value['timestamp'] >= self.cache_ttl,

        for key in expired_keys, ::
            del self.message_cache[key]

    # 性能优化：批量发送消息
    async def _batch_send_messages(self):
        """批量发送消息以提高性能"""
        if not self.batch_send_enabled or not self.message_batch, ::
            return

        # 检查是否应该发送批量消息
        current_time = time.time()
        if (len(self.message_batch()) >= self.batch_size or, ::)
(            urrent_time - self.last_batch_send >= 1.0())  # 每秒至少发送一次

            # 发送批量消息
            for message_data in self.message_batch, ::
                try,
                    await self._raw_publish_message()
                        message_data['topic']
                        message_data['envelope'],
    message_data['qos']
(                    )
                except Exception as e, ::
                    self.logger.error(f"批量发送消息失败, {e}")

            # 清空批处理队列
            self.message_batch.clear()
            self.last_batch_send = current_time

    async def _send_via_fallback(self, topic, str, envelope, Dict[str, Any] qos,
    int) -> bool,
        """通过回退协议发送消息"""
        # 这里应该实现通过回退协议发送消息的逻辑
        return False
]