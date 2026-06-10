"""
记忆学习引擎
============
记录用户反馈并优化回應模板

设计目标：
1. 记录用户对回應的反馈
2. 使用移动平均更新成功率
3. 分析成功回應模式
4. 建议新的回應模板
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryLearningEngine:
    """Records user feedback and optimizes response templates."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.feedback_history: List[Dict[str, Any]] = []
        self.template_stats: Dict[str, Dict[str, float]] = {}

    def record_feedback(self, template_id: str, success: bool, context: Optional[Dict[str, Any]] = None) -> None:
        self.feedback_history.append({
            "template_id": template_id,
            "success": success,
            "context": context or {},
        })
        stats = self.template_stats.setdefault(template_id, {"total": 0, "success": 0.0})
        stats["total"] += 1
        stats["success"] = (stats["success"] * (stats["total"] - 1) + (1.0 if success else 0.0)) / stats["total"]

    def get_success_rate(self, template_id: str) -> float:
        stats = self.template_stats.get(template_id)
        return stats["success"] if stats else 0.0

    def suggest_improvements(self, min_samples: int = 3) -> List[Dict[str, Any]]:
        suggestions = []
        for tid, stats in self.template_stats.items():
            if stats["total"] >= min_samples and stats["success"] < 0.5:
                suggestions.append({"template_id": tid, "success_rate": stats["success"], "suggestion": "needs improvement"})
        return suggestions


__all__ = ["MemoryLearningEngine"]
