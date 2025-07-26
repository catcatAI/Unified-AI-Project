from typing import Callable, Dict, List, Any

class InternalBus:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable[[Any], None]]] = {}

    def publish(self, channel: str, message: Any):
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                callback(message)

    def subscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        self.subscriptions[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel in self.subscriptions:
            self.subscriptions[channel].remove(callback)
