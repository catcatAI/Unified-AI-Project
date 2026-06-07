"""
Autonomous Action Executor Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""
from __future__ import annotations

from core.engine.action_executor import (
    ActionExecutor,
    ActionQueue,
    ActionPriority,
    Action,
    ActionResult,
    ActionStatus,
    ActionCategory,
    SafetyCheck,
)