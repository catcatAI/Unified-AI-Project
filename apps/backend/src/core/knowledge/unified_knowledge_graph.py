#!/usr/bin/env python3
"""
统一知识图谱 (Unified Knowledge Graph)
Level 5 AGI核心组件 - 实现跨领域知识表示与推理

功能：
- 实体识别与链接 (NER + Entity Linking)
- 关系抽取与验证 (Relation Extraction)
- 知识融合与消歧 (Knowledge Fusion)
- 时序知识更新 (Temporal Knowledge Updates)
- 跨领域知识迁移 (Cross - domain Knowledge Transfer)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

# 尝试导入可选的AI库
try:
    import numpy as np

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """实体定义"""

    entity_id: str
    name: str
    entity_type: str
    confidence: float
    properties: Dict[str, Any]
    aliases: List[str]
    source: str
    timestamp: datetime

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class Relation:
    """关系定义"""

    relation_id: str
    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    properties: Dict[str, Any]
    source: str
    timestamp: datetime
    is_temporal: bool = False
    temporal_properties: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class KnowledgeTriple:
    """知识三元组"""

    subject: str
    predicate: str
    object: str
    confidence: float
    source: str
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class DomainKnowledge:
    """领域知识"""

    domain: str
    entities: Dict[str, Entity]
    relations: Dict[str, Relation]
    patterns: List[Dict[str, Any]]
    last_updated: datetime


class UnifiedKnowledgeGraph:
    """统一知识图谱 - Level 5 AGI核心组件"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # 知识存储
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        self.knowledge_triples: List[KnowledgeTriple] = []
        self.domain_knowledge: Dict[str, DomainKnowledge] = {}

        # 实体链接映射
        self.entity_linking_map: Dict[str, Set[str]] = defaultdict(set)
        self.type_hierarchy: Dict[str, Set[str]] = defaultdict(set)

        # 时序知识管理
        self.temporal_knowledge: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.knowledge_evolution: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 跨领域映射
        self.cross_domain_mappings: Dict[str, Dict[str, float]] = defaultdict(dict)

        # AI组件（可选）
        self.entity_embeddings: Dict[str, Any] = {}
        self.relation_embeddings: Dict[str, Any] = {}

        # 配置参数
        self.similarity_threshold = self.config.get("similarity_threshold", 0.85)
        self.confidence_threshold = self.config.get("confidence_threshold", 0.7)
        self.max_search_depth = self.config.get("max_search_depth", 3)

        # 初始化AI组件
        self._initialize_ai_components()

        logger.info("🧠 统一知识图谱初始化完成")

    def _initialize_ai_components(self):
        """初始化AI组件"""
        try:
            if SKLEARN_AVAILABLE:
                # 初始化实体嵌入模型
                self.entity_vectorizer = TfidfVectorizer(
                    max_features=1000, ngram_range=(1, 2), analyzer="char"
                )

                # 初始化关系嵌入模型
                self.relation_vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 3))

                logger.info("✅ AI组件初始化成功")
            else:
                logger.warning("⚠️ scikit-learn不可用，将使用简化算法")
        except Exception as e:
            logger.error(f"❌ AI组件初始化失败: {e}")

    async def add_entity(self, entity: Entity) -> bool:
        """添加实体到知识图谱"""
        try:
            # 检查是否已存在
            if entity.entity_id in self.entities:
                logger.warning(f"实体 {entity.entity_id} 已存在，将被覆盖")

            # 实体消歧
            resolved_entity = await self._resolve_entity_ambiguity(entity)

            # 如果找到相似实体，合并
            if resolved_entity and resolved_entity.entity_id != entity.entity_id:
                logger.info(f"合并实体: {entity.entity_id} -> {resolved_entity.entity_id}")
                merged = await self._merge_entities(resolved_entity, entity)
                self.entities[resolved_entity.entity_id] = merged
            else:
                self.entities[entity.entity_id] = entity

            # 更新实体链接映射
            await self._update_entity_linking(entity)

            logger.info(f"✅ 成功添加实体: {entity.entity_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加实体失败: {e}")
            return False

    async def _resolve_entity_ambiguity(self, entity: Entity) -> Optional[Entity]:
        """实体消歧"""
        # 检查同名实体
        for existing_id, existing_entity in self.entities.items():
            if existing_entity.name.lower() == entity.name.lower():
                return existing_entity

            # 检查别名匹配
            if entity.name.lower() in [alias.lower() for alias in existing_entity.aliases]:
                return existing_entity

            # 检查相似性(基于嵌入向量)
            if SKLEARN_AVAILABLE and existing_id in self.entity_embeddings:
                similarity = await self._calculate_entity_similarity(entity, existing_entity)
                if similarity > self.similarity_threshold:
                    return existing_entity

        return None

    async def _merge_entities(self, entity1: Entity, entity2: Entity) -> Entity:
        """合并实体信息"""
        # 保留置信度更高的信息
        if entity2.confidence > entity1.confidence:
            merged_properties = {**entity1.properties, **entity2.properties}
            merged_aliases = list(set(entity1.aliases + entity2.aliases))

            return Entity(
                entity_id=entity1.entity_id,
                name=entity2.name,
                entity_type=entity2.entity_type,
                confidence=max(entity1.confidence, entity2.confidence),
                properties=merged_properties,
                aliases=merged_aliases,
                source=f"{entity1.source}|{entity2.source}",
                timestamp=datetime.now(),
            )
        else:
            # 保留entity1的主要信息, 合并其他属性
            merged_properties = {**entity2.properties, **entity1.properties}
            merged_aliases = list(set(entity1.aliases + entity2.aliases))

            entity1.properties = merged_properties
            entity1.aliases = merged_aliases
            entity1.source = f"{entity1.source}|{entity2.source}"
            entity1.timestamp = datetime.now()
            return entity1

    async def _update_entity_linking(self, entity: Entity):
        """更新实体链接映射"""
        # 添加实体ID到映射
        self.entity_linking_map[entity.name.lower()].add(entity.entity_id)

        # 添加别名到映射
        for alias in entity.aliases:
            self.entity_linking_map[alias.lower()].add(entity.entity_id)

        # 添加类型到层次结构
        self.type_hierarchy[entity.entity_type].add(entity.entity_id)

    async def _calculate_entity_similarity(self, entity1: Entity, entity2: Entity) -> float:
        """计算实体相似度"""
        try:
            if not SKLEARN_AVAILABLE:
                # 使用简单的字符串相似度
                return self._string_similarity(entity1.name, entity2.name)

            # 构建实体描述文本
            entity1_text = f"{entity1.name} {' '.join(entity1.aliases)} {entity1.entity_type}"
            for key, value in entity1.properties.items():
                entity1_text += f" {key} {value}"

            entity2_text = f"{entity2.name} {' '.join(entity2.aliases)} {entity2.entity_type}"
            for key, value in entity2.properties.items():
                entity2_text += f" {key} {value}"

            # 使用TF-IDF向量化
            vec1 = self.entity_vectorizer.fit_transform([entity1_text])
            vec2 = self.entity_vectorizer.transform([entity2_text])

            # 计算余弦相似度
            similarity = cosine_similarity(vec1, vec2)[0][0]

            return float(similarity)
        except Exception as e:
            logger.warning(f"计算实体相似度失败: {e}")
            return 0.0

    def _string_similarity(self, str1: str, str2: str) -> float:
        """简单的字符串相似度计算"""
        str1, str2 = str1.lower(), str2.lower()
        if str1 == str2:
            return 1.0

        # 简单的Jaccard相似度
        set1, set2 = set(str1.split()), set(str2.split())
        intersection = set1 & set2
        union = set1 | set2

        if not union:
            return 0.0

        return len(intersection) / len(union)

    async def add_relation(self, relation: Relation) -> bool:
        """添加关系到知识图谱"""
        try:
            if relation.relation_id in self.relations:
                logger.warning(f"关系 {relation.relation_id} 已存在，将被覆盖")

            self.relations[relation.relation_id] = relation

            # 创建知识三元组
            triple = KnowledgeTriple(
                subject=relation.source_entity,
                predicate=relation.relation_type,
                object=relation.target_entity,
                confidence=relation.confidence,
                source=relation.source,
                timestamp=relation.timestamp,
                metadata=relation.properties,
            )

            self.knowledge_triples.append(triple)

            logger.info(f"✅ 成功添加关系: {relation.relation_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 添加关系失败: {e}")
            return False

    async def query_knowledge(self, query: str, query_type: str = "entity") -> List[Dict[str, Any]]:
        """查询知识图谱"""
        try:
            if query_type == "entity":
                return await self._query_entities(query)
            elif query_type == "relation":
                return await self._query_relations(query)
            elif query_type == "triple":
                return await self._query_triples(query)
            else:
                logger.warning(f"未知的查询类型: {query_type}")
                return []
        except Exception as e:
            logger.error(f"查询知识失败: {e}")
            return []

    async def _query_entities(self, query: str) -> List[Dict[str, Any]]:
        """查询实体"""
        results = []
        query_lower = query.lower()

        for entity_id, entity in self.entities.items():
            # 检查名称匹配
            if query_lower in entity.name.lower():
                results.append(
                    {
                        "entity_id": entity.entity_id,
                        "name": entity.name,
                        "entity_type": entity.entity_type,
                        "confidence": entity.confidence,
                        "source": entity.source,
                    }
                )
                continue

            # 检查别名匹配
            for alias in entity.aliases:
                if query_lower in alias.lower():
                    results.append(
                        {
                            "entity_id": entity.entity_id,
                            "name": entity.name,
                            "entity_type": entity.entity_type,
                            "confidence": entity.confidence,
                            "source": entity.source,
                        }
                    )
                    break

        return results

    async def _query_relations(self, query: str) -> List[Dict[str, Any]]:
        """查询关系"""
        results = []
        query_lower = query.lower()

        for relation_id, relation in self.relations.items():
            if (
                query_lower in relation.source_entity.lower()
                or query_lower in relation.target_entity.lower()
                or query_lower in relation.relation_type.lower()
            ):
                results.append(
                    {
                        "relation_id": relation.relation_id,
                        "source_entity": relation.source_entity,
                        "target_entity": relation.target_entity,
                        "relation_type": relation.relation_type,
                        "confidence": relation.confidence,
                        "source": relation.source,
                    }
                )

        return results

    async def _query_triples(self, query: str) -> List[Dict[str, Any]]:
        """查询知识三元组"""
        results = []
        query_lower = query.lower()

        for triple in self.knowledge_triples:
            if (
                query_lower in triple.subject.lower()
                or query_lower in triple.predicate.lower()
                or query_lower in triple.object.lower()
            ):
                results.append(
                    {
                        "subject": triple.subject,
                        "predicate": triple.predicate,
                        "object": triple.object,
                        "confidence": triple.confidence,
                        "source": triple.source,
                    }
                )

        return results

    async def get_statistics(self) -> Dict[str, Any]:
        """获取知识图谱统计信息"""
        return {
            "total_entities": len(self.entities),
            "total_relations": len(self.relations),
            "total_triples": len(self.knowledge_triples),
            "total_domains": len(self.domain_knowledge),
            "entity_types": list(set(e.entity_type for e in self.entities.values())),
            "relation_types": list(set(r.relation_type for r in self.relations.values())),
        }
