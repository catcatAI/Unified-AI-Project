"""
LIS Cache Interface & HAM Implementation
IMMUNO-NARRATIVE CACHE of the Linguistic Immune System.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from .types import (
    LIS_IncidentRecord,
    LIS_SemanticAnomalyDetectedEvent,
    LIS_AnomalyType,
    LIS_InterventionReport,
    NarrativeAntibodyObject,
    LIS_IncidentStatus
)
from ai.memory.ham_memory.ham_manager import HAMMemoryManager

logger = logging.getLogger(__name__)

# Constants for storage
LIS_INCIDENT_PREFIX = "lis_incident_v1_"
LIS_ANTIBODY_PREFIX = "lis_antibody_v1_"

class LISCacheInterface(ABC):
    """Abstract Base Class for the IMMUNO-NARRATIVE CACHE."""

    @abstractmethod
    async def store_incident(self, incident_record: LIS_IncidentRecord) -> bool:
        """Stores a new LIS incident record."""
        pass

    @abstractmethod
    async def get_incident_by_id(self, incident_id: str) -> Optional[LIS_IncidentRecord]:
        """Retrieves a specific LIS incident record by its unique ID."""
        pass

    @abstractmethod
    async def query_incidents(self, 
                                anomaly_type: Optional[LIS_AnomalyType] = None,
                                status: Optional[LIS_IncidentStatus] = None,
                                limit: int = 10) -> List[LIS_IncidentRecord]:
        """Queries the cache for LIS incident records."""
        pass

    @abstractmethod
    async def find_related_incidents(self, event: LIS_SemanticAnomalyDetectedEvent, top_n: int = 3) -> List[LIS_IncidentRecord]:
        """Finds past incidents that are semantically similar."""
        pass

    @abstractmethod
    async def store_antibody(self, antibody: NarrativeAntibodyObject) -> bool:
        """Stores a new narrative antibody."""
        pass

    @abstractmethod
    async def get_learned_antibodies(self, for_anomaly_type: Optional[LIS_AnomalyType] = None, limit: int = 5) -> List[NarrativeAntibodyObject]:
        """Retrieves learned antibodies."""
        pass

class HAMLISCache(LISCacheInterface):
    """Practical implementation of LISCache using HAM Memory System."""

    def __init__(self, ham_manager: HAMMemoryManager):
        self.ham_manager = ham_manager
        logger.info("HAMLISCache initialized.")

    async def store_incident(self, incident_record: LIS_IncidentRecord) -> bool:
        """Stores incident into HAM using its rehydrated gist capability."""
        try:
            mem_id = f"{LIS_INCIDENT_PREFIX}{incident_record['incident_id']}"
            metadata = {
                "type": "lis_incident",
                "anomaly_type": incident_record["anomaly_event"]["anomaly_type"],
                "status": incident_record["status"],
                "severity": incident_record["anomaly_event"]["severity_score"],
                "timestamp": incident_record["timestamp_logged"]
            }
            # Store in HAM
            success = await self.ham_manager.store_experience(
                raw_data=incident_record,
                data_type="lis_incident",
                metadata=metadata
            )
            return success is not None
        except Exception as e:
            logger.error(f"Failed to store incident in HAMLISCache: {e}")
            return False

    async def get_incident_by_id(self, incident_id: str) -> Optional[LIS_IncidentRecord]:
        # Querying HAM by metadata filter
        results = await self.ham_manager.query_core_memory(
            metadata_filters={"incident_id": incident_id},
            data_type_filter="lis_incident",
            limit=1
        )
        if results:
            return results[0].get("rehydrated_gist")
        return None

    async def query_incidents(self, 
                                anomaly_type: Optional[LIS_AnomalyType] = None,
                                status: Optional[LIS_IncidentStatus] = None,
                                limit: int = 10) -> List[LIS_IncidentRecord]:
        filters = {}
        if anomaly_type:
            filters["anomaly_type"] = anomaly_type
        if status:
            filters["status"] = status
            
        results = await self.ham_manager.query_core_memory(
            metadata_filters=filters,
            data_type_filter="lis_incident",
            limit=limit
        )
        return [r.get("rehydrated_gist") for r in results if r.get("rehydrated_gist")]

    async def find_related_incidents(self, event: LIS_SemanticAnomalyDetectedEvent, top_n: int = 3) -> List[LIS_IncidentRecord]:
        # In a real system, this would use vector similarity. 
        # Here we fallback to type matching in HAM.
        return await self.query_incidents(anomaly_type=event["anomaly_type"], limit=top_n)

    async def store_antibody(self, antibody: NarrativeAntibodyObject) -> bool:
        try:
            metadata = {
                "type": "lis_antibody",
                "primary_type": antibody["target_anomaly_types"][0] if antibody["target_anomaly_types"] else "GENERIC",
                "effectiveness": antibody["effectiveness_score"],
                "timestamp": antibody["timestamp_created"]
            }
            success = await self.ham_manager.store_experience(
                raw_data=antibody,
                data_type="lis_antibody",
                metadata=metadata
            )
            return success is not None
        except Exception as e:
            logger.error(f"Failed to store antibody: {e}")
            return False

    async def get_learned_antibodies(self, for_anomaly_type: Optional[LIS_AnomalyType] = None, limit: int = 5) -> List[NarrativeAntibodyObject]:
        filters = {}
        if for_anomaly_type:
            filters["primary_type"] = for_anomaly_type
            
        results = await self.ham_manager.query_core_memory(
            metadata_filters=filters,
            data_type_filter="lis_antibody",
            limit=limit
        )
        # Sort by effectiveness desc
        gists = [r.get("rehydrated_gist") for r in results if r.get("rehydrated_gist")]
        gists.sort(key=lambda x: x.get("effectiveness_score", 0.0), reverse=True)
        return gists
