import asyncio
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from core.system.config.magic_numbers import cache_value, threshold_value, timeout_value

# from .retry_policy import RetryPolicy
# from .circuit_breaker import CircuitBreaker
from shared.network_resilience import (
    CircuitBreaker,
    RetryPolicy,
)
from typing_extensions import Literal

from .advanced_performance_optimizer import (
    HSPAdvancedPerformanceEnhancer,
    HSPAdvancedPerformanceOptimizer,
)
from .bridge.data_aligner import DataAligner
from .bridge.message_bridge import MessageBridge
from .extensibility import HSPExtensionManager, HSPMessageRegistry
from .external.external_connector import ExternalConnector
from .fallback.fallback_protocols import (
    FileBasedProtocol,
    HTTPProtocol,
    InMemoryProtocol,
)
from .internal.internal_bus import InternalBus
from .performance_optimizer import HSPPerformanceEnhancer, HSPPerformanceOptimizer
from .security import HSPSecurityContext, HSPSecurityManager
from .types import (
    HSPAcknowledgementPayload,
    HSPCapabilityAdvertisementPayload,
    HSPMessageEnvelope,
    HSPOpinionPayload,
    HSPQoSParameters,
    HSPTaskResultPayload,
)
from .versioning import HSPVersionConverter, HSPVersionManager

# 條件導入 unittest.mock，只在測試模式下導入
if os.environ.get("TEST_MODE") or os.environ.get("TESTING"):
    from unittest.mock import AsyncMock, MagicMock
else:
    # 在非測試模式下定義佔位符類
    class MagicMock:
        """占位符 MagicMock 類，在非測試模式下使用"""

        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name) -> str:
            """Execute the   getattr   operation."""
            return MagicMock()

        def __call__(self, *args, **kwargs) -> str:
            """Execute the   call   operation."""
            return MagicMock()

    class AsyncMock:
        """占位符 AsyncMock 類，在非測試模式下使用"""

        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name) -> str:
            """Execute the   getattr   operation."""
            return AsyncMock()

        async def __call__(self, *args, **kwargs) -> None:
            """Execute the   call   operation."""
            return None


# Define logger
logger = logging.getLogger(__name__)


# Define the base path for schemas, ensuring cross-platform compatibility
SCHEMA_BASE_PATH = Path(__file__).resolve().parent.parent.parent / "schemas"

# =============================================================================
# ANGELA-MATRIX: [L4] [δ] [A] [L6+]
# Max-size bound for unbounded message batch collection
# =============================================================================
_MAX_MESSAGE_BATCH = 1000


def get_schema_uri(schema_name: str) -> str:
    """Constructs a file URI for a given schema name."""
    schema_path = SCHEMA_BASE_PATH / schema_name
    if not schema_path.is_file():
        # Fallback for when running in a different environment (like tests):
        # This makes the path relative to the current working directory
        # In a real-world scenario, a more robust solution might be needed
        # like using an environment variable or a configuration setting.
        logger.warning(
            f"Schema file not found: {schema_name}. Path was: {schema_path}", exc_info=True
        )
        return f"file:///{schema_name}_not_found"
    return schema_path.as_uri()


class HSPConnector:
    def __init__(
        self,
        ai_id: str,
        mock_mode: bool = False,
        broker_address: str = "localhost",
        broker_port: int = 1883,
        mock_mqtt_client: Optional[MagicMock] = None,
        internal_bus: Optional[InternalBus] = None,
        message_bridge: Optional[MessageBridge] = None,
        enable_fallback: bool = True,
        **kwargs,
    ) -> None:
        self._load_config(ai_id, mock_mode, broker_address, broker_port, enable_fallback)
        self._init_plugin_system()
        self._init_protocols(
            ai_id, broker_address, broker_port, mock_mqtt_client, internal_bus, message_bridge
        )
        self._register_default_hooks(**kwargs)

    def _load_config(
        self,
        ai_id: str,
        mock_mode: bool,
        broker_address: str,
        broker_port: int,
        enable_fallback: bool,
    ) -> None:
        self.ai_id = ai_id
        self.mock_mode = mock_mode
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.enable_fallback = enable_fallback
        self.fallback_manager = None
        self.fallback_initialized = False
        self.logger = logging.getLogger(__name__)
        self.hsp_available = False
        self._is_connected = False

        self._task_semaphore = threading.Semaphore(100)
        self._max_concurrent_tasks = 100
        self._pending_tasks: set = set()

    def _init_plugin_system(self) -> None:
        self.message_cache: Dict[str, Any] = {}
        self.cache_ttl = cache_value("hsp_cache_ttl", 300)
        self.batch_send_enabled = True
        self.batch_size = 10
        self.message_batch: List[Dict[str, Any]] = []
        self.last_batch_send = time.time()

        self.performance_optimizer = HSPPerformanceOptimizer()
        self.performance_enhancer = HSPPerformanceEnhancer(self.performance_optimizer)

        self.security_manager = HSPSecurityManager()
        self.security_context = HSPSecurityContext(self.security_manager)

        self.advanced_performance_optimizer = HSPAdvancedPerformanceOptimizer()
        self.advanced_performance_enhancer = HSPAdvancedPerformanceEnhancer(
            self.advanced_performance_optimizer
        )

        self.extension_manager = HSPExtensionManager()
        self.message_registry = HSPMessageRegistry()

        self.version_manager = HSPVersionManager()
        self.version_converter = HSPVersionConverter(self.version_manager)

    def _init_protocols(
        self,
        ai_id: str,
        broker_address: str,
        broker_port: int,
        mock_mqtt_client: Optional[MagicMock],
        internal_bus: Optional[InternalBus],
        message_bridge: Optional[MessageBridge],
    ) -> None:
        if self.mock_mode:
            self.logger.info("HSPConnector: Initializing in mock mode.")
            self.logger.debug(
                f"HSPConnector.__init__ - ai_id: {ai_id}, mock_mode: {self.mock_mode}"
            )
            self.external_connector = MagicMock()
            self.external_connector.ai_id = ai_id
            self.external_connector.connect.return_value = True
            self.external_connector.disconnect.return_value = True
            self.external_connector.subscribe.return_value = True
            self.external_connector.unsubscribe.return_value = True
            self.external_connector.publish = AsyncMock(return_value=True)
            if mock_mqtt_client:
                self.external_connector.mqtt_client = mock_mqtt_client
            else:
                mock_mqtt_client_instance = MagicMock()
                mock_mqtt_client_instance.publish = AsyncMock(return_value=True)
                self.external_connector.mqtt_client = mock_mqtt_client_instance
            self.is_connected = True
            self.hsp_available = True
        else:
            self.external_connector = ExternalConnector(
                ai_id=ai_id, broker_address=broker_address, broker_port=broker_port
            )
            self.is_connected = False
            self.hsp_available = False

        if internal_bus is None:
            self.internal_bus = InternalBus()
        else:
            self.internal_bus = internal_bus

        self.data_aligner = DataAligner()

        if message_bridge is None:
            self.message_bridge = MessageBridge(
                self.external_connector, self.internal_bus, self.data_aligner
            )
        else:
            self.message_bridge = message_bridge

    def _register_default_hooks(self, **kwargs) -> None:
        self._fact_callbacks = []
        self._capability_advertisement_callbacks = []
        self._task_request_callbacks = []
        self._task_result_callbacks = []
        self._acknowledgement_callbacks = []
        self._connect_callbacks = []
        self._disconnect_callbacks = []

        self._pending_acks: Dict[str, asyncio.Future[Any]] = {}
        self._message_retry_counts: Dict[str, int] = {}
        self.ack_timeout_sec = kwargs.get("ack_timeout_sec", 3)
        self.max_ack_retries = kwargs.get("max_ack_retries", 2)
        self.retry_policy = RetryPolicy(max_retries=self.max_ack_retries, backoff_factor=2)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=int(threshold_value("hsp_failure_threshold", 5)),
            recovery_timeout=timeout_value("hsp_recovery_timeout", 300.0),
        )

        self._capability_provider_callback: Optional[
            Callable[[], List[HSPCapabilityAdvertisementPayload]]
        ] = None

        callback = self.performance_enhancer.enhance_receive(
            self.message_bridge.handle_external_message
        )
        if callable(callback):
            self.external_connector.on_message_callback = cast(Callable, callback)

        self.internal_bus.subscribe("hsp.internal.message", self._handle_internal_message)

        self.internal_bus.subscribe("hsp.external.fact", self._dispatch_fact_to_callbacks_sync)
        self.internal_bus.subscribe(
            "hsp.external.capability_advertisement",
            self._dispatch_capability_advertisement_to_callbacks_sync,
        )
        self.internal_bus.subscribe(
            "hsp.external.task_request", self._dispatch_task_request_to_callbacks_sync
        )
        self.internal_bus.subscribe(
            "hsp.external.task_result", self._dispatch_task_result_to_callbacks_sync
        )
        self.internal_bus.subscribe(
            "hsp.external.acknowledgement",
            self._dispatch_acknowledgement_to_callbacks_sync,
        )

    def _run_bounded_task(self, coro_factory) -> None:
        """Run an async coroutine with bounded concurrency."""
        if not self._task_semaphore.acquire(blocking=False):
            self.logger.warning(
                "Dropping task: too many pending HSP tasks (%s)", self._max_concurrent_tasks
            )
            return

        async def _run():
            try:
                await coro_factory()
            finally:
                self._task_semaphore.release()

        task = asyncio.create_task(_run())
        self._pending_tasks.add(task)
        task.add_done_callback(
            lambda t: (
                self._pending_tasks.discard(t),
                (
                    self.logger.warning("HSP bounded task failed: %s", t.exception())
                    if not t.cancelled() and t.exception()
                    else None
                ),
            )
        )

    def _handle_internal_message(self, message: Any) -> None:
        """处理内部消息的同步包装器"""
        self._run_bounded_task(lambda: self.message_bridge.handle_internal_message(message))

    def _dispatch_fact_to_callbacks_sync(self, message: Any) -> None:
        """同步包装器用于分发事实消息到回调"""
        self._run_bounded_task(lambda: self._dispatch_fact_to_callbacks(message))

    def _dispatch_capability_advertisement_to_callbacks_sync(self, message: Any) -> None:
        """同步包装器用于分发能力广告消息到回调"""
        self._run_bounded_task(
            lambda: self._dispatch_capability_advertisement_to_callbacks(message)
        )

    def _dispatch_task_request_to_callbacks_sync(self, message: Any) -> None:
        """同步包装器用于分发任务请求消息到回调"""
        self._run_bounded_task(lambda: self._dispatch_task_request_to_callbacks(message))

    def _dispatch_task_result_to_callbacks_sync(self, message: Any) -> None:
        """同步包装器用于分发任务结果消息到回调"""
        self._run_bounded_task(lambda: self._dispatch_task_result_to_callbacks(message))

    def _dispatch_acknowledgement_to_callbacks_sync(self, message: Any) -> None:
        """同步包装器用于分发确认消息到回调"""
        self._run_bounded_task(lambda: self._dispatch_acknowledgement_to_callbacks(message))

    async def _dispatch_fact_to_callbacks(self, message: Any) -> None:
        """异步分发事实消息到回调"""
        for callback in self._fact_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except (
                Exception
            ) as e:  # broad exception acceptable: callback execution may raise various runtime errors
                self.logger.error(f"Error in fact callback: {e}", exc_info=True)

    async def _dispatch_capability_advertisement_to_callbacks(self, message: Any) -> None:
        """异步分发能力广告消息到回调"""
        for callback in self._capability_advertisement_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except (
                Exception
            ) as e:  # broad exception acceptable: callback execution may raise various runtime errors
                self.logger.error(f"Error in capability advertisement callback: {e}", exc_info=True)

    async def _dispatch_task_request_to_callbacks(self, message: Any) -> None:
        """异步分发任务请求消息到回调"""
        for callback in self._task_request_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
            except (
                Exception
            ) as e:  # broad exception acceptable: callback execution may raise various runtime errors
                self.logger.error(f"Error in task request callback: {e}", exc_info=True)

    # - - - Test compatibility properties - - -
    @property
    def qos(self) -> int:
        """Default QoS level for test compatibility."""
        return 1

    @property
    def mqtt_client(self):
        """Provides access to the underlying MQTT client for test compatibility."""
        return self.external_connector.mqtt_client

    @mqtt_client.setter
    def mqtt_client(self, value) -> None:
        """Allows tests to set the mock MQTT client."""
        self.external_connector.mqtt_client = value

    async def connect(self) -> bool:
        """Connect to the HSP network."""
        if hasattr(self, "external_connector") and hasattr(self.external_connector, "connect"):
            success = await self.external_connector.connect()
            self.is_connected = success
            return success
        self.is_connected = True
        return True

    @property
    def subscribed_topics(self) -> set:
        """Provides access to subscribed topics for test compatibility."""
        return getattr(self.external_connector, "subscribed_topics", set())

    @property
    def on_message(self) -> Callable:
        """Provides message callback for test compatibility."""

        # Tests expect signature on_message(client, topic, payload, qos, properties)
        # MessageBridge.handle_external_message expects handle_external_message(topic, message)
        async def test_compatible_on_message(client, topic, payload, qos, properties) -> None:
            """Execute the test compatible on message operation."""
            topic_str = topic.decode() if isinstance(topic, (bytes, bytearray)) else topic
            payload_str = payload.decode() if isinstance(payload, (bytes, bytearray)) else payload
            # 直接调用回调函数而不是创建任务
            if self.external_connector.on_message_callback:
                await self.external_connector.on_message_callback(topic_str, payload_str)

        return test_compatible_on_message

    @on_message.setter
    def on_message(self, callback: Callable) -> None:
        """Allows setting message callback for test compatibility."""

        # Wrap a test-provided callback (client, topic, payload, qos, properties)
        async def wrapper(topic: str, message: str) -> None:
            """Wrap the decorated function."""
            await callback(None, topic, message, 1, None)

        self.external_connector.on_message_callback = cast(Callable, wrapper)

    def register_on_fact_callback(self, callback: Callable) -> None:
        """注册事实消息回调"""
        self._fact_callbacks.append(callback)

    def register_on_capability_advertisement_callback(self, callback: Callable) -> None:
        """注册能力广告消息回调"""
        self._capability_advertisement_callbacks.append(callback)

    def register_on_task_request_callback(self, callback: Callable) -> None:
        """注册任务请求消息回调"""
        self._task_request_callbacks.append(callback)

    def register_on_task_result_callback(self, callback: Callable) -> None:
        """注册任务结果消息回调"""
        self._task_result_callbacks.append(callback)

    def register_on_acknowledgement_callback(self, callback: Callable) -> None:
        """注册确认消息回调"""
        self._acknowledgement_callbacks.append(callback)

    def register_on_connect_callback(self, callback: Callable) -> None:
        """注册连接回调"""
        self._connect_callbacks.append(callback)

    def register_on_disconnect_callback(self, callback: Callable) -> None:
        """注册断开连接回调"""
        self._disconnect_callbacks.append(callback)

    # - - - Backward compatibility methods -
    def on_fact_received(self, callback: Callable) -> None:
        """Backward compatibility method for registering fact callbacks."""
        self.register_on_fact_callback(callback)

    def on_command_received(self, callback: Callable) -> None:
        """Backward compatibility method for registering command callbacks (maps to task_request)."""
        self.register_on_task_request_callback(callback)

    def on_connect_callback(self, callback: Callable) -> None:
        """Backward compatibility method for registering connect callbacks."""
        self.register_on_connect_callback(callback)

    def on_disconnect_callback(self, callback: Callable) -> None:
        """Backward compatibility method for registering disconnect callbacks."""
        self.register_on_disconnect_callback(callback)

    async def mqtt_subscribe(self, topic: str, qos: int = 1) -> None:
        """Direct MQTT subscription for test compatibility."""
        if self.mock_mode:
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector, "subscribed_topics"):
                self.external_connector.subscribed_topics = set()
            self.external_connector.subscribed_topics.add(topic)
            # Also call the mock subscribe method
            if hasattr(self.external_connector, "subscribe"):
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe):
                    await self.external_connector.subscribe(topic, qos)
                else:
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)
        else:
            if hasattr(self.external_connector, "subscribe"):
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe):
                    await self.external_connector.subscribe(topic, qos)
                else:
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)

    async def close(self) -> None:
        """Disconnects the external connector and cleans up resources."""
        self.logger.info("HSPConnector: Disconnecting external connector...")
        if self.external_connector and hasattr(self.external_connector, "disconnect"):
            try:
                await self.external_connector.disconnect()
                self.logger.info("HSPConnector: External connector disconnected.")
            except (
                Exception
            ) as e:  # broad exception acceptable: connector disconnect may raise various errors
                self.logger.error(
                    f"HSPConnector: Error during external connector disconnect: {e}", exc_info=True
                )

        if self.fallback_manager:
            try:
                # 修复：确保正确调用shutdown方法(不是异步方法)
                if hasattr(self.fallback_manager, "shutdown") and callable(
                    self.fallback_manager.shutdown
                ):
                    self.fallback_manager.shutdown()
                self.logger.info("HSPConnector: Fallback manager shut down.")
            except (
                Exception
            ) as e:  # broad exception acceptable: fallback shutdown may raise various errors
                self.logger.error(
                    f"HSPConnector: Error during fallback manager shutdown: {e}", exc_info=True
                )

        self.is_connected = False
        self.hsp_available = False

    async def disconnect(self) -> None:
        """Disconnect from the service."""
        if self.mock_mode:
            self.logger.info("HSPConnector: Mock disconnect successful.")
            self.is_connected = False
        else:
            try:
                await self.external_connector.disconnect()
            except (
                Exception
            ) as e:  # broad exception acceptable: disconnect may raise various errors (already closed)
                self.logger.warning(
                    f"HSPConnector: external disconnect raised (likely already closed) {e}",
                    exc_info=True,
                )
            finally:
                # Reflect underlying state or force false
                try:
                    self.is_connected = bool(
                        getattr(self.external_connector, "is_connected", False)
                    )
                except (
                    Exception
                ) as e:  # broad exception acceptable: state reflection may raise various errors
                    logger.error(f"Error in {__name__}: {e}", exc_info=True)
                    self.is_connected = False

        if self.fallback_manager and self.fallback_initialized:
            try:
                # 修复：确保正确调用shutdown方法(不是异步方法)
                if hasattr(self.fallback_manager, "shutdown") and callable(
                    self.fallback_manager.shutdown
                ):
                    self.fallback_manager.shutdown()
            except (
                Exception
            ) as e:  # broad exception acceptable: fallback shutdown may raise various errors
                self.logger.warning(f"HSPConnector: fallback shutdown error: {e}", exc_info=True)
            finally:
                self.fallback_initialized = False

        for callback in self._disconnect_callbacks:
            try:
                await callback()
            except (
                Exception
            ) as e:  # broad exception acceptable: callback execution may raise various errors
                self.logger.warning(f"HSPConnector: disconnect callback error: {e}", exc_info=True)

    async def _initialize_protocols_with_config(self, config: Dict[str, Any]) -> bool:
        """
        Initializes the individual fallback protocols based on the provided configuration.
        """
        try:
            protocols_config = config.get("protocols", {})

            # Initialize in-memory protocol
            memory_config = protocols_config.get("memory", {})
            if memory_config.get("enabled", True) and self.fallback_manager:
                memory_protocol = InMemoryProtocol()
                priority = memory_config.get("priority", 1)
                self.fallback_manager.add_protocol(memory_protocol, priority=priority)
                self.logger.debug(f"Added memory protocol with priority {priority}")

            # Initialize file-based protocol
            file_config = protocols_config.get("file", {})
            if file_config.get("enabled", True) and self.fallback_manager:
                base_path = file_config.get("base_path", "data/fallback_comm")
                file_protocol = FileBasedProtocol(base_path=base_path)
                priority = file_config.get("priority", 2)
                self.fallback_manager.add_protocol(file_protocol, priority=priority)
                self.logger.debug(f"Added file protocol with priority {priority}")

            # Initialize HTTP protocol
            http_config = protocols_config.get("http", {})
            if http_config.get("enabled", True) and self.fallback_manager:
                host = http_config.get("host", "127.0.0.1")
                # Check TESTING env var here as well
                port = 0 if os.environ.get("TESTING") == "true" else http_config.get("port", 8765)
                http_protocol = HTTPProtocol(host=host, port=port)
                priority = http_config.get("priority", 3)
                self.fallback_manager.add_protocol(http_protocol, priority=priority)
                self.logger.debug(f"Added HTTP protocol with priority {priority}")

            # Initialize and start the fallback manager
            if self.fallback_manager:
                # 修复：确保正确调用initialize和start方法(不是异步方法)
                if (
                    hasattr(self.fallback_manager, "initialize")
                    and callable(self.fallback_manager.initialize)
                    and hasattr(self.fallback_manager, "start")
                    and callable(self.fallback_manager.start)
                ):
                    # Continue with the rest of the logic
                    init_result = self.fallback_manager.initialize()
                    if init_result:
                        self.fallback_manager.start()
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False

        except (
            Exception
        ) as e:  # broad exception acceptable: protocol initialization involves multiple operations that may fail
            self.logger.error(f"Error initializing protocols with config: {e}", exc_info=True)
            return False

    def get_communication_status(self) -> Dict[str, Any]:
        """
        Returns the current communication status.
        """
        status = {
            "hsp_available": self.hsp_available,
            "is_connected": self.is_connected,
            "fallback_enabled": self.enable_fallback,
            "fallback_initialized": self.fallback_initialized,
        }

        if self.fallback_manager:
            # 修复：确保正确调用get_status方法(不是异步方法)
            if hasattr(self.fallback_manager, "get_status") and callable(
                self.fallback_manager.get_status
            ):
                status["fallback_status"] = self.fallback_manager.get_status()

        return status

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "hsp_healthy": False,
            "fallback_healthy": False,
            "overall_healthy": False,
        }

        # 检查HSP健康状态
        if self.hsp_available and self.is_connected:
            try:
                # 可以添加实际的健康检查逻辑
                health["hsp_healthy"] = True
            except (ConnectionError, RuntimeError) as e:
                health["hsp_healthy"] = False
                self.hsp_available = False
                logger.debug(f"HSP健康檢查失敗（可忽略）: {e}")

        # 检查fallback健康状态
        if self.fallback_manager:
            try:
                # 修复：确保正确调用get_status方法(不是异步方法)
                if hasattr(self.fallback_manager, "get_status") and callable(
                    self.fallback_manager.get_status
                ):
                    fallback_status = self.fallback_manager.get_status()
                    health["fallback_healthy"] = fallback_status.get("active_protocol") is not None
            except (AttributeError, KeyError, RuntimeError) as e:
                health["fallback_healthy"] = False
                logger.debug(f"Fallback健康檢查失敗（可忽略）: {e}")

        health["overall_healthy"] = health["hsp_healthy"] or health["fallback_healthy"]
        return health

    # 添加subscribe方法以解决测试中的AttributeError
    async def subscribe(self, topic: str, qos: int = 1) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: The topic to subscribe to
            qos: Quality of Service level (default: 1)
        """
        if self.mock_mode:
            # In mock mode, just add to subscribed topics
            if not hasattr(self.external_connector, "subscribed_topics"):
                self.external_connector.subscribed_topics = set()
            self.external_connector.subscribed_topics.add(topic)
            # Also call the mock subscribe method
            if hasattr(self.external_connector, "subscribe"):
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe):
                    await self.external_connector.subscribe(topic, qos)
                else:
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)
        else:
            if hasattr(self.external_connector, "subscribe"):
                # 确保subscribe方法是可等待的
                if asyncio.iscoroutinefunction(self.external_connector.subscribe):
                    await self.external_connector.subscribe(topic, qos)
                else:
                    # For synchronous subscribe methods, just call directly
                    self.external_connector.subscribe(topic, qos)

    async def publish_opinion(
        self, opinion_payload: HSPOpinionPayload, topic: Optional[str] = None
    ) -> bool:
        """
        Publishes an opinion to the HSP network.

        Args:
            opinion_payload: The opinion to publish.
            topic: The topic to publish to. If None, uses the standard opinion topic.

        Returns: bool True if the opinion was published successfully, False otherwise.
        """
        try:
            # Create the HSP message envelope
            envelope: HSPMessageEnvelope = self._create_envelope(
                message_type="HSP.Opinion",
                payload=dict(opinion_payload),
                payload_schema_uri=get_schema_uri("HSP_Opinion_v0.1.schema.json"),
            )

            # Use the standard opinion topic if not provided
            if topic is None:
                topic = f"hsp/knowledge/opinions/{self.ai_id}"

            # Publish the message
            success = await self.publish_message(topic, envelope)

            if success:
                self.logger.info(f"Opinion {opinion_payload.get('id')} published successfully.")
            else:
                logger.error(
                    f"Failed to publish opinion {opinion_payload.get('id')}.", exc_info=True
                )

            return success

        except (
            Exception
        ) as e:  # broad exception acceptable: opinion publishing involves multiple operations that may fail
            self.logger.error(f"Error publishing opinion: {e}", exc_info=True)
            return False

    async def subscribe_to_facts(self, callback: Callable[..., Any]) -> None:
        # Subscribe to fact messages
        """Execute the subscribe to facts operation."""
        self.register_on_fact_callback(callback)

        # Subscribe to the fact topic
        topic = "hsp/knowledge/facts/#"
        await self.subscribe(topic)

    async def subscribe_to_opinions(self, callback: Callable[..., Any]) -> None:
        # Register the callback for opinion messages
        # Note: We'll treat opinions as a special type of fact for now
        """Execute the subscribe to opinions operation."""
        self.register_on_fact_callback(callback)

        # Subscribe to the opinion topic
        topic = "hsp/knowledge/opinions/#"
        await self.subscribe(topic)

    def get_connector_status(self) -> Dict[str, Any]:
        # Get the connector status
        """Get the connector status by self."""
        return self.get_communication_status()

    async def _dispatch_task_result_to_callbacks(self, message: Dict[str, Any]) -> None:
        """Dispatch request."""
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(
            f"Dispatching task result to {len(self._task_result_callbacks)} callbacks. Message: {message}"
        )

        # 安全验证
        is_valid, validated_message = self.security_context.authenticate_and_process_message(
            message
        )
        if not is_valid:
            logger.warning(
                f"消息安全验证失败: {message.get('message_id', 'unknown')}", exc_info=True
            )
            return

        # 使用验证后的消息
        payload = validated_message.get("payload")
        sender_ai_id = validated_message.get("sender_ai_id")

        if payload and sender_ai_id:
            result_payload = HSPTaskResultPayload(**cast(Dict[str, Any], payload))
            for callback in self._task_result_callbacks:
                self.logger.debug(f"Calling on_task_result_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(result_payload, sender_ai_id, validated_message)
                else:
                    callback(result_payload, sender_ai_id, validated_message)

            # Check if ACK is required and send it
            qos_params = message.get("qos_parameters")
            if qos_params and qos_params.get("requires_ack"):
                ack_payload: HSPAcknowledgementPayload = {
                    "status": "received",
                    "ack_timestamp": datetime.now(timezone.utc()).isoformat(),
                    "target_message_id": message.get("message_id", ""),
                }
                ack_envelope: HSPMessageEnvelope = {
                    "hsp_envelope_version": "0.1",
                    "message_id": str(uuid.uuid4()),
                    "correlation_id": message.get(
                        "message_id"
                    ),  # Use original message_id as correlation_id
                    "sender_ai_id": self.ai_id,
                    "recipient_ai_id": sender_ai_id,
                    "timestamp_sent": datetime.now(timezone.utc()).isoformat(),
                    "message_type": "HSP.Acknowledgement_v0.1",
                    "protocol_version": "0.1",
                    "communication_pattern": "acknowledgement",
                    "security_parameters": None,
                    "qos_parameters": {"requires_ack": False, "priority": "low"},
                    "routing_info": None,
                    "payload_schema_uri": get_schema_uri("HSP_Acknowledgement_v0.1.schema.json"),
                    "payload": dict(ack_payload),
                }
                # Publish ACK to the sender's ACK topic with correct prefix and QoS 1
                ack_topic = f"hsp/acks/{sender_ai_id}"
                await self.publish_message(ack_topic, ack_envelope, qos=1)

    async def _dispatch_acknowledgement_to_callbacks(self, message: Dict[str, Any]) -> None:
        """Dispatch request."""
        payload = message.get("payload")
        sender_ai_id = message.get("sender_ai_id")

        self.logger.debug(
            f"Dispatching acknowledgement to {len(self._acknowledgement_callbacks)} callbacks. Message: {message}"
        )

        # 安全验证
        is_valid, validated_message = self.security_context.authenticate_and_process_message(
            message
        )
        if not is_valid:
            logger.warning(
                f"消息安全验证失败: {message.get('message_id', 'unknown')}", exc_info=True
            )
            return

        # 使用验证后的消息
        payload = validated_message.get("payload")
        sender_ai_id = validated_message.get("sender_ai_id")

        if payload and sender_ai_id:
            ack_payload = HSPAcknowledgementPayload(**cast(Dict[str, Any], payload))
            correlation_id = validated_message.get("correlation_id")

            # Resolve pending ACK if any
            if correlation_id and correlation_id in self._pending_acks:
                ack_future = self._pending_acks[correlation_id]
                if not ack_future.done():
                    ack_future.set_result(ack_payload)
                    self.logger.debug(f"Resolved pending ACK for correlation_id: {correlation_id}")
                del self._pending_acks[correlation_id]

            for callback in self._acknowledgement_callbacks:
                self.logger.debug(f"Calling on_acknowledgement_callback: {callback}")
                if asyncio.iscoroutinefunction(callback):
                    await callback(ack_payload, sender_ai_id, validated_message)
                else:
                    callback(ack_payload, sender_ai_id, validated_message)

    async def _handle_fact_message(self, fact_message: Dict[str, Any]) -> None:
        """
        Handle a fact message.

        Args:
                fact_message: The fact message to handle.
        """
        # Dispatch the fact message to callbacks
        await self._dispatch_fact_to_callbacks(fact_message)

    async def _handle_opinion_message(self, opinion_message: Dict[str, Any]) -> None:
        """
        Handle an opinion message.

        Args:
                opinion_message: The opinion message to handle.
        """
        # Dispatch the opinion message to callbacks (treated as facts for now)
        await self._dispatch_fact_to_callbacks(opinion_message)

    def _create_envelope(
        self,
        message_type: str,
        payload: Dict[str, Any],
        payload_schema_uri: Optional[str] = None,
        recipient_ai_id: str = "all",
        communication_pattern: Literal[
            "publish",
            "request",
            "response",
            "stream_data",
            "stream_ack",
            "acknowledgement",
            "negative_acknowledgement",
            "broadcast",
            "multicast",
            "unicast",
            "notification",
            "event",
            "command",
            "query",
            "reply",
        ] = "publish",
        qos_parameters: Optional[HSPQoSParameters] = None,
    ) -> HSPMessageEnvelope:
        """
        Creates an HSP message envelope with standard fields.

        Args:
            message_type: The type of message (e.g., "HSP.Fact").
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
            "message_id": str(uuid.uuid4()),
            "correlation_id": None,
            "sender_ai_id": self.ai_id,
            "recipient_ai_id": recipient_ai_id,
            "timestamp_sent": datetime.now(timezone.utc).isoformat(),
            "message_type": message_type,
            "protocol_version": self.version_manager.current_version,
            "communication_pattern": communication_pattern,
            "security_parameters": None,
            "qos_parameters": qos_parameters or {"requires_ack": False, "priority": "medium"},
            "routing_info": None,
            "payload_schema_uri": payload_schema_uri,
            "payload": payload,
        }

        # 应用安全处理
        try:
            self.security_context.secure_message(dict(envelope), self.ai_id)
            # 确保返回类型正确
            return envelope
        except (
            Exception
        ) as e:  # broad exception acceptable: security processing involves multiple operations that may fail
            self.logger.error(f"安全处理消息失败: {e}", exc_info=True)
            return envelope

    def _cache_message(self, message_id: str, result: bool) -> None:
        """Cache a message result with TTL."""
        if message_id:
            self.message_cache[message_id] = {"result": result, "timestamp": time.time()}

    def _get_cached_message(self, message_id: str) -> Optional[bool]:
        """Get a cached message result, respecting TTL."""
        if message_id and message_id in self.message_cache:
            entry = self.message_cache[message_id]
            if time.time() - entry["timestamp"] < self.cache_ttl:
                return entry["result"]
            else:
                del self.message_cache[message_id]
        return None

    async def _batch_send_messages(self) -> None:
        """Flush the message batch if conditions are met."""
        current_time = time.time()
        if (
            len(self.message_batch) >= self.batch_size
            or (current_time - self.last_batch_send) > 1.0
        ):
            batch_to_send = self.message_batch[:]
            self.message_batch.clear()
            self.last_batch_send = current_time
            for item in batch_to_send:
                try:
                    await self._raw_publish_message(
                        item["topic"], item["envelope"], item.get("qos", 1)
                    )
                except (
                    Exception
                ) as e:  # broad exception acceptable: batch send may fail with various errors
                    self.logger.error(f"Batch send error: {e}", exc_info=True)

    async def _raw_publish_message(
        self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1
    ) -> bool:
        """原始发布消息方法"""
        try:
            # Prepare message for ExternalConnector.send
            message = dict(envelope)
            message["target_id"] = envelope.get("recipient_ai_id") or "all"

            if hasattr(self.external_connector, "send"):
                return await self.external_connector.send(message)
            elif hasattr(self.external_connector, "publish"):
                # Fallback for mock or older implementation
                payload = json.dumps(envelope, ensure_ascii=False)
                await self.external_connector.publish(topic, payload, qos)
                return True

            logger.error("ExternalConnector has neither 'send' nor 'publish' method", exc_info=True)
            return False
        except (
            Exception
        ) as e:  # broad exception acceptable: raw publish may fail with various errors
            self.logger.error(f"Error in _raw_publish_message: {e}", exc_info=True)
            return False

    async def publish_message(self, topic: str, envelope: HSPMessageEnvelope, qos: int = 1) -> bool:
        self.logger.debug("HSPConnector: publish_message called.")

        message_id, correlation_id, requires_ack = self._publish_setup(envelope)

        _optimized_message = await self.performance_optimizer.optimize_message_routing(
            cast(Dict[str, Any], envelope)
        )

        if not requires_ack:
            cached_result = self._get_cached_message(message_id)
            if cached_result is not None:
                self.logger.debug(f"使用缓存结果发送消息: {message_id}")
                return cached_result

        if self.batch_send_enabled and not requires_ack:
            return await self._try_batch_send(topic, envelope, qos, message_id)

        if correlation_id not in self._message_retry_counts:
            self._message_retry_counts[correlation_id] = 0

        try:
            raw_result = await self.circuit_breaker(self.retry_policy(self._raw_publish_message))(
                topic, envelope, qos
            )

            if not raw_result:
                self.logger.warning(f"Message {correlation_id} raw publish failed.")
                self._cache_message(message_id, False)
                return False

            self.logger.debug(f"Message {correlation_id} published via HSP (decorated).")

            if requires_ack:
                return await self._handle_ack_wait(correlation_id, message_id, topic, envelope, qos)

            self._cleanup_message(correlation_id, message_id, True)
            return True

        except Exception as e:
            self.logger.error(f"Error publishing message {correlation_id}: {e}", exc_info=True)
            return await self._handle_publish_retry(
                correlation_id, message_id, topic, envelope, qos
            )

    def _publish_setup(self, envelope: HSPMessageEnvelope) -> Tuple[str, str, bool]:
        message_id = envelope.get("message_id")
        correlation_id = envelope.get("correlation_id") or message_id
        qos_params = envelope.get("qos_parameters") or {}
        requires_ack = qos_params.get("requires_ack", False)
        return message_id, correlation_id, requires_ack

    async def _try_batch_send(
        self, topic: str, envelope: HSPMessageEnvelope, qos: int, message_id: str
    ) -> bool:
        self.message_batch.append({"topic": topic, "envelope": envelope, "qos": qos})
        if len(self.message_batch) > _MAX_MESSAGE_BATCH:
            self.message_batch = self.message_batch[-_MAX_MESSAGE_BATCH:]
        await self._batch_send_messages()
        self._cache_message(message_id, True)
        return True

    async def _handle_ack_wait(
        self,
        correlation_id: str,
        message_id: str,
        topic: str,
        envelope: HSPMessageEnvelope,
        qos: int,
    ) -> bool:
        ack_future = asyncio.Future()
        self._pending_acks[correlation_id] = ack_future
        try:
            await asyncio.wait_for(ack_future, timeout=self.ack_timeout_sec)
            self.logger.info(f"ACK received for message {correlation_id}.")
            self._cleanup_message(correlation_id, message_id, True)
            return True
        except asyncio.TimeoutError:
            self.logger.warning(f"ACK timeout for message {correlation_id}.", exc_info=True)
            self._pending_acks.pop(correlation_id, None)
            if self.enable_fallback and self.fallback_manager:
                fallback_success = await self._send_via_fallback(topic, dict(envelope), qos)
                if fallback_success:
                    self.logger.info(
                        f"Message {correlation_id} sent via fallback after ACK timeout."
                    )
                    self._cleanup_message(correlation_id, message_id, True)
                    return True
                self.logger.error(f"Fallback failed for message {correlation_id}.", exc_info=True)
            return await self._handle_publish_retry(
                correlation_id, message_id, topic, envelope, qos
            )

    async def _handle_publish_retry(
        self,
        correlation_id: str,
        message_id: str,
        topic: str,
        envelope: HSPMessageEnvelope,
        qos: int,
    ) -> bool:
        retry_count = self._message_retry_counts.get(correlation_id, 0)
        if retry_count < self.max_ack_retries:
            self._message_retry_counts[correlation_id] = retry_count + 1
            self.logger.info(
                f"Retrying message {correlation_id} (attempt {retry_count + 1}/{self.max_ack_retries})."
            )
            await asyncio.sleep(2**retry_count)
            return await self.publish_message(topic, envelope, qos)
        self.logger.error(f"Max retries exceeded for message {correlation_id}.", exc_info=True)
        self._cleanup_message(correlation_id, message_id, False)
        return False

    def _cleanup_message(self, correlation_id: str, message_id: str, success: bool) -> None:
        self._pending_acks.pop(correlation_id, None)
        self._message_retry_counts.pop(correlation_id, None)
        self._cache_message(message_id, success)
