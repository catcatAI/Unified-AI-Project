"""
Angela AI v6.0 - Autonomic Nervous System
自主神经系统

Simulates the sympathetic and parasympathetic nervous systems controlling
arousal levels and their effects on physiological, emotional, and cognitive states.

Features:
- Sympathetic and parasympathetic branches
- Arousal level (0-100) with dynamic regulation
- Stimuli and inhibition factors
- Effects on physiology, emotion, and cognition
- Homeostatic regulation

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
import logging
logger = logging.getLogger(__name__)


class NerveType(Enum):
    """神经类型 / Nerve types"""
    SYMPATHETIC = ("交感神经", "Sympathetic", "fight_or_flight")
    PARASYMPATHETIC = ("副交感神经", "Parasympathetic", "rest_and_digest")
    ENTERIC = ("肠神经系统", "Enteric", "digestion")
    
    def __init__(self, cn_name: str, en_name: str, function: str):
        self.cn_name = cn_name
        self.en_name = en_name
        self.function = function


class ANSState(Enum):
    """自主神经系统状态 / ANS states"""
    DEEP_REST = ("深度休息", 0, 20)           # 副交感主导
    RELAXED = ("放松", 20, 40)               # 轻度副交感
    BALANCED = ("平衡", 40, 60)              # 平衡状态
    ALERT = ("警觉", 60, 80)                 # 轻度交感
    HIGHLY_AROUSED = ("高度唤醒", 80, 100)    # 交感主导
    
    def __init__(self, cn_name: str, min_level: int, max_level: int):
        self.cn_name = cn_name
        self.min_level = min_level
        self.max_level = max_level
    
    @classmethod
    def from_arousal(cls, level: float) -> ANSState:
        """根据唤醒水平获取状态"""
        for state in cls:
            if state.min_level <= level < state.max_level:
                return state
        return cls.HIGHLY_AROUSED


@dataclass
class StimulusFactor:
    """刺激因素 / Stimulus factor"""
    name: str
    nerve_type: NerveType
    intensity: float  # 0-1
    duration: float   # seconds
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PhysiologicalEffects:
    """生理效应 / Physiological effects"""
    heart_rate: float       # 心率 (bpm)
    blood_pressure: float   # 血压 (mmHg normalized)
    respiration_rate: float # 呼吸频率 (breaths/min)
    pupil_dilation: float   # 瞳孔扩张 (0-1)
    digestion: float        # 消化功能 (0-1)
    sweating: float         # 出汗程度 (0-1)
    

@dataclass
class EmotionalEffects:
    """情绪效应 / Emotional effects"""
    anxiety: float          # 焦虑 (0-1)
    calmness: float         # 平静 (0-1)
    excitement: float       # 兴奋 (0-1)
    irritability: float     # 易怒 (0-1)
    confidence: float       # 自信 (0-1)


@dataclass
class CognitiveEffects:
    """认知效应 / Cognitive effects"""
    focus: float            # 专注力 (0-1)
    reaction_time: float    # 反应时间 (normalized)
    memory_consolidation: float  # 记忆巩固 (0-1)
    decision_speed: float   # 决策速度 (0-1)
    creativity: float       # 创造力 (0-1)


class AutonomicNervousSystem:
    """
    自主神经系统主类 / Main autonomic nervous system class
    
    Simulates the sympathetic and parasympathetic nervous systems, controlling
    arousal levels and their cascading effects on Angela's physiology, emotions,
    and cognitive functions.
    
    Attributes:
        arousal_level: Current arousal level (0-100)
        sympathetic_tone: Sympathetic nervous system activation (0-100)
        parasympathetic_tone: Parasympathetic nervous system activation (0-100)
        active_stimuli: Currently active stimulus factors
        homeostatic_target: Target arousal level for homeostasis
    
    Example:
        >>> ans = AutonomicNervousSystem()
        >>> await ans.initialize()
        >>> 
        >>> # Apply sympathetic stimulus (stress)
        >>> await ans.apply_stimulus("stress", NerveType.SYMPATHETIC, intensity=0.7)
        >>> 
        >>> # Check effects
        >>> effects = ans.get_current_effects()
        >>> print(f"Heart rate: {effects.physiological.heart_rate:.0f} bpm")
        >>> print(f"Focus: {effects.cognitive.focus:.2f}")
        
        >>> # Apply calming stimulus
        >>> await ans.apply_stimulus("meditation", NerveType.PARASYMPATHETIC, intensity=0.6)
    """
    
    # Base physiological parameters
    BASE_HEART_RATE = 70.0  # bpm
    BASE_RESP_RATE = 16.0   # breaths/min
    BASE_PUPIL_SIZE = 0.3   # normalized
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Core state
        self.arousal_level: float = 50.0  # 0-100
        self.sympathetic_tone: float = 30.0  # 0-100
        self.parasympathetic_tone: float = 50.0  # 0-100
        
        # Stimuli tracking
        self.active_stimuli: List[StimulusFactor] = []
        self.stimulus_history: List[StimulusFactor] = []
        
        # Homeostasis
        self.homeostatic_target: float = 50.0
        self.homeostatic_strength: float = 0.05  # Return to baseline rate
        
        # Running state
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._state_change_callbacks: List[Callable[[ANSState, ANSState], None]] = []
        self._arousal_callbacks: List[Callable[[float], None]] = []
        
        # Last state for change detection
        self._last_state: ANSState = ANSState.BALANCED
    
    async def initialize(self):
        """Initialize the autonomic nervous system"""
        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
    
    async def shutdown(self):
        """Shutdown the system"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
    
    async def _update_loop(self):
        """Background update loop"""
        while self._running:
            await self._decay_stimuli()
            await self._apply_homeostasis()
            await self._calculate_tones()
            await self._detect_state_change()
            await asyncio.sleep(0.5)  # 500ms update interval
    
    async def _decay_stimuli(self):
        """Decay active stimuli over time"""
        current_time = datetime.now()
        remaining_stimuli = []
        
        for stimulus in self.active_stimuli:
            elapsed = (current_time - stimulus.timestamp).total_seconds()
            if elapsed < stimulus.duration:
                # Decay intensity over time
                remaining_intensity = stimulus.intensity * (
                    1 - (elapsed / stimulus.duration)
                )
                if remaining_intensity > 0.05:
                    remaining_stimuli.append(stimulus)
        
        self.active_stimuli = remaining_stimuli
    
    async def _apply_homeostasis(self):
        """Apply homeostatic drive toward baseline"""
        # Gradually return to homeostatic target
        diff = self.homeostatic_target - self.arousal_level
        adjustment = diff * self.homeostatic_strength
        self.arousal_level += adjustment
        self.arousal_level = max(0, min(100, self.arousal_level))
    
    async def _calculate_tones(self):
        """Calculate sympathetic and parasympathetic tones"""
        # Base calculation from arousal level
        # High arousal = high sympathetic, low parasympathetic
        self.sympathetic_tone = min(100, self.arousal_level * 1.2)
        self.parasympathetic_tone = max(0, 100 - self.arousal_level * 1.2)
        
        # Apply active stimuli
        for stimulus in self.active_stimuli:
            if stimulus.nerve_type == NerveType.SYMPATHETIC:
                boost = stimulus.intensity * 30
                self.sympathetic_tone = min(100, self.sympathetic_tone + boost)
                self.parasympathetic_tone = max(0, self.parasympathetic_tone - boost * 0.5)
            elif stimulus.nerve_type == NerveType.PARASYMPATHETIC:
                boost = stimulus.intensity * 30
                self.parasympathetic_tone = min(100, self.parasympathetic_tone + boost)
                self.sympathetic_tone = max(0, self.sympathetic_tone - boost * 0.5)
    
    async def _detect_state_change(self):
        """Detect and notify state changes"""
        current_state = ANSState.from_arousal(self.arousal_level)
        if current_state != self._last_state:
            for callback in self._state_change_callbacks:
                try:
                    callback(self._last_state, current_state)
                except Exception as e:
                    logger.error(f'Error in {__name__}: {e}', exc_info=True)
                    pass

            self._last_state = current_state
        
        # Arousal level callbacks
        for callback in self._arousal_callbacks:
            try:
                callback(self.arousal_level)
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
                pass

    
    async def apply_stimulus(
        self, 
        name: str, 
        nerve_type: NerveType, 
        intensity: float,
        duration: float = 10.0
    ):
        """
        Apply a stimulus to the nervous system
        
        Args:
            name: Name/description of the stimulus
            nerve_type: Type of nerve pathway (sympathetic/parasympathetic)
            intensity: Intensity of the stimulus (0-1)
            duration: Duration of the stimulus effect in seconds
        """
        stimulus = StimulusFactor(
            name=name,
            nerve_type=nerve_type,
            intensity=intensity,
            duration=duration
        )
        self.active_stimuli.append(stimulus)
        self.stimulus_history.append(stimulus)
        
        # Immediate effect on arousal
        if nerve_type == NerveType.SYMPATHETIC:
            self.arousal_level += intensity * 20
        elif nerve_type == NerveType.PARASYMPATHETIC:
            self.arousal_level -= intensity * 20
        
        self.arousal_level = max(0, min(100, self.arousal_level))
    
    def set_arousal_directly(self, level: float):
        """
        Directly set the arousal level (bypassing stimuli)
        
        Args:
            level: Target arousal level (0-100)
        """
        self.arousal_level = max(0, min(100, level))
    
    def get_current_state(self) -> ANSState:
        """Get current ANS state"""
        return ANSState.from_arousal(self.arousal_level)
    
    def get_current_effects(self) -> Tuple[PhysiologicalEffects, EmotionalEffects, CognitiveEffects]:
        """
        Calculate current effects on physiology, emotion, and cognition
        
        Returns:
            Tuple of (PhysiologicalEffects, EmotionalEffects, CognitiveEffects)
        """
        arousal = self.arousal_level / 100.0  # Normalize to 0-1
        
        # Physiological effects
        physiological = PhysiologicalEffects(
            heart_rate=self.BASE_HEART_RATE + arousal * 60,  # 70-130 bpm
            blood_pressure=1.0 + arousal * 0.4,  # Normalized BP
            respiration_rate=self.BASE_RESP_RATE + arousal * 20,  # 16-36 breaths/min
            pupil_dilation=self.BASE_PUPIL_SIZE + arousal * 0.5,  # 0.3-0.8
            digestion=max(0, 1.0 - arousal * 1.5),  # Decreases with arousal
            sweating=arousal * 0.8 if arousal > 0.6 else 0.0,  # Starts at high arousal
        )
        
        # Emotional effects
        emotional = EmotionalEffects(
            anxiety=max(0, (arousal - 0.5) * 2.0),  # Increases above 50%
            calmness=max(0, 1.0 - arousal * 1.2),  # Decreases with arousal
            excitement=arousal * 0.8 if arousal > 0.4 else arousal * 0.3,
            irritability=max(0, (arousal - 0.7) * 3.0),  # High arousal only
            confidence=0.5 + arousal * 0.3 if arousal < 0.7 else 0.8 - (arousal - 0.7),
        )
        
        # Cognitive effects
        # Optimal arousal for cognition is around 0.6-0.7 (Yerkes-Dodson Law)
        optimal_arousal = 0.65
        arousal_distance = abs(arousal - optimal_arousal)
        
        cognitive = CognitiveEffects(
            focus=max(0, 1.0 - arousal_distance * 2.0),
            reaction_time=1.0 - arousal * 0.4,  # Faster at higher arousal
            memory_consolidation=1.0 - arousal * 0.3,  # Better at lower arousal
            decision_speed=arousal * 0.8 if arousal > 0.5 else arousal * 0.4,
            creativity=max(0, 1.0 - arousal * 1.2),  # Better at lower arousal
        )
        
        return physiological, emotional, cognitive
    
    def get_physiological_effects(self) -> PhysiologicalEffects:
        """Get current physiological effects"""
        return self.get_current_effects()[0]
    
    def get_emotional_effects(self) -> EmotionalEffects:
        """Get current emotional effects"""
        return self.get_current_effects()[1]
    
    def get_cognitive_effects(self) -> CognitiveEffects:
        """Get current cognitive effects"""
        return self.get_current_effects()[2]
    
    def get_active_stimuli(self) -> List[StimulusFactor]:
        """Get list of currently active stimuli"""
        return self.active_stimuli.copy()
    
    def register_state_change_callback(
        self, 
        callback: Callable[[ANSState, ANSState], None]
    ):
        """Register callback for ANS state changes"""
        self._state_change_callbacks.append(callback)
    
    def register_arousal_callback(self, callback: Callable[[float], None]):
        """Register callback for arousal level changes"""
        self._arousal_callbacks.append(callback)
    
    def get_system_summary(self) -> Dict[str, Any]:
        """Get comprehensive system summary"""
        phys, emo, cog = self.get_current_effects()
        
        return {
            "arousal_level": self.arousal_level,
            "state": self.get_current_state().cn_name,
            "sympathetic_tone": self.sympathetic_tone,
            "parasympathetic_tone": self.parasympathetic_tone,
            "active_stimuli_count": len(self.active_stimuli),
            "physiological": {
                "heart_rate": phys.heart_rate,
                "blood_pressure": phys.blood_pressure,
                "respiration_rate": phys.respiration_rate,
                "digestion": phys.digestion,
            },
            "emotional": {
                "anxiety": emo.anxiety,
                "calmness": emo.calmness,
                "excitement": emo.excitement,
            },
            "cognitive": {
                "focus": cog.focus,
                "reaction_time": cog.reaction_time,
                "creativity": cog.creativity,
            },
        }


# Predefined stimulus templates
class StimulusTemplates:
    """预定义刺激模板 / Predefined stimulus templates"""
    
    @staticmethod
    def stress(intensity: float = 0.5) -> Tuple[str, NerveType, float]:
        """Stress stimulus (sympathetic)"""
        return ("stress", NerveType.SYMPATHETIC, intensity)
    
    @staticmethod
    def exercise(intensity: float = 0.6) -> Tuple[str, NerveType, float]:
        """Exercise stimulus (sympathetic)"""
        return ("exercise", NerveType.SYMPATHETIC, intensity)
    
    @staticmethod
    def meditation(intensity: float = 0.5) -> Tuple[str, NerveType, float]:
        """Meditation stimulus (parasympathetic)"""
        return ("meditation", NerveType.PARASYMPATHETIC, intensity)
    
    @staticmethod
    def deep_breathing(intensity: float = 0.4) -> Tuple[str, NerveType, float]:
        """Deep breathing stimulus (parasympathetic)"""
        return ("deep_breathing", NerveType.PARASYMPATHETIC, intensity)
    
    @staticmethod
    def surprise(intensity: float = 0.7) -> Tuple[str, NerveType, float]:
        """Surprise stimulus (sympathetic)"""
        return ("surprise", NerveType.SYMPATHETIC, intensity)
    
    @staticmethod
    def comfort(intensity: float = 0.5) -> Tuple[str, NerveType, float]:
        """Comfort stimulus (parasympathetic)"""
        return ("comfort", NerveType.PARASYMPATHETIC, intensity)


# Example usage
if __name__ == "__main__":
    async def demo():
        ans = AutonomicNervousSystem()
        await ans.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 自主神经系统演示")
        print("Autonomic Nervous System Demo")
        print("=" * 60)
        
        # Initial state
        print("\n初始状态 / Initial state:")
        summary = ans.get_system_summary()
        print(f"  唤醒水平: {summary['arousal_level']:.1f}")
        print(f"  状态: {summary['state']}")
        
        # Apply stress
        print("\n应用压力刺激 / Applying stress stimulus:")
        await ans.apply_stimulus(*StimulusTemplates.stress(intensity=0.8))
        await asyncio.sleep(1)
        
        phys, emo, cog = ans.get_current_effects()
        print(f"  唤醒水平: {ans.arousal_level:.1f}")
        print(f"  心率: {phys.heart_rate:.0f} bpm")
        print(f"  焦虑: {emo.anxiety:.2f}")
        print(f"  专注度: {cog.focus:.2f}")
        
        # Apply meditation
        print("\n应用冥想刺激 / Applying meditation stimulus:")
        await ans.apply_stimulus(*StimulusTemplates.meditation(intensity=0.7))
        await asyncio.sleep(1)
        
        phys, emo, cog = ans.get_current_effects()
        print(f"  唤醒水平: {ans.arousal_level:.1f}")
        print(f"  平静度: {emo.calmness:.2f}")
        print(f"  消化功能: {phys.digestion:.2f}")
        
        # Full summary
        print("\n系统摘要 / System summary:")
        summary = ans.get_system_summary()
        for key, value in summary.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    - {k}: {v:.2f}")
            else:
                print(f"  {key}: {value}")
        
        await ans.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
