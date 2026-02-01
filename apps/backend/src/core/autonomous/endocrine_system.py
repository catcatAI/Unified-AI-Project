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

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
import asyncio
import math


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
        HormoneType.ENDorphin: {
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
                HormoneType.ENDorphin: 15.0 * intensity,
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
                HormoneType.TESTOSTERONE: 15.0 * intensity,
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
                HormoneType.ENDorphin: 15.0 * intensity,
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
                HormoneType.ENDorphin: 25.0 * intensity,
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
                HormoneType.ENDorphin: 10.0 * intensity,
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
                HormoneType.ENDorphin: 20.0 * intensity,
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
                except Exception:
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
            self.hormones[HormoneType.ENDorphin].get_normalized_level() * 0.2 -
            self.hormones[HormoneType.CORTISOL].get_normalized_level() * 0.1
        )
        
        # Stress resilience
        effects["stress_resilience"] += (
            self.hormones[HormoneType.SEROTONIN].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.OXYTOCIN].get_normalized_level() * 0.3 +
            self.hormones[HormoneType.ENDorphin].get_normalized_level() * 0.2 -
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
            self.hormones[HormoneType.ENDorphin].get_normalized_level() * 0.2 -
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
    
    asyncio.run(demo())
