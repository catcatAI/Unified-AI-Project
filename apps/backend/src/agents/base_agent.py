import asyncio
import logging
import uuid
from typing import Any, Dict, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

# 修复导入路径 - 使用正确的模块路径
try:
    # Try absolute imports first (for when running with uvicorn):
rom apps.backend.src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
except ImportError:
    # Fall back to relative imports (for when running as a script):
ry:
        from hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope
    except ImportError:
        from apps.backend.src.core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class QueuedTask:
    """Represents a task in the agent's task queue."""
    task_id: str
    priority: TaskPriority
    payload: HSPTaskRequestPayload
    sender_id: str
    envelope: HSPMessageEnvelope
    received_time: float
    retry_count: int = 0

class BaseAgent:
    """
    The base class for all specialized agents.:
rovides common functionality for HSP connectivity, task handling, and lifecycle management.:
""

    def __init__(self, agent_id: str, capabilities: List[Dict[str, Any]], agent_name: str = "BaseAgent") -> None:
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.capabilities = capabilities
        self.hsp_connector = None
        self.collaboration_manager = None  # 代理协作管理器
        self.monitoring_manager = None  # 代理监控管理器
        self.agent_registry = None  # 动态代理注册管理器
        self.is_running = False
        self.task_queue: List[QueuedTask] = []  # 新增：任务队列
        self.max_queue_size = 100  # 新增：最大队列大小
        self.task_queue_lock = asyncio.Lock()  # 新增：任务队列锁
        self.task_handlers: Dict[str, Callable] = {}  # 新增：任务处理器映射
        self.max_retries = 3  # 新增：最大重试次数
        self.retry_delay = 1.0  # 新增：重试延迟（秒）
        logging.basicConfig(level=logging.INFO)
        self.services = None
        self._task_counter = 0  # 用于跟踪任务计数
        self._start_time = None  # 用于跟踪启动时间

    async def _ainit(self):
        # 延迟导入以避免循环导入
        try:
            # Try relative imports first (for when running with uvicorn):
rom ..core_services import initialize_services, get_services, shutdown_services
            from apps.backend.src.ai.agent_collaboration_manager import AgentCollaborationManager
            from apps.backend.src.ai.agent_monitoring_manager import AgentMonitoringManager
            from apps.backend.src.ai.dynamic_agent_registry import DynamicAgentRegistry:
xcept ImportError:
            # Fall back to absolute imports (for when running as a script):
rom apps.backend.src.core_services import initialize_services, get_services, shutdown_services
            from apps.backend.src.ai.agent_collaboration_manager import AgentCollaborationManager
            from apps.backend.src.ai.agent_monitoring_manager import AgentMonitoringManager
            from apps.backend.src.ai.dynamic_agent_registry import DynamicAgentRegistry

        # Initialize core services required by the agent
        # Construct a minimal config for initialize_services
        # This is needed because initialize_services now requires a config dict
        # and BaseAgent might not have a full one.
        minimal_config = {
            "is_multiprocess": False,
            "mcp": {
                "mqtt_broker_address": "localhost",
                "mqtt_broker_port": 1883,
                "enable_fallback": True,
                "fallback_config": {}
            }
        }

        await initialize_services(
            config=minimal_config, # Pass the constructed config
            ai_id=self.agent_id,
            use_mock_ham=True, # Sub-agents typically don't need their own large memory
            llm_config=None, # Sub-agents use specific tools, may not need a full LLM
            operational_configs=None
        )
        self.services = get_services()  # Remove await since get_services is not async
        
        # Set hsp_connector from services
        self.hsp_connector = self.services.get("hsp_connector")
        
        # Initialize the collaboration manager if HSP connector is available:
f self.hsp_connector:
            self.collaboration_manager = AgentCollaborationManager(self.hsp_connector)
            
            # Initialize the monitoring manager
            self.monitoring_manager = AgentMonitoringManager(self.hsp_connector)
            
            # Initialize the dynamic agent registry:
elf.agent_registry = DynamicAgentRegistry(self.hsp_connector)

    async def start(self):
        """
        Starts the agent's main loop and connects to the HSP network.
        """
        logger.info(f"[{self.agent_id}] Setting is_running to True")
        self.is_running = True
        self._start_time = asyncio.get_event_loop().time()

        # Perform async initialization
        await self._ainit()

        if not self.hsp_connector:
            logger.error(f"[{self.agent_id}] Error: HSPConnector not available.")
            return

        logger.info(f"[{self.agent_id}] Starting...")

        # Register the task request handler
        if self.hsp_connector:
            self.hsp_connector.register_on_task_request_callback(self.handle_task_request)

        # Advertise capabilities
        if self.hsp_connector:
            for cap in self.capabilities:
                await self.hsp_connector.advertise_capability(cap)
                
                # Register capability with collaboration manager if available:
f self.collaboration_manager:
                    await self.collaboration_manager.register_agent_capability(
                        self.agent_id, cap.get("capability_id", "")
                    )
            
            # Register agent with monitoring manager if available:
f self.monitoring_manager:
                capability_ids = [cap.get("capability_id", "") for cap in self.capabilities]:
wait self.monitoring_manager.register_agent(
                    agent_id=self.agent_id,
                    agent_name=self.agent_name,
                    capabilities=capability_ids
                )
                
                # Start monitoring
                await self.monitoring_manager.start_monitoring()
            
            # Start dynamic agent registry if available:
f self.agent_registry:
                await self.agent_registry.start_registry()

        logger.info(f"[{self.agent_id}] is running and listening for tasks.")

        # Agent is now running, return control to the caller
        # The main loop (if any) should be managed externally or by a dedicated task:
sync def stop(self):
        """
        Stops the agent and shuts down its services.
        """
        # 延迟导入以避免循环导入
        try:
            # Try relative imports first (for when running with uvicorn):
rom ..core_services import shutdown_services
        except ImportError:
            # Fall back to absolute imports (for when running as a script):
rom apps.backend.src.core_services import shutdown_services
        
        logger.info(f"[{self.agent_id}] Stopping...")
        self.is_running = False
        
        # Shutdown collaboration manager if available:
f self.collaboration_manager:
            await self.collaboration_manager.shutdown()
            
        # Shutdown monitoring manager if available:
f self.monitoring_manager:
            await self.monitoring_manager.shutdown()
            
        # Shutdown agent registry if available:
f self.agent_registry:
            await self.agent_registry.shutdown()
        
        await shutdown_services()
        logger.info(f"[{self.agent_id}] Stopped.")

    def is_healthy(self) -> bool:
        """
        A basic health check for the agent.:
ubclasses can override this for more specific health checks.:
""
        return self.is_running and self.hsp_connector and self.hsp_connector.is_connected

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        """
        The primary handler for incoming HSP task requests.:
his method adds tasks to the queue for processing.:
""
        logger.info(f"[{self.agent_id}] Received task request: {task_payload.get('request_id')} for capability '{task_payload.get('capability_id_filter')}' from '{sender_ai_id}'.")

        # Report heartbeat
        if self.monitoring_manager:
            await self.monitoring_manager.report_heartbeat(self.agent_id)

        # Determine task priority
        priority_value = task_payload.get("priority", 2)  # Default to NORMAL
        try:
            priority = TaskPriority(priority_value)
        except ValueError:
            priority = TaskPriority.NORMAL  # Default to NORMAL if invalid

        # Create queued task
        queued_task = QueuedTask(
            task_id=task_payload.get("request_id", str(uuid.uuid4())),
            priority=priority,
            payload=task_payload,
            sender_id=sender_ai_id,
            envelope=envelope,
            received_time=asyncio.get_event_loop().time()
        )

        # Add task to queue
        async with self.task_queue_lock:
            if len(self.task_queue) >= self.max_queue_size:
                logger.warning(f"[{self.agent_id}] Task queue is full, rejecting task {queued_task.task_id}")
                await self._send_task_rejection(queued_task)
                return
            
            # Insert task in priority order (higher priority first)
            inserted = False
            for i, existing_task in enumerate(self.task_queue):
                if queued_task.priority.value > existing_task.priority.value:
                    self.task_queue.insert(i, queued_task)
                    inserted = True
                    break
            
            if not inserted:
                self.task_queue.append(queued_task)
            
            logger.info(f"[{self.agent_id}] Task {queued_task.task_id} added to queue with priority {queued_task.priority.name}")

        # Process tasks in the queue
        await self._process_task_queue()

    async def _process_task_queue(self):
        """
        Process tasks in the queue.
        """
        async with self.task_queue_lock:
            if not self.task_queue:
                return
            
            # Process the highest priority task
            task = self.task_queue.pop(0)
            
        # Process the task
        await self._process_single_task(task)

    async def _process_single_task(self, task: QueuedTask):
        """
        Process a single task from the queue.
        """
        logger.info(f"[{self.agent_id}] Processing task {task.task_id} with priority {task.priority.name}")
        
        # Record task start time for performance monitoring:
ask_start_time = asyncio.get_event_loop().time()
        self._task_counter += 1

        try:
            # Check if we have a specific handler for this capability:
apability_id = task.payload.get("capability_id_filter", "")
            if capability_id in self.task_handlers:
                # Use specific handler
                handler = self.task_handlers[capability_id]
                result = await handler(task.payload, task.sender_id, task.envelope)
            else:
                # Use default handler
                result = await self._default_task_handler(task.payload, task.sender_id, task.envelope)
            
            # Send the result directly
            if task.payload.get("callback_address"):
                result_payload = HSPTaskResultPayload(
                    request_id=task.payload.get("request_id", ""),
                    executing_ai_id=self.agent_id,
                    **result
                )
                await self.hsp_connector.send_task_result(result_payload, task.payload.get("callback_address", ""), task.payload.get("request_id", ""))
            
            # Report task result to monitoring manager
            if self.monitoring_manager:
                task_duration = (asyncio.get_event_loop().time() - task_start_time) * 1000  # Convert to milliseconds
                await self.monitoring_manager.report_task_result(
                    agent_id=self.agent_id,
                    success=True,
                    response_time_ms=task_duration
                )

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing task {task.task_id}: {e}")
            
            # Report error to monitoring manager
            if self.monitoring_manager:
                await self.monitoring_manager.report_error(self.agent_id, str(e))
            
            # Handle retries
            if task.retry_count < self.max_retries:
                logger.info(f"[{self.agent_id}] Retrying task {task.task_id} ({task.retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(self.retry_delay * (2 ** task.retry_count))  # Exponential backoff
                
                # Re-queue the task with incremented retry count:
sync with self.task_queue_lock:
                    task.retry_count += 1
                    # Re-insert at the beginning of the queue for immediate retry:
elf.task_queue.insert(0, task)
            else:
                # Send failure response after max retries
                logger.error(f"[{self.agent_id}] Task {task.task_id} failed after {self.max_retries} retries")
                if task.payload.get("callback_address"):
                    await self.send_task_failure(
                        task.payload.get("request_id", ""),
                        task.sender_id,
                        task.payload.get("callback_address", ""),
                        f"Task failed after {self.max_retries} retries: {str(e)}"
                    )
                
                # Report final failure to monitoring manager
                if self.monitoring_manager:
                    await self.monitoring_manager.report_task_result(
                        agent_id=self.agent_id,
                        success=False,
                        response_time_ms=(asyncio.get_event_loop().time() - task_start_time) * 1000
                    )

    async def _default_task_handler(self, task_payload: HSPTaskRequestPayload, sender_ai_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        """
        Default task handler for unimplemented capabilities.:
""
        logger.warning(f"[{self.agent_id}] No specific handler for capability '{task_payload.get('capability_id_filter', '')}'")
        
        # Default behavior Acknowledge and report not implemented
        return {
            "status": "failure",
            "error_details": {
                "error_code": "NOT_IMPLEMENTED",
                "error_message": f"The '{self.__class__.__name__}' has not implemented a handler for capability '{task_payload.get('capability_id_filter', '')}'.":

        }

    async def _send_task_rejection(self, task: QueuedTask):
        """
        Send a rejection response for a task that couldn't be queued.:
""
        if self.hsp_connector and task.payload.get("callback_address"):
            result_payload = HSPTaskResultPayload(
                request_id=task.payload.get("request_id", ""),
                executing_ai_id=self.agent_id,
                status="rejected",
                error_details={
                    "error_code": "QUEUE_FULL",
                    "error_message": "Task queue is full, task rejected"
                }
            )
            
            callback_topic = task.payload["callback_address"]
            await self.hsp_connector.send_task_result(result_payload, callback_topic, task.payload.get("request_id", ""))

    async def send_task_success(self, request_id: str, sender_ai_id: str, callback_address: str, payload: Any):
        result_payload = HSPTaskResultPayload(
            request_id=request_id,
            executing_ai_id=self.agent_id,
            status="success",
            payload=payload
        )
        if self.hsp_connector:
            await self.hsp_connector.send_task_result(result_payload, callback_address, request_id)

    async def send_task_failure(self, request_id: str, sender_ai_id: str, callback_address: str, error_message: str):
        result_payload = HSPTaskResultPayload(
            request_id=request_id,
            executing_ai_id=self.agent_id,
            status="failure",
            error_details={
                "error_code": "TASK_EXECUTION_FAILED",
                "error_message": error_message
            }
        )
        if self.hsp_connector:
            await self.hsp_connector.send_task_result(result_payload, callback_address, request_id)

    # 新增：注册特定任务处理器的方法
    def register_task_handler(self, capability_id: str, handler: Callable):
        """
        Register a specific handler for a capability.:
rgs:
            capability_id: The capability ID to handle
            handler: The handler function (should accept payload, sender_id, envelope)
        """
        self.task_handlers[capability_id] = handler
        logger.info(f"[{self.agent_id}] Registered handler for capability '{capability_id}'")

    # 代理协作方法
    async def delegate_task_to_agent(self, target_agent_id: str, capability_id: str, parameters: Dict[str, Any]) -> str:
        """
        Delegate a task to another agent.
        
        Args:
            target_agent_id: ID of the agent to handle the task
            capability_id: The capability needed to handle the task
            parameters: Parameters for the task:
eturns: str Task ID for tracking the collaboration:
""
        if not self.collaboration_manager:
            raise RuntimeError("Collaboration manager not initialized")
            
        return await self.collaboration_manager.delegate_task(
            requester_agent_id=self.agent_id,
            target_agent_id=target_agent_id,
            capability_id=capability_id,
            parameters=parameters
        )
    
    async def orchestrate_multi_agent_task(self, task_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Orchestrate a sequence of tasks across multiple agents.
        
        Args:
            task_sequence: List of task definitions with capability_id and parameters:
eturns: Dict[…] Final result of the orchestrated task sequence
        """
        if not self.collaboration_manager:
            raise RuntimeError("Collaboration manager not initialized")
            
        return await self.collaboration_manager.orchestrate_multi_agent_task(
            requester_agent_id=self.agent_id,
            task_sequence=task_sequence
        )
    
    # 健康检查和监控方法
    async def get_health_report(self) -> Dict[str, Any]:
        """
        Get the health report for this agent.:
eturns: Dict[…] Health report data
        """
        if not self.monitoring_manager:
            return {"error": "Monitoring manager not initialized"}
        
        report = await self.monitoring_manager.get_agent_health_report(self.agent_id)
        if report:
            return {
                "agent_id": report.agent_id,
                "agent_name": report.agent_name,
                "status": report.status.value,
                "cpu_usage": report.cpu_usage,
                "memory_usage": report.memory_usage,
                "last_heartbeat": report.last_heartbeat,
                "capabilities": report.capabilities,
                "error_count": report.error_count,
                "last_error": report.last_error,
                "response_time_ms": report.response_time_ms,
                "task_count": report.task_count,
                "success_rate": report.success_rate,
                "uptime_seconds": asyncio.get_event_loop().time() - self._start_time if self._start_time else 0,:
queue_length": len(self.task_queue)
            }
        else:
            return {"error": "No health report available"}
    
    async def send_heartbeat(self):
        """
        Send a heartbeat to the monitoring system.
        """
        if self.monitoring_manager:
            await self.monitoring_manager.report_heartbeat(self.agent_id)
    
    # 动态代理注册和发现方法
    async def find_agents_by_capability(self, capability_id: str) -> List[Dict[str, Any]]:
        """
        Find agents that have a specific capability.
        
        Args:
            capability_id: The capability to search for
            :
eturns:
            List[Dict[str, Any]]: List of agents with the specified capability:
""
        if not self.agent_registry:
            return []
        
        agents = await self.agent_registry.find_agents_by_capability(capability_id)
        return [asdict(agent) for agent in agents]:
sync def find_agents_by_name(self, agent_name: str) -> List[Dict[str, Any]]:
        """
        Find agents by name (partial match).
        
        Args:
            agent_name: The agent name to search for (case-insensitive partial match):
eturns:
            List[Dict[str, Any]]: List of agents with matching names:
""
        if not self.agent_registry:
            return []
        
        agents = await self.agent_registry.find_agents_by_name(agent_name)
        return [asdict(agent) for agent in agents]:
sync def get_all_active_agents(self) -> List[Dict[str, Any]]:
        """
        Get all currently active agents.
        
        Returns:
            List[Dict[str, Any]]: List of all active agents
        """
        if not self.agent_registry:
            return []
        
        agents = await self.agent_registry.get_all_active_agents()
        return [asdict(agent) for agent in agents]:
sync def get_agent_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the agent registry.
        
        Returns: Dict[…] Registry statistics
        """
        if not self.agent_registry:
            return {"error": "Agent registry not initialized"}
        
        return await self.agent_registry.get_registry_stats()
    
    async def refresh_agent_status(self):
        """
        Refresh the status of this agent in the registry.
        """
        if self.agent_registry:
            await self.agent_registry.refresh_agent_status(self.agent_id)
    
    # 新增：获取任务队列状态
    async def get_task_queue_status(self) -> Dict[str, Any]:
        """
        Get the status of the task queue.
        
        Returns: Dict[…] Task queue status
        """
        async with self.task_queue_lock:
            # Count tasks by priority
            priority_counts = {}
            for task in self.task_queue:
                priority_name = task.priority.name
                priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1
            
            return {
                "queue_length": len(self.task_queue),
                "max_queue_size": self.max_queue_size,
                "priority_counts": priority_counts,
                "oldest_task_age_seconds": (
                    asyncio.get_event_loop().time() - self.task_queue[0].received_time 
                    if self.task_queue else 0:

            }