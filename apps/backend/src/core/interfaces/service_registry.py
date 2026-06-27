"""
ANGELA-MATRIX: [L3] [β] [A] [L3]
Central service registry for explicit dependency injection.
Replaces implicit singleton patterns across the system.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}

    @property
    def service_names(self) -> List[str]:
        return list(self._services.keys())

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service
        logger.debug(f"Registered service: {name}")

    def get(self, name: str, expected_type: Optional[type] = None) -> Optional[Any]:
        service = self._services.get(name)
        if service is not None and expected_type is not None:
            if not isinstance(service, expected_type):
                raise TypeError(
                    f"Service '{name}' has type {type(service).__name__}, "
                    f"expected {expected_type.__name__}"
                )
        return service

    def unregister(self, name: str) -> None:
        self._services.pop(name, None)

    def has(self, name: str) -> bool:
        return name in self._services

    def clear(self) -> None:
        self._services.clear()


_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry

