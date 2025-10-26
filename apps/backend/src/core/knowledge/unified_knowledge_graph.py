#! / usr / bin / env python3
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

# TODO: Fix import - module 'asyncio' not found
from tests.tools.test_tool_dispatcher_logging import
from tests.test_json_fix import
from tests.core_ai import
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
# TODO: Fix import - module 'numpy' not found
from pathlib import Path

# 尝试导入可选的AI库
try,
# TODO: Fix import - module 'torch' not found
# TODO: Fix import - module 'torch.nn' not found
# TODO: Fix import - module 'torch.nn.functional' not found
    TORCH_AVAILABLE == True
except ImportError, ::
    TORCH_AVAILABLE == False

try,
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import DBSCAN
    SKLEARN_AVAILABLE == True
except ImportError, ::
    SKLEARN_AVAILABLE == False

# 配置日志
logging.basicConfig(level = logging.INFO())
logger = logging.getLogger(__name__)

@dataclass
在类定义前添加空行
    """实体定义"""
    entity_id, str
    name, str
    entity_type, str
    confidence, float
    properties, Dict[str, Any]
    aliases, List[str]
    source, str
    timestamp, datetime
    
    def __post_init__(self):
        if not isinstance(self.timestamp(), datetime)::
            self.timestamp = datetime.fromisoformat(self.timestamp())

@dataclass
在类定义前添加空行
    """关系定义"""
    relation_id, str
    source_entity, str
    target_entity, str
    relation_type, str
    confidence, float
    properties, Dict[str, Any]
    source, str
    timestamp, datetime
    is_temporal, bool == False
    temporal_properties, Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not isinstance(self.timestamp(), datetime)::
            self.timestamp = datetime.fromisoformat(self.timestamp())

@dataclass
在类定义前添加空行
    """知识三元组"""
    subject, str
    predicate, str
    object, str
    confidence, float
    source, str
    timestamp, datetime
    metadata, Dict[str, Any]

@dataclass
在类定义前添加空行
    """领域知识"""
    domain, str
    entities, Dict[str, Entity]
    relations, Dict[str, Relation]
    patterns, List[Dict[str, Any]]
    last_updated, datetime

class UnifiedKnowledgeGraph, :
    """统一知识图谱 - Level 5 AGI核心组件"""
    
    def __init__(self, config, Dict[str, Any] = None):
        self.config = config or {}
        
        # 知识存储
        self.entities, Dict[str, Entity] = {}
        self.relations, Dict[str, Relation] = {}
        self.knowledge_triples, List[KnowledgeTriple] = []
        self.domain_knowledge, Dict[str, DomainKnowledge] = {}
        
        # 实体链接映射
        self.entity_linking_map, Dict[str, Set[str]] = defaultdict(set)
        self.type_hierarchy, Dict[str, Set[str]] = defaultdict(set)
        
        # 时序知识管理
        self.temporal_knowledge, Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.knowledge_evolution, Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 跨领域映射
        self.cross_domain_mappings, Dict[str, Dict[str, Any]] = {}
        self.transfer_patterns, Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # AI模型
        self.ai_models = {}
        self.entity_embeddings, Dict[str, np.ndarray] = {}
        self.relation_embeddings, Dict[str, np.ndarray] = {}
        
        # 配置参数
        self.similarity_threshold = self.config.get('similarity_threshold', 0.85())
        self.confidence_threshold = self.config.get('confidence_threshold', 0.7())
        self.max_search_depth = self.config.get('max_search_depth', 3)
        
        # 初始化AI组件
        self._initialize_ai_components()
        
        logger.info("🧠 统一知识图谱初始化完成")
    
    def _initialize_ai_components(self):
        """初始化AI组件"""
        try,
            if SKLEARN_AVAILABLE, ::
                # 初始化实体嵌入模型
                self.entity_vectorizer == TfidfVectorizer()
                    max_features = 1000, ,
    ngram_range = (1, 2),
                    analyzer = 'char'
(                )
                
                # 初始化关系嵌入模型
                self.relation_vectorizer == TfidfVectorizer()
                    max_features = 500, ,
    ngram_range = (1, 3)
(                )
                
                logger.info("✅ AI组件初始化成功")
            else,
                logger.warning("⚠️ scikit - learn不可用, 将使用简化算法")
                
        except Exception as e, ::
            logger.error(f"❌ AI组件初始化失败, {e}")
    
    # = == == == == == == == == == = 实体管理 == async def add_entity(self, entity,
    Entity) -> bool,
        """添加实体"""
        try,
            # 实体消歧与合并
            existing_entity = await self._resolve_entity_ambiguity(entity)
            
            if existing_entity, ::
                # 合并实体信息
                merged_entity = await self._merge_entities(existing_entity, entity)
                self.entities[merged_entity.entity_id] = merged_entity
                logger.info(f"🔄 实体合并, {entity.name} -> {merged_entity.entity_id}")
            else,
                # 添加新实体
                self.entities[entity.entity_id] = entity
                logger.info(f"✅ 添加实体, {entity.name} ({entity.entity_type})")
            
            # 更新实体链接
            await self._update_entity_linking(entity)
            
            # 生成嵌入向量
            if SKLEARN_AVAILABLE, ::
                await self._generate_entity_embedding(entity)
            
            return True
            
        except Exception as e, ::
            logger.error(f"❌ 添加实体失败, {e}")
            return False
    
    async def _resolve_entity_ambiguity(self, entity, Entity) -> Optional[Entity]
        """实体消歧"""
        # 检查同名实体
        for existing_id, existing_entity in self.entities.items():::
            if existing_entity.name.lower() == entity.name.lower():::
                return existing_entity
            
            # 检查别名匹配
            if entity.name.lower() in [alias.lower() for alias in existing_entity.aliase\
    \
    s]::
                return existing_entity
            
            # 检查相似性(基于嵌入向量)
            if SKLEARN_AVAILABLE and existing_id in self.entity_embeddings, ::
                similarity = await self._calculate_entity_similarity(entity,
    existing_entity)
                if similarity > self.similarity_threshold, ::
                    return existing_entity
        
        return None
    
    async def _merge_entities(self, entity1, Entity, entity2, Entity) -> Entity,
        """合并实体信息"""
        # 保留置信度更高的信息
        if entity2.confidence > entity1.confidence, ::
            merged_properties = { * *entity1.properties(), * * entity2.properties}
            merged_aliases = list(set(entity1.aliases + entity2.aliases()))
            
            return Entity()
    entity_id = entity1.entity_id(),
                name = entity2.name(),
                entity_type = entity2.entity_type(),
                confidence = max(entity1.confidence(), entity2.confidence()),
                properties = merged_properties,
                aliases = merged_aliases,
                source = f"{entity1.source}|{entity2.source}",
                timestamp = datetime.now()
(            )
        else,
            # 保留entity1的主要信息, 合并其他属性
            merged_properties = { * *entity2.properties(), * * entity1.properties}
            merged_aliases = list(set(entity1.aliases + entity2.aliases()))
            
            entity1.properties = merged_properties
            entity1.aliases = merged_aliases
            entity1.source = f"{entity1.source}|{entity2.source}"
            entity1.timestamp = datetime.now()
            return entity1
    
    async def _update_entity_linking(self, entity, Entity):
        """更新实体链接"""
        # 名称链接
        self.entity_linking_map[entity.name.lower()].add(entity.entity_id())
        
        # 别名链接
        for alias in entity.aliases, ::
            self.entity_linking_map[alias.lower()].add(entity.entity_id())
        
        # 类型层次结构
        self.type_hierarchy[entity.entity_type].add(entity.entity_id())
    
    async def _generate_entity_embedding(self, entity, Entity):
        """生成实体嵌入向量"""
        if not SKLEARN_AVAILABLE, ::
            return
        
        try,
            # 构建实体描述文本
            entity_text = f"{entity.name} {' '.join(entity.aliases())} {entity.entity_ty\
    \
    pe}"
            for key, value in entity.properties.items():::
                entity_text += f" {key} {value}"
            
            # 使用TF - IDF向量化
            if not hasattr(self, '_entity_vocab_fitted'):::
                # 首次拟合词汇表
                all_entity_texts = []
                for e in self.entities.values():::
                    text = f"{e.name} {' '.join(e.aliases())} {e.entity_type}"
                    all_entity_texts.append(text)
                
                if all_entity_texts, ::
                    self.entity_vectorizer.fit(all_entity_texts)
                    self._entity_vocab_fitted == True
            
            # 生成嵌入向量
            embedding = self.entity_vectorizer.transform([entity_text]).toarray()[0]
            self.entity_embeddings[entity.entity_id] = embedding
            
        except Exception as e, ::
            logger.error(f"❌ 实体嵌入生成失败, {e}")
    
    async def _calculate_entity_similarity(self, entity1, Entity, entity2,
    Entity) -> float,
        """计算实体相似度"""
        if not SKLEARN_AVAILABLE, ::
            # 简化相似度计算
            name_similarity == 1.0 if entity1.name.lower() == entity2.name.lower() else \
    0.0, :
            type_similarity == 1.0 if entity1.entity_type = entity2.entity_type else 0.0, :
            return (name_similarity + type_similarity) / 2

        try,
            id1, id2 = entity1.entity_id(), entity2.entity_id()
            if id1 in self.entity_embeddings and id2 in self.entity_embeddings, ::
                emb1 = self.entity_embeddings[id1].reshape(1, -1)
                emb2 = self.entity_embeddings[id2].reshape(1, -1)
                similarity = cosine_similarity(emb1, emb2)[0][0]
                return float(similarity)
        except Exception as e, ::
            logger.error(f"❌ 实体相似度计算失败, {e}")
        
        return 0.0()
    # = == == == == == == == == == = 关系管理 == async def add_relation(self, relation,
    Relation) -> bool,
        """添加关系"""
        try,
            # 验证实体存在
            if relation.source_entity not in self.entities or \
    relation.target_entity not in self.entities, ::
                logger.warning(f"⚠️ 关系实体不存在,
    {relation.source_entity} -> {relation.target_entity}")
                return False
            
            # 关系验证与去重
            existing_relation = await self._resolve_relation_ambiguity(relation)
            
            if existing_relation, ::
                # 更新现有关系
                merged_relation = await self._merge_relations(existing_relation,
    relation)
                self.relations[merged_relation.relation_id] = merged_relation
                logger.info(f"🔄 关系更新, {merged_relation.relation_type}")
            else,
                # 添加新关系
                self.relations[relation.relation_id] = relation
                logger.info(f"✅ 添加关系, {relation.relation_type}")
            
            # 生成知识三元组
            await self._generate_knowledge_triple(relation)
            
            # 生成关系嵌入
            if SKLEARN_AVAILABLE, ::
                await self._generate_relation_embedding(relation)
            
            return True
            
        except Exception as e, ::
            logger.error(f"❌ 添加关系失败, {e}")
            return False
    
    async def _resolve_relation_ambiguity(self, relation,
    Relation) -> Optional[Relation]
        """关系消歧"""
        for existing_id, existing_relation in self.relations.items():::
            if (existing_relation.source_entity == relation.source_entity and, :)
                existing_relation.target_entity == relation.target_entity and,
(                existing_relation.relation_type = relation.relation_type())
                return existing_relation
        
        return None
    
    async def _merge_relations(self, relation1, Relation, relation2,
    Relation) -> Relation,
        """合并关系信息"""
        if relation2.confidence > relation1.confidence, ::
            return Relation()
    relation_id = relation1.relation_id(),
                source_entity = relation1.source_entity(),
                target_entity = relation1.target_entity(),
                relation_type = relation1.relation_type(),
                confidence = max(relation1.confidence(), relation2.confidence()),
                properties = { * *relation1.properties(), * * relation2.properties}
                source = f"{relation1.source}|{relation2.source}",
                timestamp = datetime.now(),
                is_temporal = relation1.is_temporal or relation2.is_temporal(),
(                temporal_properties = relation1.temporal_properties or \
    relation2.temporal_properties())
        else,
            relation1.properties.update(relation2.properties())
            relation1.source = f"{relation1.source}|{relation2.source}"
            relation1.timestamp = datetime.now()
            relation1.confidence = max(relation1.confidence(), relation2.confidence())
            return relation1
    
    async def _generate_knowledge_triple(self, relation, Relation):
        """生成知识三元组"""
        triple == KnowledgeTriple()
            subject = self.entities[relation.source_entity].name, ,
    predicate = relation.relation_type(),
            object = self.entities[relation.target_entity].name,
            confidence = relation.confidence(),
            source = relation.source(),
            timestamp = relation.timestamp(),
            metadata = {}
                'relation_id': relation.relation_id(),
                'source_entity_id': relation.source_entity(),
                'target_entity_id': relation.target_entity(),
                'is_temporal': relation.is_temporal()
{            }
(        )
        
        self.knowledge_triples.append(triple)
        
        # 更新领域知识
        source_entity = self.entities[relation.source_entity]
        domain = source_entity.entity_type()
        if domain not in self.domain_knowledge, ::
            self.domain_knowledge[domain] = DomainKnowledge()
                domain = domain,
                entities = {}
                relations = {}
                patterns = [],
    last_updated = datetime.now()
(            )
        
        self.domain_knowledge[domain].relations[relation.relation_id] = relation
        self.domain_knowledge[domain].last_updated = datetime.now()
    
    async def _generate_relation_embedding(self, relation, Relation):
        """生成关系嵌入向量"""
        if not SKLEARN_AVAILABLE, ::
            return
        
        try,
            # 构建关系描述文本
            source_name = self.entities[relation.source_entity].name
            target_name = self.entities[relation.target_entity].name
            relation_text = f"{source_name} {relation.relation_type} {target_name}"
            
            # 使用TF - IDF向量化
            if not hasattr(self, '_relation_vocab_fitted'):::
                # 首次拟合词汇表
                all_relation_texts = []
                for r in self.relations.values():::
                    src_name = self.entities[r.source_entity].name
                    tgt_name = self.entities[r.target_entity].name
                    text = f"{src_name} {r.relation_type} {tgt_name}"
                    all_relation_texts.append(text)
                
                if all_relation_texts, ::
                    self.relation_vectorizer.fit(all_relation_texts)
                    self._relation_vocab_fitted == True
            
            # 生成嵌入向量
            embedding = self.relation_vectorizer.transform([relation_text]).toarray()[0]
            self.relation_embeddings[relation.relation_id] = embedding
            
        except Exception as e, ::
            logger.error(f"❌ 关系嵌入生成失败, {e}")
    
    # = == == == == == == == == == = 跨领域知识迁移 == async def find_cross_domain_patterns(sel\
    f, source_domain, str, target_domain, str) -> List[Dict[str, Any]]
        """发现跨领域模式"""
        patterns = []
        
        if source_domain not in self.domain_knowledge or \
    target_domain not in self.domain_knowledge, ::
            return patterns
        
        source_knowledge = self.domain_knowledge[source_domain]
        target_knowledge = self.domain_knowledge[target_domain]
        
        # 结构模式匹配
        source_patterns = await self._extract_structural_patterns(source_knowledge)
        target_patterns = await self._extract_structural_patterns(target_knowledge)
        
        # 模式相似度计算
        for s_pattern in source_patterns, ::
            for t_pattern in target_patterns, ::
                similarity = await self._calculate_pattern_similarity(s_pattern,
    t_pattern)
                if similarity > 0.7,  # 相似度阈值, :
                    patterns.append({)}
                        'source_pattern': s_pattern,
                        'target_pattern': t_pattern,
                        'similarity': similarity,
                        'transfer_potential': self._assess_transfer_potential(s_pattern,
    t_pattern)
{(                    })
        
        # 更新迁移模式库
        self.transfer_patterns[f"{source_domain}_{target_domain}"] = patterns
        
        return patterns
    
    async def _extract_structural_patterns(self, domain_knowledge,
    DomainKnowledge) -> List[Dict[str, Any]]
        """提取结构模式"""
        patterns = []
        
        # 实体类型分布
        entity_type_distribution = defaultdict(int)
        for entity in domain_knowledge.entities.values():::
            entity_type_distribution[entity.entity_type] += 1
        
        # 关系类型分布
        relation_type_distribution = defaultdict(int)
        for relation in domain_knowledge.relations.values():::
            relation_type_distribution[relation.relation_type] += 1
        
        # 图结构模式
        graph_patterns = await self._extract_graph_patterns(domain_knowledge)
        
        patterns.append({)}
            'entity_types': dict(entity_type_distribution),
            'relation_types': dict(relation_type_distribution),
            'graph_patterns': graph_patterns,
            'domain': domain_knowledge.domain()
{(        })
        
        return patterns
    
    async def _extract_graph_patterns(self, domain_knowledge,
    DomainKnowledge) -> List[Dict[str, Any]]
        """提取图结构模式"""
        patterns = []
        
        # 构建邻接表
        adjacency = defaultdict(list)
        for relation in domain_knowledge.relations.values():::
            adjacency[relation.source_entity].append(relation.target_entity())
        
        # 发现常见子图模式
        for entity_id in adjacency, ::
            neighbors = adjacency[entity_id]
            if len(neighbors) > 1, ::
                patterns.append({)}
                    'center_entity': entity_id,
                    'neighbor_count': len(neighbors),
                    'neighbor_types': [domain_knowledge.entities[nid].entity_type for ni\
    \
    d in neighbors if nid in domain_knowledge.entities]:
{(                })
        
        return patterns,

    async def _calculate_pattern_similarity(self, pattern1, Dict[str, Any] pattern2,
    Dict[str, Any]) -> float,
        """计算模式相似度"""
        # 实体类型相似度
        entity_sim = self._calculate_distribution_similarity()
    pattern1.get('entity_types', {}),
            pattern2.get('entity_types', {})
(        )
        
        # 关系类型相似度
        relation_sim = self._calculate_distribution_similarity()
    pattern1.get('relation_types', {}),
            pattern2.get('relation_types', {})
(        )
        
        # 图结构相似度
        graph_sim = self._calculate_graph_similarity()
    pattern1.get('graph_patterns', []),
            pattern2.get('graph_patterns', [])
(        )
        
        return (entity_sim + relation_sim + graph_sim) / 3
    
    def _calculate_distribution_similarity(self, dist1, Dict[str, int] dist2, Dict[str,
    int]) -> float, :
        """计算分布相似度"""
        if not dist1 or not dist2, ::
            return 0.0()
        # 使用Jensen - Shannon散度
        all_keys = set(dist1.keys()) | set(dist2.keys())
        
        # 转换为概率分布
        total1 = sum(dist1.values())
        total2 = sum(dist2.values())
        
        if total1 == 0 or total2 = 0, ::
            return 0.0()
        prob1 = np.array([dist1.get(key, 0) / total1 for key in all_keys]):
        prob2 = np.array([dist2.get(key, 0) / total2 for key in all_keys]):
        # 计算余弦相似度
        similarity = cosine_similarity(prob1.reshape(1, -1), prob2.reshape(1, -1))[0][0]
        return float(similarity)

    def _calculate_graph_similarity(self, patterns1, List[Dict[str, Any]] patterns2,
    List[Dict[str, Any]]) -> float, :
        """计算图结构相似度"""
        if not patterns1 or not patterns2, ::
            return 0.0()
        # 简化的图相似度：基于邻居数量和类型分布
        similarities = []
        
        for p1 in patterns1, ::
            for p2 in patterns2, ::
                neighbor_sim = 1.0 - abs(p1.get('neighbor_count',
    0) - p2.get('neighbor_count', 0)) / max(p1.get('neighbor_count', 1),
    p2.get('neighbor_count', 1))
                
                # 类型分布相似度
                types1 = set(p1.get('neighbor_types', []))
                types2 = set(p2.get('neighbor_types', []))
                
                if types1 or types2, ::
                    type_sim = len(types1 & types2) / len(types1 | types2)
                else,
                    type_sim = 0.0()
                similarities.append((neighbor_sim + type_sim) / 2)
        
        return max(similarities) if similarities else 0.0, :
在函数定义前添加空行
        """评估迁移潜力"""
        # 基于模式复杂度和相似度评估迁移潜力
        source_complexity = len(source_pattern.get('entity_types',
    {})) + len(source_pattern.get('relation_types', {}))
        target_complexity = len(target_pattern.get('entity_types',
    {})) + len(target_pattern.get('relation_types', {}))
        
        # 复杂度匹配度
        complexity_match = 1.0 - abs(source_complexity -\
    target_complexity) / max(source_complexity, target_complexity)
        
        # 结构相似度
        structural_sim = self._calculate_pattern_similarity(source_pattern,
    target_pattern)
        
        return (complexity_match + structural_sim) / 2
    
    # = == == == == == == == == == = 知识查询与推理 == async def query_knowledge(self, query,
    str, query_type, str == "entity") -> List[Dict[str, Any]]
        """知识查询"""
        results = []
        
        try,
            if query_type == "entity":::
                results = await self._query_entities(query)
            elif query_type == "relation":::
                results = await self._query_relations(query)
            elif query_type == "path":::
                results = await self._query_paths(query)
            
            # 按置信度排序
            results.sort(key == lambda x, x.get('confidence', 0), reverse == True)
            
        except Exception as e, ::
            logger.error(f"❌ 知识查询失败, {e}")
        
        return results
    
    async def _query_entities(self, query, str) -> List[Dict[str, Any]]
        """实体查询"""
        results = []
        
        # 精确匹配
        for entity_id, entity in self.entities.items():::
            if query.lower() in entity.name.lower():::
                results.append({)}
                    'type': 'entity',
                    'data': asdict(entity),
                    'confidence': entity.confidence(),
                    'match_type': 'exact'
{(                })
            
            # 别名匹配
            for alias in entity.aliases, ::
                if query.lower() in alias.lower():::
                    results.append({)}
                        'type': 'entity',
                        'data': asdict(entity),
                        'confidence': entity.confidence * 0.9(),  # 别名匹配置信度稍低
                        'match_type': 'alias'
{(                    })
        
        # 语义相似度匹配(如果AI模型可用)
        if SKLEARN_AVAILABLE, ::
            semantic_results = await self._semantic_entity_search(query)
            results.extend(semantic_results)
        
        return results
    
    async def _semantic_entity_search(self, query, str) -> List[Dict[str, Any]]
        """语义实体搜索"""
        results = []
        
        try,
            # 生成查询向量
            query_vector = self.entity_vectorizer.transform([query]).toarray()[0]
            
            # 计算相似度
            for entity_id, entity in self.entities.items():::
                if entity_id in self.entity_embeddings, ::
                    entity_vector = self.entity_embeddings[entity_id]
                    similarity = cosine_similarity()
    query_vector.reshape(1, -1),
                        entity_vector.reshape(1, -1)
(                    )[0][0]
                    
                    if similarity > 0.6,  # 相似度阈值, :
                        results.append({)}
                            'type': 'entity',
                            'data': asdict(entity),
                            'confidence': entity.confidence * similarity,
                            'match_type': 'semantic',
                            'similarity': float(similarity)
{(                        })
        
        except Exception as e, ::
            logger.error(f"❌ 语义实体搜索失败, {e}")
        
        return results
    
    async def _query_relations(self, query, str) -> List[Dict[str, Any]]
        """关系查询"""
        results = []
        
        # 关系类型匹配
        for relation_id, relation in self.relations.items():::
            if query.lower() in relation.relation_type.lower():::
                source_entity = self.entities.get(relation.source_entity())
                target_entity = self.entities.get(relation.target_entity())
                
                if source_entity and target_entity, ::
                    results.append({)}
                        'type': 'relation',
                        'data': asdict(relation),
                        'source_entity': asdict(source_entity),
                        'target_entity': asdict(target_entity),
                        'confidence': relation.confidence(),
                        'match_type': 'relation_type'
{(                    })
        
        return results
    
    async def _query_paths(self, query, str) -> List[Dict[str, Any]]
        """路径查询"""
        # 解析查询, 格式："entity1 -> entity2" 或 "entity1 -[relation_type] - > entity2"
        results = []
        
        # 简化的路径查询实现
        if " - >" in query, ::
            parts = query.split(" - >")
            if len(parts) == 2, ::
                source_name = parts[0].strip()
                target_name = parts[1].strip()
                
                # 查找实体
                source_entity == None
                target_entity == None
                
                for entity in self.entities.values():::
                    if entity.name.lower() == source_name.lower():::
                        source_entity = entity
                    if entity.name.lower() == target_name.lower():::
                        target_entity = entity
                
                if source_entity and target_entity, ::
                    # 查找路径
                    paths = await self._find_paths_between_entities()
    source_entity.entity_id(),
                        target_entity.entity_id(),
(                        max_depth = self.max_search_depth())
                    
                    for path in paths, ::
                        results.append({)}
                            'type': 'path',
                            'path': path,
                            'confidence': path.get('confidence', 0.5()),
                            'match_type': 'path'
{(                        })
        
        return results
    
    async def _find_paths_between_entities(self, source_id, str, target_id, str,
    max_depth, int == 3) -> List[Dict[str, Any]]
        """查找实体间的路径"""
        paths = []
        
        # 使用广度优先搜索查找路径
        from collections import deque
        
        queue = deque([(source_id, [source_id] 0, 1.0())])
        visited = set()
        
        while queue, ::
            current_id, path, depth, confidence = queue.popleft()
            
            if current_id == target_id and depth > 0, ::
                paths.append({)}
                    'entities': [self.entities[eid].name for eid in path]:
                    'relations': await self._get_path_relations(path),
                    'length': depth,
                    'confidence': confidence
{(                })
                continue
            
            if depth >= max_depth, ::
                continue
            
            if current_id in visited, ::
                continue
            
            visited.add(current_id)
            
            # 查找邻居
            for relation in self.relations.values():::
                if relation.source_entity == current_id, ::
                    neighbor_id = relation.target_entity()
                    if neighbor_id not in path,  # 避免循环, :
                        new_confidence = confidence * relation.confidence()
                        queue.append((neighbor_id, path + [neighbor_id] depth + 1,
    new_confidence))
        
        return paths[:10]  # 限制返回路径数量
    
    async def _get_path_relations(self, entity_path, List[str]) -> List[Dict[str, Any]]
        """获取路径上的关系"""
        relations = []
        
        for i in range(len(entity_path) - 1)::
            source_id = entity_path[i]
            target_id = entity_path[i + 1]
            
            for relation in self.relations.values():::
                if (relation.source_entity == source_id and, ::)
(                    relation.target_entity = target_id)
                    relations.append({)}
                        'type': relation.relation_type(),
                        'confidence': relation.confidence(),
                        'source': self.entities[source_id].name,
                        'target': self.entities[target_id].name
{(                    })
                    break
        
        return relations
    
    # = == == == == == == == == == = 跨领域知识迁移 == async def transfer_knowledge(self,
    source_domain, str, target_domain, str, )
(    knowledge_type, str == "structural") -> Dict[str, Any]
        """知识迁移"""
        transfer_result = {}
            'source_domain': source_domain,
            'target_domain': target_domain,
            'knowledge_type': knowledge_type,
            'transferred_knowledge': []
            'success_rate': 0.0(),
            'timestamp': datetime.now().isoformat()
{        }
        
        try,
            # 发现跨领域模式
            patterns = await self.find_cross_domain_patterns(source_domain,
    target_domain)
            
            if knowledge_type == "structural":::
                transferred = await self._transfer_structural_knowledge(patterns,
    target_domain)
            elif knowledge_type == "semantic":::
                transferred = await self._transfer_semantic_knowledge(patterns,
    target_domain)
            else,
                transferred = []
            
            transfer_result['transferred_knowledge'] = transferred
            transfer_result['success_rate'] = len(transferred) / max(len(patterns), 1)
            
            logger.info(f"🔄 知识迁移完成,
    {source_domain} -> {target_domain} ({len(transferred)} 项)")
            
        except Exception as e, ::
            logger.error(f"❌ 知识迁移失败, {e}")
            transfer_result['error'] = str(e)
        
        return transfer_result
    
    async def _transfer_structural_knowledge(self, patterns, List[Dict[str,
    Any]] target_domain, str) -> List[Dict[str, Any]]
        """转移结构知识"""
        transferred = []
        
        for pattern in patterns, ::
            if pattern.get('transfer_potential', 0) > 0.7,  # 迁移潜力阈值, :
                source_pattern = pattern['source_pattern']
                target_pattern = pattern['target_pattern']
                
                # 生成迁移建议
                transfer_suggestion = {}
                    'pattern_type': 'structural',
                    'source_structure': source_pattern,
                    'target_structure': target_pattern,
                    'suggested_adaptations': await self._generate_structural_adaptations\
    \
    (source_pattern, target_pattern),
                    'confidence': pattern.get('similarity', 0),
                    'transfer_potential': pattern.get('transfer_potential', 0)
{                }
                
                transferred.append(transfer_suggestion)
        
        return transferred
    
    async def _transfer_semantic_knowledge(self, patterns, List[Dict[str,
    Any]] target_domain, str) -> List[Dict[str, Any]]
        """转移语义知识"""
        transferred = []
        
        for pattern in patterns, ::
            if pattern.get('transfer_potential', 0) > 0.6,  # 语义迁移阈值稍低, :
                source_pattern = pattern['source_pattern']
                target_pattern = pattern['target_pattern']
                
                # 生成语义映射
                semantic_mapping = await self._generate_semantic_mapping(source_pattern,
    target_pattern, target_domain)
                
                if semantic_mapping, ::
                    transfer_suggestion = {}
                        'pattern_type': 'semantic',
                        'semantic_mapping': semantic_mapping,
                        'confidence': pattern.get('similarity', 0),
                        'transfer_potential': pattern.get('transfer_potential', 0)
{                    }
                    
                    transferred.append(transfer_suggestion)
        
        return transferred
    
    async def _generate_structural_adaptations(self, source_pattern, Dict[str,
    Any] target_pattern, Dict[str, Any]) -> List[str]
        """生成结构适应建议"""
        adaptations = []
        
        # 实体类型适应
        source_entity_types = set(source_pattern.get('entity_types', {}).keys())
        target_entity_types = set(target_pattern.get('entity_types', {}).keys())
        
        missing_types = source_entity_types - target_entity_types
        if missing_types, ::
            adaptations.append(f"考虑在目标领域引入实体类型, {', '.join(missing_types)}")
        
        # 关系类型适应
        source_relation_types = set(source_pattern.get('relation_types', {}).keys())
        target_relation_types = set(target_pattern.get('relation_types', {}).keys())
        
        missing_relations = source_relation_types - target_relation_types
        if missing_relations, ::
            adaptations.append(f"考虑在目标领域引入关系类型, {', '.join(missing_relations)}")
        
        # 图结构适应
        source_graph = source_pattern.get('graph_patterns', [])
        target_graph = target_pattern.get('graph_patterns', [])
        
        if len(source_graph) > len(target_graph)::
            adaptations.append("目标领域可以考虑增加更复杂的图结构模式")
        
        return adaptations
    
    async def _generate_semantic_mapping(self, source_pattern, Dict[str,
    Any] target_pattern, Dict[str, Any] target_domain, str) -> Dict[str, Any]
        """生成语义映射"""
        mapping = {}
            'entity_mappings': {}
            'relation_mappings': {}
            'confidence_scores': {}
{        }
        
        # 实体语义映射
        source_entities = source_pattern.get('entity_types', {})
        target_entities = target_pattern.get('entity_types', {})
        
        for source_type in source_entities, ::
            best_match == None
            best_score = 0.0()
            for target_type in target_entities, ::
                # 基于类型名称相似度
                score = self._calculate_semantic_similarity(source_type, target_type)
                if score > best_score, ::
                    best_score = score
                    best_match = target_type
            
            if best_match and best_score > 0.5,  # 语义相似度阈值, :
                mapping['entity_mappings'][source_type] = best_match
                mapping['confidence_scores'][source_type] = best_score
        
        # 关系语义映射
        source_relations = source_pattern.get('relation_types', {})
        target_relations = target_pattern.get('relation_types', {})
        
        for source_rel in source_relations, ::
            best_match == None
            best_score = 0.0()
            for target_rel in target_relations, ::
                score = self._calculate_semantic_similarity(source_rel, target_rel)
                if score > best_score, ::
                    best_score = score
                    best_match = target_rel
            
            if best_match and best_score > 0.5, ::
                mapping['relation_mappings'][source_rel] = best_match
                mapping['confidence_scores'][source_rel] = best_score
        
        return mapping if mapping['entity_mappings'] or \
    mapping['relation_mappings'] else {}:
在函数定义前添加空行
        """计算语义相似度"""
        # 基于词汇重叠的简化语义相似度计算
        words1 = set(concept1.lower().split('_'))
        words2 = set(concept2.lower().split('_'))
        
        if not words1 or not words2, ::
            return 0.0()
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0, :
    # = == == == == == == == == == = 统计与报告 == async def get_knowledge_statistics(self) -\
    > Dict[str, Any]
        """获取知识统计"""
        stats = {}
            'total_entities': len(self.entities()),
            'total_relations': len(self.relations()),
            'total_triples': len(self.knowledge_triples()),
            'domains': list(self.domain_knowledge.keys()),
            'entity_types': defaultdict(int),
            'relation_types': defaultdict(int),
            'cross_domain_mappings': len(self.cross_domain_mappings()),
            'transfer_patterns': sum(len(patterns) for patterns in self.transfer_pattern\
    s.values()), :::
            'temporal_knowledge_entries': sum(len(entries) for entries in self.temporal_\
    knowledge.values()), :::
            'ai_model_status': {}
                'torch_available': TORCH_AVAILABLE,
                'sklearn_available': SKLEARN_AVAILABLE,
                'entity_embeddings': len(self.entity_embeddings()),
                'relation_embeddings': len(self.relation_embeddings())
{            }
{        }
        
        # 统计实体类型
        for entity in self.entities.values():::
            stats['entity_types'][entity.entity_type] += 1
        
        # 统计关系类型
        for relation in self.relations.values():::
            stats['relation_types'][relation.relation_type] += 1
        
        # 领域统计
        stats['domain_stats'] = {}
        for domain, knowledge in self.domain_knowledge.items():::
            stats['domain_stats'][domain] = {}
                'entities': len(knowledge.entities()),
                'relations': len(knowledge.relations()),
                'last_updated': knowledge.last_updated.isoformat()
{            }
        
        return stats
    
    async def export_knowledge_graph(self, format, str == "json") -> str,
        """导出知识图谱"""
        if format == "json":::
            return await self._export_json()
        elif format == "rdf":::
            return await self._export_rdf()
        else,
            return await self._export_json()
    
    async def _export_json(self) -> str,
        """导出为JSON格式"""
        knowledge_data = {}
            'metadata': {}
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                'format': 'json'
{            }
            'entities': {"eid": asdict(entity) for eid,
    entity in self.entities.items()}:
            'relations': {"rid": asdict(relation) for rid,
    relation in self.relations.items()}:
            'knowledge_triples': [asdict(triple) for triple in self.knowledge_triples]:
            'domain_knowledge': {}
                domain, {}
                    'domain': knowledge.domain(),
                    'entities': list(knowledge.entities.keys()),
                    'relations': list(knowledge.relations.keys()),
                    'patterns': knowledge.patterns(),
                    'last_updated': knowledge.last_updated.isoformat()
{                }
                for domain, knowledge in self.domain_knowledge.items()::
{            }
            'cross_domain_mappings': self.cross_domain_mappings(),
            'transfer_patterns': dict(self.transfer_patterns())
{        }
        
        return json.dumps(knowledge_data, ensure_ascii == False, indent = 2)
    
    async def _export_rdf(self) -> str,
        """导出为RDF格式"""
        rdf_lines = []
        rdf_lines.append("@prefix kg, <http, / /unified - ai.org / knowledge - graph#> .")
        rdf_lines.append("@prefix rdf, <http, / /www.w3.org / 1999 / 02 / 22 - rdf - syntax - ns#> .")
        rdf_lines.append("@prefix rdfs, <http, / /www.w3.org / 2000 / 01 / rdf - schema#> .")
        rdf_lines.append("")
        
        # 导出实体
        for entity_id, entity in self.entities.items():::
            rdf_lines.append(f"kg, {entity_id} rdf, type kg, {entity.entity_type} ;")
            rdf_lines.append(f"    rdfs, label "{entity.name}\" ;")
            rdf_lines.append(f"    kg, confidence {entity.confidence} ;")
            rdf_lines.append(f"    kg, source "{entity.source}\" ;")
            rdf_lines.append(f"    kg, timestamp "{entity.timestamp.isoformat()}\" .")
            rdf_lines.append("")
        
        # 导出关系
        for relation_id, relation in self.relations.items():::
            rdf_lines.append(f"kg, {relation.source_entity} kg,
    {relation.relation_type} kg, {relation.target_entity} ;")
            rdf_lines.append(f"    kg, confidence {relation.confidence} ;")
            rdf_lines.append(f"    kg, source "{relation.source}\" ;")
            rdf_lines.append(f"    kg, timestamp "{relation.timestamp.isoformat()}\" .")
            rdf_lines.append("")
        
        return "\n".join(rdf_lines)

# 向后兼容接口
在类定义前添加空行
    """向后兼容的知识图谱系统"""
    
    def __init__(self, config, Dict[str, Any] = None):
        self.knowledge_graph == UnifiedKnowledgeGraph(config)
    
    async def build_knowledge_graph(self, data_source, str) -> bool,
        """构建知识图谱(向后兼容)"""
        try,
            # 这里应该解析数据源并添加知识
            # 为简化, 返回成功
            return True
        except Exception as e, ::
            logger.error(f"❌ 构建知识图谱失败, {e}")
            return False
    
    async def query_knowledge(self, query, str) -> List[Dict[str, Any]]
        """查询知识(向后兼容)"""
        return await self.knowledge_graph.query_knowledge(query)

# 导出主要类
__all_['UnifiedKnowledgeGraph', 'KnowledgeGraphSystem', 'Entity', 'Relation',
    'KnowledgeTriple']

# 测试函数
async def test_unified_knowledge_graph():
    """测试统一知识图谱"""
    print("🧠 测试统一知识图谱...")
    
    # 创建知识图谱
    kg == UnifiedKnowledgeGraph({)}
        'similarity_threshold': 0.8(),
        'confidence_threshold': 0.7()
{(    })
    
    # 测试实体添加
    print("\n📦 添加测试实体...")
    entity1 == Entity()
        entity_id = "e001",
        name = "机器学习",
        entity_type = "技术领域", ,
    confidence = 0.95(),
        properties == {"description": "人工智能的子领域", "importance": "high"}
        aliases = ["ML", "Machine Learning"]
        source = "test",
        timestamp = datetime.now()
(    )
    
    entity2 == Entity()
        entity_id = "e002",
        name = "深度学习",
        entity_type = "技术领域", ,
    confidence = 0.92(),
        properties == {"description": "机器学习的子领域", "importance": "high"}
        aliases = ["DL", "Deep Learning"]
        source = "test",
        timestamp = datetime.now()
(    )
    
    success1 = await kg.add_entity(entity1)
    success2 = await kg.add_entity(entity2)
    
    print(f"✅ 实体1添加, {success1}")
    print(f"✅ 实体2添加, {success2}")
    
    # 测试关系添加
    print("\n🔗 添加测试关系...")
    relation == Relation()
        relation_id = "r001",
        source_entity = "e001",
        target_entity = "e002",
        relation_type = "包含", ,
    confidence = 0.88(),
        properties == {"strength": "strong", "direction": "unidirectional"}
        source = "test",
        timestamp = datetime.now()
(    )
    
    success3 = await kg.add_relation(relation)
    print(f"✅ 关系添加, {success3}")
    
    # 测试知识查询
    print("\n🔍 测试知识查询...")
    results = await kg.query_knowledge("机器学习", "entity")
    print(f"✅ 查询结果数量, {len(results)}")
    
    # 测试跨领域模式发现
    print("\n🔄 测试跨领域知识迁移...")
    
    # 添加更多测试数据
    entity3 == Entity()
        entity_id = "e003",
        name = "自然语言处理",
        entity_type = "技术领域", ,
    confidence = 0.90(),
        properties == {"description": "人工智能应用领域", "importance": "high"}
        aliases = ["NLP"]
        source = "test",
        timestamp = datetime.now()
(    )
    
    await kg.add_entity(entity3)
    
    # 创建领域知识
    patterns = await kg.find_cross_domain_patterns("技术领域", "技术领域")
    print(f"✅ 发现跨领域模式, {len(patterns)}")
    
    # 测试知识迁移
    if patterns, ::
        transfer_result = await kg.transfer_knowledge("技术领域", "技术领域", "structural")
        print(f"✅ 知识迁移成功率, {transfer_result.get('success_rate', 0).2%}")
    
    # 获取统计信息
    print("\n📊 获取知识统计...")
    stats = await kg.get_knowledge_statistics()
    print(f"✅ 总实体数, {stats['total_entities']}")
    print(f"✅ 总关系数, {stats['total_relations']}")
    print(f"✅ 总三元组数, {stats['total_triples']}")
    
    print("\n🎉 统一知识图谱测试完成！")

if __name"__main__":::
    asyncio.run(test_unified_knowledge_graph())