# ANGELA-MATRIX: L0[基础层] [A] L1

import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class LIS_AnomalyType(str, enum.Enum):
    REPETITION_ECHO = "REPETITION_ECHO"
    ETHICAL_DIVERGENCE = "ETHICAL_DIVERGENCE"
    ADVERSARIAL_PROMPT = "ADVERSARIAL_PROMPT"
    CONTEXT_DRIFT = "CONTEXT_DRIFT"
    SEMANTIC_INJECTION = "SEMANTIC_INJECTION"


@dataclass
class LIS_SemanticAnomalyDetectedEvent:
    anomaly_id: str
    anomaly_type: str
    severity_score: float
    description: str
    context_snippet: str
    timestamp_detected: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LIS_IncidentRecord:
    incident_id: str
    status: str
    anomaly_event: dict[str, Any]
    intervention_reports: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    timestamp_logged: str = ""


@dataclass
class NarrativeAntibodyObject:
    antibody_id: str
    target_anomaly_types: list[str]
    trigger_conditions: dict[str, Any]
    response_pattern: dict[str, Any]
    effectiveness_score: float
    usage_count: int
    timestamp_created: str
    version: str


__all__ = [
    "LIS_AnomalyType",
    "LIS_SemanticAnomalyDetectedEvent",
    "LIS_IncidentRecord",
    "NarrativeAntibodyObject",
]
