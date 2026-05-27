"""
Angela AI v7.5.0-dev - Autonomous System Package (Backward Compat Shim)
=======================================================================
A3 refactor: all modules moved to core/{life,bio,engine}/ subpackages.
This file re-exports everything from the new locations for backward compatibility.
"""

import logging

logger = logging.getLogger(__name__)

# =============================================================================
# Biological Simulation Systems → core/bio/
# =============================================================================
try:
    from core.bio.physiological_tactile import (
        PhysiologicalTactileSystem,
        Receptor,
        BodyPart,
        TrajectoryAnalyzer,
        TrajectoryPoint,
        TrajectoryAnalysis,
        AdaptationMechanism,
        ReceptorAdaptationState,
    )
except ImportError as e:
    logger.warning(f"Failed to import physiological_tactile: {e}")
    PhysiologicalTactileSystem = None
    Receptor = None
    BodyPart = None
    TrajectoryAnalyzer = None
    TrajectoryPoint = None
    TrajectoryAnalysis = None
    AdaptationMechanism = None
    ReceptorAdaptationState = None

try:
    from core.bio.endocrine_system import (
        EndocrineSystem,
        Hormone,
        HormoneType,
        HormoneKinetics,
        ReceptorStatus,
        FeedbackLoop,
        FeedbackNode,
    )
except ImportError as e:
    logger.warning(f"Failed to import endocrine_system: {e}")
    EndocrineSystem = None
    Hormone = None
    HormoneType = None
    HormoneKinetics = None
    ReceptorStatus = None
    FeedbackLoop = None
    FeedbackNode = None

try:
    from core.bio.autonomic_nervous_system import AutonomicNervousSystem, ANSState, NerveType
except ImportError as e:
    logger.warning(f"Failed to import autonomic_nervous_system: {e}")
    AutonomicNervousSystem = None
    ANSState = None
    NerveType = None

try:
    from core.bio.neuroplasticity import (
        NeuroplasticitySystem,
        MemoryTrace,
        HebbianRule,
        SkillAcquisition,
        SkillTrace,
        HabitFormation,
        HabitTrace,
        TraumaMemorySystem,
        TraumaMemory,
        ExplicitImplicitLearning,
        LearningEvent,
    )
except ImportError as e:
    logger.warning(f"Failed to import neuroplasticity: {e}")
    NeuroplasticitySystem = None
    MemoryTrace = None
    HebbianRule = None
    SkillAcquisition = None
    SkillTrace = None
    HabitFormation = None
    HabitTrace = None
    TraumaMemorySystem = None
    TraumaMemory = None
    ExplicitImplicitLearning = None
    LearningEvent = None

try:
    from core.bio.emotional_blending import (
        EmotionalBlendingSystem,
        PADEmotion,
        EmotionalExpression,
        MultidimensionalStateMatrix,
        StateDimension,
    )
except ImportError as e:
    logger.warning(f"Failed to import emotional_blending: {e}")
    EmotionalBlendingSystem = None
    PADEmotion = None
    EmotionalExpression = None
    MultidimensionalStateMatrix = None
    StateDimension = None

try:
    from core.bio.biological_integrator import BiologicalIntegrator, SystemInteraction
except ImportError as e:
    logger.warning(f"Failed to import biological_integrator: {e}")
    BiologicalIntegrator = None
    SystemInteraction = None

try:
    from core.bio.memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge, MemoryConsolidation
except ImportError as e:
    logger.warning(f"Failed to import memory_neuroplasticity_bridge: {e}")
    MemoryNeuroplasticityBridge = None
    MemoryConsolidation = None

try:
    from core.bio.extended_behavior_library import ExtendedBehaviorLibrary, BehaviorDefinition
except ImportError as e:
    logger.warning(f"Failed to import extended_behavior_library: {e}")
    ExtendedBehaviorLibrary = None
    BehaviorDefinition = None

try:
    from core.bio.multidimensional_trigger import MultidimensionalTriggerSystem, TriggerDimension
except ImportError as e:
    logger.warning(f"Failed to import multidimensional_trigger: {e}")
    MultidimensionalTriggerSystem = None
    TriggerDimension = None

# =============================================================================
# Execution Systems → core/engine/
# =============================================================================
try:
    from core.engine.state_matrix import StateMatrix4D, DimensionState
except ImportError as e:
    logger.warning(f"Failed to import state_matrix: {e}")
    StateMatrix4D = None
    DimensionState = None

try:
    from core.engine.action_executor import (
        ActionExecutor,
        ActionQueue,
        ActionPriority,
        Action,
        ActionResult,
        ActionStatus,
        ActionCategory,
    )
except ImportError as e:
    logger.warning(f"Failed to import action_executor: {e}")
    ActionExecutor = None
    ActionQueue = None
    ActionPriority = None
    Action = None
    ActionResult = None
    ActionStatus = None
    ActionCategory = None

try:
    from core.engine.desktop_interaction import DesktopInteraction, FileOperation, DesktopState
except ImportError as e:
    logger.warning(f"Failed to import desktop_interaction: {e}")
    DesktopInteraction = None
    FileOperation = None
    DesktopState = None

try:
    from core.engine.browser_controller import BrowserController, SearchResult, BrowserState
except ImportError as e:
    logger.warning(f"Failed to import browser_controller: {e}")
    BrowserController = None
    SearchResult = None
    BrowserState = None

try:
    from core.engine.audio_system import AudioSystem, TTSConfig, LyricsSync
except ImportError as e:
    logger.warning(f"Failed to import audio_system: {e}")
    AudioSystem = None
    TTSConfig = None
    LyricsSync = None

try:
    from core.engine.desktop_presence import DesktopPresence, MouseTracker
except ImportError as e:
    logger.warning(f"Failed to import desktop_presence: {e}")
    DesktopPresence = None
    MouseTracker = None

try:
    from core.engine.live2d_integration import Live2DIntegration, Live2DExpression, Live2DAction
except ImportError as e:
    logger.warning(f"Failed to import live2d_integration: {e}")
    Live2DIntegration = None
    Live2DExpression = None
    Live2DAction = None

# =============================================================================
# Integration Systems → core/life/ + core/bio/
# =============================================================================
try:
    from core.life.digital_life_integrator import DigitalLifeIntegrator, LifeCycleState
except ImportError as e:
    logger.warning(f"Failed to import digital_life_integrator: {e}")
    DigitalLifeIntegrator = None
    LifeCycleState = None

try:
    from core.life.cyber_identity import CyberIdentity, SelfModel, IdentityGrowth
except ImportError as e:
    logger.warning(f"Failed to import cyber_identity: {e}")
    CyberIdentity = None
    SelfModel = None
    IdentityGrowth = None

try:
    from core.life.self_generation import SelfGeneration, AvatarBuilder
except ImportError as e:
    logger.warning(f"Failed to import self_generation: {e}")
    SelfGeneration = None
    AvatarBuilder = None

# =============================================================================
# Art Learning and Live2D Generation Systems → core/engine/
# =============================================================================
try:
    from core.engine.art_learning_system import (
        ArtLearningSystem,
        ArtKnowledge,
        ArtDomain,
        TutorialContent,
        ImageAnalysis,
        LearningSession,
        BodyPartMapping,
        Live2DParameter,
        LearningType,
    )
except ImportError as e:
    logger.warning(f"Failed to import art_learning_system: {e}")
    ArtLearningSystem = None
    ArtKnowledge = None
    ArtDomain = None
    TutorialContent = None
    ImageAnalysis = None
    LearningSession = None
    BodyPartMapping = None
    Live2DParameter = None
    LearningType = None

try:
    from core.engine.live2d_avatar_generator import (
        Live2DAvatarGenerator,
        GeneratedAvatar,
        Live2DModelConfig,
        GenerationStage,
        ViewAngle,
        BodyLayer,
    )
except ImportError as e:
    logger.warning(f"Failed to import live2d_avatar_generator: {e}")
    Live2DAvatarGenerator = None
    GeneratedAvatar = None
    Live2DModelConfig = None
    GenerationStage = None
    ViewAngle = None
    BodyLayer = None

try:
    from core.engine.art_learning_workflow import (
        ArtLearningWorkflow,
        WorkflowStage,
        LearningObjective,
        WorkflowProgress,
        SkillAssessment,
        GenerationResult,
        WorkflowConfig,
    )
except ImportError as e:
    logger.warning(f"Failed to import art_learning_workflow: {e}")
    ArtLearningWorkflow = None
    WorkflowStage = None
    LearningObjective = None
    WorkflowProgress = None
    SkillAssessment = None
    GenerationResult = None
    WorkflowConfig = None

try:
    from core.life.autonomous_life_cycle import AutonomousLifeCycle, LifePhase, LifeDecision, FormulaMetrics
except ImportError as e:
    logger.warning(f"Failed to import autonomous_life_cycle: {e}")
    AutonomousLifeCycle = None
    LifePhase = None
    LifeDecision = None
    FormulaMetrics = None

__version__ = "7.5.0-dev"
__author__ = "Angela AI Development Team"

__all__ = [
    "__version__", "__author__",
    "PhysiologicalTactileSystem", "Receptor", "BodyPart", "TrajectoryAnalyzer",
    "TrajectoryPoint", "TrajectoryAnalysis", "AdaptationMechanism", "ReceptorAdaptationState",
    "EndocrineSystem", "Hormone", "HormoneType", "HormoneKinetics", "ReceptorStatus",
    "FeedbackLoop", "FeedbackNode",
    "AutonomicNervousSystem", "ANSState", "NerveType",
    "NeuroplasticitySystem", "MemoryTrace", "HebbianRule", "SkillAcquisition",
    "SkillTrace", "HabitFormation", "HabitTrace", "TraumaMemorySystem", "TraumaMemory",
    "ExplicitImplicitLearning", "LearningEvent",
    "EmotionalBlendingSystem", "PADEmotion", "EmotionalExpression",
    "MultidimensionalStateMatrix", "StateDimension",
    "StateMatrix4D", "DimensionState",
    "ActionExecutor", "ActionQueue", "ActionPriority", "Action", "ActionResult",
    "ActionStatus", "ActionCategory",
    "DesktopInteraction", "FileOperation", "DesktopState",
    "BrowserController", "SearchResult", "BrowserState",
    "AudioSystem", "TTSConfig", "LyricsSync",
    "DesktopPresence", "MouseTracker",
    "Live2DIntegration", "Live2DExpression", "Live2DAction",
    "BiologicalIntegrator", "SystemInteraction",
    "DigitalLifeIntegrator", "LifeCycleState",
    "MemoryNeuroplasticityBridge", "MemoryConsolidation",
    "ExtendedBehaviorLibrary", "BehaviorDefinition",
    "MultidimensionalTriggerSystem", "TriggerDimension",
    "CyberIdentity", "SelfModel", "IdentityGrowth",
    "SelfGeneration", "AvatarBuilder",
    "AutonomousLifeCycle", "LifePhase", "LifeDecision", "FormulaMetrics",
    "ArtLearningSystem", "ArtKnowledge", "ArtDomain", "TutorialContent",
    "ImageAnalysis", "LearningSession", "BodyPartMapping", "Live2DParameter", "LearningType",
    "Live2DAvatarGenerator", "GeneratedAvatar", "Live2DModelConfig",
    "GenerationStage", "ViewAngle", "BodyLayer",
    "ArtLearningWorkflow", "WorkflowStage", "LearningObjective",
    "WorkflowProgress", "SkillAssessment", "GenerationResult", "WorkflowConfig",
]


def get_system_info() -> dict:
    """Get comprehensive information about the autonomous system package."""
    return {
        "version": __version__,
        "author": __author__,
        "modules": {
            "biological": [
                "physiological_tactile", "endocrine_system", "autonomic_nervous_system",
                "neuroplasticity", "emotional_blending", "state_matrix",
            ],
            "execution": [
                "action_executor", "desktop_interaction", "browser_controller",
                "audio_system", "desktop_presence", "live2d_integration",
            ],
            "integration": [
                "biological_integrator", "digital_life_integrator",
                "memory_neuroplasticity_bridge", "extended_behavior_library",
                "multidimensional_trigger", "cyber_identity", "self_generation",
                "autonomous_life_cycle",
            ],
            "art_learning": [
                "art_learning_system", "live2d_avatar_generator", "art_learning_workflow",
            ],
        },
        "capabilities": [
            "biological_simulation", "hormonal_regulation", "neural_plasticity",
            "emotional_blending", "trajectory_analysis", "receptor_adaptation",
            "hormone_kinetics", "feedback_regulation", "skill_acquisition",
            "habit_formation", "trauma_memory", "explicit_implicit_learning",
            "multidimensional_state_matrix", "action_execution", "desktop_interaction",
            "browser_control", "audio_synthesis", "live2d_animation",
            "memory_consolidation", "behavior_generation", "identity_formation",
            "self_generation", "autonomous_life_cycle", "theoretical_frameworks",
            "hsm_formula", "cdm_model", "life_intensity", "active_cognition",
            "non_paradox_existence", "art_learning", "live2d_generation",
            "anime_style_learning", "tutorial_search", "image_analysis",
            "body_part_rigging", "physiological_live2d_bridge",
            "skill_acquisition_power_law", "implicit_style_learning",
        ],
    }


async def initialize_all_systems() -> dict:
    """Initialize all autonomous systems for Angela AI."""
    from core.bio.physiological_tactile import PhysiologicalTactileSystem
    from core.bio.endocrine_system import EndocrineSystem
    from core.bio.autonomic_nervous_system import AutonomicNervousSystem
    from core.bio.neuroplasticity import NeuroplasticitySystem
    from core.bio.emotional_blending import EmotionalBlendingSystem
    from core.engine.action_executor import ActionExecutor
    from core.engine.desktop_interaction import DesktopInteraction
    from core.engine.browser_controller import BrowserController
    from core.engine.audio_system import AudioSystem
    from core.engine.desktop_presence import DesktopPresence
    from core.engine.live2d_integration import Live2DIntegration
    from core.bio.biological_integrator import BiologicalIntegrator
    from core.life.digital_life_integrator import DigitalLifeIntegrator
    from core.bio.memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge
    from core.bio.extended_behavior_library import ExtendedBehaviorLibrary
    from core.bio.multidimensional_trigger import MultidimensionalTriggerSystem
    from core.life.cyber_identity import CyberIdentity
    from core.life.self_generation import SelfGeneration
    from core.life.autonomous_life_cycle import AutonomousLifeCycle
    from core.engine.art_learning_system import ArtLearningSystem
    from core.engine.live2d_avatar_generator import Live2DAvatarGenerator
    from core.engine.art_learning_workflow import ArtLearningWorkflow

    systems = {
        "physiological_tactile": PhysiologicalTactileSystem(),
        "endocrine_system": EndocrineSystem(),
        "autonomic_nervous_system": AutonomicNervousSystem(),
        "neuroplasticity": NeuroplasticitySystem(),
        "emotional_blending": EmotionalBlendingSystem(),
        "action_executor": ActionExecutor(),
        "desktop_interaction": DesktopInteraction(),
        "browser_controller": BrowserController(),
        "audio_system": AudioSystem(),
        "desktop_presence": DesktopPresence(),
        "live2d_integration": Live2DIntegration(),
        "biological_integrator": BiologicalIntegrator(),
        "digital_life_integrator": DigitalLifeIntegrator(),
        "memory_neuroplasticity_bridge": MemoryNeuroplasticityBridge(),
        "extended_behavior_library": ExtendedBehaviorLibrary(),
        "multidimensional_trigger": MultidimensionalTriggerSystem(),
        "cyber_identity": CyberIdentity(),
        "self_generation": SelfGeneration(),
        "autonomous_life_cycle": AutonomousLifeCycle(),
    }

    browser = systems.get("browser_controller")
    neuroplasticity = systems.get("neuroplasticity")
    live2d = systems.get("live2d_integration")
    tactile = systems.get("physiological_tactile")
    identity = systems.get("cyber_identity")

    if browser:
        systems["art_learning"] = ArtLearningSystem(
            browser_controller=browser, vision_service=None, neuroplasticity=neuroplasticity
        )
        systems["live2d_generator"] = Live2DAvatarGenerator(
            image_generator=None, art_learning_system=systems["art_learning"],
        )
        systems["art_learning_workflow"] = ArtLearningWorkflow(
            art_learning_system=systems["art_learning"],
            avatar_generator=systems["live2d_generator"],
            live2d_integration=live2d,
            physiological_tactile=tactile,
            cyber_identity=identity,
        )

    for name, system in systems.items():
        if hasattr(system, "initialize"):
            await system.initialize()

    # C2: register Live2D singleton for WebSocket state broadcast
    live2d_reg = systems.get("live2d_integration")
    if live2d_reg:
        try:
            from core.interfaces.service_registry import get_registry
            get_registry().register("live2d_integration", live2d_reg)
        except Exception:
            pass

    return systems
