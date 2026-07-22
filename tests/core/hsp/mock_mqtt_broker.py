"""Mock MQTT broker for testing purposes."""

import asyncio
import inspect
import json


class MockMqttBroker:
    """A simplified mock MQTT broker for testing HSP connector functionality."""

    def __init__(self):
        self.subscriptions = {}
        self.published_messages = []
        self.is_running = False

    async def start(self):
        self.is_running = True

    async def shutdown(self):
        self.is_running = False

    async def publish(self, topic, payload, qos=1, retain=False, **kwargs):
        if not self.is_running:
            raise Exception("Broker is not running")
        message = {"topic": topic, "payload": payload, "qos": qos, "retain": retain}
        self.published_messages.append(message)
        for sub_topic, callbacks in self.subscriptions.items():
            if self._topic_matches(sub_topic, topic):
                for callback in callbacks:
                    if inspect.iscoroutinefunction(callback):
                        await callback(topic, payload, qos)
                    else:
                        callback(topic, payload, qos)
        return None

    def subscribe(self, topic, qos=1, callback=None):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        if callback is not None and callback not in self.subscriptions[topic]:
            self.subscriptions[topic].append(callback)

    def _topic_matches(self, subscription_topic, message_topic):
        if subscription_topic == message_topic:
            return True
        return False
