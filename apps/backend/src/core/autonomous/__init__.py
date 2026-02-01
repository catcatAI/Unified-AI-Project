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

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Biological Simulation Systems
    from .physiological_tactile import (
        PhysiologicalTactileSystem, Receptor, BodyPart,
        TrajectoryAnalyzer, TrajectoryPoint, TrajectoryAnalysis,
        AdaptationMechanism, ReceptorAdaptationState
    )
    from .endocrine_system import (
        EndocrineSystem, Hormone, HormoneType,
        HormoneKinetics, ReceptorStatus,
        FeedbackLoop, FeedbackNode
    )
    from .autonomic_nervous_system import AutonomicNervousSystem, ANSState, NerveType
    from .neuroplasticity import (
        NeuroplasticitySystem, MemoryTrace, HebbianRule,
        SkillAcquisition, SkillTrace,
        HabitFormation, HabitTrace,
        TraumaMemorySystem, TraumaMemory,
        ExplicitImplicitLearning, LearningEvent
    )
    from .emotional_blending import (
        EmotionalBlendingSystem, PADEmotion, EmotionalExpression,
        MultidimensionalStateMatrix, StateDimension
    )
    from .state_matrix import StateMatrix4D, DimensionState
    
    # Execution Systems
    from .action_executor import ActionExecutor, ActionQueue, ActionPriority
    from .desktop_interaction import DesktopInteraction, FileOperation, DesktopState
    from .browser_controller import BrowserController, SearchResult, BrowserState
    from .audio_system import AudioSystem, TTSConfig, MusicPlayer, LyricsSync
    from .desktop_presence import DesktopPresence, MouseTracker, CollisionDetector
    from .live2d_integration import Live2DIntegration, Live2DExpression, Live2DAction
    
    # Integration Systems
    from .biological_integrator import BiologicalIntegrator, SystemInteraction
    from .digital_life_integrator import DigitalLifeIntegrator, LifeCycleState
    from .memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge, MemoryConsolidation
    from .extended_behavior_library import ExtendedBehaviorLibrary, BehaviorDefinition
    from .multidimensional_trigger import MultidimensionalTrigger, TriggerDimension
    from .cyber_identity import CyberIdentity, SelfModel, IdentityGrowth
    from .self_generation import SelfGeneration, Live2DGenerator, AvatarBuilder

__version__ = "6.0.0"
__author__ = "Angela AI Development Team"

# Package-level exports
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Biological Systems
    "PhysiologicalTactileSystem",
    "SkinReceptor",
    "BodyPart",
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
    
    # Physiological Tactile Extensions
    "TrajectoryAnalyzer",
    "TrajectoryPoint",
    "TrajectoryAnalysis",
    "AdaptationMechanism",
    "ReceptorAdaptationState",
    
    # Endocrine System Extensions
    "HormoneKinetics",
    "ReceptorStatus",
    "FeedbackLoop",
    "FeedbackNode",
    
    # State Matrix System
    "StateMatrix4D",
    "DimensionState",
    
    # Execution Systems
    "ActionExecutor",
    "ActionQueue",
    "ActionPriority",
    "DesktopInteraction",
    "FileOperation",
    "DesktopState",
    "BrowserController",
    "SearchResult",
    "BrowserState",
    "AudioSystem",
    "TTSConfig",
    "MusicPlayer",
    "LyricsSync",
    "DesktopPresence",
    "MouseTracker",
    "CollisionDetector",
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
    "MultidimensionalTrigger",
    "TriggerDimension",
    "CyberIdentity",
    "SelfModel",
    "IdentityGrowth",
    "SelfGeneration",
    "Live2DGenerator",
    "AvatarBuilder",
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
                "self_generation"
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
            "self_generation"
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
    from .multidimensional_trigger import MultidimensionalTrigger
    from .cyber_identity import CyberIdentity
    from .self_generation import SelfGeneration
    
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
        'multidimensional_trigger': MultidimensionalTrigger(),
        'cyber_identity': CyberIdentity(),
        'self_generation': SelfGeneration(),
    }
    
    # Initialize each system
    for name, system in systems.items():
        if hasattr(system, 'initialize'):
            await system.initialize()
    
    return systems
