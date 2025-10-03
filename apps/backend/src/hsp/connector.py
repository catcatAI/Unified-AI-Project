import json # Added for JSON serialization
from .external.external_connector import ExternalConnector


from .internal.internal_bus import InternalBus
from .bridge.data_aligner import DataAligner
from .bridge.message_bridge import MessageBridge
from unittest.mock import MagicMock, AsyncMock # Added for mock mode
from .types import HSPMessageEnvelope, HSPFactPayload, HSPCapabilityAdvertisementPayload, HSPTaskRequestPayload, HSPTaskResultPayload, HSPAcknowledgementPayload, HSPOpinionPayload, HSPQoSParameters
from ..core.hsp.types import HSPErrorDetails
import uuid # Added for UUID generation
from datetime import datetime, timezone # Added for timestamp generation
import asyncio # Added for asyncio.iscoroutinefunction
import logging

# Type alias for Future with HSPAcknowledgementPayload result
AckFuture = asyncio.Future[HSPAcknowledgementPayload]
import time
# 修复导入路径 - 使用正确的模块路径
from ..core.shared.error import HSPConnectionError # Added for unified error handling
from pathlib import Path

# 添加缺失的导入
from typing import Optional, Dict, Any, List, Callable
from ..core.hsp.performance_optimizer import HSPPerformanceOptimizer, HSPPerformanceEnhancer
from ..core.hsp.network_resilience import RetryPolicy, CircuitBreaker
from ..core.hsp.fallback.fallback_protocols import MessagePriority, FallbackMessage
from ..core.hsp.utils.fallback_config_loader import get_config_loader
from ..core.hsp.fallback.fallback_manager import get_fallback_manager

# 定义logger
logger = logging.getLogger(__name__)
import os # Added this import

# Define the base path for schemas, ensuring cross-platform compatibility
SCHEMA_BASE_PATH = Path(__file__).resolve.parent.parent.parent / "schemas"

def get_schema_uri(schema_name: str) -> str:
    """Constructs a file URI for a given schema name.""":
    schema_path = SCHEMA_BASE_PATH / schema_name
    if not schema_path.is_file:
        # Fallback for when running in a different environment (like tests)
    # This makes the path relative to the current working directory
    # In a real-world scenario, a more robust solution might be needed
    # like using an environment variable or a configuration setting.
    project_root = Path.cwd
    schema_path = project_root / "apps" / "backend" / "schemas" / schema_name
        if not schema_path.is_file:
             # As a last resort, return a placeholder if the file isn't found
             # This prevents crashes but signals a configuration issue.
             logger.warning(f"Schema file not found: {schema_name}. Path was: {schema_path}")
             return f"file:///{schema_name}_not_found"
    return str(schema_path.as_uri)

class HSPConnector:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int = 1883, mock_mode: bool = False, mock_mqtt_client: Optional[MagicMock] = None, internal_bus: Optional[InternalBus] = None, message_bridge: Optional[MessageBridge] = None, enable_fallback: bool = True, **kwargs) -> None:
    self.ai_id = ai_id
    self.mock_mode = mock_mode
    self.broker_address = broker_address
    self.broker_port = broker_port
    self.enable_fallback = enable_fallback
    self.fallback_manager = None
    self.fallback_initialized = False
    self.logger = logging.getLogger(__name__)
    self.hsp_available = False  # Track HSP availability
    self._is_connected = False  # Initialize _is_connected attribute

    # 性能优化参数
    self.message_cache: Dict[str, Any] = {}  # 消息缓存
    self.cache_ttl = 300  # 缓存有效期（秒）
    self.batch_send_enabled = True  # 批量发送
    self.batch_size = 10  # 批量大小
    self.message_batch: List[Dict[str, Any]] = []  # 消息批处理队列
    self.last_batch_send = time.time()  # 上次批量发送时间

    # 性能优化器
    self.performance_optimizer = HSPPerformanceOptimizer
    self.performance_enhancer = HSPPerformanceEnhancer(self.performance_optimizer)

        if self.mock_mode:


    self.logger.info("HSPConnector: Initializing in mock mode.")
            self.logger.debug(f"HSPConnector.__init__ - ai_id: {ai_id}, mock_mode: {mock_mode}")
            self.external_connector = MagicMock(spec=ExternalConnector)
            self.external_connector.ai_id = ai_id # Ensure mock has ai_id
            self.external_connector.connect.return_value = True
            self.external_connector.disconnect.return_value = True
            self.external_connector.subscribe.return_value = True
            self.external_connector.unsubscribe.return_value = True
            self.external_connector.publish = AsyncMock(return_value=True) # Explicitly set return value for publish
            # Explicitly mock mqtt_client and its publish method
            if mock_mqtt_client:

    self.external_connector.mqtt_client = mock_mqtt_client
            else:

                mock_mqtt_client_instance = MagicMock
                mock_mqtt_client_instance.publish = AsyncMock(return_value=True)
                self.external_connector.mqtt_client = mock_mqtt_client_instance

            self.is_connected = True # Considered connected in mock mode
            self.hsp_available = True  # Mock mode considers HSP available
        else:

            self.external_connector = ExternalConnector(
                ai_id=ai_id,
                broker_address=broker_address,
                broker_port=broker_port,
                )
            self.is_connected = False # Actual connection status
            self.hsp_available = False

        if internal_bus is None:


    self.internal_bus = InternalBus
        else:

            self.internal_bus = internal_bus

    self.data_aligner = DataAligner # DataAligner can be unique per connector

        if message_bridge is None:


    self.message_bridge = MessageBridge(
                self.external_connector,
                self.internal_bus,
                self.data_aligner
            )
        else:

            self.message_bridge = message_bridge

        # Callbacks for different message types
    self._fact_callbacks = []
    self._opinion_callbacks = []  # 添加这一行
    self._capability_advertisement_callbacks = []
    self._task_request_callbacks = []
    self._task_result_callbacks = []
        self._acknowledgement_callbacks = []  # New for incoming ACKs
    self._connect_callbacks = []
    self._disconnect_callbacks = []

    self._pending_acks: Dict[str, AckFuture] = {}  # New To track messages awaiting ACK
        self._message_retry_counts: Dict[str, int] = {}  # New To track retry counts for messages
    self.ack_timeout_sec = 10 # New Default timeout for ACK
    self.max_ack_retries = 3 # New Max retries for messages requiring ACK
    self.retry_policy = RetryPolicy(max_attempts=self.max_ack_retries, backoff_factor=2, max_delay=60) # Initialize retry policy
    self.circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=300) # Initialize circuit breaker
    self._capability_provider_callback: Optional[Callable[, List[HSPCapabilityAdvertisementPayload]]] = None # New Callback to get capabilities

        # Initialize fallback protocols if enabled
    # Moved to connect method to ensure event loop is running

        # Register internal message bridge handler for external messages
    def sync_handle_external_message(topic, message)
            """同步包装器，用于处理异步handle_external_message"""
            if self.message_bridge:

    asyncio.create_task(self.message_bridge.handle_external_message(topic, message))

        if hasattr(self.external_connector, 'on_message_callback')


    self.external_connector.on_message_callback = self.performance_enhancer.enhance_receive(sync_handle_external_message)

    # Subscribe to internal bus messages that are results from external
        def sync_handle_internal_message(message)
            """同步包装器，用于处理异步handle_internal_message"""
            if self.message_bridge:

    asyncio.create_task(self.message_bridge.handle_internal_message(message))

    self.internal_bus.subscribe("hsp.internal.message", sync_handle_internal_message)

    # Subscribe to internal bus messages that are results from external
        def sync_dispatch_fact(message)
            """同步包装器，用于处理异步_dispatch_fact_to_callbacks"""
            asyncio.create_task(self._dispatch_fact_to_callbacks(message))

        def sync_dispatch_opinion(message)
            """同步包装器，用于处理异步_dispatch_opinion_to_callbacks"""
            asyncio.create_task(self._dispatch_opinion_to_callbacks(message))

        def sync_dispatch_capability(message)
            """同步包装器，用于处理异步_dispatch_capability_advertisement_to_callbacks"""
            asyncio.create_task(self._dispatch_capability_advertisement_to_callbacks(message))

        def sync_dispatch_task_request(message)
            """同步包装器，用于处理异步_dispatch_task_request_to_callbacks"""
            asyncio.create_task(self._dispatch_task_request_to_callbacks(message))

        def sync_dispatch_task_result(message)
            """同步包装器，用于处理异步_dispatch_task_result_to_callbacks"""
            asyncio.create_task(self._dispatch_task_result_to_callbacks(message))

        def sync_dispatch_ack(message)
            """同步包装器，用于处理异步_dispatch_acknowledgement_to_callbacks"""
            asyncio.create_task(self._dispatch_acknowledgement_to_callbacks(message))

    self.internal_bus.subscribe("hsp.external.fact", sync_dispatch_fact)
    self.internal_bus.subscribe("hsp.external.opinion", sync_dispatch_opinion)
    self.internal_bus.subscribe("hsp.external.capability_advertisement", sync_dispatch_capability)
    self.internal_bus.subscribe("hsp.external.task_request", sync_dispatch_task_request)
    self.internal_bus.subscribe("hsp.external.task_result", sync_dispatch_task_result)
    self.internal_bus.subscribe("hsp.external.acknowledgement", sync_dispatch_ack)

    # --- Test compatibility properties ---
    @property
    def default_qos(self)
        """Default QoS level for test compatibility.""":
    return 1

    @property
    def mqtt_client(self)
        """Provides access to the underlying MQTT client for test compatibility.""":
    return self.external_connector.mqtt_client

    @mqtt_client.setter
    def mqtt_client(self, value)
    """Allows tests to set the mock MQTT client."""
    self.external_connector.mqtt_client = value

    @property
    def subscribed_topics(self)
        """Provides access to subscribed topics for test compatibility.""":
    return getattr(self.external_connector, 'subscribed_topics', set)

    @property
    def on_message(self)
        """Provides message callback for test compatibility."""
    # Tests expect signature on_message(client, topic, payload, qos, properties)
    # MessageBridge.handle_external_message expects handle_external_message(topic, message)
        async def test_compatible_on_message(client, topic, payload, qos, properties) -> None:
            topic_str = topic.decode if isinstance(topic, (bytes, bytearray)) else topic:
    payload_str = payload.decode if isinstance(payload, (bytes, bytearray)) else payload:
    if self.external_connector.on_message_callback is not None:

    _ = await self.external_connector.on_message_callback(topic_str, payload_str)
    return test_compatible_on_message

    @on_message.setter
    def on_message(self, callback)
        """Allows setting message callback for test compatibility."""
    # Wrap a test-provided callback (client, topic, payload, qos, properties)
        async def wrapper(topic, message)
    _ = await callback(None, topic, message, 1, None)
    self.external_connector.on_message_callback = wrapper

    # --- Backward compatibility methods ---
    def on_fact_received(self, callback)
        """Backward compatibility method for registering fact callbacks.""":
    self.register_on_fact_callback(callback)

    def on_command_received(self, callback)
        """Backward compatibility method for registering command callbacks (maps to task_request).""":
    self.register_on_task_request_callback(callback)

    def on_connect_callback(self, callback)
        """Backward compatibility method for registering connect callbacks.""" :
    self.register_on_connect_callback(callback)

    def on_disconnect_callback(self, callback)
        """Backward compatibility method for registering disconnect callbacks.""":
    self.register_on_disconnect_callback(callback)

    async def mqtt_subscribe(self, topic: str, qos: int = 1)
        """Direct MQTT subscription for test compatibility.""":

    async def close(self)
    """Disconnects the external connector and cleans up resources."""
    self.logger.info("HSPConnector: Disconnecting external connector...")
        if self.external_connector and hasattr(self.external_connector, 'disconnect')

    try:


                _ = await self.external_connector.disconnect
                self.logger.info("HSPConnector: External connector disconnected.")
            except Exception as e:

                self.logger.error(f"HSPConnector: Error during external connector disconnect: {e}")

        if self.fallback_manager:


    try:



                _ = await self.fallback_manager.shutdown
                self.logger.info("HSPConnector: Fallback manager shut down.")
            except Exception as e:

                self.logger.error(f"HSPConnector: Error during fallback manager shutdown: {e}")

    self.is_connected = False
    self.hsp_available = False

    async def _run_in_event_loop(self, coro)
    """
    在事件循环中安全地运行协程

    Args:
            coro: 要运行的协程

    Returns:
            协程的结果
    """
    # 获取或创建事件循环
        try:

            loop = asyncio.get_event_loop
        except RuntimeError:

            loop = asyncio.new_event_loop
            asyncio.set_event_loop(loop)

    # 运行协程
        if loop.is_running:
            # 如果事件循环正在运行，创建任务
            task = loop.create_task(coro)
            # 等待任务完成
            return await task
        else:
            # 否则运行直到完成
            return await loop.run_until_complete(coro)

    async def connect(self)
    if self.mock_mode:

    self.logger.info("HSPConnector: Mock connect successful.")
            self.is_connected = True
            self.hsp_available = True
            if self.enable_fallback:
                # 在事件循环中初始化fallback协议
                _ = await self._run_in_event_loop(self._initialize_fallback_protocols)
            # In mock mode, explicitly subscribe to relevant topics on the mock MQTT client
            _ = await self.external_connector.subscribe("hsp/knowledge/facts/#", self.external_connector.on_message_callback)
            _ = await self.external_connector.subscribe("hsp/capabilities/advertisements/#", self.external_connector.on_message_callback)
            _ = await self.external_connector.subscribe(f"hsp/requests/{self.ai_id}", self.external_connector.on_message_callback)
            _ = await self.external_connector.subscribe(f"hsp/results/{self.ai_id}", self.external_connector.on_message_callback)
            # Set up the mock broker to use our on_message_callback
            if hasattr(self.external_connector, 'mqtt_client') and self.external_connector.mqtt_client:

    self.external_connector.mqtt_client.on_message_callback = self.external_connector.on_message_callback
                # Set up connect/disconnect callbacks
                self.external_connector.mqtt_client.on_connect_callback = self._handle_mock_connect
                self.external_connector.mqtt_client.on_disconnect_callback = self._handle_mock_disconnect
        else:

            for attempt in range(3)


    try:



                    self.logger.info(f"Attempting to connect to HSP... (Attempt {attempt + 1}/3)")
                    _ = await self.external_connector.connect
                    self.is_connected = self.external_connector.is_connected
                    self.hsp_available = self.is_connected
                    if self.is_connected:

    self.logger.info("HSP connection successful.")
                        if self.enable_fallback:
                            # 在事件循环中初始化fallback协议
                            _ = await self._run_in_event_loop(self._initialize_fallback_protocols)
                        break  # Exit loop on successful connection
                except Exception as e:

                    self.logger.error(f"HSP connection attempt {attempt + 1} failed: {e}")
                    if attempt == 2:

    _ = await self._handle_hsp_connection_error(e, attempt + 1)
                    else:

                        self.logger.warning(f"HSP connection attempt {attempt + 1} failed: {e}. Retrying...")
                        _ = await asyncio.sleep(2 ** attempt)  # Exponential backoff

            # If still not connected after retries, ensure fallback is initialized
            if not self.is_connected and self.enable_fallback:
                # 在事件循环中初始化fallback协议
                _ = await self._run_in_event_loop(self._initialize_fallback_protocols)

    # 处理连接回调
        for callback in self._connect_callbacks:

    if asyncio.iscoroutinefunction(callback)


    _ = await self._run_in_event_loop(callback)
            else:

                callback

    # New Perform post-connection synchronization
    _ = await self._run_in_event_loop(self._post_connect_synchronization)

    async def disconnect(self)
    if self.mock_mode:

    self.logger.info("HSPConnector: Mock disconnect successful.")
            self.is_connected = False
        else:

            try:


                _ = await self.external_connector.disconnect
            except Exception as e:

                self.logger.warning(f"HSPConnector: external disconnect raised (likely already closed) {e}")
            finally:
                # Reflect underlying state or force false
                try:

                    self.is_connected = bool(getattr(self.external_connector, 'is_connected', False))
                except Exception:

                    self.is_connected = False

        if self.fallback_manager and self.fallback_initialized:


    try:



                _ = await self.fallback_manager.shutdown
            except Exception as e:

                self.logger.warning(f"HSPConnector: fallback shutdown error: {e}")
            finally:
                self.fallback_initialized = False

    # 处理断开连接回调
        for callback in self._disconnect_callbacks:

    try:


                if asyncio.iscoroutinefunction(callback)



    _ = await self._run_in_event_loop(callback)
                else:

                    callback
            except Exception as e:

                self.logger.warning(f"HSPConnector: disconnect callback error: {e}")

    async def _handle_mock_connect(self)
    """Handle mock connection event."""
    self.is_connected = True
    # 处理连接回调
        for callback in self._connect_callbacks:

    if asyncio.iscoroutinefunction(callback)


    _ = await self._run_in_event_loop(callback)
            else:

                callback

    async def _handle_mock_disconnect(self)
    """Handle mock disconnection event."""
    self.is_connected = False
    # 处理断开连接回调
        for callback in self._disconnect_callbacks:

    try:


                if asyncio.iscoroutinefunction(callback)



    _ = await self._run_in_event_loop(callback)
                else:

                    callback
            except Exception as e:

                self.logger.warning(f"HSPConnector: disconnect callback error: {e}")

            try:


                if asyncio.iscoroutinefunction(callback)



    _ = await self._run_in_event_loop(callback)
                else:

                    callback
            except Exception as e:

                self.logger.warning(f"HSPConnector: disconnect callback error: {e}")

    # 性能优化：消息缓存机制
    def _cache_message(self, message_id: str, message: Any)
    """缓存消息以提高性能"""
    self.message_cache[message_id] = {
            'message': message,
            'timestamp': time.time
    }

    def _get_cached_message(self, message_id: str) -> Optional[Any]:
    """从缓存中获取消息"""
        if message_id in self.message_cache:

    cached = self.message_cache[message_id]
            # 检查缓存是否过期
            if time.time - cached['timestamp'] < self.cache_ttl:

    return cached['message']
            else:
                # 移除过期缓存
                del self.message_cache[message_id]
    return None

    def _clean_expired_cache(self)
    """清理过期缓存"""
    current_time = time.time
    expired_keys = [
            key for key, value in self.message_cache.items:
    if current_time - value['timestamp'] >= self.cache_ttl
    ]
        for key in expired_keys:

    del self.message_cache[key]

    # 性能优化：批量发送消息
    async def _batch_send_messages(self)
    """批量发送消息以提高性能"""
        if not self.batch_send_enabled or not self.message_batch:

    return

    # 检查是否应该发送批量消息
    current_time = time.time
        if (len(self.message_batch) >= self.batch_size or :

    current_time - self.last_batch_send >= 1.0):  # 每秒至少发送一次

            # 发送批量消息
            for message_data in self.message_batch:

    try:


                    await self._raw_publish_message(
                        message_data['topic'],
                        message_data['envelope'],
                        message_data['qos']
                    )
                except Exception as e:

                    self.logger.error(f"批量发送消息失败: {e}")

            # 清空批处理队列
            self.message_batch.clear
            self.last_batch_send = current_time

    async def publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
    print(f"DEBUG: publish_message called. topic: {topic}, envelope: {envelope}")
    logging.info(f"HSPConnector: publish_message called. self.external_connector.publish is {type(self.external_connector.publish)}")

    message_id = envelope.get("message_id")
        correlation_id = envelope.get("correlation_id") or message_id # Use message_id if correlation_id is not set
    qos_params = envelope.get("qos_parameters") or
    requires_ack = qos_params.get("requires_ack", False)

        # Track if this is a retry to prevent infinite recursion
    # 使用消息ID作为键来存储重试信息，而不是直接修改envelope
    message_id = envelope.get("message_id", "")
    is_retry = getattr(self, f"_is_retry_{message_id}", False)
    retry_count_in_envelope = getattr(self, f"_retry_count_{message_id}", 0)

    # If ACK is required, set up tracking
        if requires_ack:
            # Create a future to track the ACK
            ack_future: Optional[AckFuture] = asyncio.Future
            self._pending_acks[correlation_id] = ack_future

            # Track retry count for main publishing
    if correlation_id not in self._message_retry_counts:

    self._message_retry_counts[correlation_id] = 0
            # Track fallback retry count separately
    if f"{correlation_id}_fallback" not in self._message_retry_counts:

    self._message_retry_counts[f"{correlation_id}_fallback"] = 0
        else:

            ack_future = None  # type Optional[AckFuture]

    # Try to publish the message with retries
    try:
            # Apply retry policy as a decorator
    retry_decorated_publish = self.retry_policy(self._raw_publish_message)
            result = await retry_decorated_publish(topic, envelope, qos)

            # If ACK is required, wait for it
    if requires_ack and result and ack_future is not None:

    try:
                    # Wait for ACK with timeout
    await asyncio.wait_for(ack_future, timeout=self.ack_timeout_sec)  # type ignore
                    print(f"DEBUG: ACK received for message {message_id}")
                    # Clean up tracking
                    self._pending_acks.pop(correlation_id, None)
                    self._message_retry_counts.pop(correlation_id, None)
                    # Also clean up fallback retry count
    self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                    return True
                except asyncio.TimeoutError:

                    print(f"DEBUG: ACK timeout for message {message_id}")
                    # Handle retry logic only if this is not already a retry beyond max retries
    if retry_count_in_envelope < self.max_ack_retries:

    retry_count = self._message_retry_counts.get(correlation_id, 0)
                        if retry_count < self.max_ack_retries:

    print(f"DEBUG: Retrying message {message_id}, attempt {retry_count + 1}")
                            self._message_retry_counts[correlation_id] = retry_count + 1
                            # 使用属性存储重试信息，而不是直接修改envelope
                            setattr(self, f"_is_retry_{message_id}", True)
                            setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                            return await self.publish_message(topic, envelope, qos)
                        else:

                            print(f"DEBUG: Max retries exceeded for message {message_id}")
                            # Clean up tracking
                            self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            # Try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Trying fallback for message {message_id}")
    fallback_result = await self._send_via_fallback(topic, envelope, qos)
                                return fallback_result
                            return False
                    else:
                        # This is already beyond max retries, so we shouldn't retry again
    print(f"DEBUG: Already exceeded max retries for message {message_id}, not retrying again")
                        # Clean up tracking
                        self._pending_acks.pop(correlation_id, None)
                        self._message_retry_counts.pop(correlation_id, None)
                        # Try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Trying fallback for message {message_id}")
                            # Initialize fallback retry count if not already set
    if f"{correlation_id}_fallback" not in self._message_retry_counts:

    self._message_retry_counts[f"{correlation_id}_fallback"] = 0

                            fallback_result = await self._send_via_fallback(topic, envelope, qos)
                            # Handle fallback retries for messages that have not exceeded fallback retry limit
                            # Only retry fallback if we haven't exceeded the fallback retry limit
    current_fallback_retry_count = self._message_retry_counts.get(f"{correlation_id}_fallback", 0)
                            if not fallback_result and current_fallback_retry_count < self.max_ack_retries:

    print(f"DEBUG: Fallback failed, retrying fallback for message {message_id}, attempt {current_fallback_retry_count + 1}")
    self._message_retry_counts[f"{correlation_id}_fallback"] = current_fallback_retry_count + 1
                                # Clean up for recursive call
    self._pending_acks.pop(correlation_id, None)
                                self._message_retry_counts.pop(correlation_id, None)
                                # Retry through recursive call with fallback retry count
                                # 使用属性存储重试信息，而不是直接修改envelope
                                setattr(self, f"_is_retry_{message_id}", True)
                                # 使用属性存储重试信息，而不是直接修改envelope
                                setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                                return await self.publish_message(topic, envelope, qos)
                            elif fallback_result:
                                # Success - clean up tracking
                                self._pending_acks.pop(correlation_id, None)
                                self._message_retry_counts.pop(correlation_id, None)
                                self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                                return True
                            else:

                                print(f"DEBUG: Max fallback retries exceeded for message {message_id}")
                                # Clean up tracking
                                self._pending_acks.pop(correlation_id, None)
                                self._message_retry_counts.pop(correlation_id, None)
                                self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                                return False
                        return False
            elif requires_ack and not result:
                # Publishing failed, handle retries first only if this is not already beyond max retries
    if retry_count_in_envelope < self.max_ack_retries:

    retry_count = self._message_retry_counts.get(correlation_id, 0)
                    if retry_count < self.max_ack_retries:

    print(f"DEBUG: Publishing failed, retrying message {message_id}, attempt {retry_count + 1}")
                        self._message_retry_counts[correlation_id] = retry_count + 1
                        # 使用属性存储重试信息，而不是直接修改envelope
                        setattr(self, f"_is_retry_{message_id}", True)
                        setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                        return await self.publish_message(topic, envelope, qos)
                    else:

                        print(f"DEBUG: Max retries exceeded for message {message_id}")
                        # Clean up tracking
                        self._pending_acks.pop(correlation_id, None)
                        self._message_retry_counts.pop(correlation_id, None)
                        # Try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Trying fallback for message {message_id}")
                            # Initialize fallback retry count if not already set
    if f"{correlation_id}_fallback" not in self._message_retry_counts:

    self._message_retry_counts[f"{correlation_id}_fallback"] = 0

                            fallback_result = await self._send_via_fallback(topic, envelope, qos)
                            # Handle fallback retries for messages that have not exceeded fallback retry limit
                            # Only retry fallback if we haven't exceeded the fallback retry limit
    current_fallback_retry_count = self._message_retry_counts.get(f"{correlation_id}_fallback", 0)
                            if not fallback_result and current_fallback_retry_count < self.max_ack_retries:

    print(f"DEBUG: Fallback failed, retrying fallback for message {message_id}, attempt {current_fallback_retry_count + 1}")
    self._message_retry_counts[f"{correlation_id}_fallback"] = current_fallback_retry_count + 1
                                # Clean up for recursive call
    self._pending_acks.pop(correlation_id, None)
                                self._message_retry_counts.pop(correlation_id, None)
                                # Retry through recursive call with fallback retry count
                                # 使用属性存储重试信息，而不是直接修改envelope
                                setattr(self, f"_is_retry_{message_id}", True)
                                # 使用属性存储重试信息，而不是直接修改envelope
                                setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                                return await self.publish_message(topic, envelope, qos)
                            elif fallback_result:
                                # Success - clean up tracking
                                self._pending_acks.pop(correlation_id, None)
                                self._message_retry_counts.pop(correlation_id, None)
                                self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                                return True
                            else:

                                print(f"DEBUG: Max fallback retries exceeded for message {message_id}")
                                # Clean up tracking
                                self._pending_acks.pop(correlation_id, None)
                                self._message_retry_counts.pop(correlation_id, None)
                                self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                                return False
                        return False
                else:
                    # This is already beyond max retries, so we shouldn't retry again
    print(f"DEBUG: Already exceeded max retries for message {message_id}, not retrying again")
                    # Clean up tracking
                    self._pending_acks.pop(correlation_id, None)
                    self._message_retry_counts.pop(correlation_id, None)
                    # Try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Trying fallback for message {message_id}")
                        # Initialize fallback retry count if not already set
    if f"{correlation_id}_fallback" not in self._message_retry_counts:

    self._message_retry_counts[f"{correlation_id}_fallback"] = 0

                        fallback_result = await self._send_via_fallback(topic, envelope, qos)
                        # Handle fallback retries for messages that have not exceeded fallback retry limit
                        # Only retry fallback if we haven't exceeded the fallback retry limit
    current_fallback_retry_count = self._message_retry_counts.get(f"{correlation_id}_fallback", 0)
                        if not fallback_result and current_fallback_retry_count < self.max_ack_retries:

    print(f"DEBUG: Fallback failed, retrying fallback for message {message_id}, attempt {current_fallback_retry_count + 1}")
    self._message_retry_counts[f"{correlation_id}_fallback"] = current_fallback_retry_count + 1
                            # Clean up for recursive call
    self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            # Retry through recursive call with fallback retry count
                            # 使用属性存储重试信息，而不是直接修改envelope
                            setattr(self, f"_is_retry_{message_id}", True)
                            setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                            return await self.publish_message(topic, envelope, qos)
                        elif fallback_result:
                            # Success - clean up tracking
                            self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                            return True
                        else:

                            print(f"DEBUG: Max fallback retries exceeded for message {message_id}")
                            # Clean up tracking
                            self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                            return False
                    return False
            else:
                # No ACK required, return result directly
                return result
        except Exception as e:

            self.logger.error(f"Error in publish_message: {e}", exc_info=True)
            print(f"DEBUG: Error in publish_message: {e}")
            # Handle retries first only if this is not already beyond max retries
    if requires_ack and retry_count_in_envelope < self.max_ack_retries:

    retry_count = self._message_retry_counts.get(correlation_id, 0)
                if retry_count < self.max_ack_retries:

    print(f"DEBUG: Error occurred, retrying message {message_id}, attempt {retry_count + 1}")
                    self._message_retry_counts[correlation_id] = retry_count + 1
                    # 使用属性存储重试信息，而不是直接修改envelope
                    setattr(self, f"_is_retry_{message_id}", True)
                    setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                    return await self.publish_message(topic, envelope, qos)
                else:

                    print(f"DEBUG: Max retries exceeded for message {message_id}")
                    # Clean up tracking
                    self._pending_acks.pop(correlation_id, None)
                    self._message_retry_counts.pop(correlation_id, None)
                    # Try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Trying fallback for message {message_id}")
    fallback_result = await self._send_via_fallback(topic, envelope, qos)
                        # Handle fallback retries for messages that have not exceeded fallback retry limit
                        # Only retry fallback if we haven't exceeded the fallback retry limit
    current_fallback_retry_count = self._message_retry_counts.get(f"{correlation_id}_fallback", 0)
                        if not fallback_result and current_fallback_retry_count < self.max_ack_retries:

    print(f"DEBUG: Fallback failed, retrying fallback for message {message_id}, attempt {current_fallback_retry_count + 1}")
    self._message_retry_counts[f"{correlation_id}_fallback"] = current_fallback_retry_count + 1
                            # Clean up for recursive call
    self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            # Retry through recursive call with fallback retry count
                            # 使用属性存储重试信息，而不是直接修改envelope
                            setattr(self, f"_is_retry_{message_id}", True)
                            setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                            return await self.publish_message(topic, envelope, qos)
                        elif fallback_result:
                            # Success - clean up tracking
                            self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                            return True
                        else:

                            print(f"DEBUG: Max fallback retries exceeded for message {message_id}")
                            # Clean up tracking
                            self._pending_acks.pop(correlation_id, None)
                            self._message_retry_counts.pop(correlation_id, None)
                            self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                            return False
                    return False
            elif requires_ack and retry_count_in_envelope >= self.max_ack_retries:
                # This is already beyond max retries, so we shouldn't retry again
    print(f"DEBUG: Already exceeded max retries for message {message_id}, not retrying again after error")
                # Clean up tracking
                self._pending_acks.pop(correlation_id, None)
                self._message_retry_counts.pop(correlation_id, None)
                # Try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Trying fallback for message {message_id}")
                    # Initialize fallback retry count if not already set
    if f"{correlation_id}_fallback" not in self._message_retry_counts:

    self._message_retry_counts[f"{correlation_id}_fallback"] = 0

                    fallback_result = await self._send_via_fallback(topic, envelope, qos)
                    # Handle fallback retries for messages that have not exceeded fallback retry limit
                    # Only retry fallback if we haven't exceeded the fallback retry limit
    current_fallback_retry_count = self._message_retry_counts.get(f"{correlation_id}_fallback", 0)
                    if not fallback_result and current_fallback_retry_count < self.max_ack_retries:

    print(f"DEBUG: Fallback failed, retrying fallback for message {message_id}, attempt {current_fallback_retry_count + 1}")
    self._message_retry_counts[f"{correlation_id}_fallback"] = current_fallback_retry_count + 1
                        # Clean up for recursive call
    self._pending_acks.pop(correlation_id, None)
                        self._message_retry_counts.pop(correlation_id, None)
                        # Retry through recursive call with fallback retry count
                        # 使用属性存储重试信息，而不是直接修改envelope
                        setattr(self, f"_is_retry_{message_id}", True)
                        # 使用属性存储重试信息，而不是直接修改envelope
                        setattr(self, f"_retry_count_{message_id}", retry_count_in_envelope + 1)
                        return await self.publish_message(topic, envelope, qos)
                    elif fallback_result:
                        # Success - clean up tracking
                        self._pending_acks.pop(correlation_id, None)
                        self._message_retry_counts.pop(correlation_id, None)
                        self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                        return True
                    else:

                        print(f"DEBUG: Max fallback retries exceeded for message {message_id}")
                        # Clean up tracking
                        self._pending_acks.pop(correlation_id, None)
                        self._message_retry_counts.pop(correlation_id, None)
                        self._message_retry_counts.pop(f"{correlation_id}_fallback", None)
                        return False
                return False
            else:
                # No ACK required, try fallback if enabled
    if self.enable_fallback and self.fallback_manager:

    print(f"DEBUG: Error occurred, trying fallback for message {message_id}")
    fallback_result = await self._send_via_fallback(topic, envelope, qos)
                    return fallback_result
                return False

    async def publish_fact(self, fact_payload: HSPFactPayload, topic: str, qos: int = 1) -> bool:
    """
    发布事实消息

    Args:
            fact_payload: 事实载荷
            topic: 发布主题
            qos: 服务质量等级

    Returns: bool 发布是否成功
    """
    envelope: HSPMessageEnvelope = {  # type ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": "all",
            "timestamp_sent": datetime.now(timezone.utc).isoformat,
            "message_type": "HSP::Fact_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_Fact_v0.1.schema.json"),
            "payload": dict(fact_payload)
    }
    print(f"DEBUG: HSPConnector.publish_fact - Publishing to topic: {topic}")
    result = await self.publish_message(topic, envelope, qos)
    print(f"DEBUG: HSPConnector.publish_fact - Publish result: {result}")
    return result

    async def publish_opinion(self, opinion_payload: HSPOpinionPayload, topic: str, qos: int = 1) -> bool:
    """
    发布观点消息

    Args:
            opinion_payload: 观点载荷
            topic: 发布主题
            qos: 服务质量等级

    Returns: bool 发布是否成功
    """
    envelope: HSPMessageEnvelope = {  # type ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": "all",
            "timestamp_sent": datetime.now(timezone.utc).isoformat,
            "message_type": "HSP::Opinion_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_Opinion_v0.1.schema.json"),
            "payload": dict(opinion_payload)
    }
    return await self.publish_message(topic, envelope, qos)

    def _create_envelope(
    self,
    message_type: str,
    payload: Dict[str, Any],
    payload_schema_uri: Optional[str] = None,
    recipient_ai_id: str = "all",
    communication_pattern: str = "publish",
    qos_parameters: Optional[HSPQoSParameters] = None
    ) -> HSPMessageEnvelope:
    """
    Creates an HSP message envelope with standard fields.:

    Args:
    message_type: The type of message (e.g., "HSP::Fact").
            payload: The message payload.
            payload_schema_uri: URI to the payload schema.
            recipient_ai_id: The recipient AI ID (default: "all").
            communication_pattern: The communication pattern (default: "publish").
            qos_parameters: Quality of service parameters.

    Returns:
            HSPMessageEnvelope: The created envelope.
    """
    envelope: HSPMessageEnvelope = {
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": recipient_ai_id,
            "timestamp_sent": datetime.now(timezone.utc).isoformat,
            "message_type": message_type,
            "protocol_version": self.version_manager.current_version,
            "communication_pattern": communication_pattern,
            "security_parameters": None,
            "qos_parameters": qos_parameters or {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": payload_schema_uri,
            "payload": payload
    }
    return envelope

    async def _raw_publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
        """Internal method for raw message publishing prioritizing mqtt_client.publish for tests, with fallback to external_connector.publish.""":
    try:

    payload_str = json.dumps(envelope)
            print(f"DEBUG: _raw_publish_message - topic: {topic}, envelope: {envelope}")
            # Access mqtt_client correctly via property which handles external_connector access
            mqtt_client = self.mqtt_client
            print(f"DEBUG: _raw_publish_message - mqtt_client: {mqtt_client}")
            print(f"DEBUG: _raw_publish_message - hasattr(mqtt_client, 'publish') {hasattr(mqtt_client, 'publish')}")
            if mqtt_client and hasattr(mqtt_client, 'publish')
                # 确保publish方法是可等待的
                print(f"DEBUG: _raw_publish_message - Using mqtt_client.publish")
                if asyncio.iscoroutinefunction(mqtt_client.publish)

    print(f"DEBUG: _raw_publish_message - mqtt_client.publish is coroutine function")
                    result = await mqtt_client.publish(topic, payload_str, qos=qos)
                else:

                    print(f"DEBUG: _raw_publish_message - mqtt_client.publish is not coroutine function")
                    # For synchronous publish methods, run in thread pool to avoid blocking
                    loop = asyncio.get_event_loop
                    result = await loop.run_in_executor(None, mqtt_client.publish, topic, payload_str, qos)
                self.logger.debug(f"Published message via mqtt_client.publish: {topic}")
                print(f"DEBUG: Published message via mqtt_client.publish: {topic}")
                return True
            elif hasattr(self.external_connector, 'publish')
                # Fallback to external_connector.publish if mqtt_client is not available
    print(f"DEBUG: _raw_publish_message - Using external_connector.publish")
                if asyncio.iscoroutinefunction(self.external_connector.publish)

    result = await self.external_connector.publish(topic, payload_str, qos=qos)
                else:
                    # For synchronous publish methods, run in thread pool to avoid blocking
                    loop = asyncio.get_event_loop
                    result = await loop.run_in_executor(None, self.external_connector.publish, topic, payload_str, qos)
                self.logger.debug(f"Published message via external_connector.publish: {topic}")
                print(f"DEBUG: Published message via external_connector.publish: {topic}")
                return True
            else:

                self.logger.error("No publish method available in mqtt_client or external_connector")
                print("DEBUG: No publish method available in mqtt_client or external_connector")
                return False
        except Exception as e:

            self.logger.error(f"Error in _raw_publish_message: {e}", exc_info=True)
            print(f"DEBUG: Error in _raw_publish_message: {e}")
            return False

    async def send_task_request(self, payload: HSPTaskRequestPayload, target_ai_id_or_topic: str, qos: int = 1) -> Optional[str]:
    correlation_id = str(uuid.uuid4)
    envelope: HSPMessageEnvelope = { #type ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4),
            "correlation_id": correlation_id,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": payload.get("target_ai_id", target_ai_id_or_topic) or "unknown",
            "timestamp_sent": datetime.now(timezone.utc).isoformat,
            "message_type": "HSP::TaskRequest_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "request",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": True, "priority": "high"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_TaskRequest_v0.1.schema.json"),
            "payload": dict(payload)
    }
        # The topic for task requests is usually hsp/requests/{recipient_ai_id}
    # If target_ai_id_or_topic is a topic, use it directly.
    # Otherwise, construct the topic.
        mqtt_topic = target_ai_id_or_topic if "/" in target_ai_id_or_topic else f"hsp/requests/{target_ai_id_or_topic}":

    success = await self.publish_message(mqtt_topic, envelope, qos)
        return correlation_id if success else None
    async def send_task_result(self, payload: HSPTaskResultPayload, target_ai_id_or_topic: str, correlation_id: str, qos: int = 1) -> bool:
    envelope: HSPMessageEnvelope = { #type ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4),
            "correlation_id": correlation_id,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": payload.get("requester_ai_id", target_ai_id_or_topic),
            "timestamp_sent": datetime.now(timezone.utc).isoformat,
            "message_type": "HSP::TaskResult_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "response",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "high"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_TaskResult_v0.1.schema.json"),
            "payload": dict(payload)
    }
        mqtt_topic = target_ai_id_or_topic if "/" in target_ai_id_or_topic else f"hsp/results/{target_ai_id_or_topic}":
    return await self.publish_message(mqtt_topic, envelope, qos)

    async def publish_capability_advertisement(self, cap_payload: HSPCapabilityAdvertisementPayload, qos: int = 1)
    topic = f"hsp/capabilities/advertisements/{self.ai_id}" # Specific topic for this AI's capabilities
    envelope: HSPMessageEnvelope = { #type ignore
            "hsp_envelope_version": "0.1",
            "message_id": str(uuid.uuid4),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": "all",
            "timestamp_sent": datetime.now(timezone.utc).isoformat,
            "message_type": "HSP::CapabilityAdvertisement_v0.1",
            "protocol_version": "0.1",
            "communication_pattern": "publish",
            "security_parameters": None,
            "qos_parameters": {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": get_schema_uri("HSP_CapabilityAdvertisement_v0.1.schema.json"),
            "payload": dict(cap_payload)
    }
        # Also echo to internal bus for in-process consumers/tests
    _ = await self.internal_bus.publish_async("hsp.external.capability_advertisement", envelope)
    return await self.publish_message(topic, envelope, qos)

    # --- Registration methods for external modules to receive specific message types ---
    def register_on_fact_callback(self, callback: Callable[[HSPFactPayload, str, HSPMessageEnvelope], None])
    self.logger.debug(f"Registering on_fact_callback: {callback}")
    print(f"DEBUG: HSPConnector.register_on_fact_callback - Callback: {callback}")
    self._fact_callbacks.append(callback)

    def register_on_opinion_callback(self, callback: Callable[[HSPOpinionPayload, str, HSPMessageEnvelope], None])
    self.logger.debug(f"Registering on_opinion_callback: {callback}")
    self._opinion_callbacks.append(callback)

    def register_on_capability_advertisement_callback(self, callback: Callable[[HSPCapabilityAdvertisementPayload, str, HSPMessageEnvelope], None])
    self.logger.debug(f"Registering on_capability_advertisement_callback: {callback}")
    self._capability_advertisement_callbacks.append(callback)

    def register_on_task_request_callback(self, callback: Callable[[HSPTaskRequestPayload, str, HSPMessageEnvelope], None])
    self._task_request_callbacks.append(callback)

    def register_on_task_result_callback(self, callback: Callable[[HSPTaskResultPayload, str, HSPMessageEnvelope], None])
    self._task_result_callbacks.append(callback)

    def register_on_connect_callback(self, callback: Callable[, None])
    self._connect_callbacks.append(callback)

    def register_on_disconnect_callback(self, callback: Callable[, None])
    self._disconnect_callbacks.append(callback)

    def register_on_acknowledgement_callback(self, callback: Callable[[HSPAcknowledgementPayload, str, HSPMessageEnvelope], None])
    self._acknowledgement_callbacks.append(callback)

    def register_capability_provider(self, callback: Callable[, List[HSPCapabilityAdvertisementPayload]])
    """Registers a callback function that provides the AI's current capabilities."""
    self._capability_provider_callback = callback

    async def advertise_capability(self, capability: HSPCapabilityAdvertisementPayload)
    """Publishes a capability advertisement."""
    _ = await self.publish_capability_advertisement(capability)

    async def _handle_hsp_connection_error(self, error: Exception, attempt: int)
    """统一 HSP 连接错误处理机制"""
    error_message = f"HSP connection error (attempt {attempt}) {error}"
    self.logger.error(error_message)
    raise HSPConnectionError(error_message)

    # 添加subscribe_to_facts方法
    async def subscribe_to_facts(self, callback: Callable[[HSPFactPayload, str, HSPMessageEnvelope], None])
    """订阅事实消息"""
    self.register_on_fact_callback(callback)
    # 订阅事实主题
    _ = await self.subscribe("hsp/knowledge/facts/#")

    async def subscribe_to_opinions(self, callback: Callable[[HSPOpinionPayload, str, HSPMessageEnvelope], None])
    """订阅观点消息"""
    self.register_on_opinion_callback(callback)
    # 订阅观点主题
    _ = await self.subscribe("hsp/knowledge/opinions/#")

    async def subscribe(self, topic: str, qos: int = 1)
    """
    Subscribe to a topic.

    Args:
            topic: The topic to subscribe to
            qos: Quality of Service level (default: 1)
    """
        if self.mock_mode:
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector, 'subscribed_topics')

    self.external_connector.subscribed_topics = set
            self.external_connector.subscribed_topics.add(topic)
            # Also call the mock subscribe method
            if hasattr(self.external_connector, 'subscribe')
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe)

    _ = await self.external_connector.subscribe(topic, qos)
                else:
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)
        else:

            if hasattr(self.external_connector, 'subscribe')
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe)

    _ = await self.external_connector.subscribe(topic, qos)
                else:
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)

    # --- Internal dispatch methods ---
    async def _dispatch_fact_to_callbacks(self, message: Dict[str, Any])
    # message here is the full envelope from the internal bus
    payload = message.get("payload")
    sender_ai_id = message.get("sender_ai_id")

    self.logger.debug(f"Dispatching fact to {len(self._fact_callbacks)} callbacks. Message: {message}")
    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Dispatching fact to {len(self._fact_callbacks)} callbacks. Message: {message}")
    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - _fact_callbacks: {self._fact_callbacks}")
    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - payload: {payload}")
    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - sender_ai_id: {sender_ai_id}")

        if payload and sender_ai_id:


    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Creating HSPFactPayload")
            try:

                fact_payload = HSPFactPayload(**payload)
                print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - fact_payload created: {fact_payload}")
            except Exception as e:

                print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Error creating HSPFactPayload: {e}")
                import traceback
                traceback.print_exc
                return

            print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Iterating through {len(self._fact_callbacks)} callbacks")
            for i, callback in enumerate(self._fact_callbacks)

    self.logger.debug(f"Calling on_fact_callback #{i} {callback}")
                print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Calling on_fact_callback #{i} {callback}")
                if asyncio.iscoroutinefunction(callback)

    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Callback #{i} is coroutine function")
                    try:

                        _ = await callback(fact_payload, sender_ai_id, message)
                        print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Callback #{i} completed successfully")
                    except Exception as e:

                        print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Error in callback #{i} {e}")
                        import traceback
                        traceback.print_exc
                else:

                    print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Callback #{i} is regular function")
                    try:

                        callback(fact_payload, sender_ai_id, message)
                        print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Callback #{i} completed successfully")
                    except Exception as e:

                        print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Error in callback #{i} {e}")
                        import traceback
                        traceback.print_exc
            print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - Finished calling {len(self._fact_callbacks)} callbacks")
        else:

            print(f"DEBUG: HSPConnector._dispatch_fact_to_callbacks - payload or sender_ai_id is None/empty")

        # Check if ACK is required and send it
    qos_params = message.get("qos_parameters")
        if qos_params and qos_params.get("requires_ack")

    ack_payload: HSPAcknowledgementPayload = {
                "status": "received",
                "ack_timestamp": datetime.now(timezone.utc).isoformat,
                "target_message_id": message.get("message_id", "")
            }
            ack_envelope: HSPMessageEnvelope = {
                "hsp_envelope_version": "0.1",
                "message_id": str(uuid.uuid4),
                "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                "sender_ai_id": self.ai_id,
                "recipient_ai_id": sender_ai_id or "unknown",
                "timestamp_sent": datetime.now(timezone.utc).isoformat,
                "message_type": "HSP::Acknowledgement_v0.1",
                "protocol_version": "0.1",
                "communication_pattern": "acknowledgement",
                "security_parameters": None,
                "qos_parameters": {"requires_ack": False, "priority": "low"},
                "routing_info": None,
                "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                "payload": dict(ack_payload)
            }
            # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
    ack_topic = f"hsp/acks/{sender_ai_id or 'unknown'}"
            await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_opinion_to_callbacks(self, message: Dict[str, Any])
    payload = message.get("payload")
    sender_ai_id = message.get("sender_ai_id")

    self.logger.debug(f"Dispatching opinion to {len(self._opinion_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:


    opinion_payload = HSPOpinionPayload(**payload)
            for callback in self._opinion_callbacks:

    self.logger.debug(f"Calling on_opinion_callback: {callback}")
                if asyncio.iscoroutinefunction(callback)

    _ = await callback(opinion_payload, sender_ai_id, message)
                else:

                    callback(opinion_payload, sender_ai_id, message)

            # Check if ACK is required and send it
    qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack")

    ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat,
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat,
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": dict(ack_payload)
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
    ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_capability_advertisement_to_callbacks(self, message: Dict[str, Any])
    payload = message.get("payload")
    sender_ai_id = message.get("sender_ai_id")

    self.logger.debug(f"Dispatching capability advertisement to {len(self._capability_advertisement_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:


    cap_payload = HSPCapabilityAdvertisementPayload(**payload)
            for callback in self._capability_advertisement_callbacks:

    self.logger.debug(f"Calling on_capability_advertisement_callback: {callback}")
                if asyncio.iscoroutinefunction(callback)

    _ = await callback(cap_payload, sender_ai_id, message)
                else:

                    callback(cap_payload, sender_ai_id, message)

            # Check if ACK is required and send it
    qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack")

    ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat,
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat,
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": dict(ack_payload)
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
    ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_task_request_to_callbacks(self, message: Dict[str, Any])
    payload = message.get("payload")
    sender_ai_id = message.get("sender_ai_id")

    self.logger.debug(f"Dispatching task request to {len(self._task_request_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:


    task_request_payload = HSPTaskRequestPayload(**payload)
            for callback in self._task_request_callbacks:

    self.logger.debug(f"Calling on_task_request_callback: {callback}")
                if asyncio.iscoroutinefunction(callback)

    _ = await callback(task_request_payload, sender_ai_id, message)
                else:

                    callback(task_request_payload, sender_ai_id, message)

            # Check if ACK is required and send it
    qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack")

    ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat,
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat,
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": dict(ack_payload)
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
    ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any])
    payload = message.get("payload")
    sender_ai_id = message.get("sender_ai_id")

    self.logger.debug(f"Dispatching task result to {len(self._task_result_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:


    task_result_payload = HSPTaskResultPayload(**payload)
            for callback in self._task_result_callbacks:

    self.logger.debug(f"Calling on_task_result_callback: {callback}")
                if asyncio.iscoroutinefunction(callback)

    _ = await callback(task_result_payload, sender_ai_id, message)
                else:

                    callback(task_result_payload, sender_ai_id, message)

            # Check if ACK is required and send it
    qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack")

    ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc).isoformat,
                    "target_message_id": message.get("message_id", "")
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4),
                    "correlation_id": message.get("message_id"),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc).isoformat,
                    "message_type": "HSP::Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": dict(ack_payload)
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
    ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_acknowledgement_to_callbacks(self, message: Dict[str, Any])
    payload = message.get("payload")
    sender_ai_id = message.get("sender_ai_id")

    self.logger.debug(f"Dispatching acknowledgement to {len(self._acknowledgement_callbacks)} callbacks. Message: {message}")

        if payload and sender_ai_id:


    ack_payload = HSPAcknowledgementPayload(**payload)
            target_message_id = ack_payload.get("target_message_id")
            correlation_id = message.get("correlation_id")

            # Resolve pending ACK if any
            # Use correlation_id to match with pending ACKs
    if correlation_id and correlation_id in self._pending_acks:

    ack_future = self._pending_acks[correlation_id]
                if not ack_future.done:

    ack_future.set_result(ack_payload)
                    self.logger.debug(f"Resolved pending ACK for correlation_id: {correlation_id}")
                    # Clean up tracking
                    self._pending_acks.pop(correlation_id, None)
                    self._message_retry_counts.pop(correlation_id, None)
                    # Also clean up fallback retry count
    self._message_retry_counts.pop(f"{correlation_id}_fallback", None)

            for callback in self._acknowledgement_callbacks:


    self.logger.debug(f"Calling on_acknowledgement_callback: {callback}")
                if asyncio.iscoroutinefunction(callback)

    _ = await callback(ack_payload, sender_ai_id, message)
                else:

                    callback(ack_payload, sender_ai_id, message)

    def unsubscribe(self, topic: str, callback: Optional[Callable[[str], None]] = None)
    if callback is None:
            # Direct MQTT unsubscribe compatibility (best-effort in mock)
            if self.mock_mode and hasattr(self.external_connector, 'subscribed_topics')

    self.external_connector.subscribed_topics.discard(topic)
            # If external connector has unsubscribe, call it
            if hasattr(self.external_connector, 'unsubscribe')

    try:


                    self.external_connector.unsubscribe(topic)
                except Exception:

                    pass
        else:

            self.internal_bus.unsubscribe(f"hsp.external.{topic}", callback)

    # --- Properties ---
    @property
    def is_connected(self) -> bool:
    return self._is_connected

    @is_connected.setter
    def is_connected(self, value: bool)
    self._is_connected = value

    # --- Fallback Protocol Methods ---
    async def _initialize_fallback_protocols(self)
    """
    Initializes the fallback communication protocols based on the configuration.
    This is called when the primary HSP connector fails to connect.
    """
        if not self.enable_fallback:

    return

    try
            # Load fallback configuration
    config_loader = get_config_loader
            if not config_loader.is_fallback_enabled:

    self.logger.info("Fallback protocols disabled in configuration")
                return

            fallback_config = config_loader.get_fallback_config
            message_config = fallback_config.get("message", )

            # Set logging level for fallback protocols
    logging_config = fallback_config.get("logging", )
            if logging_config.get("level")

    fallback_logger = logging.getLogger("src.hsp.fallback")
                fallback_logger.setLevel(getattr(logging, logging_config["level"]))

            self.fallback_manager = get_fallback_manager

            # Initialize protocols with the loaded configuration
    success = await self._initialize_protocols_with_config(fallback_config)

            if success and self.fallback_manager:


    self.fallback_initialized = True
                # Register a handler for incoming fallback messages
    if self.fallback_manager:

    for item in self.fallback_manager.protocols:


    if isinstance(item, tuple) and len(item) == 2:



    _, protocol = item
                            protocol.register_handler("hsp_message", self._handle_fallback_message)

                # Set the health check interval for the fallback manager
    health_interval = message_config.get("health_check_interval", 30)
                self.fallback_manager.health_check_interval = health_interval

                self.logger.info("Fallback protocols initialized successfully with configuration")
    else:

    self.logger.error("Failed to initialize fallback protocols")
        except Exception as e:

            self.logger.error(f"Error initializing fallback protocols: {e}")

    async def _initialize_protocols_with_config(self, config: Dict[str, Any]) -> bool:
    """
    Initializes the individual fallback protocols based on the provided configuration.
    """
        try:

            from .fallback.fallback_protocols import InMemoryProtocol, FileBasedProtocol, HTTPProtocol

            protocols_config = config.get("protocols", )

            # Initialize in-memory protocol
            memory_config = protocols_config.get("memory", )
            if memory_config.get("enabled", True) and self.fallback_manager:

    memory_protocol = InMemoryProtocol
                priority = memory_config.get("priority", 1)
                self.fallback_manager.add_protocol(memory_protocol, priority=priority)
                self.logger.debug(f"Added memory protocol with priority {priority}")

            # Initialize file-based protocol
            file_config = protocols_config.get("file", )
            if file_config.get("enabled", True) and self.fallback_manager:

    base_path = file_config.get("base_path", "data/fallback_comm")
                file_protocol = FileBasedProtocol(base_path=base_path)
                priority = file_config.get("priority", 2)
                self.fallback_manager.add_protocol(file_protocol, priority=priority)
                self.logger.debug(f"Added file protocol with priority {priority}")

            # Initialize HTTP protocol
            http_config = protocols_config.get("http", )
            if http_config.get("enabled", True) and self.fallback_manager:

    host = http_config.get("host", "127.0.0.1")
                # Check TESTING env var here as well
                port = 0 if os.environ.get('TESTING') == 'true' else http_config.get("port", 8765)
    http_protocol = HTTPProtocol(host=host, port=port)
                priority = http_config.get("priority", 3)
                self.fallback_manager.add_protocol(http_protocol, priority=priority)
                self.logger.debug(f"Added HTTP protocol with priority {priority}")

            # Initialize and start the fallback manager
            if self.fallback_manager:

    if await self.fallback_manager.initialize:
    _ = await self.fallback_manager.start
                    return True
                else:

                    return False
            else:

                return False

        except Exception as e:


            self.logger.error(f"Error initializing protocols with config: {e}")
            return False

    async def _send_via_fallback(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
    """
    Sends a message using the fallback communication protocols.
    """
        if not self.fallback_manager:

    return False

        try:
            # Determine the message priority
            priority = MessagePriority.NORMAL
            qos_params = envelope.get("qos_parameters")
            if qos_params:

    if qos >= 2:
    priority = MessagePriority.HIGH
                elif qos_params.get("priority") == "high":

    priority = MessagePriority.HIGH
                elif qos_params.get("priority") == "low":

    priority = MessagePriority.LOW

            # Create a fallback message
            fallback_msg = FallbackMessage(
                id=envelope["message_id"],
                sender_id=envelope["sender_ai_id"],
                recipient_id=envelope["recipient_ai_id"],
                message_type="hsp_message",
                payload={
                    "topic": topic,
                    "envelope": envelope,
                    "qos": qos
                },
                timestamp=time.time,
                priority=priority,
                correlation_id=envelope.get("correlation_id")
            )

            success = await self.fallback_manager.send_message(
                fallback_msg.recipient_id,
                fallback_msg.message_type,
                fallback_msg.payload,
                priority=fallback_msg.priority,
                correlation_id=fallback_msg.correlation_id
            )

            if success:


    self.logger.debug(f"Message sent via fallback: {envelope['message_id']}")
            else:

                self.logger.error(f"Failed to send message via fallback: {envelope['message_id']}")

            return success

        except Exception as e:


            self.logger.error(f"Error sending via fallback: {e}")
            return False

    async def _handle_fallback_message(self, message: FallbackMessage)
    """
    Handles a message received from a fallback protocol.
    """
        try:

            payload = message.payload
            if payload.get("envelope")

    envelope = payload["envelope"]
                # Route the message to the internal bus, as if it was received from HSP
    await self.message_bridge.handle_external_message(
                    payload.get("topic", ""),
                    json.dumps(envelope)
                )
                self.logger.debug(f"Processed fallback message: {message.id}")
        except Exception as e:

            self.logger.error(f"Error handling fallback message: {e}")

    def get_communication_status(self) -> Dict[str, Any]:
    """
    Returns the current communication status.
    """
    status = {
            "hsp_available": self.hsp_available,
            "is_connected": self.is_connected,
            "fallback_enabled": self.enable_fallback,
            "fallback_initialized": self.fallback_initialized
    }

        if self.fallback_manager:


    status["fallback_status"] = self.fallback_manager.get_status

    return status

    async def health_check(self) -> Dict[str, Any]:
    """健康检查"""
    health = {
            "hsp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False
    }

    # 检查HSP健康状态
        if self.hsp_available and self.is_connected:

    try:
                # 可以添加实际的健康检查逻辑
                health["hsp_healthy"] = True
            except:
                health["hsp_healthy"] = False
                self.hsp_available = False

    # 检查fallback健康状态
        if self.fallback_manager:

    try:


                fallback_status = self.fallback_manager.get_status
                health["fallback_healthy"] = fallback_status.get("active_protocol") is not None
            except:
                health["fallback_healthy"] = False

    health["overall_healthy"] = health["hsp_healthy"] or health["fallback_healthy"]
    return health

    async def _post_connect_synchronization(self)
    """Performs synchronization tasks after a successful connection."""
    self.logger.info("Performing post-connection synchronization...")

    # 1. Re-advertise Capabilities
        if self._capability_provider_callback:

    try:


                capabilities = self._capability_provider_callback
                for cap in capabilities:

    _ = await self.publish_capability_advertisement(cap)
                self.logger.info(f"Re-advertised {len(capabilities)} capabilities.")
            except Exception as e:

                self.logger.error(f"Error re-advertising capabilities: {e}")
        else:

            self.logger.warning("No capability provider registered. Cannot re-advertise capabilities.")
            # 在测试环境中，如果我们没有能力提供者回调，尝试手动广告能力
            # 这是为了确保测试中的代理能够正确广告其能力
            if hasattr(self, '_test_capabilities')

    test_capabilities = getattr(self, '_test_capabilities', )
                if test_capabilities:

    for cap in test_capabilities:


    _ = await self.publish_capability_advertisement(cap)
                    self.logger.info(f"Manually advertised {len(test_capabilities)} test capabilities.")

    # 2. (Future) Re-publish important facts or request state updates
    # This would involve more complex logic, potentially interacting with the HAMMemoryManager
    # or a dedicated state synchronization module.
    self.logger.info("Post-connection synchronization complete.")

    async def _handle_fact_message(self, fact_message: Dict[str, Any], sender_ai_id: Optional[str] = None, full_envelope: Optional[Dict[str, Any]] = None)
    """
    Handle a fact message.

    Args:
            fact_message: The fact message to handle.
            sender_ai_id: The sender AI ID (optional for compatibility).:
    full_envelope: The full message envelope (optional for compatibility).
    """
    # Dispatch the fact message to callbacks
    _ = await self._dispatch_fact_to_callbacks(fact_message)

    async def _handle_opinion_message(self, opinion_message: Dict[str, Any], sender_ai_id: Optional[str] = None, full_envelope: Optional[Dict[str, Any]] = None)
    """
    Handle an opinion message.

    Args:
            opinion_message: The opinion message to handle.
            sender_ai_id: The sender AI ID (optional for compatibility).:
    full_envelope: The full message envelope (optional for compatibility).
    """
        # Dispatch the opinion message to callbacks (treated as facts for now)
    _ = await self._dispatch_opinion_to_callbacks(opinion_message)