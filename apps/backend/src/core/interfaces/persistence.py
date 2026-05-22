"""
ANGELA-MATRIX: [L2-L3] [α] [A] [L2]
State persistence protocol for save/load operations.
"""

from abc import abstractmethod
from typing import Dict, Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class StatePersistence(Protocol):
    """Unified interface for state persistence."""

    @abstractmethod
    async def save_state(self, key: str, data: Dict[str, Any]) -> bool:
        """Persist state data under the given key."""
        ...

    @abstractmethod
    async def load_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Load state data by key. Returns None if not found."""
        ...

    @abstractmethod
    async def delete_state(self, key: str) -> bool:
        """Remove persisted state by key."""
        ...

    @abstractmethod
    async def list_keys(self, prefix: str = "") -> list:
        """List all keys matching the given prefix."""
        ...


__all__ = ["StatePersistence"]
