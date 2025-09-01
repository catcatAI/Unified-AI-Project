from typing import TypedDict, Optional, List, Literal

LIS_AnomalyType = Literal["RHYTHM_BREAK", "LOW_DIVERSITY", "UNEXPECTED_TONE_SHIFT"]
LIS_SeverityScore = float
LIS_InterventionOutcome = Literal["SUCCESS", "FAILURE"]

class LIS_SemanticAnomalyDetectedEvent(TypedDict):
    anomaly_type: LIS_AnomalyType
    severity: LIS_SeverityScore
    # ... other fields if absolutely necessary for import

class LIS_InterventionReport(TypedDict):
    outcome: LIS_InterventionOutcome
    # ...

class LIS_IncidentRecord(TypedDict):
    incident_id: str
    anomaly_event: LIS_SemanticAnomalyDetectedEvent
    intervention_reports: Optional[List[LIS_InterventionReport]]
    # ...

class NarrativeAntibodyObject(TypedDict):
    antibody_id: str
    # ...
