import logging
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TaskExecutionEvaluator:
    """
    任務執行評估器 (Task Execution Evaluator)
    負責分析任務執行的成效，計算指標並生成改進建議。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.evaluation_history: List[Dict[str, Any]] = []
        logger.info("TaskExecutionEvaluator initialized.")

    async def evaluate_task_execution(self, task: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        對任務執行結果進行全面評估。
        """
        task_id = task.get('id', 'unknown')
        logger.info(f"Evaluating task execution for [{task_id}]")

        # 1. 計算核心指標
        metrics = self._calculate_metrics(task, execution_result)
        
        # 2. 分析反饋 (如果有)
        feedback_analysis = self._analyze_feedback(execution_result.get('feedback', {}))
        
        # 3. 生成改進建議
        suggestions = self._generate_suggestions(metrics, feedback_analysis)

        evaluation = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "feedback_analysis": feedback_analysis,
            "suggestions": suggestions,
            "overall_rating": self._calculate_overall_rating(metrics)
        }

        self.evaluation_history.append(evaluation)
        logger.info(f"Task {task_id} evaluated with rating: {evaluation['overall_rating']:.2f}")
        return evaluation

    def _calculate_metrics(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """計算執行指標：成功率、耗時、資源效率等"""
        start_time = result.get('start_time', time.time())
        end_time = result.get('end_time', time.time())
        duration = end_time - start_time
        
        # 基礎成功率判斷
        success_rate = 1.0 if result.get('success', False) else 0.0
        
        # 質量分數
        output = str(result.get('output', ""))
        quality_score = min(1.0, len(output) / 500.0) if success_rate > 0 else 0.0

        return {
            "success_rate": success_rate,
            "duration": duration,
            "efficiency": 0.85 if duration < 5.0 else 0.6,
            "quality_score": quality_score
        }

    def _analyze_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """分析外部或系統內部的反饋數據"""
        if not feedback:
            return {"sentiment": "neutral", "accuracy_gap": 0.0}
            
        return {
            "sentiment": feedback.get("sentiment", "neutral"),
            "accuracy_gap": feedback.get("error_margin", 0.05)
        }

    def _generate_suggestions(self, metrics: Dict[str, Any], feedback: Dict[str, Any]) -> List[str]:
        """基於指標生成改進建議"""
        suggestions = []
        if metrics["success_rate"] < 1.0:
            suggestions.append("分析失敗原因並重試")
        if metrics["duration"] > 5.0:
            suggestions.append("優化執行路徑以減少耗時")
        if feedback.get("accuracy_gap", 0) > 0.1:
            suggestions.append("校準模型參數以提高準確度")
            
        return suggestions if suggestions else ["繼續保持當前策略"]

    def _calculate_overall_rating(self, metrics: Dict[str, Any]) -> float:
        """計算綜合評分"""
        return (metrics["success_rate"] * 0.5 + 
                metrics["quality_score"] * 0.3 + 
                metrics["efficiency"] * 0.2)

    def get_historical_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取歷史評估數據"""
        return self.evaluation_history[-limit:]
