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
import logging
logger = logging.getLogger(__name__)


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
                    except Exception as e:
                        logger.error(f'Error in {__name__}: {e}', exc_info=True)
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
            except Exception as e:
                logger.error(f'Error in {__name__}: {e}', exc_info=True)
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


@dataclass
class StateDimension:
    """状态维度 / State dimension"""
    name: str
    cn_name: str
    values: Dict[str, float]  # 维度内的各项指标 / Metrics within dimension
    weight: float = 1.0  # 维度权重
    timestamp: datetime = field(default_factory=datetime.now)


class MultidimensionalStateMatrix:
    """
    多维度状态矩阵 / Multidimensional State Matrix (4D Matrix)
    
    Implements a 4-dimensional state matrix for Angela AI:
    - α Dimension: Physiological (生理维度)
      - energy, comfort, arousal, rest_need
    - β Dimension: Cognitive (认知维度)
      - curiosity, focus, confusion, learning
    - γ Dimension: Emotional (情感维度)
      - happiness, sadness, anger, fear, etc.
    - δ Dimension: Social (社交维度)
      - attention, bond, trust, presence
    
    Features:
    - Inter-dimensional influence modeling
    - State computation and blending
    - Dynamic weight adjustment
    
    Example:
        >>> matrix = MultidimensionalStateMatrix()
        >>> 
        >>> # Set dimension states
        >>> matrix.set_alpha_dimension(energy=0.8, comfort=0.7, arousal=0.6)
        >>> matrix.set_beta_dimension(curiosity=0.9, focus=0.8)
        >>> matrix.set_gamma_dimension(happiness=0.8, sadness=0.1)
        >>> matrix.set_delta_dimension(attention=0.7, trust=0.9)
        >>> 
        >>> # Compute inter-dimensional influences
        >>> matrix.compute_inter_influences()
        >>> 
        >>> # Get overall state summary
        >>> summary = matrix.get_state_summary()
        >>> print(f"Overall wellbeing: {summary['wellbeing']:.2f}")
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize 4 dimensions
        self.alpha = StateDimension(  # Physiological
            name="alpha",
            cn_name="生理维度",
            values={
                "energy": 0.5,
                "comfort": 0.5,
                "arousal": 0.5,
                "rest_need": 0.5,
            },
            weight=self.config.get("alpha_weight", 1.0)
        )
        
        self.beta = StateDimension(  # Cognitive
            name="beta",
            cn_name="认知维度",
            values={
                "curiosity": 0.5,
                "focus": 0.5,
                "confusion": 0.0,
                "learning": 0.5,
            },
            weight=self.config.get("beta_weight", 1.0)
        )
        
        self.gamma = StateDimension(  # Emotional
            name="gamma",
            cn_name="情感维度",
            values={
                "happiness": 0.5,
                "sadness": 0.0,
                "anger": 0.0,
                "fear": 0.0,
                "disgust": 0.0,
                "surprise": 0.0,
                "trust": 0.5,
                "anticipation": 0.5,
            },
            weight=self.config.get("gamma_weight", 1.0)
        )
        
        self.delta = StateDimension(  # Social
            name="delta",
            cn_name="社交维度",
            values={
                "attention": 0.5,
                "bond": 0.5,
                "trust": 0.5,
                "presence": 0.5,
            },
            weight=self.config.get("delta_weight", 1.0)
        )
        
        # Inter-dimensional influence matrix
        # influence_matrix[from][to] = influence strength
        self.influence_matrix: Dict[str, Dict[str, float]] = {
            "alpha": {
                "beta": 0.3,   # Physiological affects cognitive
                "gamma": 0.5,  # Physiological affects emotional
                "delta": 0.2,  # Physiological affects social
            },
            "beta": {
                "alpha": 0.2,  # Cognitive affects physiological
                "gamma": 0.4,  # Cognitive affects emotional
                "delta": 0.3,  # Cognitive affects social
            },
            "gamma": {
                "alpha": 0.4,  # Emotional affects physiological
                "beta": 0.3,   # Emotional affects cognitive
                "delta": 0.5,  # Emotional affects social
            },
            "delta": {
                "alpha": 0.2,  # Social affects physiological
                "beta": 0.3,   # Social affects cognitive
                "gamma": 0.6,  # Social affects emotional
            },
        }
        
        # Update tracking
        self.last_update: datetime = datetime.now()
        self.update_count: int = 0
    
    def set_alpha_dimension(
        self,
        energy: Optional[float] = None,
        comfort: Optional[float] = None,
        arousal: Optional[float] = None,
        rest_need: Optional[float] = None
    ) -> None:
        """
        设置α维度（生理） / Set alpha dimension (physiological)
        
        Args:
            energy: Energy level (0-1)
            comfort: Comfort level (0-1)
            arousal: Arousal level (0-1)
            rest_need: Rest need level (0-1)
        """
        if energy is not None:
            self.alpha.values["energy"] = max(0.0, min(1.0, energy))
        if comfort is not None:
            self.alpha.values["comfort"] = max(0.0, min(1.0, comfort))
        if arousal is not None:
            self.alpha.values["arousal"] = max(0.0, min(1.0, arousal))
        if rest_need is not None:
            self.alpha.values["rest_need"] = max(0.0, min(1.0, rest_need))
        
        self.alpha.timestamp = datetime.now()
        self._update_count()
    
    def set_beta_dimension(
        self,
        curiosity: Optional[float] = None,
        focus: Optional[float] = None,
        confusion: Optional[float] = None,
        learning: Optional[float] = None
    ) -> None:
        """
        设置β维度（认知） / Set beta dimension (cognitive)
        
        Args:
            curiosity: Curiosity level (0-1)
            focus: Focus level (0-1)
            confusion: Confusion level (0-1)
            learning: Learning state (0-1)
        """
        if curiosity is not None:
            self.beta.values["curiosity"] = max(0.0, min(1.0, curiosity))
        if focus is not None:
            self.beta.values["focus"] = max(0.0, min(1.0, focus))
        if confusion is not None:
            self.beta.values["confusion"] = max(0.0, min(1.0, confusion))
        if learning is not None:
            self.beta.values["learning"] = max(0.0, min(1.0, learning))
        
        self.beta.timestamp = datetime.now()
        self._update_count()
    
    def set_gamma_dimension(
        self,
        happiness: Optional[float] = None,
        sadness: Optional[float] = None,
        anger: Optional[float] = None,
        fear: Optional[float] = None,
        disgust: Optional[float] = None,
        surprise: Optional[float] = None,
        trust: Optional[float] = None,
        anticipation: Optional[float] = None
    ) -> None:
        """
        设置γ维度（情感） / Set gamma dimension (emotional)
        
        Args:
            happiness: Happiness level (0-1)
            sadness: Sadness level (0-1)
            anger: Anger level (0-1)
            fear: Fear level (0-1)
            disgust: Disgust level (0-1)
            surprise: Surprise level (0-1)
            trust: Trust level (0-1)
            anticipation: Anticipation level (0-1)
        """
        if happiness is not None:
            self.gamma.values["happiness"] = max(0.0, min(1.0, happiness))
        if sadness is not None:
            self.gamma.values["sadness"] = max(0.0, min(1.0, sadness))
        if anger is not None:
            self.gamma.values["anger"] = max(0.0, min(1.0, anger))
        if fear is not None:
            self.gamma.values["fear"] = max(0.0, min(1.0, fear))
        if disgust is not None:
            self.gamma.values["disgust"] = max(0.0, min(1.0, disgust))
        if surprise is not None:
            self.gamma.values["surprise"] = max(0.0, min(1.0, surprise))
        if trust is not None:
            self.gamma.values["trust"] = max(0.0, min(1.0, trust))
        if anticipation is not None:
            self.gamma.values["anticipation"] = max(0.0, min(1.0, anticipation))
        
        self.gamma.timestamp = datetime.now()
        self._update_count()
    
    def set_delta_dimension(
        self,
        attention: Optional[float] = None,
        bond: Optional[float] = None,
        trust: Optional[float] = None,
        presence: Optional[float] = None
    ) -> None:
        """
        设置δ维度（社交） / Set delta dimension (social)
        
        Args:
            attention: Attention level (0-1)
            bond: Bond level (0-1)
            trust: Trust level (0-1)
            presence: Presence level (0-1)
        """
        if attention is not None:
            self.delta.values["attention"] = max(0.0, min(1.0, attention))
        if bond is not None:
            self.delta.values["bond"] = max(0.0, min(1.0, bond))
        if trust is not None:
            self.delta.values["trust"] = max(0.0, min(1.0, trust))
        if presence is not None:
            self.delta.values["presence"] = max(0.0, min(1.0, presence))
        
        self.delta.timestamp = datetime.now()
        self._update_count()
    
    def _update_count(self) -> None:
        """Update modification count and timestamp"""
        self.update_count += 1
        self.last_update = datetime.now()
    
    def compute_inter_influences(self) -> Dict[str, Dict[str, float]]:
        """
        计算维度间相互影响 / Compute inter-dimensional influences
        
        Calculates how each dimension affects others based on
        the influence matrix and current values.
        
        Returns:
            Dictionary mapping source -> target -> influence amount
        """
        influences: Dict[str, Dict[str, float]] = {}
        
        dimensions = {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma,
            "delta": self.delta,
        }
        
        for source_name, targets in self.influence_matrix.items():
            influences[source_name] = {}
            source_dim = dimensions[source_name]
            
            # Calculate source dimension intensity
            source_avg = sum(source_dim.values.values()) / len(source_dim.values)
            
            for target_name, base_influence in targets.items():
                target_dim = dimensions[target_name]
                
                # Calculate influence based on:
                # 1. Base influence strength
                # 2. Source dimension intensity
                # 3. Dimension weights
                influence_amount = (
                    base_influence *
                    source_avg *
                    source_dim.weight *
                    target_dim.weight
                )
                
                influences[source_name][target_name] = influence_amount
                
                # Apply influence to target dimension
                self._apply_influence(target_dim, source_name, influence_amount)
        
        return influences
    
    def _apply_influence(
        self,
        target_dim: StateDimension,
        source_name: str,
        amount: float
    ) -> None:
        """应用维度间影响 / Apply influence to target dimension"""
        # Dimension-specific influence rules
        if target_dim.name == "alpha":  # Physiological
            if source_name == "gamma":  # Emotional affects physiological
                # Positive emotions increase energy, reduce rest need
                happiness = self.gamma.values.get("happiness", 0.5)
                target_dim.values["energy"] = min(
                    1.0, target_dim.values["energy"] + amount * happiness * 0.1
                )
                target_dim.values["rest_need"] = max(
                    0.0, target_dim.values["rest_need"] - amount * happiness * 0.1
                )
        
        elif target_dim.name == "beta":  # Cognitive
            if source_name == "alpha":  # Physiological affects cognitive
                # High energy increases focus
                energy = self.alpha.values.get("energy", 0.5)
                target_dim.values["focus"] = min(
                    1.0, target_dim.values["focus"] + amount * energy * 0.1
                )
            if source_name == "gamma":  # Emotional affects cognitive
                # High arousal emotions reduce focus
                arousal_emotions = (
                    self.gamma.values.get("anger", 0) +
                    self.gamma.values.get("fear", 0) +
                    self.gamma.values.get("surprise", 0)
                ) / 3
                target_dim.values["focus"] = max(
                    0.0, target_dim.values["focus"] - amount * arousal_emotions * 0.15
                )
        
        elif target_dim.name == "gamma":  # Emotional
            if source_name == "alpha":  # Physiological affects emotional
                # High arousal increases emotional intensity
                arousal = self.alpha.values.get("arousal", 0.5)
                for emotion in ["happiness", "sadness", "anger", "fear"]:
                    target_dim.values[emotion] = min(
                        1.0, target_dim.values[emotion] + amount * arousal * 0.05
                    )
            if source_name == "delta":  # Social affects emotional
                # Bond increases happiness
                bond = self.delta.values.get("bond", 0.5)
                target_dim.values["happiness"] = min(
                    1.0, target_dim.values["happiness"] + amount * bond * 0.1
                )
        
        elif target_dim.name == "delta":  # Social
            if source_name == "gamma":  # Emotional affects social
                # Happiness increases bond
                happiness = self.gamma.values.get("happiness", 0.5)
                target_dim.values["bond"] = min(
                    1.0, target_dim.values["bond"] + amount * happiness * 0.1
                )
                target_dim.values["presence"] = min(
                    1.0, target_dim.values["presence"] + amount * happiness * 0.08
                )
    
    def get_dimension_state(self, dimension: str) -> Dict[str, float]:
        """
        获取维度状态 / Get dimension state
        
        Args:
            dimension: "alpha", "beta", "gamma", or "delta"
            
        Returns:
            Dictionary of dimension values
        """
        if dimension == "alpha":
            return self.alpha.values.copy()
        elif dimension == "beta":
            return self.beta.values.copy()
        elif dimension == "gamma":
            return self.gamma.values.copy()
        elif dimension == "delta":
            return self.delta.values.copy()
        return {}
    
    def get_dimension_average(self, dimension: str) -> float:
        """获取维度平均值 / Get average value for a dimension"""
        values = self.get_dimension_state(dimension)
        if not values:
            return 0.0
        return sum(values.values()) / len(values)
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        获取状态摘要 / Get comprehensive state summary
        
        Returns:
            Dictionary with all dimension states and computed metrics
        """
        alpha_avg = self.get_dimension_average("alpha")
        beta_avg = self.get_dimension_average("beta")
        gamma_avg = self.get_dimension_average("gamma")
        delta_avg = self.get_dimension_average("delta")
        
        # Calculate overall wellbeing
        wellbeing = (
            alpha_avg * 0.3 +
            beta_avg * 0.2 +
            gamma_avg * 0.3 +
            delta_avg * 0.2
        )
        
        # Calculate arousal/activation level
        arousal = self.alpha.values["arousal"] * 0.4 + self.gamma.values["surprise"] * 0.3
        
        # Calculate valence (positive/negative)
        positive = self.gamma.values["happiness"] + self.gamma.values["trust"]
        negative = self.gamma.values["sadness"] + self.gamma.values["anger"] + self.gamma.values["fear"]
        valence = (positive - negative) / 2  # -1 to 1
        
        return {
            "alpha": self.alpha.values.copy(),
            "beta": self.beta.values.copy(),
            "gamma": self.gamma.values.copy(),
            "delta": self.delta.values.copy(),
            "averages": {
                "alpha": alpha_avg,
                "beta": beta_avg,
                "gamma": gamma_avg,
                "delta": delta_avg,
            },
            "computed": {
                "wellbeing": wellbeing,
                "arousal": arousal,
                "valence": valence,
            },
            "timestamp": self.last_update.isoformat(),
            "update_count": self.update_count,
        }
    
    def set_dimension_weight(self, dimension: str, weight: float) -> None:
        """设置维度权重 / Set dimension weight"""
        if dimension == "alpha":
            self.alpha.weight = weight
        elif dimension == "beta":
            self.beta.weight = weight
        elif dimension == "gamma":
            self.gamma.weight = weight
        elif dimension == "delta":
            self.delta.weight = weight
    
    def get_influence_matrix(self) -> Dict[str, Dict[str, float]]:
        """获取影响矩阵 / Get influence matrix"""
        return {
            source: targets.copy()
            for source, targets in self.influence_matrix.items()
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
        
        # Multidimensional State Matrix Demo
        print("\n" + "=" * 60)
        print("4D状态矩阵演示 / 4D State Matrix Demo")
        print("=" * 60)
        
        matrix = MultidimensionalStateMatrix()
        
        print("\n9. 设置4维度状态 / Setting 4D state:")
        matrix.set_alpha_dimension(energy=0.8, comfort=0.7, arousal=0.6, rest_need=0.2)
        matrix.set_beta_dimension(curiosity=0.9, focus=0.8, confusion=0.1, learning=0.7)
        matrix.set_gamma_dimension(happiness=0.85, sadness=0.1, trust=0.8, anger=0.05)
        matrix.set_delta_dimension(attention=0.9, bond=0.7, trust=0.8, presence=0.6)
        
        print("   α生理维度 / Physiological:", matrix.get_dimension_state("alpha"))
        print("   β认知维度 / Cognitive:", matrix.get_dimension_state("beta"))
        print("   γ情感维度 / Emotional:", matrix.get_dimension_state("gamma"))
        print("   δ社交维度 / Social:", matrix.get_dimension_state("delta"))
        
        print("\n10. 计算维度间影响 / Computing inter-dimensional influences:")
        influences = matrix.compute_inter_influences()
        for source, targets in influences.items():
            print(f"   {source} -> {targets}")
        
        print("\n11. 更新后的维度平均值 / Updated dimension averages:")
        summary = matrix.get_state_summary()
        for dim, avg in summary["averages"].items():
            print(f"   {dim}维度 / dimension: {avg:.2f}")
        
        print("\n12. 计算指标 / Computed metrics:")
        print(f"   幸福感 / Wellbeing: {summary['computed']['wellbeing']:.2f}")
        print(f"   唤醒度 / Arousal: {summary['computed']['arousal']:.2f}")
        print(f"   情感效价 / Valence: {summary['computed']['valence']:.2f}")
    
    asyncio.run(demo())
