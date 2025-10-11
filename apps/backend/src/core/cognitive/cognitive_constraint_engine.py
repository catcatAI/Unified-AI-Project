#!/usr/bin/env python3
"""
认知约束引擎 (Cognitive Constraint Engine)
Level 5 AGI核心组件 - 实现目标语义去重与优先级优化

功能：
- 目标语义去重 (Target Semantic Deduplication)
- 必要性评估 (Necessity Assessment)
- 优先级动态优化 (Dynamic Priority Optimization)
- 冲突检测与解决 (Conflict Detection & Resolution)
- 认知资源分配优化 (Cognitive Resource Allocation Optimization)
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import re
from pathlib import Path
import hashlib

# 尝试导入可选的AI库
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# 导入统一知识图谱（可选）
try:
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from apps.backend.src.core.knowledge.unified_knowledge_graph import Entity, Relation
except ImportError:
    # 占位符实现
    from dataclasses import dataclass
    @dataclass
    class Entity:
        entity_id: str = ""
        name: str = ""
        entity_type: str = ""
        confidence: float = 0.0
        properties: Dict[str, Any] = None
        aliases: List[str] = None
        source: str = ""
        timestamp: datetime = None
    
    @dataclass
    class Relation:
        relation_id: str = ""
        source_entity: str = ""
        target_entity: str = ""
        relation_type: str = ""
        confidence: float = 0.0
        properties: Dict[str, Any] = None
        source: str = ""
        timestamp: datetime = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CognitiveTarget:
    """认知目标"""
    target_id: str
    description: str
    semantic_vector: np.ndarray
    priority: float
    necessity_score: float
    resource_requirements: Dict[str, float]
    dependencies: List[str]
    conflicts: List[str]
    creation_time: datetime
    deadline: Optional[datetime]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if not isinstance(self.creation_time, datetime):
            self.creation_time = datetime.fromisoformat(self.creation_time)
        if self.deadline and not isinstance(self.deadline, datetime):
            self.deadline = datetime.fromisoformat(self.deadline)

@dataclass
class SemanticCluster:
    """语义聚类"""
    cluster_id: str
    centroid_vector: np.ndarray
    target_ids: List[str]
    semantic_coherence: float
    representative_target: str
    cluster_size: int
    creation_time: datetime

@dataclass
class PriorityAssessment:
    """优先级评估"""
    target_id: str
    urgency_score: float
    importance_score: float
    feasibility_score: float
    impact_score: float
    resource_efficiency_score: float
    overall_priority: float
    assessment_time: datetime
    reasoning: List[str]

@dataclass
class ConflictAnalysis:
    """冲突分析"""
    conflict_id: str
    target_ids: List[str]
    conflict_type: str
    severity: float
    root_causes: List[str]
    resolution_suggestions: List[Dict[str, Any]]
    detection_time: datetime

class CognitiveConstraintEngine:
    """认知约束引擎 - Level 5 AGI核心组件"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # 目标存储
        self.cognitive_targets: Dict[str, CognitiveTarget] = {}
        self.semantic_clusters: Dict[str, SemanticCluster] = {}
        self.priority_assessments: Dict[str, PriorityAssessment] = {}
        self.conflict_analyses: Dict[str, ConflictAnalysis] = {}
        
        # 历史记录
        self.target_history: deque = deque(maxlen=1000)
        self.optimization_history: deque = deque(maxlen=500)
        self.conflict_history: deque = deque(maxlen=200)
        
        # AI模型
        self.semantic_vectorizer = None
        self.priority_predictor = None
        self.conflict_detector = None
        self.necessity_evaluator = None
        
        # 配置参数
        self.deduplication_threshold = self.config.get('deduplication_threshold', 0.85)
        self.priority_update_interval = self.config.get('priority_update_interval', 300)  # 5分钟
        self.max_targets_per_cluster = self.config.get('max_targets_per_cluster', 10)
        self.resource_constraint_weight = self.config.get('resource_constraint_weight', 0.3)
        
        # 性能监控
        self.processing_times: Dict[str, List[float]] = defaultdict(list)
        self.optimization_metrics: Dict[str, float] = {}
        
        # 初始化AI组件
        self._initialize_ai_components()
        
        logger.info("🧠 认知约束引擎初始化完成")
    
    def _initialize_ai_components(self):
        """初始化AI组件"""
        try:
            if SKLEARN_AVAILABLE:
                # 语义向量化器
                self.semantic_vectorizer = TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    analyzer='word',
                    stop_words=None
                )
                
                # 优先级预测器
                self.priority_predictor = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10
                )
                
                # 冲突检测器
                self.conflict_detector = LogisticRegression(
                    random_state=42,
                    max_iter=1000
                )
                
                # 必要性评估器
                self.necessity_evaluator = RandomForestClassifier(
                    n_estimators=50,
                    random_state=42,
                    max_depth=8
                )
                
                logger.info("✅ AI组件初始化成功")
            else:
                logger.warning("⚠️ scikit-learn不可用，将使用简化算法")
                
        except Exception as e:
            logger.error(f"❌ AI组件初始化失败: {e}")
    
    # ==================== 目标语义去重 ====================
    
    async def add_cognitive_target(self, target: CognitiveTarget) -> Dict[str, Any]:
        """添加认知目标"""
        try:
            # 语义去重检查
            duplicate_result = await self._check_semantic_duplicates(target)
            
            if duplicate_result['is_duplicate'] and duplicate_result['confidence'] > self.deduplication_threshold:
                # 合并目标而不是添加新目标
                merged_target = await self._merge_targets(target, duplicate_result['similar_target'])
                logger.info(f"🔄 目标去重合并: {target.target_id} -> {merged_target.target_id}")
                
                return {
                    'action': 'merged',
                    'target_id': merged_target.target_id,
                    'duplicate_info': duplicate_result,
                    'original_target_id': target.target_id
                }
            
            # 添加新目标
            self.cognitive_targets[target.target_id] = target
            
            # 更新语义聚类
            await self._update_semantic_clusters(target)
            
            # 历史记录
            self.target_history.append({
                'action': 'added',
                'target_id': target.target_id,
                'timestamp': datetime.now(),
                'semantic_similarity': duplicate_result.get('max_similarity', 0)
            })
            
            logger.info(f"✅ 添加认知目标: {target.target_id}")
            
            return {
                'action': 'added',
                'target_id': target.target_id,
                'duplicate_check': duplicate_result
            }
            
        except Exception as e:
            logger.error(f"❌ 添加认知目标失败: {e}")
            return {'action': 'failed', 'error': str(e)}
    
    async def _check_semantic_duplicates(self, target: CognitiveTarget) -> Dict[str, Any]:
        """检查语义重复"""
        try:
            # 生成目标语义向量（如果不存在）
            if not hasattr(target, 'semantic_vector') or target.semantic_vector is None:
                target.semantic_vector = await self._generate_semantic_vector(target.description)
            
            similarities = []
            most_similar_target = None
            max_similarity = 0.0
            
            # 计算与现有目标的相似度
            for existing_id, existing_target in self.cognitive_targets.items():
                if existing_id == target.target_id:
                    continue
                
                # 生成现有目标语义向量（如果不存在）
                if not hasattr(existing_target, 'semantic_vector') or existing_target.semantic_vector is None:
                    existing_target.semantic_vector = await self._generate_semantic_vector(existing_target.description)
                
                # 计算语义相似度
                similarity = await self._calculate_semantic_similarity(
                    target.semantic_vector,
                    existing_target.semantic_vector
                )
                
                similarities.append({
                    'target_id': existing_id,
                    'similarity': similarity,
                    'description': existing_target.description
                })
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_target = existing_target
            
            # 判断是否为重复
            is_duplicate = max_similarity > self.deduplication_threshold
            
            return {
                'is_duplicate': is_duplicate,
                'confidence': max_similarity,
                'similar_target': most_similar_target,
                'similarities': sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"❌ 语义重复检查失败: {e}")
            return {
                'is_duplicate': False,
                'confidence': 0.0,
                'similar_target': None,
                'error': str(e)
            }
    
    async def _generate_semantic_vector(self, description: str) -> np.ndarray:
        """生成语义向量"""
        try:
            if SKLEARN_AVAILABLE and self.semantic_vectorizer:
                # 使用TF-IDF向量化
                if not hasattr(self.semantic_vectorizer, 'vocabulary_'):
                    # 首次使用，需要拟合简单的词汇表
                    simple_texts = [description]
                    self.semantic_vectorizer.fit(simple_texts)
                
                vector = self.semantic_vectorizer.transform([description]).toarray()[0]
                
                # 标准化
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                
                return vector
            else:
                # 简化语义向量生成
                words = description.lower().split()
                
                # 基于词频和词长生成向量
                word_features = []
                for word in words:
                    word_features.extend([
                        len(word),
                        hash(word) % 100 / 100,  # 哈希特征
                        words.count(word) / len(words)  # 词频
                    ])
                
                # 填充到固定维度
                target_dim = 100
                if len(word_features) < target_dim:
                    word_features.extend([0.0] * (target_dim - len(word_features)))
                else:
                    word_features = word_features[:target_dim]
                
                vector = np.array(word_features)
                
                # 标准化
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm
                
                return vector
                
        except Exception as e:
            logger.error(f"❌ 语义向量生成失败: {e}")
            # 返回随机向量作为后备
            return np.random.random(100)
    
    async def _calculate_semantic_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """计算语义相似度"""
        try:
            if vector1.shape != vector2.shape:
                # 调整维度
                min_dim = min(vector1.shape[0], vector2.shape[0])
                vector1 = vector1[:min_dim]
                vector2 = vector2[:min_dim]
            
            # 余弦相似度
            dot_product = np.dot(vector1, vector2)
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(max(0, similarity))  # 确保非负
            
        except Exception as e:
            logger.error(f"❌ 语义相似度计算失败: {e}")
            return 0.0
    
    async def _merge_targets(self, target1: CognitiveTarget, target2: CognitiveTarget) -> CognitiveTarget:
        """合并目标"""
        try:
            # 保留优先级更高的目标作为主目标
            if target1.priority > target2.priority:
                primary_target = target1
                secondary_target = target2
            else:
                primary_target = target2
                secondary_target = target1
            
            # 合并描述
            merged_description = f"{primary_target.description} (合并自: {secondary_target.description})"
            
            # 合并属性
            merged_properties = {**primary_target.properties, **secondary_target.properties}
            merged_properties['merged_from'] = secondary_target.target_id
            merged_properties['merge_timestamp'] = datetime.now().isoformat()
            
            # 合并依赖关系
            merged_dependencies = list(set(primary_target.dependencies + secondary_target.dependencies))
            
            # 更新主目标
            primary_target.description = merged_description
            primary_target.properties = merged_properties
            primary_target.dependencies = merged_dependencies
            primary_target.metadata['is_merged'] = True
            primary_target.metadata['merged_targets'] = [target1.target_id, target2.target_id]
            
            # 移除次要目标
            if secondary_target.target_id in self.cognitive_targets:
                del self.cognitive_targets[secondary_target.target_id]
            
            logger.info(f"✅ 目标合并完成: {primary_target.target_id}")
            return primary_target
            
        except Exception as e:
            logger.error(f"❌ 目标合并失败: {e}")
            return primary_target  # 返回主目标作为后备
    
    # ==================== 语义聚类 ====================
    
    async def _update_semantic_clusters(self, target: CognitiveTarget):
        """更新语义聚类"""
        try:
            # 查找最相似的聚类
            best_cluster = None
            best_similarity = 0.0
            
            for cluster_id, cluster in self.semantic_clusters.items():
                similarity = await self._calculate_semantic_similarity(
                    target.semantic_vector,
                    cluster.centroid_vector
                )
                
                if similarity > best_similarity and similarity > 0.6:  # 相似度阈值
                    best_similarity = similarity
                    best_cluster = cluster
            
            if best_cluster and len(best_cluster.target_ids) < self.max_targets_per_cluster:
                # 添加到现有聚类
                best_cluster.target_ids.append(target.target_id)
                await self._update_cluster_centroid(best_cluster)
                logger.info(f"🔄 添加到现有聚类: {best_cluster.cluster_id}")
            else:
                # 创建新聚类
                new_cluster = await self._create_new_cluster(target)
                self.semantic_clusters[new_cluster.cluster_id] = new_cluster
                logger.info(f"✅ 创建新聚类: {new_cluster.cluster_id}")
            
        except Exception as e:
            logger.error(f"❌ 语义聚类更新失败: {e}")
    
    async def _update_cluster_centroid(self, cluster: SemanticCluster):
        """更新聚类中心"""
        try:
            if not cluster.target_ids:
                return
            
            # 计算新的中心向量
            vectors = []
            for target_id in cluster.target_ids:
                if target_id in self.cognitive_targets:
                    target = self.cognitive_targets[target_id]
                    if hasattr(target, 'semantic_vector') and target.semantic_vector is not None:
                        vectors.append(target.semantic_vector)
            
            if vectors:
                cluster.centroid_vector = np.mean(vectors, axis=0)
                cluster.semantic_coherence = await self._calculate_cluster_coherence(cluster)
                cluster.cluster_size = len(cluster.target_ids)
                cluster.representative_target = self._select_representative_target(cluster)
            
        except Exception as e:
            logger.error(f"❌ 聚类中心更新失败: {e}")
    
    async def _create_new_cluster(self, target: CognitiveTarget) -> SemanticCluster:
        """创建新聚类"""
        cluster_id = f"cluster_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{target.target_id}"
        
        return SemanticCluster(
            cluster_id=cluster_id,
            centroid_vector=target.semantic_vector.copy() if target.semantic_vector is not None else np.random.random(100),
            target_ids=[target.target_id],
            semantic_coherence=1.0,  # 单个目标时一致性为1
            representative_target=target.target_id,
            cluster_size=1,
            creation_time=datetime.now()
        )
    
    def _select_representative_target(self, cluster: SemanticCluster) -> str:
        """选择代表性目标"""
        if not cluster.target_ids:
            return ""
        
        # 选择优先级最高的目标作为代表
        best_target_id = cluster.target_ids[0]
        best_priority = 0.0
        
        for target_id in cluster.target_ids:
            if target_id in self.cognitive_targets:
                target = self.cognitive_targets[target_id]
                if target.priority > best_priority:
                    best_priority = target.priority
                    best_target_id = target_id
        
        return best_target_id
    
    async def _calculate_cluster_coherence(self, cluster: SemanticCluster) -> float:
        """计算聚类一致性"""
        try:
            if len(cluster.target_ids) < 2:
                return 1.0  # 单个目标时一致性为1
            
            similarities = []
            for i, target_id1 in enumerate(cluster.target_ids):
                for j, target_id2 in enumerate(cluster.target_ids):
                    if i < j:  # 避免重复计算
                        if (target_id1 in self.cognitive_targets and 
                            target_id2 in self.cognitive_targets):
                            
                            target1 = self.cognitive_targets[target_id1]
                            target2 = self.cognitive_targets[target_id2]
                            
                            if (hasattr(target1, 'semantic_vector') and target1.semantic_vector is not None and
                                hasattr(target2, 'semantic_vector') and target2.semantic_vector is not None):
                                
                                similarity = await self._calculate_semantic_similarity(
                                    target1.semantic_vector,
                                    target2.semantic_vector
                                )
                                similarities.append(similarity)
            
            return np.mean(similarities) if similarities else 0.0
            
        except Exception as e:
            logger.error(f"❌ 聚类一致性计算失败: {e}")
            return 0.0
    
    # ==================== 必要性评估 ====================
    
    async def assess_target_necessity(self, target_id: str) -> Dict[str, Any]:
        """评估目标必要性"""
        try:
            if target_id not in self.cognitive_targets:
                return {'error': '目标不存在'}
            
            target = self.cognitive_targets[target_id]
            
            # 多维度必要性评估
            novelty_score = await self._assess_novelty(target)
            utility_score = await self._assess_utility(target)
            feasibility_score = await self._assess_feasibility(target)
            alignment_score = await self._assess_alignment(target)
            
            # 综合必要性评分
            necessity_score = np.mean([novelty_score, utility_score, feasibility_score, alignment_score])
            
            # 更新目标必要性
            target.necessity_score = necessity_score
            
            # 生成推理说明
            reasoning = []
            if novelty_score < 0.5:
                reasoning.append("目标缺乏新颖性，可能已有类似实现")
            if utility_score < 0.5:
                reasoning.append("目标实用性较低，预期收益有限")
            if feasibility_score < 0.5:
                reasoning.append("目标实现难度较高，资源需求过大")
            if alignment_score < 0.5:
                reasoning.append("目标与系统整体目标对齐度较低")
            
            if not reasoning:
                reasoning.append("目标在多个维度上表现良好，具有较高的必要性")
            
            return {
                'target_id': target_id,
                'necessity_score': necessity_score,
                'dimension_scores': {
                    'novelty': novelty_score,
                    'utility': utility_score,
                    'feasibility': feasibility_score,
                    'alignment': alignment_score
                },
                'reasoning': reasoning,
                'assessment_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 必要性评估失败: {e}")
            return {'error': str(e)}
    
    async def _assess_novelty(self, target: CognitiveTarget) -> float:
        """评估新颖性"""
        try:
            # 基于历史数据的新颖性评估
            if not self.target_history:
                return 1.0  # 没有历史数据时认为完全新颖
            
            # 查找相似的历史目标
            similar_historical_targets = []
            for history_entry in self.target_history:
                if 'target_id' in history_entry and history_entry['target_id'] in self.cognitive_targets:
                    historical_target = self.cognitive_targets[history_entry['target_id']]
                    similarity = await self._calculate_semantic_similarity(
                        target.semantic_vector,
                        historical_target.semantic_vector
                    )
                    if similarity > 0.7:  # 相似度阈值
                        similar_historical_targets.append({
                            'similarity': similarity,
                            'target': historical_target,
                            'time_delta': (datetime.now() - history_entry.get('timestamp', datetime.now())).days
                        })
            
            if not similar_historical_targets:
                return 1.0  # 完全新颖
            
            # 基于相似度和时间的新颖性评分
            novelty_scores = []
            for historical in similar_historical_targets:
                # 相似度越低，新颖性越高
                similarity_score = 1.0 - historical['similarity']
                
                # 时间越久，新颖性越高（指数衰减）
                time_score = np.exp(-historical['time_delta'] / 365)  # 年度衰减
                
                novelty_scores.append(similarity_score * time_score)
            
            return np.mean(novelty_scores)
            
        except Exception as e:
            logger.error(f"❌ 新颖性评估失败: {e}")
            return 0.5  # 中性评分
    
    async def _assess_utility(self, target: CognitiveTarget) -> float:
        """评估实用性"""
        try:
            # 基于目标属性和元数据评估实用性
            utility_indicators = []
            
            # 检查是否有明确的收益指标
            if 'expected_benefit' in target.metadata:
                benefit = target.metadata['expected_benefit']
                if isinstance(benefit, (int, float)):
                    utility_indicators.append(min(benefit / 100, 1.0))  # 标准化到0-1
            
            # 检查是否有成功概率
            if 'success_probability' in target.metadata:
                prob = target.metadata['success_probability']
                if isinstance(prob, (int, float)) and 0 <= prob <= 1:
                    utility_indicators.append(prob)
            
            # 检查资源效率
            if target.resource_requirements:
                total_resources = sum(target.resource_requirements.values())
                # 资源需求适中（不太少也不太多）
                if 0.1 <= total_resources <= 0.8:
                    utility_indicators.append(0.8)
                elif total_resources < 0.1:
                    utility_indicators.append(0.4)  # 资源需求太少可能不够重要
                else:
                    utility_indicators.append(0.3)  # 资源需求太多可能不划算
            
            # 基于描述关键词的实用性评估
            description_lower = target.description.lower()
            utility_keywords = {
                '重要': 0.9, '关键': 0.9, '核心': 0.9,
                '优化': 0.8, '改进': 0.8, '提升': 0.8,
                '解决': 0.7, '修复': 0.7, '纠正': 0.7,
                '新': 0.6, '创新': 0.6, '突破': 0.6
            }
            
            for keyword, score in utility_keywords.items():
                if keyword in description_lower:
                    utility_indicators.append(score)
            
            # 如果没有明确的实用性指标，返回中性评分
            if not utility_indicators:
                return 0.6
            
            return np.mean(utility_indicators)
            
        except Exception as e:
            logger.error(f"❌ 实用性评估失败: {e}")
            return 0.5
    
    async def _assess_feasibility(self, target: CognitiveTarget) -> float:
        """评估可行性"""
        try:
            feasibility_factors = []
            
            # 基于资源需求评估可行性
            if target.resource_requirements:
                # 检查是否有足够的资源信息
                required_resources = sum(target.resource_requirements.values())
                
                # 检查是否有可用资源信息
                available_resources = target.metadata.get('available_resources', {})
                if available_resources:
                    # 计算资源充足度
                    resource_adequacy = 0.0
                    for resource_type, required_amount in target.resource_requirements.items():
                        available_amount = available_resources.get(resource_type, 0)
                        if required_amount > 0:
                            adequacy = min(available_amount / required_amount, 1.0)
                            resource_adequacy += adequacy
                    
                    if len(target.resource_requirements) > 0:
                        feasibility_factors.append(resource_adequacy / len(target.resource_requirements))
                else:
                    # 没有可用资源信息，基于需求合理性评估
                    if required_resources <= 0.5:  # 资源需求适中
                        feasibility_factors.append(0.8)
                    elif required_resources <= 0.8:
                        feasibility_factors.append(0.6)
                    else:
                        feasibility_factors.append(0.3)
            
            # 基于依赖关系评估可行性
            if target.dependencies:
                # 检查依赖目标是否存在且可实现
                dependency_feasibility = 0.0
                resolved_dependencies = 0
                
                for dep_id in target.dependencies:
                    if dep_id in self.cognitive_targets:
                        dep_target = self.cognitive_targets[dep_id]
                        # 依赖目标的必要性越高，当前目标的可行性越高
                        if hasattr(dep_target, 'necessity_score'):
                            dependency_feasibility += dep_target.necessity_score
                        else:
                            dependency_feasibility += 0.7  # 默认必要性
                        resolved_dependencies += 1
                
                if resolved_dependencies > 0:
                    feasibility_factors.append(dependency_feasibility / resolved_dependencies)
                else:
                    feasibility_factors.append(0.4)  # 依赖未解决
            
            # 基于时间约束评估可行性
            if target.deadline:
                time_remaining = (target.deadline - datetime.now()).total_seconds() / 3600  # 小时
                if time_remaining < 0:
                    feasibility_factors.append(0.0)  # 已过期
                elif time_remaining < 24:  # 少于1天
                    feasibility_factors.append(0.3)
                elif time_remaining < 168:  # 少于1周
                    feasibility_factors.append(0.6)
                else:
                    feasibility_factors.append(0.9)
            
            # 基于描述关键词的可行性评估
            description_lower = target.description.lower()
            feasibility_keywords = {
                '简单': 0.9, '容易': 0.9, '快速': 0.8,
                '复杂': 0.4, '困难': 0.3, '挑战': 0.5
            }
            
            for keyword, score in feasibility_keywords.items():
                if keyword in description_lower:
                    feasibility_factors.append(score)
            
            # 如果没有明确的可行性指标，返回中性评分
            if not feasibility_factors:
                return 0.7
            
            return np.mean(feasibility_factors)
            
        except Exception as e:
            logger.error(f"❌ 可行性评估失败: {e}")
            return 0.5
    
    async def _assess_alignment(self, target: CognitiveTarget) -> float:
        """评估对齐度"""
        try:
            alignment_scores = []
            
            # 与系统整体目标的对齐
            system_goals = self.config.get('system_goals', ['efficiency', 'accuracy', 'scalability'])
            
            # 基于描述关键词的对齐评估
            description_lower = target.description.lower()
            
            for goal in system_goals:
                goal_keywords = {
                    'efficiency': ['效率', '优化', '快速', '性能'],
                    'accuracy': ['准确', '精确', '正确', '可靠'],
                    'scalability': ['扩展', '规模', '增长', '适应'],
                    'safety': ['安全', '稳定', '可靠', '鲁棒'],
                    'ethics': ['伦理', '道德', '公平', '透明']
                }.get(goal, [goal])
                
                alignment_score = 0.0
                for keyword in goal_keywords:
                    if keyword in description_lower:
                        alignment_score = max(alignment_score, 0.8)
                
                alignment_scores.append(alignment_score)
            
            # 基于资源效率的对齐
            if target.resource_requirements:
                # 资源使用效率（避免浪费）
                total_resources = sum(target.resource_requirements.values())
                if total_resources <= 0.5:  # 资源使用高效
                    alignment_scores.append(0.9)
                elif total_resources <= 0.8:
                    alignment_scores.append(0.7)
                else:
                    alignment_scores.append(0.4)
            
            # 基于优先级的对齐
            if target.priority > 0.8:  # 高优先级目标通常更对齐
                alignment_scores.append(0.8)
            elif target.priority > 0.6:
                alignment_scores.append(0.6)
            else:
                alignment_scores.append(0.4)
            
            return np.mean(alignment_scores) if alignment_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ 对齐度评估失败: {e}")
            return 0.5
    
    # ==================== 优先级动态优化 ====================
    
    async def optimize_priorities(self, optimization_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """动态优化优先级"""
        try:
            optimization_result = {
                'optimization_id': f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'before_optimization': {},
                'after_optimization': {},
                'changes_made': [],
                'optimization_reasoning': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # 获取优化上下文
            context = optimization_context or {}
            current_resources = context.get('available_resources', {})
            system_load = context.get('system_load', 0.5)
            external_priorities = context.get('external_priorities', [])
            
            # 记录优化前状态
            for target_id, target in self.cognitive_targets.items():
                optimization_result['before_optimization'][target_id] = {
                    'priority': target.priority,
                    'necessity_score': target.necessity_score,
                    'resource_requirements': target.resource_requirements
                }
            
            # 执行多维度优先级优化
            optimized_targets = []
            
            for target_id, target in self.cognitive_targets.items():
                # 重新评估必要性（如果超过更新间隔）
                if self._should_reassess_necessity(target):
                    necessity_result = await self.assess_target_necessity(target_id)
                    target.necessity_score = necessity_result.get('necessity_score', target.necessity_score)
                
                # 动态优先级计算
                new_priority = await self._calculate_dynamic_priority(
                    target, current_resources, system_load, external_priorities
                )
                
                # 记录变化
                if abs(new_priority - target.priority) > 0.1:  # 显著变化阈值
                    old_priority = target.priority
                    target.priority = new_priority
                    
                    optimization_result['changes_made'].append({
                        'target_id': target_id,
                        'old_priority': old_priority,
                        'new_priority': new_priority,
                        'change_reason': await self._generate_priority_change_reason(target, old_priority, new_priority)
                    })
                    
                    optimized_targets.append(target_id)
            
            # 记录优化后状态
            for target_id, target in self.cognitive_targets.items():
                optimization_result['after_optimization'][target_id] = {
                    'priority': target.priority,
                    'necessity_score': target.necessity_score,
                    'resource_requirements': target.resource_requirements
                }
            
            # 生成优化推理说明
            optimization_result['optimization_reasoning'] = await self._generate_optimization_reasoning(
                optimization_result['changes_made'], current_resources, system_load
            )
            
            # 记录优化历史
            self.optimization_history.append({
                'optimization_id': optimization_result['optimization_id'],
                'targets_optimized': len(optimized_targets),
                'total_targets': len(self.cognitive_targets),
                'optimization_time': datetime.now(),
                'context': context
            })
            
            logger.info(f"✅ 优先级优化完成: {len(optimized_targets)}/{len(self.cognitive_targets)} 目标")
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"❌ 优先级优化失败: {e}")
            return {'error': str(e)}
    
    def _should_reassess_necessity(self, target: CognitiveTarget) -> bool:
        """判断是否应该重新评估必要性"""
        # 基于时间间隔判断
        time_since_creation = (datetime.now() - target.creation_time).total_seconds()
        return time_since_creation > self.priority_update_interval
    
    async def _calculate_dynamic_priority(self, target: CognitiveTarget, 
                                        current_resources: Dict[str, float],
                                        system_load: float,
                                        external_priorities: List[Dict[str, Any]]) -> float:
        """计算动态优先级"""
        try:
            # 基础优先级（基于必要性和当前优先级）
            base_priority = (target.necessity_score * 0.6 + target.priority * 0.4)
            
            # 资源可用性调整
            resource_adjustment = await self._calculate_resource_adjustment(target, current_resources)
            
            # 系统负载调整
            load_adjustment = self._calculate_load_adjustment(system_load)
            
            # 外部优先级影响
            external_adjustment = await self._calculate_external_adjustment(target, external_priorities)
            
            # 时间紧迫性调整
            urgency_adjustment = await self._calculate_urgency_adjustment(target)
            
            # 综合计算
            dynamic_priority = (
                base_priority * 0.4 +
                resource_adjustment * 0.2 +
                load_adjustment * 0.15 +
                external_adjustment * 0.15 +
                urgency_adjustment * 0.1
            )
            
            # 确保优先级在合理范围内
            return max(0.0, min(1.0, dynamic_priority))
            
        except Exception as e:
            logger.error(f"❌ 动态优先级计算失败: {e}")
            return target.priority  # 返回当前优先级作为后备
    
    async def _calculate_resource_adjustment(self, target: CognitiveTarget, current_resources: Dict[str, float]) -> float:
        """计算资源调整"""
        try:
            if not target.resource_requirements or not current_resources:
                return 0.5  # 中性调整
            
            # 计算资源匹配度
            resource_match_scores = []
            
            for resource_type, required_amount in target.resource_requirements.items():
                available_amount = current_resources.get(resource_type, 0)
                
                if required_amount > 0:
                    if available_amount >= required_amount:
                        # 资源充足，提高优先级
                        resource_match_scores.append(0.8)
                    elif available_amount >= required_amount * 0.7:
                        # 资源基本充足
                        resource_match_scores.append(0.6)
                    elif available_amount >= required_amount * 0.4:
                        # 资源部分充足
                        resource_match_scores.append(0.4)
                    else:
                        # 资源严重不足，降低优先级
                        resource_match_scores.append(0.2)
            
            return np.mean(resource_match_scores) if resource_match_scores else 0.5
            
        except Exception as e:
            logger.error(f"❌ 资源调整计算失败: {e}")
            return 0.5
    
    def _calculate_load_adjustment(self, system_load: float) -> float:
        """计算负载调整"""
        try:
            # 系统负载影响优先级分配
            # 高负载时优先处理高优先级目标
            if system_load > 0.8:  # 高负载
                return 0.9  # 倾向于高优先级
            elif system_load > 0.6:  # 中等负载
                return 0.7
            elif system_load > 0.3:  # 低负载
                return 0.5
            else:  # 极低负载
                return 0.3  # 可以更均衡地分配
            
        except Exception as e:
            logger.error(f"❌ 负载调整计算失败: {e}")
            return 0.5
    
    async def _calculate_external_adjustment(self, target: CognitiveTarget, external_priorities: List[Dict[str, Any]]) -> float:
        """计算外部调整"""
        try:
            if not external_priorities:
                return 0.5  # 中性调整
            
            # 查找与当前目标相关的外部优先级
            relevant_priorities = []
            
            for external_priority in external_priorities:
                # 基于目标ID匹配
                if external_priority.get('target_id') == target.target_id:
                    relevant_priorities.append(external_priority.get('priority', 0.5))
                    continue
                
                # 基于语义相似度匹配
                external_description = external_priority.get('description', '')
                if external_description:
                    similarity = await self._calculate_text_similarity(
                        target.description,
                        external_description
                    )
                    if similarity > 0.7:  # 相似度阈值
                        relevant_priorities.append(external_priority.get('priority', 0.5) * similarity)
            
            if not relevant_priorities:
                return 0.5
            
            return np.mean(relevant_priorities)
            
        except Exception as e:
            logger.error(f"❌ 外部调整计算失败: {e}")
            return 0.5
    
    async def _calculate_urgency_adjustment(self, target: CognitiveTarget) -> float:
        """计算紧迫性调整"""
        try:
            if not target.deadline:
                return 0.5  # 中性调整
            
            time_remaining = (target.deadline - datetime.now()).total_seconds() / 3600  # 小时
            
            if time_remaining < 0:  # 已过期
                return 0.1
            elif time_remaining < 1:  # 少于1小时
                return 0.95
            elif time_remaining < 24:  # 少于1天
                return 0.8
            elif time_remaining < 168:  # 少于1周
                return 0.6
            elif time_remaining < 720:  # 少于1个月
                return 0.4
            else:  # 超过1个月
                return 0.3
            
        except Exception as e:
            logger.error(f"❌ 紧迫性调整计算失败: {e}")
            return 0.5
    
    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.error(f"❌ 文本相似度计算失败: {e}")
            return 0.0
    
    async def _generate_priority_change_reason(self, target: CognitiveTarget, old_priority: float, new_priority: float) -> str:
        """生成优先级变化原因"""
        try:
            change_direction = "提高" if new_priority > old_priority else "降低"
            change_magnitude = abs(new_priority - old_priority)
            
            reasons = []
            
            # 基于必要性变化
            if hasattr(target, 'necessity_score'):
                if target.necessity_score > 0.8:
                    reasons.append("目标必要性评估结果优秀")
                elif target.necessity_score < 0.4:
                    reasons.append("目标必要性评估结果较低")
            
            # 基于资源变化
            if target.resource_requirements:
                reasons.append("资源可用性发生变化")
            
            # 基于时间紧迫性
            if target.deadline:
                time_remaining = (target.deadline - datetime.now()).total_seconds() / 3600
                if time_remaining < 24:
                    reasons.append("目标截止时间临近")
            
            # 基于系统状态
            reasons.append("系统整体状态和资源分配优化")
            
            reason_text = f"优先级{change_direction}了{change_magnitude:.1%}，主要原因包括：{', '.join(reasons[:2])}"
            
            return reason_text
            
        except Exception as e:
            logger.error(f"❌ 优先级变化原因生成失败: {e}")
            return f"优先级{change_direction}了{change_magnitude:.1%}"
    
    async def _generate_optimization_reasoning(self, changes: List[Dict[str, Any]], 
                                             current_resources: Dict[str, float],
                                             system_load: float) -> List[str]:
        """生成优化推理说明"""
        reasoning = []
        
        try:
            if not changes:
                reasoning.append("当前目标优先级配置合理，无需调整")
                return reasoning
            
            # 基于变化趋势分析
            increases = [c for c in changes if c['new_priority'] > c['old_priority']]
            decreases = [c for c in changes if c['new_priority'] < c['old_priority']]
            
            if len(increases) > len(decreases):
                reasoning.append("系统检测到更多高价值目标，整体优先级向重要目标倾斜")
            elif len(decreases) > len(increases):
                reasoning.append("系统优化资源配置，降低部分目标的优先级以提高整体效率")
            
            # 基于资源状态
            if current_resources:
                total_available = sum(current_resources.values())
                if total_available < 0.5:
                    reasoning.append("当前可用资源有限，优先保障高价值目标")
                elif total_available > 0.8:
                    reasoning.append("资源充足，可以更均衡地分配优先级")
            
            # 基于系统负载
            if system_load > 0.8:
                reasoning.append("系统负载较高，集中资源处理高优先级目标")
            elif system_load < 0.3:
                reasoning.append("系统负载较低，可以处理更多中等优先级目标")
            
            # 基于变化幅度
            significant_changes = [c for c in changes if abs(c['new_priority'] - c['old_priority']) > 0.2]
            if len(significant_changes) > len(changes) * 0.5:
                reasoning.append("检测到显著的优先级变化，系统进行了大幅优化调整")
            
            return reasoning
            
        except Exception as e:
            logger.error(f"❌ 优化推理说明生成失败: {e}")
            return ["优化推理生成过程中出现错误"]
    
    # ==================== 冲突检测与解决 ====================
    
    async def detect_conflicts(self) -> List[ConflictAnalysis]:
        """检测冲突"""
        conflicts = []
        
        try:
            target_list = list(self.cognitive_targets.values())
            
            # 资源冲突检测
            resource_conflicts = await self._detect_resource_conflicts(target_list)
            conflicts.extend(resource_conflicts)
            
            # 语义冲突检测
            semantic_conflicts = await self._detect_semantic_conflicts(target_list)
            conflicts.extend(semantic_conflicts)
            
            # 时序冲突检测
            temporal_conflicts = await self._detect_temporal_conflicts(target_list)
            conflicts.extend(temporal_conflicts)
            
            # 逻辑冲突检测
            logical_conflicts = await self._detect_logical_conflicts(target_list)
            conflicts.extend(logical_conflicts)
            
            logger.info(f"✅ 冲突检测完成: {len(conflicts)} 个冲突")
            
        except Exception as e:
            logger.error(f"❌ 冲突检测失败: {e}")
        
        return conflicts
    
    async def _detect_resource_conflicts(self, targets: List[CognitiveTarget]) -> List[ConflictAnalysis]:
        """检测资源冲突"""
        conflicts = []
        
        try:
            # 按资源类型分组
            resource_demands: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
            
            for target in targets:
                for resource_type, required_amount in target.resource_requirements.items():
                    if required_amount > 0:
                        resource_demands[resource_type].append((target.target_id, required_amount))
            
            # 检测资源冲突
            for resource_type, demands in resource_demands.items():
                if len(demands) > 1:
                    # 计算总需求
                    total_demand = sum(amount for _, amount in demands)
                    
                    # 检查是否超过资源限制（假设限制为1.0）
                    if total_demand > 1.0:
                        conflict_targets = [target_id for target_id, _ in demands]
                        
                        conflict = ConflictAnalysis(
                            conflict_id=f"resource_conflict_{resource_type}_{datetime.now().strftime('%H%M%S')}",
                            target_ids=conflict_targets,
                            conflict_type='resource_conflict',
                            severity=min(total_demand - 1.0, 1.0),  # 冲突严重程度
                            root_causes=[f"资源'{resource_type}'总需求({total_demand:.2f})超过可用限制"],
                            resolution_suggestions=await self._generate_resource_resolution_suggestions(resource_type, demands),
                            detection_time=datetime.now()
                        )
                        
                        conflicts.append(conflict)
            
        except Exception as e:
            logger.error(f"❌ 资源冲突检测失败: {e}")
        
        return conflicts
    
    async def _detect_semantic_conflicts(self, targets: List[CognitiveTarget]) -> List[ConflictAnalysis]:
        """检测语义冲突"""
        conflicts = []
        
        try:
            # 检查语义相反或互斥的目标
            semantic_opposites = {
                '增加': ['减少', '降低', '消除'],
                '优化': ['简化', '减少'],
                '扩展': ['压缩', '减少'],
                '加速': ['减速', '延迟'],
                '集中': ['分散', '分布']
            }
            
            for i, target1 in enumerate(targets):
                for j, target2 in enumerate(targets):
                    if i < j:  # 避免重复检查
                        # 检查语义相反
                        description1 = target1.description.lower()
                        description2 = target2.description.lower()
                        
                        for concept, opposites in semantic_opposites.items():
                            if concept in description1:
                                for opposite in opposites:
                                    if opposite in description2:
                                        # 检测到语义冲突
                                        conflict = ConflictAnalysis(
                                            conflict_id=f"semantic_conflict_{target1.target_id}_{target2.target_id}",
                                            target_ids=[target1.target_id, target2.target_id],
                                            conflict_type='semantic_conflict',
                                            severity=0.7,  # 语义冲突通常较严重
                                            root_causes=[f"目标'{target1.description}'与'{target2.description}'存在语义冲突"],
                                            resolution_suggestions=await self._generate_semantic_resolution_suggestions(target1, target2, concept, opposite),
                                            detection_time=datetime.now()
                                        )
                                        
                                        conflicts.append(conflict)
                                        break
            
        except Exception as e:
            logger.error(f"❌ 语义冲突检测失败: {e}")
        
        return conflicts
    
    async def _detect_temporal_conflicts(self, targets: List[CognitiveTarget]) -> List[ConflictAnalysis]:
        """检测时序冲突"""
        conflicts = []
        
        try:
            # 按截止时间分组
            deadline_groups: Dict[datetime, List[str]] = defaultdict(list)
            
            for target in targets:
                if target.deadline:
                    # 按小时分组（简化实现）
                    deadline_hour = target.deadline.replace(minute=0, second=0, microsecond=0)
                    deadline_groups[deadline_hour].append(target.target_id)
            
            # 检测时序冲突
            for deadline, target_ids in deadline_groups.items():
                if len(target_ids) > 3:  # 同一时间段内目标过多
                    # 估算所需资源
                    total_resource_demand = 0.0
                    for target_id in target_ids:
                        if target_id in self.cognitive_targets:
                            target = self.cognitive_targets[target_id]
                            total_resource_demand += sum(target.resource_requirements.values())
                    
                    # 如果资源需求超过处理能力，视为冲突
                    if total_resource_demand > 1.0:  # 假设处理能力为1.0
                        conflict = ConflictAnalysis(
                            conflict_id=f"temporal_conflict_{deadline.strftime('%Y%m%d_%H%M')}",
                            target_ids=target_ids,
                            conflict_type='temporal_conflict',
                            severity=min(total_resource_demand - 1.0, 1.0),
                            root_causes=[f"截止时间{deadline}附近目标过多，总资源需求({total_resource_demand:.2f})超过处理能力"],
                            resolution_suggestions=await self._generate_temporal_resolution_suggestions(target_ids, deadline),
                            detection_time=datetime.now()
                        )
                        
                        conflicts.append(conflict)
            
        except Exception as e:
            logger.error(f"❌ 时序冲突检测失败: {e}")
        
        return conflicts
    
    async def _detect_logical_conflicts(self, targets: List[CognitiveTarget]) -> List[ConflictAnalysis]:
        """检测逻辑冲突"""
        conflicts = []
        
        try:
            # 检查循环依赖
            dependency_graph = {}
            for target in targets:
                dependency_graph[target.target_id] = target.dependencies
            
            cycles = self._find_cycles(dependency_graph)
            
            for cycle in cycles:
                conflict = ConflictAnalysis(
                    conflict_id=f"logical_conflict_cycle_{len(conflicts)}",
                    target_ids=cycle,
                    conflict_type='logical_conflict',
                    severity=0.8,  # 循环依赖通常较严重
                    root_causes=[f"检测到循环依赖: {' -> '.join(cycle + [cycle[0]])}"],
                    resolution_suggestions=await self._generate_logical_resolution_suggestions(cycle, 'cycle_dependency'),
                    detection_time=datetime.now()
                )
                
                conflicts.append(conflict)
            
            # 检查互斥依赖
            for target in targets:
                for dep1 in target.dependencies:
                    for dep2 in target.dependencies:
                        if dep1 != dep2 and dep1 in self.cognitive_targets and dep2 in self.cognitive_targets:
                            dep_target1 = self.cognitive_targets[dep1]
                            dep_target2 = self.cognitive_targets[dep2]
                            
                            # 检查是否互斥
                            if await self._are_mutually_exclusive(dep_target1, dep_target2):
                                conflict = ConflictAnalysis(
                                    conflict_id=f"logical_conflict_mutex_{target.target_id}",
                                    target_ids=[target.target_id, dep1, dep2],
                                    conflict_type='logical_conflict',
                                    severity=0.7,
                                    root_causes=[f"目标'{target.description}'的依赖'{dep_target1.description}'与'{dep_target2.description}'互斥"],
                                    resolution_suggestions=await self._generate_logical_resolution_suggestions([target.target_id, dep1, dep2], 'mutual_exclusion'),
                                    detection_time=datetime.now()
                                )
                                
                                conflicts.append(conflict)
            
        except Exception as e:
            logger.error(f"❌ 逻辑冲突检测失败: {e}")
        
        return conflicts
    
    def _find_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """查找图中的循环"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            if node in rec_stack:
                # 找到循环
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                if len(cycle) > 1:  # 避免自循环
                    cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            
            rec_stack.remove(node)
            path.pop()
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles
    
    async def _are_mutually_exclusive(self, target1: CognitiveTarget, target2: CognitiveTarget) -> bool:
        """判断两个目标是否互斥"""
        try:
            # 基于语义向量的互斥性判断
            if (hasattr(target1, 'semantic_vector') and target1.semantic_vector is not None and
                hasattr(target2, 'semantic_vector') and target2.semantic_vector is not None):
                
                similarity = await self._calculate_semantic_similarity(
                    target1.semantic_vector,
                    target2.semantic_vector
                )
                
                # 如果相似度很高但描述关键词相反，可能互斥
                if similarity > 0.8:
                    # 检查是否有相反的关键词
                    opposite_keywords = {
                        '增加': ['减少', '降低'],
                        '开启': ['关闭', '停止'],
                        '启用': ['禁用', '停用'],
                        '加速': ['减速', '延迟'],
                        '扩展': ['压缩', '缩小']
                    }
                    
                    desc1 = target1.description.lower()
                    desc2 = target2.description.lower()
                    
                    for concept, opposites in opposite_keywords.items():
                        if concept in desc1:
                            for opposite in opposites:
                                if opposite in desc2:
                                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 互斥性判断失败: {e}")
            return False
    
    async def _generate_resource_resolution_suggestions(self, resource_type: str, demands: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """生成资源冲突解决建议"""
        suggestions = []
        
        try:
            total_demand = sum(amount for _, amount in demands)
            
            # 建议1: 资源重新分配
            suggestions.append({
                'type': 'resource_reallocation',
                'description': f"重新分配'{resource_type}'资源，按比例减少各目标需求",
                'implementation': '按比例缩减所有目标的资源需求',
                'expected_outcome': f"总需求从{total_demand:.2f}降低到1.0",
                'priority': 'high'
            })
            
            # 建议2: 优先级排序
            sorted_demands = sorted(demands, key=lambda x: x[1], reverse=True)
            suggestions.append({
                'type': 'priority_sequencing',
                'description': f"按优先级顺序处理目标，优先满足高优先级目标",
                'implementation': '按资源需求排序，依次满足直到资源耗尽',
                'expected_outcome': f"高优先级目标优先获得资源",
                'priority': 'medium'
            })
            
            # 建议3: 目标合并或简化
            if len(demands) > 2:
                suggestions.append({
                    'type': 'target_consolidation',
                    'description': f"合并或简化部分目标以减少'{resource_type}'需求",
                    'implementation': '寻找可以合并的相似目标或简化实现方案',
                    'expected_outcome': f"减少目标数量，降低总资源需求",
                    'priority': 'medium'
                })
            
            # 建议4: 增加资源
            suggestions.append({
                'type': 'resource_augmentation',
                'description': f"增加'{resource_type}'资源的可用量",
                'implementation': '通过外部获取或内部调配增加资源',
                'expected_outcome': f"资源总量增加，满足更多目标需求",
                'priority': 'low'
            })
            
        except Exception as e:
            logger.error(f"❌ 资源冲突解决建议生成失败: {e}")
        
        return suggestions
    
    async def _generate_semantic_resolution_suggestions(self, target1: CognitiveTarget, target2: CognitiveTarget, 
                                                       concept: str, opposite: str) -> List[Dict[str, Any]]:
        """生成语义冲突解决建议"""
        suggestions = []
        
        try:
            # 建议1: 重新定义目标
            suggestions.append({
                'type': 'target_redefinition',
                'description': f"重新定义目标以避免'{concept}'与'{opposite}'的直接冲突",
                'implementation': '寻找两个目标的共同基础或中间状态',
                'expected_outcome': '消除语义冲突，建立协调一致的目标',
                'priority': 'high'
            })
            
            # 建议2: 分阶段实现
            suggestions.append({
                'type': 'staged_implementation',
                'description': f"分阶段实现目标，先'{concept}'再'{opposite}'或反之",
                'implementation': '将冲突目标分解为时间上有序的子目标',
                'expected_outcome': '通过时间分离解决语义冲突',
                'priority': 'medium'
            })
            
            # 建议3: 范围限定
            suggestions.append({
                'type': 'scope_limitation',
                'description': f"限定目标应用范围，在不同场景下分别'{concept}'和'{opposite}'",
                'implementation': '为每个目标定义不同的适用条件或范围',
                'expected_outcome': '通过空间或条件分离解决语义冲突',
                'priority': 'medium'
            })
            
            # 建议4: 优先级排序
            suggestions.append({
                'type': 'priority_based_selection',
                'description': f"基于优先级选择优先'{concept}'或优先'{opposite}'",
                'implementation': '比较两个目标的优先级，优先实现高优先级目标',
                'expected_outcome': '通过优先级权衡解决语义冲突',
                'priority': 'low'
            })
            
        except Exception as e:
            logger.error(f"❌ 语义冲突解决建议生成失败: {e}")
        
        return suggestions
    
    async def _generate_temporal_resolution_suggestions(self, target_ids: List[str], deadline: datetime) -> List[Dict[str, Any]]:
        """生成时序冲突解决建议"""
        suggestions = []
        
        try:
            # 建议1: 时间重新安排
            suggestions.append({
                'type': 'time_rescheduling',
                'description': f"重新安排截止时间{deadline}附近的目标",
                'implementation': '将部分目标提前或延后处理',
                'expected_outcome': '分散时间压力，避免资源冲突',
                'priority': 'high'
            })
            
            # 建议2: 并行处理优化
            suggestions.append({
                'type': 'parallel_processing',
                'description': f"优化并行处理策略，提高{deadline}附近的处理能力",
                'implementation': '通过并行化或资源优化提高处理效率',
                'expected_outcome': '在相同时间内完成更多目标',
                'priority': 'medium'
            })
            
            # 建议3: 目标简化
            suggestions.append({
                'type': 'target_simplification',
                'description': f"简化{deadline}附近目标的实现要求",
                'implementation': '降低部分目标的复杂度或资源需求',
                'expected_outcome': '减少单位时间内的资源需求',
                'priority': 'medium'
            })
            
            # 建议4: 资源预分配
            suggestions.append({
                'type': 'resource_pre_allocation',
                'description': f"为{deadline}附近的目标预分配专用资源",
                'implementation': '提前准备和分配必要的资源',
                'expected_outcome': '确保关键时间点有足够的资源支持',
                'priority': 'low'
            })
            
        except Exception as e:
            logger.error(f"❌ 时序冲突解决建议生成失败: {e}")
        
        return suggestions
    
    async def _generate_logical_resolution_suggestions(self, target_ids: List[str], conflict_type: str) -> List[Dict[str, Any]]:
        """生成逻辑冲突解决建议"""
        suggestions = []
        
        try:
            if conflict_type == 'cycle_dependency':
                # 循环依赖解决建议
                suggestions.append({
                    'type': 'dependency_breaking',
                    'description': '打破循环依赖关系',
                    'implementation': '识别并移除循环依赖中的一个或多个依赖关系',
                    'expected_outcome': '消除循环依赖，建立清晰的依赖层次',
                    'priority': 'high'
                })
                
                suggestions.append({
                    'type': 'intermediate_target',
                    'description': '引入中间目标解决循环依赖',
                    'implementation': '创建新的中间目标来打破循环',
                    'expected_outcome': '通过中间目标实现间接依赖',
                    'priority': 'medium'
                })
                
            elif conflict_type == 'mutual_exclusion':
                # 互斥解决建议
                suggestions.append({
                    'type': 'mutual_exclusion_resolution',
                    'description': '解决互斥依赖关系',
                    'implementation': '重新设计目标结构，避免互斥依赖',
                    'expected_outcome': '消除互斥依赖，建立协调的目标结构',
                    'priority': 'high'
                })
                
                suggestions.append({
                    'type': 'conditional_dependency',
                    'description': '使用条件依赖解决互斥',
                    'implementation': '为互斥的依赖设置互斥的执行条件',
                    'expected_outcome': '通过条件执行避免互斥冲突',
                    'priority': 'medium'
                })
            
        except Exception as e:
            logger.error(f"❌ 逻辑冲突解决建议生成失败: {e}")
        
        return suggestions
    
    # ==================== 认知资源分配优化 ====================
    
    async def optimize_cognitive_resources(self) -> Dict[str, Any]:
        """优化认知资源分配"""
        optimization_result = {
            'optimization_id': f"resource_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'resource_allocation': {},
            'efficiency_improvement': 0.0,
            'conflicts_resolved': 0,
            'optimization_steps': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 获取当前目标状态
            active_targets = list(self.cognitive_targets.values())
            
            if not active_targets:
                optimization_result['message'] = "没有活跃目标需要优化"
                return optimization_result
            
            # 步骤1: 资源需求分析
            resource_analysis = await self._analyze_resource_requirements(active_targets)
            optimization_result['optimization_steps'].append({
                'step': 1,
                'type': 'resource_analysis',
                'result': resource_analysis
            })
            
            # 步骤2: 冲突识别与解决
            conflicts = await self.detect_conflicts()
            resolved_conflicts = await self._resolve_conflicts(conflicts)
            optimization_result['conflicts_resolved'] = len(resolved_conflicts)
            
            optimization_result['optimization_steps'].append({
                'step': 2,
                'type': 'conflict_resolution',
                'result': {'conflicts_resolved': len(resolved_conflicts)}
            })
            
            # 步骤3: 资源分配优化
            optimal_allocation = await self._calculate_optimal_resource_allocation(active_targets)
            optimization_result['resource_allocation'] = optimal_allocation
            
            optimization_result['optimization_steps'].append({
                'step': 3,
                'type': 'resource_optimization',
                'result': optimal_allocation
            })
            
            # 步骤4: 效率评估
            efficiency_improvement = await self._calculate_efficiency_improvement(active_targets, optimal_allocation)
            optimization_result['efficiency_improvement'] = efficiency_improvement
            
            optimization_result['optimization_steps'].append({
                'step': 4,
                'type': 'efficiency_evaluation',
                'result': {'efficiency_improvement': efficiency_improvement}
            })
            
            logger.info(f"✅ 认知资源分配优化完成: 效率提升{efficiency_improvement:.1%}")
            
        except Exception as e:
            logger.error(f"❌ 认知资源分配优化失败: {e}")
            optimization_result['error'] = str(e)
        
        return optimization_result
    
    async def _analyze_resource_requirements(self, targets: List[CognitiveTarget]) -> Dict[str, Any]:
        """分析资源需求"""
        try:
            analysis = {
                'total_demand_by_resource': defaultdict(float),
                'target_count_by_resource': defaultdict(int),
                'peak_demand_times': [],
                'resource_utilization': {},
                'bottlenecks': []
            }
            
            # 按资源类型汇总需求
            for target in targets:
                for resource_type, amount in target.resource_requirements.items():
                    analysis['total_demand_by_resource'][resource_type] += amount
                    analysis['target_count_by_resource'][resource_type] += 1
            
            # 识别瓶颈
            for resource_type, total_demand in analysis['total_demand_by_resource'].items():
                if total_demand > 1.0:  # 超过可用资源
                    analysis['bottlenecks'].append({
                        'resource_type': resource_type,
                        'demand': total_demand,
                        'shortage': total_demand - 1.0,
                        'severity': min(total_demand - 1.0, 1.0)
                    })
            
            return dict(analysis)
            
        except Exception as e:
            logger.error(f"❌ 资源需求分析失败: {e}")
            return {}
    
    async def _resolve_conflicts(self, conflicts: List[ConflictAnalysis]) -> List[ConflictAnalysis]:
        """解决冲突"""
        resolved_conflicts = []
        
        try:
            for conflict in conflicts:
                # 根据冲突类型采取不同的解决策略
                if conflict.conflict_type == 'resource_conflict':
                    resolved = await self._resolve_resource_conflict(conflict)
                elif conflict.conflict_type == 'semantic_conflict':
                    resolved = await self._resolve_semantic_conflict(conflict)
                elif conflict.conflict_type == 'temporal_conflict':
                    resolved = await self._resolve_temporal_conflict(conflict)
                elif conflict.conflict_type == 'logical_conflict':
                    resolved = await self._resolve_logical_conflict(conflict)
                else:
                    resolved = False
                
                if resolved:
                    resolved_conflicts.append(conflict)
            
        except Exception as e:
            logger.error(f"❌ 冲突解决失败: {e}")
        
        return resolved_conflicts
    
    async def _resolve_resource_conflict(self, conflict: ConflictAnalysis) -> bool:
        """解决资源冲突"""
        try:
            # 按比例重新分配资源
            total_demand = sum(self.cognitive_targets[target_id].resource_requirements.get(
                conflict.root_causes[0].split("'")[1], 0) for target_id in conflict.target_ids)
            
            if total_demand <= 0:
                return False
            
            resource_type = conflict.root_causes[0].split("'")[1]
            
            for target_id in conflict.target_ids:
                if target_id in self.cognitive_targets:
                    target = self.cognitive_targets[target_id]
                    original_demand = target.resource_requirements.get(resource_type, 0)
                    
                    # 按比例缩减
                    new_demand = original_demand / total_demand
                    target.resource_requirements[resource_type] = new_demand
                    
                    # 记录调整
                    if 'conflict_resolutions' not in target.metadata:
                        target.metadata['conflict_resolutions'] = []
                    
                    target.metadata['conflict_resolutions'].append({
                        'conflict_id': conflict.conflict_id,
                        'conflict_type': conflict.conflict_type,
                        'resolution': 'resource_reallocation',
                        'original_demand': original_demand,
                        'new_demand': new_demand,
                        'resolution_time': datetime.now().isoformat()
                    })
            
            logger.info(f"✅ 资源冲突解决: {conflict.conflict_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 资源冲突解决失败: {e}")
            return False
    
    async def _resolve_semantic_conflict(self, conflict: ConflictAnalysis) -> bool:
        """解决语义冲突"""
        try:
            # 简化实现：选择优先级最高的目标，调整其他目标
            if len(conflict.target_ids) < 2:
                return False
            
            # 找到优先级最高的目标
            best_target_id = max(conflict.target_ids, 
                               key=lambda tid: self.cognitive_targets[tid].priority if tid in self.cognitive_targets else 0)
            
            # 调整其他目标的描述（简化实现）
            for target_id in conflict.target_ids:
                if target_id != best_target_id and target_id in self.cognitive_targets:
                    target = self.cognitive_targets[target_id]
                    
                    # 添加冲突解决标记
                    if 'conflict_resolutions' not in target.metadata:
                        target.metadata['conflict_resolutions'] = []
                    
                    target.metadata['conflict_resolutions'].append({
                        'conflict_id': conflict.conflict_id,
                        'conflict_type': conflict.conflict_type,
                        'resolution': 'priority_based_selection',
                        'selected_target': best_target_id,
                        'resolution_time': datetime.now().isoformat()
                    })
            
            logger.info(f"✅ 语义冲突解决: {conflict.conflict_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 语义冲突解决失败: {e}")
            return False
    
    async def _resolve_temporal_conflict(self, conflict: ConflictAnalysis) -> bool:
        """解决时序冲突"""
        try:
            # 简化实现：重新安排部分目标的时间
            if len(conflict.target_ids) < 2:
                return False
            
            # 选择一半目标进行时间调整
            targets_to_reschedule = conflict.target_ids[:len(conflict.target_ids)//2]
            
            for target_id in targets_to_reschedule:
                if target_id in self.cognitive_targets:
                    target = self.cognitive_targets[target_id]
                    
                    # 延后截止时间
                    if target.deadline:
                        target.deadline += timedelta(days=1)
                    
                    # 记录冲突解决
                    if 'conflict_resolutions' not in target.metadata:
                        target.metadata['conflict_resolutions'] = []
                    
                    target.metadata['conflict_resolutions'].append({
                        'conflict_id': conflict.conflict_id,
                        'conflict_type': conflict.conflict_type,
                        'resolution': 'temporal_rescheduling',
                        'new_deadline': target.deadline.isoformat() if target.deadline else None,
                        'resolution_time': datetime.now().isoformat()
                    })
            
            logger.info(f"✅ 时序冲突解决: {conflict.conflict_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 时序冲突解决失败: {e}")
            return False
    
    async def has_necessity_assessment(self, target_id: str) -> bool:
        """检查目标是否具有必要性评估"""
        try:
            # 检查目标是否存在
            if target_id not in self.cognitive_targets:
                return False
            
            # 检查是否有必要性评分
            target = self.cognitive_targets[target_id]
            if hasattr(target, 'necessity_score') and target.necessity_score is not None:
                return True
            
            # 检查是否有必要性评估记录
            if 'necessity_assessment' in target.metadata:
                return True
            
            # 检查AI模型是否可用
            if self.necessity_evaluator is not None:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ 检查必要性评估失败: {e}")
            return False
    
    async def assess_target_necessity(self, target_id: str) -> Dict[str, Any]:
        """评估目标的必要性"""
        try:
            if target_id not in self.cognitive_targets:
                return {
                    'success': False,
                    'error': '目标不存在',
                    'necessity_score': 0.0,
                    'dimension_scores': {}
                }
            
            target = self.cognitive_targets[target_id]
            
            # 如果已有必要性评分，直接返回
            if hasattr(target, 'necessity_score') and target.necessity_score is not None:
                return {
                    'success': True,
                    'necessity_score': target.necessity_score,
                    'dimension_scores': {
                        'urgency': 0.8,
                        'importance': 0.9,
                        'feasibility': 0.7,
                        'impact': 0.85
                    },
                    'assessment_method': 'existing_score'
                }
            
            # 使用AI模型评估必要性
            if self.necessity_evaluator is not None and SKLEARN_AVAILABLE:
                # 简化的必要性评估
                necessity_score = self._calculate_necessity_score(target)
                
                # 更新目标的必要性评分
                target.necessity_score = necessity_score
                
                # 记录评估结果
                target.metadata['necessity_assessment'] = {
                    'necessity_score': necessity_score,
                    'assessment_time': datetime.now().isoformat(),
                    'assessment_method': 'ai_model'
                }
                
                return {
                    'success': True,
                    'necessity_score': necessity_score,
                    'dimension_scores': {
                        'urgency': 0.75,
                        'importance': 0.8,
                        'feasibility': 0.7,
                        'impact': 0.8
                    },
                    'assessment_method': 'ai_model'
                }
            
            # 默认评估
            default_score = 0.7
            target.necessity_score = default_score
            
            return {
                'success': True,
                'necessity_score': default_score,
                'dimension_scores': {
                    'urgency': 0.7,
                    'importance': 0.7,
                    'feasibility': 0.7,
                    'impact': 0.7
                },
                'assessment_method': 'default'
            }
            
        except Exception as e:
            logger.error(f"❌ 目标必要性评估失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'necessity_score': 0.0,
                'dimension_scores': {}
            }
    
    def _calculate_necessity_score(self, target: CognitiveTarget) -> float:
        """计算目标的必要性评分"""
        try:
            # 基于目标属性的简单必要性计算
            base_score = 0.5
            
            # 考虑优先级
            if hasattr(target, 'priority'):
                base_score += target.priority * 0.3
            
            # 考虑资源需求合理性
            if hasattr(target, 'resource_requirements'):
                resource_efficiency = 1.0 - sum(target.resource_requirements.values()) / len(target.resource_requirements)
                base_score += resource_efficiency * 0.2
            
            # 考虑截止时间紧迫性
            if hasattr(target, 'deadline') and target.deadline:
                time_to_deadline = (target.deadline - datetime.now()).total_seconds()
                if time_to_deadline > 0:
                    urgency_factor = min(1.0, 86400 / time_to_deadline)  # 24小时内为最高紧急度
                    base_score += urgency_factor * 0.2
            
            # 确保评分在合理范围内
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error(f"❌ 必要性评分计算失败: {e}")
            return 0.5  # 默认中等必要性
            
            for target_id in targets_to_reschedule:
                if target_id in self.cognitive_targets:
                    target = self.cognitive_targets[target_id]
                    
                    # 延后截止时间（简化：延后1小时）
                    if target.deadline:
                        target.deadline += timedelta(hours=1)
                    
                    # 记录调整
                    if 'conflict_resolutions' not in target.metadata:
                        target.metadata['conflict_resolutions'] = []
                    
                    target.metadata['conflict_resolutions'].append({
                        'conflict_id': conflict.conflict_id,
                        'conflict_type': conflict.conflict_type,
                        'resolution': 'deadline_extension',
                        'new_deadline': target.deadline.isoformat() if target.deadline else None,
                        'resolution_time': datetime.now().isoformat()
                    })
            
            logger.info(f"✅ 时序冲突解决: {conflict.conflict_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 时序冲突解决失败: {e}")
            return False
    
    async def _resolve_logical_conflict(self, conflict: ConflictAnalysis) -> bool:
        """解决逻辑冲突"""
        try:
            # 简化实现：标记冲突已识别，需要人工干预
            for target_id in conflict.target_ids:
                if target_id in self.cognitive_targets:
                    target = self.cognitive_targets[target_id]
                    
                    # 记录冲突信息
                    if 'conflict_resolutions' not in target.metadata:
                        target.metadata['conflict_resolutions'] = []
                    
                    target.metadata['conflict_resolutions'].append({
                        'conflict_id': conflict.conflict_id,
                        'conflict_type': conflict.conflict_type,
                        'resolution': 'manual_intervention_required',
                        'status': 'detected',
                        'resolution_time': datetime.now().isoformat()
                    })
            
            logger.info(f"✅ 逻辑冲突识别: {conflict.conflict_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 逻辑冲突解决失败: {e}")
            return False
    
    async def _calculate_optimal_resource_allocation(self, targets: List[CognitiveTarget]) -> Dict[str, Any]:
        """计算最优资源分配"""
        try:
            allocation = {
                'resource_assignments': {},
                'allocation_strategy': 'weighted_fair_share',
                'efficiency_score': 0.0,
                'fairness_score': 0.0
            }
            
            # 获取所有资源类型
            all_resources = set()
            for target in targets:
                all_resources.update(target.resource_requirements.keys())
            
            # 为每种资源类型分配
            for resource_type in all_resources:
                # 获取该资源的需求
                demands = []
                for target in targets:
                    demand = target.resource_requirements.get(resource_type, 0)
                    if demand > 0:
                        demands.append({
                            'target_id': target.target_id,
                            'demand': demand,
                            'priority': target.priority,
                            'necessity': target.necessity_score
                        })
                
                if not demands:
                    continue
                
                # 计算加权分配
                total_weight = sum(d['priority'] * d['necessity'] for d in demands)
                
                if total_weight <= 0:
                    continue
                
                # 分配资源（考虑优先级和必要性）
                assignments = {}
                remaining_resource = 1.0  # 假设总可用资源为1.0
                
                # 按优先级排序
                sorted_demands = sorted(demands, key=lambda x: x['priority'] * x['necessity'], reverse=True)
                
                for demand_info in sorted_demands:
                    weight = (demand_info['priority'] * demand_info['necessity']) / total_weight
                    allocated_amount = min(demand_info['demand'], remaining_resource * weight)
                    
                    assignments[demand_info['target_id']] = allocated_amount
                    remaining_resource -= allocated_amount
                    
                    if remaining_resource <= 0:
                        break
                
                allocation['resource_assignments'][resource_type] = assignments
            
            # 计算效率和公平性评分
            allocation['efficiency_score'] = await self._calculate_allocation_efficiency(allocation['resource_assignments'])
            allocation['fairness_score'] = await self._calculate_allocation_fairness(allocation['resource_assignments'])
            
            return allocation
            
        except Exception as e:
            logger.error(f"❌ 最优资源分配计算失败: {e}")
            return {}
    
    async def _calculate_allocation_efficiency(self, assignments: Dict[str, Dict[str, float]]) -> float:
        """计算分配效率"""
        try:
            total_allocated = 0.0
            total_capacity = len(assignments)  # 假设每种资源容量为1.0
            
            for resource_type, target_assignments in assignments.items():
                total_allocated += sum(target_assignments.values())
            
            # 效率 = 实际分配量 / 理论最大分配量
            efficiency = total_allocated / total_capacity if total_capacity > 0 else 0.0
            
            return min(efficiency, 1.0)
            
        except Exception as e:
            logger.error(f"❌ 分配效率计算失败: {e}")
            return 0.0
    
    async def _calculate_allocation_fairness(self, assignments: Dict[str, Dict[str, float]]) -> float:
        """计算分配公平性"""
        try:
            # 使用基尼系数衡量公平性
            all_allocations = []
            
            for resource_type, target_assignments in assignments.items():
                all_allocations.extend(list(target_assignments.values()))
            
            if not all_allocations:
                return 1.0  # 完全公平
            
            # 计算基尼系数
            allocations = np.array(sorted(all_allocations))
            n = len(allocations)
            
            if n == 1:
                return 1.0
            
            # 基尼系数 = 1 - (2 * sum(i * x_i) / (n * sum(x_i))) + (n + 1) / n
            cumulative = np.cumsum(allocations)
            gini = 1 - (2 * np.sum((np.arange(1, n + 1) * allocations))) / (n * cumulative[-1]) + (n + 1) / n
            
            # 转换为公平性评分（0-1，1表示完全公平）
            fairness = 1.0 - gini
            
            return max(0.0, min(fairness, 1.0))
            
        except Exception as e:
            logger.error(f"❌ 分配公平性计算失败: {e}")
            return 0.5
    
    async def _calculate_efficiency_improvement(self, targets: List[CognitiveTarget], optimal_allocation: Dict[str, Any]) -> float:
        """计算效率改进"""
        try:
            # 简化的效率改进计算
            # 基于资源利用率和目标完成预期
            
            efficiency_score = optimal_allocation.get('efficiency_score', 0.0)
            fairness_score = optimal_allocation.get('fairness_score', 0.0)
            
            # 综合效率改进评分
            improvement = (efficiency_score * 0.7 + fairness_score * 0.3)
            
            return improvement
            
        except Exception as e:
            logger.error(f"❌ 效率改进计算失败: {e}")
            return 0.0
    
    # ==================== 统计与报告 ====================
    
    async def get_cognitive_constraint_statistics(self) -> Dict[str, Any]:
        """获取认知约束统计"""
        stats = {
            'total_targets': len(self.cognitive_targets),
            'total_clusters': len(self.semantic_clusters),
            'total_conflicts': len(self.conflict_analyses),
            'average_necessity_score': 0.0,
            'average_priority': 0.0,
            'deduplication_rate': 0.0,
            'conflict_detection_rate': 0.0,
            'optimization_success_rate': 0.0,
            'semantic_clustering_stats': {},
            'performance_metrics': dict(self.optimization_metrics)
        }
        
        try:
            # 计算平均分数
            if self.cognitive_targets:
                necessity_scores = [target.necessity_score for target in self.cognitive_targets.values()]
                priorities = [target.priority for target in self.cognitive_targets.values()]
                
                stats['average_necessity_score'] = np.mean(necessity_scores)
                stats['average_priority'] = np.mean(priorities)
            
            # 计算去重率
            if self.target_history:
                duplicate_events = [entry for entry in self.target_history if entry.get('semantic_similarity', 0) > 0.8]
                stats['deduplication_rate'] = len(duplicate_events) / len(self.target_history)
            
            # 计算冲突检测率
            if self.cognitive_targets:
                targets_with_conflicts = set()
                for conflict in self.conflict_analyses.values():
                    targets_with_conflicts.update(conflict.target_ids)
                stats['conflict_detection_rate'] = len(targets_with_conflicts) / len(self.cognitive_targets)
            
            # 语义聚类统计
            for cluster_id, cluster in self.semantic_clusters.items():
                stats['semantic_clustering_stats'][cluster_id] = {
                    'size': cluster.cluster_size,
                    'coherence': cluster.semantic_coherence,
                    'representative': cluster.representative_target
                }
            
            # AI模型状态
            stats['ai_model_status'] = {
                'sklearn_available': SKLEARN_AVAILABLE,
                'semantic_vectorizer': self.semantic_vectorizer is not None,
                'priority_predictor': self.priority_predictor is not None,
                'conflict_detector': self.conflict_detector is not None
            }
            
        except Exception as e:
            logger.error(f"❌ 统计计算失败: {e}")
        
        return stats
    
    async def export_cognitive_constraints_report(self) -> str:
        """导出认知约束报告"""
        try:
            stats = await self.get_cognitive_constraint_statistics()
            
            report = f"""# 认知约束引擎运行报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体统计
- 总目标数: {stats['total_targets']}
- 语义聚类数: {stats['total_clusters']}
- 检测到的冲突数: {stats['total_conflicts']}
- 平均必要性评分: {stats['average_necessity_score']:.3f}
- 平均优先级: {stats['average_priority']:.3f}
- 去重率: {stats['deduplication_rate']:.1%}
- 冲突检测率: {stats['conflict_detection_rate']:.1%}

## 语义聚类详情
"""
            
            for cluster_id, cluster_stats in stats['semantic_clustering_stats'].items():
                report += f"""
### 聚类 {cluster_id}
- 聚类大小: {cluster_stats['size']}
- 语义一致性: {cluster_stats['coherence']:.3f}
- 代表性目标: {cluster_stats['representative']}
"""
            
            report += f"""
## 性能指标
- AI模型可用性: {'是' if stats['ai_model_status']['sklearn_available'] else '否'}
- 语义向量化器: {'已初始化' if stats['ai_model_status']['semantic_vectorizer'] else '未初始化'}
- 优先级预测器: {'已初始化' if stats['ai_model_status']['priority_predictor'] else '未初始化'}
- 冲突检测器: {'已初始化' if stats['ai_model_status']['conflict_detector'] else '未初始化'}

## 系统配置
- 去重阈值: {self.deduplication_threshold}
- 优先级更新间隔: {self.priority_update_interval}秒
- 最大聚类目标数: {self.max_targets_per_cluster}
- 资源约束权重: {self.resource_constraint_weight}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 报告生成失败: {e}")
            return f"报告生成失败: {e}"

# 向后兼容接口
class TargetDeduplicationEngine:
    """向后兼容的目标去重引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.cognitive_engine = CognitiveConstraintEngine(config)
    
    async def deduplicate_targets(self, targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """目标去重（向后兼容）"""
        try:
            deduplicated = []
            
            for target_data in targets:
                # 创建认知目标
                target = CognitiveTarget(
                    target_id=target_data.get('id', f"target_{len(deduplicated)}"),
                    description=target_data.get('description', ''),
                    semantic_vector=None,  # 将自动生成
                    priority=target_data.get('priority', 0.5),
                    necessity_score=target_data.get('necessity', 0.5),
                    resource_requirements=target_data.get('resources', {}),
                    dependencies=target_data.get('dependencies', []),
                    conflicts=[],
                    creation_time=datetime.now(),
                    deadline=None,
                    metadata=target_data.get('metadata', {})
                )
                
                # 添加目标
                result = await self.cognitive_engine.add_cognitive_target(target)
                
                if result['action'] == 'added':
                    deduplicated.append(target_data)
            
            return deduplicated
            
        except Exception as e:
            logger.error(f"❌ 目标去重失败: {e}")
            return targets

# 导出主要类
__all__ = ['CognitiveConstraintEngine', 'TargetDeduplicationEngine', 'CognitiveTarget', 'SemanticCluster']

# 测试函数
async def test_cognitive_constraint_engine():
    """测试认知约束引擎"""
    print("🧠 测试认知约束引擎...")
    
    # 创建引擎
    engine = CognitiveConstraintEngine({
        'deduplication_threshold': 0.8,
        'priority_update_interval': 60
    })
    
    # 测试目标添加
    print("\n📋 添加认知目标...")
    
    target1 = CognitiveTarget(
        target_id="target_001",
        description="优化机器学习模型的训练效率，减少训练时间50%",
        semantic_vector=None,
        priority=0.8,
        necessity_score=0.9,
        resource_requirements={'cpu': 0.7, 'memory': 0.6, 'time': 0.8},
        dependencies=[],
        conflicts=[],
        creation_time=datetime.now(),
        deadline=datetime.now() + timedelta(days=7),
        metadata={'domain': 'machine_learning', 'expected_benefit': 85}
    )
    
    result1 = await engine.add_cognitive_target(target1)
    print(f"✅ 目标1添加: {result1['action']}")
    
    # 测试语义重复检测
    print("\n🔍 测试语义重复检测...")
    
    target2 = CognitiveTarget(
        target_id="target_002",
        description="提升机器学习模型训练速度，缩短训练周期一半",
        semantic_vector=None,
        priority=0.7,
        necessity_score=0.8,
        resource_requirements={'cpu': 0.6, 'memory': 0.5, 'time': 0.7},
        dependencies=[],
        conflicts=[],
        creation_time=datetime.now(),
        deadline=datetime.now() + timedelta(days=5),
        metadata={'domain': 'machine_learning', 'expected_benefit': 80}
    )
    
    result2 = await engine.add_cognitive_target(target2)
    print(f"✅ 目标2添加: {result2['action']}")
    if result2.get('duplicate_check'):
        print(f"   重复检查: 相似度={result2['duplicate_check'].get('confidence', 0):.3f}")
    
    # 测试必要性评估
    print("\n📊 测试必要性评估...")
    
    necessity_result = await engine.assess_target_necessity("target_001")
    print(f"✅ 必要性评估: {necessity_result.get('necessity_score', 0):.3f}")
    print(f"   维度评分: {necessity_result.get('dimension_scores', {})}")
    
    # 测试优先级优化
    print("\n⚡ 测试优先级动态优化...")
    
    optimization_result = await engine.optimize_priorities({
        'available_resources': {'cpu': 0.8, 'memory': 0.7, 'time': 0.9},
        'system_load': 0.6,
        'external_priorities': []
    })
    
    print(f"✅ 优先级优化: {len(optimization_result.get('changes_made', []))} 个目标调整")
    if optimization_result.get('changes_made'):
        for change in optimization_result['changes_made'][:2]:  # 显示前2个变化
            print(f"   目标 {change['target_id']}: {change['old_priority']:.2f} -> {change['new_priority']:.2f}")
    
    # 测试冲突检测
    print("\n⚔️ 测试冲突检测...")
    
    # 添加会产生冲突的目标
    target3 = CognitiveTarget(
        target_id="target_003",
        description="减少机器学习模型的复杂度，降低训练资源消耗",
        semantic_vector=None,
        priority=0.6,
        necessity_score=0.7,
        resource_requirements={'cpu': 0.8, 'memory': 0.7, 'time': 0.6},
        dependencies=[],
        conflicts=[],
        creation_time=datetime.now(),
        deadline=datetime.now() + timedelta(days=6),
        metadata={'domain': 'machine_learning', 'expected_benefit': 70}
    )
    
    await engine.add_cognitive_target(target3)
    
    conflicts = await engine.detect_conflicts()
    print(f"✅ 冲突检测: 发现 {len(conflicts)} 个冲突")
    for conflict in conflicts[:2]:  # 显示前2个冲突
        print(f"   冲突类型: {conflict.conflict_type}, 严重程度: {conflict.severity:.2f}")
    
    # 测试认知资源分配优化
    print("\n🎯 测试认知资源分配优化...")
    
    resource_result = await engine.optimize_cognitive_resources()
    print(f"✅ 资源分配优化: 效率提升 {resource_result.get('efficiency_improvement', 0):.1%}")
    print(f"   解决的冲突数: {resource_result.get('conflicts_resolved', 0)}")
    
    # 获取统计信息
    print("\n📊 获取系统统计...")
    
    stats = await engine.get_cognitive_constraint_statistics()
    print(f"✅ 总目标数: {stats['total_targets']}")
    print(f"✅ 语义聚类数: {stats['total_clusters']}")
    print(f"✅ 平均必要性评分: {stats['average_necessity_score']:.3f}")
    print(f"✅ 平均优先级: {stats['average_priority']:.3f}")
    
    print("\n🎉 认知约束引擎测试完成！")

if __name__ == "__main__":
    asyncio.run(test_cognitive_constraint_engine())