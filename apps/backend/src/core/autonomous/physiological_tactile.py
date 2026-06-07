"""
Autonomous Physiological Tactile Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""
from __future__ import annotations

from core.bio.physiological_tactile_system import (
    PhysiologicalTactileSystem,
)
from core.bio.physiological_tactile_types import (
    ReceptorType,
    TactileType,
    BodyRegion,
    BodyPart,
    Receptor,
    TactileStimulus,
    EmotionalTactileMapping,
    TactileResponse,
    Live2DTouchResponse,
)
from core.bio.physiological_tactile_analysis import (
    TrajectoryPoint,
    TrajectoryAnalysis,
    TrajectoryAnalyzer,
    ReceptorAdaptationState,
    AdaptationMechanism,
)