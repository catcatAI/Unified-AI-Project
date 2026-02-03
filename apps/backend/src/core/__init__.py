"""
Angela AI v6.0 - Core Module
核心模块

Contains core systems including action execution, orchestration,
theoretical formulas for digital life, and system management components.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

# Action Execution Layer
from .action_execution_bridge import (
    ActionExecutionBridge,
    ActionExecutionBridgeFactory,
    ActionType,
    ExecutionResult,
    ExecutionResultStatus,
    ExecutionContext,
    FeedbackCollector,
)

# Autonomous Systems
from .autonomous.action_executor import (
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
from .hsm_formula_system import (
    HSMFormulaSystem,
    CognitiveGap,
    ExplorationEvent,
    GovernanceBlueprint,
    ExplorationResult,
)

from .cdm_dividend_model import (
    CDMCognitiveDividendModel,
    CognitiveInvestment,
    LifeSenseOutput,
    CognitiveActivity,
    DividendDistribution,
)

from .life_intensity_formula import (
    LifeIntensityFormula,
    KnowledgeState,
    ConstraintState,
    ObserverPresence,
    KnowledgeDomain,
    LifeIntensitySnapshot,
)

from .active_cognition_formula import (
    ActiveCognitionFormula,
    StressVector,
    OrderBaseline,
    ActiveConstruction,
    StressSource,
    OrderType,
)

from .non_paradox_existence import (
    NonParadoxExistence,
    GrayZoneVariable,
    PossibilityState,
    CoexistenceField,
    GrayZoneVariableType,
)

__version__ = "6.0.0"
__author__ = "Angela AI Development Team"

__all__ = [
    # Version
    "__version__",
    "__author__",
    
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
]
