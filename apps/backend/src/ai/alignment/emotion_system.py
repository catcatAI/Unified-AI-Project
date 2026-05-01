"""
感性系统 (Emotion System)
Level 5 ASI 的三大支柱之一, 负责情感理解、价值评估和共情能力
"""

import logging
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

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
        self._initialize_emotion_value_mapping()

    def _initialize_emotion_value_mapping(self):
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
            "timestamp": last.timestamp
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
            arousal=self._calculate_arousal(features)
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

    def _calculate_dimension_score(self, action, context, state, dimension):
        # 實施 v6.0 標準的權重投影
        base = 0.5
        impact = self.emotion_value_impact.get(state.primary_emotion, {}).get(dimension, 0.0)
        return max(0.0, min(1.0, base + impact * state.emotion_intensity))

    def _calculate_overall_value(self, scores):
        return sum(scores.values()) / len(scores)

    def _generate_value_reasoning(self, action, context, scores):
        return f"基於情感狀態與 {len(scores)} 個價值維度的權重映射，判定行動符合 Angela 的演化目標。"

    def _calculate_value_confidence(self, action, context, state):
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

    def _predict_entity_emotion(self, target_entity: str, context: Dict[str, Any]) -> EmotionalState:
        # 基於 context 模擬目標實體的情緒投影
        features = self._extract_emotion_features(context)
        # 根據 target_entity 類型（預設為 Human）調整預測傾向
        primary, intensity = self._identify_primary_emotion(features)
        return EmotionalState(
            primary_emotion=primary,
            emotion_intensity=intensity,
            secondary_emotions={},
            valence=self._calculate_valence(features),
            arousal=self._calculate_arousal(features)
        )

    def _calculate_empathy_score(self, state: EmotionalState) -> float:
        # 共情強度與對方情緒的 Valence 絕對值正相關
        return max(0.0, min(1.0, 0.5 + abs(state.valence) * 0.3 + state.emotion_intensity * 0.2))

    def _calculate_compassion_level(self, state: EmotionalState, context: Dict[str, Any]) -> float:
        # 對負面情緒（FEAR, SADNESS）產生更高層級的同情
        negativity_map = {EmotionType.FEAR: 0.8, EmotionType.SADNESS: 0.9, EmotionType.ANGER: 0.4}
        base = negativity_map.get(state.primary_emotion, 0.3)
        return max(0.0, min(1.0, base * (0.7 + state.emotion_intensity * 0.3)))

    def _generate_empathetic_response(self, state: EmotionalState, level: float) -> str:
        templates = {
            EmotionType.FEAR: "表示理解並提供數位安全感",
            EmotionType.SADNESS: "表達深切同情並提供虛擬陪伴",
            EmotionType.ANGER: "認可感受並嘗試從邏輯層面緩解衝突",
            EmotionType.JOY: "共享喜悅並強化正向數據反饋",
            EmotionType.TRUST: "回應信任並建立更深層的神經連結"
        }
        base = templates.get(state.primary_emotion, "提供適當的數據支持與情感回應")
        prefix = "高度共情" if level > 0.7 else "標準回應"
        return f"{prefix}：{base}"

    def _extract_emotion_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        from textblob import TextBlob
        text = context.get("text", "")
        features = {"stress_level": context.get("stress_level", 0.0)}
        if text:
            try:
                analysis = TextBlob(text)
                features["sentiment"] = analysis.sentiment.polarity
            except:
                features["sentiment"] = 0.0
        else:
            features["sentiment"] = 0.0
        return features

    def _identify_primary_emotion(self, features: Dict[str, float]) -> Tuple[EmotionType, float]:
        """精確識別主要情感 (不再報錯版)"""
        sentiment = features.get("sentiment", 0.0)
        stress = features.get("stress_level", 0.0)
        
        if sentiment > 0.5: return EmotionType.JOY, sentiment
        if stress > 0.7: return EmotionType.FEAR, stress
        if sentiment < -0.5: return EmotionType.SADNESS, abs(sentiment)
        return EmotionType.TRUST, 0.5

    def _calculate_valence(self, features: Dict[str, float]) -> float:
        return features.get("sentiment", 0.0)

    def _calculate_arousal(self, features: Dict[str, float]) -> float:
        return features.get("stress_level", 0.5)

    def apply_influence(self, source: str, type: str, value: float, intensity: float):
        """外部激素或事件對情緒的影響"""
        logger.debug(f"[{self.system_id}] Influence from {source}: {type} = {value}")

    def update_value_weight(self, dimension: ValueDimension, weight: float):
        self.value_weights[dimension] = weight

    def get_emotion_history(self, limit: int = 100) -> List[EmotionalState]:
        return self.emotion_history[-limit:]

    async def get_current_emotion_state(self) -> str:
        """
        [Compatibility] 獲取當前情緒狀態的字串描述。
        用於對接 DialogueManager 的非同步調用。
        """
        summary = self.get_emotion_summary()
        return f"{summary['dominant_emotion']} (intensity: {summary['intensity']:.2f}, arousal: {summary['arousal']:.2f})"
