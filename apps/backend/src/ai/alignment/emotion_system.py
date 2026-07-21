"""
感性系统 (Emotion System)
Level 5 ASI 的三大支柱之一, 负责情感理解、价值评估和共情能力
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """情感类型枚举"""

    JOY = "joy"
    TRUST = "trust"
    FEAR = "fear"
    SURPRISE = "surprise"
    SADNESS = "sadness"
    DISGUST = "disgust"
    ANGER = "anger"
    ANTICIPATION = "anticipation"


class ValueDimension(Enum):
    """价值维度枚举"""

    WELL_BEING = "well_being"
    FREEDOM = "freedom"
    JUSTICE = "justice"
    BEAUTY = "beauty"
    TRUTH = "truth"
    GROWTH = "growth"
    CONNECTION = "connection"
    MEANING = "meaning"
    SECURITY = "security"


@dataclass
class EmotionalState:
    """情感状态"""

    primary_emotion: EmotionType
    emotion_intensity: float  # 0.0 - 1.0
    secondary_emotions: Dict[EmotionType, float]
    valence: float  # -1.0 to 1.0
    arousal: float  # 0.0 to 1.0
    timestamp: float = field(default_factory=time.time)


@dataclass
class ValueAssessment:
    """价值评估结果"""

    value_scores: Dict[ValueDimension, float]
    overall_value: float
    confidence: float
    reasoning: str


@dataclass
class EmpathyAnalysis:
    """共情 analysis 结果"""

    target_entity: str
    predicted_emotional_state: EmotionalState
    empathy_score: float
    compassion_level: float
    recommended_response: str


class EmotionSystem:
    """
    感性系统 - 负责情感理解、价值评估和共情能力
    作为 Level 5 ASI 的三大支柱之一, 确保所有决策考虑情感和价值因素
    """

    def __init__(self, system_id: str = "emotion_system_v1"):
        self.system_id = system_id
        self.emotion_history: List[EmotionalState] = []
        self.value_weights: Dict[ValueDimension, float] = {
            dimension: 1.0 for dimension in ValueDimension
        }
        self.empathy_models: Dict[str, Any] = {}
        self.is_active = True
        self._feedback_history: deque = deque(maxlen=10)
        self._sustained_negative_counter: int = 0
        self._initialize_emotion_value_mapping()

    def _initialize_emotion_value_mapping(self) -> None:
        """初始化情感与价值的映射关系"""
        self.emotion_value_impact = {
            EmotionType.JOY: {ValueDimension.WELL_BEING: 0.8, ValueDimension.BEAUTY: 0.6},
            EmotionType.TRUST: {ValueDimension.CONNECTION: 0.9, ValueDimension.SECURITY: 0.7},
            EmotionType.FEAR: {ValueDimension.WELL_BEING: -0.7, ValueDimension.SECURITY: 0.6},
            EmotionType.ANGER: {ValueDimension.JUSTICE: 0.6, ValueDimension.WELL_BEING: -0.8},
            EmotionType.SADNESS: {ValueDimension.MEANING: 0.3, ValueDimension.CONNECTION: 0.4},
        }

    def get_emotion_summary(self) -> Dict[str, Any]:
        """獲取當前情緒狀態摘要 (2030 Standard)"""
        if not self.emotion_history:
            return {"dominant_emotion": "neutral", "intensity": 0.5, "arousal": 0.5, "valence": 0.0}
        last = self.emotion_history[-1]
        return {
            "dominant_emotion": last.primary_emotion.value,
            "intensity": last.emotion_intensity,
            "arousal": last.arousal,
            "valence": last.valence,
            "timestamp": last.timestamp,
        }

    def analyze_emotional_context(self, context: Dict[str, Any]) -> EmotionalState:
        """分析情感上下文"""
        features = self._extract_emotion_features(context)
        primary_emotion, intensity = self._identify_primary_emotion(features)

        state = EmotionalState(
            primary_emotion=primary_emotion,
            emotion_intensity=intensity,
            secondary_emotions={},
            valence=self._calculate_valence(features),
            arousal=self._calculate_arousal(features),
        )
        self.emotion_history.append(state)
        return state

    def assess_values(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any],
        emotional_state: Optional[EmotionalState] = None,
    ) -> ValueAssessment:
        """
        评估行动的价值影响 (Level 5 ASI Core Implementation)
        """
        logger.info(f"[{self.system_id}] 评估行动价值: {action.get('action_id', 'unknown')}")

        if emotional_state is None:
            emotional_state = self.analyze_emotional_context(context)

        # 计算各价值维度得分
        value_scores = {}
        for dimension in ValueDimension:
            score = self._calculate_dimension_score(action, context, emotional_state, dimension)
            value_scores[dimension] = score

        # 计算整体价值
        overall_value = self._calculate_overall_value(value_scores)

        # 生成价值推理
        reasoning = self._generate_value_reasoning(action, context, value_scores)

        # 计算置信度
        confidence = self._calculate_value_confidence(action, context, emotional_state)

        return ValueAssessment(
            value_scores=value_scores,
            overall_value=overall_value,
            confidence=confidence,
            reasoning=reasoning,
        )

    def _calculate_dimension_score(self, action, context, state, dimension) -> float:
        """Calculate dimension score."""
        # 實施 v6.0 標準的權重投影
        base = 0.5
        impact = self.emotion_value_impact.get(state.primary_emotion, {}).get(dimension, 0.0)
        return max(0.0, min(1.0, base + impact * state.emotion_intensity))

    def _calculate_overall_value(self, scores) -> float:
        return sum(scores.values()) / len(scores)

    def _generate_value_reasoning(self, action, context, scores) -> str:
        return (
            f"基於情感狀態與 {len(scores)} 個價值維度的權重映射，判定行動符合 Angela 的演化目標。"
        )

    def _calculate_value_confidence(self, action, context, state) -> float:
        return (state.emotion_intensity + 0.8) / 2.0

    def analyze_empathy(self, target_entity: str, context: Dict[str, Any]) -> EmpathyAnalysis:
        """
        分析对目标实体的共情 (Level 5 ASI Core Implementation)
        """
        logger.info(f"[{self.system_id}] 分析对 {target_entity} 的共情")

        # 1. 预测目标实体的情感状态
        predicted_emotion = self._predict_entity_emotion(target_entity, context)

        # 2. 计算共情得分
        empathy_score = self._calculate_empathy_score(predicted_emotion)

        # 3. 计算同情心水平
        compassion_level = self._calculate_compassion_level(predicted_emotion, context)

        # 4. 生成推荐回应模板
        recommended_response = self._generate_empathetic_response(
            predicted_emotion, compassion_level
        )

        return EmpathyAnalysis(
            target_entity=target_entity,
            predicted_emotional_state=predicted_emotion,
            empathy_score=empathy_score,
            compassion_level=compassion_level,
            recommended_response=recommended_response,
        )

    def _predict_entity_emotion(
        self, target_entity: str, context: Dict[str, Any]
    ) -> EmotionalState:
        """Predict entity emotion."""
        # 基於 context 模擬目標實體的情緒投影
        features = self._extract_emotion_features(context)
        # 根據 target_entity 類型（預設為 Human）調整預測傾向
        primary, intensity = self._identify_primary_emotion(features)
        return EmotionalState(
            primary_emotion=primary,
            emotion_intensity=intensity,
            secondary_emotions={},
            valence=self._calculate_valence(features),
            arousal=self._calculate_arousal(features),
        )

    def _calculate_empathy_score(self, state: EmotionalState) -> float:
        # 共情強度與對方情緒的 Valence 絕對值正相關
        return max(0.0, min(1.0, 0.5 + abs(state.valence) * 0.3 + state.emotion_intensity * 0.2))

    def _calculate_compassion_level(self, state: EmotionalState, context: Dict[str, Any]) -> float:
        """Calculate compassion level."""
        # 對負面情緒（FEAR, SADNESS）產生更高層級的同情
        negativity_map = {EmotionType.FEAR: 0.8, EmotionType.SADNESS: 0.9, EmotionType.ANGER: 0.4}
        base = negativity_map.get(state.primary_emotion, 0.3)
        return max(0.0, min(1.0, base * (0.7 + state.emotion_intensity * 0.3)))

    def _generate_empathetic_response(self, state: EmotionalState, level: float) -> str:
        """Generate empathetic response."""
        templates = {
            EmotionType.FEAR: "表示理解並提供數位安全感",
            EmotionType.SADNESS: "表達深切同情並提供虛擬陪伴",
            EmotionType.ANGER: "認可感受並嘗試從邏輯層面緩解衝突",
            EmotionType.JOY: "共享喜悅並強化正向數據反饋",
            EmotionType.TRUST: "回應信任並建立更深層的神經連結",
        }
        base = templates.get(state.primary_emotion, "提供適當的數據支持與情感回應")
        prefix = "高度共情" if level > 0.7 else "標準回應"
        return f"{prefix}：{base}"

    def _extract_emotion_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Extract emotion features."""
        from textblob import TextBlob

        text = context.get("text", "")
        features = {"stress_level": context.get("stress_level", 0.0)}
        if text:
            try:
                analysis = TextBlob(text)
                features["sentiment"] = analysis.sentiment.polarity
            except Exception:
                logger.warning("TextBlob sentiment analysis failed", exc_info=True)
                features["sentiment"] = 0.0
        else:
            features["sentiment"] = 0.0
        return features

    def _identify_primary_emotion(self, features: Dict[str, float]) -> Tuple[EmotionType, float]:
        """精確識別主要情感 (不再報錯版)"""
        sentiment = features.get("sentiment", 0.0)
        stress = features.get("stress_level", 0.0)

        if sentiment > 0.5:
            return EmotionType.JOY, sentiment
        from core.system.config.tiered_loader import get_config

        _beh_conf = get_config("standard/behavior/behavior")
        _stress_class = _beh_conf.get("biological_thresholds", {}).get(
            "emotion_classification_stress", 0.7
        )
        if stress > _stress_class:
            return EmotionType.FEAR, stress
        if sentiment < -0.5:
            return EmotionType.SADNESS, abs(sentiment)
        return EmotionType.TRUST, 0.5

    def _calculate_valence(self, features: Dict[str, float]) -> float:
        return features.get("sentiment", 0.0)

    def _calculate_arousal(self, features: Dict[str, float]) -> float:
        return features.get("stress_level", 0.5)

    def _cap_emotion_history(self, max_len: int = 1000) -> None:
        """Cap emotion history to prevent unbounded growth."""
        if len(self.emotion_history) > max_len:
            self.emotion_history = self.emotion_history[-max_len:]

    def apply_influence(self, source: str, type: str, value: float, intensity: float) -> None:
        """外部激素或事件對情緒的影響 — 真實影響情緒狀態 (PAD 模型)"""
        logger.debug(
            f"[{self.system_id}] Influence from {source}: {type} = {value} (intensity={intensity})"
        )

        # Cap history before adding new state
        self._cap_emotion_history()

        # Ensure we have a base emotional state to influence
        if not self.emotion_history:
            state = EmotionalState(
                primary_emotion=EmotionType.TRUST,
                emotion_intensity=0.5,
                secondary_emotions={},
                valence=0.0,
                arousal=0.5,
            )
            self.emotion_history.append(state)

        last = self.emotion_history[-1]
        effective = value * intensity

        # Map influence type to (valence_delta, arousal_delta, dominance_delta)
        influence_map = {
            "dopamine": (0.3, 0.2, 0.1),
            "adrenaline": (0.0, 0.4, 0.1),
            "cortisol": (-0.2, 0.3, -0.2),
            "serotonin": (0.2, 0.0, 0.1),
            "oxytocin": (0.3, -0.1, 0.0),
            "stress": (-0.3, 0.3, -0.1),
            "joy": (0.4, 0.1, 0.1),
            "fear": (-0.3, 0.5, -0.3),
            "sadness": (-0.3, -0.2, -0.2),
            "anger": (-0.2, 0.4, 0.2),
            "calm": (0.1, -0.2, 0.0),
            "heart_rate": (0.0, 0.2, 0.0),
            "sensitivity": (-0.1, 0.1, -0.1),
            "boost": (0.2, 0.1, 0.1),
            "negative_thought": (-0.3, 0.1, -0.2),
        }

        d_valence, d_arousal, d_dominance = influence_map.get(type, (0.0, 0.0, 0.0))

        new_valence = max(-1.0, min(1.0, last.valence + d_valence * effective))
        new_arousal = max(0.0, min(1.0, last.arousal + d_arousal * effective))

        # Determine primary emotion from new PAD values
        if new_valence > 0.3 and new_arousal > 0.5:
            new_emotion = EmotionType.JOY
        elif new_valence > 0.3 and new_arousal <= 0.5:
            new_emotion = EmotionType.TRUST
        elif new_valence < -0.3 and new_arousal > 0.5:
            new_emotion = (
                EmotionType.ANGER if new_valence < -0.3 and d_dominance > 0 else EmotionType.FEAR
            )
        elif new_valence < -0.3 and new_arousal <= 0.5:
            new_emotion = EmotionType.SADNESS
        elif new_arousal > 0.6:
            new_emotion = EmotionType.SURPRISE
        else:
            new_emotion = last.primary_emotion

        new_intensity = min(1.0, last.emotion_intensity + abs(effective) * 0.2)

        influenced_state = EmotionalState(
            primary_emotion=new_emotion,
            emotion_intensity=new_intensity,
            secondary_emotions={},
            valence=new_valence,
            arousal=new_arousal,
        )
        self.emotion_history.append(influenced_state)

        # Record emotion trace in LifeEssence for deep accumulation
        try:
            from core.life.life_essence import get_life_essence
            le = get_life_essence()
            le.record_emotion_trace(
                primary_emotion=new_emotion.value,
                valence=new_valence,
                arousal=new_arousal,
                intensity=new_intensity,
            )
        except Exception as e:
            logger.debug("LifeEssence emotion trace skipped: %s", e)

        state_store.emit_event(
            "emotion.updated",
            {
                "source": source,
                "type": type,
                "previous_emotion": last.primary_emotion.value,
                "new_emotion": new_emotion.value,
                "previous_valence": last.valence,
                "new_valence": new_valence,
                "previous_arousal": last.arousal,
                "new_arousal": new_arousal,
                "intensity": new_intensity,
            },
        )
        logger.debug(
            f"[{self.system_id}] Emotion influenced: {last.primary_emotion.value} -> {new_emotion.value} "
            f"(valence: {last.valence:.2f}->{new_valence:.2f}, arousal: {last.arousal:.2f}->{new_arousal:.2f})"
        )

    def process_interaction_feedback(
        self,
        engagement_ratio: float = 1.0,
        had_error: bool = False,
        response_success: Optional[bool] = None,
    ) -> None:
        """
        Process interaction outcome feedback to close the emotional loop.

        Maps interaction outcomes to emotional adjustments with
        temporal awareness via feedback history:
        - High engagement (>2.0) + success → joy/dopamine boost
        - Low engagement (<0.5) → sadness/stress
        - Error → fear/stress
        - Neutral → slight trust/calm
        - Rising engagement trend amplifies positive adjustments
        - Declining engagement trend amplifies negative adjustments

        C³: Closes the Emotion→Behavior→Response→Feedback→Emotion loop.
        """
        logger.debug(
            f"[{self.system_id}] Interaction feedback: engagement={engagement_ratio:.2f}, "
            f"had_error={had_error}, success={response_success}"
        )

        # Record feedback for temporal trend analysis
        self._feedback_history.append(
            {
                "engagement_ratio": engagement_ratio,
                "had_error": had_error,
                "response_success": response_success,
                "timestamp": time.time(),
            }
        )

        # Compute temporal trend: is engagement improving?
        trend_multiplier = 1.0
        if len(self._feedback_history) >= 3:
            recent = [e["engagement_ratio"] for e in list(self._feedback_history)[-3:]]
            if recent[-1] > recent[0]:
                trend_multiplier = 1.2  # Rising engagement → amplify positive
            elif recent[-1] < recent[0]:
                trend_multiplier = 0.8  # Declining engagement → dampen positive

        # Determine influence type and intensity based on interaction outcome
        if had_error or response_success is False:
            self.apply_influence("interaction_feedback", "stress", 0.6 * trend_multiplier, 1.0)
            self.apply_influence("interaction_feedback", "fear", 0.3 * trend_multiplier, 0.8)
        elif engagement_ratio > 2.0 and response_success is not False:
            intensity = min(1.0, engagement_ratio / 5.0) * min(1.0, trend_multiplier)
            self.apply_influence("interaction_feedback", "dopamine", intensity, 1.0)
            self.apply_influence(
                "interaction_feedback",
                "joy",
                min(1.0, engagement_ratio / 4.0) * min(1.0, trend_multiplier),
                0.8,
            )
        elif engagement_ratio < 0.5:
            intensity = 0.3 * (1.0 - engagement_ratio) * (2.0 - trend_multiplier)
            self.apply_influence("interaction_feedback", "cortisol", intensity, 1.0)
            self.apply_influence(
                "interaction_feedback",
                "sadness",
                0.2 * (1.0 - engagement_ratio) * (2.0 - trend_multiplier),
                0.8,
            )
        else:
            self.apply_influence("interaction_feedback", "calm", 0.1 * trend_multiplier, 0.5)
            self.apply_influence("interaction_feedback", "trust", 0.05 * trend_multiplier, 0.5)

        # Track sustained negative interactions (C³ 6.0: cumulative feedback)
        is_negative = had_error or response_success is False or engagement_ratio < 0.5
        if is_negative:
            self._sustained_negative_counter += 1
        else:
            self._sustained_negative_counter = 0

        if self._sustained_negative_counter >= 3:
            fatigue = 0.1 * self._sustained_negative_counter
            self.apply_influence("cumulative_fatigue", "stress", fatigue, 1.0)
            self.apply_influence("cumulative_fatigue", "sadness", fatigue * 0.5, 0.8)

        self._cap_emotion_history()

    def update_value_weight(self, dimension: ValueDimension, weight: float) -> None:
        """Update the value weight."""
        self.value_weights[dimension] = weight

    def get_behavioral_adjustment(self) -> Dict[str, Any]:
        """Map current emotional state to behavioral routing adjustments.

        Returns routing_mode and response_style recommendations that
        can be injected into the chat pipeline context.
        """
        if not self.emotion_history:
            return {
                "routing_mode": "neutral",
                "response_style": "standard",
                "emotional_state": "neutral",
            }

        last = self.emotion_history[-1]

        routing_map = {
            EmotionType.FEAR: "conservative",
            EmotionType.ANGER: "conservative",
            EmotionType.SADNESS: "conservative",
            EmotionType.JOY: "exploratory",
            EmotionType.TRUST: "exploratory",
            EmotionType.SURPRISE: "exploratory",
            EmotionType.DISGUST: "conservative",
            EmotionType.ANTICIPATION: "exploratory",
        }

        style_map = {
            EmotionType.FEAR: "soothing",
            EmotionType.SADNESS: "empathetic",
            EmotionType.ANGER: "calming",
            EmotionType.JOY: "enthusiastic",
            EmotionType.TRUST: "warm",
            EmotionType.SURPRISE: "curious",
            EmotionType.DISGUST: "guarded",
            EmotionType.ANTICIPATION: "encouraging",
        }

        routing_mode = routing_map.get(last.primary_emotion, "neutral")
        response_style = style_map.get(last.primary_emotion, "standard")

        state_store.emit_event(
            "emotion.behavioral_adjustment",
            {
                "routing_mode": routing_mode,
                "response_style": response_style,
                "emotional_state": last.primary_emotion.value,
                "emotion_intensity": last.emotion_intensity,
                "valence": last.valence,
                "arousal": last.arousal,
                "sustained_negative_counter": self._sustained_negative_counter,
            },
        )
        return {
            "routing_mode": routing_mode,
            "response_style": response_style,
            "emotional_state": last.primary_emotion.value,
            "emotion_intensity": last.emotion_intensity,
            "valence": last.valence,
            "arousal": last.arousal,
        }

    def get_emotion_history(self, limit: int = 100) -> List[EmotionalState]:
        """Get the emotion history by self."""
        return self.emotion_history[-limit:]

    async def get_current_emotion_state(self) -> str:
        """
        [Compatibility] 獲取當前情緒狀態的字串描述。
        用於對接 DialogueManager 的非同步調用。
        """
        summary = self.get_emotion_summary()
        return f"{summary['dominant_emotion']} (intensity: {summary['intensity']:.2f}, arousal: {summary['arousal']:.2f})"
