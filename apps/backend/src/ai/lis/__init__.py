"""
LIS (Linguistic Immune System) Sub-package.
Responsible for detecting, diagnosing, and responding to semantic anomalies.
"""

import logging

logger = logging.getLogger(__name__)

from .lis_manager import LISManager  # noqa: E402
from .lis_cache_interface import LISCacheInterface, HAMLISCache  # noqa: E402
from .err_introspector import ERRIntrospector  # noqa: E402
from .types import (  # noqa: E402
    LIS_AnomalyType,
    LIS_SemanticAnomalyDetectedEvent,
    LIS_IncidentRecord,
    NarrativeAntibodyObject,
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
    "NarrativeAntibodyObject",
]
