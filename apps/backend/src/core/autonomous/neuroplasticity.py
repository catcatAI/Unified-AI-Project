"""
Autonomous Neuroplasticity Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""

from __future__ import annotations

from core.bio.explicit_implicit_learning import (
    ExplicitImplicitLearning,
    LearningEvent,
)
from core.bio.habit_formation import (
    HabitFormation,
    HabitTrace,
)
from core.bio.neuroplasticity_core import (
    ConsolidationPhase,
    EbbinghausForgettingCurve,
    HebbianRule,
    LTDParameters,
    LTPParameters,
    MemoryTrace,
    NeuroplasticitySystem,
    SynapticState,
    SynapticWeight,
)
from core.bio.skill_acquisition import (
    SkillAcquisition,
    SkillTrace,
)
from core.bio.trauma_memory import (
    TraumaMemory,
    TraumaMemorySystem,
)
