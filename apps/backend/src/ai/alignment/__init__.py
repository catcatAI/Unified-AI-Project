# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# Alignment Systems Package
"""
AGI / ASI 对齐系统包, 包含理智、感性和存在三大支柱系统,
以及决策论系统、对抗性生成系统和ASI自主对齐机制
"""

import logging

try:
    from .reasoning_system import ReasoningSystem
except ImportError:
    ReasoningSystem = None

logger = logging.getLogger(__name__)

_MAX_EMOTION_HISTORY = 500
_MAX_CHECK_HISTORY = 200


# Full implementations for alignment subsystem management
# NOTE: previously the three classes below were defined inline as always-present
# stubs that SHADOWED the real implementations in the submodules, so
# `from ai.alignment import EmotionSystem` returned the weak stub instead of the
# real class. They are now re-exported as the single source of truth.
from .emotion_system import EmotionSystem


from .ontology_system import OntologySystem


try:
    from .alignment_manager import AlignmentManager
except ImportError:
    logger.debug("alignment_manager not available, using stub")

    class AlignmentManager:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "AlignmentManager requires ai.alignment.alignment_manager module. "
                "Install with: pip install -e 'apps/backend[ml]'"
            )


try:
    from .decision_theory_system import DecisionTheorySystem
except ImportError:
    logger.debug("decision_theory_system not available, using stub")

    class DecisionTheorySystem:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "DecisionTheorySystem requires ai.alignment.decision_theory_system module. "
                "Install with: pip install -e 'apps/backend[ml]'"
            )


try:
    from .adversarial_generation_system import AdversarialGenerationSystem
except ImportError:
    logger.debug("adversarial_generation_system not available, using stub")

    class AdversarialGenerationSystem:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "AdversarialGenerationSystem requires ai.alignment.adversarial_generation_system module. "
                "Install with: pip install -e 'apps/backend[ml]'"
            )


from .asi_autonomous_alignment import ASIAutonomousAlignment


__all__ = [
    "ReasoningSystem",
    "EmotionSystem",
    "OntologySystem",
    "AlignmentManager",
    "DecisionTheorySystem",
    "AdversarialGenerationSystem",
    "ASIAutonomousAlignment",
]
