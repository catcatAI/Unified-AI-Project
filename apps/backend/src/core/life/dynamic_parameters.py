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

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ParameterState:
    """
    A dynamic parameter with spatial gravity, homeostatic drift, and trends.

    Represents an adaptive threshold that varies over time / state / experience,
    mirroring the uncertainty of living systems (e.g. mood thresholds rise and
    fall, action success rate adjusts after outcomes).
    """

    base_value: float
    current_value: float
    variation_range: Tuple[float, float]
    volatility: float

    # Spatial attributes (Native Coordinate AI)
    spatial_dimension: Optional[str] = None
    spatial_anchor: Optional[Tuple[float, float, float]] = None
    inertia_mass: float = 1.0

    last_update: datetime = field(default_factory=datetime.now)
    update_interval: float = 60.0
    history: List[float] = field(default_factory=list)
    influence_map: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.history:
            self.history = [self.base_value]

    def get_gravity_pull(self, state_matrix: Any) -> float:
        """Compute spatial gravity perturbation from state matrix position."""
        if not self.spatial_dimension or not self.spatial_anchor or not state_matrix:
            return 0.0
        try:
            positions = state_matrix.get_position()
            if self.spatial_dimension not in positions:
                return 0.0
            current_coord = positions[self.spatial_dimension]
            distance = sum((a - b) ** 2 for a, b in zip(current_coord, self.spatial_anchor)) ** 0.5
            gravity = 1.0 / (max(1.0, distance) * self.inertia_mass)
            direction = 1.0 if sum(current_coord) > sum(self.spatial_anchor) else -1.0
            return gravity * direction * self.volatility
        except Exception:
            logger.debug("DynamicParams gravity calculation error", exc_info=True)
            return 0.0

    def get_trend(self, window: int = 10) -> float:
        """Return parameter trend (recent window vs earlier window difference)."""
        if len(self.history) < window:
            return 0.0
        recent = self.history[-window:]
        earlier = (
            self.history[-window * 2 : -window]
            if len(self.history) >= window * 2
            else self.history[:window]
        )
        if not earlier:
            return 0.0
        return (sum(recent) / len(recent)) - (sum(earlier) / len(earlier))

    def get_value(self, context: Optional[Dict[str, float]] = None, state_matrix: Any = None) -> float:
        """Return current value, influenced by spatial gravity or legacy context rules.

        Deterministic when no context/state_matrix is provided (pure query);
        adds simulation noise only when an external influence is applied.
        """
        value = self.current_value
        if state_matrix and self.spatial_dimension:
            value += self.get_gravity_pull(state_matrix)
        elif context:
            for factor_name, factor_value in context.items():
                value += self._calculate_influence(factor_name, factor_value)
            value += random.gauss(0, self.volatility * 0.1)
        return max(self.variation_range[0], min(self.variation_range[1], value))

    def _calculate_influence(self, factor_name: str, factor_value: float) -> float:
        if factor_name in self.influence_map:
            weight = self.influence_map[factor_name]
        else:
            influence_weights = {
                "energy": 0.3,
                "mood": 0.2,
                "stress": -0.25,
                "confidence": 0.15,
                "fatigue": -0.2,
                "recent_success": 0.35,
                "recent_failure": -0.3,
            }
            weight = influence_weights.get(factor_name, 0.1)
        return factor_value * weight * self.volatility

    def update(self, time_delta: Optional[float] = None, state_matrix: Any = None):
        """Update parameter value (homeostatic drift + gravity pull + random walk)."""
        if time_delta is None:
            time_delta = (datetime.now() - self.last_update).total_seconds()
        if time_delta < self.update_interval:
            return

        drift_to_base = (self.base_value - self.current_value) * 0.1
        gravity_pull = 0.0
        if state_matrix and self.spatial_dimension:
            gravity_pull = self.get_gravity_pull(state_matrix) * 0.5
        random_walk = random.gauss(0, self.volatility * 0.05)

        self.current_value += drift_to_base + random_walk + gravity_pull
        self.current_value = max(
            self.variation_range[0], min(self.variation_range[1], self.current_value)
        )
        self.history.append(self.current_value)
        if len(self.history) > 100:
            self.history.pop(0)
        self.last_update = datetime.now()


class DynamicThresholdManager:
    """Dynamic threshold/parameter manager for adaptive behavior thresholds.

    Manages a set of ParameterState entries that vary over time, state matrix,
    and behavior outcomes (record_outcome). Integration with StateMatrix4D is
    provided via update_from_state_matrix.
    """

    _DEFAULT_THRESHOLDS = {
        "emotion_happiness_threshold": 0.6,
        "emotion_sadness_threshold": 0.5,
        "emotion_anger_threshold": 0.5,
        "social_initiative_threshold": 0.5,
        "action_success_rate": 0.85,
        "decision_confidence_threshold": 0.7,
        "risk_tolerance": 0.5,
        "energy_decay_rate": 0.05,
        "rest_recovery_rate": 0.1,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None,
                 state_matrix: Optional[Any] = None):
        self.config = config or {}
        self.state_matrix = state_matrix
        self.parameters: Dict[str, ParameterState] = {}

        thresholds = dict(self._DEFAULT_THRESHOLDS)
        thresholds.update(self.config.get("thresholds", {}))
        for name, base in thresholds.items():
            self.parameters[name] = ParameterState(
                base_value=base,
                current_value=base,
                variation_range=(0.0, 1.0),
                volatility=0.2,
            )

        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        self._update_interval = self.config.get("update_interval", 60.0)

    async def start(self) -> None:
        """Start the background dynamic update loop."""
        if self._update_task is None:
            self._running = True
            self._update_task = asyncio.create_task(self._update_loop())

    async def stop(self) -> None:
        """Stop the background dynamic update loop."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None

    async def _update_loop(self) -> None:
        """Background update loop: drift every parameters over time."""
        while self._running:
            try:
                await asyncio.sleep(self._update_interval)
                for param_state in self.parameters.values():
                    param_state.update(state_matrix=self.state_matrix)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.error("DynamicParams update error", exc_info=True)
                await asyncio.sleep(10)

    def _build_context(self) -> Dict[str, float]:
        """Build a global context from current parameter values."""

        def get_val(name: str, default: float = 0.5) -> float:
            param = self.parameters.get(name)
            return param.current_value if param else default

        return {
            "energy": get_val("energy_decay_rate", 0.05),
            "mood": get_val("emotion_happiness_threshold", 0.6),
            "stress": 1.0 - get_val("emotion_anger_threshold", 0.7),
            "confidence": get_val("decision_confidence_threshold", 0.7),
            "fatigue": 1.0 - get_val("rest_recovery_rate", 0.1),
            "recent_success": get_val("action_success_rate", 0.85),
            "recent_failure": 1.0 - get_val("action_success_rate", 0.85),
        }

    def _build_context_for_parameter(
        self, param_name: str, global_context: Dict[str, float]
    ) -> Dict[str, float]:
        """Build a per-parameter context capturing cross-parameter influence."""
        context = global_context.copy()
        if param_name == "emotion_happiness_threshold":
            context["recent_success"] = context.get("recent_success", 0.5) * 1.5
            context["fatigue"] = context.get("fatigue", 0.5) * 1.3
        elif param_name == "action_success_rate":
            context["energy"] = context.get("energy", 0.5) * 1.2
            context["confidence"] = context.get("confidence", 0.5) * 1.4
        elif param_name == "decision_confidence_threshold":
            context["recent_failure"] = context.get("recent_failure", 0.5) * 1.3
            context["energy"] = context.get("energy", 0.5) * 1.1
        return context

    def get_parameter(self, param_name: str, context: Optional[Dict[str, float]] = None) -> float:
        """Get a dynamic parameter value, adjusted by context / spatial gravity."""
        param = self.parameters.get(param_name)
        if param is None:
            return 0.5
        return param.get_value(context, self.state_matrix)

    def set_parameter(self, param_name: str, value: float) -> None:
        """Set a parameter base value (clamped to [0,1])."""
        param = self.parameters.get(param_name)
        if param is None:
            self.parameters[param_name] = ParameterState(
                base_value=value,
                current_value=value,
                variation_range=(0.0, 1.0),
                volatility=0.2,
            )
            return
        param.base_value = max(0.0, min(1.0, value))

    def set_parameter_base(self, name: str, base_value: float) -> None:
        """Set a parameter's long-term base value."""
        param = self.parameters.get(name)
        if param is not None:
            param.base_value = max(0.0, min(1.0, base_value))

    def adjust_parameter_volatility(self, name: str, delta: float) -> None:
        """Adjust a parameter's volatility (e.g. stress raises volatility)."""
        param = self.parameters.get(name)
        if param is not None:
            param.volatility = max(0.0, min(1.0, param.volatility + delta))

    def record_outcome(self, action_type: str, success: bool, intensity: float = 1.0) -> None:
        """Record a behavioral outcome to adjust related parameters."""
        if success:
            param = self.parameters.get("action_success_rate")
            if param:
                param.base_value = min(0.98, param.base_value + 0.02 * intensity)
            param = self.parameters.get("decision_confidence_threshold")
            if param:
                param.base_value = max(0.3, param.base_value - 0.02 * intensity)
        else:
            param = self.parameters.get("action_success_rate")
            if param:
                param.base_value = max(0.3, param.base_value - 0.03 * intensity)
            for name in ("emotion_happiness_threshold", "action_success_rate"):
                self.adjust_parameter_volatility(name, 0.05 * intensity)
                p = self.parameters.get(name)
                if p is not None:
                    p.inertia_mass = max(0.1, p.inertia_mass - 0.1 * intensity)

    def get_all_parameters_summary(self) -> Dict[str, Any]:
        """Return a summary of all dynamic parameters."""
        return {
            name: {
                "base": param.base_value,
                "current": param.current_value,
                "range": list(param.variation_range),
                "volatility": param.volatility,
                "trend": param.get_trend(),
            }
            for name, param in self.parameters.items()
        }

    def update_from_state_matrix(self, state_matrix: Any) -> None:
        """Update parameters from state matrix values."""
        if state_matrix is None:
            return
        try:
            alpha = getattr(state_matrix, "alpha", None)
            if alpha is not None:
                energy = alpha.values.get("energy", 0.5)
                happiness = self.parameters.get("emotion_happiness_threshold")
                if happiness:
                    happiness.base_value = max(0.1, min(0.9, 0.6 - energy * 0.2))
                    happiness.current_value = happiness.base_value
                anger = self.parameters.get("emotion_anger_threshold")
                if anger:
                    anger.base_value = max(0.1, min(0.9, 0.5 + energy * 0.1))
                    anger.current_value = anger.base_value

            gamma = getattr(state_matrix, "gamma", None)
            if gamma is not None:
                happiness_val = gamma.values.get("happiness", 0.5)
                sadness = self.parameters.get("emotion_sadness_threshold")
                if sadness:
                    sadness.base_value = max(0.1, min(0.9, 0.5 - happiness_val * 0.2))
                    sadness.current_value = sadness.base_value

            beta = getattr(state_matrix, "beta", None)
            if beta is not None:
                curiosity = beta.values.get("curiosity", 0.5)
                social = self.parameters.get("social_initiative_threshold")
                if social:
                    social.base_value = max(0.1, min(0.9, 0.5 + curiosity * 0.2))
                    social.current_value = social.base_value
        except Exception:
            logger.warning("Failed to update from state matrix", exc_info=True)
