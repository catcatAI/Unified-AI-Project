"""
Autonomous Endocrine System Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""
from __future__ import annotations

from core.bio.endocrine_system_core import (
    EndocrineSystem,
)
from core.bio.endocrine_types import (
    HormoneType,
    Hormone,
    HormonalEffect,
)
from core.bio.hormone_kinetics import (
    ReceptorStatus,
    HormoneKinetics,
)
from core.bio.feedback_loop import (
    FeedbackNode,
    FeedbackLoop,
)