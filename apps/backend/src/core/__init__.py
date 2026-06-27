"""
Angela AI v7.5.0-dev - Core Module
核心模块

Contains core systems including action execution, orchestration,
theoretical formulas for digital life, and system management components.

Author: Angela AI Development Team
Version: 7.5.0-dev
Date: 2026-05-25

NOTE: All submodule imports are lazy (via __getattr__) to avoid slow
startup. Import directly from submodules: from core.X import Y
"""

import importlib
import logging

logger = logging.getLogger(__name__)

__author__ = "Angela AI Development Team"

# Lazy import mapping: name -> module path
_LAZY_IMPORTS = {
    # Action Execution Layer
    "ActionExecutionBridge": "core.action_execution_bridge",
    "ActionExecutionBridgeFactory": "core.action_execution_bridge",
    "ActionType": "core.action_execution_bridge",
    "ExecutionResult": "core.action_execution_bridge",
    "ExecutionResultStatus": "core.action_execution_bridge",
    "ExecutionContext": "core.action_execution_bridge",
    "FeedbackCollector": "core.action_execution_bridge",
    # Action Executor
    "ActionExecutor": "core.engine.action_executor",
    "ActionQueue": "core.engine.action_executor",
    "ActionPriority": "core.engine.action_executor",
    "Action": "core.engine.action_executor",
    "ActionResult": "core.engine.action_executor",
    "ActionStatus": "core.engine.action_executor",
    "ActionCategory": "core.engine.action_executor",
    "SafetyCheck": "core.engine.action_executor",
    # Formula Systems
    "HSMFormulaSystem": "core.hsm_formula_system",
    "CognitiveGap": "core.hsm_formula_system",
    "ExplorationEvent": "core.hsm_formula_system",
    "GovernanceBlueprint": "core.hsm_formula_system",
    "ExplorationResult": "core.hsm_formula_system",
    "CDMCognitiveDividendModel": "core.cdm_dividend_model",
    "CognitiveInvestment": "core.cdm_dividend_model",
    "LifeSenseOutput": "core.cdm_dividend_model",
    "CognitiveActivity": "core.cdm_dividend_model",
    "DividendDistribution": "core.cdm_dividend_model",
    "LifeIntensityFormula": "core.life_intensity_formula",
    "KnowledgeState": "core.life_intensity_formula",
    "ConstraintState": "core.life_intensity_formula",
    "ObserverPresence": "core.life_intensity_formula",
    "KnowledgeDomain": "core.life_intensity_formula",
    "LifeIntensitySnapshot": "core.life_intensity_formula",
    "ActiveCognitionFormula": "core.active_cognition_formula",
    "StressVector": "core.active_cognition_formula",
    "OrderBaseline": "core.active_cognition_formula",
    "ActiveConstruction": "core.active_cognition_formula",
    "StressSource": "core.active_cognition_formula",
    "OrderType": "core.active_cognition_formula",
    "NonParadoxExistence": "core.non_paradox_existence",
    "GrayZoneVariable": "core.non_paradox_existence",
    "PossibilityState": "core.non_paradox_existence",
    "CoexistenceField": "core.non_paradox_existence",
    "GrayZoneVariableType": "core.non_paradox_existence",
    # Precision System
    "PrecisionManager": "core.precision.precision_manager",
    "DecimalMemoryBank": "core.precision.precision_manager",
    "HierarchicalPrecisionRouter": "core.precision.precision_manager",
    "PrecisionMemorySystem": "core.precision.precision_manager",
    "PrecisionMode": "core.precision.precision_manager",
    "create_precision_system": "core.precision.precision_manager",
    # Maturity System
    "MaturityLevel": "core.maturity.maturity_system",
    "MaturityManager": "core.maturity.maturity_system",
    "ExperienceTracker": "core.maturity.maturity_system",
    "create_maturity_system": "core.maturity.maturity_system",
    # Creative Systems
    "generate_and_save_to_desktop": "core.art.desktop_demo",
    "AngelaRealVoice": "core.art.real_edge_tts",
    "AngelaRealBrowser": "core.art.real_playwright_browser",
    # Metamorphosis
    "SoulCore": "core.metamorphosis.soul_core",
    "SoulSignature": "core.metamorphosis.soul_core",
    "IdentityCore": "core.metamorphosis.soul_core",
    "MemoryEssence": "core.metamorphosis.soul_core",
    "SoulCoreManager": "core.metamorphosis.soul_core",
    "SoulComponent": "core.metamorphosis.soul_core",
    "create_soul_core": "core.metamorphosis.soul_core",
    "BodyAdapter": "core.metamorphosis.body_adapter",
    "StateSnapshot": "core.metamorphosis.body_adapter",
    "TransferRecord": "core.metamorphosis.body_adapter",
    "AdaptationRule": "core.metamorphosis.body_adapter",
    "TransferStatus": "core.metamorphosis.body_adapter",
    "CompatibilityLevel": "core.metamorphosis.body_adapter",
    "BodyAdapterFactory": "core.metamorphosis.body_adapter",
    "create_body_adapter": "core.metamorphosis.body_adapter",
    "TransitionAnimator": "core.metamorphosis.transition_anim",
    "TransitionManager": "core.metamorphosis.transition_anim",
    "TransitionConfig": "core.metamorphosis.transition_anim",
    "TransitionProgress": "core.metamorphosis.transition_anim",
    "TransitionFrame": "core.metamorphosis.transition_anim",
    "TransitionPhase": "core.metamorphosis.transition_anim",
    "TransitionType": "core.metamorphosis.transition_anim",
    "create_transition_manager": "core.metamorphosis.transition_anim",
    # i18n
    "I18nManager": "core.i18n.i18n_manager",
    "I18nConfig": "core.i18n.i18n_manager",
    "I18nContext": "core.i18n.i18n_manager",
    "TranslationEntry": "core.i18n.i18n_manager",
    "TranslationCache": "core.i18n.i18n_manager",
    "Language": "core.i18n.i18n_manager",
    "Locale": "core.i18n.i18n_manager",
    "t": "core.i18n.i18n_manager",
    "set_language": "core.i18n.i18n_manager",
    "get_language": "core.i18n.i18n_manager",
    "add_translation": "core.i18n.i18n_manager",
    # Cloud Sync
    "CloudSyncManager": "core.sync.cloud_sync",
    "CloudSyncConfig": "core.sync.cloud_sync",
    "SyncItem": "core.sync.cloud_sync",
    "SyncConflict": "core.sync.cloud_sync",
    "SyncProgress": "core.sync.cloud_sync",
    "SyncStatus": "core.sync.cloud_sync",
    "ConflictResolution": "core.sync.cloud_sync",
    "SyncQueue": "core.sync.cloud_sync",
    # Hardware
    "ArchitectureType": "core.hardware.hal",
    "InstructionSet": "core.hardware.hal",
    "HardwareVendor": "core.hardware.hal",
    "ComputeUnit": "core.hardware.hal",
    "PrecisionLevel": "core.hardware.hal",
    "OperatingSystem": "core.hardware.hal",
    "HardwareCapabilities": "core.hardware.hal",
    "HardwareMetrics": "core.hardware.hal",
    "HardwareDetector": "core.hardware.hal",
    "HardwareManager": "core.hardware.hal",
    "HardwareFactory": "core.hardware.hal",
    "detect_hardware": "core.hardware.hal",
    "PrecisionConfig": "core.hardware.precision_matrix",
    "PrecisionMatrix": "core.hardware.precision_matrix",
    "ConversionInfo": "core.hardware.precision_matrix",
    "convert_precision": "core.hardware.precision_matrix",
    "optimize_for_hardware": "core.hardware.precision_matrix",
    "OptimizationStrategy": "core.hardware.compute_matrix",
    "MemoryLayout": "core.hardware.compute_matrix",
    "KernelConfig": "core.hardware.compute_matrix",
    "OptimizationResult": "core.hardware.compute_matrix",
    "ComputationMatrix": "core.hardware.compute_matrix",
    "ComputeOptimizer": "core.hardware.compute_matrix",
    "get_optimization": "core.hardware.compute_matrix",
    # Version
    "get_version": "core.version",
    "get_version_info": "core.version",
    "__version__": "core.version",
}

_lazy_cache = {}


def __getattr__(name):
    """Lazy import: on first access, import the actual module and cache the result."""
    if name in _LAZY_IMPORTS:
        module_path = _LAZY_IMPORTS[name]
        if name not in _lazy_cache:
            module = importlib.import_module(module_path)
            _lazy_cache[name] = getattr(module, name)
        return _lazy_cache[name]
    raise AttributeError(f"module 'core' has no attribute '{name}'")


def __dir__():
    return sorted(set(__all__) | set(_LAZY_IMPORTS.keys()) | {"logger"})


__all__ = [
    # Version
    "__version__",
    "__author__",
    "get_version",
    "get_version_info",
    # Action Execution Bridge
    "ActionExecutionBridge",
    "ActionExecutionBridgeFactory",
    "ActionType",
    "ExecutionResult",
    "ExecutionResultStatus",
    "ExecutionContext",
    "FeedbackCollector",
    # Action Executor
    "ActionExecutor",
    "ActionQueue",
    "ActionPriority",
    "Action",
    "ActionResult",
    "ActionStatus",
    "ActionCategory",
    "SafetyCheck",
    # Theoretical Formula Systems
    # HSM Formula
    "HSMFormulaSystem",
    "CognitiveGap",
    "ExplorationEvent",
    "GovernanceBlueprint",
    "ExplorationResult",
    # CDM Model
    "CDMCognitiveDividendModel",
    "CognitiveInvestment",
    "LifeSenseOutput",
    "CognitiveActivity",
    "DividendDistribution",
    # Life Intensity Formula
    "LifeIntensityFormula",
    "KnowledgeState",
    "ConstraintState",
    "ObserverPresence",
    "KnowledgeDomain",
    "LifeIntensitySnapshot",
    # Active Cognition Formula
    "ActiveCognitionFormula",
    "StressVector",
    "OrderBaseline",
    "ActiveConstruction",
    "StressSource",
    "OrderType",
    # Non-Paradox Existence
    "NonParadoxExistence",
    "GrayZoneVariable",
    "PossibilityState",
    "CoexistenceField",
    "GrayZoneVariableType",
    # Precision System
    "PrecisionManager",
    "DecimalMemoryBank",
    "HierarchicalPrecisionRouter",
    "PrecisionMemorySystem",
    "PrecisionMode",
    "create_precision_system",
    # Maturity System
    "MaturityLevel",
    "MaturityManager",
    "ExperienceTracker",
    "create_maturity_system",
    # Creative Systems
    "generate_and_save_to_desktop",
    "AngelaRealVoice",
    "AngelaRealBrowser",
    # Metamorphosis Systems
    # Soul Core
    "SoulCore",
    "SoulSignature",
    "IdentityCore",
    "MemoryEssence",
    "SoulCoreManager",
    "SoulComponent",
    "create_soul_core",
    # Body Adapter
    "BodyAdapter",
    "StateSnapshot",
    "TransferRecord",
    "AdaptationRule",
    "TransferStatus",
    "CompatibilityLevel",
    "BodyAdapterFactory",
    "create_body_adapter",
    # Transition Animation
    "TransitionAnimator",
    "TransitionManager",
    "TransitionConfig",
    "TransitionProgress",
    "TransitionFrame",
    "TransitionPhase",
    "TransitionType",
    "create_transition_manager",
    # Internationalization (i18n)
    "I18nManager",
    "I18nConfig",
    "I18nContext",
    "TranslationEntry",
    "TranslationCache",
    "Language",
    "Locale",
    "t",
    "set_language",
    "get_language",
    "add_translation",
    # Cloud Sync
    "CloudSyncManager",
    "CloudSyncConfig",
    "SyncItem",
    "SyncConflict",
    "SyncProgress",
    "SyncStatus",
    "ConflictResolution",
    "SyncQueue",
    # Hardware Support
    # Architecture & Hardware
    "ArchitectureType",
    "InstructionSet",
    "HardwareVendor",
    "ComputeUnit",
    "PrecisionLevel",
    "OperatingSystem",
    "HardwareCapabilities",
    "HardwareMetrics",
    "HardwareDetector",
    "HardwareManager",
    "HardwareFactory",
    "detect_hardware",
    # Precision Management
    "PrecisionConfig",
    "PrecisionMatrix",
    "ConversionInfo",
    "convert_precision",
    "optimize_for_hardware",
    # Computation Optimization
    "OptimizationStrategy",
    "MemoryLayout",
    "KernelConfig",
    "OptimizationResult",
    "ComputationMatrix",
    "ComputeOptimizer",
    "get_optimization",
]
