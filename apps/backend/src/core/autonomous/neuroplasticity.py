"""
Autonomous Neuroplasticity Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""
from __future__ import annotations

from core.bio.neuroplasticity_core import (
    NeuroplasticitySystem,
    MemoryTrace,
    HebbianRule,
    SynapticState,
    ConsolidationPhase,
    SynapticWeight,
    LTPParameters,
    LTDParameters,
    EbbinghausForgettingCurve,
)
from core.bio.skill_acquisition import (
    SkillAcquisition,
    SkillTrace,
)
from core.bio.habit_formation import (
    HabitFormation,
    HabitTrace,
)
from core.bio.trauma_memory import (
    TraumaMemorySystem,
    TraumaMemory,
)
from core.bio.explicit_implicit_learning import (
    ExplicitImplicitLearning,
    LearningEvent,
)