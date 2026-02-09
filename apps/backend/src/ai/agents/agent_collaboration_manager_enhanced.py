import asyncio
import logging
import os
import sys
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from core.hsp.connector import HSPConnector
from core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

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
    result: Optional[Union[Dict[str, Any], asyncio.Future]] = None
    error_message: Optional[str] = None
    priority: int = 1
    created_time: float = field(default_factory=time.time)
    retry_count: int = 0
    cache_key: Optional[str] = None

@dataclass
class CachedTaskResult:
    """缓存的任务结果 (Cached Task Result)"""
    result: Dict[str, Any]
    timestamp: float
    expiry_time: float

class AgentCollaborationManagerEnhanced:
    """
    Manages complex collaboration between agents with priority queuing and caching.
    """

    def __init__(self, hsp_connector: HSPConnector) -> None:
        self.hsp_connector = hsp_connector
        self.active_collaborations: Dict[str, CollaborationTask] = {}
        self.agent_capabilities: Dict[str, List[str]] = {}
        self.collaboration_lock = asyncio.Lock()
        self.task_queue: List[CollaborationTask] = []
        self.max_queue_size: int = 1000
        self.task_cache: Dict[str, CachedTaskResult] = {}
        self.cache_expiry_seconds: int = 300

        if self.hsp_connector:
            self.hsp_connector.register_on_task_result_callback(self._handle_task_result)

    async def register_agent_capability(self, agent_id: str, capability_id: str):
        async with self.collaboration_lock:
            if agent_id not in self.agent_capabilities:
                self.agent_capabilities[agent_id] = []
            if capability_id not in self.agent_capabilities[agent_id]:
                self.agent_capabilities[agent_id].append(capability_id)
                logger.info(f"Registered capability '{capability_id}' for agent '{agent_id}'")

    async def find_agent_for_capability(self, capability_id: str) -> Optional[str]:
        async with self.collaboration_lock:
            for agent_id, capabilities in self.agent_capabilities.items():
                if capability_id in capabilities:
                    return agent_id
            return None

    def _generate_cache_key(self, capability_id: str, parameters: Dict[str, Any]) -> str:
        normalized_params = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(f"{capability_id}{normalized_params}".encode()).hexdigest()

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        async with self.collaboration_lock:
            if cache_key in self.task_cache:
                cached = self.task_cache[cache_key]
                if current_time < cached.expiry_time:
                    return cached.result
                del self.task_cache[cache_key]
        return None

    async def delegate_task(self, requester_agent_id: str, target_agent_id: str,
                           capability_id: str, parameters: Dict[str, Any],
                           priority: int = 1, use_cache: bool = True) -> str:
        
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(capability_id, parameters)
            cached_result = await self._get_cached_result(cache_key)
            if cached_result is not None:
                logger.info(f"Using cached result for capability '{capability_id}'")
                # In a real system, we'd fire an event or return this immediately
                # For this manager, we still create a task record but mark it COMPLETED
        
        task_id = f"collab_task_{int(time.time() * 1000)}_{len(self.active_collaborations) + 1}"
        
        collaboration_task = CollaborationTask(
            task_id=task_id,
            requester_agent_id=requester_agent_id,
            target_agent_id=target_agent_id,
            capability_id=capability_id,
            parameters=parameters,
            priority=priority,
            cache_key=cache_key
        )

        async with self.collaboration_lock:
            self.active_collaborations[task_id] = collaboration_task
            self._add_task_to_queue(collaboration_task)

        task_payload = HSPTaskRequestPayload(
            request_id=task_id,
            requester_ai_id=requester_agent_id,
            target_ai_id=target_agent_id,
            capability_id_filter=capability_id,
            parameters=parameters,
            status="pending",
            priority=priority
        )

        try:
            success = await self.hsp_connector.send_task_request(
                payload=task_payload,
                target_ai_id_or_topic=target_agent_id
            )

            if success:
                collaboration_task.status = CollaborationStatus.IN_PROGRESS
                logger.info(f"Delegated task '{task_id}' to '{target_agent_id}' (priority {priority})")
            else:
                collaboration_task.status = CollaborationStatus.FAILED
                collaboration_task.error_message = "Failed to send HSP request"
        except Exception as e:
            collaboration_task.status = CollaborationStatus.FAILED
            collaboration_task.error_message = str(e)
            logger.error(f"Error delegating task '{task_id}': {e}")
            
        return task_id

    def _add_task_to_queue(self, task: CollaborationTask):
        inserted = False
        for i, existing in enumerate(self.task_queue):
            if task.priority > existing.priority:
                self.task_queue.insert(i, task)
                inserted = True
                break
        if not inserted:
            self.task_queue.append(task)

    async def _handle_task_result(self, result_payload: HSPTaskResultPayload,
                                  sender_ai_id: str, envelope: HSPMessageEnvelope):
        task_id = result_payload.get("request_id", "")
        async with self.collaboration_lock:
            if task_id in self.active_collaborations:
                task = self.active_collaborations[task_id]
                if result_payload.get("status") == "success":
                    task.status = CollaborationStatus.COMPLETED
                    task.result = result_payload.get("payload", {})
                    if task.cache_key:
                        self.task_cache[task.cache_key] = CachedTaskResult(
                            result=task.result,
                            timestamp=time.time(),
                            expiry_time=time.time() + self.cache_expiry_seconds
                        )
                else:
                    task.status = CollaborationStatus.FAILED
                    task.error_message = result_payload.get("error_details", {}).get("error_message", "Unknown error")
                
                self.task_queue = [t for t in self.task_queue if t.task_id != task_id]

    async def orchestrate_multi_agent_task(self, requester_agent_id: str, task_sequence: List[Dict[str, Any]]) -> Dict[str, Any]:
        results = {}
        for i, task_def in enumerate(task_sequence):
            cap_id = task_def["capability_id"]
            params = task_def.get("parameters", {})
            
            # Placeholder resolution (simplified)
            for k, v in params.items():
                if isinstance(v, str) and "output_of_task_" in v:
                    idx = int(v.split("output_of_task_")[1].split()[0])
                    if idx in results: params[k] = results[idx]

            target_id = await self.find_agent_for_capability(cap_id)
            if not target_id: return {"status": "failed", "error": f"No agent for {cap_id}"}
            
            task_id = await self.delegate_task(requester_agent_id, target_id, cap_id, params, task_def.get("priority", 1))
            
            timeout = task_def.get("timeout", 30)
            start = time.time()
            while time.time() - start < timeout:
                status = self.active_collaborations.get(task_id)
                if status and status.status in [CollaborationStatus.COMPLETED, CollaborationStatus.FAILED]:
                    break
                await asyncio.sleep(0.5)
            
            final_status = self.active_collaborations.get(task_id)
            if final_status and final_status.status == CollaborationStatus.COMPLETED:
                results[i] = final_status.result
            else:
                return {"status": "failed", "error": f"Task {i} failed or timed out"}
        
        return {"status": "success", "results": results}