"""
Influence Applicator — 軸間影響應用器
====================================

將 state_matrix.py 的 _apply_influence() 串列 if-elif 重構為配置驅動的應用器。
每個 source->target 組合定義一組 field-level 影響權重。

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional


InfluenceRules = Dict[str, Dict[str, List[Tuple[str, str, float]]]]

INFLUENCE_RULES: InfluenceRules = {
    "alpha": {
        "beta": [
            ("energy", "focus", 0.1),
            ("energy", "clarity", 0.08),
            ("comfort", "happiness", 0.1),
            ("comfort", "calm", 0.08),
            ("arousal", "focus", 0.05),
        ],
        "gamma": [
            ("comfort", "happiness", 0.1),
            ("comfort", "calm", 0.08),
            ("energy", "vitality", 0.05),
        ],
        "delta": [
            ("comfort", "engagement", 0.08),
            ("comfort", "presence", 0.05),
        ],
    },
    "beta": {
        "alpha": [
            ("focus", "arousal", 0.05),
            ("focus", "energy", 0.03),
        ],
        "gamma": [
            ("focus", "focus", 0.1),
            ("curiosity", "anticipation", 0.05),
        ],
        "delta": [
            ("curiosity", "attention", 0.1),
        ],
    },
    "gamma": {
        "alpha": [
            ("happiness", "energy", 0.1),
            ("happiness", "comfort", 0.08),
            ("happiness", "tension", -0.1),
            ("fear", "tension", 0.15),
            ("calm", "focus", 0.1),
        ],
        "beta": [
            ("calm", "focus", 0.1),
            ("fear", "confusion", 0.15),
        ],
        "delta": [
            ("happiness", "engagement", 0.1),
            ("happiness", "presence", 0.08),
            ("happiness", "happiness", 0.12),
        ],
    },
    "delta": {
        "gamma": [
            ("bond", "happiness", 0.12),
            ("bond", "trust", 0.1),
        ],
        "beta": [
            ("attention", "focus", 0.05),
        ],
    },
    "epsilon": {},
    "theta": {},
}


def apply_influence_to_axis(
    source_values: Dict[str, float],
    target_dim: Any,
    rules: List[Tuple[str, str, float]],
    amount: float = 1.0,
) -> None:
    """
    應用一組影響規則到目標軸

    Args:
        source_values: 源軸的 field 值字典
        target_dim: 目標軸（DimensionState）
        rules: (source_field, target_field, weight) 列表
        amount: 影響強度因子（原 compute_influences 的計算結果）
    """
    for src_field, tgt_field, weight in rules:
        if src_field not in source_values:
            continue
        src_val = source_values.get(src_field, 0.5)
        target_dim.values[tgt_field] = min(
            1.0, max(0.0, target_dim.values.get(tgt_field, 0.5) + amount * weight * src_val)
        )


class InfluenceApplicator:
    """
    軸間影響應用器

    將 compute_influences() 的 _apply_influence() 邏輯外化為配置。
    """

    def __init__(self, rules: Optional[InfluenceRules] = None):
        self._rules = rules or INFLUENCE_RULES

    def apply(
        self,
        source: str,
        target: str,
        source_dim: Any,
        target_dim: Any,
        amount: float,
    ) -> None:
        """將 source -> target 的影響應用到軸狀態"""
        if source not in self._rules:
            return
        if target not in self._rules[source]:
            return
        rules = self._rules[source][target]
        if not rules:
            return
        apply_influence_to_axis(source_dim.values, target_dim, rules, amount=amount)


_default_applicator: Optional[InfluenceApplicator] = None


def get_applicator() -> InfluenceApplicator:
    global _default_applicator
    if _default_applicator is None:
        _default_applicator = InfluenceApplicator()
    return _default_applicator