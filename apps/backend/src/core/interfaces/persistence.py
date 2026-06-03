"""
ANGELA-MATRIX: [L2-L3] [α] [A] [L2]
State persistence protocol for save/load operations.
"""

import logging
from abc import abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, Protocol, runtime_checkable

from core.system.config.async_io import async_json_dump, async_json_load

logger = logging.getLogger(__name__)


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


class JsonFileStateStore:
    """Concrete StatePersistence implementation using JSON files.

    Usage:
        store = JsonFileStateStore(data_dir="data/state/")
        await store.save_state("matrix/alpha", {"value": 0.5})
        data = await store.load_state("matrix/alpha")
    """

    def __init__(self, data_dir: str = "data/state/"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        """Resolve a state key to a file path."""
        safe = key.replace("/", "_").replace("\\", "_")
        return self._data_dir / f"{safe}.json"

    async def save_state(self, key: str, data: Dict[str, Any]) -> bool:
        """Persist state data under the given key."""
        try:
            path = self._resolve_path(key)
            await async_json_dump(data, str(path), ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save state key={key}: {e}", exc_info=True)
            return False

    async def load_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Load state data by key, returning None if not found."""
        try:
            path = self._resolve_path(key)
            if path.exists():
                return await async_json_load(str(path))
            return None
        except Exception as e:
            logger.error(f"Failed to load state key={key}: {e}", exc_info=True)
            return None

    async def delete_state(self, key: str) -> bool:
        """Remove persisted state by key."""
        try:
            path = self._resolve_path(key)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            logger.error(f"Failed to delete state key={key}: {e}", exc_info=True)
            return False

    async def list_keys(self, prefix: str = "") -> list:
        """List all keys matching the given prefix."""
        try:
            pattern = f"{prefix.replace('/', '_')}*.json"
            return sorted(
                str(f.stem) for f in self._data_dir.glob(pattern)
            )
        except Exception as e:
            logger.error(f"Failed to list keys prefix={prefix}: {e}", exc_info=True)
            return []


__all__ = ["StatePersistence", "JsonFileStateStore"]
