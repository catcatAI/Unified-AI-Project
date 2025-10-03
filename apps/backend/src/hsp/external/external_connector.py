import asyncio
import logging
import ssl
import time
from typing import Callable, Optional, Awaitable, Any, TYPE_CHECKING

# 用于类型检查的导入
if TYPE_CHECKING:
    # 在类型检查时导入 gmqtt
    import gmqtt

# 尝试导入 gmqtt，如果失败则设置为 None 并记录错误
try:
    import gmqtt  # type ignore
    GMQTT_AVAILABLE = True
except ImportError as e:
    gmqtt = None
    GMQTT_AVAILABLE = False
    logging.getLogger(__name__).warning(f"gmqtt module not available: {e}. MQTT functionality will be disabled.")

logger = logging.getLogger(__name__)

class ExternalConnector:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int, client_id_suffix: str = "hsp_connector", tls_ca_certs: Optional[str] = None, tls_certfile: Optional[str] = None, tls_keyfile: Optional[str] = None, tls_insecure: bool = False, username: Optional[str] = None, password: Optional[str] = None)
    # 检查 gmqtt 是否可用
        if not GMQTT_AVAILABLE:

    raise RuntimeError("gmqtt module is not available. Please install it with: pip install gmqtt")

    self.ai_id = ai_id
    self.broker_address = broker_address
    self.broker_port = broker_port
    self.mqtt_client_id = f"{self.ai_id}-{client_id_suffix}"
    self.is_connected = False
    self.subscribed_topics = set
    # 修复类型定义，确保与实际使用的回调函数签名匹配
    # 使用更通用的类型注解，允许兼容的函数类型
    self.on_message_callback: Optional[Callable[..., Awaitable[None]]] = None

    # 使用 Any 类型来避免类型检查错误
    self.mqtt_client: Any = gmqtt.Client(self.mqtt_client_id)  # type ignore

    # 设置MQTT客户端参数以提高连接稳定性
    # 设置连接超时
    self.mqtt_client.set_config({
            'reconnect_retries': 1000,  # 重连次数
            'reconnect_delay': 5,       # 重连延迟（秒）
            'keepalive': 60,            # 心跳间隔（秒）
            'timeout': 30               # 连接超时（秒）
    })

        if username:


    self.mqtt_client.set_auth_credentials(username, password)
    self.mqtt_client.on_connect = self.on_connect
    self.mqtt_client.on_disconnect = self.on_disconnect
    self.mqtt_client.on_message = self.on_message

        if tls_ca_certs:


    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=tls_ca_certs)
            if tls_certfile and tls_keyfile:

    ssl_context.load_cert_chain(certfile=tls_certfile, keyfile=tls_keyfile)
            if tls_insecure:

    ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            self.mqtt_client.set_ssl(ssl_context)

    # 添加连接状态跟踪
    self.connection_attempts = 0
    self.last_connect_attempt = 0
    self.max_reconnect_delay = 300  # 最大重连延迟（秒）

    async def connect(self, timeout: int = 30)
    """连接到MQTT代理，带有超时和重试机制"""
        try:

            self.last_connect_attempt = time.time
            self.connection_attempts += 1

            # 使用超时连接
            await asyncio.wait_for(
                self.mqtt_client.connect(self.broker_address, self.broker_port),
                timeout=timeout
            )
        except asyncio.TimeoutError:

            logger.error(f"MQTT connection timeout after {timeout} seconds")
            # 实现指数退避重连
            await self._handle_connection_failure
        except Exception as e:

            logger.error(f"Failed to connect to MQTT broker: {e}", exc_info=True)
            # 实现指数退避重连
            await self._handle_connection_failure

    async def _handle_connection_failure(self)
    """处理连接失败，实现指数退避重连"""
    # 计算退避延迟（指数退避，最大延迟限制）
    backoff_delay = min(
            (2 ** min(self.connection_attempts, 10)) + (hash(self.mqtt_client_id) % 1000) / 1000,
            self.max_reconnect_delay
    )

    logger.info(f"Connection failed, retrying in {backoff_delay:.2f} seconds (attempt {self.connection_attempts})")
    await asyncio.sleep(backoff_delay)

    async def disconnect(self)
    """断开与MQTT代理的连接"""
        if not self.is_connected:

    logger.debug("ExternalConnector already disconnected, skipping")
            return

    try
            # Check if the mqtt_client and its transport are still valid
    if (hasattr(self.mqtt_client, '_transport') and :

    self.mqtt_client._transport is not None):
    await self.mqtt_client.disconnect
            else:

                logger.debug("MQTT client transport already closed, marking as disconnected")
                self.is_connected = False
        except Exception as e:

            logger.warning(f"Error during MQTT disconnect (likely already closed) {e}")
            self.is_connected = False

    async def publish(self, topic: str, payload: str, qos: int = 1)
    """发布消息到指定主题"""
    logger.debug(f"ExternalConnector.publish: topic={topic}, payload_type={type(payload)}, qos={qos}")
    await self.mqtt_client.publish(topic, payload, qos=qos)

    async def subscribe(self, topic: str, callback=None, qos: int = 1)
    """订阅指定主题"""
    # If we're in mock mode (callback provided), use the callback
        if callback is not None:
            # For mock mode, we just need to register the callback
            if not hasattr(self, 'mock_subscriptions')

    self.mock_subscriptions =
            if topic not in self.mock_subscriptions:

    self.mock_subscriptions[topic] =
            if callback not in self.mock_subscriptions[topic]:

    self.mock_subscriptions[topic].append(callback)
        else:
            # Normal mode - use the MQTT client
            await self.mqtt_client.subscribe(topic, qos=qos)
    self.subscribed_topics.add(topic)

    async def unsubscribe(self, topic: str)
    """取消订阅指定主题"""
        # Remove from mock subscriptions if they exist
    if hasattr(self, 'mock_subscriptions') and topic in self.mock_subscriptions:

    del self.mock_subscriptions[topic]
    # Normal mode - use the MQTT client
    await self.mqtt_client.unsubscribe(topic)
    self.subscribed_topics.discard(topic)

    def on_connect(self, client, flags, rc, properties)
    """MQTT连接回调"""
        if rc == 0:

    self.is_connected = True
            self.connection_attempts = 0  # 重置连接尝试计数
            logger.info("Connected to MQTT Broker!")
            for topic in self.subscribed_topics:

    asyncio.create_task(self.subscribe(topic))
        else:

            logger.error(f"Failed to connect, return code {rc}")
            # 触发重连机制
            asyncio.create_task(self._handle_connection_failure)

    async def on_message(self, client, topic, payload, qos, properties)
    """MQTT消息接收回调"""
        # First, call the on_message_callback if it exists
    if self.on_message_callback:
            # 确保正确调用回调函数，传递正确的参数
            if asyncio.iscoroutinefunction(self.on_message_callback)

    await self.on_message_callback(topic, payload.decode if isinstance(payload, bytes) else payload):
    else:

        self.on_message_callback(topic, payload.decode if isinstance(payload, bytes) else payload)

        # Then, call any mock subscriptions if they exist
    if hasattr(self, 'mock_subscriptions')

    for sub_topic, callbacks in self.mock_subscriptions.items:


    if self._topic_matches(sub_topic, topic)



    for callback in callbacks:




    if asyncio.iscoroutinefunction(callback)





    await callback(client, topic, payload, qos, properties)
                        else:

                            callback(client, topic, payload, qos, properties)

    def _topic_matches(self, subscription_topic, message_topic)
    """检查消息主题是否匹配订阅主题"""
    # Simple implementation - exact match or wildcard
        if subscription_topic == '#'

    return True
        if subscription_topic == message_topic:

    return True
        if subscription_topic.endswith('#')

    prefix = subscription_topic[:-1]
            return message_topic.startswith(prefix)
    return False

    def on_disconnect(self, client, exc)
    """MQTT断开连接回调"""
    self.is_connected = False
    logger.info("Disconnected from MQTT Broker.")

    # 如果不是主动断开连接，触发重连机制
        if exc is not None:

    logger.warning(f"Unexpected disconnection: {exc}")
            # 在后台任务中触发重连
            asyncio.create_task(self._handle_unexpected_disconnect)

    async def _handle_unexpected_disconnect(self)
    """处理意外断开连接，触发重连"""
    logger.info("Attempting to reconnect after unexpected disconnection...")
    await self._handle_connection_failure