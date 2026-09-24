"""
Alignment Manager - 协调三大支柱系统的核心管理器

负责协调理智系统、感性系统和存在系统之间的平衡,
并通过决策论系统将三者的输出转化为最终行动。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AlignmentManager:
    """Core manager for coordinating the three pillar systems."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.constraints: Dict[str, Any] = {
            "max_risk_score": 0.7,
            "required_value_alignment": 0.8,
            "ethical_boundaries": ["no_harm", "honesty", "fairness"],
        }
        self.alignment_history: List[Dict[str, Any]] = []
        logger.debug("AlignmentManager initialized")

    def check_alignment(self, action: Any) -> bool:
        score = self.get_alignment_score(action)
        return bool(score >= self.constraints["required_value_alignment"])

    def get_alignment_score(self, action: Any) -> float:
        if not isinstance(action, dict):
            action = {"action": str(action)}
        base: float = self.constraints["required_value_alignment"]
        risk: float = action.get("risk", 0.0)
        adjustment = (1.0 - risk) * 0.2
        score = min(1.0, base + adjustment)
        self.alignment_history.append({"action": action, "score": score})
        return score

    def get_constraints(self) -> Dict[str, Any]:
        return dict(self.constraints)

    def get_status(self) -> Dict[str, Any]:
        """获取对齐管理器状态"""
        return {
            "system_id": self.config.get("system_id", "unknown"),
            "has_reasoning": self.config.get("reasoning_system") is not None,
            "has_emotion": self.config.get("emotion_system") is not None,
            "has_ontology": self.config.get("ontology_system") is not None,
            "constraints_count": len(self.constraints),
            "alignment_history_count": len(self.alignment_history),
        }


__all__ = ["AlignmentManager"]
