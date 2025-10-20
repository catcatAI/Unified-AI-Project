import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time

# 创建占位符类型和类


class HSPTaskRequestPayload(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class HSPTaskResultPayload(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class HSPMessageEnvelope(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class HSPConnector:
    def register_on_task_result_callback(self, callback):
        pass

    async def send_task_request(self, payload, target_ai_id_or_topic):
        return True


logger: Any = logging.getLogger(__name__)


class CollaborationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CollaborationTask:
    task_id: str
    requester_agent_id: str
    target_agent_id: str
    capability_id: str
    parameters: Dict[str, Any]
    status: CollaborationStatus = CollaborationStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    priority: int = 1  # 新增：任务优先级
    created_time: float = field(default_factory=time.time)  # 新增：任务创建时间
    retry_count: int = 0  # 新增：重试计数
    cache_key: Optional[str] = None  # 新增：缓存键


@dataclass
class CachedTaskResult:
    """缓存的任务结果"""
    result: Dict[str, Any]
    timestamp: float
    expiry_time: float


class AgentCollaborationManager:
    """
    Manages collaboration between different AI agents in the Unified AI Project.
    This class handles task delegation, result aggregation, and inter-agent communication.
    """

    def __init__(self, hsp_connector: HSPConnector) -> None:
        self.hsp_connector = hsp_connector
        self.active_collaborations: Dict[str, CollaborationTask] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.collaboration_lock = asyncio.Lock()
        self.task_queue: List[CollaborationTask] = []  # 新增：任务队列
        self.max_queue_size = 1000  # 新增：最大队列大小
        self.task_cache: Dict[str, CachedTaskResult] = {}  # 新增：任务缓存
        self.cache_expiry_seconds = 300  # 新增：缓存过期时间（5分钟）

        # Register callbacks for task results:
        if self.hsp_connector:
            self.hsp_connector.register_on_task_result_callback(self._handle_task_result)

    async def register_agent_capability(self, agent_id: str, capability_id: str):
        """Register an agent's capability for collaboration."""
        async with self.collaboration_lock:
            if agent_id not in self.agent_capabilities:
                self.agent_capabilities[agent_id] = []

            if capability_id not in self.agent_capabilities[agent_id]:
                self.agent_capabilities[agent_id].append(capability_id)
                logger.info(f"Registered capability '{capability_id}' for agent '{agent_id}'")

    async def find_agent_for_capability(self, capability_id: str) -> Optional[str]:
        """Find an agent that can handle the specified capability."""
        async with self.collaboration_lock:
            for agent_id, capabilities in self.agent_capabilities.items():
                if capability_id in capabilities:
                    return agent_id
            return None

    def _generate_cache_key(self, capability_id: str, parameters: Dict[str, Any]) -> str:
        """生成任务缓存键"""
        # 创建参数的规范化表示
        normalized_params = json.dumps(parameters, sort_keys=True)
        # 生成MD5哈希作为缓存键
        cache_key = hashlib.md5(f"{capability_id}:{normalized_params}".encode()).hexdigest()
        return cache_key

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存的结果"""
        current_time = time.time()
        async with self.collaboration_lock:
            if cache_key in self.task_cache:
                cached_result = self.task_cache[cache_key]
                # 检查是否过期
                if current_time < cached_result.expiry_time:
                    return cached_result.result
                else:
                    # 删除过期的缓存
                    del self.task_cache[cache_key]
        return None

    async def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """缓存任务结果"""
        current_time = time.time()
        expiry_time = current_time + self.cache_expiry_seconds
        cached_result = CachedTaskResult(
            result=result,
            timestamp=current_time,
            expiry_time=expiry_time
        )
        async with self.collaboration_lock:
            self.task_cache[cache_key] = cached_result

    async def delegate_task(self, requester_agent_id: str, target_agent_id: str,
                          capability_id: str, parameters: Dict[str, Any], priority: int = 1, 
                          use_cache: bool = True) -> str:
        """
        Delegate a task from one agent to another.

        Args:
                requester_agent_id: ID of the agent requesting the task
                target_agent_id: ID of the agent to handle the task
                capability_id: The capability needed to handle the task
                parameters: Parameters for the task
                priority: Task priority (1-10, higher is more urgent)
                use_cache: Whether to use caching for this task
        Returns: str Task ID for tracking the collaboration
        """
        # 检查缓存
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(capability_id, parameters)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                # 返回缓存结果（模拟）
                logger.info(f"Using cached result for task with capability '{capability_id}'")
                # 这里应该实际返回缓存结果给请求者
                pass

        task_id = f"collab_task_{int(time.time() * 1000)}_{len(self.active_collaborations) + 1}"

        # Create collaboration task
        collaboration_task = CollaborationTask(
            task_id=task_id,
            requester_agent_id=requester_agent_id,
            target_agent_id=target_agent_id,
            capability_id=capability_id,
            parameters=parameters,
            priority=priority,
            cache_key=cache_key
        )

        # Store the task
        async with self.collaboration_lock:
            self.active_collaborations[task_id] = collaboration_task
            # Add to task queue for priority-based processing
            self._add_task_to_queue(collaboration_task)

        # Send task request via HSP
        task_payload = HSPTaskRequestPayload({
            "request_id": task_id,
            "requester_ai_id": requester_agent_id,
            "target_ai_id": target_agent_id,
            "capability_id_filter": capability_id,
            "parameters": parameters,
            "status": "pending",
            "priority": priority,
            "use_cache": use_cache
        })

        try:
            # Send the task request
            success = await self.hsp_connector.send_task_request(
                payload=task_payload,
                target_ai_id_or_topic=target_agent_id
            )

            if success:
                collaboration_task.status = CollaborationStatus.IN_PROGRESS
                logger.info(f"Delegated task '{task_id}' from '{requester_agent_id}' to '{target_agent_id}' with priority {priority}")
            else:
                collaboration_task.status = CollaborationStatus.FAILED
                collaboration_task.error_message = "Failed to send task request via HSP"
                logger.error(f"Failed to delegate task '{task_id}' from '{requester_agent_id}' to '{target_agent_id}'")

        except Exception as e:
            collaboration_task.status = CollaborationStatus.FAILED
            collaboration_task.error_message = str(e)
            logger.error(f"Exception while delegating task '{task_id}': {e}")

        return task_id

    async def delegate_task_async(self, requester_agent_id: str, target_agent_id: str,
                                capability_id: str, parameters: Dict[str, Any], priority: int = 1) -> asyncio.Future:
        """
        Asynchronously delegate a task from one agent to another.

        Args:
                requester_agent_id: ID of the agent requesting the task
                target_agent_id: ID of the agent to handle the task
                capability_id: The capability needed to handle the task
                parameters: Parameters for the task
                priority: Task priority (1-10, higher is more urgent)
        Returns: asyncio.Future for tracking the collaboration
        """
        # Create a future for async result
        future = asyncio.Future()
        
        # Delegate the task
        task_id = await self.delegate_task(requester_agent_id, target_agent_id, capability_id, parameters, priority)
        
        # Store the future for later completion
        async with self.collaboration_lock:
            if task_id in self.active_collaborations:
                self.active_collaborations[task_id].result = future
        
        return future

    async def delegate_tasks_batch(self, requester_agent_id: str, 
                                 task_definitions: List[Dict[str, Any]]) -> List[str]:
        """
        Delegate multiple tasks in batch.

        Args:
                requester_agent_id: ID of the agent requesting the tasks
                task_definitions: List of task definitions with target_agent_id, capability_id, parameters, and priority
        Returns: List of task IDs
        """
        task_ids = []
        
        # Create all tasks first
        tasks_to_create = []
        for task_def in task_definitions:
            target_agent_id = task_def.get("target_agent_id")
            capability_id = task_def.get("capability_id")
            parameters = task_def.get("parameters", {})
            priority = task_def.get("priority", 1)
            
            task_id = f"collab_task_{int(time.time() * 1000)}_{len(self.active_collaborations) + len(tasks_to_create) + 1}"
            
            # Create collaboration task
            collaboration_task = CollaborationTask(
                task_id=task_id,
                requester_agent_id=requester_agent_id,
                target_agent_id=target_agent_id,
                capability_id=capability_id,
                parameters=parameters,
                priority=priority
            )
            
            tasks_to_create.append((task_id, collaboration_task, task_def))
        
        # Store all tasks atomically
        async with self.collaboration_lock:
            for task_id, collaboration_task, task_def in tasks_to_create:
                self.active_collaborations[task_id] = collaboration_task
                self._add_task_to_queue(collaboration_task)
                task_ids.append(task_id)
        
        # Send all task requests
        for task_id, collaboration_task, task_def in tasks_to_create:
            target_agent_id = task_def.get("target_agent_id")
            capability_id = task_def.get("capability_id")
            parameters = task_def.get("parameters", {})
            priority = task_def.get("priority", 1)
            
            task_payload = HSPTaskRequestPayload({
                "request_id": task_id,
                "requester_ai_id": requester_agent_id,
                "target_ai_id": target_agent_id,
                "capability_id_filter": capability_id,
                "parameters": parameters,
                "status": "pending",
                "priority": priority
            })

            try:
                # Send the task request
                success = await self.hsp_connector.send_task_request(
                    payload=task_payload,
                    target_ai_id_or_topic=target_agent_id
                )

                if success:
                    collaboration_task.status = CollaborationStatus.IN_PROGRESS
                    logger.info(f"Delegated batch task '{task_id}' from '{requester_agent_id}' to '{target_agent_id}' with priority {priority}")
                else:
                    collaboration_task.status = CollaborationStatus.FAILED
                    collaboration_task.error_message = "Failed to send task request via HSP"
                    logger.error(f"Failed to delegate batch task '{task_id}' from '{requester_agent_id}' to '{target_agent_id}'")

            except Exception as e:
                collaboration_task.status = CollaborationStatus.FAILED
                collaboration_task.error_message = str(e)
                logger.error(f"Exception while delegating batch task '{task_id}': {e}")
        
        return task_ids

    def _add_task_to_queue(self, task: CollaborationTask):
        """Add a task to the priority queue."""
        # Insert task in priority order (higher priority first)
        inserted = False
        for i, existing_task in enumerate(self.task_queue):
            if task.priority > existing_task.priority:
                self.task_queue.insert(i, task)
                inserted = True
                break
        
        if not inserted:
            self.task_queue.append(task)

    async def _handle_task_result(self, result_payload: HSPTaskResultPayload,
                                 sender_ai_id: str, envelope: HSPMessageEnvelope):
        """Handle task results from collaborating agents."""
        task_id = result_payload.get("request_id", "")

        async with self.collaboration_lock:
            if task_id in self.active_collaborations:
                collaboration_task = self.active_collaborations[task_id]

                if result_payload.get("status") == "success":
                    collaboration_task.status = CollaborationStatus.COMPLETED
                    collaboration_task.result = result_payload.get("payload", {})
                    logger.info(f"Task '{task_id}' completed successfully")
                    
                    # 缓存结果（如果有缓存键）
                    if collaboration_task.cache_key:
                        await self._cache_result(collaboration_task.cache_key, collaboration_task.result)
                    
                    # Remove from queue
                    self.task_queue = [t for t in self.task_queue if t.task_id != task_id]
                else:
                    collaboration_task.status = CollaborationStatus.FAILED
                    collaboration_task.error_message = result_payload.get("error_details", {}).get("error_message", "Unknown error")
                    logger.error(f"Task '{task_id}' failed: {collaboration_task.error_message}")
                    # Remove from queue
                    self.task_queue = [t for t in self.task_queue if t.task_id != task_id]

    async def get_collaboration_status(self, task_id: str) -> Optional[CollaborationTask]:
        """Get the status of a collaboration task."""
        async with self.collaboration_lock:
            return self.active_collaborations.get(task_id)

    async def get_task_queue_status(self) -> Dict[str, Any]:
        """Get the status of the task queue."""
        async with self.collaboration_lock:
            priority_counts = {}
            for task in self.task_queue:
                priority = task.priority
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            return {
                "queue_length": len(self.task_queue),
                "max_queue_size": self.max_queue_size,
                "priority_counts": priority_counts
            }

    async def get_cache_status(self) -> Dict[str, Any]:
        """Get the status of the task cache."""
        async with self.collaboration_lock:
            current_time = time.time()
            # 计算未过期的缓存项数量
            active_cache_count = sum(1 for cached_result in self.task_cache.values() 
                                   if current_time < cached_result.expiry_time)
            
            return {
                "total_cache_items": len(self.task_cache),
                "active_cache_items": active_cache_count,
                "cache_expiry_seconds": self.cache_expiry_seconds
            }

    async def clear_expired_cache(self) -> int:
        """清理过期的缓存项，返回清理的数量"""
        current_time = time.time()
        cleaned_count = 0
        
        async with self.collaboration_lock:
            expired_keys = [
                key for key, cached_result in self.task_cache.items()
                if current_time >= cached_result.expiry_time
            ]
            
            for key in expired_keys:
                del self.task_cache[key]
                cleaned_count += 1
        
        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} expired cache items")
        
        return cleaned_count

    async def clear_cache(self):
        """清空所有缓存"""
        async with self.collaboration_lock:
            self.task_cache.clear()
        logger.info("Cache cleared")

    async def orchestrate_multi_agent_task(self, requester_agent_id: str,
                                         task_sequence: List[Dict[str, Any]]):
        """
        Orchestrate a sequence of tasks across multiple agents.

        Args:
                requester_agent_id: ID of the agent requesting the task sequence
                task_sequence: List of task definitions with capability_id and parameters
        Returns: Dict Result of the orchestrated task sequence
        """
        results = {}

        for i, task_def in enumerate(task_sequence):
            capability_id = task_def["capability_id"]
            parameters = task_def["parameters"]

            # Replace placeholders with previous results:
            for key, value in parameters.items():
                if isinstance(value, str) and "<output_of_task_" in value:
                    task_index = int(value.split("<output_of_task_")[1].split(">")[0])
                    if task_index in results:
                        parameters[key] = results[task_index]

            # Find an agent for this capability:
            target_agent_id = await self.find_agent_for_capability(capability_id)

            if not target_agent_id:
                logger.error(f"No agent found for capability '{capability_id}'")
                return {
                    "status": "failed",
                    "error": f"No agent found for capability '{capability_id}'"
                }

            # Delegate the task
            task_id = await self.delegate_task(
                requester_agent_id=requester_agent_id,
                target_agent_id=target_agent_id,
                capability_id=capability_id,
                parameters=parameters,
                priority=task_def.get("priority", 1)
            )

            # Wait for task completion (with timeout):
            timeout = task_def.get("timeout", 30)
            start_time = asyncio.get_event_loop().time()

            while asyncio.get_event_loop().time() - start_time < timeout:
                task_status = await self.get_collaboration_status(task_id)
                if task_status and task_status.status in [CollaborationStatus.COMPLETED, CollaborationStatus.FAILED]:
                    break
                await asyncio.sleep(0.5)

            # Check final status
            task_status = await self.get_collaboration_status(task_id)
            if task_status and task_status.status == CollaborationStatus.COMPLETED:
                results[i] = task_status.result
            else:
                error_msg = task_status.error_message if task_status else "Task timed out"
                logger.error(f"Task {i} failed: {error_msg}")
                return {
                    "status": "failed",
                    "error": f"Task {i} failed: {error_msg}"
                }

        return {
            "status": "success",
            "results": results
        }

    async def shutdown(self):
        """Shutdown the collaboration manager and clean up resources."""
        logger.info("Shutting down AgentCollaborationManager")
        # In a more complex implementation, we might want to cancel pending tasks
        # or notify other agents about shutdown