"""
LIS (Linguistic Immune System) Sub-package.
Responsible for detecting, diagnosing, and responding to semantic anomalies.
"""

from .lis_manager import LISManager
from .lis_cache_interface import LISCacheInterface, HAMLISCache
from .err_introspector import ERRIntrospector
from .types import (
import logging
logger = logging.getLogger(__name__)
    LIS_AnomalyType,
    LIS_SemanticAnomalyDetectedEvent,
    LIS_IncidentRecord,
    NarrativeAntibodyObject
)

VERSION = "0.1.0"
__all__ = [
    "LISManager",
    "LISCacheInterface",
    "HAMLISCache",
    "ERRIntrospector",
    "LIS_AnomalyType",
    "LIS_SemanticAnomalyDetectedEvent",
    "LIS_IncidentRecord",
    "NarrativeAntibodyObject"
]
