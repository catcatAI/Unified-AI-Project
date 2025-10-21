from typing import Callable, Dict, List, Any

class MockMessageBus:
    def __init__(self) -> None:
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.sent_messages: List[Dict[str, Any]] = []

    def subscribe(self, topic: str, callback: Callable):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(callback)

    def publish(self, topic: str, message: Dict[str, Any]):
        self.sent_messages.append({"topic": topic, "message": message})
        if topic in self.subscriptions:
            for callback in self.subscriptions[topic]:
                callback(message)

    def clear(self):
        self.subscriptions = {}
        self.sent_messages = []