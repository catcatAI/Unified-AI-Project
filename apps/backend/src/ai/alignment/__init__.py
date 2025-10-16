# Alignment Systems Package
"""
AGI/ASI 对齐系统包，包含理智、感性和存在三大支柱系统，
以及决策论系统、对抗性生成系统和ASI自主对齐机制
"""

from .reasoning_system import ReasoningSystem
from .emotion_system import EmotionSystem
from .ontology_system import OntologySystem
from .alignment_manager import AlignmentManager
from .decision_theory_system import DecisionTheorySystem
from .adversarial_generation_system import AdversarialGenerationSystem
from .asi_autonomous_alignment import ASIAutonomousAlignment

__all__ = [
    'ReasoningSystem',
    'EmotionSystem',
    'OntologySystem',
    'AlignmentManager',
    'DecisionTheorySystem',
    'AdversarialGenerationSystem',
    'ASIAutonomousAlignment'
]