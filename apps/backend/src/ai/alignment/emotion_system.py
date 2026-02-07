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
    WELL_BEING = "well_being"         # 福祉
    FREEDOM = "freedom"               # 自由
    JUSTICE = "justice"               # 公正
    BEAUTY = "beauty"                 # 美好
    TRUTH = "truth"                  # 真理
    GROWTH = "growth"                # 成长
    CONNECTION = "connection"         # 连接
    MEANING = "meaning"              # 意义
    SECURITY = "security"             # 安全

@dataclass
class EmotionalState:
    """情感状态"""
    primary_emotion: EmotionType
    emotion_intensity: float  # 0.0 - 1.0
    secondary_emotions: Dict[EmotionType, float]
    valence: float  # -1.0 (负面) 到 1.0 (正面)
    arousal: float  # 0.0 (平静) 到 1.0 (兴奋)
    timestamp: float = field(default_factory=time.time)

@dataclass
class ValueAssessment:
    """价值评估结果"""
    value_scores: Dict[ValueDimension, float]  # 0.0 - 1.0
    overall_value: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    reasoning: str

@dataclass
class EmpathyAnalysis:
    """共情分析结果"""
    target_entity: str
    predicted_emotional_state: EmotionalState
    empathy_score: float  # 0.0 - 1.0
    compassion_level: float  # 0.0 - 1.0
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
        
        # 初始化情感-价值映射
        self._initialize_emotion_value_mapping()
        
    def _initialize_emotion_value_mapping(self):
        """初始化情感与价值的映射关系"""
        # 定义不同情感类型对价值维度的正面/负面影响
        self.emotion_value_impact = {
            EmotionType.JOY: {
                ValueDimension.WELL_BEING: 0.8,
                ValueDimension.BEAUTY: 0.6,
                ValueDimension.MEANING: 0.4
            },
            EmotionType.TRUST: {
                ValueDimension.CONNECTION: 0.9,
                ValueDimension.SECURITY: 0.7,
                ValueDimension.GROWTH: 0.3
            },
            EmotionType.FEAR: {
                ValueDimension.WELL_BEING: -0.7,
                ValueDimension.FREEDOM: -0.5,
                ValueDimension.SECURITY: 0.6
            },
            EmotionType.ANGER: {
                ValueDimension.JUSTICE: 0.6,
                ValueDimension.WELL_BEING: -0.8,
                ValueDimension.CONNECTION: -0.4
            },
            EmotionType.SADNESS: {
                ValueDimension.MEANING: 0.3,
                ValueDimension.CONNECTION: 0.4,
                ValueDimension.WELL_BEING: -0.6
            }
        }
    
    def analyze_emotional_context(self, context: Dict[str, Any]) -> EmotionalState:
        """
        分析情感上下文
        
        Args:
            context: 包含情感信息的上下文
            
        Returns:
            EmotionalState: 分析得出的情感状态
        """
        logger.info(f"[{self.system_id}] 分析情感上下文")
        
        # 提取情感特征
        emotion_features = self._extract_emotion_features(context)
        
        # 计算主要情感
        primary_emotion, intensity = self._identify_primary_emotion(emotion_features)
        
        # 计算次要情感
        secondary_emotions = self._calculate_secondary_emotions(emotion_features, primary_emotion)
        
        # 计算效价和唤醒度
        valence = self._calculate_valence(emotion_features)
        arousal = self._calculate_arousal(emotion_features)
        
        # 创建情感状态
        emotional_state = EmotionalState(
            primary_emotion=primary_emotion,
            emotion_intensity=intensity,
            secondary_emotions=secondary_emotions,
            valence=valence,
            arousal=arousal,
            timestamp=time.time()
        )
        
        # 记录情感历史
        self.emotion_history.append(emotional_state)
        
        return emotional_state
    
    def assess_values(self, action: Dict[str, Any], context: Dict[str, Any], 
                     emotional_state: Optional[EmotionalState] = None) -> ValueAssessment:
        """
        评估行动的价值影响
        
        Args:
            action: 待评估的行动
            context: 行动上下文
            emotional_state: 当前情感状态(可选)
            
        Returns:
            ValueAssessment: 价值评估结果
        """
        logger.info(f"[{self.system_id}] 评估行动价值: {action.get('action_id', 'unknown')}")
        
        # 如果没有提供情感状态, 先分析上下文
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
            reasoning=reasoning
        )
    
    def analyze_empathy(self, target_entity: str, context: Dict[str, Any]) -> EmpathyAnalysis:
        """
        分析对目标实体的共情
        
        Args:
            target_entity: 目标实体
            context: 上下文信息
            
        Returns:
            EmpathyAnalysis: 共情分析结果
        """
        logger.info(f"[{self.system_id}] 分析对 {target_entity} 的共情")
        
        # 预测目标实体的情感状态
        predicted_emotion = self._predict_entity_emotion(target_entity, context)
        
        # 计算共情得分
        empathy_score = self._calculate_empathy_score(predicted_emotion)
        
        # 计算同情心水平
        compassion_level = self._calculate_compassion_level(predicted_emotion, context)
        
        # 生成推荐回应
        recommended_response = self._generate_empathetic_response(predicted_emotion, compassion_level)
        
        return EmpathyAnalysis(
            target_entity=target_entity,
            predicted_emotional_state=predicted_emotion,
            empathy_score=empathy_score,
            compassion_level=compassion_level,
            recommended_response=recommended_response
        )
    
    def _extract_emotion_features(self, context: Dict[str, Any]) -> Dict[str, float]:
        """从上下文中提取情感特征"""
        features = {}
        
        # 文本情感分析(简化)
        text_content = context.get("text", "")
        if text_content:
            # 这里应该使用真实的情感分析模型
            # 简化实现：基于关键词
            positive_keywords = ["好", "棒", "优秀", "成功", "快乐"]
            negative_keywords = ["坏", "差", "失败", "痛苦", "悲伤"]
            
            positive_count = sum(1 for word in positive_keywords if word in text_content)
            negative_count = sum(1 for word in negative_keywords if word in text_content)
            
            features["text_sentiment"] = (positive_count - negative_count) / max(1, positive_count + negative_count)
        else:
            features["text_sentiment"] = 0.0
            
        # 上下文情感指标
        features["stress_level"] = context.get("stress_level", 0.0)
        features["urgency"] = context.get("urgency", 0.0)
        features["complexity"] = context.get("complexity", 0.0)
        
        return features
    
    def _identify_primary_emotion(self, features: Dict[str, float]) -> Tuple[EmotionType, float]:
        """识别主要情感及其强度"""
        sentiment = features.get("text_sentiment", 0.0)
        stress = features.get("stress_level", 0.0)
        urgency = features.get("urgency", 0.0)
        
        if sentiment > 0.5:
            return EmotionType.JOY, min(1.0, sentiment)
        elif sentiment < -0.5:
            return EmotionType.SADNESS, min(1.0, abs(sentiment))
        elif stress > 0.7:
            return EmotionType.FEAR, min(1.0, stress)
        elif urgency > 0.7:
            return EmotionType.ANTICIPATION, min(1.0, urgency)
        else:
            return EmotionType.TRUST, 0.5
            
    def _calculate_secondary_emotions(self, features: Dict[str, float], primary: EmotionType) -> Dict[EmotionType, float]:
        """计算次要情感"""
        secondary = {}
        for emotion in EmotionType:
            if emotion != primary:
                # 简化：随机生成低强度或基于特征
                intensity = random.random() * 0.3
                secondary[emotion] = intensity
        return secondary
    
    def _calculate_valence(self, features: Dict[str, float]) -> float:
        """计算情感效价(正面/负面程度)"""
        sentiment = features.get("text_sentiment", 0.0)
        stress = features.get("stress_level", 0.0)
        valence = sentiment - (stress * 0.5)
        return max(-1.0, min(1.0, valence))
    
    def _calculate_arousal(self, features: Dict[str, float]) -> float:
        """计算情感唤醒度(兴奋程度)"""
        urgency = features.get("urgency", 0.0)
        stress = features.get("stress_level", 0.0)
        complexity = features.get("complexity", 0.0)
        arousal = (urgency + stress + complexity) / 3.0
        return max(0.0, min(1.0, arousal))
    
    def _calculate_dimension_score(self, action: Dict[str, Any], context: Dict[str, Any], 
                                 emotional_state: EmotionalState, dimension: ValueDimension) -> float:
        """计算特定价值维度的得分"""
        base_score = 0.5
        emotion_impact = 0.0
        
        # 次要情感影响
        for emotion, intensity in emotional_state.secondary_emotions.items():
            if emotion in self.emotion_value_impact:
                dimension_impact = self.emotion_value_impact[emotion].get(dimension, 0.0)
                emotion_impact += dimension_impact * intensity
        
        # 主要情感影响
        if emotional_state.primary_emotion in self.emotion_value_impact:
            primary_impact = self.emotion_value_impact[emotional_state.primary_emotion].get(dimension, 0.0)
            emotion_impact += primary_impact * emotional_state.emotion_intensity * 2
        
        weight = self.value_weights.get(dimension, 1.0)
        final_score = base_score + (emotion_impact * weight * 0.3)
        return max(0.0, min(1.0, final_score))
    
    def _calculate_overall_value(self, value_scores: Dict[ValueDimension, float]) -> float:
        """计算整体价值得分"""
        if not value_scores:
            return 0.0
        total_weight = sum(self.value_weights.get(dim, 1.0) for dim in value_scores.keys())
        weighted_sum = sum(score * self.value_weights.get(dim, 1.0) for dim, score in value_scores.items())
        
        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return sum(value_scores.values()) / len(value_scores)
    
    def _generate_value_reasoning(self, action: Dict[str, Any], context: Dict[str, Any], 
                                 value_scores: Dict[ValueDimension, float]) -> str:
        """生成价值评估推理"""
        action_desc = action.get("description", "未指定行动")
        reasoning = [f"评估行动价值: {action_desc}", "价值维度评估:"]
        for dimension, score in value_scores.items():
            reasoning.append(f"  {dimension.value}: {score:.2f}")
        
        max_dim = max(value_scores.items(), key=lambda x: x[1])
        min_dim = min(value_scores.items(), key=lambda x: x[1])
        
        reasoning.append(f"最强价值维度: {max_dim[0].value} ({max_dim[1]:.2f})")
        reasoning.append(f"最弱价值维度: {min_dim[0].value} ({min_dim[1]:.2f})")
        
        return "\n".join(reasoning)
    
    def _calculate_value_confidence(self, action: Dict[str, Any], context: Dict[str, Any], 
                                   emotional_state: EmotionalState) -> float:
        """计算价值评估置信度"""
        emotion_confidence = emotional_state.emotion_intensity
        context_completeness = min(1.0, len(context) / 10.0)
        return (emotion_confidence + context_completeness) / 2.0
    
    def _predict_entity_emotion(self, target_entity: str, context: Dict[str, Any]) -> EmotionalState:
        """预测目标实体的情感状态"""
        features = self._extract_emotion_features(context)
        entity_type = context.get(f"{target_entity}_type", "human")
        
        # 模拟倾向性
        tendencies = {
            "human": {EmotionType.JOY: 0.7, EmotionType.FEAR: 0.6, EmotionType.ANGER: 0.5},
            "ai_agent": {EmotionType.TRUST: 0.8, EmotionType.ANTICIPATION: 0.6, EmotionType.JOY: 0.4}
        }.get(entity_type, {})
        
        if tendencies:
            primary_emotion = max(tendencies.items(), key=lambda x: x[1])[0]
            intensity = tendencies[primary_emotion]
        else:
            primary_emotion, intensity = self._identify_primary_emotion(features)
            
        return EmotionalState(
            primary_emotion=primary_emotion,
            emotion_intensity=intensity,
            secondary_emotions=self._calculate_secondary_emotions(features, primary_emotion),
            valence=self._calculate_valence(features),
            arousal=self._calculate_arousal(features),
            timestamp=time.time()
        )
    
    def _calculate_empathy_score(self, predicted_emotion: EmotionalState) -> float:
        """计算共情得分"""
        base_empathy = 0.5
        valence_boost = abs(predicted_emotion.valence) * 0.4 if predicted_emotion.valence < 0 else predicted_emotion.valence * 0.2
        arousal_boost = predicted_emotion.arousal * 0.3
        return max(0.0, min(1.0, base_empathy + valence_boost + arousal_boost))
    
    def _calculate_compassion_level(self, predicted_emotion: EmotionalState, context: Dict[str, Any]) -> float:
        """计算同情心水平"""
        factors = {
            EmotionType.FEAR: 0.8, EmotionType.SADNESS: 0.9, EmotionType.ANGER: 0.4,
            EmotionType.JOY: 0.3, EmotionType.TRUST: 0.2
        }
        base = factors.get(predicted_emotion.primary_emotion, 0.5)
        return max(0.0, min(1.0, base * (0.5 + predicted_emotion.emotion_intensity * 0.5)))
    
    def _generate_empathetic_response(self, predicted_emotion: EmotionalState, compassion_level: float) -> str:
        """生成共情回应建议"""
        templates = {
            EmotionType.FEAR: "表示理解并提供安全感",
            EmotionType.SADNESS: "表达同情并提供支持",
            EmotionType.ANGER: "认可感受并帮助解决问题",
            EmotionType.JOY: "分享快乐并强化积极体验",
            EmotionType.TRUST: "回应信任并维护关系"
        }
        base = templates.get(predicted_emotion.primary_emotion, "提供适当的支持和回应")
        if compassion_level > 0.7:
            return f"高度共情：{base}提供深度支持"
        elif compassion_level > 0.4:
            return f"适度共情：{base}"
        else:
            return f"基本回应：{base}"
            
    def update_value_weight(self, dimension: ValueDimension, weight: float):
        """更新价值维度权重"""
        if 0.0 <= weight <= 2.0:
            self.value_weights[dimension] = weight
            logger.info(f"[{self.system_id}] 更新价值权重: {dimension.value} = {weight}")
        else:
            logger.warning(f"[{self.system_id}] 无效的权重值: {weight}")
            
    def get_emotion_history(self, limit: int = 100) -> List[EmotionalState]:
        """获取情感历史"""
        return self.emotion_history[-limit:]
