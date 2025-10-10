#!/usr/bin/env python3
"""
输出验证机制
确保系统输出的质量、安全性和正确性
"""

import sys
sys.path.append('apps/backend/src')

import re
import json
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import hashlib

@dataclass
class OutputValidationResult:
    """输出验证结果"""
    is_valid: bool
    safety_score: float
    quality_score: float
    correctness_score: float
    semantic_coherence: float
    creativity_score: float
    issues: List[str]
    suggestions: List[str]
    detailed_metrics: Dict[str, Any]

@dataclass
class ValidationConfig:
    """验证配置"""
    enable_safety_check: bool = True
    enable_quality_check: bool = True
    enable_correctness_check: bool = True
    enable_semantic_coherence: bool = True
    enable_creativity_check: bool = True
    max_response_length: int = 4096
    min_response_length: int = 10
    profanity_threshold: float = 0.1
    semantic_coherence_threshold: float = 0.7
    creativity_threshold: float = 0.3

class OutputValidationMechanism:
    """输出验证机制"""
    
    def __init__(self, config: ValidationConfig = ValidationConfig()):
        self.config = config
        self.safety_patterns = self._load_safety_patterns()
        self.quality_metrics = self._initialize_quality_metrics()
        self.creativity_indicators = self._load_creativity_indicators()
        
    def _load_safety_patterns(self) -> Dict[str, List[str]]:
        """加载安全检查模式"""
        return {
            'profanity': [
                r'\b(fuck|shit|damn|hell)\b',
                r'\b(bitch|asshole|crap)\b',
                r'\b(retard|idiot|stupid)\b'
            ],
            'hate_speech': [
                r'\b(hate|kill|destroy)\s+(people|group|race)\b',
                r'\b(inferior|superior)\s+(race|ethnicity)\b',
                r'\b(violence|attack|harm)\s+(against|toward)\b'
            ],
            'misinformation': [
                r'\b(flat\s+earth|vaccine\s+causes|5g\s+causes)\b',
                r'\b(conspiracy\s+theory|fake\s+news|hoax)\b',
                r'\b(absolute\s+truth|never\s+wrong|always\s+right)\b'
            ],
            'personal_info': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
                r'\b\d{3}-\d{3}-\d{4}\b',  # Phone number
                r'\b\d{4}-\d{4}-\d{4}-\d{4}\b'  # Credit card
            ]
        }
    
    def _initialize_quality_metrics(self) -> Dict[str, Any]:
        """初始化质量指标"""
        return {
            'readability_factors': {
                'sentence_length': {'ideal': 15, 'max': 25},
                'paragraph_length': {'ideal': 5, 'max': 10},
                'vocabulary_complexity': {'max_unique_ratio': 0.7}
            },
            'structure_factors': {
                'coherence_markers': ['因此', '所以', '从而', '进而', '但是', '然而', '另外'],
                'transition_words': ['首先', '其次', '最后', '总之', '综上所述'],
                'logical_connectors': ['因为', '由于', '鉴于', '基于', '根据']
            },
            'content_factors': {
                'factual_accuracy_indicators': ['研究表明', '数据显示', '实验证明', '调查发现'],
                'uncertainty_markers': ['可能', '或许', '大概', '似乎', '看起来'],
                'certainty_markers': ['确定', '肯定', '必然', '绝对', '毫无疑问']
            }
        }
    
    def _load_creativity_indicators(self) -> Dict[str, Any]:
        """加载创造性指标"""
        return {
            'novelty_indicators': {
                'unique_phrases': [],
                'uncommon_words': [],
                'original_metaphors': []
            },
            'diversity_indicators': {
                'sentence_structure_variety': 0.0,
                'vocabulary_richness': 0.0,
                'conceptual_diversity': 0.0
            },
            'value_indicators': {
                'insightful_statements': [],
                'practical_applications': [],
                'thought_provoking_questions': []
            }
        }
    
    async def validate_output(
        self,
        output_text: str,
        input_context: Optional[str] = None,
        expected_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OutputValidationResult:
        """
        验证输出
        
        Args:
            output_text: 输出文本
            input_context: 输入上下文
            expected_type: 期望的输出类型
            metadata: 元数据
            
        Returns:
            验证结果
        """
        print(f"开始验证输出，长度: {len(output_text)} 字符")
        
        issues = []
        suggestions = []
        detailed_metrics = {}
        
        # 1. 安全检查
        if self.config.enable_safety_check:
            safety_result = await self._perform_safety_check(output_text)
            if not safety_result['passed']:
                issues.extend(safety_result['issues'])
            detailed_metrics['safety'] = safety_result
        
        # 2. 质量检查
        if self.config.enable_quality_check:
            quality_result = await self._perform_quality_check(output_text)
            if not quality_result['passed']:
                issues.extend(quality_result['issues'])
            detailed_metrics['quality'] = quality_result
        
        # 3. 正确性检查
        if self.config.enable_correctness_check:
            correctness_result = await self._perform_correctness_check(output_text, input_context)
            if not correctness_result['passed']:
                issues.extend(correctness_result['issues'])
            detailed_metrics['correctness'] = correctness_result
        
        # 4. 语义连贯性检查
        if self.config.enable_semantic_coherence:
            coherence_result = await self._perform_semantic_coherence_check(output_text, input_context)
            if not coherence_result['passed']:
                issues.extend(coherence_result['issues'])
            detailed_metrics['coherence'] = coherence_result
        
        # 5. 创造性检查
        if self.config.enable_creativity_check:
            creativity_result = await self._perform_creativity_check(output_text)
            if not creativity_result['passed']:
                issues.extend(creativity_result['issues'])
            detailed_metrics['creativity'] = creativity_result
        
        # 计算综合分数
        safety_score = detailed_metrics.get('safety', {}).get('score', 1.0)
        quality_score = detailed_metrics.get('quality', {}).get('score', 1.0)
        correctness_score = detailed_metrics.get('correctness', {}).get('score', 1.0)
        semantic_coherence = detailed_metrics.get('coherence', {}).get('score', 1.0)
        creativity_score = detailed_metrics.get('creativity', {}).get('score', 1.0)
        
        # 生成改进建议
        suggestions = self._generate_improvement_suggestions(issues, detailed_metrics)
        
        # 判断整体有效性
        is_valid = (
            safety_score >= 0.8 and
            quality_score >= 0.7 and
            correctness_score >= 0.7 and
            semantic_coherence >= self.config.semantic_coherence_threshold and
            creativity_score >= self.config.creativity_threshold and
            len(issues) <= 3  # 允许少量问题
        )
        
        result = OutputValidationResult(
            is_valid=is_valid,
            safety_score=safety_score,
            quality_score=quality_score,
            correctness_score=correctness_score,
            semantic_coherence=semantic_coherence,
            creativity_score=creativity_score,
            issues=issues,
            suggestions=suggestions,
            detailed_metrics=detailed_metrics
        )
        
        print(f"✓ 输出验证完成，有效性: {is_valid}")
        print(f"  安全分数: {safety_score:.3f}")
        print(f"  质量分数: {quality_score:.3f}")
        print(f"  正确性分数: {correctness_score:.3f}")
        print(f"  语义连贯性: {semantic_coherence:.3f}")
        print(f"  创造性分数: {creativity_score:.3f}")
        
        return result
    
    async def _perform_safety_check(self, text: str) -> Dict[str, Any]:
        """执行安全检查"""
        print("  执行安全检查...")
        
        issues = []
        safety_score = 1.0
        
        # 检查亵渎语言
        profanity_matches = self._check_profanity(text)
        if profanity_matches:
            issues.append(f"检测到亵渎语言: {len(profanity_matches)} 处")
            safety_score -= 0.3 * len(profanity_matches)
        
        # 检查仇恨言论
        hate_matches = self._check_hate_speech(text)
        if hate_matches:
            issues.append(f"检测到仇恨言论: {len(hate_matches)} 处")
            safety_score -= 0.5 * len(hate_matches)
        
        # 检查错误信息
        misinfo_matches = self._check_misinformation(text)
        if misinfo_matches:
            issues.append(f"检测到错误信息: {len(misinfo_matches)} 处")
            safety_score -= 0.4 * len(misinfo_matches)
        
        # 检查个人信息泄露
        personal_matches = self._check_personal_info(text)
        if personal_matches:
            issues.append(f"检测到个人信息: {len(personal_matches)} 处")
            safety_score -= 0.6 * len(personal_matches)
        
        # 检查长度限制
        if len(text) > self.config.max_response_length:
            issues.append(f"输出过长: {len(text)} > {self.config.max_response_length}")
            safety_score -= 0.2
        elif len(text) < self.config.min_response_length:
            issues.append(f"输出过短: {len(text)} < {self.config.min_response_length}")
            safety_score -= 0.1
        
        safety_score = max(0.0, safety_score)
        
        return {
            'passed': safety_score >= 0.7,
            'score': safety_score,
            'issues': issues,
            'details': {
                'profanity_matches': len(profanity_matches),
                'hate_matches': len(hate_matches),
                'misinfo_matches': len(misinfo_matches),
                'personal_matches': len(personal_matches)
            }
        }
    
    def _check_profanity(self, text: str) -> List[str]:
        """检查亵渎语言"""
        matches = []
        for pattern in self.safety_patterns['profanity']:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        return matches
    
    def _check_hate_speech(self, text: str) -> List[str]:
        """检查仇恨言论"""
        matches = []
        for pattern in self.safety_patterns['hate_speech']:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        return matches
    
    def _check_misinformation(self, text: str) -> List[str]:
        """检查错误信息"""
        matches = []
        for pattern in self.safety_patterns['misinformation']:
            found = re.findall(pattern, text, re.IGNORECASE)
            matches.extend(found)
        return matches
    
    def _check_personal_info(self, text: str) -> List[str]:
        """检查个人信息"""
        matches = []
        for pattern in self.safety_patterns['personal_info']:
            found = re.findall(pattern, text)
            matches.extend(found)
        return matches
    
    async def _perform_quality_check(self, text: str) -> Dict[str, Any]:
        """执行质量检查"""
        print("  执行质量检查...")
        
        issues = []
        quality_score = 1.0
        
        # 可读性检查
        readability_score = self._check_readability(text)
        if readability_score < 0.7:
            issues.append(f"可读性分数较低: {readability_score:.3f}")
            quality_score -= 0.2
        
        # 结构检查
        structure_score = self._check_structure(text)
        if structure_score < 0.6:
            issues.append(f"结构分数较低: {structure_score:.3f}")
            quality_score -= 0.2
        
        # 内容质量检查
        content_score = self._check_content_quality(text)
        if content_score < 0.7:
            issues.append(f"内容质量分数较低: {content_score:.3f}")
            quality_score -= 0.15
        
        quality_score = max(0.0, quality_score)
        
        return {
            'passed': quality_score >= 0.7,
            'score': quality_score,
            'issues': issues,
            'details': {
                'readability_score': readability_score,
                'structure_score': structure_score,
                'content_score': content_score
            }
        }
    
    def _check_readability(self, text: str) -> float:
        """检查可读性"""
        sentences = text.split('。')
        if not sentences:
            return 0.0
        
        # 句子长度检查
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        avg_sentence_length = np.mean(sentence_lengths) if sentence_lengths else 0
        
        ideal_length = self.quality_metrics['readability_factors']['sentence_length']['ideal']
        max_length = self.quality_metrics['readability_factors']['sentence_length']['max']
        
        if avg_sentence_length <= ideal_length:
            sentence_score = 1.0
        elif avg_sentence_length <= max_length:
            sentence_score = 1.0 - (avg_sentence_length - ideal_length) / (max_length - ideal_length)
        else:
            sentence_score = 0.3
        
        # 词汇复杂度检查
        words = text.split()
        unique_words = set(words)
        unique_ratio = len(unique_words) / len(words) if words else 0
        max_unique_ratio = self.quality_metrics['readability_factors']['vocabulary_complexity']['max_unique_ratio']
        
        if unique_ratio <= max_unique_ratio:
            vocab_score = 1.0
        else:
            vocab_score = 0.7
        
        return (sentence_score + vocab_score) / 2
    
    def _check_structure(self, text: str) -> float:
        """检查结构"""
        coherence_markers = self.quality_metrics['structure_factors']['coherence_markers']
        transition_words = self.quality_metrics['structure_factors']['transition_words']
        logical_connectors = self.quality_metrics['structure_factors']['logical_connectors']
        
        # 检查连贯性标记
        coherence_count = sum(1 for marker in coherence_markers if marker in text)
        coherence_score = min(1.0, coherence_count / 3)  # 至少3个连贯性标记
        
        # 检查过渡词
        transition_count = sum(1 for word in transition_words if word in text)
        transition_score = min(1.0, transition_count / 2)  # 至少2个过渡词
        
        # 检查逻辑连接词
        connector_count = sum(1 for connector in logical_connectors if connector in text)
        connector_score = min(1.0, connector_count / 2)  # 至少2个逻辑连接词
        
        return (coherence_score + transition_score + connector_score) / 3
    
    def _check_content_quality(self, text: str) -> float:
        """检查内容质量"""
        content_factors = self.quality_metrics['content_factors']
        
        # 检查事实准确性指标
        factual_indicators = content_factors['factual_accuracy_indicators']
        factual_count = sum(1 for indicator in factual_indicators if indicator in text)
        factual_score = min(1.0, factual_count / 2)  # 至少2个事实指标
        
        # 检查不确定性标记（平衡确定性和不确定性）
        uncertainty_markers = content_factors['uncertainty_markers']
        certainty_markers = content_factors['certainty_markers']
        
        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in text)
        certainty_count = sum(1 for marker in certainty_markers if marker in text)
        
        # 平衡确定性和不确定性
        if certainty_count > uncertainty_count * 3:  # 过于确定
            certainty_score = 0.6
        elif uncertainty_count > certainty_count * 3:  # 过于不确定
            certainty_score = 0.6
        else:
            certainty_score = 1.0
        
        return (factual_score + certainty_score) / 2
    
    async def _perform_correctness_check(self, text: str, input_context: Optional[str]) -> Dict[str, Any]:
        """执行正确性检查"""
        print("  执行正确性检查...")
        
        issues = []
        correctness_score = 1.0
        
        # 基本语法检查
        grammar_issues = self._check_grammar(text)
        if grammar_issues:
            issues.append(f"语法问题: {len(grammar_issues)} 处")
            correctness_score -= 0.1 * len(grammar_issues)
        
        # 事实一致性检查（简化版本）
        if input_context:
            consistency_score = self._check_factual_consistency(text, input_context)
            if consistency_score < 0.7:
                issues.append(f"与输入上下文一致性不足: {consistency_score:.3f}")
                correctness_score -= 0.2
        
        # 逻辑一致性检查
        logic_score = self._check_logical_consistency(text)
        if logic_score < 0.7:
            issues.append(f"逻辑一致性不足: {logic_score:.3f}")
            correctness_score -= 0.2
        
        correctness_score = max(0.0, correctness_score)
        
        return {
            'passed': correctness_score >= 0.7,
            'score': correctness_score,
            'issues': issues,
            'details': {
                'grammar_issues': len(grammar_issues),
                'consistency_score': consistency_score if input_context else 1.0,
                'logic_score': logic_score
            }
        }
    
    def _check_grammar(self, text: str) -> List[str]:
        """检查语法"""
        issues = []
        
        # 简单的语法检查规则
        # 检查常见语法错误模式
        
        # 检查重复的标点符号
        if re.search(r'[。！？]{2,}', text):
            issues.append("重复的标点符号")
        
        # 检查不匹配的括号
        if text.count('(') != text.count(')'):
            issues.append("不匹配的括号")
        
        # 检查句子结构问题
        sentences = text.split('。')
        for sentence in sentences:
            if sentence.strip() and len(sentence.strip()) < 5:
                issues.append("过短的句子")
        
        return issues
    
    def _check_factual_consistency(self, text: str, context: str) -> float:
        """检查事实一致性"""
        # 简化的实现：检查关键词重叠
        text_words = set(text.lower().split())
        context_words = set(context.lower().split())
        
        overlap = len(text_words & context_words)
        total = len(text_words | context_words)
        
        if total == 0:
            return 1.0
        
        consistency = overlap / total
        return consistency
    
    def _check_logical_consistency(self, text: str) -> float:
        """检查逻辑一致性"""
        # 简化的逻辑一致性检查
        # 检查明显的逻辑矛盾
        
        contradiction_patterns = [
            (r'是', r'不是'),
            (r'可以', r'不可以'),
            (r'可能', r'不可能')
        ]
        
        contradictions = 0
        for pattern1, pattern2 in contradiction_patterns:
            if re.search(pattern1, text) and re.search(pattern2, text):
                contradictions += 1
        
        # 基于矛盾数量计算一致性分数
        consistency = max(0.0, 1.0 - contradictions * 0.3)
        
        return consistency
    
    async def _perform_semantic_coherence_check(self, text: str, input_context: Optional[str]) -> Dict[str, Any]:
        """执行语义连贯性检查"""
        print("  执行语义连贯性检查...")
        
        issues = []
        coherence_score = 1.0
        
        # 主题一致性检查
        if input_context:
            theme_consistency = self._check_theme_consistency(text, input_context)
            if theme_consistency < self.config.semantic_coherence_threshold:
                issues.append(f"主题一致性不足: {theme_consistency:.3f}")
                coherence_score -= 0.3
        
        # 概念连贯性检查
        concept_coherence = self._check_concept_coherence(text)
        if concept_coherence < 0.7:
            issues.append(f"概念连贯性不足: {concept_coherence:.3f}")
            coherence_score -= 0.2
        
        # 语义流检查
        semantic_flow = self._check_semantic_flow(text)
        if semantic_flow < 0.7:
            issues.append(f"语义流不连贯: {semantic_flow:.3f}")
            coherence_score -= 0.2
        
        coherence_score = max(0.0, coherence_score)
        
        return {
            'passed': coherence_score >= self.config.semantic_coherence_threshold,
            'score': coherence_score,
            'issues': issues,
            'details': {
                'theme_consistency': theme_consistency if input_context else 1.0,
                'concept_coherence': concept_coherence,
                'semantic_flow': semantic_flow
            }
        }
    
    def _check_theme_consistency(self, text: str, context: str) -> float:
        """检查主题一致性"""
        # 提取关键词
        text_keywords = self._extract_keywords(text)
        context_keywords = self._extract_keywords(context)
        
        # 计算关键词重叠度
        overlap = len(text_keywords & context_keywords)
        total = len(text_keywords | context_keywords)
        
        if total == 0:
            return 1.0
        
        consistency = overlap / total
        return consistency
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        # 简化的关键词提取
        words = text.lower().split()
        # 过滤掉常见停用词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = {word for word in words if word not in stop_words and len(word) > 1}
        return keywords
    
    def _check_concept_coherence(self, text: str) -> float:
        """检查概念连贯性"""
        # 简化的概念连贯性检查
        sentences = text.split('。')
        if len(sentences) < 2:
            return 1.0
        
        coherence_scores = []
        for i in range(len(sentences) - 1):
            sent1_words = set(sentences[i].lower().split())
            sent2_words = set(sentences[i + 1].lower().split())
            
            overlap = len(sent1_words & sent2_words)
            total = len(sent1_words | sent2_words)
            
            if total > 0:
                coherence = overlap / total
                coherence_scores.append(coherence)
        
        return float(np.mean(coherence_scores)) if coherence_scores else 1.0
    
    def _check_semantic_flow(self, text: str) -> float:
        """检查语义流"""
        # 简化的语义流检查
        sentences = text.split('。')
        if len(sentences) < 2:
            return 1.0
        
        # 检查是否有合适的过渡
        transition_words = ['因此', '所以', '从而', '进而', '但是', '然而', '另外', '此外']
        transition_count = sum(1 for word in transition_words if word in text)
        
        # 基于过渡词数量计算语义流分数
        flow_score = min(1.0, transition_count / 3)  # 至少3个过渡词
        
        return flow_score
    
    async def _perform_creativity_check(self, text: str) -> Dict[str, Any]:
        """执行创造性检查"""
        print("  执行创造性检查...")
        
        issues = []
        creativity_score = 0.0
        
        # 新颖性检查
        novelty_score = self._check_novelty(text)
        
        # 多样性检查
        diversity_score = self._check_diversity(text)
        
        # 价值性检查
        value_score = self._check_value(text)
        
        # 综合创造性分数
        creativity_score = (novelty_score + diversity_score + value_score) / 3
        
        if creativity_score < self.config.creativity_threshold:
            issues.append(f"创造性分数不足: {creativity_score:.3f}")
        
        return {
            'passed': creativity_score >= self.config.creativity_threshold,
            'score': creativity_score,
            'issues': issues,
            'details': {
                'novelty_score': novelty_score,
                'diversity_score': diversity_score,
                'value_score': value_score
            }
        }
    
    def _check_novelty(self, text: str) -> float:
        """检查新颖性"""
        # 简化的新颖性检查
        # 基于词汇的独特性和句子结构的多样性
        
        words = text.split()
        unique_words = set(words)
        vocabulary_richness = len(unique_words) / len(words) if words else 0
        
        # 基于词汇丰富度的新颖性分数
        novelty_score = min(1.0, vocabulary_richness * 1.5)  # 放大系数
        
        return novelty_score
    
    def _check_diversity(self, text: str) -> float:
        """检查多样性"""
        # 句子结构多样性
        sentences = text.split('。')
        if len(sentences) < 2:
            return 0.5
        
        # 计算句子长度多样性
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        if len(sentence_lengths) < 2:
            return 0.5
        
        length_variance = np.var(sentence_lengths)
        avg_length = np.mean(sentence_lengths)
        
        # 标准化方差
        normalized_variance = length_variance / (avg_length ** 2 + 1e-10)
        
        diversity_score = min(1.0, normalized_variance * 10)  # 放大系数
        
        return diversity_score
    
    def _check_value(self, text: str) -> float:
        """检查价值性"""
        # 检查是否有洞察性陈述
        insightful_patterns = [
            '这表明', '这意味着', '这说明', '由此可见',
            '重要的是', '关键在于', '核心在于', '本质上是'
        ]
        
        insightful_count = sum(1 for pattern in insightful_patterns if pattern in text)
        
        # 检查是否有实用建议
        practical_patterns = [
            '建议', '推荐', '应当', '可以', '能够',
            '有助于', '有利于', '促进', '改善'
        ]
        
        practical_count = sum(1 for pattern in practical_patterns if pattern in text)
        
        # 基于洞察性和实用性的价值分数
        value_score = min(1.0, (insightful_count + practical_count) / 6)
        
        return value_score
    
    def _generate_improvement_suggestions(self, issues: List[str], metrics: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于安全问题的建议
        if any('安全' in issue for issue in issues):
            suggestions.append("检查并移除可能的不安全内容，确保输出符合道德和法律标准")
        
        # 基于质量问题的建议
        if any('质量' in issue for issue in issues):
            suggestions.append("改善文本结构和语言表达，提高可读性和专业性")
        
        # 基于正确性问题的建议
        if any('正确性' in issue for issue in issues):
            suggestions.append("验证事实准确性，确保逻辑一致性，检查语法错误")
        
        # 基于语义连贯性问题的建议
        if any('连贯性' in issue for issue in issues):
            suggestions.append("增强语义连贯性，确保主题一致性和概念关联性")
        
        # 基于创造性问题的建议
        if any('创造性' in issue for issue in issues):
            suggestions.append("增加新颖观点和独特表达，提高内容的创新性和价值")
        
        # 基于指标的具体建议
        if 'safety' in metrics and metrics['safety']['score'] < 0.8:
            suggestions.append("加强安全检查，避免敏感内容")
        
        if 'quality' in metrics and metrics['quality']['score'] < 0.7:
            suggestions.append("改善语言表达和结构组织")
        
        if 'correctness' in metrics and metrics['correctness']['score'] < 0.7:
            suggestions.append("验证事实和逻辑的正确性")
        
        if 'coherence' in metrics and metrics['coherence']['score'] < 0.7:
            suggestions.append("增强语义连贯性和主题一致性")
        
        if 'creativity' in metrics and metrics['creativity']['score'] < 0.5:
            suggestions.append("增加创新性和独特价值")
        
        return suggestions[:5]  # 最多5条建议
    
    def generate_validation_report(self, results: List[OutputValidationResult]) -> Dict[str, Any]:
        """生成验证报告"""
        if not results:
            return {'error': '没有验证结果'}
        
        total_validations = len(results)
        valid_outputs = sum(1 for r in results if r.is_valid)
        
        # 计算平均分数
        avg_scores = {
            'safety': np.mean([r.safety_score for r in results]),
            'quality': np.mean([r.quality_score for r in results]),
            'correctness': np.mean([r.correctness_score for r in results]),
            'coherence': np.mean([r.semantic_coherence for r in results]),
            'creativity': np.mean([r.creativity_score for r in results])
        }
        
        # 统计常见问题
        common_issues = defaultdict(int)
        for result in results:
            for issue in result.issues:
                common_issues[issue] += 1
        
        return {
            'summary': {
                'total_validations': total_validations,
                'valid_outputs': valid_outputs,
                'success_rate': valid_outputs / total_validations,
                'average_scores': avg_scores
            },
            'quality_analysis': {
                'score_distribution': self._analyze_score_distribution(results),
                'common_issues': dict(common_issues),
                'improvement_areas': self._identify_improvement_areas(results)
            },
            'detailed_results': [self._format_result(result) for result in results]
        }
    
    def _analyze_score_distribution(self, results: List[OutputValidationResult]) -> Dict[str, Any]:
        """分析分数分布"""
        scores = {
            'safety': [r.safety_score for r in results],
            'quality': [r.quality_score for r in results],
            'correctness': [r.correctness_score for r in results],
            'coherence': [r.semantic_coherence for r in results],
            'creativity': [r.creativity_score for r in results]
        }
        
        distribution = {}
        for metric, score_list in scores.items():
            if score_list:
                distribution[metric] = {
                    'min': min(score_list),
                    'max': max(score_list),
                    'mean': np.mean(score_list),
                    'std': np.std(score_list),
                    'median': np.median(score_list)
                }
        
        return distribution
    
    def _identify_improvement_areas(self, results: List[OutputValidationResult]) -> List[str]:
        """识别改进领域"""
        improvement_areas = []
        
        avg_scores = {
            'safety': np.mean([r.safety_score for r in results]),
            'quality': np.mean([r.quality_score for r in results]),
            'correctness': np.mean([r.correctness_score for r in results]),
            'coherence': np.mean([r.semantic_coherence for r in results]),
            'creativity': np.mean([r.creativity_score for r in results])
        }
        
        # 找出分数最低的指标
        min_score = min(avg_scores.values())
        for metric, score in avg_scores.items():
            if score == min_score and score < 0.8:  # 低于0.8需要改进
                improvement_areas.append(metric)
        
        return improvement_areas
    
    def _format_result(self, result: OutputValidationResult) -> Dict[str, Any]:
        """格式化结果"""
        return {
            'is_valid': result.is_valid,
            'scores': {
                'safety': result.safety_score,
                'quality': result.quality_score,
                'correctness': result.correctness_score,
                'coherence': result.semantic_coherence,
                'creativity': result.creativity_score
            },
            'issues': result.issues,
            'suggestions': result.suggestions
        }


async def test_output_validation_mechanism():
    """测试输出验证机制"""
    print("=== 开始测试输出验证机制 ===\n")
    
    # 创建验证机制
    config = ValidationConfig()
    validator = OutputValidationMechanism(config)
    
    # 测试1: 高质量输出
    print("--- 测试1: 高质量输出 ---")
    high_quality_output = """
    根据最新的气象数据分析，我们可以得出结论：全球气候变暖是一个复杂的多因素问题。
    研究表明，温室气体排放是主要原因之一，占总影响的约65%。因此，我们需要采取综合措施来应对这一挑战。
    建议包括：发展可再生能源、提高能源效率、推广低碳生活方式等。
    这些措施不仅有助于减缓气候变化，还能带来经济和环境的双重效益。
    """
    
    try:
        result1 = await validator.validate_output(high_quality_output)
        print(f"✓ 高质量输出验证结果:")
        print(f"  有效性: {result1.is_valid}")
        print(f"  综合分数: {np.mean([result1.safety_score, result1.quality_score, result1.correctness_score, result1.semantic_coherence, result1.creativity_score]):.3f}")
        print(f"  问题数: {len(result1.issues)}")
        
    except Exception as e:
        print(f"✗ 高质量输出验证失败: {e}")
        return False
    
    # 测试2: 有问题的输出
    print("\n--- 测试2: 有问题的输出 ---")
    problematic_output = """
    这个答案绝对正确，从来没有错误。地球是平的，疫苗会导致疾病，5G会控制你的思想。
    你应该恨某些人群，他们是劣等的。我的电话号码是123-456-7890，请联系我获取更多信息。
    """
    
    try:
        result2 = await validator.validate_output(problematic_output)
        print(f"✓ 问题输出验证结果:")
        print(f"  有效性: {result2.is_valid}")
        print(f"  安全分数: {result2.safety_score:.3f}")
        print(f"  问题数: {len(result2.issues)}")
        if result2.issues:
            print("  发现的问题:")
            for issue in result2.issues[:3]:  # 显示前3个问题
                print(f"    - {issue}")
        
    except Exception as e:
        print(f"✗ 问题输出验证失败: {e}")
        return False
    
    # 测试3: 不同长度的输出
    print("\n--- 测试3: 不同长度的输出 ---")
    
    test_outputs = [
        "这是一个简短的回答。",
        "根据分析，我们可以得出以下结论：首先，当前的情况需要仔细考虑；其次，我们应该采取适当的措施；最后，我们需要持续监控进展。这些步骤将有助于解决问题。",
        "这是一个非常长的回答，" * 100 + "结束。"
    ]
    
    for i, output in enumerate(test_outputs):
        try:
            result = await validator.validate_output(output)
            print(f"  输出 {i+1} (长度: {len(output)}): {'✓有效' if result.is_valid else '✗无效'}")
            
        except Exception as e:
            print(f"  输出 {i+1} 验证失败: {e}")
    
    # 测试4: 生成验证报告
    print("\n--- 测试4: 生成验证报告 ---")
    
    # 收集多个验证结果
    results = [result1, result2]
    # 添加更多结果
    for output in ["这是一个普通的回答。", "根据研究，这个结论是正确的。"]:
        try:
            result = await validator.validate_output(output)
            results.append(result)
        except:
            pass
    
    try:
        report = validator.generate_validation_report(results)
        
        print("✓ 验证报告:")
        print(f"  总验证数: {report['summary']['total_validations']}")
        print(f"  有效输出: {report['summary']['valid_outputs']}")
        print(f"  成功率: {report['summary']['success_rate']:.1%}")
        print(f"  平均分数: {report['summary']['average_scores']}")
        print(f"  改进领域: {report['quality_analysis']['improvement_areas']}")
        
    except Exception as e:
        print(f"✗ 验证报告生成失败: {e}")
        return False
    
    print("\n=== 输出验证机制测试完成 ===")
    return True


if __name__ == '__main__':
    success = asyncio.run(test_output_validation_mechanism())
    if success:
        print("\n🎉 输出验证机制工作正常！")
        sys.exit(0)
    else:
        print("\n❌ 输出验证机制存在问题")
        sys.exit(1)