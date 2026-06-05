"""
实时同步系統 - 系統間的實時數據同步和狀態同步
Real-time sync system for inter-system data and state synchronization
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class SyncEventType(Enum):
    """Types of sync events."""

    STATUS_CHANGE = auto()
    DATA_UPDATE = auto()
    SYSTEM_EVENT = auto()


@dataclass
class SyncEvent:
    """A sync event to be broadcast across system components."""

    id: str
    event_type: SyncEventType
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.name,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class RealtimeSync:
    """
    Manages real-time event broadcasting across system components.
    Components register as clients and receive SyncEvent broadcasts.
    """

    def __init__(self):
        self._clients: Dict[str, Callable] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the sync system."""
        self._initialized = True
        logger.info("RealtimeSync initialized")

    async def register_client(self, name: str, callback: Callable) -> None:
        """Register a client to receive events."""
        self._clients[name] = callback
        logger.info(f"Client '{name}' registered with RealtimeSync")

    async def unregister_client(self, name: str) -> None:
        """Remove a registered client."""
        self._clients.pop(name, None)
        logger.info(f"Client '{name}' unregistered from RealtimeSync")

    async def broadcast_event(self, event: SyncEvent) -> None:
        """Broadcast an event to all registered clients."""
        logger.info(f"Broadcasting event {event.id} ({event.event_type.name})")
        for name, callback in self._clients.items():
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"Error notifying client '{name}': {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """Return current sync status."""
        return {
            "initialized": self._initialized,
            "clients": list(self._clients.keys()),
        }


sync_manager = RealtimeSync()


__all__ = ["sync_manager", "SyncEvent", "SyncEventType", "RealtimeSync"]
