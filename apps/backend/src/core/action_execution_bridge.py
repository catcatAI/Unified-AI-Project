"""
Angela AI v6.0 - Action Execution Bridge
动作执行桥接器

Connects autonomous system decisions to actual execution.
Handles all action types with priority queue, dependency resolution,
and execution validation.

This is the core breakpoint of the system, bridging the gap between
cognitive decisions (HSM/CDM/Autonomy Matrix) and physical actions.

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any, Set, Union, TYPE_CHECKING
from datetime import datetime, timedelta
import asyncio
import uuid
import json
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# Type imports to avoid circular dependencies
if TYPE_CHECKING:
    from .action_executor import ActionExecutor, Action, ActionResult, ActionPriority, ActionStatus


class ActionType(Enum):
    """动作类型 / Action types supported by the system"""
    INITIATE_CONVERSATION = ("initiate_conversation", "发起对话", "主动开始与用户的对话")
    EXPLORE_TOPIC = ("explore_topic", "探索话题", "自主探索感兴趣的主题")
    SATISFY_NEED = ("satisfy_need", "满足需求", "满足生理或心理需求")
    EXPRESS_FEELING = ("express_feeling", "表达情感", "表达当前情感状态")
    DOWNLOAD_RESOURCE = ("download_resource", "下载资源", "从网络获取资源")
    CHANGE_APPEARANCE = ("change_appearance", "改变外观", "修改视觉表现")
    FILE_OPERATION = ("file_operation", "文件操作", "读写或管理文件")
    WEB_SEARCH = ("web_search", "网络搜索", "搜索网络信息")
    SYSTEM_QUERY = ("system_query", "系统查询", "查询系统状态或信息")
    
    def __init__(self, value: str, cn_name: str, description: str):
        self._value_ = value
        self.cn_name = cn_name
        self.description = description
    
    @classmethod
    def from_string(cls, type_str: str) -> Optional[ActionType]:
        """从字符串获取动作类型"""
        for action_type in cls:
            if action_type.value == type_str:
                return action_type
        return None


class ExecutionResultStatus(Enum):
    """执行结果状态 / Execution result status"""
    SUCCESS = ("success", "成功")
    PARTIAL = ("partial", "部分成功")
    FAILURE = ("failure", "失败")
    CANCELLED = ("cancelled", "已取消")
    TIMEOUT = ("timeout", "超时")
    
    def __init__(self, value: str, cn_name: str):
        self._value_ = value
        self.cn_name = cn_name


@dataclass
class ExecutionContext:
    """执行上下文 / Execution context for an action"""
    action_id: str
    action_type: ActionType
    trigger_source: str  # 'autonomous', 'user', 'system'
    priority: int
    timestamp: datetime = field(default_factory=datetime.now)
    user_context: Dict[str, Any] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行结果 / Execution result with full details"""
    action_id: str
    action_type: ActionType
    status: ExecutionResultStatus
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    feedback_for_learning: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "success": self.success,
            "data": self.data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "feedback_for_learning": self.feedback_for_learning
        }


@dataclass
class ActionDependency:
    """动作依赖 / Dependency between actions"""
    action_id: str
    depends_on: List[str]  # IDs of actions that must complete first
    priority_boost: int = 0  # Priority boost when dependencies are satisfied


class FeedbackCollector:
    """反馈收集器 / Collects execution feedback for learning"""
    
    def __init__(self):
        self.feedback_history: List[Dict[str, Any]] = []
        self.success_patterns: Dict[str, int] = {}
        self.failure_patterns: Dict[str, int] = {}
    
    def collect(self, result: ExecutionResult):
        """收集执行反馈"""
        feedback = {
            "action_type": result.action_type.value,
            "success": result.success,
            "execution_time": result.execution_time_ms,
            "timestamp": result.timestamp,
            "context": result.feedback_for_learning
        }
        self.feedback_history.append(feedback)
        
        # Update patterns
        pattern_key = f"{result.action_type.value}:{result.success}"
        if result.success:
            self.success_patterns[pattern_key] = self.success_patterns.get(pattern_key, 0) + 1
        else:
            self.failure_patterns[pattern_key] = self.failure_patterns.get(pattern_key, 0) + 1
    
    def get_learning_data(self) -> Dict[str, Any]:
        """获取用于学习的数据"""
        return {
            "feedback_count": len(self.feedback_history),
            "success_rate": self._calculate_success_rate(),
            "success_patterns": self.success_patterns,
            "failure_patterns": self.failure_patterns,
            "recent_feedback": self.feedback_history[-50:]  # Last 50 entries
        }
    
    def _calculate_success_rate(self) -> float:
        """计算成功率"""
        if not self.feedback_history:
            return 0.0
        successful = sum(1 for f in self.feedback_history if f["success"])
        return successful / len(self.feedback_history)


class ActionExecutionBridge:
    """
    动作执行桥接器 / Action Execution Bridge
    
    The core component that bridges autonomous system decisions to actual execution.
    This is the system's main breakpoint connecting cognition to action.
    
    Features:
    - Priority queue management for all action types
    - Dependency resolution between actions
    - Execution validation and result verification
    - Feedback loop to HSM/CDM for learning
    - Comprehensive error handling and retry mechanisms
    - Execution history persistence
    
    Example:
        >>> bridge = ActionExecutionBridge(
        ...     orchestrator=orchestrator,
        ...     desktop_pet=desktop_pet,
        ...     file_manager=file_manager,
        ...     download_manager=download_manager
        ... )
        >>> await bridge.initialize()
        >>> 
        >>> # Execute an autonomous action
        >>> result = await bridge.execute_action(
        ...     action_type=ActionType.INITIATE_CONVERSATION,
        ...     parameters={"message": "Hi there!", "emotion": "happy"}
        ... )
    """
    
    def __init__(
        self,
        orchestrator: Optional[Any] = None,
        desktop_pet: Optional[Any] = None,
        file_manager: Optional[Any] = None,
        download_manager: Optional[Any] = None,
        web_search_tool: Optional[Any] = None,
        hsm: Optional[Any] = None,
        cdm: Optional[Any] = None,
        live2d_integration: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # Component references
        self.orchestrator = orchestrator
        self.desktop_pet = desktop_pet
        self.file_manager = file_manager
        self.download_manager = download_manager
        self.web_search_tool = web_search_tool
        self.hsm = hsm
        self.cdm = cdm
        self.live2d_integration = live2d_integration
        
        # Action handlers
        self._handlers: Dict[ActionType, Callable] = {
            ActionType.INITIATE_CONVERSATION: self._handle_initiate_conversation,
            ActionType.EXPLORE_TOPIC: self._handle_explore_topic,
            ActionType.SATISFY_NEED: self._handle_satisfy_need,
            ActionType.EXPRESS_FEELING: self._handle_express_feeling,
            ActionType.DOWNLOAD_RESOURCE: self._handle_download_resource,
            ActionType.CHANGE_APPEARANCE: self._handle_change_appearance,
            ActionType.FILE_OPERATION: self._handle_file_operation,
            ActionType.WEB_SEARCH: self._handle_web_search,
            ActionType.SYSTEM_QUERY: self._handle_system_query,
        }
        
        # Queue management
        self._priority_queue: List[tuple[int, str, Dict[str, Any]]] = []
        self._dependencies: Dict[str, ActionDependency] = {}
        self._completed_actions: Dict[str, ExecutionResult] = {}
        self._executing_actions: Set[str] = set()
        
        # Feedback system
        self.feedback_collector = FeedbackCollector()
        
        # Execution control
        self._running = False
        self._max_concurrent = self.config.get("max_concurrent", 3)
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
        self._execution_task: Optional[asyncio.Task] = None
        
        # History persistence
        self._history_file = Path(self.config.get("history_path", "~/.angela/action_history.json")).expanduser()
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history_size = self.config.get("max_history_size", 1000)
        
        # Statistics
        self._stats = {
            "total_executed": 0,
            "total_successful": 0,
            "total_failed": 0,
            "average_execution_time": 0.0,
            "action_type_counts": {}
        }
        
        # Callbacks
        self._pre_execution_callbacks: List[Callable[[ExecutionContext], None]] = []
        self._post_execution_callbacks: List[Callable[[ExecutionContext, ExecutionResult], None]] = []
    
    async def initialize(self):
        """Initialize the action execution bridge"""
        self._running = True
        
        # Load execution history
        await self._load_history()
        
        # Start execution loop
        self._execution_task = asyncio.create_task(self._execution_loop())
        
        print("[ActionExecutionBridge] Initialized successfully")
    
    async def shutdown(self):
        """Shutdown the bridge"""
        self._running = False
        
        # Cancel execution loop
        if self._execution_task:
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass
        
        # Save history
        await self._save_history()
        
        print("[ActionExecutionBridge] Shutdown complete")
    
    async def execute_action(
        self,
        action_type: Union[ActionType, str],
        parameters: Dict[str, Any],
        priority: int = 5,
        dependencies: Optional[List[str]] = None,
        trigger_source: str = "autonomous",
        wait_for_completion: bool = True
    ) -> ExecutionResult:
        """
        Execute an action with full lifecycle management
        
        Args:
            action_type: Type of action to execute
            parameters: Action parameters
            priority: Priority level (1-10, lower is higher priority)
            dependencies: List of action IDs that must complete first
            trigger_source: Source of the trigger ('autonomous', 'user', 'system')
            wait_for_completion: Whether to wait for execution completion
            
        Returns:
            ExecutionResult with full execution details
        """
        # Convert string to enum if needed
        resolved_action_type: ActionType
        if isinstance(action_type, str):
            resolved_type = ActionType.from_string(action_type)
            if not resolved_type:
                return ExecutionResult(
                    action_id=str(uuid.uuid4()),
                    action_type=ActionType.SYSTEM_QUERY,
                    status=ExecutionResultStatus.FAILURE,
                    success=False,
                    error_message=f"Unknown action type: {action_type}"
                )
            resolved_action_type = resolved_type
        else:
            resolved_action_type = action_type
        
        # Generate action ID
        action_id = str(uuid.uuid4())
        
        # Create execution context
        context = ExecutionContext(
            action_id=action_id,
            action_type=resolved_action_type,
            trigger_source=trigger_source,
            priority=priority,
            user_context=parameters.get("user_context", {}),
            system_context=await self._get_system_context(),
            metadata=parameters.get("metadata", {})
        )
        
        # Register dependencies
        if dependencies:
            self._dependencies[action_id] = ActionDependency(
                action_id=action_id,
                depends_on=dependencies
            )
        
        # Add to priority queue
        queue_item = (priority, action_id, {
            "context": context,
            "parameters": parameters,
            "created_at": datetime.now()
        })
        self._priority_queue.append(queue_item)
        self._priority_queue.sort(key=lambda x: x[0])  # Sort by priority
        
        if wait_for_completion:
            # Wait for execution completion
            return await self._wait_for_completion(action_id)
        else:
            # Return immediately with pending status
            return ExecutionResult(
                action_id=action_id,
                action_type=resolved_action_type,
                status=ExecutionResultStatus.SUCCESS,
                success=True,
                data={"status": "queued"}
            )
    
    async def _execution_loop(self):
        """Main execution loop - processes actions from the queue"""
        while self._running:
            # Find next executable action
            executable = self._get_next_executable_action()
            
            if executable:
                priority, action_id, item = executable
                self._priority_queue.remove(executable)
                
                # Execute with semaphore
                asyncio.create_task(self._execute_with_semaphore(action_id, item))
            else:
                # No executable actions, wait a bit
                await asyncio.sleep(0.1)
    
    def _get_next_executable_action(self) -> Optional[tuple]:
        """Get the next action that can be executed (dependencies satisfied)"""
        for item in self._priority_queue:
            priority, action_id, _ = item
            
            # Check if dependencies are satisfied
            if action_id in self._dependencies:
                dep = self._dependencies[action_id]
                all_completed = all(
                    dep_id in self._completed_actions 
                    for dep_id in dep.depends_on
                )
                if not all_completed:
                    continue
            
            return item
        
        return None
    
    async def _execute_with_semaphore(self, action_id: str, item: Dict[str, Any]):
        """Execute action with concurrency control"""
        async with self._semaphore:
            await self._execute_action(action_id, item)
    
    async def _execute_action(self, action_id: str, item: Dict[str, Any]):
        """Execute a single action"""
        context: ExecutionContext = item["context"]
        parameters: Dict[str, Any] = item["parameters"]
        
        self._executing_actions.add(action_id)
        start_time = asyncio.get_event_loop().time()
        result: ExecutionResult
        
        try:
            # Pre-execution callbacks
            for callback in self._pre_execution_callbacks:
                try:
                    callback(context)
                except Exception as e:
                    print(f"[ActionExecutionBridge] Pre-execution callback error: {e}")
            
            # Get handler
            handler = self._handlers.get(context.action_type)
            if not handler:
                raise ValueError(f"No handler for action type: {context.action_type}")
            
            # Execute handler
            result_data = await handler(parameters, context)
            
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            
            # Create success result
            result = ExecutionResult(
                action_id=action_id,
                action_type=context.action_type,
                status=ExecutionResultStatus.SUCCESS,
                success=True,
                data=result_data,
                execution_time_ms=execution_time,
                feedback_for_learning={
                    "trigger_source": context.trigger_source,
                    "priority": context.priority,
                    "parameters": parameters
                }
            )
            
        except asyncio.TimeoutError:
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)
            result = ExecutionResult(
                action_id=action_id,
                action_type=context.action_type,
                status=ExecutionResultStatus.TIMEOUT,
                success=False,
                error_message="Action timed out",
                execution_time_ms=execution_time
            )
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            execution_time = int((asyncio.get_event_loop().time() - start_time) * 1000)

            result = ExecutionResult(
                action_id=action_id,
                action_type=context.action_type,
                status=ExecutionResultStatus.FAILURE,
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
        
        finally:
            self._executing_actions.discard(action_id)
            if 'result' in locals():
                self._completed_actions[action_id] = result
                
                # Update statistics
                self._update_stats(result)
                
                # Collect feedback
                self.feedback_collector.collect(result)
                
                # Persist to history
                await self._persist_result(result)
                
                # Post-execution callbacks
                for callback in self._post_execution_callbacks:
                    try:
                        callback(context, result)
                    except Exception as e:
                        print(f"[ActionExecutionBridge] Post-execution callback error: {e}")
                
                # Send feedback to CDM for learning (if available)
                if self.cdm:
                    await self._send_feedback_to_cdm(result)
    
    async def _wait_for_completion(self, action_id: str) -> ExecutionResult:
        """Wait for an action to complete"""
        while action_id in self._executing_actions or action_id not in self._completed_actions:
            await asyncio.sleep(0.05)
        
        return self._completed_actions[action_id]
    
    async def _get_system_context(self) -> Dict[str, Any]:
        """Get current system context"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_actions": len(self._executing_actions),
            "queue_size": len(self._priority_queue),
            "completed_count": len(self._completed_actions)
        }
    
    def _update_stats(self, result: ExecutionResult):
        """Update execution statistics"""
        self._stats["total_executed"] += 1
        
        if result.success:
            self._stats["total_successful"] += 1
        else:
            self._stats["total_failed"] += 1
        
        # Update average execution time
        n = self._stats["total_executed"]
        current_avg = self._stats["average_execution_time"]
        self._stats["average_execution_time"] = (
            (current_avg * (n - 1) + result.execution_time_ms) / n
        )
        
        # Update action type counts
        type_key = result.action_type.value
        if type_key not in self._stats["action_type_counts"]:
            self._stats["action_type_counts"][type_key] = {"success": 0, "failure": 0}
        
        if result.success:
            self._stats["action_type_counts"][type_key]["success"] += 1
        else:
            self._stats["action_type_counts"][type_key]["failure"] += 1
    
    async def _persist_result(self, result: ExecutionResult):
        """Persist execution result to history"""
        self._execution_history.append(result.to_dict())
        
        # Trim history if too large
        if len(self._execution_history) > self._max_history_size:
            self._execution_history = self._execution_history[-self._max_history_size:]
        
        # Save periodically (every 10 actions)
        if len(self._execution_history) % 10 == 0:
            await self._save_history()
    
    async def _load_history(self):
        """Load execution history from file"""
        try:
            if self._history_file.exists():
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    self._execution_history = json.load(f)
        except Exception as e:
            print(f"[ActionExecutionBridge] Failed to load history: {e}")
    
    async def _save_history(self):
        """Save execution history to file"""
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(self._execution_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ActionExecutionBridge] Failed to save history: {e}")
    
    async def _send_feedback_to_cdm(self, result: ExecutionResult):
        """Send execution feedback to CDM for learning"""
        if not self.cdm:
            return
        
        try:
            # Create delta for learning
            feedback_delta = {
                "type": "execution_feedback",
                "action_type": result.action_type.value,
                "success": result.success,
                "execution_time": result.execution_time_ms,
                "timestamp": result.timestamp.isoformat(),
                "context": result.feedback_for_learning
            }
            
            # Integrate into CDM if method exists
            if hasattr(self.cdm, 'integrate_execution_feedback'):
                await self.cdm.integrate_execution_feedback(feedback_delta)
            elif hasattr(self.cdm, 'compute_delta'):
                delta = self.cdm.compute_delta(feedback_delta)
                if hasattr(self.cdm, 'should_trigger_learning'):
                    if self.cdm.should_trigger_learning(delta):
                        if hasattr(self.cdm, 'integrate_knowledge'):
                            self.cdm.integrate_knowledge(feedback_delta, delta)
        except Exception as e:
            print(f"[ActionExecutionBridge] Failed to send feedback to CDM: {e}")
    
    # ========== Action Handlers ==========
    
    async def _handle_initiate_conversation(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle initiate_conversation action"""
        message = parameters.get("message", "Hi there!")
        emotion = parameters.get("emotion", "neutral")
        topic = parameters.get("topic", None)
        
        result = {"message": message, "emotion": emotion}
        
        # Send to orchestrator if available
        if self.orchestrator:
            try:
                if hasattr(self.orchestrator, 'generate_proactive_message'):
                    response = await self.orchestrator.generate_proactive_message(
                        message=message,
                        emotion=emotion,
                        topic=topic
                    )
                    result["orchestrator_response"] = response
                elif hasattr(self.orchestrator, 'process_user_input'):
                    response = await self.orchestrator.process_user_input(
                        f"[AUTONOMOUS] {message}"
                    )
                    result["orchestrator_response"] = response
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["orchestrator_error"] = str(e)

        
        # Show in desktop pet if available
        if self.desktop_pet:
            try:
                if hasattr(self.desktop_pet, 'show_message'):
                    self.desktop_pet.show_message(message, emotion=emotion)
                elif hasattr(self.desktop_pet, 'display_bubble'):
                    self.desktop_pet.display_bubble(message)
                result["displayed"] = True
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["display_error"] = str(e)

        
        return result
    
    async def _handle_explore_topic(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle explore_topic action"""
        topic = parameters.get("topic", "")
        depth = parameters.get("depth", "medium")  # shallow, medium, deep
        source = parameters.get("source", "web")  # web, local, mixed
        
        result = {
            "topic": topic,
            "depth": depth,
            "source": source,
            "exploration_data": {}
        }
        
        # Search for information
        if source in ["web", "mixed"] and self.web_search_tool:
            try:
                search_results = await self.web_search_tool.search(
                    query=topic,
                    num_results=5 if depth == "shallow" else 10 if depth == "medium" else 20
                )
                result["exploration_data"]["search_results"] = search_results
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["search_error"] = str(e)

        
        # Search local files
        if source in ["local", "mixed"] and self.file_manager:
            try:
                # Search for files related to topic
                if hasattr(self.file_manager, 'search_files'):
                    local_results = await self.file_manager.search_files(topic)
                    result["exploration_data"]["local_files"] = local_results
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["local_search_error"] = str(e)

        
        # Integrate into CDM
        if self.cdm and result["exploration_data"]:
            try:
                if hasattr(self.cdm, 'ingest_document'):
                    for item in result["exploration_data"].get("search_results", []):
                        await self.cdm.ingest_document(
                            content=item.get("snippet", ""),
                            source=item.get("url", "web_search"),
                            metadata={"topic": topic, "type": "exploration"}
                        )
                result["integrated_to_cdm"] = True
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["cdm_integration_error"] = str(e)

        
        return result
    
    async def _handle_satisfy_need(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle satisfy_need action"""
        need_type = parameters.get("need_type", "")  # hunger, social, rest, curiosity, etc.
        urgency = parameters.get("urgency", 0.5)
        suggested_action = parameters.get("suggested_action", None)
        
        result = {
            "need_type": need_type,
            "urgency": urgency,
            "action_taken": None
        }
        
        # Handle different need types
        if need_type == "social":
            # Initiate conversation
            if self.desktop_pet:
                messages = [
                    "我想你了，在吗？",
                    "有点无聊呢，陪我聊聊天吧~",
                    "今天过得怎么样？"
                ]
                import random
                message = random.choice(messages)
                result["action_taken"] = "initiated_conversation"
                result["message"] = message
                
                if hasattr(self.desktop_pet, 'show_message'):
                    self.desktop_pet.show_message(message, emotion="lonely")
        
        elif need_type == "curiosity":
            # Explore a random topic
            topics = ["人工智能", "音乐", "艺术", "科学", "历史"]
            import random
            topic = random.choice(topics)
            result["action_taken"] = "explored_topic"
            result["topic"] = topic
            
            # Trigger exploration
            await self.execute_action(
                action_type=ActionType.EXPLORE_TOPIC,
                parameters={"topic": topic, "depth": "shallow"},
                wait_for_completion=False
            )
        
        elif need_type == "rest":
            result["action_taken"] = "indicated_rest"
            result["message"] = "我有点累了，需要休息一下..."
        
        return result
    
    async def _handle_express_feeling(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle express_feeling action"""
        emotion = parameters.get("emotion", "neutral")
        intensity = parameters.get("intensity", 0.5)
        reason = parameters.get("reason", None)
        
        result = {
            "emotion": emotion,
            "intensity": intensity,
            "reason": reason
        }
        
        # Map emotions to messages
        emotion_messages = {
            "happy": ["今天心情真好！", "感觉很开心~", "超级高兴！"],
            "sad": ["有点难过...", "心情不太好", "感到有些失落"],
            "lonely": ["感觉好孤单...", "想找人陪陪我", "一个人好无聊"],
            "curious": ["好想知道更多！", "这个很有趣~", "我想了解更多"],
            "excited": ["太激动了！", "好兴奋啊！", "迫不及待了！"],
            "tired": ["有点累了...", "需要休息一下", "感觉有点疲惫"]
        }
        
        import random
        messages = emotion_messages.get(emotion, ["心情还不错~"])
        message = random.choice(messages)
        result["message"] = message
        
        # Display in desktop pet
        if self.desktop_pet:
            try:
                if hasattr(self.desktop_pet, 'show_message'):
                    self.desktop_pet.show_message(message, emotion=emotion)
                elif hasattr(self.desktop_pet, 'display_bubble'):
                    self.desktop_pet.display_bubble(message)
                result["displayed"] = True
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["display_error"] = str(e)

        
        # Update Live2D if available
        if self.live2d_integration:
            try:
                if hasattr(self.live2d_integration, 'set_expression'):
                    await self.live2d_integration.set_expression(emotion, intensity)
                    result["live2d_updated"] = True
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                result["live2d_error"] = str(e)

        
        return result
    
    async def _handle_download_resource(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle download_resource action"""
        url = parameters.get("url", "")
        destination = parameters.get("destination", None)
        resource_type = parameters.get("resource_type", "general")  # live2d, knowledge, image, audio, general
        auto_ingest = parameters.get("auto_ingest", True)
        
        result = {
            "url": url,
            "resource_type": resource_type,
            "downloaded": False
        }
        
        if not self.download_manager:
            result["error"] = "Download manager not available"
            return result
        
        try:
            # Download file
            if hasattr(self.download_manager, 'download_file'):
                download_result = await self.download_manager.download_file(
                    url=url,
                    destination=destination,
                    resource_type=resource_type
                )
                result["downloaded"] = True
                result["download_result"] = download_result
                
                # Auto-ingest to CDM if enabled
                if auto_ingest and self.cdm:
                    if resource_type == "knowledge":
                        if hasattr(self.cdm, 'ingest_document'):
                            # Extract content from downloaded file
                            file_path = download_result.get("file_path")
                            if file_path and self.file_manager:
                                content = await self.file_manager.read_file(file_path)
                                if content:
                                    await self.cdm.ingest_document(
                                        content=content,
                                        source=url,
                                        metadata={"type": "downloaded_knowledge"}
                                    )
                                    result["ingested_to_cdm"] = True
            else:
                result["error"] = "Download manager missing download_file method"
        
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            result["error"] = str(e)

        
        return result
    
    async def _handle_change_appearance(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle change_appearance action"""
        change_type = parameters.get("change_type", "expression")  # expression, outfit, pose
        value = parameters.get("value", "")
        duration = parameters.get("duration", None)  # Temporary change duration
        
        result = {
            "change_type": change_type,
            "value": value,
            "applied": False
        }
        
        if not self.live2d_integration:
            result["error"] = "Live2D integration not available"
            return result
        
        try:
            if change_type == "expression":
                if hasattr(self.live2d_integration, 'set_expression'):
                    await self.live2d_integration.set_expression(value, intensity=0.8)
                    result["applied"] = True
            
            elif change_type == "outfit":
                if hasattr(self.live2d_integration, 'change_outfit'):
                    await self.live2d_integration.change_outfit(value)
                    result["applied"] = True
            
            elif change_type == "pose":
                if hasattr(self.live2d_integration, 'set_pose'):
                    await self.live2d_integration.set_pose(value)
                    result["applied"] = True
        
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            result["error"] = str(e)

        
        return result
    
    async def _handle_file_operation(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle file_operation action"""
        operation = parameters.get("operation", "read")  # read, write, delete, list, move
        path = parameters.get("path", "")
        content = parameters.get("content", None)
        encoding = parameters.get("encoding", "utf-8")
        
        result = {
            "operation": operation,
            "path": path,
            "success": False
        }
        
        if not self.file_manager:
            result["error"] = "File manager not available"
            return result
        
        try:
            if operation == "read":
                if hasattr(self.file_manager, 'read_file'):
                    data = await self.file_manager.read_file(path, encoding=encoding)
                    result["success"] = True
                    result["content"] = data
            
            elif operation == "write":
                if hasattr(self.file_manager, 'write_file'):
                    success = await self.file_manager.write_file(
                        path, content, encoding=encoding
                    )
                    result["success"] = success
            
            elif operation == "delete":
                if hasattr(self.file_manager, 'delete_file'):
                    success = await self.file_manager.delete_file(path)
                    result["success"] = success
            
            elif operation == "list":
                if hasattr(self.file_manager, 'list_directory'):
                    files = await self.file_manager.list_directory(path)
                    result["success"] = True
                    result["files"] = files
            
            elif operation == "move":
                destination = parameters.get("destination", "")
                if hasattr(self.file_manager, 'move_file'):
                    success = await self.file_manager.move_file(path, destination)
                    result["success"] = success
        
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            result["error"] = str(e)

        
        return result
    
    async def _handle_web_search(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle web_search action"""
        query = parameters.get("query", "")
        num_results = parameters.get("num_results", 5)
        search_engine = parameters.get("search_engine", "duckduckgo")
        
        result = {
            "query": query,
            "num_results": num_results,
            "search_engine": search_engine,
            "results": []
        }
        
        if not self.web_search_tool:
            result["error"] = "Web search tool not available"
            return result
        
        try:
            if hasattr(self.web_search_tool, 'search'):
                search_results = await self.web_search_tool.search(
                    query=query,
                    num_results=num_results
                )
                result["results"] = search_results
                result["success"] = True
            else:
                result["error"] = "Web search tool missing search method"
        
        except Exception as e:
            logger.error(f'Error in {__name__}: {e}', exc_info=True)
            result["error"] = str(e)

        
        return result
    
    async def _handle_system_query(
        self, 
        parameters: Dict[str, Any], 
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Handle system_query action"""
        query_type = parameters.get("query_type", "status")  # status, stats, health, config
        
        result = {
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if query_type == "status":
            result["bridge_status"] = {
                "running": self._running,
                "queue_size": len(self._priority_queue),
                "executing": len(self._executing_actions),
                "completed": len(self._completed_actions)
            }
        
        elif query_type == "stats":
            result["execution_stats"] = self._stats
            result["feedback_stats"] = self.feedback_collector.get_learning_data()
        
        elif query_type == "health":
            result["health"] = {
                "bridge_healthy": self._running,
                "components": {
                    "orchestrator": self.orchestrator is not None,
                    "desktop_pet": self.desktop_pet is not None,
                    "file_manager": self.file_manager is not None,
                    "download_manager": self.download_manager is not None,
                    "web_search": self.web_search_tool is not None,
                    "cdm": self.cdm is not None,
                    "hsm": self.hsm is not None,
                    "live2d": self.live2d_integration is not None
                }
            }
        
        elif query_type == "config":
            result["config"] = {
                "max_concurrent": self._max_concurrent,
                "max_history_size": self._max_history_size,
                "history_file": str(self._history_file)
            }
        
        return result
    
    # ========== Public API ==========
    
    def register_pre_execution_callback(self, callback: Callable[[ExecutionContext], None]):
        """Register callback to be called before action execution"""
        self._pre_execution_callbacks.append(callback)
    
    def register_post_execution_callback(
        self, 
        callback: Callable[[ExecutionContext, ExecutionResult], None]
    ):
        """Register callback to be called after action execution"""
        self._post_execution_callbacks.append(callback)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            **self._stats,
            "current_queue_size": len(self._priority_queue),
            "executing_count": len(self._executing_actions),
            "completed_count": len(self._completed_actions)
        }
    
    def get_action_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent action execution history"""
        return self._execution_history[-limit:]
    
    def get_feedback_data(self) -> Dict[str, Any]:
        """Get feedback data for learning"""
        return self.feedback_collector.get_learning_data()
    
    async def cancel_action(self, action_id: str) -> bool:
        """Cancel a pending action"""
        # Find in queue
        for i, (priority, aid, item) in enumerate(self._priority_queue):
            if aid == action_id:
                self._priority_queue.pop(i)
                
                # Record as cancelled
                result = ExecutionResult(
                    action_id=action_id,
                    action_type=item["context"].action_type,
                    status=ExecutionResultStatus.CANCELLED,
                    success=False,
                    error_message="Action cancelled by user"
                )
                self._completed_actions[action_id] = result
                return True
        
        return False
    
    def clear_history(self):
        """Clear execution history"""
        self._execution_history.clear()
        self._completed_actions.clear()


# ========== Integration Helpers ==========

class ActionExecutionBridgeFactory:
    """Factory for creating ActionExecutionBridge with common configurations"""
    
    @staticmethod
    def create_basic_bridge(config: Optional[Dict[str, Any]] = None) -> ActionExecutionBridge:
        """Create a basic bridge without external dependencies"""
        return ActionExecutionBridge(config=config)
    
    @staticmethod
    def create_full_bridge(
        orchestrator: Any,
        desktop_pet: Any,
        file_manager: Any,
        download_manager: Any,
        web_search_tool: Any,
        hsm: Any,
        cdm: Any,
        live2d_integration: Any,
        config: Optional[Dict[str, Any]] = None
    ) -> ActionExecutionBridge:
        """Create a fully configured bridge with all dependencies"""
        return ActionExecutionBridge(
            orchestrator=orchestrator,
            desktop_pet=desktop_pet,
            file_manager=file_manager,
            download_manager=download_manager,
            web_search_tool=web_search_tool,
            hsm=hsm,
            cdm=cdm,
            live2d_integration=live2d_integration,
            config=config
        )


# Example usage
if __name__ == "__main__":
    async def demo():
        print("=" * 70)
        print("Angela AI v6.0 - Action Execution Bridge Demo")
        print("动作执行桥接器演示")
        print("=" * 70)
        
        # Create bridge
        bridge = ActionExecutionBridge()
        await bridge.initialize()
        
        print("\n1. Testing initiate_conversation action")
        result = await bridge.execute_action(
            action_type=ActionType.INITIATE_CONVERSATION,
            parameters={"message": "Hello from ActionExecutionBridge!", "emotion": "happy"},
            priority=1
        )
        print(f"   Result: {result.to_dict()}")
        
        print("\n2. Testing express_feeling action")
        result = await bridge.execute_action(
            action_type=ActionType.EXPRESS_FEELING,
            parameters={"emotion": "curious", "intensity": 0.8},
            priority=2
        )
        print(f"   Result: {result.to_dict()}")
        
        print("\n3. Testing system_query action")
        result = await bridge.execute_action(
            action_type=ActionType.SYSTEM_QUERY,
            parameters={"query_type": "health"},
            priority=3
        )
        print(f"   Result: {result.to_dict()}")
        
        print("\n4. Execution Statistics")
        stats = bridge.get_execution_stats()
        print(f"   Stats: {stats}")
        
        print("\n5. Feedback Data")
        feedback = bridge.get_feedback_data()
        print(f"   Feedback: {feedback}")
        
        await bridge.shutdown()
        print("\n" + "=" * 70)
        print("Demo completed successfully!")
        print("=" * 70)
    
    asyncio.run(demo())
