"""
Influence Space — 影響規則抽象 Phase 6
========================================

將硬編碼的影響矩陣重構為可配置、可組合的規則系統。
支援：
- GravityRule（逆平方定律）
- EntropyRule（熵驅動）
- MemoryRule（記憶衰減）
- 規則衝突解決策略

使用方式:
    from core.influence.space import InfluenceSpace, GravityRule

    space = InfluenceSpace()
    space.rules.add(GravityRule())

    influence = space.compute(source=alpha, target=beta)
    computed = space.compute_all(matrix)  # 對所有軸對

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

import enum
import math
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConflictStrategy(enum.Enum):
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MAX = "max"
    MIN = "min"
    AVERAGE = "average"
    ENTROPY_WEIGHTED = "entropy_weighted"


class InfluenceRule:
    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        raise NotImplementedError


@dataclass
class InfluenceResult:
    source: str = ""
    target: str = ""
    value: float = 0.0
    rules_applied: List[str] = field(default_factory=list)


class GravityRule(InfluenceRule):
    def __init__(self, softening: float = 10.0, gravity_constant: float = 25.0):
        self._softening = softening
        self._gravity_constant = gravity_constant

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        src_coord = getattr(source, "coordinate", [0.0] * 5)
        tgt_coord = getattr(target, "coordinate", [0.0] * 5)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(src_coord, tgt_coord)))
        return self._gravity_constant / (dist + self._softening)


class EntropyRule(InfluenceRule):
    def __init__(self, weight: float = 0.2):
        self._weight = weight

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        src_vals = list(getattr(source, "values", {}).values()) if hasattr(source, "values") else [0.5] * 4
        if not src_vals:
            return base_strength
        total = sum(abs(v) for v in src_vals) or 1.0
        probs = [abs(v) / total for v in src_vals]
        entropy = -sum(p * math.log(p + 1e-10) for p in probs) / math.log(len(probs))
        return base_strength * (1.0 + self._weight * entropy)


class MemoryRule(InfluenceRule):
    def __init__(self, weight: float = 0.15):
        self._weight = weight

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        trend = (context or {}).get("history_trend", 0.0)
        return base_strength * (1.0 + self._weight * trend)


class WeightRule(InfluenceRule):
    def __init__(self, weight: float = 1.0):
        self._weight = weight

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        src_w = getattr(source, "weight", 1.0) if hasattr(source, "weight") else 1.0
        tgt_w = getattr(target, "weight", 1.0) if hasattr(target, "weight") else 1.0
        return base_strength * (src_w * tgt_w) * self._weight


class InfluenceRuleSet:
    def __init__(self, strategy: ConflictStrategy = ConflictStrategy.AVERAGE):
        self._rules: List[InfluenceRule] = []
        self._strategy = strategy

    def add(self, rule: InfluenceRule) -> None:
        self._rules.append(rule)

    def compute_all(
        self,
        source: Any,
        target: Any,
        base: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, List[str]]:
        factors: List[float] = []
        names: List[str] = []
        ctx = context or {}
        for rule in self._rules:
            f = rule.compute(source, target, base, ctx)
            factors.append(f)
            names.append(rule.__class__.__name__)
        if not factors:
            return base, []
        resolved = self._resolve(factors, ctx)
        return resolved, names

    def _resolve(
        self, factors: List[float], context: Optional[Dict[str, Any]] = None
    ) -> float:
        if not factors:
            return 0.0
        if self._strategy == ConflictStrategy.FIRST_WINS:
            return factors[0]
        if self._strategy == ConflictStrategy.LAST_WINS:
            return factors[-1]
        if self._strategy == ConflictStrategy.MAX:
            return max(factors)
        if self._strategy == ConflictStrategy.MIN:
            return min(factors)
        if self._strategy == ConflictStrategy.AVERAGE:
            return sum(factors) / len(factors)
        if self._strategy == ConflictStrategy.ENTROPY_WEIGHTED:
            total = sum(factors)
            if total == 0:
                return 0.0
            probs = [f / total for f in factors]
            ent = -sum(p * math.log(p + 1e-10) for p in probs)
            weights = [1.0 + ent - p for p in probs]
            w_total = sum(weights)
            return sum(f * w for f, w in zip(factors, weights)) / w_total
        return factors[0]


class InfluenceSpace:
    def __init__(
        self,
        axes: Optional[Dict[str, Any]] = None,
        base_matrix: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        self._axes = axes or {}
        self._base_matrix = base_matrix or {}
        self._rules = InfluenceRuleSet()
        self._cache: Dict[Tuple[str, str], float] = {}

    @property
    def rules(self) -> InfluenceRuleSet:
        return self._rules

    def add_rule(self, rule: InfluenceRule) -> None:
        self._rules.add(rule)

    def compute(
        self, source: str, target: str, use_cache: bool = True
    ) -> float:
        key = (source, target)
        if use_cache and key in self._cache:
            return self._cache[key]

        src_ax = self._axes.get(source)
        tgt_ax = self._axes.get(target)
        base = self._base_matrix.get(source, {}).get(target, 0.0)

        result, _ = self._rules.compute_all(src_ax, tgt_ax, base)
        self._cache[key] = result
        return result

    def compute_all(self) -> Dict[str, Dict[str, float]]:
        result: Dict[str, Dict[str, float]] = {}
        for src_name in self._axes:
            result[src_name] = {}
            for tgt_name in self._axes:
                if src_name != tgt_name:
                    result[src_name][tgt_name] = self.compute(src_name, tgt_name)
        return result

    def invalidate_cache(self) -> None:
        self._cache.clear()

    def __repr__(self) -> str:
        return (f"InfluenceSpace(axes={len(self._axes)}, "
                f"rules={len(self._rules._rules)}, "
                f"cached={len(self._cache)} pairs)")


__all__ = [
    "ConflictStrategy",
    "EntropyRule",
    "GravityRule",
    "InfluenceResult",
    "InfluenceRule",
    "InfluenceRuleSet",
    "InfluenceSpace",
    "MemoryRule",
    "WeightRule",
]
