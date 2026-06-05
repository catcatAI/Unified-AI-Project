"""
LIS Cache Interface & HAM Implementation
IMMUNO-NARRATIVE CACHE of the Linguistic Immune System.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from .types import LIS_IncidentRecord, NarrativeAntibodyObject

logger = logging.getLogger(__name__)


class LISCacheInterface(ABC):
    @abstractmethod
    async def store_incident(self, incident: LIS_IncidentRecord) -> bool:
        ...

    @abstractmethod
    async def query_incidents(
        self,
        anomaly_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def store_antibody(self, antibody: NarrativeAntibodyObject) -> bool:
        ...

    @abstractmethod
    async def get_learned_antibodies(
        self,
        for_anomaly_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        ...


class HAMLISCache(LISCacheInterface):
    def __init__(self, ham_manager) -> None:
        self._ham = ham_manager

    async def store_incident(self, incident: LIS_IncidentRecord) -> bool:
        try:
            await self._ham.store_experience(
                experience_type="lis_incident",
                data=incident,
            )
            return True
        except Exception as e:
            logger.warning("store_incident failed: %s", e)
            return False

    async def query_incidents(
        self,
        anomaly_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        try:
            filters = {}
            if anomaly_type is not None:
                filters["anomaly_type"] = anomaly_type
            results = await self._ham.query_core_memory(
                memory_type="lis_incident",
                filters=filters,
                limit=limit or 50,
            )
            return list(results)
        except Exception as e:
            logger.warning("query_incidents failed: %s", e)
            return []

    async def store_antibody(self, antibody: NarrativeAntibodyObject) -> bool:
        try:
            await self._ham.store_experience(
                experience_type="lis_antibody",
                data=antibody,
            )
            return True
        except Exception as e:
            logger.warning("store_antibody failed: %s", e)
            return False

    async def get_learned_antibodies(
        self,
        for_anomaly_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        try:
            filters = {}
            if for_anomaly_type is not None:
                filters["target_anomaly_types"] = for_anomaly_type
            results = await self._ham.query_core_memory(
                memory_type="lis_antibody",
                filters=filters,
                limit=limit or 50,
            )
            return list(results)
        except Exception as e:
            logger.warning("get_learned_antibodies failed: %s", e)
            return []


__all__ = ["LISCacheInterface", "HAMLISCache"]

