import asyncio
import inspect
import logging
import threading
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

_pending_tasks: set = set()


class InternalBus:
    """
    Simulates an internal message bus for testing and local communication.
    (Restored to fix file corruption)
    """

    def __init__(self):
        self.subscriptions: Dict[str, List[Callable[[Any], None]]] = {}
        self._task_semaphore = threading.Semaphore(200)

    def _run_task(self, callback, message) -> None:
        """Run an async callback with bounded concurrency."""
        if not self._task_semaphore.acquire(blocking=False):
            logger.warning("Dropping internal bus task: too many pending")
            return

        async def _wrapped():
            try:
                await callback(message)
            finally:
                self._task_semaphore.release()

        task = asyncio.create_task(_wrapped())
        _pending_tasks.add(task)
        task.add_done_callback(
            lambda t: (
                _pending_tasks.discard(t),
                (
                    logger.warning("InternalBus task failed: %s", t.exception())
                    if not t.cancelled() and t.exception()
                    else None
                ),
            )
        )

    def publish(self, channel: str, message: Any) -> None:
        """Publish a message to a channel."""
        logger.debug(f"InternalBus.publish - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    self._run_task(callback, message)
                else:
                    callback(message)

    async def publish_async(self, channel: str, message: Any) -> None:
        """Awaitable version of publish."""
        logger.debug(f"InternalBus.publish_async - Channel: {channel}, Message: {message}")
        if channel in self.subscriptions:
            for callback in self.subscriptions[channel]:
                if inspect.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)

    def subscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        """Subscribe a callback to a channel."""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        self.subscriptions[channel].append(callback)

    def unsubscribe(self, channel: str, callback: Callable[[Any], None]) -> None:
        """Unsubscribe a callback from a channel."""
        if channel in self.subscriptions:
            if callback in self.subscriptions[channel]:
                self.subscriptions[channel].remove(callback)
