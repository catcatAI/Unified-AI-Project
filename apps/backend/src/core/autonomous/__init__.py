"""
Angela AI v7.5.0-dev - Autonomous System Package (Backward Compat Shim)
=======================================================================
A3 refactor: all modules moved to core/{life,bio,engine}/ subpackages.
This file re-exports everything from the new locations for backward compatibility.

All submodule imports are lazy (via __getattr__) to avoid circular imports
and slow module loading (e.g., torch/ctranslate2).
"""

import importlib
import logging
from typing import Any, List

logger = logging.getLogger(__name__)

__version__ = "7.5.0-dev"
__author__ = "Angela AI Development Team"

# Lazy import mapping: name -> (module_path, attr_name)
# When module_path == attr_name, the module itself is returned.
_LAZY_IMPORTS: dict = {
    # Biological Simulation Systems → core/bio/
    "PhysiologicalTactileSystem": ("core.bio.physiological_tactile", "PhysiologicalTactileSystem"),
    "Receptor": ("core.bio.physiological_tactile", "Receptor"),
    "BodyPart": ("core.bio.physiological_tactile", "BodyPart"),
    "TrajectoryAnalyzer": ("core.bio.physiological_tactile", "TrajectoryAnalyzer"),
    "TrajectoryPoint": ("core.bio.physiological_tactile", "TrajectoryPoint"),
    "TrajectoryAnalysis": ("core.bio.physiological_tactile", "TrajectoryAnalysis"),
    "AdaptationMechanism": ("core.bio.physiological_tactile", "AdaptationMechanism"),
    "ReceptorAdaptationState": ("core.bio.physiological_tactile", "ReceptorAdaptationState"),
    # Endocrine System
    "EndocrineSystem": ("core.bio.endocrine_system", "EndocrineSystem"),
    "FeedbackLoop": ("core.bio.endocrine_system", "FeedbackLoop"),
    "FeedbackNode": ("core.bio.endocrine_system", "FeedbackNode"),
    "Hormone": ("core.bio.endocrine_system", "Hormone"),
    "HormoneKinetics": ("core.bio.endocrine_system", "HormoneKinetics"),
    "HormoneType": ("core.bio.endocrine_system", "HormoneType"),
    "ReceptorStatus": ("core.bio.endocrine_system", "ReceptorStatus"),
    # Autonomic Nervous System
    "AutonomicNervousSystem": ("core.bio.autonomic_nervous_system", "AutonomicNervousSystem"),
    "ANSState": ("core.bio.autonomic_nervous_system", "ANSState"),
    "NerveType": ("core.bio.autonomic_nervous_system", "NerveType"),
    # Neuroplasticity
    "NeuroplasticitySystem": ("core.bio.neuroplasticity", "NeuroplasticitySystem"),
    "MemoryTrace": ("core.bio.neuroplasticity", "MemoryTrace"),
    "HebbianRule": ("core.bio.neuroplasticity", "HebbianRule"),
    "SkillAcquisition": ("core.bio.neuroplasticity", "SkillAcquisition"),
    "SkillTrace": ("core.bio.neuroplasticity", "SkillTrace"),
    "HabitFormation": ("core.bio.neuroplasticity", "HabitFormation"),
    "HabitTrace": ("core.bio.neuroplasticity", "HabitTrace"),
    "TraumaMemorySystem": ("core.bio.neuroplasticity", "TraumaMemorySystem"),
    "TraumaMemory": ("core.bio.neuroplasticity", "TraumaMemory"),
    "ExplicitImplicitLearning": ("core.bio.neuroplasticity", "ExplicitImplicitLearning"),
    "LearningEvent": ("core.bio.neuroplasticity", "LearningEvent"),
    # Emotional Blending
    "EmotionalBlendingSystem": ("core.bio.emotional_blending", "EmotionalBlendingSystem"),
    "EmotionalExpression": ("core.bio.emotional_blending", "EmotionalExpression"),
    "MultidimensionalStateMatrix": ("core.bio.emotional_blending", "MultidimensionalStateMatrix"),
    "PADEmotion": ("core.bio.emotional_blending", "PADEmotion"),
    "StateDimension": ("core.bio.emotional_blending", "StateDimension"),
    # Biological Integrator
    "BiologicalIntegrator": ("core.bio.biological_integrator", "BiologicalIntegrator"),
    "SystemInteraction": ("core.bio.biological_integrator", "SystemInteraction"),
    # Memory Neuroplasticity Bridge
    "MemoryNeuroplasticityBridge": (
        "core.bio.memory_neuroplasticity_bridge",
        "MemoryNeuroplasticityBridge",
    ),
    "MemoryConsolidation": ("core.bio.memory_neuroplasticity_bridge", "MemoryConsolidation"),
    # Extended Behavior Library
    "ExtendedBehaviorLibrary": ("core.bio.extended_behavior_library", "ExtendedBehaviorLibrary"),
    "BehaviorDefinition": ("core.bio.extended_behavior_library", "BehaviorDefinition"),
    # Multidimensional Trigger
    "MultidimensionalTriggerSystem": (
        "core.bio.multidimensional_trigger",
        "MultidimensionalTriggerSystem",
    ),
    "TriggerDimension": ("core.bio.multidimensional_trigger", "TriggerDimension"),
    # Execution Systems → core/engine/
    "StateMatrix4D": ("core.engine.state_matrix", "StateMatrix4D"),
    "DimensionState": ("core.engine.state_matrix", "DimensionState"),
    "ActionExecutor": ("core.engine.action_executor", "ActionExecutor"),
    "ActionQueue": ("core.engine.action_executor", "ActionQueue"),
    "ActionPriority": ("core.engine.action_executor", "ActionPriority"),
    "Action": ("core.engine.action_executor", "Action"),
    "ActionResult": ("core.engine.action_executor", "ActionResult"),
    "ActionStatus": ("core.engine.action_executor", "ActionStatus"),
    "ActionCategory": ("core.engine.action_executor", "ActionCategory"),
    "DesktopInteraction": ("core.engine.desktop_interaction", "DesktopInteraction"),
    "DesktopState": ("core.engine.desktop_interaction", "DesktopState"),
    "FileOperation": ("core.engine.desktop_interaction", "FileOperation"),
    "BrowserController": ("core.engine.browser_controller", "BrowserController"),
    "BrowserState": ("core.engine.browser_controller", "BrowserState"),
    "SearchResult": ("core.engine.browser_controller", "SearchResult"),
    "AudioSystem": ("core.engine.audio_system", "AudioSystem"),
    "TTSConfig": ("core.engine.audio_system", "TTSConfig"),
    "LyricsSync": ("core.engine.audio_system", "LyricsSync"),
    "Live2DIntegration": ("core.engine.live2d_integration", "Live2DIntegration"),
    # Art Learning Systems → core/engine/
    "ArtLearningSystem": ("core.engine.art_learning_system", "ArtLearningSystem"),
    "ArtKnowledge": ("core.engine.art_learning_system", "ArtKnowledge"),
    "ArtDomain": ("core.engine.art_learning_system", "ArtDomain"),
    "TutorialContent": ("core.engine.art_learning_system", "TutorialContent"),
    "ImageAnalysis": ("core.engine.art_learning_system", "ImageAnalysis"),
    "LearningSession": ("core.engine.art_learning_system", "LearningSession"),
    "BodyPartMapping": ("core.engine.art_learning_system", "BodyPartMapping"),
    "Live2DParameter": ("core.engine.art_learning_system", "Live2DParameter"),
    "LearningType": ("core.engine.art_learning_system", "LearningType"),
    "Live2DAvatarGenerator": ("core.engine.live2d_avatar_generator", "Live2DAvatarGenerator"),
    "GeneratedAvatar": ("core.engine.live2d_avatar_generator", "GeneratedAvatar"),
    "Live2DModelConfig": ("core.engine.live2d_avatar_generator", "Live2DModelConfig"),
    "GenerationStage": ("core.engine.live2d_avatar_generator", "GenerationStage"),
    "ViewAngle": ("core.engine.live2d_avatar_generator", "ViewAngle"),
    "BodyLayer": ("core.engine.live2d_avatar_generator", "BodyLayer"),
    "ArtLearningWorkflow": ("core.engine.art_learning_workflow", "ArtLearningWorkflow"),
    "WorkflowStage": ("core.engine.art_learning_workflow", "WorkflowStage"),
    "LearningObjective": ("core.engine.art_learning_workflow", "LearningObjective"),
    "WorkflowProgress": ("core.engine.art_learning_workflow", "WorkflowProgress"),
    "SkillAssessment": ("core.engine.art_learning_workflow", "SkillAssessment"),
    "GenerationResult": ("core.engine.art_learning_workflow", "GenerationResult"),
    "WorkflowConfig": ("core.engine.art_learning_workflow", "WorkflowConfig"),
    # Integration Systems → core/life/
    "DigitalLifeIntegrator": ("core.life.digital_life_integrator", "DigitalLifeIntegrator"),
    "LifeCycleState": ("core.life.digital_life_integrator", "LifeCycleState"),
    "CyberIdentity": ("core.life.cyber_identity", "CyberIdentity"),
    "SelfModel": ("core.life.cyber_identity", "SelfModel"),
    "IdentityGrowth": ("core.life.cyber_identity", "IdentityGrowth"),
    "SelfGeneration": ("core.life.self_generation", "SelfGeneration"),
    "AvatarBuilder": ("core.life.self_generation", "AvatarBuilder"),
    "AutonomousLifeCycle": ("core.life.autonomous_life_cycle", "AutonomousLifeCycle"),
    "LifePhase": ("core.life.autonomous_life_cycle", "LifePhase"),
    "LifeDecision": ("core.life.autonomous_life_cycle", "LifeDecision"),
    "FormulaMetrics": ("core.life.autonomous_life_cycle", "FormulaMetrics"),
}

# Aliases
_MOUSE_ALIASES = {
    "DesktopPresence": "DesktopInteraction",
    "MouseTracker": "DesktopInteraction",
}

_lazy_cache: dict = {}
_warned: set = set()


def _lazy_import(name: str) -> Any:
    """Import and cache a lazy import, return None on failure."""
    if name in _lazy_cache:
        return _lazy_cache[name]

    if name not in _LAZY_IMPORTS:
        # Check aliases
        if name in _MOUSE_ALIASES:
            target = _MOUSE_ALIASES[name]
            resolved = _lazy_import(target)
            _lazy_cache[name] = resolved
            return resolved
        return _MISSING_SENTINEL

    module_path, attr = _LAZY_IMPORTS[name]
    try:
        module = importlib.import_module(module_path)
        result = getattr(module, attr)
        _lazy_cache[name] = result
        return result
    except Exception:
        if name not in _warned:
            logger.warning("Failed to lazy-import %s from %s", name, module_path)
            _warned.add(name)
        _lazy_cache[name] = None
        return None


class _MissingSentinel:
    def __getattr__(self, attr):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def __bool__(self):
        return True

    def __repr__(self):
        return "<missing>"


_MISSING_SENTINEL = _MissingSentinel()


def __getattr__(name: str) -> Any:
    if name in (
        "__all__",
        "_lazy_cache",
        "_warned",
        "logger",
        "_LAZY_IMPORTS",
        "_MOUSE_ALIASES",
        "_MISSING_SENTINEL",
        "_MissingSentinel",
        "_lazy_import",
    ):
        raise AttributeError(name)
    if name in __all__:
        return _lazy_import(name)
    raise AttributeError(f"module 'core.autonomous' has no attribute {name!r}")


def __dir__() -> List[str]:
    return sorted(__all__)


__all__ = [
    "__version__",
    "__author__",
    "PhysiologicalTactileSystem",
    "Receptor",
    "BodyPart",
    "TrajectoryAnalyzer",
    "TrajectoryPoint",
    "TrajectoryAnalysis",
    "AdaptationMechanism",
    "ReceptorAdaptationState",
    "EndocrineSystem",
    "Hormone",
    "HormoneType",
    "HormoneKinetics",
    "ReceptorStatus",
    "FeedbackLoop",
    "FeedbackNode",
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
    "AutonomousLifeCycle",
    "LifePhase",
    "LifeDecision",
    "FormulaMetrics",
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
    """Get comprehensive information about the autonomous system package."""
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
                "biological_integrator",
            ],
            "execution": [
                "state_matrix",
                "action_executor",
                "desktop_interaction",
                "browser_controller",
                "audio_system",
                "desktop_presence",
                "live2d_integration",
            ],
            "integration": [
                "biological_integrator",
                "digital_life_integrator",
                "memory_neuroplasticity_bridge",
                "extended_behavior_library",
                "multidimensional_trigger",
                "cyber_identity",
                "self_generation",
                "autonomous_life_cycle",
            ],
            "art_learning": [
                "art_learning_system",
                "live2d_avatar_generator",
                "art_learning_workflow",
            ],
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
            "implicit_style_learning",
        ],
    }


async def initialize_all_systems() -> dict:
    """Initialize all autonomous systems for Angela AI."""
    from core.bio.autonomic_nervous_system import AutonomicNervousSystem
    from core.bio.biological_integrator import BiologicalIntegrator
    from core.bio.emotional_blending import EmotionalBlendingSystem
    from core.bio.endocrine_system import EndocrineSystem
    from core.bio.extended_behavior_library import ExtendedBehaviorLibrary
    from core.bio.memory_neuroplasticity_bridge import MemoryNeuroplasticityBridge
    from core.bio.multidimensional_trigger import MultidimensionalTriggerSystem
    from core.bio.neuroplasticity import NeuroplasticitySystem
    from core.bio.physiological_tactile import PhysiologicalTactileSystem
    from core.engine.action_executor import ActionExecutor
    from core.engine.art_learning_system import ArtLearningSystem
    from core.engine.art_learning_workflow import ArtLearningWorkflow
    from core.engine.audio_system import AudioSystem
    from core.engine.browser_controller import BrowserController
    from core.engine.desktop_interaction import DesktopInteraction
    from core.engine.desktop_interaction import DesktopInteraction as DesktopPresence
    from core.engine.live2d_avatar_generator import Live2DAvatarGenerator
    from core.engine.live2d_integration import Live2DIntegration
    from core.life.autonomous_life_cycle import AutonomousLifeCycle
    from core.life.cyber_identity import CyberIdentity
    from core.life.digital_life_integrator import DigitalLifeIntegrator
    from core.life.self_generation import SelfGeneration

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
            image_generator=None,
            art_learning_system=systems["art_learning"],
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
        except Exception as e:
            logger.warning(f"Failed to register live2d_integration service: {e}", exc_info=True)

    return systems
