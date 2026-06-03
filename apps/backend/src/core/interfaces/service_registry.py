"""
ANGELA-MATRIX: [L3] [β] [A] [L3]
Central service registry for explicit dependency injection.
Replaces implicit singleton patterns across the system.
"""

from typing import Dict, Any, Optional, TypeVar, Generic, Type
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceRegistry:
    """Central registry for service instances with lifecycle management."""

    def __init__(self):
        self._services: Dict[str, Any] = {}

    def register(self, name: str, instance: Any) -> None:
        """Register a service instance by name."""
        self._services[name] = instance
        logger.debug(f"Registered service: {name} ({type(instance).__name__})")

    def get(self, name: str, expected_type: Optional[Type[T]] = None) -> Optional[Any]:
        """Retrieve a registered service by name."""
        instance = self._services.get(name)
        if instance is not None and expected_type is not None:
            if not isinstance(instance, expected_type):
                logger.warning(
                    f"Service '{name}' type mismatch: "
                    f"expected {expected_type.__name__}, got {type(instance).__name__}"
                    , exc_info=True
                )
        return instance

    def unregister(self, name: str) -> None:
        """Remove a service from the registry."""
        self._services.pop(name, None)

    def clear(self) -> None:
        """Remove all registered services."""
        self._services.clear()

    @property
    def service_names(self) -> list:
        return list(self._services.keys())


# Global registry instance
_registry = ServiceRegistry()


def get_registry() -> ServiceRegistry:
    """Get the global ServiceRegistry singleton."""
    return _registry


__all__ = ["ServiceRegistry", "get_registry"]
