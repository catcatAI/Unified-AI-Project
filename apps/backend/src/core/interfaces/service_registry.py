"""
ANGELA-MATRIX: [L3] [β] [A] [L3]
Central service registry for explicit dependency injection.
Replaces implicit singleton patterns across the system.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service
        logger.debug(f"Registered service: {name}")

    def get(self, name: str) -> Optional[Any]:
        return self._services.get(name)

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)

    def has(self, name: str) -> bool:
        return name in self._services


_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry

