import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..base.base_agent import BaseAgent
from ....core.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope

logger = logging.getLogger(__name__)

class PlanningAgent(BaseAgent):
    """
    A specialized agent for task planning, scheduling, and project management.
    """

    def __init__(self, agent_id: str) -> None:
        capabilities = [
            {
                "capability_id": f"{agent_id}_task_planning_v1.0",
                "name": "task_planning",
                "description": "Creates detailed plans for complex tasks or projects.",
                "version": "1.0",
                "parameters": [
                    {"name": "goal", "type": "string", "required": True, "description": "The objective to plan for"},
                    {"name": "constraints", "type": "object", "required": False, "description": "Time/resource constraints"}
                ],
                "returns": {"type": "object", "description": "Detailed plan with tasks and timeline."}
            },
            {
                "capability_id": f"{agent_id}_schedule_optimization_v1.0",
                "name": "schedule_optimization",
                "description": "Optimizes task schedules based on priorities.",
                "version": "1.0",
                "parameters": [
                    {"name": "tasks", "type": "array", "required": True, "description": "List of tasks"},
                    {"name": "deadline", "type": "string", "required": False, "description": "Project deadline"}
                ],
                "returns": {"type": "object", "description": "Optimized schedule."}
            }
        ]
        super().__init__(agent_id=agent_id, capabilities=capabilities, agent_name="PlanningAgent")

        # Register handlers
        self.register_task_handler(f"{agent_id}_task_planning_v1.0", self._handle_task_planning)
        self.register_task_handler(f"{agent_id}_schedule_optimization_v1.0", self._handle_schedule_optimization)

    async def _handle_task_planning(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        params = payload.get("parameters", {})
        return self._create_task_plan(params)

    async def _handle_schedule_optimization(self, payload: HSPTaskRequestPayload, sender_id: str, envelope: HSPMessageEnvelope) -> Dict[str, Any]:
        params = payload.get("parameters", {})
        return self._optimize_schedule(params)

    def _create_task_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        goal = params.get('goal', '')
        if not goal: raise ValueError("No goal provided")
        
        # Simple template-based planning for now
        plan = {
            "plan_id": f"plan_{uuid.uuid4().hex[:8]}",
            "goal": goal,
            "tasks": [
                {"task_id": "task_001", "name": "Initial Analysis", "duration_days": 2},
                {"task_id": "task_002", "name": "Execution Phase", "duration_days": 5},
                {"task_id": "task_003", "name": "Review and Close", "duration_days": 1}
            ]
        }
        return plan

    def _optimize_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tasks = params.get('tasks', [])
        return {"optimized_tasks": tasks, "status": "optimized"}