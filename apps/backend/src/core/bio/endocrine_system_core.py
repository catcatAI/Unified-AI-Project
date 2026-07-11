"""
Angela AI v6.0 - Endocrine System Core
内分泌系统核心

Main endocrine system simulation class with hormone management,
emotional response triggering, activity/social/stress responses,
circadian rhythm, and feedback loop application.

Author: Angela AI Development Team
Version: 6.0.0
"""

# =============================================================================
# ANGELA-MATRIX: L1[生物层] α [A] L2+
# =============================================================================
#
# 职责: 模拟人类内分泌系统，管理 12 种激素的产生、调节和效果
# 维度: 主要影响生理维度 (α) 的能量、舒适度、唤醒度、活力等
# 安全: 使用 Key A (后端控制) 进行激素状态管理
# 成熟度: L2+ 等级开始理解内分泌系统对行为的影响
#
# 激素类型:
# - 肾上腺素 (Adrenaline): 压力反应、能量提升
# - 皮质醇 (Cortisol): 压力管理、代谢调节
# - 多巴胺 (Dopamine): 奖励机制、动机驱动
# - 血清素 (Serotonin): 情绪稳定、幸福感
# - 催产素 (Oxytocin): 社交纽带、信任感
# - 内啡肽 (Endorphin): 疼痛缓解、愉悦感
# - 甲状腺素 (Thyroxine): 代谢调节、能量调节
# - 雌激素/睾酮 (Estrogen/Testosterone): 生殖系统、活力
# - 生长激素 (Growth Hormone): 生长、修复
# - 胰岛素 (Insulin): 葡萄糖调节、能量存储
# - 褪黑素 (Melatonin): 睡眠调节、昼夜节律
# - 去甲肾上腺素 (Norepinephrine): 警觉性、专注度
#
# =============================================================================

from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from core.system.config.magic_numbers import loop_sleep
from core.tracing import get_tracer

from .endocrine_types import Hormone, HormoneType

logger = logging.getLogger(__name__)


class EndocrineSystem:
    """
    内分泌系统主类 / Main endocrine system class

    Simulates the human endocrine system with 12 hormones, their dynamic regulation,
    and effects on Angela's emotional state, energy levels, and social behavior.

    Attributes:
        hormones: Dictionary of all hormone instances
        circadian_phase: Current phase of circadian rhythm (0-24 hours)
        stress_level: Current stress level affecting hormone production
        feedback_loops: Active feedback regulation mechanisms

    Example:
        >>> system = EndocrineSystem()
        >>> await system.initialize()
        >>>
        >>> # Simulate emotional event
        >>> await system.trigger_emotional_response("joy", intensity=0.8)
        >>>
        >>> # Check dopamine level
        >>> dopamine = system.get_hormone_level(HormoneType.DOPAMINE)
        >>> print(f"Dopamine: {dopamine:.1f}")

        >>> # Get effects on current state
        >>> effects = system.calculate_systemic_effects()
        >>> print(f"Energy boost: {effects['energy']:.2f}")
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        from app_config_loader import get_formula_config
        self.formula_config = get_formula_config("biological")
        self.config = config or {}
        self.hormones: Dict[HormoneType, Hormone] = {}
        self.circadian_phase: float = 12.0  # Start at noon
        self.stress_level: float = 0.0
        self._running: bool = False
        self._callbacks: list[Callable] = []
        self._update_task: Optional[asyncio.Task] = None
        self.feedback_loops: dict[tuple, float] = {}
        self.emotional_state: dict[str, float] = {}
        self.activity_level: float = 0.0
        self.social_engagement: float = 0.0

        self._initialize_hormones()

    def _initialize_hormones(self) -> None:
        """Initialize all hormone instances from configuration"""
        configs = self.formula_config.get("hormones", {})
        for ht in HormoneType:
            h_conf = configs.get(ht.name, {})
            if not h_conf:
                # Fallback to a safe default if config is missing
                h_conf = {"base_level": 50.0, "production_rate": 1.0, "half_life": 60.0}

            self.hormones[ht] = Hormone(
                hormone_type=ht,
                base_level=h_conf.get("base_level", 50.0),
                current_level=h_conf.get("base_level", 50.0),
                production_rate=h_conf.get("production_rate", 1.0),
                half_life_minutes=h_conf.get("half_life", 60.0),
            )

    async def advance_time(self, seconds: float) -> None:
        """
        推進內分泌系統時間 (2030 Standard).
        使用藥代動力學模型進行連續演化。
        """
        dt_min = seconds / 60.0
        for hormone in self.hormones.values():
            hormone.update(dt_minutes=dt_min)

        await self._apply_feedback_loops()

        # 壓力代謝：從配置讀取半衰期
        stress_conf = self.formula_config.get("stress", {})
        k_stress = math.log(2) / stress_conf.get("half_life", 30.0)
        self.stress_level = self.stress_level * math.exp(-k_stress * dt_min)

    async def _update_loop(self) -> None:
        """核心代謝循環"""
        last_run = datetime.now()
        while self._running:
            now = datetime.now()
            dt_sec = (now - last_run).total_seconds()

            await self.advance_time(dt_sec)
            await self._update_circadian_rhythm()

            last_run = now
            await asyncio.sleep(loop_sleep("endocrine_update", 5.0))  # 提高採樣頻率以保證數值演化平滑 (5秒一跳)

    async def _update_hormones(self) -> None:
        """(已由 advance_time 整合) 保持兼容性"""
        logger.debug("_update_hormones called (delegated to advance_time)")

    async def _apply_feedback_loops(self) -> None:
        """應用激素間的反饋調節"""
        for (source, target), factor in self.feedback_loops.items():
            source_hormone = self.hormones[source]
            target_hormone = self.hormones[target]

            # 反饋強度基於源激素的偏移程度
            deviation = (source_hormone.current_level - source_hormone.base_level) / 100.0
            # 瞬時調節量
            adjustment = factor * deviation * target_hormone.base_level * 0.1

            target_hormone.adjust(adjustment)

    async def _update_circadian_rhythm(self) -> None:
        """Update circadian phase and melatonin levels"""
        self.circadian_phase = (self.circadian_phase + 1 / 60) % 24  # Advance 1 minute

        # Melatonin peaks at night (roughly 22:00-06:00)
        hour = self.circadian_phase
        if 22 <= hour or hour < 6:
            # Night time - increase melatonin
            melatonin_boost = 15.0 * math.sin(
                math.pi * ((hour - 22) % 24 / 8 if hour >= 22 else (hour + 2) / 8)
            )
            self.hormones[HormoneType.MELATONIN].current_level = min(
                80.0, self.hormones[HormoneType.MELATONIN].base_level + melatonin_boost
            )
        else:
            # Day time - suppress melatonin
            self.hormones[HormoneType.MELATONIN].current_level = max(
                0.0, self.hormones[HormoneType.MELATONIN].current_level - 2.0
            )

        # Cortisol follows circadian rhythm (peaks in morning)
        cortisol_curve = 20 + 30 * math.exp(-((hour - 8) ** 2) / 50)
        self.hormones[HormoneType.CORTISOL].base_level = cortisol_curve

    async def trigger_emotional_response(self, emotion: str, intensity: float) -> None:
        """
        Trigger hormone changes based on emotional state

        Args:
            emotion: Emotion name (joy, sadness, fear, anger, surprise, disgust)
            intensity: Emotional intensity (0-1)
        """
        tracer = get_tracer()
        trace_id = tracer.start(
            layer="L1",
            module="endocrine_system",
            action="trigger_emotional_response",
            data={"emotion": emotion, "intensity": intensity},
        )

        try:
            self.emotional_state[emotion] = intensity

            # Define emotion-hormone mappings
            emotion_effects = {
                "joy": {
                    HormoneType.DOPAMINE: 20.0 * intensity,
                    HormoneType.SEROTONIN: 10.0 * intensity,
                    HormoneType.ENDORPHIN: 15.0 * intensity,
                    HormoneType.OXYTOCIN: 10.0 * intensity,
                },
                "sadness": {
                    HormoneType.SEROTONIN: -15.0 * intensity,
                    HormoneType.DOPAMINE: -10.0 * intensity,
                    HormoneType.CORTISOL: 10.0 * intensity,
                },
                "fear": {
                    HormoneType.ADRENALINE: 40.0 * intensity,
                    HormoneType.CORTISOL: 25.0 * intensity,
                    HormoneType.NOREPINEPHRINE: 30.0 * intensity,
                },
                "anger": {
                    HormoneType.ADRENALINE: 35.0 * intensity,
                    HormoneType.NOREPINEPHRINE: 25.0 * intensity,
                    HormoneType.ESTROGEN_TESTOSTERONE: 15.0 * intensity,
                },
                "surprise": {
                    HormoneType.ADRENALINE: 25.0 * intensity,
                    HormoneType.NOREPINEPHRINE: 20.0 * intensity,
                    HormoneType.DOPAMINE: 10.0 * intensity,
                },
                "disgust": {
                    HormoneType.CORTISOL: 15.0 * intensity,
                    HormoneType.SEROTONIN: -10.0 * intensity,
                },
                "love": {
                    HormoneType.OXYTOCIN: 30.0 * intensity,
                    HormoneType.DOPAMINE: 20.0 * intensity,
                    HormoneType.SEROTONIN: 15.0 * intensity,
                },
                "excitement": {
                    HormoneType.DOPAMINE: 25.0 * intensity,
                    HormoneType.NOREPINEPHRINE: 20.0 * intensity,
                    HormoneType.ADRENALINE: 15.0 * intensity,
                },
                "relaxation": {
                    HormoneType.SEROTONIN: 20.0 * intensity,
                    HormoneType.ENDORPHIN: 15.0 * intensity,
                    HormoneType.OXYTOCIN: 10.0 * intensity,
                    HormoneType.ADRENALINE: -20.0 * intensity,
                    HormoneType.CORTISOL: -15.0 * intensity,
                },
            }

            if emotion in emotion_effects:
                hormones_affected = []
                for hormone_type, change in emotion_effects[emotion].items():
                    await self.adjust_hormone(hormone_type, change)
                    hormones_affected.append(hormone_type.en_name)
                tracer.record(trace_id, "hormones_affected", hormones_affected)
        finally:
            tracer.finish(trace_id)

    async def trigger_activity_response(self, activity_type: str, intensity: float) -> None:
        """
        Adjust hormones based on physical/mental activity

        Args:
            activity_type: Type of activity
            intensity: Activity intensity (0-1)
        """
        self.activity_level = intensity

        activity_effects = {
            "physical_exercise": {
                HormoneType.ADRENALINE: 30.0 * intensity,
                HormoneType.ENDORPHIN: 25.0 * intensity,
                HormoneType.DOPAMINE: 15.0 * intensity,
                HormoneType.CORTISOL: 10.0 * intensity,
                HormoneType.GROWTH_HORMONE: 20.0 * intensity,
            },
            "mental_focus": {
                HormoneType.NOREPINEPHRINE: 25.0 * intensity,
                HormoneType.DOPAMINE: 20.0 * intensity,
                HormoneType.CORTISOL: 10.0 * intensity,
            },
            "creative_work": {
                HormoneType.DOPAMINE: 20.0 * intensity,
                HormoneType.SEROTONIN: 15.0 * intensity,
                HormoneType.NOREPINEPHRINE: 10.0 * intensity,
            },
            "social_interaction": {
                HormoneType.OXYTOCIN: 25.0 * intensity,
                HormoneType.DOPAMINE: 15.0 * intensity,
                HormoneType.SEROTONIN: 10.0 * intensity,
            },
            "rest": {
                HormoneType.CORTISOL: -15.0 * intensity,
                HormoneType.ADRENALINE: -20.0 * intensity,
                HormoneType.SEROTONIN: 10.0 * intensity,
                HormoneType.GROWTH_HORMONE: 15.0 * intensity,
            },
        }

        if activity_type in activity_effects:
            for hormone_type, change in activity_effects[activity_type].items():
                await self.adjust_hormone(hormone_type, change)

    async def trigger_social_response(self, interaction_type: str, intensity: float) -> None:
        """
        Adjust hormones based on social interactions

        Args:
            interaction_type: Type of social interaction
            intensity: Interaction intensity (0-1)
        """
        self.social_engagement = intensity

        social_effects = {
            "positive_interaction": {
                HormoneType.OXYTOCIN: 25.0 * intensity,
                HormoneType.DOPAMINE: 15.0 * intensity,
                HormoneType.SEROTONIN: 10.0 * intensity,
                HormoneType.ENDORPHIN: 10.0 * intensity,
            },
            "negative_interaction": {
                HormoneType.CORTISOL: 20.0 * intensity,
                HormoneType.ADRENALINE: 15.0 * intensity,
                HormoneType.SEROTONIN: -10.0 * intensity,
            },
            "intimate_bonding": {
                HormoneType.OXYTOCIN: 40.0 * intensity,
                HormoneType.DOPAMINE: 20.0 * intensity,
                HormoneType.SEROTONIN: 15.0 * intensity,
                HormoneType.ENDORPHIN: 20.0 * intensity,
            },
            "conflict": {
                HormoneType.ADRENALINE: 35.0 * intensity,
                HormoneType.CORTISOL: 25.0 * intensity,
                HormoneType.NOREPINEPHRINE: 20.0 * intensity,
                HormoneType.SEROTONIN: -15.0 * intensity,
            },
        }

        if interaction_type in social_effects:
            for hormone_type, change in social_effects[interaction_type].items():
                await self.adjust_hormone(hormone_type, change)

    async def trigger_stress_response(self, stress_level: float, stress_type: str = "acute") -> None:
        """
        Trigger stress-related hormone changes

        Args:
            stress_level: Level of stress (0-1)
            stress_type: "acute" or "chronic"
        """
        self.stress_level = stress_level

        if stress_type == "acute":
            # Acute stress - fight or flight
            await self.adjust_hormone(HormoneType.ADRENALINE, 50.0 * stress_level)
            await self.adjust_hormone(HormoneType.NOREPINEPHRINE, 40.0 * stress_level)
            await self.adjust_hormone(HormoneType.CORTISOL, 20.0 * stress_level)
        else:
            # Chronic stress - sustained cortisol
            await self.adjust_hormone(HormoneType.CORTISOL, 30.0 * stress_level)
            await self.adjust_hormone(HormoneType.ADRENALINE, 15.0 * stress_level)
            await self.adjust_hormone(HormoneType.SEROTONIN, -15.0 * stress_level)

    async def adjust_hormone(self, hormone_type: HormoneType, amount: float) -> None:
        """
        瞬時調節特定激素 (具備追蹤與回調)
        """
        tracer = get_tracer()
        trace_id = tracer.start(
            layer="L1",
            module="endocrine_system",
            action="adjust_hormone",
            data={"hormone": hormone_type.en_name, "adjustment": amount},
        )

        try:
            if hormone_type in self.hormones:
                hormone = self.hormones[hormone_type]
                old_level = hormone.current_level
                hormone.adjust(amount)

                tracer.record(trace_id, "old_level", old_level)
                tracer.record(trace_id, "new_level", hormone.current_level)

                # 通知觀察者
                for callback in self._callbacks:
                    try:
                        callback(hormone_type, old_level, hormone.current_level)
                    except Exception as e:
                        logger.error(f"Hormone callback error: {e}", exc_info=True)
        finally:
            tracer.finish(trace_id)

    def get_hormone_level(self, hormone_type: HormoneType) -> float:
        """Get current level of a specific hormone"""
        if hormone_type in self.hormones:
            return self.hormones[hormone_type].current_level
        return 0.0

    def get_all_hormone_levels(self) -> Dict[HormoneType, float]:
        """Get all hormone levels"""
        return {ht: h.current_level for ht, h in self.hormones.items()}

    def calculate_systemic_effects(self) -> Dict[str, float]:
        """
        Calculate the combined effects of all hormones on different systems

        Returns:
            Dictionary with effects on emotion, energy, social behavior, etc.
        """
        effects = {
            "energy": 0.0,
            "mood": 0.0,
            "stress_resilience": 0.0,
            "social_desire": 0.0,
            "focus": 0.0,
            "creativity": 0.0,
            "pain_tolerance": 0.0,
            "alertness": 0.0,
            "relaxation": 0.0,
        }

        # Energy effects
        effects["energy"] += (
            self.hormones[HormoneType.THYROXINE].get_normalized_level() * 0.3
            + self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.3
            + self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.2
            + self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.2
        )

        # Mood effects
        effects["mood"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.4
            + self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.3
            + self.hormones[HormoneType.ENDORPHIN].get_normalized_level() * 0.2
            - self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.1
        )

        # Stress resilience
        effects["stress_resilience"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.3
            + self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.3
            + self.hormones[HormoneType.ENDORPHIN].get_normalized_level() * 0.2
            - self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.2
        )

        # Social desire
        effects["social_desire"] += (
            self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.5
            + self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.3
            + self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.2
        )

        # Focus
        effects["focus"] += (
            self.hormones[HormoneType.NOREPINEPHRINE].get_normalized_level() * 0.4
            + self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.3
            + self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.2
            - self.hormones[HormoneType.MELATONIN].get_normalized_level() * 0.1
        )

        # Alertness
        effects["alertness"] += (
            self.hormones[HormoneType.NOREPINEPHRINE].get_normalized_level() * 0.4
            + self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.4
            - self.hormones[HormoneType.MELATONIN].get_normalized_level() * 0.2
        )

        # Relaxation
        effects["relaxation"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.3
            + self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.3
            + self.hormones[HormoneType.ENDORPHIN].get_normalized_level() * 0.2
            - self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.1
            - self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.1
        )

        return effects

    def register_change_callback(self, callback: Callable[[HormoneType, float, float], None]) -> None:
        """Register callback for hormone level changes"""
        self._callbacks.append(callback)

    async def initialize(self) -> None:
        """Initialize the endocrine system and start background tasks"""
        self._running = True
        self._update_task = asyncio.ensure_future(self._update_loop())
        logger.info("EndocrineSystem initialized")

    async def shutdown(self) -> None:
        """Shutdown the endocrine system and stop background tasks"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("EndocrineSystem shut down")

    def get_hormonal_profile(self) -> Dict[str, Any]:
        """Get complete hormonal profile"""
        return {
            "hormones": {
                ht.en_name: {
                    "current": h.current_level,
                    "base": h.base_level,
                    "normalized": h.get_normalized_level(),
                }
                for ht, h in self.hormones.items()
            },
            "circadian_phase": self.circadian_phase,
            "stress_level": self.stress_level,
            "activity_level": self.activity_level,
            "social_engagement": self.social_engagement,
            "systemic_effects": self.calculate_systemic_effects(),
        }
