"""
Base class for all specialized agents in the Unified AI Project.

Provides common functionality for HSP connectivity, task handling, and
lifecycle management.
"""

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'uuid' not found
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Assuming types_fixed is the correct, refactored types module
from .....core.hsp.types_fixed import

logger = logging.getLogger(__name__)

class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
在类定义前添加空行
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
    The base class for all specialized agents.
    Provides common functionality for HSP connectivity, task handling,
    and lifecycle management.
    """

    def __init__(self, agent_id: str, capabilities: List[Dict[str, Any]] = None,
    agent_name: str = "BaseAgent", alignment_enabled: bool = False) -> None:
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.hsp_connector: Optional[Any] = None
        self.collaboration_manager: Optional[Any] = None
        self.monitoring_manager: Optional[Any] = None
        self.agent_registry: Optional[Any] = None
        self.is_running = False
        self.task_queue: List[QueuedTask] = []
        self.max_queue_size = 100
        self.task_queue_lock: Optional[asyncio.Lock] = None
        self.task_handlers: Dict[str, Callable] = {}
        self.max_retries = 3
        self.retry_delay = 1.0
        logging.basicConfig(level = logging.INFO)
        self.services: Optional[Any] = None
        self._task_counter = 0
        self._start_time: Optional[float] = None
        self._initialized = False
        self.alignment_enabled = alignment_enabled
        self.alignment_system: Optional[Any] = None
        self.initialize_basic()

    def initialize_basic(self):
        """Basic synchronous initialization to avoid complex dependencies."""
        if self._initialized:
            return
        self.task_queue_lock = asyncio.Lock()
        self._initialized = True
        logger.info(f"[{self.agent_id}] BaseAgent basic initialization complete.")

    async def initialize_full(self):
        """Full asynchronous initialization including all services."""
        if self._initialized and self.hsp_connector: # Avoid re - init:
            return

        try:
from .....core.hsp.connector import
from ....ai.agent_collaboration_manager import
from ....ai.agent_monitoring_manager import
from ....ai.dynamic_agent_registry import

            self.hsp_connector = HSPConnector()
                broker_address = "localhost",
                broker_port = 1883,
                client_id = self.agent_id
(            )
            self.collaboration_manager = AgentCollaborationManager(self.hsp_connector)
            self.monitoring_manager = AgentMonitoringManager(self.hsp_connector)
            self.agent_registry = DynamicAgentRegistry(self.hsp_connector)
            self._initialized = True
            logger.info(f"[{self.agent_id}] BaseAgent full initialization complete.")
        except Exception as e:
            logger.warning(f"[{self.agent_id}] Full initialization failed,
    using basic mode: {e}")
            self.initialize_basic()

    async def start(self):
        """Starts the agent's main loop and connects to the HSP network."""
        if self.is_running:
            return
            
        logger.info(f"[{self.agent_id}] Setting is_running to True")
        self.is_running = True
        self._start_time = asyncio.get_event_loop().time()

        await self.initialize_full()

        if not self.hsp_connector:
            logger.error(f"[{self.agent_id}] Error: HSPConnector not available.")
            self.is_running = False
            return

        logger.info(f"[{self.agent_id}] Starting HSP connection...")
        self.hsp_connector.register_on_task_request_callback(self.handle_task_request)

        for cap in self.capabilities:
            await self.hsp_connector.advertise_capability(cap)

        logger.info(f"[{self.agent_id}] is running and listening for tasks.")

    async def stop(self):
        """Stops the agent and shuts down its services."""
        logger.info(f"[{self.agent_id}] Stopping...")
        self.is_running = False
        if self.hsp_connector:
            await self.hsp_connector.disconnect()
        logger.info(f"[{self.agent_id}] Stopped.")

    def is_healthy(self) -> bool:
        """A basic health check for the agent."""
        return self.is_running and self.hsp_connector is not None and \
    self.hsp_connector.is_connected()

    async def handle_task_request(self, task_payload: HSPTaskRequestPayload,
    sender_ai_id: str, envelope: HSPMessageEnvelope):
        """The primary handler for incoming HSP task requests."""
        request_id = task_payload.get("request_id", str(uuid.uuid4()))
        capability_id = task_payload.get('capability_id_filter', '')
        logger.info(f"[{self.agent_id}] Received task request {request_id} for capabilit\
    \
    y '{capability_id}' from '{sender_ai_id}'.")

        try:
            priority = TaskPriority(task_payload.get("priority", 2))
        except ValueError:
            priority = TaskPriority.NORMAL

        queued_task = QueuedTask()
            task_id = request_id,
            priority = priority,
            payload = task_payload,
            sender_id = sender_ai_id,
            envelope = envelope,
            received_time = asyncio.get_event_loop().time()
(        )

        async with self.task_queue_lock:
            if len(self.task_queue) >= self.max_queue_size:
                logger.warning(f"[{self.agent_id}] Task queue is full,
    rejecting task {queued_task.task_id}")
                await self._send_task_rejection(queued_task)
                return
            
            # Simple append, priority can be handled in processing
            self.task_queue.append(queued_task)
            self.task_queue.sort(key = lambda t: t.priority.value, reverse = True)
            logger.info(f"[{self.agent_id}] Task {queued_task.task_id} added to queue wi\
    \
    th priority {queued_task.priority.name}")

        asyncio.create_task(self._process_task_queue())

    async def _process_task_queue(self):
        """Processes tasks from the queue one by one."""
        if not self.task_queue:
            return

        async with self.task_queue_lock:
            if not self.task_queue: # Double check after acquiring lock:
                return
            task = self.task_queue.pop(0)
        
        await self._process_single_task(task)

    async def _process_single_task(self, task: QueuedTask):
        """Processes a single task."""
        logger.info(f"[{self.agent_id}] Processing task {task.task_id} with priority {ta\
    \
    sk.priority.name}")
        task_start_time = asyncio.get_event_loop().time()
        self._task_counter += 1

        try:
            capability_id = task.payload.get("capability_id_filter", "")
            handler = self.task_handlers.get(capability_id, self._default_task_handler)
            result = await handler(task.payload, task.sender_id, task.envelope)

            if task.payload.get("callback_address") and self.hsp_connector:
                result_payload = HSPTaskResultPayload()
                    request_id = task.task_id,
                    executing_ai_id = self.agent_id,
                    * * result
(                )
                await self.hsp_connector.send_task_result(result_payload,
    task.payload["callback_address"], task.task_id)

        except Exception as e:
            logger.error(f"[{self.agent_id}] Error processing task {task.task_id}: {e}")
            if task.retry_count < self.max_retries:
                logger.info(f"[{self.agent_id}] Retrying task {task.task_id} ({task.retr\
    y_count + 1} / {self.max_retries})")
                await asyncio.sleep(self.retry_delay * (2 ** task.retry_count))
                task.retry_count += 1
                async with self.task_queue_lock:
                    self.task_queue.insert(0, task)
            else:
                logger.error(f"[{self.agent_id}] Task {task.task_id} failed after {self.\
    \
    max_retries} retries.")
                if task.payload.get("callback_address") and self.hsp_connector:
                    await self.send_task_failure()
                        task.task_id,
                        task.sender_id,
                        task.payload["callback_address"],
                        f"Task failed after {self.max_retries} retries: {str(e)}"
(                    )

    async def _default_task_handler(self, task_payload: HSPTaskRequestPayload,
    sender_ai_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        """Default task handler for unimplemented capabilities."""
        capability_id = task_payload.get('capability_id_filter', '')
        logger.warning(f"[{self.agent_id}] No specific handler for capability '{capabili\
    \
    ty_id}'")
        return {}
            "status": "failure",
            "error_details": {}
                "error_code": "NOT_IMPLEMENTED",
                "error_message": f"The '{self.__class__.__name__}' has not implemented a\
    \
    handler for capability '{capability_id}'."
{            }
{        }

    async def _send_task_rejection(self, task: QueuedTask):
        """Sends a rejection response for a task that couldn't be queued."""
        if self.hsp_connector and task.payload.get("callback_address"):
            result_payload = HSPTaskResultPayload()
                request_id = task.task_id,
                executing_ai_id = self.agent_id,
                status = "rejected",
                error_details = {}
                    "error_code": "QUEUE_FULL",
                    "error_message": "Task queue is full, task rejected"
{                }
(            )
            await self.hsp_connector.send_task_result(result_payload,
    task.payload["callback_address"], task.task_id)

    def register_task_handler(self, capability_id: str, handler: Callable):
        """Register a specific handler for a capability."""
        self.task_handlers[capability_id] = handler
        logger.info(f"[{self.agent_id}] Registered handler for capability '{capability_i\
    \
    d}'")
