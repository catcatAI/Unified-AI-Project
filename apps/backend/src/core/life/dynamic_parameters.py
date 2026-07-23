"""
Angela AI v6.0 - 动态参数系统
Dynamic Parameter System

将硬编码的固定参数改为动态调整，模拟生命的不确定性。

核心概念：
- 参数不是固定的，而是随时间、状态、经验动态变化
- 人类有时容易高兴，有时不容易（情绪阈值动态变化）
- 行为有时成功，有时失败（执行成功率动态变化）
- 能力有时觉得能做到，有时觉得不能（自我效能感动态变化）
- 通过其他参数的干涉，效果有大有小

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DynamicThresholdManager:
    """Dynamic threshold/parameter manager for adaptive behavior thresholds."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._parameters: Dict[str, float] = {
            "emotion_happiness_threshold": 0.6,
            "emotion_sadness_threshold": 0.5,
            "emotion_anger_threshold": 0.5,
            "social_initiative_threshold": 0.5,
        }
        self._parameters.update(self.config.get("thresholds", {}))

    def get_parameter(self, param_name: str, context: Optional[Dict[str, float]] = None) -> float:
        """Get dynamic parameter value, optionally adjusted by context."""
        base_value = self._parameters.get(param_name, 0.5)
        if context:
            # Simple context adjustment: average of context values shifts threshold
            ctx_adjustment = sum(context.values()) / max(len(context), 1) * 0.1
            return max(0.0, min(1.0, base_value + ctx_adjustment))
        return base_value

    def set_parameter(self, param_name: str, value: float) -> None:
        """Set a parameter value."""
        self._parameters[param_name] = max(0.0, min(1.0, value))

    def update_from_state_matrix(self, state_matrix: Any) -> None:
        """Update parameters from state matrix values."""
        if state_matrix is None:
            return
        try:
            alpha = getattr(state_matrix, "alpha", None)
            if alpha is not None:
                energy = alpha.values.get("energy", 0.5)
                self._parameters["emotion_happiness_threshold"] = max(
                    0.1, min(0.9, 0.6 - energy * 0.2)
                )
                self._parameters["emotion_anger_threshold"] = max(0.1, min(0.9, 0.5 + energy * 0.1))

            gamma = getattr(state_matrix, "gamma", None)
            if gamma is not None:
                happiness = gamma.values.get("happiness", 0.5)
                self._parameters["emotion_sadness_threshold"] = max(
                    0.1, min(0.9, 0.5 - happiness * 0.2)
                )

            beta = getattr(state_matrix, "beta", None)
            if beta is not None:
                curiosity = beta.values.get("curiosity", 0.5)
                self._parameters["social_initiative_threshold"] = max(
                    0.1, min(0.9, 0.5 + curiosity * 0.2)
                )
        except Exception:
            logger.warning("Failed to update from state matrix", exc_info=True)
