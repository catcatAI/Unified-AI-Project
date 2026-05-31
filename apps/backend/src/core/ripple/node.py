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
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Protocol, Callable
from enum import Enum
import logging
import math

logger = logging.getLogger(__name__)


class MathOp(Enum):
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    POW = "pow"
    SQRT = "sqrt"


class RippleDepth(Enum):
    D3 = 3
    D4 = 4
    D5 = 5
    D6 = 6
    D7 = 7

    @property
    def target_axes(self) -> List[str]:
        base = ["alpha", "beta", "gamma"]
        if self.value >= 4:
            base.append("delta")
        if self.value >= 5:
            base.append("theta")
        if self.value >= 6:
            base.append("epsilon")
        return base

    @property
    def cascade_decay(self) -> float:
        return 0.7 + (self.value - 3) * 0.02

    @property
    def feedback_enabled(self) -> bool:
        return self.value >= 6


class AlgorithmDepth(Enum):
    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    ULTRA = "ultra"


@dataclass
class RippleNode:
    """
    漣漪節點 — 攜帶效應和應用器

    取代 RippleEffect，不再依賴串列 if 應用到軸。
    """

    operator: MathOp
    operand_a: float = 0.0
    operand_b: Optional[float] = None
    result: float = 0.0
    result_magnitude: float = 0.0

    epsilon_delta: float = 0.0
    alpha_arousal: float = 0.0
    beta_focus: float = 0.0
    gamma_excitement: float = 0.0
    delta_engagement: float = 0.0
    theta_delta: float = 0.0

    fear_triggered: bool = False
    overload_triggered: bool = False
    confusion_triggered: bool = False

    ripple_depth: RippleDepth = RippleDepth.D3
    algorithm_depth: AlgorithmDepth = AlgorithmDepth.LIGHT
    cascade_step: int = 0
    cascade_decay_factor: float = 1.0
    depth_multiplier: float = 1.0
    description: str = ""
    feedback_ripples: List["RippleNode"] = field(default_factory=list)

    def apply(
        self,
        epsilon: float = 0.0,
        alpha: float = 0.0,
        beta: float = 0.0,
        gamma: float = 0.0,
        delta: float = 0.0,
        theta: float = 0.0,
    ) -> "RippleNode":
        """設定各軸效應"""
        self.epsilon_delta = epsilon
        self.alpha_arousal = alpha
        self.beta_focus = beta
        self.gamma_excitement = gamma
        self.delta_engagement = delta
        self.theta_delta = theta
        return self

    def get_effect(self, axis: str) -> float:
        """取得指定軸的效應值"""
        effects = {
            "epsilon": self.epsilon_delta,
            "alpha": self.alpha_arousal,
            "beta": self.beta_focus,
            "gamma": self.gamma_excitement,
            "delta": self.delta_engagement,
            "theta": self.theta_delta,
        }
        return effects.get(axis, 0.0)

    def cascade(
        self,
        targets: List[str],
        strategy: Optional["CascadeStrategy"] = None,
        source_axis: str = "epsilon",
    ) -> List["RippleNode"]:
        """
        將漣漪級聯傳播到多個軸

        Args:
            targets: 目標軸列表
            strategy: 級聯策略（預設 LinearCascade）
            source_axis: 源軸（預設 epsilon，即數學計算軸）

        Returns:
            級聯產生的所有 RippleNode（含源節點）
        """
        if strategy is None:
            strategy = LinearCascade()

        all_nodes = [self]
        source_effect = self.get_effect(source_axis)

        for step, target in enumerate(targets):
            if target == source_axis:
                continue

            decay = strategy.compute_decay(step + 1, source_effect)
            effect_val = self.get_effect(source_axis) * decay * self.depth_multiplier

            child = RippleNode(
                operator=self.operator,
                result=self.result,
                ripple_depth=self.ripple_depth,
                algorithm_depth=self.algorithm_depth,
                cascade_step=step + 1,
                cascade_decay_factor=decay,
                depth_multiplier=self.depth_multiplier,
                description=f"[CASCADE-{step + 1}] {target} axis (decay={decay:.3f})",
            )

            if target == "alpha":
                child.alpha_arousal = effect_val
            elif target == "beta":
                child.beta_focus = effect_val
            elif target == "gamma":
                child.gamma_excitement = effect_val
            elif target == "delta":
                child.delta_engagement = effect_val
            elif target == "theta":
                child.theta_delta = effect_val * 0.5

            all_nodes.append(child)

        if self.ripple_depth.feedback_enabled and self.overload_triggered:
            feedback = self._compute_feedback()
            all_nodes.extend(feedback)
            self.feedback_ripples = feedback

        return all_nodes

    def _compute_feedback(self) -> List["RippleNode"]:
        """計算反饋漣漪（深度6-7時觸發）"""
        feedback = []

        if self.overload_triggered:
            fb = RippleNode(
                operator=self.operator,
                result=self.result_magnitude * 0.5,
                cascade_step=99,
                cascade_decay_factor=0.3,
                description="[FEEDBACK] Overload decay",
            )
            fb.beta_focus = 0.4
            fb.gamma_excitement = 0.2
            feedback.append(fb)

        if self.fear_triggered:
            fb = RippleNode(
                operator=self.operator,
                result=0.0,
                cascade_step=98,
                cascade_decay_factor=0.2,
                description="[FEEDBACK] Fear suppression",
            )
            fb.gamma_excitement = 0.3
            fb.beta_focus = 0.2
            feedback.append(fb)

        if self.confusion_triggered:
            fb = RippleNode(
                operator=self.operator,
                result=self.result,
                cascade_step=97,
                cascade_decay_factor=0.25,
                description="[FEEDBACK] Confusion clarification",
            )
            fb.beta_focus = 0.3
            feedback.append(fb)

        return feedback

    def __repr__(self) -> str:
        return f"RippleNode({self.operator.value}, step={self.cascade_step}, {self.description})"


class CascadeStrategy(Protocol):
    """級聯策略協議"""

    def compute_decay(self, step: int, base_effect: float) -> float:
        """計算第 step 層的衰減因子"""
        ...


class LinearCascade:
    """線性衰減策略（現有預設）"""

    def __init__(self, base_decay: float = 0.72):
        self.base_decay = base_decay

    def compute_decay(self, step: int, base_effect: float = 1.0) -> float:
        return self.base_decay ** step


class ExponentialCascade:
    """指數衰減策略"""

    def __init__(self, rate: float = 0.3):
        self.rate = rate

    def compute_decay(self, step: int, base_effect: float = 1.0) -> float:
        return math.exp(-step * self.rate)


class AdaptiveCascade:
    """自適應衰減策略（根據情緒狀態動態調整）"""

    def __init__(self, base_decay: float = 0.72, state_getter: Optional[Callable[[], float]] = None):
        self.base_decay = base_decay
        self._state_getter = state_getter or (lambda: 0.5)

    def compute_decay(self, step: int, base_effect: float = 1.0) -> float:
        emotion_state = self._state_getter()
        adaptive_factor = 1.0 + emotion_state * 0.1
        return (self.base_decay * adaptive_factor) ** step


class AxisRippleApplicator:
    """
    軸漣漪應用器 — 將 RippleNode 的效應應用到軸狀態

    每個軸一個應用器，取代 RippleCascade._apply_ripple_to_axis 的串列 if。
    """

    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        """將漣漪效應應用到軸狀態"""
        logger.warning("[AxisRippleApplicator.apply] Not implemented — stub")


class AlphaRippleApplicator(AxisRippleApplicator):
    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        if not axis_state or not hasattr(axis_state, "values"):
            return
        if ripple.alpha_arousal > 0:
            axis_state.values["arousal"] = min(
                1.0, axis_state.values.get("arousal", 0.5) + ripple.alpha_arousal
            )
        if ripple.cascade_step > 0:
            energy = axis_state.values.get("energy", 0.5)
            axis_state.values["energy"] = min(1.0, energy + ripple.alpha_arousal * 0.5)


class BetaRippleApplicator(AxisRippleApplicator):
    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        if not axis_state or not hasattr(axis_state, "values"):
            return
        if ripple.beta_focus > 0:
            axis_state.values["focus"] = min(
                1.0, axis_state.values.get("focus", 0.5) + ripple.beta_focus
            )
        if ripple.confusion_triggered:
            confusion = axis_state.values.get("confusion", 0.0)
            axis_state.values["confusion"] = max(0.0, confusion - ripple.beta_focus * 0.3)


class GammaRippleApplicator(AxisRippleApplicator):
    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        if not axis_state or not hasattr(axis_state, "values"):
            return
        if ripple.gamma_excitement > 0:
            axis_state.values["happiness"] = min(
                1.0, axis_state.values.get("happiness", 0.5) + ripple.gamma_excitement
            )
        if ripple.fear_triggered:
            fear = axis_state.values.get("fear", 0.0)
            axis_state.values["fear"] = min(1.0, fear + 0.1)
        if ripple.overload_triggered:
            surprise = axis_state.values.get("surprise", 0.0)
            axis_state.values["surprise"] = min(1.0, surprise + 0.2)


class DeltaRippleApplicator(AxisRippleApplicator):
    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        if not axis_state or not hasattr(axis_state, "values"):
            return
        if ripple.delta_engagement > 0:
            axis_state.values["bond"] = min(
                1.0, axis_state.values.get("bond", 0.5) + ripple.delta_engagement
            )
            axis_state.values["engagement"] = min(
                1.0, axis_state.values.get("engagement", 0.5) + ripple.delta_engagement * 0.5
            )


class ThetaRippleApplicator(AxisRippleApplicator):
    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        if not axis_state or not hasattr(axis_state, "values"):
            return
        if ripple.theta_delta > 0:
            novelty = axis_state.values.get("novelty", 0.5)
            axis_state.values["novelty"] = min(1.0, novelty + ripple.theta_delta * 0.2)


class EpsilonRippleApplicator(AxisRippleApplicator):
    def apply(self, ripple: RippleNode, axis_state: Any) -> None:
        if not axis_state or not hasattr(axis_state, "values"):
            return
        if ripple.epsilon_delta > 0:
            logic = axis_state.values.get("logic", 0.5)
            axis_state.values["logic"] = min(1.0, logic + ripple.epsilon_delta * 0.3)
            certainty = axis_state.values.get("certainty", 0.5)
            axis_state.values["certainty"] = min(1.0, certainty + ripple.epsilon_delta * 0.2)


class RippleApplicatorRegistry:
    """全局應用器註冊表"""

    _registry: Dict[str, AxisRippleApplicator] = {
        "alpha": AlphaRippleApplicator(),
        "beta": BetaRippleApplicator(),
        "gamma": GammaRippleApplicator(),
        "delta": DeltaRippleApplicator(),
        "theta": ThetaRippleApplicator(),
        "epsilon": EpsilonRippleApplicator(),
    }

    @classmethod
    def get(cls, axis: str) -> Optional[AxisRippleApplicator]:
        return cls._registry.get(axis)

    @classmethod
    def apply_all(cls, ripple: RippleNode, axis_states: Dict[str, Any]) -> None:
        """將一個漣漪應用到所有軸"""
        for axis_name, axis_state in axis_states.items():
            applicator = cls.get(axis_name)
            if applicator:
                applicator.apply(ripple, axis_state)

    @classmethod
    def apply_node_to_axes(cls, ripple: RippleNode, matrix: Any) -> None:
        """將 RippleNode 應用到 StateMatrix4D"""
        if matrix is None:
            return
        for axis_name in ["alpha", "beta", "gamma", "delta", "epsilon", "theta"]:
            if hasattr(matrix, axis_name):
                applicator = cls.get(axis_name)
                if applicator:
                    applicator.apply(ripple, getattr(matrix, axis_name))


@dataclass
class RippleAccumulator:
    """漣漪累積器 — 追蹤連續運算的總效應"""

    ripples: List[RippleNode] = field(default_factory=list)
    cumulative_epsilon: float = 0.0
    cumulative_arousal: float = 0.0
    cumulative_excitement: float = 0.0
    fatigue: float = 0.0
    chain_broken: bool = False
    max_depth: int = 3

    def add(self, ripple: RippleNode) -> None:
        self.ripples.append(ripple)
        self.cumulative_epsilon += abs(ripple.epsilon_delta)
        self.cumulative_arousal += ripple.alpha_arousal
        self.cumulative_excitement += ripple.gamma_excitement
        self.fatigue = min(1.0, len(self.ripples) * 0.03)
        if ripple.cascade_step > self.max_depth:
            self.max_depth = ripple.cascade_step

    def reset(self) -> None:
        self.ripples.clear()
        self.cumulative_epsilon = 0.0
        self.cumulative_arousal = 0.0
        self.cumulative_excitement = 0.0
        self.fatigue = 0.0
        self.chain_broken = False
        self.max_depth = 3

    def summary(self) -> Dict[str, Any]:
        return {
            "count": len(self.ripples),
            "cumulative_epsilon": self.cumulative_epsilon,
            "cumulative_arousal": self.cumulative_arousal,
            "cumulative_excitement": self.cumulative_excitement,
            "fatigue": self.fatigue,
            "max_depth": self.max_depth,
            "chain_broken": self.chain_broken,
        }