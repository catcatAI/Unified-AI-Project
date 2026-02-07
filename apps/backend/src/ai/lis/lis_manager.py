"""
LIS Manager: Orchestrator of the Linguistic Immune System.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .types import (
    LIS_SemanticAnomalyDetectedEvent,
    LIS_IncidentRecord,
    LIS_IncidentStatus
)
from .err_introspector import ERRIntrospector
from .lis_cache_interface import HAMLISCache

logger = logging.getLogger(__name__)

class LISManager:
    """
    LISManager coordinates the Introspector and the Cache.
    It acts as the primary interface for other AI components to use LIS services.
    """

    def __init__(self, cache: HAMLISCache, config: Optional[Dict[str, Any]] = None):
        self.cache = cache
        self.config = config or {}
        self.introspector = ERRIntrospector(self.config.get("introspector_config"))
        logger.info("LISManager initialized.")

    async def monitor_output(self, output_text: str, context: Dict[str, Any]) -> List[LIS_SemanticAnomalyDetectedEvent]:
        """
        Monitors an output string. If anomalies are found, they are logged as incidents.
        """
        anomalies = await self.introspector.analyze_output(output_text, context)
        
        for anomaly in anomalies:
            logger.warning(f"LIS Anomaly Detected: {anomaly['anomaly_type']} - {anomaly['description']}")
            # Create an incident record
            incident: LIS_IncidentRecord = {
                "incident_id": f"inc_{uuid.uuid4().hex[:8]}",
                "status": "OPEN",
                "anomaly_event": anomaly,
                "intervention_reports": [],
                "tags": ["auto_detected", anomaly["anomaly_type"].lower()],
                "timestamp_logged": datetime.now(timezone.utc).isoformat()
            }
            # Auto-save to cache
            await self.cache.store_incident(incident)
            
        return anomalies

    async def get_system_health(self) -> Dict[str, Any]:
        """Returns a summary of recent incidents (Semantic Health)."""
        recent_incidents = await self.cache.query_incidents(limit=5)
        return {
            "status": "HEALTHY" if not recent_incidents else "OBSERVATION",
            "recent_incidents_count": len(recent_incidents),
            "latest_incidents": recent_incidents
        }
