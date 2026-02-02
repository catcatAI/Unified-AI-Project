import asyncio
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class MessageBridge:
    """A simple message bridge for routing messages between different communication protocols.
    For V1, this will be a simulated bridge that demonstrates the concept of routing.
    """

    def __init__(self):
        logger.info("MessageBridge initialized.")
        self.registered_protocols: dict[str, Callable[[str, dict[str, Any]], None]] = {}
        self.routing_rules: list[dict[str, Any]] = []

    def register_protocol_sender(
        self,
        protocol_name: str,
        sender_function: Callable[[str, dict[str, Any]], None],
    ):
        """Registers a function that can send messages for a specific protocol.
        The sender_function should accept (topic: str, message: Dict[str, Any]).
        """
        self.registered_protocols[protocol_name] = sender_function
        logger.info(f"Protocol sender '{protocol_name}' registered with MessageBridge.")

    def add_routing_rule(
        self,
        source_protocol: str,
        target_protocol: str,
        topic_pattern: str = "#",
    ):
        """Adds a routing rule to forward messages from a source protocol to a target protocol.
        topic_pattern can be used for more granular routing (e.g., "agent/commands/#").
        """
        self.routing_rules.append(
            {
                "source_protocol": source_protocol,
                "target_protocol": target_protocol,
                "topic_pattern": topic_pattern,
            },
        )
        logger.info(
            f"Routing rule added: {source_protocol} -> {target_protocol} for topic '{topic_pattern}'.",
        )

    async def route_message(
        self,
        source_protocol: str,
        topic: str,
        message: dict[str, Any],
    ):
        """Routes a message from a source protocol to appropriate target protocols based on rules."""
        logger.info(
            f"MessageBridge received message from '{source_protocol}' on topic '{topic}'.",
        )

        for rule in self.routing_rules:
            if rule["source_protocol"] == source_protocol:
                # Basic topic pattern matching (can be enhanced with regex for real-world use)
                if rule["topic_pattern"] == "#" or topic.startswith(
                    rule["topic_pattern"].replace("#", ""),
                ):
                    target_protocol = rule["target_protocol"]
                    if target_protocol in self.registered_protocols:
                        sender = self.registered_protocols[target_protocol]
                        logger.info(
                            f"MessageBridge forwarding message to '{target_protocol}' on topic '{topic}'.",
                        )
                        try:
                            # Simulate async send if the sender is not truly async
                            if asyncio.iscoroutinefunction(sender):
                                await sender(topic, message)
                            else:
                                await asyncio.to_thread(sender, topic, message)
                            logger.debug(
                                f"Successfully forwarded message to '{target_protocol}'.",
                            )
                        except Exception as e:
                            logger.error(
                                f"Error forwarding message to '{target_protocol}': {e}",
                            )
                    else:
                        logger.warning(
                            f"Target protocol '{target_protocol}' not registered. Message not forwarded.",
                        )
                else:
                    logger.debug(
                        f"Topic '{topic}' does not match pattern '{rule['topic_pattern']}'.",
                    )
            else:
                logger.debug(
                    f"Source protocol '{source_protocol}' does not match rule's source '{rule['source_protocol']}'.",
                )


if __name__ == "__main__":

    async def main():
        bridge = MessageBridge()

        # Simulated sender functions for different protocols
        async def mqtt_sender(topic: str, message: dict[str, Any]):
            print(f"[MQTT Sender] Topic: {topic}, Message: {message}")
            await asyncio.sleep(0.01)  # Simulate network delay

        async def http_post_sender(topic: str, message: dict[str, Any]):
            print(
                f"[HTTP Sender] Posting to: /api/{topic.replace('/', '_')}, Payload: {message}",
            )
            await asyncio.sleep(0.02)  # Simulate network delay

        async def websocket_sender(topic: str, message: dict[str, Any]):
            print(
                f"[WebSocket Sender] Sending to client on channel: {topic}, Data: {message}",
            )
            await asyncio.sleep(0.005)  # Simulate network delay

        # Register senders
        bridge.register_protocol_sender("mqtt", mqtt_sender)
        bridge.register_protocol_sender("http", http_post_sender)
        bridge.register_protocol_sender("websocket", websocket_sender)

        # Add routing rules
        bridge.add_routing_rule("mqtt", "http", "agent/commands/#")
        bridge.add_routing_rule("http", "websocket", "user/updates")
        bridge.add_routing_rule("mqtt", "websocket", "agent/status")
        bridge.add_routing_rule(
            "mqtt",
            "http",
            "system/logs",
        )  # Catch-all for mqtt to http

        print("\n--- Test Case 1: MQTT to HTTP ---")
        await bridge.route_message(
            "mqtt",
            "agent/commands/start",
            {"command": "start_agent", "agent_id": "A1"},
        )

        print("\n--- Test Case 2: HTTP to WebSocket ---")
        await bridge.route_message(
            "http",
            "user/updates",
            {"user_id": "U1", "status": "online"},
        )

        print("\n--- Test Case 3: MQTT to WebSocket ---")
        await bridge.route_message(
            "mqtt",
            "agent/status",
            {"agent_id": "A2", "health": "good"},
        )

        print("\n--- Test Case 4: MQTT to HTTP (general rule) ---")
        await bridge.route_message(
            "mqtt",
            "system/logs/error",
            {"level": "error", "message": "Disk full"},
        )

        print("\n--- Test Case 5: No matching rule ---")
        await bridge.route_message("unknown_protocol", "some/topic", {"data": "test"})

        print(
            "\n--- Test Case 6: Matching rule, but target protocol not registered ---",
        )
        bridge.add_routing_rule("mqtt", "unregistered_protocol", "test/topic")
        await bridge.route_message("mqtt", "test/topic", {"data": "should_fail"})

    asyncio.run(main())
