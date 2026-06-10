"""
LIS (Linguistic Immune System) Sub-package.
Responsible for detecting, diagnosing, and responding to semantic anomalies.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# =============================================================================
# DEPRECATED: This subpackage has no production consumers.
# Retained for reference — not wired into the running system.
# See MASTER_CONSOLIDATED_PLAN.md § Phase 4 Priority 2.
# =============================================================================

import logging

logger = logging.getLogger(__name__)

try:
    from .lis_manager import LISManager  # noqa: E402
except ImportError:
    LISManager = None
try:
    from .lis_cache_interface import LISCacheInterface, HAMLISCache  # noqa: E402
except ImportError:
    LISCacheInterface = HAMLISCache = None
try:
    from .err_introspector import ERRIntrospector  # noqa: E402
except ImportError:
    ERRIntrospector = None
try:
    from .types import (  # noqa: E402
        LIS_AnomalyType,
        LIS_SemanticAnomalyDetectedEvent,
        LIS_IncidentRecord,
        NarrativeAntibodyObject,
    )
except ImportError:
    LIS_AnomalyType = LIS_SemanticAnomalyDetectedEvent = LIS_IncidentRecord = NarrativeAntibodyObject = None

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
