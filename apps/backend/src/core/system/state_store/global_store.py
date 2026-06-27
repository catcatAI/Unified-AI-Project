"""
Global State Store - Single Source of Truth
Centralizes system states to eliminate circular dependencies.
C5: Now with async persistence via JsonFileStateStore.
"""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from core.interfaces.service_registry import get_registry
from utils.async_utils import safe_create_task_sync

logger = logging.getLogger(__name__)


class GlobalStateStore:
    """
    Central repository for all Angela AI states.
    Modules push updates here, and consumers subscribe to changes.
    C5: supports optional persistence via StatePersistence protocol backend.
    """
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._lock = asyncio.Lock()
        self._sync_lock = threading.Lock()
        self._states: Dict[str, Any] = {
            "alpha": {},  # Biological
            "beta": {},   # Cognitive
            "gamma": {},  # Emotional
            "delta": {},  # Social
            "epsilon": {}, # Mathematical
            "theta": {},  # Meta-cognitive
            "zeta": {},   # Consciousness Flow
            "environment": {},
            "hardware": {},
            "neuro_vocabulary": {}  # C6 數值→語意映射
        }
        self._subscribers: Dict[str, List[Callable]] = {k: [] for k in self._states.keys()}
        self._global_subscribers: List[Callable] = []
        self._last_update: Dict[str, datetime] = {k: datetime.now() for k in self._states.keys()}
        self._dirty: Dict[str, bool] = {k: False for k in self._states.keys()}
        self._persistence: Optional[Any] = None

    def set_persistence(self, backend: Any) -> None:
        """Attach a persistence backend (must implement StatePersistence protocol)."""
        self._persistence = backend
        logger.info(f"[StateStore] Persistence backend attached: {backend.__class__.__name__}")

    async def save_domain(self, domain: str) -> bool:
        """Persist a single domain if a backend is attached."""
        if not self._persistence:
            return False
        async with self._lock:
            data = self._states.get(domain)
            if data is None:
                return False
        ok = await self._persistence.save_state(f"domain/{domain}", dict(data))
        if ok:
            self._dirty[domain] = False
        return ok

    async def save_all(self) -> int:
        """Persist all dirty domains. Returns number of domains saved."""
        if not self._persistence:
            return 0
        count = 0
        async with self._lock:
            domains = list(self._states.keys())
        for domain in domains:
            ok = await self.save_domain(domain)
            if ok:
                count += 1
        return count

    async def load_domain(self, domain: str) -> bool:
        """Restore a single domain from persistence."""
        if not self._persistence:
            return False
        data = await self._persistence.load_state(f"domain/{domain}")
        if data is None:
            return False
        async with self._lock:
            self._states[domain] = dict(data)
        self._dirty[domain] = False
        return True

    async def load_all(self) -> int:
        """Restore all domains from persistence. Returns number of domains loaded."""
        if not self._persistence:
            return 0
        count = 0
        async with self._lock:
            domains = list(self._states.keys())
        for domain in domains:
            ok = await self.load_domain(domain)
            if ok:
                count += 1
        return count

    def update_state(self, domain: str, data: Dict[str, Any], notify: bool = True) -> None:
        """Update state for a specific domain."""
        with self._sync_lock:
            if domain not in self._states:
                logger.warning(f"[StateStore] Attempted to update unknown domain: {domain}", exc_info=True)
                self._states[domain] = {}
                self._subscribers[domain] = []

            # Selective update to prevent full overwrite
            self._states[domain].update(data)
            self._last_update[domain] = datetime.now()
            self._dirty[domain] = True

        if notify:
            self._notify_subscribers(domain)
        self._fire_state_change_hook(domain, data)

    def _fire_state_change_hook(self, domain: str, data: Dict[str, Any]) -> None:
        """Fire on_state_change plugin hook (non-blocking)."""
        try:
            from core.plugin import plugin_manager as _pm
            safe_create_task_sync(
                _pm.execute_hook('on_state_change', {
                    'domain': domain,
                    'data': data,
                }), name="StateStore-on_state_change"
            )
        except Exception as e:
            logger.warning(f"Failed to execute plugin hook on_state_change: {e}", exc_info=True)

    def get_state(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve state for a domain or the entire system."""
        if domain:
            return self._states.get(domain, {}).copy()
        return {k: v.copy() for k, v in self._states.items()}

    def is_dirty(self, domain: Optional[str] = None) -> bool:
        """Check if a domain (or any domain) has unsaved changes."""
        if domain:
            return self._dirty.get(domain, False)
        return any(self._dirty.values())

    def subscribe(self, domain: str, callback: Callable) -> None:
        """Subscribe to changes in a specific domain."""
        if domain in self._subscribers:
            self._subscribers[domain].append(callback)
        else:
            self._global_subscribers.append(callback)

    def _notify_subscribers(self, domain: str) -> None:
        """Notify subscribers of a domain change."""
        data = self._states[domain]
        # Notify domain-specific subscribers (iterate over copy for safety)
        for callback in list(self._subscribers.get(domain, [])):
            try:
                callback(domain, data)
            except Exception as e:
                logger.error(f"[StateStore] Error in subscriber callback for {domain}: {e}", exc_info=True)

        # Notify global subscribers (iterate over copy for safety)
        for callback in list(self._global_subscribers):
            try:
                callback(domain, data)
            except Exception as e:
                logger.error(f"[StateStore] Error in global subscriber callback: {e}", exc_info=True)


# Singleton Access
state_store = GlobalStateStore()

# Attach default JSON file persistence backend
try:
    from core.interfaces.persistence import JsonFileStateStore
    _default_backend = JsonFileStateStore(data_dir="data/state/")
    state_store.set_persistence(_default_backend)
except Exception as e:
    logger.warning(f"[StateStore] Default persistence backend unavailable: {e}", exc_info=True)

get_registry().register("global_state_store", state_store)
