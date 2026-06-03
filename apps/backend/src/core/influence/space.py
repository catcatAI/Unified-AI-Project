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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from abc import ABC, abstractmethod
from enum import Enum
import math


@dataclass
class InfluenceResult:
    """影響計算結果"""
    source: str
    target: str
    base_strength: float
    spatial_factor: float
    final_influence: float
    rules_applied: List[str]

    def __repr__(self) -> str:
        return f"Influence({self.source}->{self.target}: {self.final_influence:.3f})"


class InfluenceRule(ABC):
    """影響規則抽象基類"""

    name: str = ""

    @abstractmethod
    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """計算影響因子"""
        ...

    def __repr__(self) -> str:
        return f"InfluenceRule({self.name})"


class GravityRule(InfluenceRule):
    """重力規則 — 逆平方定律"""

    def __init__(
        self,
        softening: float = 10.0,
        gravity_constant: float = 25.0,
        min_factor: float = 0.5,
        max_factor: float = 2.0,
    ):
        self.name = "gravity"
        self.softening = softening
        self.gravity_constant = gravity_constant
        self.min_factor = min_factor
        self.max_factor = max_factor

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute a result from inputs."""
        dist = self._distance(source, target)
        raw = self.gravity_constant / (dist * dist + self.softening)
        return max(self.min_factor, min(self.max_factor, raw))

    def _distance(self, source: Any, target: Any) -> float:
        """Distance."""
        if hasattr(source, 'coordinate') and hasattr(target, 'coordinate'):
            sc = source.coordinate
            tc = target.coordinate
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(sc, tc)))
        return 1.0


class EntropyRule(InfluenceRule):
    """熵規則 — 高熵軸對周圍軸影響更強"""

    def __init__(self, weight: float = 0.2, entropy_threshold: float = 0.6):
        self.name = "entropy"
        self.weight = weight
        self.entropy_threshold = entropy_threshold

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute a result from inputs."""
        source_entropy = self._compute_entropy(source)
        if source_entropy > self.entropy_threshold:
            return base_strength * (1.0 + self.weight)
        return base_strength

    def _compute_entropy(self, axis: Any) -> float:
        """Compute entropy."""
        if hasattr(axis, 'values') and axis.values:
            values = list(axis.values.values())
            total = sum(values)
            if total <= 0:
                return 0.0
            probs = [v / total for v in values]
            return -sum(p * math.log(p + 1e-10) for p in probs if p > 0)
        return 0.5


class MemoryRule(InfluenceRule):
    """記憶規則 — 歷史影響的衰減和強化"""

    def __init__(self, weight: float = 0.15, history_trend: float = 0.0):
        self.name = "memory"
        self.weight = weight
        self.history_trend = history_trend

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute a result from inputs."""
        if context and 'history_trend' in context:
            trend = context['history_trend']
            if trend > 0.05:
                return base_strength * (1.0 + self.weight)
            elif trend < -0.05:
                return base_strength * (1.0 - self.weight * 0.5)
        return base_strength


class WeightRule(InfluenceRule):
    """權重規則 — 軸權重影響"""

    def __init__(self, weight_power: float = 1.0):
        self.name = "weight"
        self.weight_power = weight_power

    def compute(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compute a result from inputs."""
        source_w = getattr(source, 'weight', 1.0)
        target_w = getattr(target, 'weight', 1.0)
        weight_factor = (source_w ** self.weight_power) * (target_w ** self.weight_power)
        return base_strength * weight_factor


class ConflictStrategy(Enum):
    """規則衝突解決策略"""
    FIRST_WINS = "first"
    LAST_WINS = "last"
    MAX = "max"
    MIN = "min"
    AVERAGE = "average"
    ENTROPY_WEIGHTED = "entropy_weighted"


class InfluenceRuleSet:
    """
    規則集合 — 管理多個影響規則的組合
    """

    def __init__(
        self,
        strategy: ConflictStrategy = ConflictStrategy.ENTROPY_WEIGHTED,
    ):
        self._rules: List[InfluenceRule] = []
        self._strategy = strategy
        self._weights: Dict[str, float] = {}

    def add(self, rule: InfluenceRule, weight: float = 1.0) -> "InfluenceRuleSet":
        """Execute the add operation."""
        self._rules.append(rule)
        self._weights[rule.name] = weight
        return self

    def remove(self, rule_name: str) -> bool:
        """Execute the remove operation."""
        for i, r in enumerate(self._rules):
            if r.name == rule_name:
                self._rules.pop(i)
                self._weights.pop(rule_name, None)
                return True
        return False

    def compute_all(
        self,
        source: Any,
        target: Any,
        base_strength: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, List[str]]:
        """Compute all."""
        if not self._rules:
            return base_strength, []

        raw_factors = []
        rule_names = []

        for rule in self._rules:
            factor = rule.compute(source, target, base_strength, context)
            raw_factors.append(factor)
            rule_names.append(rule.name)

        final = self._resolve(raw_factors, context)
        return final, rule_names

    def _resolve(self, factors: List[float], context: Optional[Dict[str, Any]]) -> float:
        """Resolve."""
        if not factors:
            return 0.0

        if self._strategy == ConflictStrategy.FIRST_WINS:
            return factors[0]
        elif self._strategy == ConflictStrategy.LAST_WINS:
            return factors[-1]
        elif self._strategy == ConflictStrategy.MAX:
            return max(factors)
        elif self._strategy == ConflictStrategy.MIN:
            return min(factors)
        elif self._strategy == ConflictStrategy.AVERAGE:
            return sum(factors) / len(factors)
        elif self._strategy == ConflictStrategy.ENTROPY_WEIGHTED:
            total_w = sum(self._weights.get(r, 1.0) for r in self._weights)
            return sum(f * self._weights.get(r, 1.0) for f, r in zip(factors, self._weights)) / total_w

        return sum(factors) / len(factors)

    def __repr__(self) -> str:
        return f"InfluenceRuleSet({[r.name for r in self._rules]})"


class InfluenceSpace:
    """
    影響空間
    ========

    將軸間影響從硬編碼矩陣替換為規則化計算。
    每個 source-target 軸對通過規則集計算實際影響力。

    替代：
        computed[source][target] = base_strength * source_avg * weight * spatial_factor

    現在：
        influence = space.compute(source=alpha, target=gamma)
    """

    def __init__(
        self,
        axes: Optional[Dict[str, Any]] = None,
        base_matrix: Optional[Dict[str, Dict[str, float]]] = None,
        rules: Optional[InfluenceRuleSet] = None,
        softening: float = 10.0,
    ):
        self._axes: Dict[str, Any] = axes or {}
        self._base_matrix: Dict[str, Dict[str, float]] = base_matrix or {}
        self._rules = rules or InfluenceRuleSet()
        self._softening = softening

        self._cache: Dict[Tuple[str, str], float] = {}
        self._cache_enabled = True

    def register_axis(self, name: str, axis: Any) -> None:
        """註冊一個軸"""
        self._axes[name] = axis

    def set_base_matrix(self, matrix: Dict[str, Dict[str, float]]) -> None:
        """設定基礎影響矩陣"""
        self._base_matrix = matrix
        self._cache.clear()

    def add_rule(self, rule: InfluenceRule, weight: float = 1.0) -> "InfluenceSpace":
        """Add a rule."""
        self._rules.add(rule, weight)
        self._cache.clear()
        return self

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule."""
        result = self._rules.remove(rule_name)
        self._cache.clear()
        return result

    def compute(
        self,
        source_name: str,
        target_name: str,
        context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> float:
        """
        計算 source → target 的影響力

        Args:
            source_name: 源軸名
            target_name: 目標軸名
            context: 額外上下文（history_trend 等）
            use_cache: 是否使用緩存

        Returns:
            影響力值
        """
        cache_key = (source_name, target_name)
        if use_cache and self._cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]

        source = self._axes.get(source_name)
        target = self._axes.get(target_name)

        if source is None or target is None:
            return 0.0

        base_strength = self._base_matrix.get(source_name, {}).get(target_name, 0.0)
        if base_strength == 0.0:
            return 0.0

        source_avg = getattr(source, 'get_average', lambda: 0.5)()
        source_weight = getattr(source, 'weight', 1.0)
        target_weight = getattr(target, 'weight', 1.0)

        base = base_strength * source_avg * source_weight * target_weight

        if self._rules._rules:
            final, _ = self._rules.compute_all(source, target, base, context)
        else:
            final = base

        if self._cache_enabled:
            self._cache[cache_key] = final

        return final

    def compute_all(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
        """
        計算所有軸對的影響力

        Returns:
            {source: {target: influence}}
        """
        result: Dict[str, Dict[str, float]] = {}

        for source_name in self._axes:
            result[source_name] = {}
            for target_name in self._axes:
                if source_name != target_name:
                    result[source_name][target_name] = self.compute(source_name, target_name, context)

        return result

    def apply_influences(
        self,
        matrix: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """
        將計算出的影響力實際應用到 StateMatrix4D

        Returns:
            應用結果摘要
        """
        computed = self.compute_all(context)
        results = {}

        for source_name, targets in computed.items():
            results[source_name] = {}
            source_dim = getattr(matrix, source_name, None)
            if source_dim is None:
                continue
            source_dim.get_average()

            for target_name, influence in targets.items():
                target_dim = getattr(matrix, target_name, None)
                if target_dim is None:
                    continue

                applied_influence = influence
                target_dim.values["trust"] = min(
                    1.0, target_dim.values.get("trust", 0.5) + applied_influence * 0.01
                )
                results[source_name][target_name] = applied_influence

        return results

    def invalidate_cache(self) -> None:
        """清除緩存"""
        self._cache.clear()

    def __repr__(self) -> str:
        n_axes = len(self._axes)
        n_rules = len(self._rules._rules)
        return f"InfluenceSpace(axes={n_axes}, rules={n_rules})"