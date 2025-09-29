import asyncio
from typing import Callable, Dict, List, Any
import inspect

class InternalBus:
    def __init__(self) -> None:
        self.subscriptions: Dict[str, List[Callable[[Any], None]]] = {} 

    def publish(self, channel: str, message: Any):
        print(f"DEBUG: InternalBus.publish - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    asyncio.create_task(callback(message))
                else:
                    callback(message)

    async def publish_async(self, channel: str, message: Any):
        """Awaitable version of publish that awaits coroutine callbacks sequentially.
        _ = Useful in tests to ensure downstream async handlers (e.g., ACK dispatch) complete before assertions.
        """
        print(f"DEBUG: InternalBus.publish_async - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    _ = await callback(message)
                else:
                    callback(message)

    def subscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        self.subscriptions[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Any], None]):
        if channel in self.subscriptions:
            self.subscriptions[channel].remove(callback)