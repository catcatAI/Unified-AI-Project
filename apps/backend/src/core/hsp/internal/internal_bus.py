import logging
import asyncio
import inspect
from typing import Dict, List, Callable, Any

logger = logging.getLogger(__name__)

class InternalBus:
    """
    Simulates an internal message bus for testing and local communication.
    (Restored to fix file corruption)
    """

    def __init__(self):
        self.subscriptions: Dict[str, List[Callable[[Any], None]]] = {}

    def publish(self, channel: str, message: Any):
        logger.debug(f"InternalBus.publish - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(message))
                else:
                    callback(message)

    async def publish_async(self, channel: str, message: Any):
        """Awaitable version of publish."""
        logger.debug(f"InternalBus.publish_async - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)

    def subscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        self.subscriptions[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel in self.subscriptions:
            if callback in self.subscriptions[channel]:
                self.subscriptions[channel].remove(callback)