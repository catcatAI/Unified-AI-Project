"""
Angela AI v6.0 - Endocrine System
内分泌系统

Simulates human endocrine system with 12 hormones, their production, regulation,
and effects on emotions, energy, social behavior, and physical state.

Features:
- 12 hormone types with base and current levels
- Dynamic production based on emotions, activities, social interactions, and stress
- Feedback regulation loops
- Effects on emotion, energy, and social behavior
- Circadian rhythm simulation

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
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
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import asyncio
import math
import logging
logger = logging.getLogger(__name__)


class HormoneType(Enum):
    """12种激素类型 / 12 hormone types"""
    ADRENALINE = ("肾上腺素", "Adrenaline", "stress_response", "energy_boost")
    CORTISOL = ("皮质醇", "Cortisol", "stress_management", "metabolism")
    DOPAMINE = ("多巴胺", "Dopamine", "reward", "motivation")
    SEROTONIN = ("血清素", "Serotonin", "mood_stability", "wellbeing")
    OXYTOCIN = ("催产素", "Oxytocin", "bonding", "social_trust")
    ENDORPHIN = ("内啡肽", "Endorphin", "pain_relief", "pleasure")
    THYROXINE = ("甲状腺素", "Thyroxine", "metabolism", "energy_regulation")
    ESTROGEN_TESTOSTERONE = ("雌激素/睾酮", "Estrogen/Testosterone", "reproductive", "vitality")
    GROWTH_HORMONE = ("生长激素", "Growth Hormone", "growth", "repair")
    INSULIN = ("胰岛素", "Insulin", "glucose_regulation", "energy_storage")
    MELATONIN = ("褪黑素", "Melatonin", "sleep_regulation", "circadian_rhythm")
    NOREPINEPHRINE = ("去甲肾上腺素", "Norepinephrine", "alertness", "focus")
    
    def __init__(self, cn_name: str, en_name: str, primary_role: str, secondary_role: str):
        self.cn_name = cn_name
        self.en_name = en_name
        self.primary_role = primary_role
        self.secondary_role = secondary_role


@dataclass
class Hormone:
    """激素 / Hormone"""
    hormone_type: HormoneType
    base_level: float  # 基础水平 (0-100) / Base level
    current_level: float  # 当前水平 / Current level
    production_rate: float  # 产生速率 / Production rate per minute
    decay_rate: float  # 衰减率 / Decay rate per minute
    min_level: float = 0.0  # 最小水平 / Minimum level
    max_level: float = 100.0  # 最大水平 / Maximum level
    last_update: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.current_level = max(self.min_level, min(self.max_level, self.current_level))
    
    def get_normalized_level(self) -> float:
        """Get level normalized to 0-1 range"""
        return (self.current_level - self.min_level) / (self.max_level - self.min_level)
    
    def update(self, minutes: float = 1.0):
        """Update hormone level over time"""
        time_delta = minutes
        
        # Natural decay toward base level
        if self.current_level > self.base_level:
            decay = self.decay_rate * time_delta
            self.current_level = max(self.base_level, self.current_level - decay)
        elif self.current_level < self.base_level:
            recovery = self.decay_rate * 0.5 * time_delta  # Slower recovery
            self.current_level = min(self.base_level, self.current_level + recovery)
        
        self.last_update = datetime.now()


@dataclass
class HormonalEffect:
    """激素效果 / Hormonal effect"""
    target_system: str  # 目标系统 / Target system (emotion, energy, social, etc.)
    effect_type: str  # 效果类型 / Effect type
    magnitude: float  # 效果强度 (-1 to 1) / Effect magnitude
    duration: float  # 持续时间(分钟) / Duration in minutes
    

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
    
    # Default hormone configurations
    DEFAULT_HORMONE_CONFIGS: Dict[HormoneType, Dict[str, float]] = {
        HormoneType.ADRENALINE: {
            "base_level": 10.0,
            "production_rate": 5.0,
            "decay_rate": 3.0,
        },
        HormoneType.CORTISOL: {
            "base_level": 20.0,
            "production_rate": 2.0,
            "decay_rate": 1.5,
        },
        HormoneType.DOPAMINE: {
            "base_level": 40.0,
            "production_rate": 3.0,
            "decay_rate": 2.0,
        },
        HormoneType.SEROTONIN: {
            "base_level": 50.0,
            "production_rate": 2.5,
            "decay_rate": 1.0,
        },
        HormoneType.OXYTOCIN: {
            "base_level": 30.0,
            "production_rate": 4.0,
            "decay_rate": 2.5,
        },
        HormoneType.ENDORPHIN: {
            "base_level": 25.0,
            "production_rate": 6.0,
            "decay_rate": 4.0,
        },
        HormoneType.THYROXINE: {
            "base_level": 60.0,
            "production_rate": 1.0,
            "decay_rate": 0.5,
        },
        HormoneType.ESTROGEN_TESTOSTERONE: {
            "base_level": 35.0,
            "production_rate": 1.5,
            "decay_rate": 1.0,
        },
        HormoneType.GROWTH_HORMONE: {
            "base_level": 15.0,
            "production_rate": 2.0,
            "decay_rate": 1.5,
        },
        HormoneType.INSULIN: {
            "base_level": 45.0,
            "production_rate": 3.0,
            "decay_rate": 2.5,
        },
        HormoneType.MELATONIN: {
            "base_level": 5.0,
            "production_rate": 8.0,
            "decay_rate": 5.0,
        },
        HormoneType.NOREPINEPHRINE: {
            "base_level": 20.0,
            "production_rate": 4.0,
            "decay_rate": 3.0,
        },
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.hormones: Dict[HormoneType, Hormone] = {}
        self.circadian_phase: float = 12.0  # Start at noon
        self.stress_level: float = 0.0
        self.activity_level: float = 0.5
        self.social_engagement: float = 0.5
        self.emotional_state: Dict[str, float] = {}
        
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        self._callbacks: List[Callable[[HormoneType, float, float], None]] = []
        
        # Feedback loop configurations
        self.feedback_loops: Dict[Tuple[HormoneType, HormoneType], float] = {
            # Inhibitory feedbacks
            (HormoneType.CORTISOL, HormoneType.CORTISOL): -0.3,  # Self-inhibition
            (HormoneType.ADRENALINE, HormoneType.ADRENALINE): -0.2,
            # Stimulatory feedbacks
            (HormoneType.DOPAMINE, HormoneType.SEROTONIN): 0.1,
            (HormoneType.OXYTOCIN, HormoneType.DOPAMINE): 0.15,
            (HormoneType.SEROTONIN, HormoneType.MELATONIN): 0.2,
        }
        
        self._initialize_hormones()
    
    def _initialize_hormones(self):
        """Initialize all hormone instances"""
        for hormone_type, config in self.DEFAULT_HORMONE_CONFIGS.items():
            self.hormones[hormone_type] = Hormone(
                hormone_type=hormone_type,
                base_level=config["base_level"],
                current_level=config["base_level"],
                production_rate=config["production_rate"],
                decay_rate=config["decay_rate"],
            )
    
    async def initialize(self):
        """Initialize the endocrine system"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the endocrine system"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop for hormone dynamics"""
        while self._running:
            await self._update_hormones()
            await self._apply_feedback_loops()
            await self._update_circadian_rhythm()
            await asyncio.sleep(60)  # Update every minute
    
    async def _update_hormones(self):
        """Update all hormone levels"""
        for hormone in self.hormones.values():
            hormone.update(minutes=1.0)
    
    async def _apply_feedback_loops(self):
        """Apply feedback regulation between hormones"""
        for (source, target), factor in self.feedback_loops.items():
            source_level = self.hormones[source].current_level
            target_hormone = self.hormones[target]
            
            # Calculate feedback effect
            normalized_source = source_level / 100.0
            adjustment = factor * normalized_source * target_hormone.production_rate
            
            # Apply adjustment
            target_hormone.current_level = max(
                target_hormone.min_level,
                min(target_hormone.max_level, 
                    target_hormone.current_level + adjustment)
            )
    
    async def _update_circadian_rhythm(self):
        """Update circadian phase and melatonin levels"""
        self.circadian_phase = (self.circadian_phase + 1/60) % 24  # Advance 1 minute
        
        # Melatonin peaks at night (roughly 22:00-06:00)
        hour = self.circadian_phase
        if 22 <= hour or hour < 6:
            # Night time - increase melatonin
            melatonin_boost = 15.0 * math.sin(math.pi * (
                (hour - 22) % 24 / 8 if hour >= 22 else (hour + 2) / 8
            ))
            self.hormones[HormoneType.MELATONIN].current_level = min(
                80.0,
                self.hormones[HormoneType.MELATONIN].base_level + melatonin_boost
            )
        else:
            # Day time - suppress melatonin
            self.hormones[HormoneType.MELATONIN].current_level = max(
                0.0,
                self.hormones[HormoneType.MELATONIN].current_level - 2.0
            )
        
        # Cortisol follows circadian rhythm (peaks in morning)
        cortisol_curve = 20 + 30 * math.exp(-((hour - 8) ** 2) / 50)
        self.hormones[HormoneType.CORTISOL].base_level = cortisol_curve
    
    async def trigger_emotional_response(self, emotion: str, intensity: float):
        """
        Trigger hormone changes based on emotional state
        
        Args:
            emotion: Emotion name (joy, sadness, fear, anger, surprise, disgust)
            intensity: Emotional intensity (0-1)
        """
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
            for hormone_type, change in emotion_effects[emotion].items():
                await self.adjust_hormone(hormone_type, change)
    
    async def trigger_activity_response(self, activity_type: str, intensity: float):
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
    
    async def trigger_social_response(self, interaction_type: str, intensity: float):
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
    
    async def trigger_stress_response(self, stress_level: float, stress_type: str = "acute"):
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
    
    async def adjust_hormone(self, hormone_type: HormoneType, amount: float):
        """
        Adjust a specific hormone level
        
        Args:
            hormone_type: Type of hormone to adjust
            amount: Amount to add (positive or negative)
        """
        if hormone_type in self.hormones:
            hormone = self.hormones[hormone_type]
            old_level = hormone.current_level
            hormone.current_level = max(
                hormone.min_level,
                min(hormone.max_level, hormone.current_level + amount)
            )
            
            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(hormone_type, old_level, hormone.current_level)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

    
    def get_hormone_level(self, hormone_type: HormoneType) -> float:
        """Get current level of a specific hormone"""
        return self.hormones.get(hormone_type, Hormone(
            hormone_type=hormone_type, base_level=0, current_level=0,
            production_rate=0, decay_rate=0
        )).current_level
    
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
            self.hormones[HormoneType.THYROXINE].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.2 +
            self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.2
        )
        
        # Mood effects
        effects["mood"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.4 +
            self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.ENDORPHIN].get_normalized_level() * 0.2 -
            self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.1
        )
        
        # Stress resilience
        effects["stress_resilience"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.ENDORPHIN].get_normalized_level() * 0.2 -
            self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.2
        )
        
        # Social desire
        effects["social_desire"] += (
            self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.5 +
            self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.2
        )
        
        # Focus
        effects["focus"] += (
            self.hormones[HormoneType.NOREPINEPHRINE].get_normalized_level() * 0.4 +
            self.hormones[HormoneType.DOPAMINE].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.2 -
            self.hormones[HormoneType.MELATONIN].get_normalized_level() * 0.1
        )
        
        # Alertness
        effects["alertness"] += (
            self.hormones[HormoneType.NOREPINEPHRINE].get_normalized_level() * 0.4 +
            self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.4 -
            self.hormones[HormoneType.MELATONIN].get_normalized_level() * 0.2
        )
        
        # Relaxation
        effects["relaxation"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.ENDORPHIN].get_normalized_level() * 0.2 -
            self.hormones[HormoneType.ADRENALINE].get_normalized_level() * 0.1 -
            self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.1
        )
        
        return effects
    
    def register_change_callback(
        self, 
        callback: Callable[[HormoneType, float, float], None]
    ):
        """Register callback for hormone level changes"""
        self._callbacks.append(callback)
    
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


@dataclass
class ReceptorStatus:
    """受体状态 / Receptor status"""
    receptor_type: str
    occupancy: float  # 占用率 (0-1)
    upregulation: float  # 上调因子
    downregulation: float  # 下调因子
    sensitivity: float  # 当前敏感度


class HormoneKinetics:
    """
    激素动力学 / Hormone Kinetics
    
    Models hormone metabolism, receptor occupancy, receptor regulation,
    and secretion patterns using biologically-inspired mathematical models.
    
    Features:
    - Half-life metabolism (exponential decay)
    - Receptor occupancy (Hill equation)
    - Receptor regulation (upregulation/downregulation)
    - Secretion regulation (basal + pulsatile)
    
    Example:
        >>> kinetics = HormoneKinetics()
        >>> 
        >>> # Calculate hormone level after time with half-life
        >>> level = kinetics.metabolize(
        ...     initial_level=50.0,
        ...     half_life_hours=1.5,
        ...     time_hours=2.0
        ... )
        >>> print(f"Remaining: {level:.2f}")
        
        >>> # Calculate receptor occupancy using Hill equation
        >>> occupancy = kinetics.calculate_occupancy(
        ...     hormone_level=30.0,
        ...     kd=15.0,  # Dissociation constant
        ...     hill_coefficient=1.5
        ... )
        >>> print(f"Receptor occupancy: {occupancy:.2%}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize hormone kinetics model
        
        Args:
            config: Configuration dictionary with optional parameters
        """
        self.config = config or {}
        
        # Default half-lives for hormones (hours)
        self.half_lives: Dict[HormoneType, float] = {
            HormoneType.ADRENALINE: 0.1,  # 6 minutes
            HormoneType.CORTISOL: 1.5,    # 90 minutes
            HormoneType.DOPAMINE: 0.1,    # 6 minutes
            HormoneType.SEROTONIN: 1.0,   # 1 hour
            HormoneType.OXYTOCIN: 0.1,    # 6 minutes
            HormoneType.ENDORPHIN: 0.5,   # 30 minutes
            HormoneType.THYROXINE: 168.0, # 7 days
            HormoneType.ESTROGEN_TESTOSTERONE: 24.0,  # 1 day
            HormoneType.GROWTH_HORMONE: 0.3,  # 18 minutes
            HormoneType.INSULIN: 0.1,     # 6 minutes
            HormoneType.MELATONIN: 0.5,   # 30 minutes
            HormoneType.NOREPINEPHRINE: 0.05,  # 3 minutes
        }
        
        # Override with config
        if "half_lives" in self.config:
            self.half_lives.update(self.config["half_lives"])
        
        # Receptor parameters
        self.default_kd: float = self.config.get("default_kd", 20.0)  # Dissociation constant
        self.default_hill: float = self.config.get("default_hill", 1.0)
        
        # Receptor regulation tracking
        self.receptor_status: Dict[HormoneType, ReceptorStatus] = {}
        self._initialize_receptors()
    
    def _initialize_receptors(self) -> None:
        """Initialize receptor status for all hormones"""
        for hormone_type in HormoneType:
            self.receptor_status[hormone_type] = ReceptorStatus(
                receptor_type=f"{hormone_type.en_name}_receptor",
                occupancy=0.0,
                upregulation=1.0,
                downregulation=1.0,
                sensitivity=1.0
            )
    
    def metabolize(
        self,
        initial_level: float,
        hormone_type: HormoneType,
        time_hours: float,
        half_life: Optional[float] = None
    ) -> float:
        """
        半衰期代谢 / Half-life metabolism (exponential decay)
        
        Formula: C(t) = C₀ * (1/2)^(t/t½)
        
        Args:
            initial_level: Initial hormone level
            hormone_type: Type of hormone
            time_hours: Time elapsed (hours)
            half_life: Optional custom half-life (uses default if not provided)
            
        Returns:
            Remaining hormone level after metabolism
        """
        t_half = half_life or self.half_lives.get(hormone_type, 1.0)
        
        # Exponential decay formula
        remaining = initial_level * (0.5 ** (time_hours / t_half))
        
        return remaining
    
    def calculate_metabolism_rate(
        self,
        current_level: float,
        hormone_type: HormoneType,
        half_life: Optional[float] = None
    ) -> float:
        """
        计算代谢速率 / Calculate metabolism rate
        
        Args:
            current_level: Current hormone level
            hormone_type: Type of hormone
            half_life: Optional custom half-life
            
        Returns:
            Metabolism rate (amount per hour)
        """
        t_half = half_life or self.half_lives.get(hormone_type, 1.0)
        
        # Rate constant k = ln(2) / t½
        k = math.log(2) / t_half
        
        # Rate = k * [C]
        rate = k * current_level
        
        return rate
    
    def calculate_occupancy(
        self,
        hormone_level: float,
        kd: Optional[float] = None,
        hill_coefficient: Optional[float] = None,
        receptor_status: Optional[ReceptorStatus] = None
    ) -> float:
        """
        受体占用计算 / Receptor occupancy (Hill equation)
        
        Hill equation: Y = [H]ⁿ / (Kdⁿ + [H]ⁿ)
        
        Args:
            hormone_level: Current hormone concentration
            kd: Dissociation constant (EC50)
            hill_coefficient: Hill coefficient (cooperativity)
            receptor_status: Optional receptor status for regulation effects
            
        Returns:
            Fraction of receptors occupied (0-1)
        """
        kd = kd or self.default_kd
        n = hill_coefficient or self.default_hill
        
        # Adjust effective KD based on receptor regulation
        if receptor_status:
            # Upregulation decreases effective KD (increases sensitivity)
            # Downregulation increases effective KD (decreases sensitivity)
            effective_kd = kd / receptor_status.sensitivity
        else:
            effective_kd = kd
        
        # Hill equation
        if effective_kd == 0:
            return 1.0 if hormone_level > 0 else 0.0
        
        occupancy = (hormone_level ** n) / ((effective_kd ** n) + (hormone_level ** n))
        
        return min(1.0, max(0.0, occupancy))
    
    def update_receptor_regulation(
        self,
        hormone_type: HormoneType,
        chronic_level: float,
        time_days: float = 1.0
    ) -> ReceptorStatus:
        """
        受体调节 / Receptor regulation (upregulation/downregulation)
        
        Chronic high hormone levels lead to downregulation (desensitization).
        Chronic low levels lead to upregulation (sensitization).
        
        Args:
            hormone_type: Type of hormone
            chronic_level: Average level over time period (normalized 0-1)
            time_days: Time period for regulation (days)
            
        Returns:
            Updated ReceptorStatus
        """
        status = self.receptor_status[hormone_type]
        
        # Regulation rate (per day)
        regulation_rate = 0.1 * time_days
        
        if chronic_level > 0.7:
            # High chronic level -> downregulation (desensitization)
            status.downregulation += regulation_rate * (chronic_level - 0.7)
            status.upregulation = max(0.5, status.upregulation - regulation_rate * 0.5)
        elif chronic_level < 0.3:
            # Low chronic level -> upregulation (sensitization)
            status.upregulation += regulation_rate * (0.3 - chronic_level)
            status.downregulation = max(0.5, status.downregulation - regulation_rate * 0.5)
        else:
            # Normal levels -> gradual return to baseline
            status.upregulation = 1.0 + (status.upregulation - 1.0) * 0.9
            status.downregulation = 1.0 + (status.downregulation - 1.0) * 0.9
        
        # Calculate overall sensitivity
        status.sensitivity = status.upregulation / status.downregulation
        status.sensitivity = max(0.3, min(3.0, status.sensitivity))
        
        return status
    
    def calculate_secretion(
        self,
        basal_rate: float,
        stimulus: float,
        pulse_frequency: float = 1.0,
        pulse_amplitude: float = 0.3,
        time_hours: float = 0.0
    ) -> float:
        """
        分泌调节计算 / Secretion regulation (basal + pulsatile)
        
        Many hormones are secreted in pulses superimposed on basal secretion.
        
        Formula: S = S_basal + S_stimulus + S_pulse
        
        Args:
            basal_rate: Basal secretion rate
            stimulus: Stimulus-induced secretion
            pulse_frequency: Pulses per hour
            pulse_amplitude: Amplitude of pulses (as fraction of basal)
            time_hours: Current time (for pulse phase)
            
        Returns:
            Total secretion rate
        """
        # Basal secretion
        secretion = basal_rate
        
        # Stimulus-induced secretion
        secretion += stimulus
        
        # Pulsatile component (sinusoidal)
        if pulse_frequency > 0:
            pulse_phase = 2 * math.pi * pulse_frequency * time_hours
            pulse = basal_rate * pulse_amplitude * math.sin(pulse_phase)
            secretion += pulse
        
        return max(0.0, secretion)
    
    def get_receptor_status(self, hormone_type: HormoneType) -> ReceptorStatus:
        """获取受体状态 / Get receptor status for a hormone"""
        return self.receptor_status.get(
            hormone_type,
            ReceptorStatus(
                receptor_type="unknown",
                occupancy=0.0,
                upregulation=1.0,
                downregulation=1.0,
                sensitivity=1.0
            )
        )
    
    def get_all_receptor_status(self) -> Dict[HormoneType, ReceptorStatus]:
        """获取所有受体状态 / Get all receptor statuses"""
        return self.receptor_status.copy()


@dataclass
class FeedbackNode:
    """反馈节点 / Feedback node"""
    hormone_type: HormoneType
    setpoint: float  # 设定点
    current_level: float  # 当前水平
    gain: float  # 增益
    feedback_type: str  # "positive" or "negative"


class FeedbackLoop:
    """
    反馈回路 / Feedback Loop
    
    Implements endocrine feedback regulation including:
    - HPA axis (Hypothalamus-Pituitary-Adrenal axis)
    - Negative feedback (cortisol inhibits CRH)
    - Hormone antagonism (leptin vs ghrelin)
    - Circadian rhythm (melatonin cycles)
    
    Example:
        >>> feedback = FeedbackLoop()
        >>> 
        >>> # Simulate HPA axis stress response
        >>> crh = 10.0  # Corticotropin-releasing hormone
        >>> acth = feedback.hpa_axis_step(crh)
        >>> cortisol = feedback.hpa_axis_step(acth, level_type="cortisol")
        >>> 
        >>> # Apply negative feedback
        >>> cortisol += 50.0  # High cortisol
        >>> inhibition = feedback.negative_feedback(
        ...     HormoneType.CORTISOL,
        ...     target_hormone=HormoneType.ADRENALINE,
        ...     current_level=cortisol
        ... )
        >>> print(f"Inhibition: {inhibition:.2f}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize feedback loop system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
        # HPA axis parameters
        self.hpa_crh_to_acth_gain: float = self.config.get("hpa_crh_gain", 2.0)
        self.hpa_acth_to_cortisol_gain: float = self.config.get("hpa_acth_gain", 3.0)
        self.hpa_cortisol_feedback: float = self.config.get("hpa_feedback", 0.4)
        
        # Negative feedback parameters
        self.negative_feedback_gain: float = self.config.get("neg_feedback_gain", 0.3)
        self.positive_feedback_gain: float = self.config.get("pos_feedback_gain", 0.2)
        
        # Circadian parameters
        self.melatonin_peak_hour: float = self.config.get("melatonin_peak", 2.0)  # 2 AM
        self.melatonin_amplitude: float = self.config.get("melatonin_amp", 40.0)
        self.cortisol_peak_hour: float = self.config.get("cortisol_peak", 8.0)  # 8 AM
        self.cortisol_amplitude: float = self.config.get("cortisol_amp", 30.0)
        
        # Feedback nodes tracking
        self.feedback_nodes: Dict[HormoneType, FeedbackNode] = {}
        self._initialize_nodes()
    
    def _initialize_nodes(self) -> None:
        """Initialize feedback nodes for all hormones"""
        for hormone_type in HormoneType:
            self.feedback_nodes[hormone_type] = FeedbackNode(
                hormone_type=hormone_type,
                setpoint=50.0,
                current_level=50.0,
                gain=0.5,
                feedback_type="negative"
            )
    
    def hpa_axis_step(
        self,
        input_level: float,
        level_type: str = "crh",
        cortisol_level: float = 20.0
    ) -> float:
        """
        HPA轴单步模拟 / HPA axis single step simulation
        
        Simulates: CRH -> ACTH -> Cortisol with negative feedback
        
        Args:
            input_level: Input hormone level (CRH or ACTH)
            level_type: "crh", "acth", or "cortisol"
            cortisol_level: Current cortisol level (for feedback calculation)
            
        Returns:
            Output hormone level
        """
        if level_type == "crh":
            # CRH stimulates ACTH release
            # Apply cortisol negative feedback
            feedback_inhibition = self.hpa_cortisol_feedback * (cortisol_level / 100.0)
            output = input_level * self.hpa_crh_to_acth_gain * (1 - feedback_inhibition)
            return max(0.0, output)
        
        elif level_type == "acth":
            # ACTH stimulates cortisol release
            output = input_level * self.hpa_acth_to_cortisol_gain
            return max(0.0, min(100.0, output))
        
        elif level_type == "cortisol":
            # Cortisol has self-inhibitory effects
            # High cortisol suppresses further production
            inhibition = (cortisol_level / 100.0) ** 2
            output = input_level * (1 - inhibition * 0.5)
            return max(0.0, output)
        
        return input_level
    
    def simulate_hpa_axis(
        self,
        stress_input: float,
        simulation_hours: float = 2.0,
        time_step: float = 0.1
    ) -> Dict[str, List[float]]:
        """
        完整HPA轴模拟 / Full HPA axis simulation
        
        Args:
            stress_input: Initial stress level (triggers CRH)
            simulation_hours: Duration of simulation
            time_step: Time step in hours
            
        Returns:
            Dictionary with time series for CRH, ACTH, and cortisol
        """
        n_steps = int(simulation_hours / time_step)
        
        crh_levels = [stress_input]
        acth_levels = [5.0]  # Baseline ACTH
        cortisol_levels = [20.0]  # Baseline cortisol
        
        for i in range(n_steps):
            # CRH (stimulated by stress, inhibited by cortisol)
            crh_feedback = self.hpa_cortisol_feedback * (cortisol_levels[-1] / 100.0)
            crh_new = stress_input * (1 - crh_feedback)
            crh_levels.append(crh_new)
            
            # ACTH (stimulated by CRH)
            acth_new = crh_new * self.hpa_crh_to_acth_gain
            acth_levels.append(max(0.0, acth_new))
            
            # Cortisol (stimulated by ACTH, natural decay)
            decay = 0.1  # 10% decay per step
            cortisol_new = cortisol_levels[-1] * (1 - decay) + acth_new * self.hpa_acth_to_cortisol_gain * time_step
            cortisol_levels.append(max(0.0, min(100.0, cortisol_new)))
        
        return {
            "crh": crh_levels,
            "acth": acth_levels,
            "cortisol": cortisol_levels,
            "time": [i * time_step for i in range(len(crh_levels))]
        }
    
    def negative_feedback(
        self,
        source_hormone: HormoneType,
        target_hormone: HormoneType,
        current_level: float,
        setpoint: Optional[float] = None
    ) -> float:
        """
        负反馈调节 / Negative feedback regulation
        
        High levels of source hormone inhibit target hormone production.
        
        Args:
            source_hormone: Hormone providing feedback
            target_hormone: Hormone being regulated
            current_level: Current level of source hormone
            setpoint: Target setpoint (uses default if not provided)
            
        Returns:
            Inhibition factor (0-1, where 1 = full inhibition)
        """
        node = self.feedback_nodes.get(target_hormone)
        sp = setpoint or (node.setpoint if node else 50.0)
        
        # Calculate deviation from setpoint
        deviation = (current_level - sp) / sp
        
        # Inhibition increases with deviation
        if deviation > 0:
            inhibition = min(1.0, deviation * self.negative_feedback_gain)
        else:
            inhibition = 0.0
        
        return inhibition
    
    def hormone_antagonism(
        self,
        hormone_a: HormoneType,
        hormone_b: HormoneType,
        level_a: float,
        level_b: float,
        antagonism_strength: float = 0.5
    ) -> Tuple[float, float]:
        """
        激素拮抗 / Hormone antagonism (e.g., leptin vs ghrelin)
        
        Two hormones with opposing effects influence each other.
        
        Args:
            hormone_a: First hormone
            hormone_b: Second hormone (opposing)
            level_a: Level of hormone A
            level_b: Level of hormone B
            antagonism_strength: Strength of antagonism (0-1)
            
        Returns:
            Tuple of (adjusted_level_a, adjusted_level_b)
        """
        # Normalize levels to 0-1
        norm_a = level_a / 100.0
        norm_b = level_b / 100.0
        
        # Mutual suppression
        adjusted_a = level_a * (1 - norm_b * antagonism_strength * 0.5)
        adjusted_b = level_b * (1 - norm_a * antagonism_strength * 0.5)
        
        return max(0.0, adjusted_a), max(0.0, adjusted_b)
    
    def circadian_rhythm(
        self,
        hormone_type: HormoneType,
        hour_of_day: float,
        base_level: float = 20.0
    ) -> float:
        """
        昼夜节律 / Circadian rhythm modulation
        
        Calculates hormone level based on circadian phase.
        
        Args:
            hormone_type: Type of hormone
            hour_of_day: Current hour (0-24)
            base_level: Baseline level without circadian influence
            
        Returns:
            Adjusted hormone level
        """
        if hormone_type == HormoneType.MELATONIN:
            # Melatonin peaks at night
            # Gaussian-like peak around peak hour
            distance_from_peak = min(
                abs(hour_of_day - self.melatonin_peak_hour),
                abs(hour_of_day - (self.melatonin_peak_hour + 24))
            )
            circadian_factor = math.exp(-(distance_from_peak ** 2) / 20)
            return base_level + self.melatonin_amplitude * circadian_factor
        
        elif hormone_type == HormoneType.CORTISOL:
            # Cortisol peaks in morning (wake response)
            distance_from_peak = min(
                abs(hour_of_day - self.cortisol_peak_hour),
                abs(hour_of_day - (self.cortisol_peak_hour + 24))
            )
            circadian_factor = math.exp(-(distance_from_peak ** 2) / 18)
            return base_level + self.cortisol_amplitude * circadian_factor
        
        # No circadian modulation for other hormones
        return base_level
    
    def get_feedback_node(self, hormone_type: HormoneType) -> FeedbackNode:
        """获取反馈节点 / Get feedback node for a hormone"""
        return self.feedback_nodes.get(
            hormone_type,
            FeedbackNode(
                hormone_type=hormone_type,
                setpoint=50.0,
                current_level=50.0,
                gain=0.5,
                feedback_type="negative"
            )
        )
    
    def set_setpoint(self, hormone_type: HormoneType, setpoint: float) -> None:
        """设定目标值 / Set setpoint for a hormone"""
        if hormone_type in self.feedback_nodes:
            self.feedback_nodes[hormone_type].setpoint = setpoint


# Example usage
if __name__ == "__main__":
    async def demo():
        system = EndocrineSystem()
        await system.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 内分泌系统演示")
        print("Endocrine System Demo")
        print("=" * 60)
        
        # Show initial state
        print("\n初始激素水平 / Initial hormone levels:")
        for hormone_type, level in system.get_all_hormone_levels().items():
            print(f"  {hormone_type.cn_name}: {level:.1f}")
        
        # Trigger emotions
        print("\n触发情绪反应 / Triggering emotional responses:")
        
        print("\n1. 快乐 / Joy:")
        await system.trigger_emotional_response("joy", intensity=0.8)
        print(f"   多巴胺: {system.get_hormone_level(HormoneType.DOPAMINE):.1f}")
        print(f"   血清素: {system.get_hormone_level(HormoneType.SEROTONIN):.1f}")
        
        print("\n2. 压力 / Stress:")
        await system.trigger_stress_response(0.6, stress_type="acute")
        print(f"   肾上腺素: {system.get_hormone_level(HormoneType.ADRENALINE):.1f}")
        print(f"   皮质醇: {system.get_hormone_level(HormoneType.CORTISOL):.1f}")
        
        # Show systemic effects
        print("\n系统性影响 / Systemic effects:")
        effects = system.calculate_systemic_effects()
        for system_name, value in effects.items():
            print(f"  {system_name}: {value:.2f}")
        
        await system.shutdown()
        print("\n系统已关闭 / System shutdown complete")
        
        # Hormone Kinetics Demo
        print("\n" + "=" * 60)
        print("激素动力学演示 / Hormone Kinetics Demo")
        print("=" * 60)
        
        kinetics = HormoneKinetics()
        
        print("\n3. 半衰期代谢 / Half-life metabolism:")
        initial = 80.0
        for hours in [0.5, 1.0, 2.0, 4.0]:
            remaining = kinetics.metabolize(initial, HormoneType.CORTISOL, hours)
            print(f"   {hours}小时后 / after {hours}h: {remaining:.1f} (半衰期 / half-life: 1.5h)")
        
        print("\n4. 受体占用 (Hill方程) / Receptor occupancy (Hill equation):")
        for level in [10, 20, 40, 80]:
            occupancy = kinetics.calculate_occupancy(level, kd=30.0, hill_coefficient=1.5)
            print(f"   激素水平 {level}: 占用率 / occupancy: {occupancy:.2%}")
        
        print("\n5. 分泌调节 / Secretion regulation:")
        for t in [0, 0.25, 0.5, 0.75, 1.0]:
            secretion = kinetics.calculate_secretion(
                basal_rate=10.0,
                stimulus=20.0,
                pulse_frequency=4.0,
                time_hours=t
            )
            print(f"   t={t}h: 分泌率 / secretion rate: {secretion:.2f}")
        
        # Feedback Loop Demo
        print("\n" + "=" * 60)
        print("反馈回路演示 / Feedback Loop Demo")
        print("=" * 60)
        
        feedback = FeedbackLoop()
        
        print("\n6. HPA轴模拟 / HPA axis simulation:")
        hpa_result = feedback.simulate_hpa_axis(stress_input=30.0, simulation_hours=1.0)
        print(f"   初始CRH: {hpa_result['crh'][0]:.1f}")
        print(f"   峰值ACTH: {max(hpa_result['acth']):.1f}")
        print(f"   峰值皮质醇: {max(hpa_result['cortisol']):.1f}")
        
        print("\n7. 负反馈调节 / Negative feedback:")
        cortisol_levels = [20, 40, 60, 80]
        for level in cortisol_levels:
            inhibition = feedback.negative_feedback(
                HormoneType.CORTISOL,
                HormoneType.ADRENALINE,
                level
            )
            print(f"   皮质醇 / cortisol {level}: 抑制 / inhibition: {inhibition:.2%}")
        
        print("\n8. 昼夜节律 / Circadian rhythm:")
        for hour in [0, 6, 12, 18, 22]:
            melatonin = feedback.circadian_rhythm(HormoneType.MELATONIN, hour, base_level=5.0)
            cortisol = feedback.circadian_rhythm(HormoneType.CORTISOL, hour, base_level=20.0)
            print(f"   {hour:02d}:00 - 褪黑素 / melatonin: {melatonin:.1f}, 皮质醇 / cortisol: {cortisol:.1f}")
    
    asyncio.run(demo())
