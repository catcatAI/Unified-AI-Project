import asyncio
from typing import Callable, Dict, List, Any
from unittest.mock import AsyncMock
import inspect

class InternalBus:
    def __init__(self):
        self.subscriptions: Dict[str, List[Callable[[Any], None]]] = {}

    def publish(self, channel: str, message: Any):
        print(f"DEBUG: InternalBus.publish - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(message))
                else:
                    callback(message)

    def subscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        self.subscriptions[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel in self.subscriptions:
            self.subscriptions[channel].remove(callback)
