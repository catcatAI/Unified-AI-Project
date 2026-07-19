"""
Autonomous Physiological Tactile Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""

from __future__ import annotations

from core.bio.physiological_tactile_analysis import (
    AdaptationMechanism,
    ReceptorAdaptationState,
    TrajectoryAnalysis,
    TrajectoryAnalyzer,
    TrajectoryPoint,
)
from core.bio.physiological_tactile_system import (
    PhysiologicalTactileSystem,
)
from core.bio.physiological_tactile_types import (
    BodyPart,
    BodyRegion,
    EmotionalTactileMapping,
    Live2DTouchResponse,
    Receptor,
    ReceptorType,
    TactileResponse,
    TactileStimulus,
    TactileType,
)
