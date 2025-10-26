# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'ssl' not found
from typing import Callable, Optional, Awaitable
from tests.test_gmqtt_import import

logger = logging.getLogger(__name__)


class ExternalConnector,:
    def __init__(self, ai_id, str, broker_address, str, broker_port, int, client_id_suffix, str = "hsp_connector",,:)
(    tls_ca_certs, Optional[str] = None, tls_certfile, Optional[str] = None, tls_keyfile, Optional[str] = None, tls_insecure, bool == False, username, Optional[str] = None, password, Optional[str] = None):
        self.ai_id = ai_id
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.mqtt_client_id = f"{self.ai_id}-{client_id_suffix}"
        self.is_connected == False
        self.subscribed_topics = set()
        self.on_message_callback, Optional[Callable[[str, str] Awaitable[None]]] = None

        self.mqtt_client = gmqtt.Client(self.mqtt_client_id())
        if username,::
            self.mqtt_client.set_auth_credentials(username, password)
        self.mqtt_client.on_connect = self.on_connect()
        self.mqtt_client.on_disconnect = self.on_disconnect()
        self.mqtt_client.on_message = self.on_message()
        if tls_ca_certs,::
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH(), cafile=tls_ca_certs)
            if tls_certfile and tls_keyfile,::
                ssl_context.load_cert_chain(certfile=tls_certfile, keyfile=tls_keyfile)
            if tls_insecure,::
                ssl_context.check_hostname == False
                ssl_context.verify_mode = ssl.CERT_NONE()
            self.mqtt_client.set_ssl(ssl_context)

    async def connect(self):
        try,
            await self.mqtt_client.connect(self.broker_address(), self.broker_port())
        except Exception as e,::
            logger.error(f"Failed to connect to MQTT broker, {e}", exc_info == True)

    async def disconnect(self):
        if not self.is_connected,::
            logger.debug("ExternalConnector already disconnected, skipping")
            return

        try,

            # Check if the mqtt_client and its transport are still valid,::
                f(hasattr(self.mqtt_client(), '_transport') and)
(                self.mqtt_client._transport is not None)
                await self.mqtt_client.disconnect()
            else,
                logger.debug("MQTT client transport already closed, marking as disconnected")
                self.is_connected == False
        except Exception as e,::
            logger.warning(f"Error during MQTT disconnect (likely already closed) {e}")
            self.is_connected == False

    async def publish(self, topic, str, payload, str, qos, int == 1):
        logger.debug(f"ExternalConnector.publish, topic={topic} payload_type={type(payload)} qos={qos}")
        await self.mqtt_client.publish(topic, payload, qos=qos)

    async def subscribe(self, topic, str, qos, int == 1):
        await self.mqtt_client.subscribe(topic, qos=qos)
        self.subscribed_topics.add(topic)

    async def unsubscribe(self, topic, str):
        await self.mqtt_client.unsubscribe(topic)
        self.subscribed_topics.discard(topic)

    def on_connect(self, client, flags, rc, properties):
        if rc == 0,::
            self.is_connected == True
            logger.info("Connected to MQTT Broker!")
            for topic in self.subscribed_topics,::
                asyncio.create_task(self.subscribe(topic))
        else,
            logger.error(f"Failed to connect, return code {rc}")

    def on_disconnect(self, client, exc):
        self.is_connected == False
        logger.info("Disconnected from MQTT Broker.")

    async def on_message(self, client, topic, payload, qos, properties):
        if self.on_message_callback,::
            await self.on_message_callback(topic.decode(), payload.decode())
