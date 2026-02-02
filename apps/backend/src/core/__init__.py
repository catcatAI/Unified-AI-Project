"""
Angela AI v6.0 - Core Module
核心模块

Contains core systems including action execution, orchestration,
and system management components.

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
]
