import asyncio
import json  # Added import json
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTT_ERR_SUCCESS

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


class HSPConnector:
    """High-Speed Synchronization Protocol (HSP) Connector.
    Handles communication between AI agents and other modules using a publish-subscribe model via MQTT.
    """

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = None,
    ):
        """Initializes the HSPConnector.

        Args:
            broker_host (str): The MQTT broker host.
            broker_port (int): The MQTT broker port.
            client_id (str): Unique client ID for the MQTT connection. If None, a random one is generated.

        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = (
            client_id
            if client_id
            else f"hsp-client-{asyncio.current_task().get_name() if asyncio.current_task() else 'unknown'}-{uuid.uuid4().hex[:8]}"
        )
        self.client = MQTTClient(self.client_id)
        self.is_connected = False
        self._callbacks: dict[
            str,
            Callable,
        ] = {}  # Store callbacks for subscribed topics

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        logger.info(
            f"HSPConnector initialized for broker: {broker_host}:{broker_port} with client ID: {self.client_id}",
        )

    async def connect(self) -> bool:
        """Establishes a connection to the MQTT broker with retry mechanism."""
        retries = 3
        for i in range(retries):
            try:
                logger.info(
                    f"Attempting to connect to HSP broker at {self.broker_host}:{self.broker_port} (Attempt {i + 1}/{retries})...",
                )
                await self.client.connect(self.broker_host, self.broker_port)
                # Connection success is handled by _on_connect callback
                # Wait a bit to ensure on_connect is called
                await asyncio.sleep(0.5)
                if self.is_connected:
                    logger.info("HSPConnector connected.")
                    return True
            except Exception as e:
                logger.error(f"Connection attempt {i + 1} failed: {e}")
                if i < retries - 1:
                    await asyncio.sleep(2**i)  # Exponential backoff
            else:
                if self.is_connected:
                    logger.info("HSPConnector connected.")
                    return True
        logger.error("Failed to connect to HSP broker after multiple retries.")
        return False

    async def disconnect(self):
        """Disconnects from the MQTT broker."""
        if self.is_connected:
            logger.info("Disconnecting HSPConnector...")
            await self.client.disconnect()
            # Disconnection success is handled by _on_disconnect callback
            await asyncio.sleep(0.1)  # Give time for disconnect callback
        else:
            logger.info("HSPConnector is not connected.")

    async def send_message(self, topic: str, payload: dict[str, Any]) -> bool:
        """Sends a message to a specific topic.

        Args:
            topic (str): The MQTT topic to publish to.
            payload (Dict[str, Any]): The message payload.

        Returns:
            bool: True if message was sent, False otherwise.

        """
        if not self.is_connected:
            logger.error("Error: HSPConnector not connected. Cannot send message.")
            return False

        try:
            # gmqtt expects payload as bytes
            message_payload = json.dumps(payload).encode("utf-8")
            self.client.publish(topic, message_payload)  # Removed await
            logger.debug(f"Sent message to topic '{topic}': {payload}")
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            return False
        else:
            return True

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[str, dict[str, Any]], Any],
    ):
        """Subscribes to a topic and registers a callback function.

        Args:
            topic (str): The MQTT topic to subscribe to.
            callback (Callable[[str, Dict[str, Any]], Any]): The callback function to be called when a message is received.
                                                              It should accept topic (str) and payload (Dict[str, Any]) as arguments.

        """
        if not self.is_connected:
            logger.error("Error: HSPConnector not connected. Cannot subscribe.")
            return

        try:
            self.client.subscribe(topic)  # Removed await
            self._callbacks[topic] = callback
            logger.info(f"Subscribed to topic '{topic}'.")
        except Exception as e:
            logger.error(f"Failed to subscribe to topic '{topic}': {e}")

    def _on_connect(self, client, flags, rc, properties):
        if rc == MQTT_ERR_SUCCESS:
            self.is_connected = True
            logger.info(f"MQTT client '{self.client_id}' connected to broker.")
        else:
            self.is_connected = False
            logger.error(f"MQTT client '{self.client_id}' failed to connect: {rc}")

    def _on_disconnect(self, client, packet, exc=None):
        self.is_connected = False
        if exc:
            logger.error(
                f"MQTT client '{self.client_id}' disconnected with exception: {exc}",
            )
        else:
            logger.info(f"MQTT client '{self.client_id}' disconnected from broker.")

    async def _on_message(self, client, topic, payload, qos, properties):
        logger.debug(f"Received message on topic '{topic}': {payload.decode('utf-8')}")
        if topic in self._callbacks:
            try:
                decoded_payload = json.loads(payload.decode("utf-8"))
                await self._callbacks[topic](topic, decoded_payload)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON payload for topic '{topic}': {e}")
            except Exception as e:
                logger.error(f"Error in callback for topic '{topic}': {e}")
        else:
            logger.warning(f"No callback registered for topic '{topic}'.")


if __name__ == "__main__":
    import json
    import time  # Added import time
    import uuid

    async def test_callback(topic: str, payload: dict[str, Any]):
        logger.info(f"Test Callback - Topic: {topic}, Payload: {payload}")

    async def main():
        # Ensure the project root is in sys.path for module resolution
        import sys

        project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        connector = HSPConnector(client_id="test-hsp-client")

        # Test connection
        if not await connector.connect():
            logger.error("Failed to connect, exiting.")
            return

        # Test subscription
        await connector.subscribe("test/topic", test_callback)
        await connector.subscribe("agent/commands", test_callback)

        # Test sending message
        await connector.send_message(
            "test/topic",
            {"message": "Hello HSP!", "timestamp": time.time()},
        )
        await connector.send_message(
            "agent/commands",
            {"command": "execute", "agent_id": "agent_X"},
        )

        # Simulate receiving messages (in a real scenario, this would be handled by the broker)
        # For testing, we can manually trigger the on_message callback
        await connector._on_message(
            connector.client,
            "test/topic",
            json.dumps({"simulated": "message"}).encode("utf-8"),
            0,
            None,
        )

        # Keep the connector alive for a bit to receive messages
        logger.info("Connector running for 5 seconds to receive messages...")
        await asyncio.sleep(5)

        # Test disconnection
        await connector.disconnect()

        # Test sending message when disconnected
        await connector.send_message(
            "agent/status",
            {"agent_id": "agent2", "status": "offline"},
        )

    asyncio.run(main())
