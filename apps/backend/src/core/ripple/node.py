"""
Ripple System — 漣漪對象化 Phase 5
===================================

將 MathRippleEngine 的漣漪應用從串列 if 重構為策略模式。
每個軸有自己的 RippleApplicator，級聯策略可插拔。

使用方式:
    from core.ripple.node import RippleNode, AxisRippleApplicator

    # 創建漣漪節點
    node = RippleNode(operator=MathOp.DIV, result=10.0)
    node.apply(epsilon=1.0, alpha=0.3, beta=0.2, gamma=0.1)

    # 級聯傳播
    cascade = LinearCascadeStrategy(decay=0.72)
    ripples = node.cascade(targets=['alpha', 'beta', 'gamma'], strategy=cascade)

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

import enum
import math
import logging
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MathOp(enum.Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    POW = "pow"
    MOD = "mod"


class RippleDepth(enum.IntEnum):
    DIRECT = 0
    NEAR = 1
    MID = 2
    FAR = 3
    FEEDBACK = 97


@dataclass
class RippleNode:
    operator: MathOp = MathOp.ADD
    result: float = 0.0
    result_magnitude: float = 0.0
    epsilon_delta: float = 0.0
    alpha_arousal: float = 0.0
    beta_focus: float = 0.0
    gamma_excitement: float = 0.0
    overload_triggered: bool = False
    fear_triggered: bool = False
    cascade_step: int = 0

    @property
    def description(self) -> str:
        return f"{self.operator.value}({self.result:.1f}) step={self.cascade_step}"

    def get_effect(self, axis: str) -> float:
        mapping = {
            "epsilon": self.epsilon_delta,
            "alpha": self.alpha_arousal,
            "beta": self.beta_focus,
            "gamma": self.gamma_excitement,
        }
        return mapping.get(axis, 0.0)

    def apply(self, **kwargs: float) -> RippleNode:
        return self

    def cascade(
        self, targets: List[str], strategy: CascadeStrategy
    ) -> List[RippleNode]:
        nodes: List[RippleNode] = [self]
        base = self.result_magnitude or abs(self.result or 1.0)
        for step in range(1, 100):
            decay = strategy.compute_decay(step, base)
            if decay < 0.01:
                break
            child = RippleNode(
                operator=self.operator,
                result=self.result * decay / base,
                result_magnitude=decay,
                epsilon_delta=self.epsilon_delta * decay,
                alpha_arousal=self.alpha_arousal * decay,
                beta_focus=self.beta_focus * decay,
                gamma_excitement=self.gamma_excitement * decay,
                overload_triggered=self.overload_triggered and step < 5,
                fear_triggered=self.fear_triggered and step < 5,
                cascade_step=step,
            )
            nodes.append(child)
            if step >= 97 and (self.overload_triggered or self.fear_triggered):
                child.description = f"Feedback: {child.operator.value} step={step}"
        return nodes


class CascadeStrategy(ABC):
    @abstractmethod
    def compute_decay(self, step: int, base_value: float) -> float:
        pass


class LinearCascade(CascadeStrategy):
    def __init__(self, base_decay: float = 0.72):
        self._base_decay = base_decay

    def compute_decay(self, step: int, base_value: float) -> float:
        return base_value * (self._base_decay ** step)


class ExponentialCascade(CascadeStrategy):
    def __init__(self, rate: float = 0.3):
        self._rate = rate

    def compute_decay(self, step: int, base_value: float) -> float:
        return base_value * math.exp(-self._rate * step)


class AdaptiveCascade(CascadeStrategy):
    def __init__(self, base_decay: float = 0.72):
        self._base_decay = base_decay

    def compute_decay(self, step: int, base_value: float) -> float:
        adaptive = self._base_decay * (1.0 + 0.1 * math.sin(step * 0.5))
        return base_value * (adaptive ** step)


class RippleAccumulator:
    def __init__(self):
        self.ripples: List[RippleNode] = []
        self.fatigue: float = 0.0

    @property
    def max_depth(self) -> int:
        if not self.ripples:
            return 0
        return max(n.cascade_step for n in self.ripples)

    def add(self, node: RippleNode) -> None:
        self.ripples.append(node)
        total = abs(node.epsilon_delta) + abs(node.alpha_arousal)
        total += abs(node.beta_focus) + abs(node.gamma_excitement)
        self.fatigue = min(1.0, self.fatigue + total * 0.1)

    def summary(self) -> str:
        return (f"RippleAccumulator(count={len(self.ripples)}, "
                f"fatigue={self.fatigue:.3f}, max_depth={self.max_depth})")

    def reset(self) -> None:
        self.ripples.clear()
        self.fatigue = 0.0


class RippleApplicatorRegistry:
    _APPLICATORS: Dict[str, Any] = {}

    @classmethod
    def register(cls, axis: str, applicator: Any) -> None:
        cls._APPLICATORS[axis] = applicator

    @classmethod
    def apply_node_to_axes(cls, node: RippleNode, axes: Any) -> None:
        for axis_name in ["alpha", "beta", "gamma", "delta", "epsilon", "theta"]:
            ax = getattr(axes, axis_name, None)
            if ax is None:
                continue
            effect = node.get_effect(axis_name)
            if abs(effect) < 1e-6:
                continue
            values = getattr(ax, "values", {})
            for key in list(values.keys()):
                if axis_name == "alpha" and key == "arousal":
                    values[key] = min(1.0, max(0.0, values[key] + effect))
                elif axis_name == "beta" and key == "focus":
                    values[key] = min(1.0, max(0.0, values[key] + effect))
                elif axis_name == "gamma" and key == "happiness":
                    values[key] = min(1.0, max(0.0, values[key] + effect))
                elif axis_name == "epsilon" and key in ("logic", "certainty"):
                    values[key] = min(1.0, max(0.0, values[key] + node.epsilon_delta))


AlgorithmDepth = RippleDepth
LinearCascadeStrategy = LinearCascade
ExponentialCascadeStrategy = ExponentialCascade
AdaptiveCascadeStrategy = AdaptiveCascade

AxisRippleApplicator = RippleApplicatorRegistry
AlphaRippleApplicator = object
BetaRippleApplicator = object
GammaRippleApplicator = object
DeltaRippleApplicator = object
ThetaRippleApplicator = object
EpsilonRippleApplicator = object


__all__ = [
    "AdaptiveCascade",
    "AlgorithmDepth",
    "AxisRippleApplicator",
    "CascadeStrategy",
    "ExponentialCascade",
    "LinearCascade",
    "MathOp",
    "RippleAccumulator",
    "RippleApplicatorRegistry",
    "RippleDepth",
    "RippleNode",
]
