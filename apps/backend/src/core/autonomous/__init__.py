"""
Angela AI v6.0 - Autonomous System Package
自主系统包初始化

This package contains all autonomous systems for Angela AI including:
- Biological Simulation Systems (生理模拟系统)
- Execution Systems (执行系统)
- Integration Systems (整合系统)

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

# Biological Simulation Systems
try:
    from .physiological_tactile import (
        PhysiologicalTactileSystem, Receptor, BodyPart,
        TrajectoryAnalyzer, TrajectoryPoint, TrajectoryAnalysis,
        AdaptationMechanism, ReceptorAdaptationState
    )
except ImportError:
    PhysiologicalTactileSystem = None
    Receptor = None
    BodyPart = None
    TrajectoryAnalyzer = None
    TrajectoryPoint = None
    TrajectoryAnalysis = None
    AdaptationMechanism = None
    ReceptorAdaptationState = None

try:
    from .endocrine_system import (
        EndocrineSystem, Hormone, HormoneType,
        HormoneKinetics, ReceptorStatus,
        FeedbackLoop, FeedbackNode
    )
except ImportError:
    EndocrineSystem = None
    Hormone = None
    HormoneType = None
    HormoneKinetics = None
    ReceptorStatus = None
    FeedbackLoop = None
    FeedbackNode = None

try:
    from .autonomic_nervous_system import AutonomicNervousSystem, ANSState, NerveType
except ImportError:
    AutonomicNervousSystem = None
    ANSState = None
    NerveType = None

try:
    from .neuroplasticity import (
        NeuroplasticitySystem, MemoryTrace, HebbianRule,
        SkillAcquisition, SkillTrace,
        HabitFormation, HabitTrace,
        TraumaMemorySystem, TraumaMemory,
        ExplicitImplicitLearning, LearningEvent
    )
except ImportError:
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
    from .emotional_blending import (
        EmotionalBlendingSystem, PADEmotion, EmotionalExpression,
        MultidimensionalStateMatrix, StateDimension
    )
except ImportError:
    EmotionalBlendingSystem = None
    PADEmotion = None
    EmotionalExpression = None
    MultidimensionalStateMatrix = None
    StateDimension = None

try:
    from .state_matrix import StateMatrix4D, DimensionState
except ImportError:
    StateMatrix4D = None
    DimensionState = None

# Execution Systems
try:
    from .action_executor import (
        ActionExecutor, ActionQueue, ActionPriority,
        Action, ActionResult, ActionStatus, ActionCategory
    )
except ImportError:
    ActionExecutor = None
    ActionQueue = None
    ActionPriority = None
    Action = None
    ActionResult = None
    ActionStatus = None
    ActionCategory = None

try:
    from .desktop_interaction import DesktopInteraction, FileOperation, DesktopState
except ImportError:
    DesktopInteraction = None
    FileOperation = None
    DesktopState = None

try:
    from .browser_controller import BrowserController, SearchResult, BrowserState
except ImportError:
    BrowserController = None
    SearchResult = None
    BrowserState = None

try:
    from .audio_system import AudioSystem, TTSConfig, LyricsSync
except ImportError:
    AudioSystem = None
    TTSConfig = None
    LyricsSync = None

try:
    from .desktop_presence import DesktopPresence, MouseTracker
except ImportError:
    DesktopPresence = None
    MouseTracker = None

try:
    from .live2d_integration import Live2DIntegration, Live2DExpression, Live2DAction
except ImportError:
    Live2DIntegration = None
    Live2DExpression = None
    Live2DAction = None

# Integration Systems
try:
    from .biological_integrator import BiologicalIntegrator, SystemInteraction
except ImportError:
    BiologicalIntegrator = None
    SystemInteraction = None

try:
    from .digital_life_integrator import DigitalLifeIntegrator, LifeCycleState
except ImportError:
    DigitalLifeIntegrator = None
    LifeCycleState = None

try:
    from .memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge, MemoryConsolidation
except ImportError:
    MemoryNeuroplasticityBridge = None
    MemoryConsolidation = None

try:
    from .extended_behavior_library import ExtendedBehaviorLibrary, BehaviorDefinition
except ImportError:
    ExtendedBehaviorLibrary = None
    BehaviorDefinition = None

try:
    from .multidimensional_trigger import MultidimensionalTriggerSystem, TriggerDimension
except ImportError:
    MultidimensionalTriggerSystem = None
    TriggerDimension = None

try:
    from .cyber_identity import CyberIdentity, SelfModel, IdentityGrowth
except ImportError:
    CyberIdentity = None
    SelfModel = None
    IdentityGrowth = None

try:
    from .self_generation import SelfGeneration, AvatarBuilder
except ImportError:
    SelfGeneration = None
    AvatarBuilder = None

# Art Learning and Live2D Generation Systems
try:
    from .art_learning_system import (
        ArtLearningSystem, ArtKnowledge, ArtDomain,
        TutorialContent, ImageAnalysis, LearningSession,
        BodyPartMapping, Live2DParameter, LearningType
    )
except ImportError:
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
    from .live2d_avatar_generator import (
        Live2DAvatarGenerator, GeneratedAvatar, Live2DModelConfig,
        GenerationStage, ViewAngle, BodyLayer
    )
except ImportError:
    Live2DAvatarGenerator = None
    GeneratedAvatar = None
    Live2DModelConfig = None
    GenerationStage = None
    ViewAngle = None
    BodyLayer = None

try:
    from .art_learning_workflow import (
        ArtLearningWorkflow, WorkflowStage, LearningObjective,
        WorkflowProgress, SkillAssessment, GenerationResult,
        WorkflowConfig
    )
except ImportError:
    ArtLearningWorkflow = None
    WorkflowStage = None
    LearningObjective = None
    WorkflowProgress = None
    SkillAssessment = None
    GenerationResult = None
    WorkflowConfig = None

try:
    from .autonomous_life_cycle import AutonomousLifeCycle, LifePhase, LifeDecision, FormulaMetrics
except ImportError:
    AutonomousLifeCycle = None
    LifePhase = None
    LifeDecision = None
    FormulaMetrics = None

__version__ = "6.0.0"
__author__ = "Angela AI Development Team"

# Package-level exports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Biological Systems
    "PhysiologicalTactileSystem",
    "EndocrineSystem",
    "Hormone",
    "HormoneType",
    "AutonomicNervousSystem",
    "ANSState",
    "NerveType",
    "NeuroplasticitySystem",
    "MemoryTrace",
    "HebbianRule",
    "SkillAcquisition",
    "SkillTrace",
    "HabitFormation",
    "HabitTrace",
    "TraumaMemorySystem",
    "TraumaMemory",
    "ExplicitImplicitLearning",
    "LearningEvent",
    "EmotionalBlendingSystem",
    "PADEmotion",
    "EmotionalExpression",
    "MultidimensionalStateMatrix",
    "StateDimension",
    "StateMatrix4D",
    "DimensionState",
    
    # Execution Systems
    "ActionExecutor",
    "ActionQueue",
    "ActionPriority",
    "Action",
    "ActionResult",
    "ActionStatus",
    "ActionCategory",
    "DesktopInteraction",
    "FileOperation",
    "DesktopState",
    "BrowserController",
    "SearchResult",
    "BrowserState",
    "AudioSystem",
    "TTSConfig",
    "LyricsSync",
    "DesktopPresence",
    "MouseTracker",
    "Live2DIntegration",
    "Live2DExpression",
    "Live2DAction",
    
    # Integration Systems
    "BiologicalIntegrator",
    "SystemInteraction",
    "DigitalLifeIntegrator",
    "LifeCycleState",
    "MemoryNeuroplasticityBridge",
    "MemoryConsolidation",
    "ExtendedBehaviorLibrary",
    "BehaviorDefinition",
    "MultidimensionalTriggerSystem",
    "TriggerDimension",
    "CyberIdentity",
    "SelfModel",
    "IdentityGrowth",
    "SelfGeneration",
    "AvatarBuilder",
    
    # Autonomous Life Cycle (Theoretical Frameworks)
    "AutonomousLifeCycle",
    "LifePhase",
    "LifeDecision",
    "FormulaMetrics",
    
    # Art Learning and Live2D Generation
    "ArtLearningSystem",
    "ArtKnowledge",
    "ArtDomain",
    "TutorialContent",
    "ImageAnalysis",
    "LearningSession",
    "BodyPartMapping",
    "Live2DParameter",
    "LearningType",
    "Live2DAvatarGenerator",
    "GeneratedAvatar",
    "Live2DModelConfig",
    "GenerationStage",
    "ViewAngle",
    "BodyLayer",
    "ArtLearningWorkflow",
    "WorkflowStage",
    "LearningObjective",
    "WorkflowProgress",
    "SkillAssessment",
    "GenerationResult",
    "WorkflowConfig",
]


def get_system_info() -> dict:
    """
    Get comprehensive information about the autonomous system package.
    
    Returns:
        dict: Package information including version, modules, and capabilities
    
    Example:
        >>> info = get_system_info()
        >>> print(info['version'])
        '6.0.0'
    """
    return {
        "version": __version__,
        "author": __author__,
        "modules": {
            "biological": [
                "physiological_tactile",
                "endocrine_system",
                "autonomic_nervous_system",
                "neuroplasticity",
                "emotional_blending",
                "state_matrix"
            ],
            "execution": [
                "action_executor",
                "desktop_interaction",
                "browser_controller",
                "audio_system",
                "desktop_presence",
                "live2d_integration"
            ],
            "integration": [
                "biological_integrator",
                "digital_life_integrator",
                "memory_neuroplasticity_bridge",
                "extended_behavior_library",
                "multidimensional_trigger",
                "cyber_identity",
                "self_generation",
                "autonomous_life_cycle"
            ],
            "art_learning": [
                "art_learning_system",
                "live2d_avatar_generator",
                "art_learning_workflow"
            ]
        },
        "capabilities": [
            "biological_simulation",
            "hormonal_regulation",
            "neural_plasticity",
            "emotional_blending",
            "trajectory_analysis",
            "receptor_adaptation",
            "hormone_kinetics",
            "feedback_regulation",
            "skill_acquisition",
            "habit_formation",
            "trauma_memory",
            "explicit_implicit_learning",
            "multidimensional_state_matrix",
            "action_execution",
            "desktop_interaction",
            "browser_control",
            "audio_synthesis",
            "live2d_animation",
            "memory_consolidation",
            "behavior_generation",
            "identity_formation",
            "self_generation",
            "autonomous_life_cycle",
            "theoretical_frameworks",
            "hsm_formula",
            "cdm_model",
            "life_intensity",
            "active_cognition",
            "non_paradox_existence",
            "art_learning",
            "live2d_generation",
            "anime_style_learning",
            "tutorial_search",
            "image_analysis",
            "body_part_rigging",
            "physiological_live2d_bridge",
            "skill_acquisition_power_law",
            "implicit_style_learning"
        ]
    }


async def initialize_all_systems() -> dict:
    """
    Initialize all autonomous systems for Angela AI.
    
    This is a convenience function to initialize all systems at once.
    In production, systems should be initialized selectively based on requirements.
    
    Returns:
        dict: Dictionary containing all initialized system instances
        
    Example:
        >>> systems = await initialize_all_systems()
        >>> tactile_system = systems['physiological_tactile']
    """
    # Import here to avoid circular imports
    from .physiological_tactile import PhysiologicalTactileSystem
    from .endocrine_system import EndocrineSystem
    from .autonomic_nervous_system import AutonomicNervousSystem
    from .neuroplasticity import NeuroplasticitySystem
    from .emotional_blending import EmotionalBlendingSystem
    from .action_executor import ActionExecutor
    from .desktop_interaction import DesktopInteraction
    from .browser_controller import BrowserController
    from .audio_system import AudioSystem
    from .desktop_presence import DesktopPresence
    from .live2d_integration import Live2DIntegration
    from .biological_integrator import BiologicalIntegrator
    from .digital_life_integrator import DigitalLifeIntegrator
    from .memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge
    from .extended_behavior_library import ExtendedBehaviorLibrary
    from .multidimensional_trigger import MultidimensionalTriggerSystem
    from .cyber_identity import CyberIdentity
    from .self_generation import SelfGeneration
    from .autonomous_life_cycle import AutonomousLifeCycle
    
    # Art Learning Systems
    from .art_learning_system import ArtLearningSystem
    from .live2d_avatar_generator import Live2DAvatarGenerator
    from .art_learning_workflow import ArtLearningWorkflow
    
    # Initialize all systems
    systems = {
        'physiological_tactile': PhysiologicalTactileSystem(),
        'endocrine_system': EndocrineSystem(),
        'autonomic_nervous_system': AutonomicNervousSystem(),
        'neuroplasticity': NeuroplasticitySystem(),
        'emotional_blending': EmotionalBlendingSystem(),
        'action_executor': ActionExecutor(),
        'desktop_interaction': DesktopInteraction(),
        'browser_controller': BrowserController(),
        'audio_system': AudioSystem(),
        'desktop_presence': DesktopPresence(),
        'live2d_integration': Live2DIntegration(),
        'biological_integrator': BiologicalIntegrator(),
        'digital_life_integrator': DigitalLifeIntegrator(),
        'memory_neuroplasticity_bridge': MemoryNeuroplasticityBridge(),
        'extended_behavior_library': ExtendedBehaviorLibrary(),
        'multidimensional_trigger': MultidimensionalTriggerSystem(),
        'cyber_identity': CyberIdentity(),
        'self_generation': SelfGeneration(),
        'autonomous_life_cycle': AutonomousLifeCycle(),
    }
    
    # Art Learning Systems (initialized with dependencies)
    browser = systems.get('browser_controller')
    vision = None  # Would be provided externally
    neuroplasticity = systems.get('neuroplasticity')
    live2d = systems.get('live2d_integration')
    tactile = systems.get('physiological_tactile')
    identity = systems.get('cyber_identity')
    
    if browser:
        systems['art_learning'] = ArtLearningSystem(
            browser_controller=browser,
            vision_service=vision,
            neuroplasticity=neuroplasticity
        )
        
        # Create Live2D avatar generator (requires image generator, would be provided externally)
        systems['live2d_generator'] = Live2DAvatarGenerator(
            image_generator=None,  # Would be set externally
            art_learning_system=systems['art_learning']
        )
        
        # Create learning workflow
        systems['art_learning_workflow'] = ArtLearningWorkflow(
            art_learning_system=systems['art_learning'],
            avatar_generator=systems['live2d_generator'],
            live2d_integration=live2d,
            physiological_tactile=tactile,
            cyber_identity=identity
        )
    
    # Initialize each system
    for name, system in systems.items():
        if hasattr(system, 'initialize'):
            await system.initialize()
    
    return systems
