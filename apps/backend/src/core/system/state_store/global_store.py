"""
Global State Store - Single Source of Truth
Centralizes system states to eliminate circular dependencies.
"""

import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from core.interfaces.service_registry import get_registry

logger = logging.getLogger(__name__)

class GlobalStateStore:
    """
    Central repository for all Angela AI states.
    Modules push updates here, and consumers subscribe to changes.
    """
    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._states: Dict[str, Any] = {
            "alpha": {},  # Biological
            "beta": {},   # Cognitive
            "gamma": {},  # Emotional
            "delta": {},  # Social
            "epsilon": {}, # Mathematical
            "theta": {},  # Meta-cognitive
            "zeta": {},   # Consciousness Flow
            "environment": {},
            "hardware": {}
        }
        self._subscribers: Dict[str, List[Callable]] = {k: [] for k in self._states.keys()}
        self._global_subscribers: List[Callable] = []
        self._last_update: Dict[str, datetime] = {k: datetime.now() for k in self._states.keys()}

    def update_state(self, domain: str, data: Dict[str, Any], notify: bool = True):
        """Update state for a specific domain."""
        if domain not in self._states:
            logger.warning(f"[StateStore] Attempted to update unknown domain: {domain}")
            self._states[domain] = {}
            self._subscribers[domain] = []

        # Selective update to prevent full overwrite
        self._states[domain].update(data)
        self._last_update[domain] = datetime.now()

        if notify:
            self._notify_subscribers(domain)

    def get_state(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve state for a domain or the entire system."""
        if domain:
            return self._states.get(domain, {}).copy()
        return {k: v.copy() for k, v in self._states.items()}

    def subscribe(self, domain: str, callback: Callable):
        """Subscribe to changes in a specific domain."""
        if domain in self._subscribers:
            self._subscribers[domain].append(callback)
        else:
            self._global_subscribers.append(callback)

    def _notify_subscribers(self, domain: str):
        """Notify subscribers of a domain change."""
        data = self._states[domain]
        # Notify domain-specific subscribers
        for callback in self._subscribers.get(domain, []):
            try:
                callback(domain, data)
            except Exception as e:
                logger.error(f"[StateStore] Error in subscriber callback for {domain}: {e}")

        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                callback(domain, data)
            except Exception as e:
                logger.error(f"[StateStore] Error in global subscriber callback: {e}")

# Singleton Access
state_store = GlobalStateStore()
get_registry().register("global_state_store", state_store)
