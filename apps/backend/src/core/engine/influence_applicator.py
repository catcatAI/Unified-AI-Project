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
    "epsilon": {
        "alpha": [
            ("logic", "energy", 0.05),
            ("precision", "tension", 0.08),
            ("fatigue", "rest_need", 0.1),
        ],
        "beta": [
            ("logic", "clarity", 0.08),
            ("precision", "focus", 0.06),
            ("complexity", "confusion", 0.05),
        ],
        "gamma": [
            ("precision", "calm", 0.05),
            ("fatigue", "sadness", 0.06),
            ("abstraction", "creativity", 0.08),
        ],
        "delta": [
            ("logic", "attention", 0.05),
            ("precision", "bond", 0.03),
        ],
        "theta": [
            ("certainty", "ambiguity", -0.08),
            ("complexity", "novelty", 0.06),
        ],
    },
    "theta": {
        "alpha": [
            ("novelty", "arousal", 0.08),
            ("theta_negativity", "tension", 0.12),
        ],
        "beta": [
            ("novelty", "curiosity", 0.1),
            ("complexity", "complexity", 0.05),
        ],
        "gamma": [
            ("theta_negativity", "sadness", 0.08),
            ("novelty", "surprise", 0.1),
        ],
        "delta": [
            ("novelty", "attention", 0.08),
            ("ambiguity", "bond", -0.05),
        ],
        "epsilon": [
            ("novelty", "abstraction", 0.06),
            ("theta_negativity", "fatigue", 0.05),
        ],
    },
    "zeta": {
        "alpha": [
            ("temporal_coherence", "vitality", 0.06),
            ("identity_continuity", "comfort", 0.05),
        ],
        "beta": [
            ("narrative_flow", "creativity", 0.08),
            ("memory_depth", "clarity", 0.07),
        ],
        "gamma": [
            ("identity_continuity", "trust", 0.08),
            ("temporal_coherence", "calm", 0.06),
        ],
        "delta": [
            ("memory_depth", "bond", 0.07),
            ("narrative_flow", "presence", 0.06),
        ],
        "epsilon": [
            ("temporal_coherence", "certainty", 0.06),
        ],
        "theta": [
            ("memory_depth", "novelty", 0.05),
            ("identity_continuity", "dimension_fit", 0.06),
        ],
    },
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
    """Get the singleton InfluenceApplicator instance."""
    global _default_applicator
    if _default_applicator is None:
        _default_applicator = InfluenceApplicator()
    return _default_applicator