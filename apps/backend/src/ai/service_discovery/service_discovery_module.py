# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ServiceDiscoveryModule:
    def __init__(self, trust_manager: Any, staleness_threshold_seconds: int = 3600):
        self.trust_manager = trust_manager
        self.staleness_threshold_seconds = staleness_threshold_seconds
        self.known_capabilities: Dict[str, Dict[str, Any]] = {}

    def process_capability_advertisement(
        self,
        payload: Dict[str, Any],
        ai_id: str,
        envelope: Dict[str, Any],
    ) -> None:
        capability_id = payload.get("capability_id")
        if not capability_id:
            return
        self.known_capabilities[capability_id] = {
            "payload": payload,
            "ai_id": ai_id,
            "envelope": envelope,
            "timestamp": datetime.now(timezone.utc),
        }

    def get_capability_by_id(self, capability_id: str) -> Optional[Dict[str, Any]]:
        entry = self.known_capabilities.get(capability_id)
        if entry:
            return {
                **entry["payload"],
                "ai_id": entry["ai_id"],
            }
        return None

    def is_capability_available(self, capability_id: str) -> bool:
        return capability_id in self.known_capabilities

    def get_all_capabilities(self) -> List[Dict[str, Any]]:
        return [
            {**entry["payload"], "ai_id": entry["ai_id"]}
            for entry in self.known_capabilities.values()
        ]

    async def find_capabilities(self) -> List[Dict[str, Any]]:
        return self.get_all_capabilities()

    async def get_all_capabilities_async(self) -> List[Dict[str, Any]]:
        return self.get_all_capabilities()

    def remove_stale_capabilities(self) -> None:
        now = datetime.now(timezone.utc)
        stale_ids = [
            cap_id
            for cap_id, entry in self.known_capabilities.items()
            if (now - entry["timestamp"]).total_seconds() > self.staleness_threshold_seconds
        ]
        for cap_id in stale_ids:
            del self.known_capabilities[cap_id]
