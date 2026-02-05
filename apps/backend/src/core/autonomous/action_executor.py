"""
Angela AI v6.0 - Action Executor
动作执行器

Central control system for executing actions with priority management,
queue handling, validation, and safety checks.

Features:
- Action queue management with priorities
- Action validation and safety checks
- Execution state tracking
- Interrupt and cancellation support
- Error handling and recovery

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import uuid
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..action_execution_bridge import ActionExecutionBridge, ExecutionResult


class ActionPriority(Enum):
    """动作优先级 / Action priorities"""
    CRITICAL = (0, "紧急", "Critical - Immediate execution required")
    HIGH = (1, "高", "High - Execute before normal actions")
    NORMAL = (2, "普通", "Normal - Standard execution order")
    LOW = (3, "低", "Low - Execute when system is idle")
    BACKGROUND = (4, "后台", "Background - Execute during idle time")
    
    def __init__(self, level: int, cn_name: str, description: str):
        self.level = level
        self.cn_name = cn_name
        self.description = description


class ActionStatus(Enum):
    """动作状态 / Action statuses"""
    PENDING = ("等待中", "Pending")
    VALIDATING = ("验证中", "Validating")
    EXECUTING = ("执行中", "Executing")
    COMPLETED = ("已完成", "Completed")
    FAILED = ("失败", "Failed")
    CANCELLED = ("已取消", "Cancelled")
    PAUSED = ("暂停", "Paused")
    
    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


class ActionCategory(Enum):
    """动作类别 / Action categories"""
    SYSTEM = ("系统", "System operations")
    UI = ("界面", "User interface actions")
    FILE = ("文件", "File operations")
    NETWORK = ("网络", "Network operations")
    AUDIO = ("音频", "Audio operations")
    VISUAL = ("视觉", "Visual operations")
    COMMUNICATION = ("通信", "Communication")
    SAFETY_CRITICAL = ("安全关键", "Safety critical operations")
    
    def __init__(self, cn_name: str, description: str):
        self.cn_name = cn_name
        self.description = description


@dataclass
class ActionResult:
    """动作执行结果 / Action execution result"""
    success: bool
    action_id: str
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0  # seconds
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SafetyCheck:
    """安全检查 / Safety check configuration"""
    check_name: str
    check_function: Callable[[Action], tuple[bool, Optional[str]]]
    is_critical: bool = False  # If True, failure blocks execution


@dataclass
class Action:
    """动作 / Action definition"""
    action_id: str
    name: str
    category: ActionCategory
    priority: ActionPriority
    function: Callable[..., Any]
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[ActionResult] = None
    dependencies: Set[str] = field(default_factory=set)
    timeout: float = 30.0  # seconds
    retry_count: int = 0
    max_retries: int = 3
    safety_checks: List[str] = field(default_factory=list)  # Names of required checks
    
    @classmethod
    def create(
        cls,
        name: str,
        category: ActionCategory,
        priority: ActionPriority,
        function: Callable[..., Any],
        parameters: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        max_retries: int = 3
    ) -> Action:
        """Factory method to create an action"""
        return cls(
            action_id=str(uuid.uuid4()),
            name=name,
            category=category,
            priority=priority,
            function=function,
            parameters=parameters or {},
            timeout=timeout,
            max_retries=max_retries
        )


class ActionQueue:
    """
    动作队列 / Action queue management
    
    Manages actions with priority-based scheduling and dependency resolution.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue: List[Action] = []
        self._completed: List[Action] = []
        self._failed: List[Action] = []
        self._action_map: Dict[str, Action] = {}
    
    def enqueue(self, action: Action) -> bool:
        """Add action to queue"""
        if len(self._queue) >= self.max_size:
            return False
        
        self._queue.append(action)
        self._action_map[action.action_id] = action
        
        # Sort by priority
        self._queue.sort(key=lambda a: a.priority.level)
        
        return True
    
    def dequeue(self) -> Optional[Action]:
        """Get next action from queue"""
        # Find first action with satisfied dependencies
        for action in self._queue:
            if self._dependencies_satisfied(action):
                self._queue.remove(action)
                return action
        return None
    
    def _dependencies_satisfied(self, action: Action) -> bool:
        """Check if all dependencies are completed"""
        for dep_id in action.dependencies:
            if dep_id in self._action_map:
                dep_action = self._action_map[dep_id]
                if dep_action.status != ActionStatus.COMPLETED:
                    return False
        return True
    
    def cancel_action(self, action_id: str) -> bool:
        """Cancel a pending action"""
        if action_id in self._action_map:
            action = self._action_map[action_id]
            if action.status == ActionStatus.PENDING:
                action.status = ActionStatus.CANCELLED
                if action in self._queue:
                    self._queue.remove(action)
                return True
        return False
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """Get action by ID"""
        return self._action_map.get(action_id)
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get queue statistics"""
        return {
            "pending": len([a for a in self._queue if a.status == ActionStatus.PENDING]),
            "executing": len([a for a in self._queue if a.status == ActionStatus.EXECUTING]),
            "completed": len(self._completed),
            "failed": len(self._failed),
            "total": len(self._action_map)
        }


class ActionExecutor:
    """
    动作执行器主类 / Main action executor class
    
    Central control system for managing and executing actions with full
    safety checks, priority handling, and state tracking.
    
    Attributes:
        queue: Action queue manager
        active_actions: Currently executing actions
        safety_checks: Registered safety checks
        execution_stats: Execution statistics
    
    Example:
        >>> executor = ActionExecutor()
        >>> await executor.initialize()
        >>> 
        >>> # Create an action
        >>> action = Action.create(
        ...     name="greet_user",
        ...     category=ActionCategory.UI,
        ...     priority=ActionPriority.NORMAL,
        ...     function=greet_function,
        ...     parameters={"user_name": "Alice"}
        ... )
        >>> 
        >>> # Submit and execute
        >>> result = await executor.submit_and_execute(action)
        >>> print(f"Success: {result.success}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Queue management
        self.queue = ActionQueue(max_size=self.config.get("max_queue_size", 1000))
        self.active_actions: Dict[str, Action] = {}
        self.max_concurrent = self.config.get("max_concurrent_actions", 5)
        
        # Safety system
        self.safety_checks: Dict[str, SafetyCheck] = {}
        self._register_default_safety_checks()
        
        # Execution control
        self._running = False
        self._executor_task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Callbacks
        self._pre_execution_callbacks: List[Callable[[Action], None]] = []
        self._post_execution_callbacks: List[Callable[[Action, ActionResult], None]] = []
        self._status_change_callbacks: Dict[str, List[Callable[[ActionStatus], None]]] = {}
        
        # Statistics
        self.execution_stats = {
            "total_executed": 0,
            "total_failed": 0,
            "total_cancelled": 0,
            "average_execution_time": 0.0,
        }
        
        # Dynamic Parameters Integration
        self._dynamic_params_manager: Optional[Any] = None
        self._dynamic_params_enabled: bool = self.config.get('enable_dynamic_params', True)
    
    async def initialize(self):
        """Initialize the action executor"""
        self._running = True
        self._executor_task = asyncio.create_task(self._execution_loop())
    
    async def shutdown(self):
        """Shutdown the executor"""
        self._running = False
        
        # Cancel all pending actions
        for action in list(self.queue._queue):
            action.status = ActionStatus.CANCELLED
        
        # Wait for active actions to complete
        if self.active_actions:
            await asyncio.gather(*[
                self._wait_for_action(action)
                for action in self.active_actions.values()
            ], return_exceptions=True)
        
        if self._executor_task:
            self._executor_task.cancel()
            try:
                await self._executor_task
            except asyncio.CancelledError:
                pass
            finally:
                self._executor_task = None
    
    async def _execution_loop(self):
        """Main execution loop"""
        while self._running:
            # Get next action
            action = self.queue.dequeue()
            
            if action:
                # Execute with semaphore for concurrency control
                asyncio.create_task(self._execute_with_semaphore(action))
            else:
                # No actions available, wait a bit
                await asyncio.sleep(0.1)
    
    async def _execute_with_semaphore(self, action: Action):
        """Execute action with concurrency control"""
        async with self._semaphore:
            await self._execute_action(action)
    
    async def _execute_action(self, action: Action):
        """Execute a single action with full lifecycle"""
        action.status = ActionStatus.VALIDATING
        action.started_at = datetime.now()
        self.active_actions[action.action_id] = action
        
        try:
            # Pre-execution callbacks
            for callback in self._pre_execution_callbacks:
                try:
                    callback(action)
                except Exception as e:
                    logger.warning(f"Pre-execution callback failed: {e}")
            
            # Validate action
            is_valid, error_msg = await self._validate_action(action)
            if not is_valid:
                action.status = ActionStatus.FAILED
                action.result = ActionResult(
                    success=False,
                    action_id=action.action_id,
                    error=error_msg or "Validation failed",
                    execution_time=0.0
                )
                self.queue._failed.append(action)
                del self.active_actions[action.action_id]
                return
            
            # Execute action
            action.status = ActionStatus.EXECUTING
            self._notify_status_change(action)
            
            start_time = asyncio.get_event_loop().time()
            
            try:
                # Get dynamic success rate
                success_rate = self._get_action_success_rate()
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    self._run_action_function(action),
                    timeout=action.timeout
                )
                
                execution_time = asyncio.get_event_loop().time() - start_time
                
                # Apply dynamic success rate (simulate occasional failures based on success rate)
                import random
                actual_success = random.random() < success_rate
                
                if actual_success:
                    action.status = ActionStatus.COMPLETED
                    action.result = ActionResult(
                        success=True,
                        action_id=action.action_id,
                        output=result,
                        execution_time=execution_time
                    )
                    self.queue._completed.append(action)
                    
                    # Update statistics
                    self._update_stats(execution_time, success=True)
                    
                    # Record success to dynamic params
                    self._record_action_outcome(action, success=True)
                else:
                    # Simulated failure due to dynamic success rate
                    action.status = ActionStatus.FAILED
                    action.result = ActionResult(
                        success=False,
                        action_id=action.action_id,
                        error="Action execution failed due to dynamic conditions",
                        execution_time=execution_time
                    )
                    self.queue._failed.append(action)
                    self._update_stats(execution_time, success=False)
                    
                    # Record failure to dynamic params
                    self._record_action_outcome(action, success=False)
                    
                    logger.warning(f"[ActionExecutor] Action {action.name} failed due to "
                                   f"dynamic success rate ({success_rate:.2%})")
                
            except asyncio.TimeoutError:
                execution_time = asyncio.get_event_loop().time() - start_time
                action.status = ActionStatus.FAILED
                action.result = ActionResult(
                    success=False,
                    action_id=action.action_id,
                    error=f"Action timed out after {action.timeout}s",
                    execution_time=execution_time
                )
                self.queue._failed.append(action)
                self._update_stats(execution_time, success=False)
                
                # Record failure to dynamic params
                self._record_action_outcome(action, success=False)
            
            action.completed_at = datetime.now()
            
            # Post-execution callbacks
            for callback in self._post_execution_callbacks:
                try:
                    callback(action, action.result)
                except Exception as e:
                    logger.warning(f"Post-execution callback failed: {e}")
            
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.result = ActionResult(
                success=False,
                action_id=action.action_id,
                error=str(e),
                execution_time=0.0
            )
            self.queue._failed.append(action)
            
            # Record failure to dynamic params
            self._record_action_outcome(action, success=False)
        
        finally:
            if action.action_id in self.active_actions:
                del self.active_actions[action.action_id]
    
    async def _validate_action(self, action: Action) -> tuple[bool, Optional[str]]:
        """Validate action through safety checks"""
        for check_name in action.safety_checks:
            if check_name in self.safety_checks:
                check = self.safety_checks[check_name]
                passed, message = check.check_function(action)
                
                if not passed:
                    if check.is_critical:
                        return False, message or f"Critical safety check failed: {check_name}"
                    else:
                        # Non-critical check failed - log but continue
                        logger.warning(f"Non-critical safety check failed: {check_name} - {message}")
        
        return True, None
    
    async def _run_action_function(self, action: Action) -> Any:
        """Run the actual action function"""
        if asyncio.iscoroutinefunction(action.function):
            return await action.function(**action.parameters)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                lambda: action.function(**action.parameters)
            )
    
    async def _wait_for_action(self, action: Action):
        """Wait for an action to complete"""
        while action.status in [ActionStatus.PENDING, ActionStatus.VALIDATING, ActionStatus.EXECUTING]:
            await asyncio.sleep(0.1)
    
    def _update_stats(self, execution_time: float, success: bool):
        """Update execution statistics"""
        self.execution_stats["total_executed"] += 1
        
        if not success:
            self.execution_stats["total_failed"] += 1
        
        # Update average execution time
        n = self.execution_stats["total_executed"]
        current_avg = self.execution_stats["average_execution_time"]
        self.execution_stats["average_execution_time"] = (
            (current_avg * (n - 1) + execution_time) / n
        )
    
    def _notify_status_change(self, action: Action):
        """Notify status change callbacks"""
        if action.action_id in self._status_change_callbacks:
            for callback in self._status_change_callbacks[action.action_id]:
                try:
                    callback(action.status)
                except Exception as e:
                    logger.warning(f"Status change callback failed for action {action.action_id}: {e}")
    
    def _register_default_safety_checks(self):
        """Register default safety checks"""
        self.register_safety_check(
            SafetyCheck(
                check_name="parameter_validation",
                check_function=self._check_parameters,
                is_critical=True
            )
        )
        
        self.register_safety_check(
            SafetyCheck(
                check_name="dependency_check",
                check_function=self._check_dependencies,
                is_critical=False
            )
        )
    
    def _check_parameters(self, action: Action) -> tuple[bool, Optional[str]]:
        """Check if required parameters are present"""
        # Basic check - ensure parameters is a dict
        if not isinstance(action.parameters, dict):
            return False, "Parameters must be a dictionary"
        return True, None
    
    def _check_dependencies(self, action: Action) -> tuple[bool, Optional[str]]:
        """Check if dependencies are valid"""
        for dep_id in action.dependencies:
            if dep_id not in self.queue._action_map:
                return False, f"Dependency {dep_id} not found"
        return True, None
    
    async def submit_and_execute(self, action: Action) -> ActionResult:
        """
        Submit an action and wait for execution
        
        Args:
            action: Action to execute
            
        Returns:
            ActionResult with execution outcome
        """
        if not self.queue.enqueue(action):
            return ActionResult(
                success=False,
                action_id=action.action_id,
                error="Queue is full"
            )
        
        # Wait for completion
        while action.status not in [ActionStatus.COMPLETED, ActionStatus.FAILED, ActionStatus.CANCELLED]:
            await asyncio.sleep(0.05)
        
        return action.result or ActionResult(
            success=False,
            action_id=action.action_id,
            error="No result available"
        )
    
    def submit(self, action: Action) -> str:
        """
        Submit an action for execution (non-blocking)
        
        Args:
            action: Action to submit
            
        Returns:
            Action ID
        """
        self.queue.enqueue(action)
        return action.action_id
    
    def cancel_action(self, action_id: str) -> bool:
        """Cancel a pending or executing action"""
        return self.queue.cancel_action(action_id)
    
    def register_safety_check(self, check: SafetyCheck):
        """Register a safety check"""
        self.safety_checks[check.check_name] = check
    
    def register_pre_execution_callback(self, callback: Callable[[Action], None]):
        """Register pre-execution callback"""
        self._pre_execution_callbacks.append(callback)
    
    def register_post_execution_callback(
        self, 
        callback: Callable[[Action, ActionResult], None]
    ):
        """Register post-execution callback"""
        self._post_execution_callbacks.append(callback)
    
    def register_status_change_callback(
        self, 
        action_id: str, 
        callback: Callable[[ActionStatus], None]
    ):
        """Register status change callback for specific action"""
        if action_id not in self._status_change_callbacks:
            self._status_change_callbacks[action_id] = []
        self._status_change_callbacks[action_id].append(callback)
    
    def get_action_status(self, action_id: str) -> Optional[ActionStatus]:
        """Get status of an action"""
        action = self.queue.get_action(action_id)
        return action.status if action else None
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        stats = self.execution_stats.copy()
        stats["queue_status"] = self.queue.get_queue_status()
        stats["active_actions"] = len(self.active_actions)
        return stats
    
    # ========== NEW: Integration with ActionExecutionBridge ==========
    
    def set_bridge(self, bridge: 'ActionExecutionBridge'):
        """Set the ActionExecutionBridge for integration"""
        self._bridge = bridge
    
    # ========== NEW: Integration with Dynamic Parameters ==========
    
    def set_dynamic_params_manager(self, manager: Any):
        """Set the DynamicThresholdManager for integration"""
        self._dynamic_params_manager = manager
        logger.info("[ActionExecutor] Dynamic parameters manager connected")
    
    def _get_action_success_rate(self, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic action success rate"""
        # For testing, we might want to bypass the random failure
        if self.config.get("bypass_dynamic_failure", False):
            return 1.0
            
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            return self._dynamic_params_manager.get_parameter('action_success_rate', context)
        return 0.85  # Default 85% success rate
    
    def _record_action_outcome(self, action: Action, success: bool):
        """Record action outcome to dynamic parameters manager"""
        if self._dynamic_params_manager and self._dynamic_params_enabled:
            try:
                self._dynamic_params_manager.record_outcome(
                    action_type=action.category.value[1],  # English name
                    success=success,
                    intensity=0.5 if action.priority.level <= 1 else 0.3
                )
            except Exception as e:
                logger.warning(f"[ActionExecutor] Failed to record outcome: {e}")
    
    async def handle_autonomous_action(
        self, 
        action_type: str, 
        parameters: Dict[str, Any],
        priority: int = 5
    ) -> 'ExecutionResult':
        """
        Handle autonomous actions from the life cycle system.
        This is the main integration point with the autonomous system.
        
        Args:
            action_type: Type of autonomous action
            parameters: Action parameters
            priority: Priority level (1-10)
            
        Returns:
            ExecutionResult from the bridge
        """
        if hasattr(self, '_bridge') and self._bridge:
            # Use bridge for execution
            return await self._bridge.execute_action(
                action_type=action_type,
                parameters=parameters,
                priority=priority,
                trigger_source="autonomous"
            )
        else:
            # Fallback: create and execute as regular action
            return await self._execute_fallback(action_type, parameters)
    
    async def _execute_fallback(
        self, 
        action_type: str, 
        parameters: Dict[str, Any]
    ) -> 'ExecutionResult':
        """Fallback execution when bridge is not available"""
        from ..action_execution_bridge import ExecutionResult, ExecutionResultStatus, ActionType
        
        action_id = str(uuid.uuid4())
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Try to handle basic action types
            if action_type == "initiate_conversation":
                message = parameters.get("message", "Hi!")
                print(f"[ActionExecutor] Fallback: {message}")
                
                execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ActionType.INITIATE_CONVERSATION,
                    status=ExecutionResultStatus.SUCCESS,
                    success=True,
                    data={"message": message, "method": "fallback"},
                    execution_time_ms=execution_time
                )
            
            elif action_type == "express_feeling":
                emotion = parameters.get("emotion", "neutral")
                print(f"[ActionExecutor] Fallback: Expressing {emotion}")
                
                execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ActionType.EXPRESS_FEELING,
                    status=ExecutionResultStatus.SUCCESS,
                    success=True,
                    data={"emotion": emotion, "method": "fallback"},
                    execution_time_ms=execution_time
                )
            
            else:
                execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
                return ExecutionResult(
                    action_id=action_id,
                    action_type=ActionType.SYSTEM_QUERY,
                    status=ExecutionResultStatus.FAILURE,
                    success=False,
                    error_message=f"No fallback handler for action type: {action_type}",
                    execution_time_ms=execution_time
                )
        
        except Exception as e:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            return ExecutionResult(
                action_id=action_id,
                action_type=ActionType.SYSTEM_QUERY,
                status=ExecutionResultStatus.FAILURE,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
    
    # ========== NEW: Execution History Persistence ==========
    
    async def save_execution_history(self, filepath: Optional[str] = None):
        """Save execution history to file"""
        path = Path(filepath or "~/.angela/executor_history.json").expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        history = []
        for action in self.queue._completed:
            if action.result:
                history.append({
                    "action_id": action.action_id,
                    "name": action.name,
                    "category": action.category.value[0],
                    "priority": action.priority.level,
                    "status": action.status.en_name,
                    "result": {
                        "success": action.result.success,
                        "error": action.result.error,
                        "execution_time": action.result.execution_time
                    },
                    "created_at": action.created_at.isoformat(),
                    "completed_at": action.completed_at.isoformat() if action.completed_at else None
                })
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    async def load_execution_history(self, filepath: Optional[str] = None):
        """Load execution history from file"""
        path = Path(filepath or "~/.angela/executor_history.json").expanduser()
        
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    # ========== NEW: Retry Mechanism ==========
    
    async def retry_action(self, action_id: str) -> Optional[ActionResult]:
        """Retry a failed action"""
        # Find in failed actions
        for action in self.queue._failed:
            if action.action_id == action_id:
                if action.retry_count < action.max_retries:
                    action.retry_count += 1
                    action.status = ActionStatus.PENDING
                    action.result = None
                    
                    # Re-queue
                    self.queue.enqueue(action)
                    
                    # Wait for completion
                    while action.status not in [ActionStatus.COMPLETED, ActionStatus.FAILED]:
                        await asyncio.sleep(0.05)
                    
                    return action.result
                else:
                    return ActionResult(
                        success=False,
                        action_id=action_id,
                        error="Max retries exceeded"
                    )
        
        return None
    
    # ========== NEW: Batch Operations ==========
    
    async def execute_batch(
        self, 
        actions: List[Action],
        continue_on_error: bool = True
    ) -> List[ActionResult]:
        """Execute multiple actions in batch"""
        results = []
        
        for action in actions:
            result = await self.submit_and_execute(action)
            results.append(result)
            
            if not result.success and not continue_on_error:
                break
        
        return results
    
    # ========== NEW: Validation Enhancement ==========
    
    def add_safety_check(
        self, 
        check_name: str, 
        check_function: Callable[[Action], tuple[bool, Optional[str]]],
        is_critical: bool = False
    ):
        """Add a custom safety check"""
        self.register_safety_check(
            SafetyCheck(
                check_name=check_name,
                check_function=check_function,
                is_critical=is_critical
            )
        )
    
    # ========== NEW: Result Validation ==========
    
    async def validate_result(
        self, 
        action: Action, 
        result: Any,
        validators: List[Callable[[Any], bool]]
    ) -> tuple[bool, Optional[str]]:
        """Validate action execution result"""
        for validator in validators:
            try:
                if not validator(result):
                    return False, f"Result validation failed: {validator.__name__}"
            except Exception as e:
                return False, f"Validation error: {str(e)}"
        
        return True, None


# Example usage
if __name__ == "__main__":
    async def demo():
        executor = ActionExecutor()
        await executor.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 动作执行器演示")
        print("Action Executor Demo")
        print("=" * 60)
        
        # Create sample actions
        async def sample_action_1(name: str):
            await asyncio.sleep(0.5)
            return f"Hello, {name}!"
        
        async def sample_action_2(value: int):
            await asyncio.sleep(0.3)
            return value * 2
        
        print("\n提交动作 / Submitting actions:")
        
        action1 = Action.create(
            name="greet",
            category=ActionCategory.COMMUNICATION,
            priority=ActionPriority.HIGH,
            function=sample_action_1,
            parameters={"name": "User"}
        )
        
        action2 = Action.create(
            name="calculate",
            category=ActionCategory.SYSTEM,
            priority=ActionPriority.NORMAL,
            function=sample_action_2,
            parameters={"value": 21}
        )
        
        # Submit actions
        id1 = executor.submit(action1)
        id2 = executor.submit(action2)
        print(f"  Action 1 ID: {id1}")
        print(f"  Action 2 ID: {id2}")
        
        # Execute one and wait
        print("\n执行并等待 / Execute and wait:")
        result = await executor.submit_and_execute(action1)
        print(f"  Success: {result.success}")
        print(f"  Output: {result.output}")
        print(f"  Time: {result.execution_time:.3f}s")
        
        # Wait for queue to process
        await asyncio.sleep(1)
        
        # Show stats
        print("\n执行统计 / Execution stats:")
        stats = executor.get_execution_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        await executor.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
