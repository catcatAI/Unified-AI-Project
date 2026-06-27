"""
Angela AI v6.0 - Neuroplasticity System
神经可塑性系统

Split into submodules for maintainability.
All public classes re-exported from here for backwards compatibility.
"""

from .explicit_implicit_learning import (  # noqa: F401
    ExplicitImplicitLearning,
    LearningEvent,
)
from .habit_formation import (  # noqa: F401
    HabitFormation,
    HabitTrace,
)
from .neuroplasticity_core import (  # noqa: F401
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
from .skill_acquisition import (  # noqa: F401
    SkillAcquisition,
    SkillTrace,
)
from .trauma_memory import (  # noqa: F401
    TraumaMemory,
    TraumaMemorySystem,
)
