"""
Angela AI v6.0 - Learning Orchestrator (學習編排器)
 ASI Core: 協調評估器與控制器，實現閉環自我演化。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ai.meta.adaptive_learning_controller import AdaptiveLearningController


class _SimpleEvaluator:
    """Minimal evaluator replacing TaskExecutionEvaluator."""

    async def evaluate_task_execution(self, task: dict, result: dict) -> dict:
        return {
            "metrics": {"coherence": 0.5, "relevance": 0.5},
            "overall_rating": 0.5,
        }


logger = logging.getLogger(__name__)


class LearningOrchestrator:
    """
    學習編排器：負責封裝「執行-評估-適應」的閉環邏輯。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.evaluator = _SimpleEvaluator()
        self.controller = AdaptiveLearningController(self.config.get("controller_config"))
        self.learning_history: List[Dict[str, Any]] = []

    async def process_learning_cycle(
        self, task: Dict[str, Any], execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        執行一個完整的學習周期。
        1. 評估任務執行的品質與指標。
        2. 將評估結果餵給控制器，決定下一階段的學習策略。
        """
        # Step 1: Evaluate
        evaluation = await self.evaluator.evaluate_task_execution(task, execution_result)

        # Step 2: Adapt
        # 將 evaluation 轉化為控制器需要的 evolution_metrics 格式
        metrics_snapshot = evaluation["metrics"]
        adaptation = await self.controller.adapt_learning_strategy(task, [metrics_snapshot])

        # Step 3: Record
        cycle_result = {
            "task_id": task.get("id"),
            "evaluation": evaluation,
            "adaptation": adaptation,
            "timestamp": datetime.now().isoformat(),
        }
        self.learning_history.append(cycle_result)

        logger.info(
            f"[LearningOrchestrator] Learning cycle completed for task {task.get('id')}. Rating: {evaluation['overall_rating']:.2f}"
        )

        return cycle_result

    def get_learning_status(self) -> Dict[str, Any]:
        """獲取當前系統的學習狀態摘要。"""
        return {
            "controller_config": self.controller.get_current_configuration(),
            "cycles_completed": len(self.learning_history),
            "latest_rating": (
                self.learning_history[-1]["evaluation"]["overall_rating"]
                if self.learning_history
                else 0.0
            ),
        }
