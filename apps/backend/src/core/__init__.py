"""
Angela AI v7.5.0-dev - Core Module
核心模块

Contains core systems including action execution, orchestration,
theoretical formulas for digital life, and system management components.

Author: Angela AI Development Team
Version: 7.5.0-dev
Date: 2026-05-25
"""

import logging

logger = logging.getLogger(__name__)

# Action Execution Layer
from .action_execution_bridge import (  # noqa: E402
    ActionExecutionBridge,
    ActionExecutionBridgeFactory,
    ActionType,
    ExecutionResult,
    ExecutionResultStatus,
    ExecutionContext,
    FeedbackCollector,
)

# Autonomous Systems (refactored to core/engine/)
from .engine.action_executor import (  # noqa: E402
    ActionExecutor,
    ActionQueue,
    ActionPriority,
    Action,
    ActionResult,
    ActionStatus,
    ActionCategory,
    SafetyCheck,
)

# Theoretical Formula Systems - Digital Life Frameworks
from .hsm_formula_system import (  # noqa: E402
    HSMFormulaSystem,
    CognitiveGap,
    ExplorationEvent,
    GovernanceBlueprint,
    ExplorationResult,
)

from .cdm_dividend_model import (  # noqa: E402
    CDMCognitiveDividendModel,
    CognitiveInvestment,
    LifeSenseOutput,
    CognitiveActivity,
    DividendDistribution,
)

from .life_intensity_formula import (  # noqa: E402
    LifeIntensityFormula,
    KnowledgeState,
    ConstraintState,
    ObserverPresence,
    KnowledgeDomain,
    LifeIntensitySnapshot,
)

from .active_cognition_formula import (  # noqa: E402
    ActiveCognitionFormula,
    StressVector,
    OrderBaseline,
    ActiveConstruction,
    StressSource,
    OrderType,
)

from .non_paradox_existence import (  # noqa: E402
    NonParadoxExistence,
    GrayZoneVariable,
    PossibilityState,
    CoexistenceField,
    GrayZoneVariableType,
)

# Precision System - Memory-Precision Integration
from .precision.precision_manager import (  # noqa: E402
    PrecisionManager,
    DecimalMemoryBank,
    HierarchicalPrecisionRouter,
    PrecisionMemorySystem,
    PrecisionMode,
    create_precision_system,
)

# Maturity System - L0 to L11 Growth
from .maturity.maturity_system import (  # noqa: E402
    MaturityLevel,
    MaturityManager,
    ExperienceTracker,
    create_maturity_system,
)

# Creative Systems - Real API Integration
from .art.desktop_demo import (  # noqa: E402
    generate_and_save_to_desktop,
)

from .art.real_creator import (  # noqa: E402
    AngelaRealCreator,
    ComfyUIClient,
    AngelaRealVoice,
    AngelaRealBrowser,
)

from .art.real_comfyui_api import (  # noqa: E402
    AngelaRealPainter,
)

from .art.real_edge_tts import (  # noqa: E402
    AngelaRealVoice,
)

from .art.real_playwright_browser import (  # noqa: E402
    AngelaRealBrowser,
)

# Metamorphosis Systems - Version Transition
from .metamorphosis.soul_core import (  # noqa: E402
    SoulCore,
    SoulSignature,
    IdentityCore,
    MemoryEssence,
    SoulCoreManager,
    SoulComponent,
    create_soul_core,
)

from .metamorphosis.body_adapter import (  # noqa: E402
    BodyAdapter,
    StateSnapshot,
    TransferRecord,
    AdaptationRule,
    TransferStatus,
    CompatibilityLevel,
    BodyAdapterFactory,
    create_body_adapter,
)

from .metamorphosis.transition_anim import (  # noqa: E402
    TransitionAnimator,
    TransitionManager,
    TransitionConfig,
    TransitionProgress,
    TransitionFrame,
    TransitionPhase,
    TransitionType,
    create_transition_manager,
)

# Internationalization (i18n)
from .i18n.i18n_manager import (  # noqa: E402
    I18nManager,
    I18nConfig,
    I18nContext,
    TranslationEntry,
    TranslationCache,
    Language,
    Locale,
    t,
    set_language,
    get_language,
    add_translation,
    create_i18n_manager,
)

# Cloud Sync
from .sync.cloud_sync import (  # noqa: E402
    CloudSyncManager,
    CloudSyncConfig,
    SyncItem,
    SyncConflict,
    SyncProgress,
    SyncStatus,
    ConflictResolution,
    SyncQueue,
    CloudSyncFactory,
    create_cloud_sync_manager,
)

# Hardware Support
from .hardware.hal import (  # noqa: E402
    ArchitectureType,
    InstructionSet,
    HardwareVendor,
    ComputeUnit,
    PrecisionLevel,
    OperatingSystem,
    HardwareCapabilities,
    HardwareMetrics,
    HardwareDetector,
    HardwareManager,
    HardwareFactory,
    detect_hardware,
    create_hardware_manager,
)

from .hardware.precision_matrix import (  # noqa: E402
    PrecisionConfig,
    PrecisionMatrix,
    PrecisionManager,
    ConversionInfo,
    convert_precision,
    optimize_for_hardware,
    create_precision_manager,
)

from .hardware.compute_matrix import (  # noqa: E402
    OptimizationStrategy,
    MemoryLayout,
    KernelConfig,
    OptimizationResult,
    ComputationMatrix,
    ComputeOptimizer,
    get_optimization,
    create_compute_optimizer,
)

# Version Management
from .version import (  # noqa: E402
    get_version,
    get_version_info,
    __version__,
)

__author__ = "Angela AI Development Team"

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
    "AngelaRealCreator",
    "ComfyUIClient",
    "AngelaRealVoice",
    "AngelaRealBrowser",
    "AngelaRealPainter",
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
    "create_i18n_manager",
    # Cloud Sync
    "CloudSyncManager",
    "CloudSyncConfig",
    "SyncItem",
    "SyncConflict",
    "SyncProgress",
    "SyncStatus",
    "ConflictResolution",
    "SyncQueue",
    "CloudSyncFactory",
    "create_cloud_sync_manager",
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
    "create_hardware_manager",
    # Precision Management
    "PrecisionConfig",
    "PrecisionMatrix",
    "PrecisionManager",
    "ConversionInfo",
    "convert_precision",
    "optimize_for_hardware",
    "create_precision_manager",
    # Computation Optimization
    "OptimizationStrategy",
    "MemoryLayout",
    "KernelConfig",
    "OptimizationResult",
    "ComputationMatrix",
    "ComputeOptimizer",
    "get_optimization",
    "create_compute_optimizer",
]
