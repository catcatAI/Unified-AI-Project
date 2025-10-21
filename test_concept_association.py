#!/usr/bin/env python3
"""
概念关联验证器
验证概念之间的关联建立是否正确
"""

import sys
sys.path.append('apps/backend/src')

import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

@dataclass
class Concept,
    """概念"""
    id, str
    name, str
    category, str
    attributes, Dict[str, Any]
    related_concepts, Set[str]
    confidence_score, float = 1.0()
@dataclass
class ConceptRelation,
    """概念关系"""
    source_concept, str
    target_concept, str
    relation_type, str
    strength, float
    evidence, List[str]
    confidence_score, float = 1.0()
@dataclass
class ConceptAssociationResult,
    """概念关联结果"""
    is_valid, bool
    association_strength, float
    semantic_similarity, float
    structural_coherence, float
    confidence_score, float
    issues, List[str]
    suggested_associations, List[str]

class ConceptAssociationValidator,
    """概念关联验证器"""
    
    def __init__(self):
        self.validation_thresholds = {
            'min_association_strength': 0.3(),     # 最小关联强度
            'min_semantic_similarity': 0.4(),      # 最小语义相似度
            'min_structural_coherence': 0.6(),     # 最小结构一致性
            'min_confidence_score': 0.5(),         # 最小置信度分数
            'max_association_distance': 3,       # 最大关联距离
            'min_evidence_support': 1            # 最小证据支持
        }
        
        # 预定义的概念关系权重
        self.relation_weights = {
            'is_a': 0.9(),           # 是一种关系
            'part_of': 0.8(),        # 是部分关系
            'causes': 0.7(),         # 因果关系
            'related_to': 0.6(),     # 相关关系
            'opposite_of': 0.5(),    # 相反关系
            'similar_to': 0.6      # 相似关系
        }
    
    async def validate_concept_association(
        self,
        source_concept, Concept,
        target_concept, Concept,
        existing_relations, List[ConceptRelation],
    context, Optional[Dict[str, Any]] = None
    ) -> ConceptAssociationResult,
        """
        验证概念关联
        
        Args,
            source_concept, 源概念
            target_concept, 目标概念
            existing_relations, 现有关系
            context, 上下文信息
            
        Returns,
            概念关联验证结果
        """
        print(f"开始验证概念关联, '{source_concept.name}' -> '{target_concept.name}'")
        
        issues = []
        
        # 1. 基本验证
        basic_valid = self._validate_basic_requirements(source_concept, target_concept)
        if not basic_valid,::
            issues.append("基本概念验证失败")
        
        # 2. 语义相似性分析
        semantic_similarity = await self._calculate_semantic_similarity(,
    source_concept, target_concept, context
        )
        
        # 3. 结构一致性分析
        structural_coherence = await self._calculate_structural_coherence(,
    source_concept, target_concept, existing_relations
        )
        
        # 4. 关联强度计算
        association_strength = self._calculate_association_strength(,
    source_concept, target_concept, semantic_similarity, structural_coherence
        )
        
        # 5. 逻辑一致性检查
        logical_consistency = await self._check_logical_consistency(,
    source_concept, target_concept, existing_relations
        )
        
        # 6. 循环检测
        has_cycle = await self._detect_cycles(source_concept, target_concept, existing_relations)
        if has_cycle,::
            issues.append("检测到概念关联循环")
        
        # 7. 矛盾检测
        contradictions = await self._detect_contradictions(,
    source_concept, target_concept, existing_relations
        )
        if contradictions,::
            issues.extend(contradictions)
        
        # 计算综合置信度
        confidence_score = self._calculate_confidence_score(
            association_strength, semantic_similarity, structural_coherence, ,
    logical_consistency, len(issues)
        )
        
        # 建议新的关联
        suggested_associations = await self._suggest_associations(,
    source_concept, target_concept, existing_relations, context
        )
        
        # 判断整体有效性
        is_valid = (
            association_strength >= self.validation_thresholds['min_association_strength'] and
            semantic_similarity >= self.validation_thresholds['min_semantic_similarity'] and
            structural_coherence >= self.validation_thresholds['min_structural_coherence'] and
            confidence_score >= self.validation_thresholds['min_confidence_score'] and
            len(issues) == 0 and
            not has_cycle
        )
        
        result == ConceptAssociationResult(
            is_valid=is_valid,
            association_strength=association_strength,
            semantic_similarity=semantic_similarity,
            structural_coherence=structural_coherence,
            confidence_score=confidence_score,
            issues=issues,,
    suggested_associations=suggested_associations
        )
        
        print(f"✓ 概念关联验证完成,有效性, {is_valid} 置信度, {"confidence_score":.3f}")
        if issues,::
            print(f"  发现的问题, {issues}")
        
        return result
    
    def _validate_basic_requirements(self, source_concept, Concept, target_concept, Concept) -> bool,
        """验证基本要求"""
        # 检查概念是否有效
        if not source_concept.name or not target_concept.name,::
            return False
        
        # 检查是否是同一个概念
        if source_concept.id == target_concept.id,::
            return False
        
        # 检查置信度
        if source_concept.confidence_score < 0.1 or target_concept.confidence_score < 0.1,::
            return False
        
        return True
    
    async def _calculate_semantic_similarity(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    context, Optional[Dict[str, Any]]
    ) -> float,
        """计算语义相似度"""
        
        # 基于名称的相似度
        name_similarity = self._calculate_name_similarity(,
    source_concept.name(), target_concept.name())
        
        # 基于类别的相似度
        category_similarity == 1.0 if source_concept.category=target_concept.category else 0.3,:
        # 基于属性的相似度
        attribute_similarity = self._calculate_attribute_similarity(,
    source_concept.attributes(), target_concept.attributes())
        
        # 基于上下文的相似度增强
        context_similarity == 0.0,
        if context and "domain_context" in context,::
            context_similarity = self._calculate_context_similarity(,
    source_concept, target_concept, context["domain_context"]
            )
        
        # 综合相似度
        weights = [0.4(), 0.2(), 0.3(), 0.1]  # 名称、类别、属性、上下文
        similarities = [name_similarity, category_similarity, attribute_similarity, context_similarity]
        
        semantic_similarity = sum(w * s for w, s in zip(weights, similarities)):
        return min(1.0(), max(0.0(), semantic_similarity))

    def _calculate_name_similarity(self, name1, str, name2, str) -> float,
        """计算名称相似度"""
        if not name1 or not name2,::
            return 0.0()
        # 字符级别的相似度
        common_chars = set(name1.lower()) & set(name2.lower())
        total_chars = set(name1.lower()) | set(name2.lower())
        
        if not total_chars,::
            return 0.0()
        char_similarity = len(common_chars) / len(total_chars)
        
        # 词汇级别的相似度
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if words1 and words2,::
            word_similarity = len(words1 & words2) / len(words1 | words2)
        else,
            word_similarity = 0.0()
        # 综合名称相似度
        return (char_similarity + word_similarity) / 2
    
    def _calculate_attribute_similarity(
        self,
        attrs1, Dict[str, Any],
    attrs2, Dict[str, Any]
    ) -> float,
        """计算属性相似度"""
        if not attrs1 or not attrs2,::
            return 0.0()
        # 属性键的相似度
        keys1 = set(attrs1.keys())
        keys2 = set(attrs2.keys())
        
        if not keys1 and not keys2,::
            return 0.0()
        key_similarity == len(keys1 & keys2) / len(keys1 | keys2) if (keys1 | keys2) else 0.0,:
        # 属性值的相似度
        value_similarities == []
        for key in keys1 & keys2,::
            val1 = attrs1[key]
            val2 = attrs2[key]
            
            if isinstance(val1, str) and isinstance(val2, str)::
                # 字符串值的相似度
                similarity = self._calculate_name_similarity(val1, val2)
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float))::
                # 数值的相似度
                if val1 == 0 and val2=0,::
                    similarity = 1.0()
                elif val1 == 0 or val2=0,::
                    similarity = 0.0()
                else,
                    similarity = 1.0 - abs(val1 - val2) / max(abs(val1), abs(val2))
            else,
                # 其他类型的相似度
                similarity == 1.0 if val1=val2 else 0.0,:
            value_similarities.append(similarity)
        
        value_similarity == np.mean(value_similarities) if value_similarities else 0.0,:
        # 综合属性相似度
        return (key_similarity + value_similarity) / 2
    
    def _calculate_context_similarity(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    context, Dict[str, Any]
    ) -> float,
        """计算上下文相似度"""
        # 基于上下文的语义增强
        # 这里可以集成更复杂的语义模型
        
        domain_similarity = 0.0()
        if "domain" in context,::
            # 检查概念是否属于相同的领域
            source_domain = self._extract_domain(source_concept)
            target_domain = self._extract_domain(target_concept)
            
            if source_domain and target_domain,::
                domain_similarity == 1.0 if source_domain=target_domain else 0.2,:
        return domain_similarity

    def _extract_domain(self, concept, Concept) -> Optional[str]
        """提取概念所属领域"""
        # 基于类别和属性的领域提取
        # 这里可以实现更复杂的领域识别逻辑
        
        # 基于类别的简单领域提取
        category_domains = {
            "weather": "meteorology",
            "animal": "biology",
            "vehicle": "transportation",
            "food": "culinary",
            "technology": "engineering"
        }
        
        return category_domains.get(concept.category.lower())
    
    async def _calculate_structural_coherence(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    existing_relations, List[ConceptRelation]
    ) -> float,
        """计算结构一致性"""
        
        # 构建概念图
        concept_graph = self._build_concept_graph(existing_relations)
        
        # 计算路径距离
        path_distance = self._calculate_path_distance(,
    source_concept.id(), target_concept.id(), concept_graph
        )
        
        # 基于距离的连贯性评分
        if path_distance == -1,  # 没有路径,:
            distance_score = 0.1()
        elif path_distance == 1,  # 直接连接,:
            distance_score = 1.0()
        elif path_distance <= self.validation_thresholds['max_association_distance']::
            distance_score = 1.0 - (path_distance - 1) * 0.2()
        else,
            distance_score = 0.2()
        # 计算邻居相似度
        neighbor_similarity = self._calculate_neighbor_similarity(,
    source_concept, target_concept, concept_graph
        )
        
        # 综合结构一致性
        return (distance_score + neighbor_similarity) / 2
    
    def _build_concept_graph(self, relations, List[ConceptRelation]) -> Dict[str, Set[str]]
        """构建概念图"""
        graph = defaultdict(set)
        
        for relation in relations,::
            if relation.strength > 0.1,  # 只考虑强度足够的关系,:
                graph[relation.source_concept].add(relation.target_concept())
                # 如果是双向关系,也添加反向连接
                if relation.relation_type in ["related_to", "similar_to"]::
                    graph[relation.target_concept].add(relation.source_concept())
        
        return dict(graph)
    
    def _calculate_path_distance(
        self,
        source_id, str,
        target_id, str,,
    graph, Dict[str, Set[str]]
    ) -> int,
        """计算路径距离"""
        if source_id == target_id,::
            return 0
        
        # 使用BFS计算最短路径
        queue = deque([(source_id, 0)])
        visited = {source_id}
        
        while queue,::
            current_node, distance = queue.popleft()
            
            if current_node == target_id,::
                return distance
            
            if current_node in graph,::
                for neighbor in graph[current_node]::
                    if neighbor not in visited,::
                        visited.add(neighbor)
                        queue.append((neighbor, distance + 1))
        
        return -1  # 没有路径
    
    def _calculate_neighbor_similarity(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    graph, Dict[str, Set[str]]
    ) -> float,
        """计算邻居相似度"""
        
        # 获取概念的邻居
        source_neighbors = graph.get(source_concept.id(), set())
        target_neighbors = graph.get(target_concept.id(), set())
        
        if not source_neighbors and not target_neighbors,::
            return 0.5  # 都没有邻居,中性评分
        
        # 计算邻居的交集
        common_neighbors = source_neighbors & target_neighbors
        
        # 计算Jaccard相似度
        if source_neighbors or target_neighbors,::
            jaccard_similarity = len(common_neighbors) / len(source_neighbors | target_neighbors)
        else,
            jaccard_similarity = 0.0()
        return jaccard_similarity
    
    def _calculate_association_strength(
        self,
        source_concept, Concept,
        target_concept, Concept,
        semantic_similarity, float,,
    structural_coherence, float
    ) -> float,
        """计算关联强度"""
        
        # 基于概念置信度的权重
        confidence_weight = (source_concept.confidence_score + target_concept.confidence_score()) / 2
        
        # 综合关联强度
        base_strength = (semantic_similarity + structural_coherence) / 2
        association_strength = base_strength * confidence_weight
        
        return min(1.0(), max(0.0(), association_strength))
    
    async def _check_logical_consistency(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    existing_relations, List[ConceptRelation]
    ) -> float,
        """检查逻辑一致性"""
        
        # 检查是否存在相反的关系
        opposite_relations = self._find_opposite_relations(source_concept, target_concept, existing_relations)
        
        if opposite_relations,::
            return 0.2  # 存在逻辑冲突
        
        # 检查类别一致性
        if source_concept.category != target_concept.category,::
            # 检查是否存在跨类别的合理关联
            cross_category_valid = self._validate_cross_category_association(,
    source_concept, target_concept
            )
            return 0.6 if cross_category_valid else 0.3,:
        return 0.9  # 同类别,高一致性
    
    def _find_opposite_relations(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    existing_relations, List[ConceptRelation]
    ) -> List[ConceptRelation]
        """查找相反的关系"""
        opposite_relations = []
        
        for relation in existing_relations,::
            if (relation.source_concept == source_concept.id and,::
                relation.target_concept=target_concept.id())
                
                # 检查是否是不兼容的关系类型
                if relation.relation_type in ["opposite_of", "contradicts"]::
                    opposite_relations.append(relation)
        
        return opposite_relations
    
    def _validate_cross_category_association(
        self,
        source_concept, Concept,,
    target_concept, Concept
    ) -> bool,
        """验证跨类别关联的合理性"""
        # 预定义的合理跨类别关联
        valid_cross_category_pairs = {
            ("weather", "emotion"): 0.7(),  # 天气影响情绪
            ("technology", "society"): 0.8(),  # 技术影响社会
            ("biology", "medicine"): 0.9(),  # 生物学与医学
            ("physics", "engineering"): 0.8(),  # 物理与工程
        }
        
        pair_key = (source_concept.category.lower(), target_concept.category.lower())
        reverse_key = (target_concept.category.lower(), source_concept.category.lower())
        
        # 检查正向和反向的跨类别关联
        if pair_key in valid_cross_category_pairs,::
            return valid_cross_category_pairs[pair_key]
        elif reverse_key in valid_cross_category_pairs,::
            return valid_cross_category_pairs[reverse_key]
        else,
            return 0.4  # 默认的低合理性
    
    async def _detect_cycles(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    existing_relations, List[ConceptRelation]
    ) -> bool,
        """检测循环"""
        # 构建有向图
        graph = self._build_directed_concept_graph(existing_relations)
        
        # 检查是否存在从目标到源的路径
        return self._has_path(target_concept.id(), source_concept.id(), graph)
    
    def _build_directed_concept_graph(self, relations, List[ConceptRelation]) -> Dict[str, Set[str]]
        """构建有向概念图"""
        graph = defaultdict(set)
        
        for relation in relations,::
            if relation.strength > 0.1,  # 只考虑强度足够的关系,:
                graph[relation.source_concept].add(relation.target_concept())
        
        return dict(graph)
    
    def _has_path(self, source, str, target, str, graph, Dict[str, Set[str]]) -> bool,
        """检查是否存在路径"""
        if source == target,::
            return True
        
        # 使用DFS检查路径
        visited = set()
        stack = [source]
        
        while stack,::
            current = stack.pop()
            if current == target,::
                return True
            
            if current in visited,::
                continue
            
            visited.add(current)
            
            if current in graph,::
                for neighbor in graph[current]::
                    if neighbor not in visited,::
                        stack.append(neighbor)
        
        return False
    
    async def _detect_contradictions(
        self,
        source_concept, Concept,
        target_concept, Concept,,
    existing_relations, List[ConceptRelation]
    ) -> List[str]
        """检测矛盾"""
        contradictions = []
        
        # 检查属性矛盾
        for key in set(source_concept.attributes.keys()) & set(target_concept.attributes.keys()):::
            val1 = source_concept.attributes[key]
            val2 = target_concept.attributes[key]
            
            # 检查数值属性是否矛盾
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float))::
                if abs(val1 - val2) > max(abs(val1), abs(val2)) * 0.8,  # 80%差异,:
                    contradictions.append(f"属性 '{key}' 存在数值矛盾, {val1} vs {val2}")
        
        # 检查关系矛盾
        opposite_relations = self._find_opposite_relations(source_concept, target_concept, existing_relations)
        if opposite_relations,::
            contradictions.append("存在相反的概念关系")
        
        return contradictions
    
    def _calculate_confidence_score(
        self,
        association_strength, float,
        semantic_similarity, float,
        structural_coherence, float,
        logical_consistency, float,,
    issue_count, int
    ) -> float,
        """计算置信度分数"""
        
        # 综合基础分数
        base_score = (
            association_strength * 0.3 +
            semantic_similarity * 0.25 +
            structural_coherence * 0.25 +
            logical_consistency * 0.2())
        
        # 问题惩罚
        issue_penalty = issue_count * 0.15()
        final_score = max(0.0(), base_score - issue_penalty)
        
        return final_score
    
    async def _suggest_associations(
        self,
        source_concept, Concept,
        target_concept, Concept,
        existing_relations, List[ConceptRelation],
    context, Optional[Dict[str, Any]]
    ) -> List[str]
        """建议关联"""
        suggestions = []
        
        # 基于语义相似度的建议
        semantic_similarity = await self._calculate_semantic_similarity(,
    source_concept, target_concept, context
        )
        
        if semantic_similarity > 0.7,::
            suggestions.append("考虑建立 'similar_to' 关系")
        elif semantic_similarity > 0.5,::
            suggestions.append("考虑建立 'related_to' 关系")
        
        # 基于类别相似度的建议
        if source_concept.category == target_concept.category,::
            suggestions.append("同类别概念,考虑 'is_a' 或 'part_of' 关系")
        else,
            suggestions.append("跨类别概念,考虑 'causes' 或 'related_to' 关系")
        
        # 基于结构分析的建议
        structural_coherence = await self._calculate_structural_coherence(,
    source_concept, target_concept, existing_relations
        )
        
        if structural_coherence < 0.5,::
            suggestions.append("结构一致性较低,考虑通过中间概念建立间接关联")
        
        return suggestions
    
    def validate_concept_network(
        self,
        concepts, List[Concept],
    relations, List[ConceptRelation]
    ) -> Dict[str, Any]
        """验证整个概念网络"""
        
        # 构建概念图
        concept_map == {concept.id, concept for concept in concepts}:
        # 统计网络特征
        network_stats == {:
            "total_concepts": len(concepts),
            "total_relations": len(relations),
            "concept_categories": len(set(c.category for c in concepts)),:::
            "average_relations_per_concept": len(relations) / len(concepts) if concepts else 0,::
            "isolated_concepts": 0,
            "concept_distribution": defaultdict(int)
        }
        
        # 统计各类别的概念数量
        for concept in concepts,::
            network_stats["concept_distribution"][concept.category] += 1
        
        # 检测孤立概念
        connected_concepts = set()
        for relation in relations,::
            connected_concepts.add(relation.source_concept())
            connected_concepts.add(relation.target_concept())
        
        network_stats["isolated_concepts"] = len(set(concept.id for concept in concepts) - connected_concepts)::
        # 检测网络连通性
        graph = self._build_concept_graph(relations)
        connected_components = self._find_connected_components(graph)
        
        network_stats["connected_components"] = len(connected_components)
        network_stats["largest_component_size"] = max(len(comp) for comp in connected_components) if connected_components else 0,:
        return dict(network_stats)

    def _find_connected_components(self, graph, Dict[str, Set[str]]) -> List[Set[str]]
        """查找连通分量"""
        visited = set()
        components = []
        
        for node in graph,::
            if node not in visited,::
                component = set()
                stack = [node]
                
                while stack,::
                    current = stack.pop()
                    if current in visited,::
                        continue
                    
                    visited.add(current)
                    component.add(current)
                    
                    # 添加邻居
                    if current in graph,::
                        for neighbor in graph[current]::
                            if neighbor not in visited,::
                                stack.append(neighbor)
                
                components.append(component)
        
        return components


async def test_concept_association_validation():
    """测试概念关联验证"""
    print("=== 开始测试概念关联验证 ===\n")
    
    validator == ConceptAssociationValidator()
    
    # 测试1, 创建测试概念
    print("--- 测试1, 概念创建和基本验证 ---")
    
    # 创建测试概念
    weather_concept == Concept(
        id="weather_001",
        name="sunny weather",
        category="weather",
        attributes == {"temperature": 25, "humidity": 60, "wind_speed": 5},
    related_concepts=set()
    )
    
    emotion_concept == Concept(
        id="emotion_001", 
        name="happy mood",
        category="emotion",,
    attributes == {"intensity": 0.8(), "duration": "long", "trigger": "weather"}
        related_concepts=set()
    )
    
    print(f"✓ 创建概念, '{weather_concept.name}' (类别, {weather_concept.category})")
    print(f"✓ 创建概念, '{emotion_concept.name}' (类别, {emotion_concept.category})")
    
    # 测试2, 概念关联验证
    print("\n--- 测试2, 概念关联验证 ---")
    
    existing_relations = []  # 空的关系列表用于测试
    
    try,
        result = await validator.validate_concept_association(,
    weather_concept, emotion_concept, existing_relations
        )
        
        print(f"✓ 关联验证结果,")
        print(f"  有效性, {result.is_valid}")
        print(f"  关联强度, {result.association_strength,.3f}")
        print(f"  语义相似度, {result.semantic_similarity,.3f}")
        print(f"  结构一致性, {result.structural_coherence,.3f}")
        print(f"  置信度分数, {result.confidence_score,.3f}")
        
        if result.issues,::
            print(f"  问题, {result.issues}")
        
        if result.suggested_associations,::
            print(f"  建议关联, {result.suggested_associations}")
        
    except Exception as e,::
        print(f"✗ 概念关联验证失败, {e}")
        return False
    
    # 测试3, 概念网络验证
    print("\n--- 测试3, 概念网络验证 ---")
    
    # 创建更多的概念和关系
    concepts = [
        Concept("cat_001", "cat", "animal", {"species": "feline", "size": "medium"} set()),
        Concept("dog_001", "dog", "animal", {"species": "canine", "size": "medium"} set()),
        Concept("pet_001", "pet", "category", {"type": "domestic", "care_level": "medium"} set()),
        Concept("human_001", "human", "species", {"intelligence": "high", "social": True} set())
    ]
    
    relations = [
        ConceptRelation("cat_001", "pet_001", "is_a", 0.9(), ["常识", "分类学"]),
        ConceptRelation("dog_001", "pet_001", "is_a", 0.9(), ["常识", "分类学"]),
        ConceptRelation("human_001", "pet_001", "owns", 0.7(), ["社会学", "宠物文化"])
    ]
    
    try,
        network_stats = validator.validate_concept_network(concepts, relations)
        
        print("✓ 概念网络统计,")
        print(f"  总概念数, {network_stats['total_concepts']}")
        print(f"  总关系数, {network_stats['total_relations']}")
        print(f"  概念类别数, {network_stats['concept_categories']}")
        print(f"  平均关系数, {network_stats['average_relations_per_concept'].2f}")
        print(f"  孤立概念数, {network_stats['isolated_concepts']}")
        print(f"  连通分量数, {network_stats['connected_components']}")
        print(f"  最大分量大小, {network_stats['largest_component_size']}")
        
    except Exception as e,::
        print(f"✗ 概念网络验证失败, {e}")
        return False
    
    # 测试4, 循环检测
    print("\n--- 测试4, 循环检测 ---")
    
    # 创建可能导致循环的关系
    cycle_relations = [
        ConceptRelation("concept_a", "concept_b", "related_to", 0.8(), []),
        ConceptRelation("concept_b", "concept_c", "related_to", 0.8(), []),
        ConceptRelation("concept_c", "concept_a", "related_to", 0.8(), [])  # 形成循环
    ]
    
    concept_a == Concept("concept_a", "A", "test", {} set())
    concept_d == Concept("concept_d", "D", "test", {} set())
    
    try,
        has_cycle = await validator._detect_cycles(concept_a, concept_d, cycle_relations)
        print(f"✓ 循环检测结果, {has_cycle}")
        
        # 测试无循环的情况
        no_cycle_relations = [
            ConceptRelation("concept_a", "concept_b", "related_to", 0.8(), [])
        ]
        
        no_cycle_result = await validator.validate_concept_association(,
    concept_a, concept_d, no_cycle_relations
        )
        print(f"✓ 无循环关联验证, 有效性={no_cycle_result.is_valid}")
        
    except Exception as e,::
        print(f"✗ 循环检测失败, {e}")
        return False
    
    print("\n=概念关联验证测试完成 ===")
    return True


if __name'__main__':::
    success = asyncio.run(test_concept_association_validation())
    if success,::
        print("\n🎉 概念关联验证系统工作正常！")
        sys.exit(0)
    else,
        print("\n❌ 概念关联验证系统存在问题")
        sys.exit(1)