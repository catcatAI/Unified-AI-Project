# ANGELA-MATRIX: L3 [γ] [A] [L0-L11]
"""Angela AI bio subpackage — bio systems."""

from core.bio.autonomic_nervous_system import (
    AutonomicNervousSystem,
    ANSState,
    NerveType,
    StimulusFactor,
    PhysiologicalEffects,
    EmotionalEffects,
    CognitiveEffects,
)
from core.bio.biological_integrator import BiologicalIntegrator, BiologicalEvent, BiologicalEventPublisher, SystemInteraction
from core.bio.cerebellum_engine import CerebellumEngine
from core.bio.emotional_blending import (
    EmotionalBlendingSystem,
    EmotionalExpression,
    EmotionalInfluence,
    PADEmotion,
    BasicEmotion,
    FacialExpression,
    VocalTone,
    BehavioralExpression,
    StateDimension,
    MultidimensionalStateMatrix,
)
from core.bio.endocrine_system import EndocrineSystem
from core.bio.endocrine_system_core import EndocrineSystem as EndocrineSystemCore
from core.bio.endocrine_types import Hormone, HormoneType, HormonalEffect
from core.bio.explicit_implicit_learning import ExplicitImplicitLearning, LearningEvent
from core.bio.extended_behavior_library import ExtendedBehaviorLibrary, BehaviorDefinition, BehaviorTrigger, BehaviorCategory, BehaviorPriority
from core.bio.feedback_loop import FeedbackLoop, FeedbackNode
from core.bio.habit_formation import HabitFormation, HabitTrace
from core.bio.hormone_kinetics import HormoneKinetics, ReceptorStatus
from core.bio.input_sensor import GlobalInputSensor
from core.bio.kinetic_validator import KineticValidator
from core.bio.multidimensional_trigger import MultidimensionalTriggerSystem, MultidimensionalTrigger, TriggerCondition, DimensionValue, TriggerDimension
from core.bio.neuroplasticity_core import NeuroplasticitySystem, SynapticWeight, MemoryTrace, HebbianRule, SynapticState, ConsolidationPhase, LTPParameters, LTDParameters, EbbinghausForgettingCurve
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
from core.bio.physiological_tactile_system import PhysiologicalTactileSystem
from core.bio.physiological_tactile_analysis import TrajectoryPoint, TrajectoryAnalysis, TrajectoryAnalyzer, ReceptorAdaptationState, AdaptationMechanism
from core.bio.skill_acquisition import SkillAcquisition, SkillTrace
from core.bio.trauma_memory import TraumaMemory, TraumaMemorySystem

__all__ = [
    "AutonomicNervousSystem",
    "ANSState",
    "NerveType",
    "StimulusFactor",
    "PhysiologicalEffects",
    "EmotionalEffects",
    "CognitiveEffects",
    "BiologicalIntegrator",
    "BiologicalEvent",
    "BiologicalEventPublisher",
    "SystemInteraction",
    "CerebellumEngine",
    "EmotionalBlendingSystem",
    "EmotionalExpression",
    "EmotionalInfluence",
    "PADEmotion",
    "BasicEmotion",
    "FacialExpression",
    "VocalTone",
    "BehavioralExpression",
    "StateDimension",
    "MultidimensionalStateMatrix",
    "EndocrineSystem",
    "EndocrineSystemCore",
    "Hormone",
    "HormoneType",
    "HormonalEffect",
    "ExplicitImplicitLearning",
    "LearningEvent",
    "ExtendedBehaviorLibrary",
    "BehaviorDefinition",
    "BehaviorTrigger",
    "BehaviorCategory",
    "BehaviorPriority",
    "FeedbackLoop",
    "FeedbackNode",
    "HabitFormation",
    "HabitTrace",
    "HormoneKinetics",
    "ReceptorStatus",
    "GlobalInputSensor",
    "KineticValidator",
    "MultidimensionalTriggerSystem",
    "MultidimensionalTrigger",
    "TriggerCondition",
    "DimensionValue",
    "TriggerDimension",
    "NeuroplasticitySystem",
    "SynapticWeight",
    "MemoryTrace",
    "HebbianRule",
    "SynapticState",
    "ConsolidationPhase",
    "LTPParameters",
    "LTDParameters",
    "EbbinghausForgettingCurve",
    "ReceptorType",
    "TactileType",
    "BodyRegion",
    "BodyPart",
    "Receptor",
    "TactileStimulus",
    "EmotionalTactileMapping",
    "TactileResponse",
    "Live2DTouchResponse",
    "PhysiologicalTactileSystem",
    "TrajectoryPoint",
    "TrajectoryAnalysis",
    "TrajectoryAnalyzer",
    "ReceptorAdaptationState",
    "AdaptationMechanism",
    "SkillAcquisition",
    "SkillTrace",
    "TraumaMemory",
    "TraumaMemorySystem",
]
