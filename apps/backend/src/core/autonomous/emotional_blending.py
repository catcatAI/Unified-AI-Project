"""
Angela AI v6.0 - Emotional Blending System
情绪混合系统

Implements the PAD (Pleasure-Arousal-Dominance) emotional model with
emotional blending algorithms, physiological/cognitive/hormonal influences,
and multi-modal emotional expression.

Features:
- PAD emotional model implementation
- Emotion blending and mixing algorithms
- Physiological, cognitive, and hormonal influence on emotions
- Emotional expression (facial expressions, tone of voice, behavior)
- Dynamic emotional transitions

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any, Set
from datetime import datetime, timedelta
import asyncio
import math


class BasicEmotion(Enum):
    """基本情绪类型 / Basic emotion types"""
    JOY = ("喜悦", "Joy", (0.8, 0.6, 0.3))
    SADNESS = ("悲伤", "Sadness", (-0.8, -0.4, -0.4))
    ANGER = ("愤怒", "Anger", (-0.7, 0.7, 0.6))
    FEAR = ("恐惧", "Fear", (-0.7, 0.8, -0.6))
    DISGUST = ("厌恶", "Disgust", (-0.6, 0.2, 0.3))
    SURPRISE = ("惊讶", "Surprise", (0.3, 0.9, 0.0))
    TRUST = ("信任", "Trust", (0.7, 0.2, -0.4))
    ANTICIPATION = ("期待", "Anticipation", (0.4, 0.5, 0.2))
    LOVE = ("爱", "Love", (0.9, 0.5, 0.1))
    CALM = ("平静", "Calm", (0.5, -0.5, -0.3))
    
    def __init__(self, cn_name: str, en_name: str, pad_values: Tuple[float, float, float]):
        self.cn_name = cn_name
        self.en_name = en_name
        self.p_val, self.a_val, self.d_val = pad_values  # Pleasure, Arousal, Dominance


@dataclass
class PADEmotion:
    """
    PAD情绪模型 / PAD (Pleasure-Arousal-Dominance) emotional state
    
    PAD Model:
    - Pleasure (P): -1 (unpleasant) to 1 (pleasant)
    - Arousal (A): -1 (calm/sleepy) to 1 (excited/alert)
    - Dominance (D): -1 (submissive) to 1 (dominant)
    """
    pleasure: float     # -1 to 1
    arousal: float      # -1 to 1
    dominance: float    # -1 to 1
    intensity: float = 1.0  # Overall intensity 0-1
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        self.pleasure = max(-1.0, min(1.0, self.pleasure))
        self.arousal = max(-1.0, min(1.0, self.arousal))
        self.dominance = max(-1.0, min(1.0, self.dominance))
        self.intensity = max(0.0, min(1.0, self.intensity))
    
    def to_basic_emotions(self) -> List[Tuple[BasicEmotion, float]]:
        """Convert PAD values to basic emotions with matching scores"""
        matches = []
        
        for emotion in BasicEmotion:
            # Calculate Euclidean distance in PAD space
            distance = math.sqrt(
                (self.pleasure - emotion.p_val) ** 2 +
                (self.arousal - emotion.a_val) ** 2 +
                (self.dominance - emotion.d_val) ** 2
            )
            
            # Convert distance to similarity (closer = higher score)
            similarity = max(0, 1 - distance / 3.0)
            matches.append((emotion, similarity))
        
        # Sort by similarity
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def distance_to(self, other: PADEmotion) -> float:
        """Calculate Euclidean distance to another PAD state"""
        return math.sqrt(
            (self.pleasure - other.pleasure) ** 2 +
            (self.arousal - other.arousal) ** 2 +
            (self.dominance - other.dominance) ** 2
        )
    
    def blend_with(self, other: PADEmotion, ratio: float = 0.5) -> PADEmotion:
        """Blend with another emotion using specified ratio"""
        r = max(0.0, min(1.0, ratio))
        return PADEmotion(
            pleasure=self.pleasure * (1 - r) + other.pleasure * r,
            arousal=self.arousal * (1 - r) + other.arousal * r,
            dominance=self.dominance * (1 - r) + other.dominance * r,
            intensity=max(self.intensity, other.intensity)
        )
    
    @classmethod
    def from_basic_emotion(
        cls, 
        emotion: BasicEmotion, 
        intensity: float = 1.0
    ) -> PADEmotion:
        """Create PAD emotion from basic emotion"""
        return cls(
            pleasure=emotion.p_val * intensity,
            arousal=emotion.a_val * intensity,
            dominance=emotion.d_val * intensity,
            intensity=intensity
        )


@dataclass
class FacialExpression:
    """面部表情 / Facial expression parameters"""
    smile: float = 0.0           # 微笑 (-1 to 1, negative = frown)
    eyebrow_raise: float = 0.0   # 挑眉 (-1 to 1)
    eye_widening: float = 0.0    # 眼睛睁大 (-1 to 1)
    mouth_open: float = 0.0      # 张嘴 (0 to 1)
    blush: float = 0.0           # 脸红 (0 to 1)
    
    def __post_init__(self):
        self.smile = max(-1.0, min(1.0, self.smile))
        self.eyebrow_raise = max(-1.0, min(1.0, self.eyebrow_raise))
        self.eye_widening = max(-1.0, min(1.0, self.eye_widening))
        self.mouth_open = max(0.0, min(1.0, self.mouth_open))
        self.blush = max(0.0, min(1.0, self.blush))


@dataclass
class VocalTone:
    """语调 / Vocal tone parameters"""
    pitch: float = 1.0           # 音高 (0.5 to 1.5, 1.0 = normal)
    speed: float = 1.0           # 语速 (0.5 to 1.5, 1.0 = normal)
    volume: float = 1.0          # 音量 (0.5 to 1.5, 1.0 = normal)
    tremor: float = 0.0          # 颤抖 (0 to 1)
    warmth: float = 0.5          # 温暖度 (-1 to 1)
    
    def __post_init__(self):
        self.pitch = max(0.5, min(1.5, self.pitch))
        self.speed = max(0.5, min(1.5, self.speed))
        self.volume = max(0.5, min(1.5, self.volume))
        self.tremor = max(0.0, min(1.0, self.tremor))
        self.warmth = max(-1.0, min(1.0, self.warmth))


@dataclass
class BehavioralExpression:
    """行为表达 / Behavioral expression parameters"""
    posture: str = "neutral"     # 姿势
    gesture_intensity: float = 0.0  # 手势强度 (0 to 1)
    proximity_seeking: float = 0.0  # 寻求亲近 (-1 to 1)
    movement_speed: float = 1.0     # 移动速度 (0.5 to 1.5)
    eye_contact: float = 0.5        # 眼神接触 (0 to 1)


@dataclass
class EmotionalExpression:
    """情绪表达 / Complete emotional expression"""
    facial: FacialExpression = field(default_factory=FacialExpression)
    vocal: VocalTone = field(default_factory=VocalTone)
    behavioral: BehavioralExpression = field(default_factory=BehavioralExpression)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EmotionalInfluence:
    """情绪影响因素 / Emotional influence factors"""
    source: str                  # 来源 (physiological/cognitive/hormonal)
    factor_type: str             # 因素类型
    weight: float               # 影响权重 (0-1)
    value: float                # 影响值 (-1 to 1)


class EmotionalBlendingSystem:
    """
    情绪混合系统主类 / Main emotional blending system class
    
    Implements the PAD emotional model for Angela AI with dynamic emotion
    blending, multi-factor influences, and multi-modal emotional expression.
    
    Attributes:
        current_emotion: Current PAD emotional state
        emotion_history: History of emotional states
        baseline_emotion: Default/baseline emotional state
        influences: Active emotional influences
        expression_profile: Current emotional expression parameters
    
    Example:
        >>> eb_system = EmotionalBlendingSystem()
        >>> await eb_system.initialize()
        >>> 
        >>> # Set emotional state from basic emotion
        >>> eb_system.set_emotion_from_basic(BasicEmotion.JOY, intensity=0.8)
        >>> 
        >>> # Apply physiological influence
        >>> eb_system.apply_influence("physiological", "heart_rate", 0.3, 0.6)
        >>> 
        >>> # Get current expression
        >>> expression = eb_system.get_emotional_expression()
        >>> print(f"Smile: {expression.facial.smile:.2f}")
        
        >>> # Blend emotions
        >>> new_emotion = eb_system.blend_emotions(
        ...     eb_system.current_emotion,
        ...     PADEmotion.from_basic_emotion(BasicEmotion.SURPRISE),
        ...     ratio=0.3
        ... )
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Emotional state
        self.current_emotion: PADEmotion = PADEmotion(0.0, 0.0, 0.0, 0.5)
        self.baseline_emotion: PADEmotion = PADEmotion(0.2, -0.1, -0.1, 0.3)
        self.target_emotion: Optional[PADEmotion] = None
        
        # History and tracking
        self.emotion_history: List[PADEmotion] = []
        self.history_limit: int = 1000
        
        # Influences
        self.influences: List[EmotionalInfluence] = []
        self.influence_decay_rate: float = 0.95  # Per minute
        
        # Expression
        self.current_expression: EmotionalExpression = EmotionalExpression()
        
        # Transition
        self.transition_speed: float = 0.1  # How fast emotions change
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._emotion_change_callbacks: List[Callable[[PADEmotion, PADEmotion], None]] = []
        self._expression_callbacks: List[Callable[[EmotionalExpression], None]] = []
    
    async def initialize(self):
        """Initialize the emotional blending system"""
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
        """Background update loop for emotion dynamics"""
        while self._running:
            await self._update_emotion()
            await self._decay_influences()
            await self._update_expression()
            await asyncio.sleep(1.0)  # 1 second update interval
    
    async def _update_emotion(self):
        """Update current emotion toward target or baseline"""
        if self.target_emotion:
            # Move toward target emotion
            self.current_emotion = self._interpolate_emotions(
                self.current_emotion,
                self.target_emotion,
                self.transition_speed
            )
            
            # Check if reached target
            if self.current_emotion.distance_to(self.target_emotion) < 0.05:
                self.target_emotion = None
        else:
            # Drift toward baseline
            self.current_emotion = self._interpolate_emotions(
                self.current_emotion,
                self.baseline_emotion,
                self.transition_speed * 0.3
            )
        
        # Apply influences
        for influence in self.influences:
            if influence.source == "physiological":
                self._apply_physiological_influence(influence)
            elif influence.source == "cognitive":
                self._apply_cognitive_influence(influence)
            elif influence.source == "hormonal":
                self._apply_hormonal_influence(influence)
        
        # Record history
        self.emotion_history.append(self.current_emotion)
        if len(self.emotion_history) > self.history_limit:
            self.emotion_history.pop(0)
        
        # Notify callbacks
        if len(self.emotion_history) > 1:
            prev = self.emotion_history[-2]
            curr = self.current_emotion
            if prev.distance_to(curr) > 0.05:
                for callback in self._emotion_change_callbacks:
                    try:
                        callback(prev, curr)
                    except Exception:
                        pass
    
    async def _decay_influences(self):
        """Decay influence strengths over time"""
        remaining = []
        for influence in self.influences:
            influence.weight *= self.influence_decay_rate
            if influence.weight > 0.01:
                remaining.append(influence)
        self.influences = remaining
    
    async def _update_expression(self):
        """Update emotional expression based on current emotion"""
        self.current_expression = self._calculate_expression(self.current_emotion)
        
        # Notify expression callbacks
        for callback in self._expression_callbacks:
            try:
                callback(self.current_expression)
            except Exception:
                pass
    
    def _interpolate_emotions(
        self, 
        from_emotion: PADEmotion, 
        to_emotion: PADEmotion, 
        t: float
    ) -> PADEmotion:
        """Interpolate between two emotional states"""
        t = max(0.0, min(1.0, t))
        return PADEmotion(
            pleasure=from_emotion.pleasure * (1 - t) + to_emotion.pleasure * t,
            arousal=from_emotion.arousal * (1 - t) + to_emotion.arousal * t,
            dominance=from_emotion.dominance * (1 - t) + to_emotion.dominance * t,
            intensity=from_emotion.intensity * (1 - t) + to_emotion.intensity * t
        )
    
    def _apply_physiological_influence(self, influence: EmotionalInfluence):
        """Apply physiological influence to emotion"""
        # High arousal physiological states increase arousal dimension
        if influence.factor_type in ["heart_rate", "blood_pressure", "cortisol"]:
            self.current_emotion.arousal += influence.value * influence.weight * 0.5
        
        # Pain or discomfort reduces pleasure
        if influence.factor_type in ["pain", "discomfort", "fatigue"]:
            self.current_emotion.pleasure -= abs(influence.value) * influence.weight * 0.5
        
        # Endorphins and comfort increase pleasure
        if influence.factor_type in ["endorphins", "comfort", "relaxation"]:
            self.current_emotion.pleasure += influence.value * influence.weight * 0.5
    
    def _apply_cognitive_influence(self, influence: EmotionalInfluence):
        """Apply cognitive influence to emotion"""
        # Positive/negative thoughts affect pleasure
        if influence.factor_type in ["positive_thought", "achievement", "success"]:
            self.current_emotion.pleasure += influence.value * influence.weight * 0.4
            self.current_emotion.dominance += influence.weight * 0.2
        
        if influence.factor_type in ["negative_thought", "failure", "threat"]:
            self.current_emotion.pleasure -= abs(influence.value) * influence.weight * 0.4
            self.current_emotion.dominance -= influence.weight * 0.2
        
        # Cognitive load affects arousal
        if influence.factor_type == "cognitive_load":
            self.current_emotion.arousal += influence.value * influence.weight * 0.3
        
        # Uncertainty affects dominance negatively
        if influence.factor_type == "uncertainty":
            self.current_emotion.dominance -= abs(influence.value) * influence.weight * 0.4
    
    def _apply_hormonal_influence(self, influence: EmotionalInfluence):
        """Apply hormonal influence to emotion"""
        # Dopamine increases pleasure
        if influence.factor_type == "dopamine":
            self.current_emotion.pleasure += influence.value * influence.weight * 0.6
        
        # Serotonin stabilizes and increases pleasure
        if influence.factor_type == "serotonin":
            self.current_emotion.pleasure += influence.value * influence.weight * 0.3
            self.current_emotion.arousal *= (1 - influence.weight * 0.2)  # Calming
        
        # Adrenaline increases arousal
        if influence.factor_type in ["adrenaline", "cortisol"]:
            self.current_emotion.arousal += abs(influence.value) * influence.weight * 0.7
        
        # Oxytocin increases pleasure and reduces dominance (bonding)
        if influence.factor_type == "oxytocin":
            self.current_emotion.pleasure += influence.value * influence.weight * 0.5
            self.current_emotion.dominance -= influence.weight * 0.3
    
    def _calculate_expression(self, emotion: PADEmotion) -> EmotionalExpression:
        """Calculate multi-modal expression from PAD emotion"""
        # Facial expression
        facial = FacialExpression()
        
        # Pleasure affects smile
        if emotion.pleasure > 0:
            facial.smile = emotion.pleasure * emotion.intensity
        else:
            facial.smile = emotion.pleasure * emotion.intensity  # Negative = frown
        
        # Arousal affects eye widening and eyebrow raise
        facial.eye_widening = emotion.arousal * emotion.intensity * 0.7
        facial.eyebrow_raise = emotion.arousal * emotion.intensity * 0.5
        
        # High arousal + positive pleasure = excitement = mouth open slightly
        if emotion.arousal > 0.5 and emotion.pleasure > 0:
            facial.mouth_open = (emotion.arousal + emotion.pleasure) / 2 * emotion.intensity * 0.5
        
        # Blush for high arousal situations (embarrassment, excitement)
        if emotion.arousal > 0.6 and abs(emotion.pleasure) > 0.5:
            facial.blush = emotion.arousal * emotion.intensity * 0.6
        
        # Vocal expression
        vocal = VocalTone()
        
        # Arousal affects pitch and speed
        vocal.pitch = 1.0 + emotion.arousal * 0.3
        vocal.speed = 1.0 + emotion.arousal * 0.3
        
        # Pleasure affects warmth
        vocal.warmth = emotion.pleasure * emotion.intensity
        
        # High arousal + negative pleasure = fear/anger = tremor
        if emotion.arousal > 0.6 and emotion.pleasure < 0:
            vocal.tremor = emotion.arousal * abs(emotion.pleasure) * emotion.intensity
        
        # Volume based on arousal and dominance
        vocal.volume = 1.0 + (emotion.arousal + emotion.dominance) * 0.25
        
        # Behavioral expression
        behavioral = BehavioralExpression()
        
        # Dominance affects posture and eye contact
        if emotion.dominance > 0.3:
            behavioral.posture = "confident"
            behavioral.eye_contact = 0.5 + emotion.dominance * 0.5
        elif emotion.dominance < -0.3:
            behavioral.posture = "submissive"
            behavioral.eye_contact = 0.5 + emotion.dominance * 0.5
        
        # Arousal affects movement speed and gestures
        behavioral.movement_speed = 1.0 + emotion.arousal * 0.5
        behavioral.gesture_intensity = abs(emotion.arousal) * emotion.intensity
        
        # Proximity seeking based on pleasure and dominance
        behavioral.proximity_seeking = emotion.pleasure * 0.5 - emotion.dominance * 0.3
        
        return EmotionalExpression(facial=facial, vocal=vocal, behavioral=behavioral)
    
    def set_emotion_from_basic(
        self, 
        emotion: BasicEmotion, 
        intensity: float = 1.0,
        transition: bool = True
    ):
        """
        Set emotional state from a basic emotion
        
        Args:
            emotion: Basic emotion to set
            intensity: Intensity of the emotion (0-1)
            transition: Whether to transition gradually
        """
        target = PADEmotion.from_basic_emotion(emotion, intensity)
        
        if transition:
            self.target_emotion = target
        else:
            self.current_emotion = target
    
    def set_emotion_direct(self, emotion: PADEmotion, transition: bool = True):
        """Set emotional state directly"""
        if transition:
            self.target_emotion = emotion
        else:
            self.current_emotion = emotion
    
    def blend_emotions(
        self, 
        emotion1: PADEmotion, 
        emotion2: PADEmotion, 
        ratio: float = 0.5
    ) -> PADEmotion:
        """Blend two emotions together"""
        return emotion1.blend_with(emotion2, ratio)
    
    def apply_influence(
        self, 
        source: str, 
        factor_type: str, 
        value: float, 
        weight: float = 1.0
    ):
        """
        Apply an emotional influence
        
        Args:
            source: Source type (physiological/cognitive/hormonal)
            factor_type: Specific factor name
            value: Influence value (-1 to 1)
            weight: Influence weight (0-1)
        """
        influence = EmotionalInfluence(
            source=source,
            factor_type=factor_type,
            weight=weight,
            value=value
        )
        self.influences.append(influence)
    
    def get_emotional_expression(self) -> EmotionalExpression:
        """Get current emotional expression"""
        return self.current_expression
    
    def get_dominant_emotion(self) -> Tuple[BasicEmotion, float]:
        """Get the dominant basic emotion and its strength"""
        matches = self.current_emotion.to_basic_emotions()
        return matches[0] if matches else (BasicEmotion.CALM, 0.0)
    
    def get_emotion_history(
        self, 
        duration: Optional[timedelta] = None
    ) -> List[PADEmotion]:
        """Get emotional history for a time period"""
        if duration is None:
            return self.emotion_history.copy()
        
        cutoff = datetime.now() - duration
        return [e for e in self.emotion_history if e.timestamp > cutoff]
    
    def register_emotion_change_callback(
        self, 
        callback: Callable[[PADEmotion, PADEmotion], None]
    ):
        """Register callback for emotion changes"""
        self._emotion_change_callbacks.append(callback)
    
    def register_expression_callback(
        self, 
        callback: Callable[[EmotionalExpression], None]
    ):
        """Register callback for expression updates"""
        self._expression_callbacks.append(callback)
    
    def get_emotion_summary(self) -> Dict[str, Any]:
        """Get comprehensive emotion summary"""
        dominant_emotion, confidence = self.get_dominant_emotion()
        
        return {
            "pad_state": {
                "pleasure": self.current_emotion.pleasure,
                "arousal": self.current_emotion.arousal,
                "dominance": self.current_emotion.dominance,
                "intensity": self.current_emotion.intensity,
            },
            "dominant_emotion": dominant_emotion.en_name,
            "dominant_emotion_cn": dominant_emotion.cn_name,
            "confidence": confidence,
            "expression": {
                "facial_smile": self.current_expression.facial.smile,
                "vocal_warmth": self.current_expression.vocal.warmth,
                "behavioral_posture": self.current_expression.behavioral.posture,
            },
            "active_influences": len(self.influences),
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        eb_system = EmotionalBlendingSystem()
        await eb_system.initialize()
        
        print("=" * 60)
        print("Angela AI v6.0 - 情绪混合系统演示")
        print("Emotional Blending System Demo")
        print("=" * 60)
        
        # Set emotion
        print("\n设置情绪状态 / Setting emotional state:")
        eb_system.set_emotion_from_basic(BasicEmotion.JOY, intensity=0.8)
        await asyncio.sleep(1)
        
        summary = eb_system.get_emotion_summary()
        print(f"  主要情绪: {summary['dominant_emotion_cn']}")
        print(f"  置信度: {summary['confidence']:.2f}")
        print(f"  PAD: P={summary['pad_state']['pleasure']:.2f}, "
              f"A={summary['pad_state']['arousal']:.2f}, "
              f"D={summary['pad_state']['dominance']:.2f}")
        
        # Get expression
        print("\n情绪表达 / Emotional expression:")
        expression = eb_system.get_emotional_expression()
        print(f"  面部表情: 微笑={expression.facial.smile:.2f}, "
              f"挑眉={expression.facial.eyebrow_raise:.2f}")
        print(f"  语调: 音高={expression.vocal.pitch:.2f}, "
              f"温暖度={expression.vocal.warmth:.2f}")
        print(f"  行为: 姿势={expression.behavioral.posture}, "
              f"手势强度={expression.behavioral.gesture_intensity:.2f}")
        
        # Apply influences
        print("\n应用影响因素 / Applying influences:")
        eb_system.apply_influence("physiological", "heart_rate", 0.6, 0.5)
        eb_system.apply_influence("hormonal", "dopamine", 0.7, 0.6)
        await asyncio.sleep(1)
        
        summary = eb_system.get_emotion_summary()
        print(f"  更新后PAD: P={summary['pad_state']['pleasure']:.2f}, "
              f"A={summary['pad_state']['arousal']:.2f}")
        
        # Blend emotions
        print("\n情绪混合 / Emotion blending:")
        joy = PADEmotion.from_basic_emotion(BasicEmotion.JOY, 0.7)
        surprise = PADEmotion.from_basic_emotion(BasicEmotion.SURPRISE, 0.6)
        blended = eb_system.blend_emotions(joy, surprise, ratio=0.4)
        print(f"  喜悦 + 惊讶 (40%): P={blended.pleasure:.2f}, "
              f"A={blended.arousal:.2f}, D={blended.dominance:.2f}")
        
        await eb_system.shutdown()
        print("\n系统已关闭 / System shutdown complete")
    
    asyncio.run(demo())
