import asyncio
import logging
import ssl
from typing import Callable, Optional
import gmqtt

logger = logging.getLogger(__name__)

class ExternalConnector:
    def __init__(self, ai_id: str, broker_address: str, broker_port: int, client_id_suffix: str = "hsp_connector", tls_ca_certs: Optional[str] = None, tls_certfile: Optional[str] = None, tls_keyfile: Optional[str] = None, tls_insecure: bool = False, username: Optional[str] = None, password: Optional[str] = None):
        self.ai_id = ai_id
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.mqtt_client_id = f"{self.ai_id}-{client_id_suffix}"
        self.is_connected = False
        self.subscribed_topics = set()
        self.on_message_callback = None

        self.mqtt_client = gmqtt.Client(self.mqtt_client_id)
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

    async def connect(self):
        try:
            await self.mqtt_client.connect(self.broker_address, self.broker_port)
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}", exc_info=True)

    async def disconnect(self):
        if not self.is_connected:
            logger.debug("ExternalConnector already disconnected, skipping")
            return
            
        try:
            # Check if the mqtt_client and its transport are still valid
            if (hasattr(self.mqtt_client, '_transport') and 
                self.mqtt_client._transport is not None):
                await self.mqtt_client.disconnect()
            else:
                logger.debug("MQTT client transport already closed, marking as disconnected")
                self.is_connected = False
        except Exception as e:
            logger.warning(f"Error during MQTT disconnect (likely already closed): {e}")
            self.is_connected = False

    async def publish(self, topic: str, payload: str, qos: int = 1):
        logger.debug(f"ExternalConnector.publish: topic={topic}, payload_type={type(payload)}, qos={qos}")
        await self.mqtt_client.publish(topic, payload, qos=qos)

    async def subscribe(self, topic: str, callback=None, qos: int = 1):
        # If we're in mock mode (callback provided), use the callback
        if callback is not None:
            # For mock mode, we just need to register the callback
            if not hasattr(self, 'mock_subscriptions'):
                self.mock_subscriptions = {}
            if topic not in self.mock_subscriptions:
                self.mock_subscriptions[topic] = []
            if callback not in self.mock_subscriptions[topic]:
                self.mock_subscriptions[topic].append(callback)
        else:
            # Normal mode - use the MQTT client
            await self.mqtt_client.subscribe(topic, qos=qos)
        self.subscribed_topics.add(topic)

    async def unsubscribe(self, topic: str):
        # Remove from mock subscriptions if they exist
        if hasattr(self, 'mock_subscriptions') and topic in self.mock_subscriptions:
            del self.mock_subscriptions[topic]
        # Normal mode - use the MQTT client
        await self.mqtt_client.unsubscribe(topic)
        self.subscribed_topics.discard(topic)

    def on_connect(self, client, flags, rc, properties):
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT Broker!")
            for topic in self.subscribed_topics:
                asyncio.create_task(self.subscribe(topic))
        else:
            logger.error(f"Failed to connect, return code {rc}")

    async def on_message(self, client, topic, payload, qos, properties):
        # First, call the on_message_callback if it exists
        if self.on_message_callback:
            # 确保正确调用回调函数，传递正确的参数
            if asyncio.iscoroutinefunction(self.on_message_callback):
                await self.on_message_callback(topic, payload.decode() if isinstance(payload, bytes) else payload)
            else:
                self.on_message_callback(topic, payload.decode() if isinstance(payload, bytes) else payload)
        
        # Then, call any mock subscriptions if they exist
        if hasattr(self, 'mock_subscriptions'):
            for sub_topic, callbacks in self.mock_subscriptions.items():
                if self._topic_matches(sub_topic, topic):
                    for callback in callbacks:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(client, topic, payload, qos, properties)
                        else:
                            callback(client, topic, payload, qos, properties)

    def _topic_matches(self, subscription_topic, message_topic):
        """Check if a message topic matches a subscription topic."""
        # Simple implementation - exact match or wildcard
        if subscription_topic == '#':
            return True
        if subscription_topic == message_topic:
            return True
        if subscription_topic.endswith('#'):
            prefix = subscription_topic[:-1]
            return message_topic.startswith(prefix)
        return False

    def on_disconnect(self, client, exc):
        self.is_connected = False
        logger.info("Disconnected from MQTT Broker.")