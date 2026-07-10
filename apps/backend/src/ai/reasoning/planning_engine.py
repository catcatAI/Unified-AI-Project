# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
# =============================================================================

"""
Planning Engine — Multi-step task planning with dependency graphs.

Decomposes goals into actionable steps, manages dependencies,
tracks execution progress, and re-plans on failure.
"""

import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.utils import any_keyword

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """A single step in a plan."""
    step_id: str
    description: str
    action: str
    depends_on: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    agent: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 2


@dataclass
class Plan:
    """A complete plan with steps and metadata."""
    plan_id: str
    goal: str
    steps: List[PlanStep] = field(default_factory=list)
    created_at: float = 0.0
    status: str = "active"
    context: Dict[str, Any] = field(default_factory=dict)


class PlanningEngine:
    """
    Multi-step planning engine that:
    1. Decomposes goals into steps
    2. Manages step dependencies
    3. Tracks execution progress
    4. Re-plans on failure
    """

    def __init__(self) -> None:
        self._plans: Dict[str, Plan] = {}

    def create_plan(self, goal: str, context: Optional[Dict[str, Any]] = None) -> Plan:
        """Create a plan from a goal description."""
        import time

        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        steps = self._decompose_goal(goal, context)

        plan = Plan(
            plan_id=plan_id,
            goal=goal,
            steps=steps,
            created_at=time.time(),
            context=context or {},
        )
        self._plans[plan_id] = plan

        logger.info(f"Created plan {plan_id} with {len(steps)} steps for: {goal[:50]}")
        return plan

    def _decompose_goal(
        self, goal: str, context: Optional[Dict[str, Any]] = None
    ) -> List[PlanStep]:
        """Decompose a goal into ordered steps with dependencies."""
        steps: List[PlanStep] = []
        lower = goal.lower()

        # Detect goal type and generate appropriate steps
        if any_keyword(lower, ("文件", "file", "讀取", "read")):
            steps = self._plan_file_operation(goal)
        elif any_keyword(lower, ("代碼", "code", "程式", "program")):
            steps = self._plan_code_task(goal)
        elif any_keyword(lower, ("搜索", "search", "查找", "find")):
            steps = self._plan_research_task(goal)
        elif any_keyword(lower, ("分析", "analyze", "數據", "data")):
            steps = self._plan_analysis_task(goal)
        else:
            steps = self._plan_generic_task(goal)

        return steps

    def _plan_file_operation(self, goal: str) -> List[PlanStep]:
        return [
            PlanStep(
                step_id="s1",
                description="Identify target file path",
                action="identify_path",
            ),
            PlanStep(
                step_id="s2",
                description="Check file existence and permissions",
                action="check_file",
                depends_on=["s1"],
            ),
            PlanStep(
                step_id="s3",
                description="Execute file operation",
                action="execute_operation",
                depends_on=["s2"],
                agent="FileOperationHandler",
            ),
        ]

    def _plan_code_task(self, goal: str) -> List[PlanStep]:
        return [
            PlanStep(
                step_id="s1",
                description="Understand code requirements",
                action="analyze_requirements",
            ),
            PlanStep(
                step_id="s2",
                description="Locate relevant code files",
                action="locate_code",
                depends_on=["s1"],
            ),
            PlanStep(
                step_id="s3",
                description="Implement code changes",
                action="implement",
                depends_on=["s2"],
                agent="CodeExecutionHandler",
            ),
            PlanStep(
                step_id="s4",
                description="Verify changes",
                action="verify",
                depends_on=["s3"],
            ),
        ]

    def _plan_research_task(self, goal: str) -> List[PlanStep]:
        return [
            PlanStep(
                step_id="s1",
                description="Identify search keywords",
                action="extract_keywords",
            ),
            PlanStep(
                step_id="s2",
                description="Perform web search",
                action="search",
                depends_on=["s1"],
                agent="WebSearchAgent",
            ),
            PlanStep(
                step_id="s3",
                description="Synthesize findings",
                action="synthesize",
                depends_on=["s2"],
            ),
        ]

    def _plan_analysis_task(self, goal: str) -> List[PlanStep]:
        return [
            PlanStep(
                step_id="s1",
                description="Identify data sources",
                action="identify_data",
            ),
            PlanStep(
                step_id="s2",
                description="Load and validate data",
                action="load_data",
                depends_on=["s1"],
            ),
            PlanStep(
                step_id="s3",
                description="Perform analysis",
                action="analyze",
                depends_on=["s2"],
                agent="DataAnalysisAgent",
            ),
            PlanStep(
                step_id="s4",
                description="Generate report",
                action="report",
                depends_on=["s3"],
            ),
        ]

    def _plan_generic_task(self, goal: str) -> List[PlanStep]:
        return [
            PlanStep(
                step_id="s1",
                description="Understand task requirements",
                action="understand",
            ),
            PlanStep(
                step_id="s2",
                description="Execute task",
                action="execute",
                depends_on=["s1"],
            ),
            PlanStep(
                step_id="s3",
                description="Verify result",
                action="verify",
                depends_on=["s2"],
            ),
        ]

    def get_ready_steps(self, plan_id: str) -> List[PlanStep]:
        """Get steps whose dependencies are all completed."""
        plan = self._plans.get(plan_id)
        if not plan:
            return []

        completed = {
            s.step_id for s in plan.steps if s.status == StepStatus.COMPLETED
        }
        ready = []
        for step in plan.steps:
            if step.status != StepStatus.PENDING:
                continue
            if all(dep in completed for dep in step.depends_on):
                ready.append(step)
        return ready

    def mark_step_complete(self, plan_id: str, step_id: str, result: str = "") -> bool:
        """Mark a step as completed."""
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        for step in plan.steps:
            if step.step_id == step_id:
                step.status = StepStatus.COMPLETED
                step.result = result
                logger.info(f"Step {step_id} completed in plan {plan_id}")
                return True
        return False

    def mark_step_failed(self, plan_id: str, step_id: str, error: str = "") -> bool:
        """Mark a step as failed and attempt re-planning."""
        plan = self._plans.get(plan_id)
        if not plan:
            return False

        for step in plan.steps:
            if step.step_id == step_id:
                step.status = StepStatus.FAILED
                step.error = error
                step.retry_count += 1

                if step.retry_count <= step.max_retries:
                    # Retry: reset to pending
                    step.status = StepStatus.PENDING
                    step.error = None
                    logger.info(f"Step {step_id} retry {step.retry_count}/{step.max_retries}")
                else:
                    logger.warning(f"Step {step_id} failed permanently in plan {plan_id}")
                return True
        return False

    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            return None

        total = len(plan.steps)
        completed = sum(1 for s in plan.steps if s.status == StepStatus.COMPLETED)
        failed = sum(1 for s in plan.steps if s.status == StepStatus.FAILED)

        return {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "progress": completed / total if total > 0 else 0.0,
            "status": "completed" if completed == total else "failed" if failed > 0 else "active",
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "status": s.status.value,
                    "result": s.result,
                }
                for s in plan.steps
            ],
        }

    def list_plans(self) -> List[Dict[str, Any]]:
        """List all plans with basic info."""
        return [
            {
                "plan_id": p.plan_id,
                "goal": p.goal[:100],
                "status": p.status,
                "steps": len(p.steps),
            }
            for p in self._plans.values()
        ]
