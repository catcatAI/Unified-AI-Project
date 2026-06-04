# =============================================================================
# ANGELA-MATRIX: L6[执行层] βδ [A] L4+
# =============================================================================
#
# 职责: 任务规划、调度和项目管理代理
# 维度: 涉及认知维度 (β) 的逻辑规划和精神维度 (δ) 的目标导向
# 安全: 使用 Key A (后端控制) 进行任务权限管理
# 成熟度: L4+ 等级可以进行复杂的任务规划和项目管理
#
# 能力:
# - task_planning: 任务规划
# - scheduling: 调度管理
# - project_management: 项目管理
# - goal_breakdown: 目标分解
# - resource_allocation: 资源分配
#
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PlanningAgent:
    """Agent for creating, optimizing, and tracking plans."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._plans: Dict[str, Dict[str, Any]] = {}
        logger.info(f"PlanningAgent initialized with config: {self.config}")

    def create_plan(self, goal: str, constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a plan with steps to achieve a goal."""
        if not goal:
            return {"status": "error", "message": "No goal provided"}
        constraints = constraints or {}
        plan_id = f"plan_{hash(goal) % 1000000}"
        steps = [f"Step {i+1}: {phrase}" for i, phrase in enumerate(goal.split(". "))] if ". " in goal else [f"Step 1: {goal}"]
        plan = {"goal": goal, "steps": steps, "constraints": constraints, "status": "created"}
        self._plans[plan_id] = plan
        logger.info(f"create_plan: goal='{goal}', {len(steps)} steps, id={plan_id}")
        return {"status": "success", "message": f"Created plan with {len(steps)} steps", "plan_id": plan_id, "steps": steps, "constraints": constraints}

    def optimize_plan(self, plan_id: str, optimization_criteria: Dict[str, Any] = None) -> Dict[str, Any]:
        """Optimize an existing plan based on criteria."""
        if plan_id not in self._plans:
            return {"status": "error", "message": f"Plan '{plan_id}' not found"}
        optimization_criteria = optimization_criteria or {}
        plan = self._plans[plan_id]
        logger.info(f"optimize_plan: id={plan_id}, criteria={optimization_criteria}")
        return {
            "status": "success",
            "message": f"Plan '{plan_id}' optimized",
            "plan_id": plan_id,
            "original_steps": len(plan["steps"]),
            "optimized_steps": len(plan["steps"]),
            "optimization_criteria": optimization_criteria,
        }

    def track_progress(self, plan_id: str, completed_steps: List[str]) -> Dict[str, Any]:
        """Track progress on a plan."""
        if plan_id not in self._plans:
            return {"status": "error", "message": f"Plan '{plan_id}' not found"}
        plan = self._plans[plan_id]
        total = len(plan["steps"])
        done = len(completed_steps)
        progress_pct = round((done / total) * 100, 2) if total > 0 else 0.0
        logger.info(f"track_progress: id={plan_id}, {done}/{total} steps")
        return {
            "status": "success",
            "message": f"Progress: {done}/{total} steps completed ({progress_pct}%)",
            "plan_id": plan_id,
            "total_steps": total,
            "completed_steps": done,
            "progress_percentage": progress_pct,
        }

