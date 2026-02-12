from typing import TypedDict, Optional, List, Literal, Dict, Any
import logging
logger = logging.getLogger(__name__)

LIS_AnomalyType = Literal[
    "RHYTHM_BREAK", 
    "LOW_DIVERSITY", 
    "UNEXPECTED_TONE_SHIFT", 
    "NARRATIVE_DIVERGENCE",
    "INTERNAL_STATE_MISALIGNMENT",
    "REPETITION_ECHO"
]

LIS_SeverityScore = float
LIS_InterventionOutcome = Literal["SUCCESS", "FAILURE", "PENDING", "PARTIAL"]
LIS_IncidentStatus = Literal["OPEN", "ANALYZED", "INTERVENED", "CLOSED_RESOLVED", "CLOSED_IGNORED"]

class LIS_SemanticAnomalyDetectedEvent(TypedDict):
    anomaly_id: str
    anomaly_type: LIS_AnomalyType
    severity_score: LIS_SeverityScore
    description: str
    context_snippet: str
    timestamp_detected: str
    metadata: Dict[str, Any]

class LIS_InterventionReport(TypedDict):
    report_id: str
    strategy_used: str
    outcome: LIS_InterventionOutcome
    details: str
    timestamp_intervention: str

class LIS_IncidentRecord(TypedDict):
    incident_id: str
    status: LIS_IncidentStatus
    anomaly_event: LIS_SemanticAnomalyDetectedEvent
    intervention_reports: List[LIS_InterventionReport]
    tags: List[str]
    timestamp_logged: str

class NarrativeAntibodyObject(TypedDict):
    antibody_id: str
    target_anomaly_types: List[LIS_AnomalyType]
    trigger_conditions: Dict[str, Any]
    response_pattern: Dict[str, Any]
    effectiveness_score: float
    usage_count: int
    timestamp_created: str
    version: str
