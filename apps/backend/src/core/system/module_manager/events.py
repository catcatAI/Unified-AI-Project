import logging
from collections.abc import Callable
from typing import Optional

from .models import ModuleStatus, HealthStatus

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable]] = {}

    def on(self, event: str, handler: Callable) -> None:
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(handler)

    def off(self, event: str, handler: Callable) -> None:
        handlers = self._subscribers.get(event)
        if handlers is not None:
            try:
                handlers.remove(handler)
            except ValueError:
                logger.warning("Handler not found in subscribers list", exc_info=True)
            if not handlers:
                del self._subscribers[event]

    def emit(self, event: str, **data) -> None:
        handlers = self._subscribers.get(event)
        if handlers is not None:
            for handler in handlers:
                handler(**data)

    def clear(self) -> None:
        self._subscribers.clear()


class HealthMonitor:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._statuses: dict[str, HealthStatus] = {}

    def check(
        self,
        name: str,
        status: ModuleStatus,
        alive: bool,
        latency_ms: float = 0.0,
        error: str = None,
        consecutive_fails: int = 0,
    ) -> None:
        hs = HealthStatus(
            name=name,
            status=status,
            alive=alive,
            latency_ms=latency_ms,
            error=error,
            consecutive_fails=consecutive_fails,
        )
        self._statuses[name] = hs
        event = f"{name}.health_ok" if alive else f"{name}.health_fail"
        self._event_bus.emit(event, status=hs)

    def get_status(self, name: str) -> Optional[HealthStatus]:
        return self._statuses.get(name)

    def get_all_statuses(self) -> dict[str, HealthStatus]:
        return dict(self._statuses)


__all__ = ["EventBus", "HealthMonitor"]
