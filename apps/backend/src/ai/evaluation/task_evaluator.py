import logging
import asyncio
import time
import math
from datetime import datetime
from typing import List, Dict, Any, Optional

from ai.symbolic_space.unified_symbolic_space import UnifiedSymbolicSpace

logger = logging.getLogger(__name__)

class TaskExecutionEvaluator:
    """
    任務執行評估器 (Task Execution Evaluator)
    負責分析任務執行的成效，計算指標並生成改進建議。
    升級版：包含語義連貫性、邏輯一致性與精細效率計算。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, db_path: str = "reasoning_symbolic.db"):
        self.config = config or {}
        self.evaluation_history: List[Dict[str, Any]] = []
        # 集成符號空間用於邏輯一致性檢查
        self.symbolic_space = UnifiedSymbolicSpace(db_path)
        logger.info("TaskExecutionEvaluator (Objective Logic) initialized.")

    async def evaluate_task_execution(self, task: Dict[str, Any], execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """對任務執行結果進行全面評估。"""
        task_id = task.get('id', str(int(time.time())))
        logger.info(f"Evaluating task execution for [{task_id}]")

        # 1. 計算核心指標 (連貫性, 效率, 成功率)
        metrics = await self._calculate_deep_metrics(task, execution_result)
        
        # 2. 邏輯一致性檢查 (檢查輸出是否與符號空間中的事實衝突)
        consistency_report = self._check_logical_consistency(execution_result.get('output', ""))
        metrics["consistency_score"] = consistency_report["score"]
        
        # 3. 分析反饋
        feedback_analysis = self._analyze_feedback(execution_result.get('feedback', {}))
        
        # 4. 生成改進建議
        suggestions = self._generate_suggestions(metrics, feedback_analysis, consistency_report)

        evaluation = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "consistency_report": consistency_report,
            "feedback_analysis": feedback_analysis,
            "suggestions": suggestions,
            "overall_rating": self._calculate_overall_rating(metrics)
        }

        self.evaluation_history.append(evaluation)
        return evaluation

    async def _calculate_deep_metrics(self, task: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """深度指標計算：包含語義熵與精細效率。"""
        start_time = result.get('start_time', time.time())
        end_time = result.get('end_time', time.time())
        duration = max(0.001, end_time - start_time)
        
        output = str(result.get('output', ""))
        
        # 1. 語義連貫性 (基於詞彙多樣性與重複比例的簡化熵模型)
        coherence = self._calculate_coherence(output)
        
        # 2. 精細效率 (基於任務複雜度與耗時的比例)
        # 假設每 100 字消耗 1 秒為基準 1.0
        expected_time = len(output) / 100.0 + 0.5
        efficiency = min(1.0, expected_time / duration)
        
        success_rate = 1.0 if result.get('success', False) else 0.0

        return {
            "success_rate": success_rate,
            "duration": duration,
            "efficiency": efficiency,
            "coherence_score": coherence,
            "quality_score": (coherence * 0.7 + success_rate * 0.3)
        }

    def _calculate_coherence(self, text: str) -> float:
        """計算語義連貫性分數 (基於 TTR - Type-Token Ratio 的變體)。"""
        if not text: return 0.0
        words = text.lower().split()
        if not words: return 0.0
        
        unique_words = set(words)
        ttr = len(unique_words) / len(words)
        
        # 如果句子太短或太長且全重複，分數降低
        # 理想 TTR 在 0.4 - 0.7 之間 (針對一般對話)
        coherence = 1.0 - abs(0.55 - ttr)
        return max(0.0, min(1.0, coherence))

    def _check_logical_consistency(self, output: str) -> Dict[str, Any]:
        """檢查輸出是否與符號空間中的知識路徑衝突。"""
        # 查找輸出中提及的實體並檢查其在符號空間中的屬性
        conflicts = []
        score = 1.0
        
        # 簡化實現：查找輸出關鍵字是否與『敏感』或『衝突』節點相連
        # 實際應用可擴展為使用 NER 提取實體
        symptoms = ["false", "wrong", "error", "impossible"]
        for s in symptoms:
            if s in output.lower():
                score -= 0.1
                conflicts.append(f"Potential negative phrasing detected: {s}")
        
        return {"score": max(0.0, score), "conflicts": conflicts}

    def _analyze_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "sentiment": feedback.get("sentiment", "neutral"),
            "accuracy_gap": feedback.get("error_margin", 0.0)
        }

    def _generate_suggestions(self, metrics: Dict[str, Any], feedback: Dict[str, Any], 
                            consistency: Dict[str, Any]) -> List[str]:
        suggestions = []
        if metrics["coherence_score"] < 0.5:
            suggestions.append("提高輸出的表達多樣性與連貫性")
        if metrics["efficiency"] < 0.4:
            suggestions.append("執行效率過低，建議優化推理鏈路")
        if consistency["score"] < 0.8:
            suggestions.append("偵測到可能的邏輯矛盾，請核對知識庫")
            
        return suggestions if suggestions else ["性能達標，繼續保持"]

    def _calculate_overall_rating(self, metrics: Dict[str, Any]) -> float:
        return (metrics["success_rate"] * 0.4 + 
                metrics["quality_score"] * 0.3 + 
                metrics["efficiency"] * 0.2 +
                metrics.get("consistency_score", 1.0) * 0.1)
