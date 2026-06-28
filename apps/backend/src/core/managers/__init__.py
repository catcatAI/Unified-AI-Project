"""
Managers module — system management and execution monitoring.

P10: SystemManager (application lifecycle, startup/shutdown orchestration).
P11: ExecutionMonitor (async execution with timeout and monitoring).
P12: DependencyManager (service dependency graph and resolution).
"""

from core.managers.dependency_manager import DependencyManager, DependencyStatus
from core.managers.execution_monitor import ExecutionMonitor, ExecutionResult, ExecutionConfig, ExecutionStatus, TerminalStatus, get_execution_monitor, execute_with_monitoring
from core.managers.system_manager import SystemManager

__all__ = [
    "DependencyManager",
    "DependencyStatus",
    "ExecutionMonitor",
    "ExecutionResult",
    "ExecutionConfig",
    "ExecutionStatus",
    "TerminalStatus",
    "get_execution_monitor",
    "execute_with_monitoring",
    "SystemManager",
]
