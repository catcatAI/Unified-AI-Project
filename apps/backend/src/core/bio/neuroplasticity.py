"""
Angela AI v6.0 - Neuroplasticity System
神经可塑性系统

Split into submodules for maintainability.
All public classes re-exported from here for backwards compatibility.
"""

from .neuroplasticity_core import (  # noqa: F401
    SynapticState,
    ConsolidationPhase,
    SynapticWeight,
    MemoryTrace,
    HebbianRule,
    LTPParameters,
    LTDParameters,
    EbbinghausForgettingCurve,
    NeuroplasticitySystem,
)
from .skill_acquisition import (  # noqa: F401
    SkillTrace,
    SkillAcquisition,
)
from .habit_formation import (  # noqa: F401
    HabitTrace,
    HabitFormation,
)
from .trauma_memory import (  # noqa: F401
    TraumaMemory,
    TraumaMemorySystem,
)
from .explicit_implicit_learning import (  # noqa: F401
    LearningEvent,
    ExplicitImplicitLearning,
)
