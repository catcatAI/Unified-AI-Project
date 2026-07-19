"""
Autonomous Action Executor Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""

from __future__ import annotations

from core.engine.action_executor import (
    Action,
    ActionCategory,
    ActionExecutor,
    ActionPriority,
    ActionQueue,
    ActionResult,
    ActionStatus,
    SafetyCheck,
)
