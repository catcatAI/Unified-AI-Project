# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L3]
# =============================================================================
#
# 职责: 多维度信任评分和管理
# 维度: 涉及认知维度 (β) 的信任评估，包括可靠性、专家性、意图一致性和合规性
# 安全: 使用 Key A (后端控制) 进行安全信任评估和风险控制
# 成熟度: L3 等级可以理解多复杂信任计算
#
# 核心功能:
# - trust_scoring: 多维度信任计算
# - relationship_tracking: 关系历史记录
# - risk_assessment: 风险评估和预测
# - compliance_validation: 合规性检查
#
# =============================================================================

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.system.state_store.global_store import state_store

logger = logging.getLogger(__name__)


class TrustDimension(Enum):
    """信任评分的多维度"""
    RELIABILITY = "reliability"      # 一致性，是否守信
    EXPERTISE = "expertise"          # 专业知识，能力水平
    INTENT_ALIGNMENT = "intent"     # 意图一致性，共情性
    COMPLIANCE = "compliance"        # 合规性，道德标准
    TRANSPARENCY = "transparency"    # 透明度，信息开放
    RESPONSIVENESS = "responsiveness" # 响应性，反馈及时性
    CONSISTENCY = "consistency"     # 一致性，行为稳定


class TrustLevel(Enum):
    """信任等级"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class RiskCategory(Enum):
    """风险类别"""
    BEHAVIORAL = "behavioral"      # 行为风险
    DATA = "data"                   # 数据风险
    MODEL = "model"                 # 模型风险
    ENVIRONMENTAL = "environmental" # 环境风险


@dataclass
class TrustScore:
    """信任评分结果"""
    dimension: TrustDimension
    score: float  # 0.0 - 1.0
    confidence: float  # 置信度 0.0 - 1.0
    evidence_count: int = 0
    last_updated: float = field(default_factory=time.time)
    source: str = "default"
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrustRelationship:
    """信任关系"""
    target_entity: str
    entity_type: str
    trust_score: Dict[TrustDimension, TrustScore]
    interaction_history: deque = field(default_factory=lambda: deque(maxlen=100))
    last_interaction: float = 0.0
    relationship_type: str = "peer"  # peer, subordinate, superior, external
    category: RiskCategory = RiskCategory.BEHAVIORAL


@dataclass
class RiskAssessment:
    """风险评估结果"""
    category: RiskCategory
    risk_level: float  # 0.0 - 1.0
    impact_score: float  # 影响程度
    probability: float  # 发生概率
    mitigation_strategies: List[str] = field(default_factory=list)
    last_assessment: float = field(default_factory=time.time)
    confidence: float = 1.0


class TrustManager:
    """
    多维度信任评分和管理系统

    职责: 计算和维护实体之间的多维度信任关系
    维度: 涉及认知维度 (β) 的信任评估
    安全: 使用 Key A (后端控制) 进行安全信任评估和风险控制
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()

        # 信任评分的历史记录
        self.trust_history: Dict[str, Dict[TrustDimension, List[TrustScore]]]
        self.relationship_cache: Dict[str, TrustRelationship]
        self.risk_assessment_cache: Dict[str, Dict[RiskCategory, RiskAssessment]]

        # 动态权重和参数
        self.dimension_weights: Dict[TrustDimension, float]
        self.risk_thresholds: Dict[RiskCategory, float]
        self.trust_decay_rate: float
        self.confidence_decay_rate: float

        # 性能优化
        self._trust_computation_cache: Dict[str, Any]
        self._relationship_computation_cache: Dict[str, Any]
        self._risk_computation_cache: Dict[str, Any]
        self._last_cache_cleared: float

        # 初始化
        self._initialize_system()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 维度权重配置
            "dimension_weights": {
                TrustDimension.RELIABILITY.value: 0.25,
                TrustDimension.EXPERTISE.value: 0.20,
                TrustDimension.INTENT_ALIGNMENT.value: 0.20,
                TrustDimension.COMPLIANCE.value: 0.15,
                TrustDimension.TRANSPARENCY.value: 0.10,
                TrustDimension.RESPONSIVENESS.value: 0.05,
                TrustDimension.CONSISTENCY.value: 0.05,
            },
            # 风险阈值配置
            "risk_thresholds": {
                RiskCategory.BEHAVIORAL.value: 0.7,
                RiskCategory.DATA.value: 0.6,
                RiskCategory.MODEL.value: 0.8,
                RiskCategory.ENVIRONMENTAL.value: 0.5,
            },
            # 衰减率配置
            "trust_decay_minutes": 60.0,  # 信任衰减时间
            "confidence_decay_minutes": 10.0,  # 置信度衰减时间
            # 缓存配置
            "cache_size_limit": 10000,
            "cache_cleanup_interval_minutes": 60.0,
        }

    def _initialize_system(self) -> None:
        """初始化系统"""
        self.trust_history = defaultdict(lambda: defaultdict(list))
        self.relationship_cache = {}
        self.risk_assessment_cache = defaultdict(dict)

        # 初始化维度权重
        self.dimension_weights = {
            dim: self.config["dimension_weights"][dim.value]
            for dim in TrustDimension
        }

        # 初始化风险阈值
        self.risk_thresholds = {
            category: self.config["risk_thresholds"][category.value]
            for category in RiskCategory
        }

        # 初始化衰减率
        self.trust_decay_rate = 1.0 / (self.config["trust_decay_minutes"] * 60.0)  # 每秒衰减率
        self.confidence_decay_rate = 1.0 / (self.config["confidence_decay_minutes"] * 60.0)

        # 初始化缓存
        self._trust_computation_cache = {}
        self._relationship_computation_cache = {}
        self._risk_computation_cache = {}
        self._last_cache_cleared = time.time()

        logger.info("TrustManager initialized successfully")

    def update_trust_score(
        self,
        entity_id: str,
        dimension: TrustDimension,
        score: float,
        context: Optional[Dict[str, Any]] = None,
        source: str = "system",
    ) -> TrustScore:
        """
        更新实体指定维度的信任评分

        Args:
            entity_id: 实体ID
            dimension: 信任维度
            score: 信任评分 0.0-1.0
            context: 评分上下文信息
            source: 评分来源

        Returns:
            TrustScore: 更新后的信任评分
        """
        try:
            # 验证输入
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"Trust score must be between 0.0 and 1.0, got {score}")

            # 创建或更新信任评分
            trust_score = TrustScore(
                dimension=dimension,
                score=score,
                confidence=self._calculate_confidence(entity_id, dimension, score),
                evidence_count=self._get_current_evidence_count(entity_id, dimension),
                last_updated=time.time(),
                source=source,
                context=context or {},
            )

            # 更新历史记录
            self.trust_history[entity_id][dimension].append(trust_score)

            # 更新关系缓存
            self._update_relationship_cache(entity_id, dimension, trust_score)

            # 触发事件
            state_store.emit_event(
                "trust.updated",
                {
                    "entity_id": entity_id,
                    "dimension": dimension.value,
                    "score": score,
                    "confidence": trust_score.confidence,
                    "source": source,
                    "timestamp": trust_score.last_updated,
                },
            )

            logger.debug(
                f"Trust score updated - entity: {entity_id}, dimension: {dimension.value}, score: {score:.3f}"
            )

            return trust_score

        except Exception as e:
            logger.error(f"Error updating trust score: {e}", exc_info=True)
            raise

    def get_overall_trust_score(
        self,
        entity_id: str,
        include_history: bool = False,
        min_confidence: float = 0.0,
    ) -> Dict[str, Any]:
        """
        获取实体的总体信任评分

        Args:
            entity_id: 实体ID
            include_history: 是否包含历史数据
            min_confidence: 最小置信度阈值

        Returns:
            Dict: 总体信任评分结果
        """
        try:
            # 获取有效的信任评分
            valid_scores = []
            for dimension, scores in self.trust_history[entity_id].items():
                latest_score = scores[-1]
                if latest_score.confidence >= min_confidence:
                    valid_scores.append((dimension, latest_score))

            if not valid_scores:
                return self._create_default_trust_result(entity_id)

            # 计算加权平均
            weighted_scores = []
            for dimension, score_obj in valid_scores:
                weight = self.dimension_weights.get(dimension, 0.1)
                weighted_scores.append(score_obj.score * weight)

            overall_score = sum(weighted_scores) / sum(self.dimension_weights.values()) if weighted_scores else 0.0

            # 确定信任等级
            trust_level = self._classify_trust_level(overall_score)

            # 获取详细评分信息
            detailed_scores = {
                dim.value: {
                    "score": score.score,
                    "confidence": score.confidence,
                    "evidence_count": score.evidence_count,
                    "last_updated": score.last_updated,
                    "source": score.source,
                }
                for dim, score in valid_scores
            }

            # 获取风险评估
            risk_assessment = self._get_overall_risk_assessment(entity_id)

            result = {
                "entity_id": entity_id,
                "overall_score": overall_score,
                "trust_level": trust_level.value,
                "confidence": self._calculate_overall_confidence(entity_id),
                "risk_level": risk_assessment["overall_risk_level"],
                "risk_category": risk_assessment["risk_category"],
                "detailed_scores": detailed_scores,
                "last_updated": time.time(),
                "interaction_count": len(self.trust_history[entity_id].get(TrustDimension.RELIABILITY, [])),
            }

            if include_history:
                result["history"] = self._get_trust_history_summary(entity_id)

            return result

        except Exception as e:
            logger.error(f"Error getting overall trust score: {e}", exc_info=True)
            return self._create_default_trust_result(entity_id)

    def assess_interaction_risk(
        self,
        entity_id: str,
        interaction_context: Dict[str, Any],
        force_reassessment: bool = False,
    ) -> Dict[str, Any]:
        """
        评估实体指定交互的風險

        Args:
            entity_id: 实体ID
            interaction_context: 交互上下文
            force_reassessment: 是否强制重新评估

        Returns:
            Dict: 风险评估结果
        """
        try:
            # 检查缓存
            cache_key = f"{entity_id}_{hash(str(sorted(interaction_context.items())))}"
            if not force_reassessment and cache_key in self._risk_computation_cache:
                cached_result = self._risk_computation_cache[cache_key]
                if time.time() - cached_result["timestamp"] < 300.0:  # 5分钟缓存
                    return cached_result

            # 获取当前状态信息
            trust_info = self.get_overall_trust_score(entity_id, min_confidence=0.0)
            history_data = interaction_context.get("history", [])
            characteristics = interaction_context.get("characteristics", {})

            # 根据分类器特征计算风险
            risk_assessments = {}
            overall_risk = 0.0
            highest_risk_category = None

            for category in RiskCategory:
                risk_score = self._calculate_category_risk(
                    entity_id, category, trust_info, history_data, characteristics
                )
                risk_assessments[category.value] = {
                    "risk_level": risk_score,
                    "category": category.value,
                    "threshold": self.risk_thresholds[category.value],
                    "is_risk": risk_score > self.risk_thresholds[category.value],
                }
                overall_risk = max(overall_risk, risk_score)
                if risk_score > self.risk_thresholds[category.value] and not highest_risk_category:
                    highest_risk_category = category.value

            # 生成风险建议
            recommendations = self._generate_risk_recommendations(
                entity_id, risk_assessments, overall_risk, characteristics
            )

            result = {
                "entity_id": entity_id,
                "overall_risk_level": overall_risk,
                "risk_category": highest_risk_category,
                "category_assessments": risk_assessments,
                "recommendations": recommendations,
                "context": interaction_context,
                "timestamp": time.time(),
            }

            # 缓存结果
            self._risk_computation_cache[cache_key] = result
            self._cleanup_cache_if_needed()

            # 触发事件
            if overall_risk > 0.7:
                state_store.emit_event(
                    "trust.risk_high",
                    {
                        "entity_id": entity_id,
                        "risk_level": overall_risk,
                        "risk_category": highest_risk_category,
                        "recommendations": recommendations,
                        "timestamp": time.time(),
                    },
                )

            logger.debug(
                f"Risk assessment completed - entity: {entity_id}, overall_risk: {overall_risk:.3f}, category: {highest_risk_category}"
            )

            return result

        except Exception as e:
            logger.error(f"Error assessing interaction risk: {e}", exc_info=True)
            return {
                "entity_id": entity_id,
                "overall_risk_level": 0.0,
                "risk_category": "none",
                "category_assessments": {},
                "recommendations": ["Error in risk assessment"],
                "timestamp": time.time(),
                "error": str(e),
            }

    def update_interaction_history(
        self,
        entity_id: str,
        interaction_type: str,
        interaction_data: Dict[str, Any],
    ) -> None:
        """
        更新交互历史记录

        Args:
            entity_id: 实体ID
            interaction_type: 交互类型
            interaction_data: 交互数据
        """
        try:
            # 创建交互记录
            interaction_record = {
                "timestamp": time.time(),
                "type": interaction_type,
                "data": interaction_data,
                "trust_impact": interaction_data.get("trust_impact", {}),
                "risk_impact": interaction_data.get("risk_impact", {}),
            }

            # 获取或创建关系对象
            if entity_id not in self.relationship_cache:
                self.relationship_cache[entity_id] = TrustRelationship(
                    target_entity=entity_id,
                    entity_type="unknown",
                    trust_score={dim: TrustScore(dim, 0.5, 0.5) for dim in TrustDimension},
                )

            # 添加到交互历史
            self.relationship_cache[entity_id].interaction_history.append(interaction_record)
            self.relationship_cache[entity_id].last_interaction = time.time()

            logger.debug(
                f"Interaction history updated - entity: {entity_id}, type: {interaction_type}"
            )

        except Exception as e:
            logger.error(f"Error updating interaction history: {e}", exc_info=True)

    def get_trust_relationship(
        self,
        source_entity: str,
        target_entity: str,
    ) -> Dict[str, Any]:
        """
        获取两个实体之间的信任关系

        Args:
            source_entity: 来源实体ID
            target_entity: 目标实体ID

        Returns:
            Dict: 信任关系信息
        """
        try:
            # 获取双方的信任评分
            source_trust = self.get_overall_trust_score(source_entity)
            target_trust = self.get_overall_trust_score(target_entity)

            # 确定关系类型（简化算法）
            relationship_type = self._determine_relationship_type(source_trust, target_trust)

            return {
                "source_entity": source_entity,
                "target_entity": target_entity,
                "source_trust": source_trust,
                "target_trust": target_trust,
                "relationship_type": relationship_type,
                "mutual_trust": (source_trust["overall_score"] + target_trust["overall_score"]) / 2,
                "last_updated": max(
                    source_trust["last_updated"], target_trust["last_updated"]
                ),
            }

        except Exception as e:
            logger.error(f"Error getting trust relationship: {e}", exc_info=True)
            return {
                "source_entity": source_entity,
                "target_entity": target_entity,
                "error": str(e),
            }

    def get_trust_analytics(
        self,
        entity_id: str,
        time_window_minutes: int = 60,
    ) -> Dict[str, Any]:
        """
        获取信任分析数据

        Args:
            entity_id: 实体ID
            time_window_minutes: 时间窗口（分钟）

        Returns:
            Dict: 信任分析结果
        """
        try:
            # 收集时间窗口内的信任评分
            end_time = time.time()
            start_time = end_time - (time_window_minutes * 60.0)

            dimension_trends = {}
            for dimension in TrustDimension:
                scores_in_window = []
                for score_obj in self.trust_history[entity_id][dimension]:
                    if score_obj.last_updated >= start_time:
                        scores_in_window.append(score_obj.score)

                if scores_in_window:
                    dimension_trends[dimension.value] = {
                        "current": scores_in_window[-1],
                        "average": sum(scores_in_window) / len(scores_in_window),
                        "min": min(scores_in_window),
                        "max": max(scores_in_window),
                        "trend": self._calculate_trend(scores_in_window),
                    }

            # 计算总体趋势
            overall_trend = self._calculate_overall_trend(entity_id, start_time, end_time)

            return {
                "entity_id": entity_id,
                "time_window_minutes": time_window_minutes,
                "dimension_trends": dimension_trends,
                "overall_trend": overall_trend,
                "last_updated": time.time(),
            }

        except Exception as e:
            logger.error(f"Error getting trust analytics: {e}", exc_info=True)
            return {
                "entity_id": entity_id,
                "error": str(e),
            }

    # -------------------------------------------------------------------------
    # 内部帮助方法
    # -------------------------------------------------------------------------

    def _calculate_confidence(
        self,
        entity_id: str,
        dimension: TrustDimension,
        new_score: float,
    ) -> float:
        """计算置信度"""
        try:
            # 获取历史评分
            history = self.trust_history[entity_id][dimension]
            if len(history) < 2:
                return 0.8  # 初始评分置信度较高

            # 计算方差（评分一致性）
            scores = [s.score for s in history]
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5

            # 根据一致性和数据量计算置信度
            consistency_factor = max(0.0, 1.0 - std_dev)
            data_factor = min(1.0, len(scores) / 10.0)
            confidence = (consistency_factor * 0.7 + data_factor * 0.3)

            return max(0.1, min(1.0, confidence))

        except Exception:
            return 0.5

    def _get_current_evidence_count(
        self,
        entity_id: str,
        dimension: TrustDimension,
    ) -> int:
        """获取当前证据数量"""
        return len(self.trust_history[entity_id][dimension])

    def _update_relationship_cache(
        self,
        entity_id: str,
        dimension: TrustDimension,
        trust_score: TrustScore,
    ) -> None:
        """更新关系缓存"""
        if entity_id not in self.relationship_cache:
            self.relationship_cache[entity_id] = TrustRelationship(
                target_entity=entity_id,
                entity_type="unknown",
                trust_score={dim: TrustScore(dim, 0.5, 0.5) for dim in TrustDimension},
            )

        # 更新指定维度的信任评分
        self.relationship_cache[entity_id].trust_score[dimension] = trust_score

    def _classify_trust_level(self, score: float) -> TrustLevel:
        """根据评分分类信任等级"""
        if score >= 0.8:
            return TrustLevel.VERY_HIGH
        elif score >= 0.6:
            return TrustLevel.HIGH
        elif score >= 0.4:
            return TrustLevel.MEDIUM
        elif score >= 0.2:
            return TrustLevel.LOW
        else:
            return TrustLevel.VERY_LOW

    def _create_default_trust_result(self, entity_id: str) -> Dict[str, Any]:
        """创建默认的信任结果"""
        return {
            "entity_id": entity_id,
            "overall_score": 0.0,
            "trust_level": TrustLevel.VERY_LOW.value,
            "confidence": 0.0,
            "risk_level": 1.0,
            "risk_category": "unknown",
            "detailed_scores": {},
            "last_updated": time.time(),
            "interaction_count": 0,
        }

    def _calculate_overall_confidence(self, entity_id: str) -> float:
        """计算总体置信度"""
        if entity_id not in self.trust_history:
            return 0.0

        total_weighted_confidence = 0.0
        total_weight = 0.0

        for dimension, scores in self.trust_history[entity_id].items():
            if scores:
                weight = self.dimension_weights.get(dimension, 0.1)
                total_weighted_confidence += scores[-1].confidence * weight
                total_weight += weight

        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0

    def _get_overall_risk_assessment(self, entity_id: str) -> Dict[str, Any]:
        """获取总体风险评估"""
        try:
            # 评估所有风险类别
            category_risks = {}
            overall_risk = 0.0
            highest_category = None

            for category in RiskCategory:
                # 基于历史数据简单评估风险
                history_risks = self._calculate_category_history_risk(entity_id, category)
                category_risks[category.value] = {
                    "risk_level": history_risks,
                    "threshold": self.risk_thresholds[category.value],
                    "is_risk": history_risks > self.risk_thresholds[category.value],
                }
                overall_risk = max(overall_risk, history_risks)
                if history_risks > self.risk_thresholds[category.value] and not highest_category:
                    highest_category = category.value

            return {
                "overall_risk_level": overall_risk,
                "risk_category": highest_category or "none",
                "category_assessments": category_risks,
            }

        except Exception:
            return {"overall_risk_level": 0.0, "risk_category": "none", "category_assessments": {}}

    def _get_trust_history_summary(self, entity_id: str) -> List[Dict[str, Any]]:
        """获取信任历史摘要"""
        summary = []
        for dimension, scores in self.trust_history[entity_id].items():
            for score in scores[-10:]:  # 最近10个评分
                summary.append(
                    {
                        "dimension": dimension.value,
                        "score": score.score,
                        "confidence": score.confidence,
                        "timestamp": score.last_updated,
                        "source": score.source,
                    }
                )

        summary.sort(key=lambda x: x["timestamp"])
        return summary

    def _calculate_category_risk(
        self,
        entity_id: str,
        category: RiskCategory,
        trust_info: Dict[str, Any],
        history_data: List[Dict[str, Any]],
        characteristics: Dict[str, Any],
    ) -> float:
        """计算指定类别的风险"""
        try:
            # 基于信任评分、历史和特征计算风险
            trust_impact = 0.0
            if "detailed_scores" in trust_info:
                for dim_name, score_info in trust_info["detailed_scores"].items():
                    trust_impact += (1.0 - score_info["score"]) * 0.3

            # 基于历史评分波动计算风险
            history_risk = self._calculate_category_history_risk(entity_id, category)

            # 基于特征计算风险
            feature_risk = self._calculate_category_feature_risk(
                entity_id, category, characteristics
            )

            # 综合风险计算
            overall_risk = (
                trust_impact * 0.3
                + history_risk * 0.5
                + feature_risk * 0.2
            )

            return max(0.0, min(1.0, overall_risk))

        except Exception:
            return 0.0

    def _calculate_category_history_risk(
        self,
        entity_id: str,
        category: RiskCategory,
    ) -> float:
        """计算历史风险"""
        try:
            if entity_id not in self.trust_history:
                return 0.0

            # 根据历史评分计算波动性风险
            total_volatility = 0.0
            total_categories = 0

            for dimension, scores in self.trust_history[entity_id].items():
                if len(scores) >= 3:
                    recent_scores = [s.score for s in scores[-3:]]
                    volatility = sum((s - sum(recent_scores) / len(recent_scores)) ** 2 for s in recent_scores)
                    total_volatility += volatility ** 0.5
                    total_categories += 1

            return total_volatility / max(1, total_categories)

        except Exception:
            return 0.0

    def _calculate_category_feature_risk(
        self,
        entity_id: str,
        category: RiskCategory,
        characteristics: Dict[str, Any],
    ) -> float:
        """计算特征风险"""
        try:
            if category == RiskCategory.BEHAVIORAL:
                # 基于行为特征评估风险
                return float(characteristics.get("behavior_risk", 0.0))
            elif category == RiskCategory.DATA:
                # 基于数据特征评估风险
                return float(characteristics.get("data_risk", 0.0))
            elif category == RiskCategory.MODEL:
                # 基于模型特征评估风险
                return float(characteristics.get("model_risk", 0.0))
            elif category == RiskCategory.ENVIRONMENTAL:
                # 基于环境特征评估风险
                return float(characteristics.get("environmental_risk", 0.0))
            else:
                return 0.0

        except Exception:
            return 0.0

    def _generate_risk_recommendations(
        self,
        entity_id: str,
        risk_assessments: Dict[str, Any],
        overall_risk: float,
        characteristics: Dict[str, Any],
    ) -> List[str]:
        """生成风险建议"""
        recommendations = []

        if overall_risk > 0.8:
            recommendations.extend([
                "立即停止所有高风险交互",
                "进行全面风险评估",
                "实施强化安全措施",
            ])
        elif overall_risk > 0.6:
            recommendations.extend([
                "限制交互频率",
                "实施监控措施",
                "制定应急预案",
            ])
        elif overall_risk > 0.4:
            recommendations.extend([
                "实施中期审查",
                "增加记录和审计",
                "制定改进计划",
            ])
        else:
            recommendations.extend([
                "继续监控风险水平",
                "定期评估合规性",
            ])

        return recommendations

    def _determine_relationship_type(
        self,
        source_trust: Dict[str, Any],
        target_trust: Dict[str, Any],
    ) -> str:
        """确定关系类型"""
        source_score = source_trust["overall_score"]
        target_score = target_trust["overall_score"]

        if source_score >= 0.7 and target_score >= 0.7:
            return "peer" if abs(source_score - target_score) < 0.2 else "superior"
        elif source_score >= 0.4 and target_score >= 0.4:
            return "peer"
        else:
            return "subordinate"

    def _calculate_trend(self, scores: List[float]) -> str:
        """计算趋势"""
        if len(scores) < 2:
            return "stable"

        recent_change = scores[-1] - scores[0]
        if abs(recent_change) < 0.05:
            return "stable"
        elif recent_change > 0.05:
            return "increasing"
        else:
            return "decreasing"

    def _calculate_overall_trend(
        self,
        entity_id: str,
        start_time: float,
        end_time: float,
    ) -> str:
        """计算总体趋势"""
        try:
            all_scores = []
            for dimension_scores in self.trust_history[entity_id].values():
                for score in dimension_scores:
                    if start_time <= score.last_updated <= end_time:
                        all_scores.append(score.score)

            if len(all_scores) < 2:
                return "stable"

            return self._calculate_trend(all_scores)

        except Exception:
            return "stable"

    def _cleanup_cache_if_needed(self) -> None:
        """清理缓存"""
        current_time = time.time()
        if current_time - self._last_cache_cleared > 300.0:  # 5分钟
            # 清理信任计算缓存
            self._trust_computation_cache = {
                k: v for k, v in self._trust_computation_cache.items()
                if current_time - v["timestamp"] < 300.0
            }

            # 清理关系计算缓存
            self._relationship_computation_cache = {
                k: v for k, v in self._relationship_computation_cache.items()
                if current_time - v["timestamp"] < 300.0
            }

            # 清理风险计算缓存
            self._risk_computation_cache = {
                k: v for k, v in self._risk_computation_cache.items()
                if current_time - v["timestamp"] < 300.0
            }

            self._last_cache_cleared = current_time
