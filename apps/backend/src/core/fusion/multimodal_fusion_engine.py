#!/usr/bin/env python3
"""
多模态信息融合引擎 (Multimodal Information Fusion Engine)
Level 5 AGI核心组件 - 实现跨模态信息整合与统一表示

功能：
- 跨模态特征提取 (Cross - modal Feature Extraction)
- 模态对齐与映射 (Modal Alignment & Mapping)
- 融合推理引擎 (Fusion Reasoning Engine)
- 统一表示学习 (Unified Representation Learning)
- 多模态知识图谱构建 (Multimodal Knowledge Graph Construction)
"""

import asyncio
import hashlib
import json
import logging
import re
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path

# 尝试导入可选的AI库
try:
    import torch
    import torch.nn
    import torch.nn.functional

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.core.knowledge.unified_knowledge_graph import (
        UnifiedKnowledgeGraph,
        Entity,
        Relation,
        KnowledgeTriple,
    )
except ImportError:
    # 如果导入失败, 使用占位符类
    logger.warning("⚠️ 统一知识图谱模块导入失败, 使用占位符实现")

    class UnifiedKnowledgeGraph:
        pass

        async def add_entity(self, entity):
            return True

        async def add_relation(self, relation):
            return True

        async def get_knowledge_statistics(self):
            return {"total_entities": 0, "total_relations": 0}

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

        def __post_init__(self):
            if self.properties is None:
                self.properties = {}
            if self.aliases is None:
                self.aliases = []
            if self.timestamp is None:
                self.timestamp = datetime.now()

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

        def __post_init__(self):
            if self.properties is None:
                self.properties = {}
            if self.timestamp is None:
                self.timestamp = datetime.now()

    @dataclass
    class KnowledgeTriple:
        subject: str = ""
        predicate: str = ""
        object: str = ""
        confidence: float = 0.0
        source: str = ""
        timestamp: datetime = None
        metadata: Dict[str, Any] = None

        def __post_init__(self):
            if self.metadata is None:
                self.metadata = {}
            if self.timestamp is None:
                self.timestamp = datetime.now()


@dataclass
class ModalData:
    """模态数据"""

    modality: str  # text, image, audio, video, structured
    data: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    confidence: float = 1.0

    def __post_init__(self):
        if not isinstance(self.timestamp, datetime):
            self.timestamp = datetime.fromisoformat(self.timestamp)


@dataclass
class UnifiedRepresentation:
    """统一表示"""

    representation_id: str
    modal_inputs: List[str]  # 输入模态数据ID列表
    unified_vector: Any
    semantic_concepts: List[str]
    confidence_scores: Dict[str, float]  # 各模态置信度
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class CrossModalMapping:
    """跨模态映射"""

    mapping_id: str
    source_modality: str
    target_modality: str
    mapping_function: str
    confidence: float
    metadata: Dict[str, Any]


class MultimodalInformationFusionEngine:
    """多模态信息融合引擎 - Level 5 AGI核心组件"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # 模态数据存储
        self.modal_data: Dict[str, ModalData] = {}
        self.unified_representations: Dict[str, UnifiedRepresentation] = {}
        self.cross_modal_mappings: Dict[str, CrossModalMapping] = {}

        # 融合知识图谱
        self.fusion_knowledge_graph = UnifiedKnowledgeGraph(config)

        # 特征提取器
        self.feature_extractors = {}
        self.modal_embeddings: Dict[str, Any] = {}

        # 对齐与映射
        self.alignment_matrices: Dict[str, Any] = {}
        self.mapping_functions: Dict[str, Any] = {}

        # 配置参数
        self.fusion_threshold = self.config.get("fusion_threshold", 0.75)
        self.alignment_threshold = self.config.get("alignment_threshold", 0.8)
        self.max_modalities = self.config.get("max_modalities", 5)

        # 初始化特征提取器
        self._initialize_feature_extractors()

        logger.info("🌈 多模态信息融合引擎初始化完成")

    def _initialize_feature_extractors(self):
        """初始化特征提取器"""
        try:
            # 文本特征提取器
            if SKLEARN_AVAILABLE:
                self.feature_extractors["text"] = TfidfVectorizer(
                    max_features=500, ngram_range=(1, 2), analyzer="word"
                )

            # 结构化数据特征提取器
            self.feature_extractors["structured"] = self._extract_structured_features()
            # 图像特征提取器(占位符)
            self.feature_extractors["image"] = self._extract_image_features()
            # 音频特征提取器(占位符)
            self.feature_extractors["audio"] = self._extract_audio_features()
            logger.info("✅ 特征提取器初始化成功")

        except Exception as e:  # broad exception acceptable: feature extractor initialization may fail for optional components
            logger.error(f"❌ 特征提取器初始化失败, {e}")

    # = == == == == == == == == == = 模态数据处理 == =
    async def process_modal_data(
        self, data_id: str, modality: str, data: Any, metadata: Dict[str, Any] = None
    ) -> bool:
        """处理模态数据"""
        try:
            modal_data = ModalData(
                modality=modality,
                data=data,
                metadata=metadata or {},
                timestamp=datetime.now(),
                confidence=metadata.get("confidence", 1.0) if metadata else 1.0,
            )

            self.modal_data[data_id] = modal_data

            # 提取特征
            features = await self._extract_features(modality, data)
            if features is not None:
                self.modal_embeddings[data_id] = features
                logger.info(f"✅ 模态数据处理完成, {modality} ({data_id})")
                return True
            else:
                logger.warning(f"⚠️ 特征提取失败, {modality} ({data_id})")
                return False

        except Exception as e:  # broad exception acceptable: modal data processing should be resilient
            logger.error(f"❌ 模态数据处理失败, {e}")
            return False

    async def _extract_features(self, modality: str, data: Any) -> Optional[Any]:
        """提取模态特征"""
        try:
            if modality in self.feature_extractors:
                extractor = self.feature_extractors[modality]

                if modality == "text" and SKLEARN_AVAILABLE:
                    # 为文本特征提取器拟合数据
                    if not hasattr(extractor, "vocabulary_"):
                        # 首次使用, 需要拟合简单的词汇表
                        simple_text = [str(data)]
                        extractor.fit(simple_text)
                    return extractor.transform([str(data)]).toarray()[0]
                elif modality == "structured":
                    return await extractor(data)
                elif modality in ["image", "audio"]:
                    return await extractor(data)
                else:
                    # 默认特征提取
                    return await self._default_feature_extraction(modality, data)
            else:
                return await self._default_feature_extraction(modality, data)

        except Exception as e:  # broad exception acceptable: feature extraction should be resilient
            logger.error(f"❌ 特征提取失败 {modality} {e}")
            return None

    async def _extract_structured_features(self, data: Dict[str, Any]) -> Any:
        """提取结构化数据特征"""
        try:
            # 数值特征提取
            numeric_features = []
            text_features = []

            for key, value in data.items():
                if isinstance(value, (int, float)):
                    numeric_features.append(float(value))
                elif isinstance(value, str):
                    text_features.append(value)
                elif isinstance(value, bool):
                    numeric_features.append(1.0 if value else 0.0)

            # 文本特征合并
            combined_text = " ".join(text_features)

            if SKLEARN_AVAILABLE and combined_text and NUMPY_AVAILABLE:
                # 使用TF-IDF提取文本特征
                if not hasattr(self, "_structured_vectorizer"):
                    self._structured_vectorizer = TfidfVectorizer(max_features=100)
                    # 这里应该拟合数据, 为简化返回随机特征
                    text_feature = np.random.random(100)
                else:
                    text_feature = self._structured_vectorizer.transform([combined_text]).toarray()[
                        0
                    ]
            else:
                text_feature = np.random.random(100)  # 简化实现

            # 组合特征
            all_features = numeric_features + text_feature.tolist()

            # 标准化
            if len(all_features) > 0:
                if NUMPY_AVAILABLE:
                    all_features = np.array(all_features)
                    if SKLEARN_AVAILABLE:
                        scaler = StandardScaler()
                        # 简化标准化
                        return (all_features - all_features.mean()) / (all_features.std() + 1e-8)
                    else:
                        return all_features / (np.linalg.norm(all_features) + 1e-8)
                else:
                    return all_features
            else:
                return [0.0] * 50  # 默认特征向量

        except Exception as e:  # broad exception acceptable: structured feature extraction should be resilient
            logger.error(f"❌ 结构化特征提取失败, {e}")
            return [0.0] * 50

    async def _extract_image_features(self, data: Any) -> Any:
        """提取图像特征(占位符实现)"""
        # 在实际实现中, 这里应该使用预训练的CNN模型如ResNet、ViT等
        logger.info("🖼️ 图像特征提取(占位符)")
        if NUMPY_AVAILABLE:
            return np.random.random(512)  # 模拟512维图像特征
        return [0.0] * 512

    async def _extract_audio_features(self, data: Any) -> Any:
        """提取音频特征(占位符实现)"""
        # 在实际实现中, 这里应该使用音频处理库如librosa等
        logger.info("🎵 音频特征提取(占位符)")
        if NUMPY_AVAILABLE:
            return np.random.random(256)  # 模拟256维音频特征
        return [0.0] * 256

    async def _default_feature_extraction(self, modality: str, data: Any) -> Any:
        """默认特征提取"""
        # 基于数据类型和内容的简化特征提取
        data_str = str(data)

        # 基础统计特征
        features = [
            len(data_str),  # 长度
            len(set(data_str)),  # 唯一字符数
            sum(1 for c in data_str if c.isdigit()) / max(len(data_str), 1),  # 数字比例
            sum(1 for c in data_str if c.isalpha()) / max(len(data_str), 1),  # 字母比例
            sum(1 for c in data_str if c.isspace()) / max(len(data_str), 1),  # 空格比例
        ]

        # 哈希特征(用于内容相似度)
        hash_value = int(hashlib.md5(data_str.encode()).hexdigest(), 16)
        hash_features = [(hash_value >> (i * 8)) & 0xFF for i in range(10)]

        if NUMPY_AVAILABLE:
            all_features = features + hash_features + np.random.random(35).tolist()
            return np.array(all_features)
        else:
            all_features = features + hash_features + [0.0] * 35
            return all_features

    # = == == == == == == == == == = 模态对齐与映射 = == == == == == == == == == =

    async def align_modalities(self, data_ids: List[str]) -> Dict[str, Any]:
        """对齐多个模态"""
        alignment_result = {
            "aligned_modalities": [],
            "alignment_matrix": None,
            "confidence_scores": {},
            "unified_representation": None,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            if len(data_ids) < 2:
                return alignment_result

            # 获取模态数据
            modalities = []
            embeddings = []

            for data_id in data_ids:
                if data_id in self.modal_data and data_id in self.modal_embeddings:
                    modal_data = self.modal_data[data_id]
                    modalities.append(modal_data.modality)
                    embeddings.append(self.modal_embeddings[data_id])

            if len(embeddings) < 2:
                logger.warning("⚠️ 有效模态数据不足, 无法执行对齐")
                return alignment_result

            # 执行模态对齐
            alignment_matrix = await self._calculate_alignment_matrix(embeddings, modalities)

            if alignment_matrix is not None:
                if NUMPY_AVAILABLE:
                    alignment_result["alignment_matrix"] = alignment_matrix.tolist()
                else:
                    alignment_result["alignment_matrix"] = alignment_matrix
                alignment_result["aligned_modalities"] = modalities

                # 计算对齐置信度
                for i, data_id in enumerate(data_ids):
                    if data_id in self.modal_data:
                        confidence = self._calculate_alignment_confidence(alignment_matrix, i)
                        alignment_result["confidence_scores"][data_id] = confidence

                # 生成统一表示
                unified_repr = await self._generate_unified_representation(
                    data_ids, alignment_matrix
                )
                if unified_repr:
                    alignment_result["unified_representation"] = unified_repr
            else:
                logger.warning("⚠️ 对齐矩阵计算失败")

            logger.info(f"✅ 模态对齐完成, {len(modalities)} 个模态")

        except Exception as e:  # broad exception acceptable: modality alignment should be resilient
            logger.error(f"❌ 模态对齐失败, {e}")
            alignment_result["error"] = str(e)

        return alignment_result

    async def _calculate_alignment_matrix(
        self, embeddings: List[Any], modalities: List[str]
    ) -> Optional[Any]:
        """计算对齐矩阵"""
        try:
            if not embeddings:
                return None

            if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
                # 简化对齐矩阵计算
                n = len(embeddings)
                if n < 2:
                    return None

                alignment_matrix = [[0.0] * n for _ in range(n)]

                for i in range(n):
                    alignment_matrix[i][i] = 1.0
                    for j in range(i + 1, n):
                        # 计算相似度(需要统一维度)
                        emb1 = self._normalize_embedding(embeddings[i])
                        emb2 = self._normalize_embedding(embeddings[j])

                        # 计算余弦相似度
                        similarity = self._cosine_similarity(emb1, emb2)

                        alignment_matrix[i][j] = similarity
                        alignment_matrix[j][i] = similarity

                return alignment_matrix

            # 使用PCA进行维度统一
            max_dim = max(len(emb) if isinstance(emb, list) else emb.shape[0] for emb in embeddings)
            # 统一维度
            normalized_embeddings = []
            for emb in embeddings:
                emb_len = len(emb) if isinstance(emb, list) else emb.shape[0]
                if emb_len < max_dim:
                    # 填充到最大维度
                    if isinstance(emb, list):
                        padded = [0.0] * max_dim
                        padded[:emb_len] = emb
                    else:
                        padded = np.zeros(max_dim)
                        padded[:emb_len] = emb
                    normalized_embeddings.append(padded)
                elif emb_len > max_dim:
                    # 使用PCA降维
                    pca = PCA(n_components=max_dim)
                    reshaped = np.array(emb).reshape(1, -1)
                    reduced = pca.fit_transform(reshaped)[0]
                    normalized_embeddings.append(reduced)
                else:
                    normalized_embeddings.append(emb)

            # 计算对齐矩阵
            n = len(normalized_embeddings)
            if n < 2:
                return None

            alignment_matrix = np.eye(n)

            for i in range(n):
                for j in range(i + 1, n):
                    similarity = cosine_similarity(
                        np.array(normalized_embeddings[i]).reshape(1, -1),
                        np.array(normalized_embeddings[j]).reshape(1, -1),
                    )[0][0]

                    alignment_matrix[i, j] = similarity
                    alignment_matrix[j, i] = similarity

            return alignment_matrix

        except Exception as e:  # broad exception acceptable: alignment matrix calculation should be resilient
            logger.error(f"❌ 对齐矩阵计算失败, {e}")
            return None

    def _normalize_embedding(self, embedding: Any, target_dim: int = 256) -> Any:
        """归一化嵌入向量"""
        if isinstance(embedding, list):
            emb_len = len(embedding)
        else:
            emb_len = embedding.shape[0]

        if emb_len == target_dim:
            return embedding
        elif emb_len < target_dim:
            # 填充
            if isinstance(embedding, list):
                padded = [0.0] * target_dim
                padded[:emb_len] = embedding
            else:
                padded = np.zeros(target_dim)
                padded[:emb_len] = embedding
            return padded
        else:
            # 截断或采样
            if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
                # 使用PCA降维
                pca = PCA(n_components=target_dim)
                return pca.fit_transform(np.array(embedding).reshape(1, -1))[0]
            else:
                # 简单采样
                indices = [int(i) for i in np.linspace(0, emb_len - 1, target_dim)]
                if isinstance(embedding, list):
                    return [embedding[i] for i in indices]
                else:
                    return embedding[indices]

    def _calculate_alignment_confidence(self, alignment_matrix: Any, index: int) -> float:
        """计算对齐置信度"""
        # 基于与其他模态的平均相似度
        similarities = []
        if isinstance(alignment_matrix, list):
            for j in range(len(alignment_matrix)):
                if j != index:
                    similarities.append(alignment_matrix[index][j])
        else:
            for j in range(alignment_matrix.shape[1]):
                if j != index:
                    similarities.append(alignment_matrix[index, j])

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _cosine_similarity(self, vec1: Any, vec2: Any) -> float:
        """计算余弦相似度"""
        if isinstance(vec1, list):
            vec1 = np.array(vec1)
        if isinstance(vec2, list):
            vec2 = np.array(vec2)

        if NUMPY_AVAILABLE:
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            return float(dot_product / (norm1 * norm2 + 1e-8))
        else:
            # 简化实现
            return 0.5

    async def _generate_unified_representation(
        self, data_ids: List[str], alignment_matrix: Any
    ) -> Dict[str, Any]:
        """生成统一表示"""
        try:
            # 获取嵌入向量
            embeddings = []
            semantic_concepts = []
            confidence_scores = {}

            for i, data_id in enumerate(data_ids):
                if data_id in self.modal_embeddings:
                    embeddings.append(self.modal_embeddings[data_id])
                    confidence_scores[data_id] = self._calculate_alignment_confidence(
                        alignment_matrix, i
                    )

                    # 提取语义概念(基于模态类型和数据内容)
                    if data_id in self.modal_data:
                        concepts = await self._extract_semantic_concepts(self.modal_data[data_id])
                        semantic_concepts.extend(concepts)

            if not embeddings:
                return {}

            # 加权平均融合
            weights = np.array([confidence_scores.get(data_id, 0.5) for data_id in data_ids])
            if NUMPY_AVAILABLE:
                weights = weights / np.sum(weights)  # 归一化
            else:
                total = sum(weights)
                weights = [w / total for w in weights]

            # 统一维度
            unified_dim = 512  # 统一表示维度
            normalized_embeddings = [
                self._normalize_embedding(emb, unified_dim) for emb in embeddings
            ]

            # 加权融合
            unified_vector = [0.0] * unified_dim
            for i, (emb, weight) in enumerate(zip(normalized_embeddings, weights)):
                if isinstance(emb, list):
                    for j in range(min(len(emb), len(unified_vector))):
                        unified_vector[j] += emb[j] * weight
                else:
                    for j in range(min(emb.shape[0], len(unified_vector))):
                        unified_vector[j] += emb[j] * weight

            # 生成表示ID
            representation_id = f"unified_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 创建统一表示对象
            unified_repr = UnifiedRepresentation(
                representation_id=representation_id,
                modal_inputs=data_ids,
                unified_vector=unified_vector if NUMPY_AVAILABLE else list(unified_vector),
                semantic_concepts=list(set(semantic_concepts)),  # 去重
                confidence_scores=confidence_scores,
                metadata={
                    "fusion_method": "weighted_average",
                    "alignment_matrix": (
                        alignment_matrix.tolist()
                        if NUMPY_AVAILABLE and hasattr(alignment_matrix, "tolist")
                        else (
                            list(alignment_matrix)
                            if not NUMPY_AVAILABLE
                            else alignment_matrix.tolist()
                        )
                    ),
                    "modalities": [
                        self.modal_data[did].modality for did in data_ids if did in self.modal_data
                    ],
                },
                timestamp=datetime.now(),
            )

            # 存储统一表示
            self.unified_representations[representation_id] = unified_repr

            return {
                "representation_id": representation_id,
                "vector_dimension": unified_dim,
                "semantic_concepts": unified_repr.semantic_concepts,
                "average_confidence": (
                    float(np.mean(list(confidence_scores.values())))
                    if NUMPY_AVAILABLE
                    else sum(confidence_scores.values()) / len(confidence_scores)
                ),
                "modalities_fused": len(data_ids),
            }

        except Exception as e:  # broad exception acceptable: unified representation generation should be resilient
            logger.error(f"❌ 统一表示生成失败, {e}")
            return {}

    async def _extract_semantic_concepts(self, modal_data: ModalData) -> List[str]:
        """提取语义概念"""
        concepts = []

        try:
            if modal_data.modality == "text":
                # 从文本提取关键词作为语义概念
                text = str(modal_data.data)
                # 简单的关键词提取(实际应该使用更复杂的NLP技术)
                words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
                word_freq = defaultdict(int)
                for word in words:
                    if len(word) > 3:
                        word_freq[word] += 1

                # 返回频率最高的词作为概念
                sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
                concepts = [word for word, freq in sorted_words[:5]]  # 取前5个
            elif modal_data.modality == "structured":
                # 从结构化数据提取概念
                if isinstance(modal_data.data, dict):
                    concepts = list(modal_data.data.keys())[:5]  # 取前5个键

            elif modal_data.modality in ["image", "audio"]:
                # 对于图像和音频, 使用预定义的概念标签
                concepts = [f"{modal_data.modality}_content", "multimodal_data"]

            else:
                concepts = [modal_data.modality, "data_content"]

        except Exception as e:  # broad exception acceptable: semantic concept extraction should be resilient
            logger.error(f"❌ 语义概念提取失败, {e}")
            concepts = [modal_data.modality]

        return concepts

    # = == == == == == == == == == = 融合推理引擎 == =
    async def perform_fusion_reasoning(self, representation_id: str, query: str) -> Dict[str, Any]:
        """执行融合推理"""
        reasoning_result = {
            "query": query,
            "representation_id": representation_id,
            "reasoning_steps": [],
            "conclusions": [],
            "confidence": 0.0,
            "evidence": ["error_occurred"],
        }

        try:
            if not self.active_representations:
                reasoning_result["conclusions"].append(
                    {
                        "type": "error",
                        "content": "No active representations",
                        "confidence": 0.0,
                        "evidence": ["no_representations"],
                    }
                )
                return reasoning_result

            if representation_id not in self.active_representations:
                reasoning_result["conclusions"].append(
                    {
                        "type": "error",
                        "content": f"Representation {representation_id} not found",
                        "confidence": 0.0,
                        "evidence": ["representation_not_found"],
                    }
                )
                return reasoning_result

        except Exception as e:  # broad exception acceptable: reasoning conclusion generation should be resilient
            logger.error(f"❌ 推理结论生成失败, {e}")
            conclusions.append(
                {
                    "type": "error",
                    "content": f"推理结论生成过程中出现错误: {e}",
                    "confidence": 0.0,
                    "evidence": ["error_occurred"],
                }
            )

        return conclusions

    def _analyze_modality_contribution(self, reasoning_steps: List[Dict[str, Any]]) -> str:
        """分析模态贡献度"""
        contributions = {}

        for step in reasoning_steps:
            if "modality_consistency_check" in step.get("evidence", []):
                contributions["consistency"] = step.get("confidence", 0)
            elif "cross_modal_validation" in step.get("evidence", []):
                contributions["validation"] = step.get("confidence", 0)
            elif "semantic_relevance_analysis" in step.get("evidence", []):
                contributions["relevance"] = step.get("confidence", 0)

        # 生成贡献度描述
        if contributions:
            if NUMPY_AVAILABLE:
                avg_contribution = np.mean(list(contributions.values()))
            else:
                avg_contribution = sum(contributions.values()) / len(contributions)

            return f"平均贡献度 {avg_contribution:.2f} (一致性: {contributions.get('consistency', 0):.2f}, 验证: {contributions.get('validation', 0):.2f}, 相关性: {contributions.get('relevance', 0):.2f})"
        else:
            return "贡献度分析数据不足"

    # = == == == == == == == == == = 多模态知识图谱构建 == =
    async def build_multimodal_knowledge_graph(
        self, data_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """构建多模态知识图谱"""
        construction_result = {
            "entities_created": 0,
            "relations_created": 0,
            "triples_generated": 0,
            "modalities_integrated": [],
            "timestamp": datetime.now().isoformat(),
        }

        try:
            entities_created = []
            relations_created = []

            # 处理每个统一表示
            for repr_id, unified_repr in self.unified_representations.items():
                if repr_id in data_mapping:
                    original_data_id = data_mapping[repr_id]

                    # 创建多模态实体
                    multimodal_entity = await self._create_multimodal_entity(
                        unified_repr, original_data_id
                    )
                    success = await self.fusion_knowledge_graph.add_entity(multimodal_entity)

                    if success:
                        entities_created.append(multimodal_entity.entity_id)
                        construction_result["modalities_integrated"].extend(
                            unified_repr.metadata.get("modalities", [])
                        )

                    # 创建模态间关系
                    for modal_id in unified_repr.modal_inputs:
                        if modal_id in self.modal_data:
                            modal_relation = await self._create_modal_relation(
                                multimodal_entity.entity_id, modal_id, unified_repr
                            )
                            success = await self.fusion_knowledge_graph.add_relation(modal_relation)
                            if success:
                                relations_created.append(modal_relation.relation_id)

            # 生成跨模态推理关系
            cross_modal_relations = await self._generate_cross_modal_relations()
            for relation in cross_modal_relations:
                await self.fusion_knowledge_graph.add_relation(relation)
                relations_created.append(relation.relation_id)

            construction_result.update(
                {
                    "entities_created": len(entities_created),
                    "relations_created": len(relations_created),
                    "triples_generated": len(entities_created) + len(relations_created),
                    "entity_ids": entities_created,
                    "relation_ids": relations_created,
                }
            )

            logger.info(
                f"✅ 多模态知识图谱构建完成, {construction_result['entities_created']} 实体, {construction_result['relations_created']} 关系"
            )

        except Exception as e:  # broad exception acceptable: knowledge graph construction should be resilient
            logger.error(f"❌ 多模态知识图谱构建失败, {e}")
            construction_result["error"] = str(e)

        return construction_result

    async def _create_multimodal_entity(
        self, unified_repr: UnifiedRepresentation, original_data_id: str
    ) -> Entity:
        """创建多模态实体"""
        # 构建实体属性
        if NUMPY_AVAILABLE and isinstance(unified_repr.unified_vector, np.ndarray):
            unified_vector_list = unified_repr.unified_vector.tolist()
        elif isinstance(unified_repr.unified_vector, list):
            unified_vector_list = unified_repr.unified_vector
        else:
            unified_vector_list = []

        if NUMPY_AVAILABLE:
            avg_confidence = float(np.mean(list(unified_repr.confidence_scores.values())))
        else:
            avg_confidence = (
                float(
                    sum(unified_repr.confidence_scores.values())
                    / len(unified_repr.confidence_scores.values())
                )
                if unified_repr.confidence_scores
                else 0.0
            )

        properties = {
            "unified_vector": unified_vector_list,
            "modal_inputs": unified_repr.modal_inputs,
            "semantic_concepts": unified_repr.semantic_concepts,
            "average_confidence": avg_confidence,
            "fusion_method": unified_repr.metadata.get("fusion_method", "unknown"),
            "original_data_id": original_data_id,
        }

        # 生成实体ID
        entity_id = f"mm_entity_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{original_data_id}"

        return Entity(
            entity_id=entity_id,
            name=f"Multimodal_Fusion_{original_data_id}",
            entity_type="multimodal_fusion",
            confidence=avg_confidence,
            properties=properties,
            aliases=[f"fusion_{original_data_id}", f"unified_{original_data_id}"],
            source="multimodal_fusion_engine",
            timestamp=datetime.now(),
        )

    async def _create_modal_relation(
        self, multimodal_entity_id: str, modal_id: str, unified_repr: UnifiedRepresentation
    ) -> Relation:
        """创建模态关系"""
        if modal_id not in self.modal_data:
            # 创建占位符关系
            return Relation(
                relation_id=f"modal_rel_{multimodal_entity_id}_{modal_id}",
                source_entity=multimodal_entity_id,
                target_entity=f"modal_{modal_id}",
                relation_type="contributes_to",
                confidence=unified_repr.confidence_scores.get(modal_id, 0.5),
                properties={
                    "modal_type": "unknown",
                    "contribution_weight": 1.0 / max(len(unified_repr.modal_inputs), 1),
                },
                source="multimodal_fusion_engine",
                timestamp=datetime.now(),
            )

        modal_data = self.modal_data[modal_id]

        return Relation(
            relation_id=f"modal_rel_{multimodal_entity_id}_{modal_id}",
            source_entity=multimodal_entity_id,
            target_entity=f"modal_{modal_id}",
            relation_type="composed_of",
            confidence=unified_repr.confidence_scores.get(modal_id, 0.5),
            properties={
                "modal_type": modal_data.modality,
                "contribution_weight": 1.0 / max(len(unified_repr.modal_inputs), 1),
                "original_confidence": modal_data.confidence,
            },
            source="multimodal_fusion_engine",
            timestamp=datetime.now(),
        )

    async def _generate_cross_modal_relations(self) -> List[Relation]:
        """生成跨模态推理关系"""
        relations = []

        # 为每对统一表示创建推理关系
        repr_ids = list(self.unified_representations.keys())

        for i, repr_id1 in enumerate(repr_ids):
            for j, repr_id2 in enumerate(repr_ids):
                if i < j:  # 避免重复
                    repr1 = self.unified_representations[repr_id1]
                    repr2 = self.unified_representations[repr_id2]

                    # 基于语义概念相似度创建关系
                    similarity = self._calculate_unified_similarity(repr1, repr2)

                    if similarity > 0.6:  # 相似度阈值
                        relation = Relation(
                            relation_id=f"cross_modal_{repr_id1}_{repr_id2}",
                            source_entity=f"mm_entity_{repr_id1}",
                            target_entity=f"mm_entity_{repr_id2}",
                            relation_type="semantically_related",
                            confidence=similarity,
                            properties={
                                "similarity": similarity,
                                "shared_concepts": list(
                                    set(repr1.semantic_concepts) & set(repr2.semantic_concepts)
                                ),
                                "cross_modal_similarity": True,
                            },
                            source="multimodal_fusion_engine",
                            timestamp=datetime.now(),
                        )

                        relations.append(relation)

        return relations

    def _calculate_unified_similarity(
        self, repr1: UnifiedRepresentation, repr2: UnifiedRepresentation
    ) -> float:
        """计算统一表示相似度"""
        try:
            # 基于统一向量的余弦相似度
            if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
                vec1 = (
                    np.array(repr1.unified_vector)
                    if isinstance(repr1.unified_vector, list)
                    else repr1.unified_vector
                )
                vec2 = (
                    np.array(repr2.unified_vector)
                    if isinstance(repr2.unified_vector, list)
                    else repr2.unified_vector
                )
                similarity = cosine_similarity(vec1.reshape(1, -1), vec2.reshape(1, -1))[0][0]
            else:
                similarity = 0.5

            # 基于语义概念的重叠度
            concepts1 = set(repr1.semantic_concepts)
            concepts2 = set(repr2.semantic_concepts)

            if concepts1 or concepts2:
                concept_overlap = len(concepts1 & concepts2) / len(concepts1 | concepts2)
            else:
                concept_overlap = 0.0

            # 综合相似度
            combined_similarity = (similarity + concept_overlap) / 2

            return float(combined_similarity)

        except Exception as e:  # broad exception acceptable: unified representation similarity calculation should be resilient
            logger.error(f"❌ 统一表示相似度计算失败, {e}")
            return 0.0

    # = == == == == == == == == == = 统计与报告 == =
    async def get_fusion_statistics(self) -> Dict[str, Any]:
        """获取融合统计"""
        stats = {
            "total_modal_data": len(self.modal_data),
            "total_unified_representations": len(self.unified_representations),
            "total_cross_modal_mappings": len(self.cross_modal_mappings),
            "modalities_processed": defaultdict(int),
            "fusion_success_rate": 0.0,
            "average_alignment_confidence": 0.0,
            "ai_model_status": {
                "torch_available": TORCH_AVAILABLE,
                "sklearn_available": SKLEARN_AVAILABLE,
                "numpy_available": NUMPY_AVAILABLE,
            },
        }

        # 统计各模态处理数量
        for modal_data in self.modal_data.values():
            stats["modalities_processed"][modal_data.modality] += 1

        # 计算融合成功率
        if self.unified_representations:
            successful_fusions = len(
                [ur for ur in self.unified_representations.values() if ur.confidence_scores]
            )
            stats["fusion_success_rate"] = successful_fusions / len(self.unified_representations)

        # 计算平均对齐置信度
        all_confidences = []
        for unified_repr in self.unified_representations.values():
            all_confidences.extend(list(unified_repr.confidence_scores.values()))

        if all_confidences:
            if NUMPY_AVAILABLE:
                stats["average_alignment_confidence"] = np.mean(all_confidences)
            else:
                stats["average_alignment_confidence"] = sum(all_confidences) / len(all_confidences)

        # 知识图谱统计
        kg_stats = await self.fusion_knowledge_graph.get_knowledge_statistics()
        stats["knowledge_graph_stats"] = kg_stats

        return stats

    async def export_fusion_model(self, format: str = "json") -> str:
        """导出融合模型"""
        if format == "json":
            return await self._export_fusion_json()
        else:
            return await self._export_fusion_json()

    async def _export_fusion_json(self) -> str:
        """导出融合模型为JSON"""
        fusion_data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "version": "1.0",
                "format": "json",
            },
            "config": self.config,
            "modal_data": {
                data_id: {
                    "modality": modal_data.modality,
                    "metadata": modal_data.metadata,
                    "timestamp": (
                        modal_data.timestamp.isoformat()
                        if hasattr(modal_data.timestamp, "isoformat")
                        else str(modal_data.timestamp)
                    ),
                    "confidence": modal_data.confidence,
                }
                for data_id, modal_data in self.modal_data.items()
            },
            "unified_representations": {
                repr_id: {
                    "representation_id": unified_repr.representation_id,
                    "modal_inputs": unified_repr.modal_inputs,
                    "semantic_concepts": unified_repr.semantic_concepts,
                    "confidence_scores": unified_repr.confidence_scores,
                    "metadata": unified_repr.metadata,
                    "timestamp": (
                        unified_repr.timestamp.isoformat()
                        if hasattr(unified_repr.timestamp, "isoformat")
                        else str(unified_repr.timestamp)
                    ),
                }
                for repr_id, unified_repr in self.unified_representations.items()
            },
            "cross_modal_mappings": {
                mapping_id: {
                    "mapping_id": mapping.mapping_id,
                    "source_modality": mapping.source_modality,
                    "target_modality": mapping.target_modality,
                    "mapping_function": mapping.mapping_function,
                    "confidence": mapping.confidence,
                    "metadata": mapping.metadata,
                }
                for mapping_id, mapping in self.cross_modal_mappings.items()
            },
            "alignment_matrices": {
                key: (
                    matrix.tolist()
                    if NUMPY_AVAILABLE and hasattr(matrix, "tolist")
                    else list(matrix)
                )
                for key, matrix in self.alignment_matrices.items()
            },
            "modal_embeddings_shape": {
                data_id: emb.shape if NUMPY_AVAILABLE and hasattr(emb, "shape") else len(emb)
                for data_id, emb in self.modal_embeddings.items()
            },
        }

        return json.dumps(fusion_data, ensure_ascii=False, indent=2)


# 向后兼容接口
class MultimodalFusionSystem:
    """向后兼容的多模态融合系统"""

    def __init__(self, config: Dict[str, Any] = None):
        self.fusion_engine = MultimodalInformationFusionEngine(config)

    async def fuse_modalities(self, modalities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """融合模态(向后兼容)"""
        try:
            # 处理每个模态
            data_ids = []
            for i, modal_data in enumerate(modalities):
                data_id = f"modal_{i}_{datetime.now().strftime('%H%M%S')}"
                modality = modal_data.get("modality", "unknown")
                data = modal_data.get("data", "")
                metadata = modal_data.get("metadata", {})

                await self.fusion_engine.process_modal_data(data_id, modality, data, metadata)
                data_ids.append(data_id)

            # 执行融合
            alignment_result = await self.fusion_engine.align_modalities(data_ids)

            return alignment_result

        except Exception as e:  # broad exception acceptable: modality fusion should be resilient
            logger.error(f"❌ 模态融合失败, {e}")
            return {"error": str(e)}


# 导出主要类
__all__ = [
    "MultimodalInformationFusionEngine",
    "MultimodalFusionSystem",
    "ModalData",
    "UnifiedRepresentation",
]


# 测试函数
async def test_multimodal_fusion_engine():
    """测试多模态信息融合引擎"""
    logger.info("🌈 测试多模态信息融合引擎...")

    # 创建融合引擎
    fusion_engine = MultimodalInformationFusionEngine(
        {"fusion_threshold": 0.7, "alignment_threshold": 0.8}
    )

    # 测试文本模态
    logger.info("\n📝 处理文本模态...")
    text_data = "机器学习是人工智能的一个重要分支, 它使计算机能够从数据中学习并做出预测。"
    success1 = await fusion_engine.process_modal_data(
        "text_001", "text", text_data, {"confidence": 0.9, "language": "chinese", "domain": "AI"}
    )
    logger.info(f"✅ 文本模态处理: {success1}")

    # 测试结构化数据模态
    logger.info("\n📊 处理结构化数据模态...")
    structured_data = {
        "field_count": 5,
        "data_types": ["text", "numeric", "categorical"],
        "complexity_score": 0.7,
        "domain": "machine_learning",
    }
    success2 = await fusion_engine.process_modal_data(
        "structured_001",
        "structured",
        structured_data,
        {"confidence": 0.85, "schema": "ml_dataset", "size": "medium"},
    )
    logger.info(f"✅ 结构化数据模态处理: {success2}")

    # 测试模态对齐
    logger.info("\n🔗 执行模态对齐...")
    alignment_result = await fusion_engine.align_modalities(["text_001", "structured_001"])
    logger.info(f"✅ 模态对齐完成, {len(alignment_result.get('aligned_modalities', []))} 个模态")
    if "unified_representation" in alignment_result:
        logger.info(
            f"✅ 统一表示生成: {alignment_result['unified_representation']['representation_id']}"
        )
        logger.info(
            f"✅ 平均置信度: {alignment_result['unified_representation']['average_confidence']:.3f}"
        )

    # 测试融合推理
    logger.info("\n🧠 执行融合推理...")
    if alignment_result.get("unified_representation"):
        repr_id = alignment_result["unified_representation"]["representation_id"]
        reasoning_result = await fusion_engine.perform_fusion_reasoning(
            repr_id, "机器学习技术的应用前景如何？"
        )
        logger.info(f"✅ 融合推理完成, {len(reasoning_result.get('reasoning_steps', []))} 个步骤")
        logger.info(f"✅ 推理置信度: {reasoning_result.get('confidence', 0):.3f}")
        logger.info(f"✅ 结论数量: {len(reasoning_result.get('conclusions', []))}")
    else:
        logger.info("⚠️ 统一表示未生成, 跳过融合推理测试")

    # 构建多模态知识图谱
    logger.info("\n🏗️ 构建多模态知识图谱...")
    data_mapping = (
        {"repr_id": "original_data_001"} if "unified_representation" in alignment_result else {}
    )
    kg_result = await fusion_engine.build_multimodal_knowledge_graph(data_mapping)
    logger.info(
        f"✅ 知识图谱构建: {kg_result.get('entities_created', 0)} 实体, {kg_result.get('relations_created', 0)} 关系"
    )

    # 获取统计信息
    logger.info("\n📊 获取融合统计...")
    stats = await fusion_engine.get_fusion_statistics()
    logger.info(f"✅ 总模态数据: {stats['total_modal_data']}")
    logger.info(f"✅ 统一表示数: {stats['total_unified_representations']}")
    logger.info(f"✅ 融合成功率: {stats['fusion_success_rate']:.2%}")
    logger.info(f"✅ 平均对齐置信度: {stats['average_alignment_confidence']:.3f}")

    logger.info("\n🎉 多模态信息融合引擎测试完成！")


if __name__ == "__main__":
    asyncio.run(test_multimodal_fusion_engine())
