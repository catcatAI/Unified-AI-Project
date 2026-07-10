"""

Base class for all specialized agents in the Unified AI Project.

Provides common functionality for HSP connectivity, task handling, and
lifecycle management.
"""

from core.utils import safe_error

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import asyncio
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from core.hsp.types import HSPMessageEnvelope, HSPTaskRequestPayload, HSPTaskResultPayload
from core.system.config.magic_numbers import cache_value, loop_sleep, retry_value

logger = logging.getLogger(__name__)


# =============================================================================
# ANGELA-MATRIX: [L1] [αβγδ] [A] L0
# =============================================================================
#
# 职责: 标准化错误处理和异常分类
# 维度: 涉及所有维度，提供统一的错误处理框架
# 安全: 使用 Key A (后端控制) 进行安全错误分类
# 成熟度: L1 等级可以理解错误处理的基础概念
# =============================================================================

class AgentError(Exception):
    """Base exception for all agent-related errors."""
    
    def __init__(self, message: str, agent_id: str = None, error_type: str = None):
        super().__init__(message)
        self.agent_id = agent_id
        self.error_type = error_type
        self.timestamp = datetime.now().isoformat()
        self.correlation_id = str(uuid.uuid4())


class TaskProcessingError(AgentError):
    """Error during task processing."""
    pass


class ConnectionError(AgentError):
    """Error in HSP connection."""
    pass


class InitializationError(AgentError):
    """Error during agent initialization."""
    pass


class ConfigurationError(AgentError):
    """Error during configuration loading."""
    pass


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
    The base class for all specialized agents.
    Provides common functionality for HSP connectivity, task handling,
    and lifecycle management.
    """

    def __init__(
        self,
        agent_id: str,
        capabilities: list[dict[str, Any]] = None,
        agent_name: str = "BaseAgent",
        alignment_enabled: bool = False,
    ) -> None:
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.capabilities = capabilities or []
        self.hsp_connector: Optional[Any] = None
        self.collaboration_manager: Optional[Any] = None
        self.monitoring_manager: Optional[Any] = None
        self.agent_registry: Optional[Any] = None
        self.is_running = False
        self.task_queue: list[QueuedTask] = []
        self.max_queue_size = cache_value("agent_queue_size", 100)
        self.task_queue_lock: Optional[asyncio.Lock] = None
        self.task_handlers: dict[str, Callable] = {}
        self.max_retries = retry_value("agent_task_retries", 3)
        self.retry_delay = loop_sleep("agent_retry_delay", 1.0)
        self.services: Optional[Any] = None
        self._task_counter = 0
        self._start_time: Optional[float] = None
        self._initialized = False
        self.alignment_enabled = alignment_enabled
        self.alignment_system: Optional[Any] = None
        # Background task reference (prevent GC and enable exception logging)
        self._queue_worker_task: Optional[asyncio.Task] = None
        self.initialize_basic()

    def initialize_basic(self) -> None:
        """Basic synchronous initialization to avoid complex dependencies."""
        if self._initialized:
            return
        self.task_queue_lock = asyncio.Lock()
        self._initialized = True
        logger.info(f"[{self.agent_id}] BaseAgent basic initialization complete.")

    async def initialize_full(self) -> None:
        """Full asynchronous initialization including all services."""
        if self._initialized and self.hsp_connector:  # Avoid re-init
            return

        try:
            from core.hsp.connector import HSPConnector

            # Note: These might not exist yet or are incorrectly indexed
            # from ....ai.agent_collaboration_manager import AgentCollaborationManager
            # from ....ai.agent_monitoring_manager import AgentMonitoringManager
            # from ....ai.dynamic_agent_registry import DynamicAgentRegistry

            self.hsp_connector = HSPConnector(ai_id=self.agent_id)
            # self.collaboration_manager = AgentCollaborationManager(self.hsp_connector)
            # self.monitoring_manager = AgentMonitoringManager(self.hsp_connector)
            # self.agent_registry = DynamicAgentRegistry(self.hsp_connector)
            self._initialized = True
            logger.info(f"[{self.agent_id}] BaseAgent full initialization complete.")
        except Exception as e:
            # Use standardized error hierarchy
            init_error = InitializationError(
                f"[{self.agent_id}] Full initialization failed: {e}",
                agent_id=self.agent_id,
                error_type="initialization_failure"
            )
            logger.warning(f"[{self.agent_id}] Full initialization failed, using basic mode: {e}", 
                         exc_info=True, extra={
                             "agent_id": self.agent_id,
                             "error_type": "initialization_failure",
                             "correlation_id": init_error.correlation_id,
                             "timestamp": init_error.timestamp
                         })
            self.initialize_basic()

    async def start(self) -> None:
        """Starts the agent's main loop and connects to the HSP network."""
        if self.is_running:
            return

        logger.info(f"[{self.agent_id}] Setting is_running to True")
        self.is_running = True
        self._start_time = asyncio.get_running_loop().time()

        await self.initialize_full()

        if not self.hsp_connector:
            logger.error(f"[{self.agent_id}] Error: HSPConnector not available.", exc_info=True)
            self.is_running = False
            return

        logger.info(f"[{self.agent_id}] Starting HSP connection...")
        self.hsp_connector.register_on_task_request_callback(self.handle_task_request)

        for cap in self.capabilities:
            await self.hsp_connector.advertise_capability(cap)

        logger.info(f"[{self.agent_id}] is running and listening for tasks.")

    async def stop(self) -> None:
        """Stops the agent and shuts down its services."""
        logger.info(f"[{self.agent_id}] Stopping...")
        self.is_running = False
        if self.hsp_connector:
            await self.hsp_connector.disconnect()
        logger.info(f"[{self.agent_id}] Stopped.")

    def is_healthy(self) -> bool:
        """A basic health check for the agent."""
        return (
            self.is_running and self.hsp_connector is not None and self.hsp_connector.is_connected
        )

    async def handle_task_request(
        self,
        task_payload: HSPTaskRequestPayload,
        sender_ai_id: str,
        envelope: HSPMessageEnvelope,
    ) -> None:
        """The primary handler for incoming HSP task requests."""
        request_id = task_payload.get("request_id", str(uuid.uuid4()))
        capability_id = task_payload.get("capability_id_filter", "")
        logger.info(
            f"[{self.agent_id}] Received task request {request_id} for capability '{capability_id}' from '{sender_ai_id}'."
        )

        try:
            priority = TaskPriority(task_payload.get("priority", 2))
        except ValueError:
            logger.warning("Invalid task priority value, using NORMAL", exc_info=True)
            priority = TaskPriority.NORMAL

        queued_task = QueuedTask(
            task_id=request_id,
            priority=priority,
            payload=task_payload,
            sender_id=sender_ai_id,
            envelope=envelope,
            received_time=asyncio.get_running_loop().time(),
        )

        async with self.task_queue_lock:
            if len(self.task_queue) >= self.max_queue_size:
                logger.warning(
                    f"[{self.agent_id}] Task queue is full, rejecting task {queued_task.task_id}"
                    , exc_info=True
                )
                await self._send_task_rejection(queued_task)
                return

            # Simple append, priority can be handled in processing
            self.task_queue.append(queued_task)
            self.task_queue.sort(key=lambda t: t.priority.value, reverse=True)
            logger.info(
                f"[{self.agent_id}] Task {queued_task.task_id} added to queue with priority {queued_task.priority.name}"
            )

        task = asyncio.create_task(self._process_task_queue())
        self._queue_worker_task = task
        
        def _handle_task_completion(completed_task: asyncio.Task):
            """Handle task completion with proper error handling and cleanup."""
            try:
                completed_task.result()
            except asyncio.CancelledError:
                logger.info(f"[{self.agent_id}] Task queue worker cancelled")
            except Exception as e:
                logger.error(f"[{self.agent_id}] Queue worker task failed: {e}", exc_info=True)
                # Trigger system error handling
                asyncio.create_task(self._handle_critical_error(e))
            finally:
                # Clear reference to prevent memory leaks
                if self._queue_worker_task == completed_task:
                    self._queue_worker_task = None
        
        task.add_done_callback(_handle_task_completion)

    async def _process_task_queue(self) -> None:
        """Processes tasks from the queue one by one."""
        if not self.task_queue:
            return

        async with self.task_queue_lock:
            if not self.task_queue:  # Double check after acquiring lock:
                return
            task = self.task_queue.pop(0)

        await self._process_single_task(task)

    async def _process_single_task(self, task: QueuedTask) -> None:
        """Processes a single task."""
        logger.info(
            f"[{self.agent_id}] Processing task {task.task_id} with priority {task.priority.name}"
        )
        self._task_counter += 1

        try:
            capability_id = task.payload.get("capability_id_filter", "")
            handler = self.task_handlers.get(capability_id, self._default_task_handler)
            result = await handler(task.payload, task.sender_id, task.envelope)

            if task.payload.get("callback_address") and self.hsp_connector:
                result_payload = HSPTaskResultPayload(
                    request_id=task.task_id,
                    executing_ai_id=self.agent_id,
                    status="success",
                    payload=result,
                )
                await self.hsp_connector.send_task_result(
                    result_payload, task.payload["callback_address"], task.task_id
                )

        except Exception as e:
            # Use standardized error hierarchy for task processing
            task_error = TaskProcessingError(
                f"[{self.agent_id}] Error processing task {task.task_id}: {e}",
                agent_id=self.agent_id,
                error_type="task_processing_error"
            )
            
            logger.error(f"[{self.agent_id}] Error processing task {task.task_id}: {e}", 
                        exc_info=True, extra={
                            "agent_id": self.agent_id,
                            "task_id": task.task_id,
                            "error_type": "task_processing_error",
                            "correlation_id": task_error.correlation_id,
                            "timestamp": task_error.timestamp
                        })
            
            if task.retry_count < self.max_retries:
                logger.info(
                    f"[{self.agent_id}] Retrying task {task.task_id} ({task.retry_count + 1} / {self.max_retries})"
                )
                await asyncio.sleep(self.retry_delay * (2**task.retry_count))
                task.retry_count += 1
                async with self.task_queue_lock:
                    self.task_queue.insert(0, task)
            else:
                logger.error(
                    f"[{self.agent_id}] Task {task.task_id} failed after {self.max_retries} retries."
                    , exc_info=True, extra={
                        "agent_id": self.agent_id,
                        "task_id": task.task_id,
                        "error_type": "task_processing_error",
                        "correlation_id": task_error.correlation_id,
                        "timestamp": task_error.timestamp
                    }
                )
                if task.payload.get("callback_address") and self.hsp_connector:
                    await self._send_task_failure(
                        task, f"Task failed after {self.max_retries} retries: {safe_error(e)}"
                    )

    async def _default_task_handler(
        self,
        task_payload: HSPTaskRequestPayload,
        sender_ai_id: str,
        envelope: HSPMessageEnvelope,
    ) -> dict[str, Any]:
        """Default task handler for unimplemented capabilities."""
        capability_id = task_payload.get("capability_id_filter", "")
        logger.warning(f"[{self.agent_id}] No specific handler for capability '{capability_id}'", exc_info=True)
        return {
            "status": "failure",
            "error_details": {
                "error_code": "NOT_IMPLEMENTED",
                "error_message": f"The '{self.__class__.__name__}' has not implemented a handler for capability '{capability_id}'.",
            },
        }

    async def _send_task_rejection(self, task: QueuedTask) -> None:
        """Sends a rejection response for a task that couldn't be queued."""
        if self.hsp_connector and task.payload.get("callback_address"):
            result_payload = HSPTaskResultPayload(
                request_id=task.task_id,
                executing_ai_id=self.agent_id,
                status="rejected",
                error_details={
                    "error_code": "QUEUE_FULL",
                    "error_message": "Task queue is full, task rejected",
                },
            )
            await self.hsp_connector.send_task_result(
                result_payload, task.payload["callback_address"], task.task_id
            )

    async def _send_task_failure(self, task: QueuedTask, error_message: str) -> None:
        """Sends a failure response for a task that failed during execution."""
        if self.hsp_connector and task.payload.get("callback_address"):
            result_payload = HSPTaskResultPayload(
                request_id=task.task_id,
                executing_ai_id=self.agent_id,
                status="failure",
                error_details={
                    "error_code": "EXECUTION_ERROR",
                    "error_message": error_message,
                },
            )
            await self.hsp_connector.send_task_result(
                result_payload, task.payload["callback_address"], task.task_id
            )

    def register_task_handler(self, capability_id: str, handler: Callable) -> None:
        """Register a specific handler for a capability."""
        self.task_handlers[capability_id] = handler
        logger.info(f"[{self.agent_id}] Registered handler for capability '{capability_id}'")

    async def _handle_critical_error(self, error: Exception) -> None:
        """Handle critical errors that could impact system stability."""
        critical_error = AgentError(
            f"[{self.agent_id}] Critical error detected: {error}",
            agent_id=self.agent_id,
            error_type="critical_error"
        )
        
        logger.error(f"[{self.agent_id}] Critical error detected: {error}", 
                    exc_info=True, extra={
                        "agent_id": self.agent_id,
                        "error_type": "critical_error",
                        "correlation_id": critical_error.correlation_id,
                        "timestamp": critical_error.timestamp
                    })
        
        # Attempt to recover from critical error
        try:
            if self.is_running and self.hsp_connector:
                await self.hsp_connector.reconnect()
                logger.info(f"[{self.agent_id}] Successfully reconnected after critical error", extra={
                    "agent_id": self.agent_id,
                    "error_type": "recovery_success",
                    "correlation_id": critical_error.correlation_id,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as reconnect_error:
            # Use standardized error hierarchy for reconnection errors
            reconnect_error_obj = ConnectionError(
                f"[{self.agent_id}] Failed to recover from critical error: {reconnect_error}",
                agent_id=self.agent_id,
                error_type="reconnection_failure"
            )
            logger.error(f"[{self.agent_id}] Failed to recover from critical error: {reconnect_error}", 
                        exc_info=True, extra={
                            "agent_id": self.agent_id,
                            "error_type": "reconnection_failure",
                            "correlation_id": reconnect_error_obj.correlation_id,
                            "timestamp": reconnect_error_obj.timestamp
                        })
            # System may be in degraded state
            await self._handle_system_degraded()

    async def _handle_system_degraded(self) -> None:
        """Handle system degraded state."""
        logger.warning(f"[{self.agent_id}] System is in degraded state")
        
        # Attempt to cleanup and restart if possible
        try:
            await self.stop()
            # Wait a moment before attempting restart
            await asyncio.sleep(loop_sleep("agent_restart_delay", 5.0))
            await self.start()
            logger.info(f"[{self.agent_id}] System restarted from degraded state")
        except Exception as restart_error:
            # Use standardized error hierarchy for restart errors
            restart_error_obj = InitializationError(
                f"[{self.agent_id}] Failed to restart system: {restart_error}",
                agent_id=self.agent_id,
                error_type="restart_failure"
            )
            logger.error(f"[{self.agent_id}] Failed to restart system: {restart_error}", 
                        exc_info=True, extra={
                            "agent_id": self.agent_id,
                            "error_type": "restart_failure",
                            "correlation_id": restart_error_obj.correlation_id,
                            "timestamp": restart_error_obj.timestamp
                        })

    async def cleanup_resources(self) -> None:
        """Properly clean up all resources to prevent memory leaks."""
        logger.info(f"[{self.agent_id}] Starting resource cleanup")
        
        # Cancel and cleanup queue worker task
        if self._queue_worker_task and not self._queue_worker_task.done():
            self._queue_worker_task.cancel()
            try:
                await self._queue_worker_task
            except asyncio.CancelledError:
                logger.info(f"[{self.agent_id}] Queue worker task cancelled during cleanup")
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error during queue worker cleanup: {e}", exc_info=True)
            finally:
                self._queue_worker_task = None
        
        # Clear task queue
        async with self.task_queue_lock:
            self.task_queue.clear()
        
        # Cleanup HSP connector
        if self.hsp_connector:
            try:
                await self.hsp_connector.disconnect()
                logger.info(f"[{self.agent_id}] HSP connector disconnected")
            except Exception as e:
                logger.error(f"[{self.agent_id}] Error disconnecting HSP connector: {e}", exc_info=True)
            finally:
                self.hsp_connector = None
        
        # Reset agent state
        self.is_running = False
        self._initialized = False
        self._task_counter = 0
        self._start_time = None
        
        logger.info(f"[{self.agent_id}] Resource cleanup completed")

    def __del__(self):
        """Ensure proper cleanup when agent is destroyed."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(self.cleanup_resources())
            else:
                logger.warning(f"[{self.agent_id}] Agent destroyed without proper cleanup (event loop not running)")
        except RuntimeError:
            logger.debug(f"[{self.agent_id}] No running event loop in destructor")
        except Exception as err:
            logger.debug(f"[{self.agent_id}] Destructor cleanup skipped: {err}")
