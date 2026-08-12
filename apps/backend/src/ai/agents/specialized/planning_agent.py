# =============================================================================
# ANGELA-MATRIX: L6[执行层] βδ [A] L4+
#
# 职责: 任务规划代理 — 委托至 PlanningEngine
# 维度: 认知(β) 逻辑规划 + 精神(δ) 目标导向
# 安全: 使用 Key A (后端控制)
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PlanningAgent:
    """Agent wrapper around PlanningEngine for task planning.

    Delegates all actual planning logic to PlanningEngine.
    This class exists only to maintain the agent interface.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        try:
            from ai.reasoning.planning_engine import PlanningEngine
            self._engine = PlanningEngine()
        except ImportError:
            self._engine = None
            logger.warning("PlanningAgent: PlanningEngine not available")

    def create_plan(self, goal: str, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not goal:
            return {"status": "error", "message": "No goal provided"}
        if self._engine:
            plan = self._engine.create_plan(goal, context=constraints)
            return {
                "status": "success",
                "plan_id": plan.plan_id,
                "steps": [s.description for s in plan.steps],
                "message": f"Created plan with {len(plan.steps)} steps",
            }
        return {"status": "error", "message": "PlanningEngine not available"}

    def optimize_plan(self, plan_id: str, criteria: Optional[Dict] = None) -> Dict[str, Any]:
        if self._engine:
            status = self._engine.get_plan_status(plan_id)
            if status:
                return {"status": "success", "plan_id": plan_id, "optimized_steps": status.get("total_steps", 0)}
        return {"status": "error", "message": f"Plan '{plan_id}' not found"}

    def track_progress(self, plan_id: str, completed_steps: List[str]) -> Dict[str, Any]:
        if self._engine:
            status = self._engine.get_plan_status(plan_id)
            if status:
                total = status.get("total_steps", 0)
                done = len(completed_steps)
                pct = round((done / total) * 100, 2) if total > 0 else 0.0
                return {
                    "status": "success",
                    "plan_id": plan_id,
                    "total_steps": total,
                    "completed_steps": done,
                    "progress_percentage": pct,
                }
        return {"status": "error", "message": f"Plan '{plan_id}' not found"}
