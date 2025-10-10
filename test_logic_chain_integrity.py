#!/usr/bin/env python3
"""
逻辑链完整性验证器
验证推理链条的逻辑完整性和一致性
"""

import sys
sys.path.append('apps/backend/src')

import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re

@dataclass
class LogicRule:
    """逻辑规则"""
    rule_id: str
    rule_type: str  # 'deductive', 'inductive', 'abductive', 'fuzzy'
    premises: List[str]
    conclusion: str
    confidence: float
    applicability_conditions: List[str]

@dataclass
class LogicChain:
    """逻辑链条"""
    chain_id: str
    premises: List[str]
    intermediate_steps: List[str]
    conclusion: str
    logical_connectives: List[str]
    rule_applications: List[LogicRule]
    overall_confidence: float
    consistency_score: float
    completeness_score: float

@dataclass
class LogicValidationResult:
    """逻辑验证结果"""
    is_valid: bool
    consistency_score: float
    completeness_score: float
    logical_gaps: List[str]
    contradictions: List[str]
    rule_violations: List[str]
    suggested_improvements: List[str]
    detailed_analysis: Dict[str, Any]

class LogicChainIntegrityValidator:
    """逻辑链完整性验证器"""
    
    def __init__(self):
        self.validation_rules = {
            'min_consistency_score': 0.7,
            'min_completeness_score': 0.8,
            'max_contradiction_ratio': 0.1,
            'min_rule_confidence': 0.6,
            'logical_connective_threshold': 0.8
        }
        
        # 预定义的逻辑规则
        self.logical_rules = {
            'modus_ponens': {
                'pattern': r'if\s+(.+?)\s+then\s+(.+)',
                'valid_connectives': ['and', 'or', 'implies']
            },
            'syllogism': {
                'pattern': r'(.+?)\s+and\s+(.+?)\s+therefore\s+(.+)',
                'valid_connectives': ['and', 'therefore']
            },
            'contradiction': {
                'pattern': r'(.+?)\s+but\s+(.+?)',
                'valid_connectives': ['but', 'however']
            }
        }
    
    async def validate_logic_chain_integrity(
        self,
        logic_chain: LogicChain,
        context: Optional[Dict[str, Any]] = None
    ) -> LogicValidationResult:
        """
        验证逻辑链完整性
        
        Args:
            logic_chain: 逻辑链条
            context: 上下文信息
            
        Returns:
            逻辑验证结果
        """
        print(f"开始验证逻辑链完整性: {logic_chain.chain_id}")
        
        issues = []
        contradictions = []
        rule_violations = []
        suggestions = []
        
        # 1. 基本结构验证
        basic_valid = self._validate_basic_structure(logic_chain)
        if not basic_valid:
            issues.append("基本逻辑结构不完整")
        
        # 2. 逻辑一致性检查
        consistency_score = await self._check_logical_consistency(logic_chain)
        if consistency_score < self.validation_rules['min_consistency_score']:
            issues.append(f"逻辑一致性分数过低: {consistency_score:.3f}")
        
        # 3. 完整性检查
        completeness_score = await self._check_completeness(logic_chain)
        if completeness_score < self.validation_rules['min_completeness_score']:
            issues.append(f"完整性分数过低: {completeness_score:.3f}")
        
        # 4. 逻辑规则验证
        rule_violations = await self._validate_logical_rules(logic_chain)
        
        # 5. 矛盾检测
        contradictions = await self._detect_contradictions(logic_chain)
        
        # 6. 逻辑缺口识别
        logical_gaps = await self._identify_logical_gaps(logic_chain)
        
        # 7. 连接词验证
        connective_validity = await self._validate_logical_connectives(logic_chain)
        
        # 8. 建议改进
        suggestions = await self._suggest_improvements(logic_chain, issues, logical_gaps)
        
        # 计算综合有效性
        is_valid = (
            consistency_score >= self.validation_rules['min_consistency_score'] and
            completeness_score >= self.validation_rules['min_completeness_score'] and
            len(contradictions) == 0 and
            len(rule_violations) == 0 and
            len(issues) == 0
        )
        
        detailed_analysis = {
            "consistency_analysis": consistency_score,
            "completeness_analysis": completeness_score,
            "connective_validity": connective_validity,
            "rule_application_count": len(logic_chain.rule_applications),
            "premise_count": len(logic_chain.premises),
            "step_count": len(logic_chain.intermediate_steps)
        }
        
        result = LogicValidationResult(
            is_valid=is_valid,
            consistency_score=consistency_score,
            completeness_score=completeness_score,
            logical_gaps=logical_gaps,
            contradictions=contradictions,
            rule_violations=rule_violations,
            suggested_improvements=suggestions,
            detailed_analysis=detailed_analysis
        )
        
        print(f"✓ 逻辑链完整性验证完成，有效性: {is_valid}")
        print(f"  一致性分数: {consistency_score:.3f}")
        print(f"  完整性分数: {completeness_score:.3f}")
        print(f"  逻辑缺口: {len(logical_gaps)} 个")
        print(f"  矛盾: {len(contradictions)} 个")
        print(f"  规则违反: {len(rule_violations)} 个")
        
        if issues:
            print(f"  问题: {issues}")
        
        return result
    
    def _validate_basic_structure(self, logic_chain: LogicChain) -> bool:
        """验证基本逻辑结构"""
        
        # 检查是否有前提
        if not logic_chain.premises:
            return False
        
        # 检查是否有结论
        if not logic_chain.conclusion:
            return False
        
        # 检查步骤是否有效
        for step in logic_chain.intermediate_steps:
            if not step or len(str(step).strip()) == 0:
                return False
        
        return True
    
    async def _check_logical_consistency(self, logic_chain: LogicChain) -> float:
        """检查逻辑一致性"""
        
        consistency_scores = []
        
        # 检查前提之间的一致性
        premise_consistency = await self._check_premise_consistency(logic_chain.premises)
        consistency_scores.append(premise_consistency)
        
        # 检查步骤间的一致性
        step_consistency = await self._check_step_consistency(logic_chain.intermediate_steps)
        consistency_scores.append(step_consistency)
        
        # 检查前提与结论的一致性
        conclusion_consistency = await self._check_conclusion_consistency(
            logic_chain.premises, logic_chain.conclusion
        )
        consistency_scores.append(conclusion_consistency)
        
        # 检查规则应用的一致性
        rule_consistency = await self._check_rule_consistency(logic_chain.rule_applications)
        consistency_scores.append(rule_consistency)
        
        return float(np.mean(consistency_scores))
    
    async def _check_premise_consistency(self, premises: List[str]) -> float:
        """检查前提一致性"""
        if len(premises) < 2:
            return 1.0
        
        consistency_scores = []
        
        for i in range(len(premises)):
            for j in range(i + 1, len(premises)):
                # 检查两个前提是否矛盾
                contradiction_score = self._detect_pairwise_contradiction(
                    premises[i], premises[j]
                )
                consistency_scores.append(1.0 - contradiction_score)
        
        return float(np.mean(consistency_scores)) if consistency_scores else 1.0
    
    async def _check_step_consistency(self, steps: List[str]) -> float:
        """检查步骤间一致性"""
        if len(steps) < 2:
            return 1.0
        
        consistency_scores = []
        
        for i in range(len(steps) - 1):
            # 检查相邻步骤的逻辑连贯性
            coherence_score = self._check_step_coherence(steps[i], steps[i + 1])
            consistency_scores.append(coherence_score)
        
        return float(np.mean(consistency_scores)) if consistency_scores else 1.0
    
    async def _check_conclusion_consistency(
        self,
        premises: List[str],
        conclusion: str
    ) -> float:
        """检查前提与结论的一致性"""
        
        # 检查结论是否与前提矛盾
        for premise in premises:
            contradiction_score = self._detect_pairwise_contradiction(premise, conclusion)
            if contradiction_score > 0.5:  # 高矛盾
                return 0.3
        
        # 检查结论是否得到前提的支持
        support_score = self._calculate_premise_support(premises, conclusion)
        
        return support_score
    
    async def _check_rule_consistency(self, rules: List[LogicRule]) -> float:
        """检查规则一致性"""
        if not rules:
            return 1.0
        
        consistency_scores = []
        
        for rule in rules:
            if rule.confidence < self.validation_rules['min_rule_confidence']:
                consistency_scores.append(0.3)
            else:
                consistency_scores.append(rule.confidence)
        
        return float(np.mean(consistency_scores))
    
    def _detect_pairwise_contradiction(self, statement1: str, statement2: str) -> float:
        """检测两句话之间的矛盾"""
        
        # 简化的矛盾检测
        # 检查明显的矛盾词汇
        contradiction_indicators = [
            ("是", "不是"), ("有", "没有"), ("可以", "不可以"),
            ("可能", "不可能"), ("应该", "不应该")
        ]
        
        for indicator1, indicator2 in contradiction_indicators:
            if indicator1 in statement1 and indicator2 in statement2:
                return 0.8
            if indicator2 in statement1 and indicator1 in statement2:
                return 0.8
        
        # 检查数值矛盾
        numbers1 = self._extract_numbers(statement1)
        numbers2 = self._extract_numbers(statement2)
        
        if numbers1 and numbers2:
            for num1 in numbers1:
                for num2 in numbers2:
                    if num1 != 0 and abs(num2 - num1) / abs(num1) > 0.9:
                        return 0.6
        
        return 0.0
    
    def _extract_numbers(self, text: str) -> List[float]:
        """提取文本中的数字"""
        numbers = re.findall(r'-?\d+\.?\d*', text)
        return [float(num) for num in numbers]
    
    def _calculate_premise_support(self, premises: List[str], conclusion: str) -> float:
        """计算前提对结论的支持度"""
        
        # 检查关键词重叠
        conclusion_words = set(conclusion.lower().split())
        
        support_scores = []
        for premise in premises:
            premise_words = set(premise.lower().split())
            overlap = len(conclusion_words & premise_words)
            total = len(conclusion_words | premise_words)
            
            if total > 0:
                support_score = overlap / total
                support_scores.append(support_score)
        
        return float(np.mean(support_scores)) if support_scores else 0.5
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """计算名称相似度（修复缺失的方法）"""
        if not name1 or not name2:
            return 0.0
        
        # 字符级别的相似度
        common_chars = set(name1.lower()) & set(name2.lower())
        total_chars = set(name1.lower()) | set(name2.lower())
        
        if not total_chars:
            return 0.0
        
        char_similarity = len(common_chars) / len(total_chars)
        
        # 词汇级别的相似度
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if words1 and words2:
            word_similarity = len(words1 & words2) / len(words1 | words2)
        else:
            word_similarity = 0.0
        
        return (char_similarity + word_similarity) / 2
    
    def _check_step_coherence(self, step1: str, step2: str) -> float:
        """检查步骤间的连贯性"""
        
        # 检查关键词传承
        words1 = set(step1.lower().split())
        words2 = set(step2.lower().split())
        
        overlap = len(words1 & words2)
        total = len(words1 | words2)
        
        if total == 0:
            return 0.5
        
        coherence_score = overlap / total
        
        # 检查逻辑连接词
        connective_words = ["因此", "所以", "从而", "进而", "接着"]
        has_connective = any(word in step2 for word in connective_words)
        
        if has_connective:
            coherence_score += 0.2
        
        return min(1.0, coherence_score)
    
    async def _check_completeness(self, logic_chain: LogicChain) -> float:
        """检查完整性"""
        
        completeness_components = []
        
        # 检查前提完整性
        premise_completeness = self._check_premise_completeness(logic_chain.premises)
        completeness_components.append(premise_completeness)
        
        # 检查推理步骤完整性
        step_completeness = self._check_step_completeness(logic_chain.intermediate_steps)
        completeness_components.append(step_completeness)
        
        # 检查规则应用完整性
        rule_completeness = self._check_rule_completeness(logic_chain.rule_applications)
        completeness_components.append(rule_completeness)
        
        # 检查连接词完整性
        connective_completeness = self._check_connective_completeness(logic_chain.logical_connectives)
        completeness_components.append(connective_completeness)
        
        return float(np.mean(completeness_components))
    
    def _check_premise_completeness(self, premises: List[str]) -> float:
        """检查前提完整性"""
        if not premises:
            return 0.0
        
        # 检查前提是否涵盖了必要的逻辑要素
        completeness_score = 1.0
        
        # 检查是否有明确的主体和谓词
        for premise in premises:
            if len(premise.split()) < 3:  # 过于简单的前提
                completeness_score -= 0.2
        
        return max(0.0, completeness_score)
    
    def _check_step_completeness(self, steps: List[str]) -> float:
        """检查步骤完整性"""
        if not steps:
            return 0.5  # 没有中间步骤，中等完整性
        
        completeness_score = 1.0
        
        # 检查步骤数量是否合理
        if len(steps) < 2:
            completeness_score -= 0.3
        
        # 检查每个步骤的完整性
        for step in steps:
            if len(step.split()) < 5:  # 步骤过于简单
                completeness_score -= 0.1
        
        return max(0.0, completeness_score)
    
    def _check_rule_completeness(self, rules: List[LogicRule]) -> float:
        """检查规则完整性"""
        if not rules:
            return 0.5  # 没有规则，中等完整性
        
        completeness_score = 1.0
        
        for rule in rules:
            if not rule.premises or not rule.conclusion:
                completeness_score -= 0.3
            if rule.confidence < self.validation_rules['min_rule_confidence']:
                completeness_score -= 0.2
        
        return max(0.0, completeness_score)
    
    def _check_connective_completeness(self, connectives: List[str]) -> float:
        """检查连接词完整性"""
        if not connectives:
            return 0.5  # 没有连接词，中等完整性
        
        # 检查是否有必要的逻辑连接词
        required_connectives = ["因此", "所以", "从而", "进而"]
        has_required = any(conn in connectives for conn in required_connectives)
        
        if has_required:
            return 1.0
        else:
            return 0.6
    
    async def _validate_logical_rules(self, logic_chain: LogicChain) -> List[str]:
        """验证逻辑规则"""
        violations = []
        
        for rule in logic_chain.rule_applications:
            # 检查规则类型是否有效
            if rule.rule_type not in ["deductive", "inductive", "abductive", "fuzzy"]:
                violations.append(f"未知规则类型: {rule.rule_type}")
            
            # 检查规则置信度
            if rule.confidence < self.validation_rules['min_rule_confidence']:
                violations.append(f"规则置信度过低: {rule.confidence:.3f}")
            
            # 检查规则应用条件
            if not rule.applicability_conditions:
                violations.append(f"规则缺少适用条件: {rule.rule_id}")
        
        return violations
    
    async def _detect_contradictions(self, logic_chain: LogicChain) -> List[str]:
        """检测矛盾"""
        contradictions = []
        
        # 检查前提与结论的矛盾
        for premise in logic_chain.premises:
            contradiction_score = self._detect_pairwise_contradiction(premise, logic_chain.conclusion)
            if contradiction_score > 0.7:
                contradictions.append(f"前提与结论矛盾: '{premise}' vs '{logic_chain.conclusion}'")
        
        # 检查中间步骤的矛盾
        for i, step in enumerate(logic_chain.intermediate_steps):
            for j in range(i + 1, len(logic_chain.intermediate_steps)):
                score = self._detect_pairwise_contradiction(step, logic_chain.intermediate_steps[j])
                if score > 0.7:
                    contradictions.append(f"步骤 {i} 与步骤 {j} 矛盾")
        
        return contradictions
    
    async def _identify_logical_gaps(self, logic_chain: LogicChain) -> List[str]:
        """识别逻辑缺口"""
        gaps = []
        
        # 检查前提到第一步的缺口
        if logic_chain.intermediate_steps:
            first_step = logic_chain.intermediate_steps[0]
            gap_score = self._calculate_step_gap(logic_chain.premises, [first_step])
            if gap_score < 0.6:
                gaps.append("前提到第一步推理存在逻辑缺口")
        
        # 检查步骤间的缺口
        for i in range(len(logic_chain.intermediate_steps) - 1):
            current_step = logic_chain.intermediate_steps[i]
            next_step = logic_chain.intermediate_steps[i + 1]
            gap_score = self._calculate_step_gap([current_step], [next_step])
            if gap_score < 0.6:
                gaps.append(f"步骤 {i} 到步骤 {i+1} 存在逻辑缺口")
        
        # 检查最后一步到结论的缺口
        if logic_chain.intermediate_steps:
            last_step = logic_chain.intermediate_steps[-1]
            gap_score = self._calculate_step_gap([last_step], [logic_chain.conclusion])
            if gap_score < 0.6:
                gaps.append("最后一步到结论存在逻辑缺口")
        
        return gaps
    
    def _calculate_step_gap(self, from_steps: List[str], to_steps: List[str]) -> float:
        """计算步骤间的逻辑缺口"""
        
        if not from_steps or not to_steps:
            return 0.0
        
        # 计算语义相似度作为缺口指标
        gap_scores = []
        
        for from_step in from_steps:
            for to_step in to_steps:
                # 计算词汇重叠度
                from_words = set(from_step.lower().split())
                to_words = set(to_step.lower().split())
                
                overlap = len(from_words & to_words)
                total = len(from_words | to_words)
                
                if total > 0:
                    similarity = overlap / total
                    gap_scores.append(similarity)
        
        return float(np.mean(gap_scores)) if gap_scores else 0.0
    
    async def _validate_logical_connectives(self, logic_chain: LogicChain) -> float:
        """验证逻辑连接词"""
        
        if not logic_chain.logical_connectives:
            return 0.5  # 没有连接词，中等有效性
        
        valid_connectives = [
            "因此", "所以", "从而", "进而", "接着", "然后",
            "因为", "由于", "鉴于", "基于", "根据"
        ]
        
        validity_scores = []
        
        for connective in logic_chain.logical_connectives:
            if connective in valid_connectives:
                validity_scores.append(1.0)
            else:
                # 检查是否是合理的连接词变体
                similarity_score = max(
                    self._calculate_name_similarity(connective, valid_conn)
                    for valid_conn in valid_connectives
                )
                validity_scores.append(similarity_score)
        
        return float(np.mean(validity_scores))
    
    async def _suggest_improvements(
        self,
        logic_chain: LogicChain,
        issues: List[str],
        logical_gaps: List[str]
    ) -> List[str]:
        """建议改进"""
        suggestions = []
        
        # 基于问题的建议
        if "逻辑一致性分数过低" in issues:
            suggestions.append("检查前提之间是否存在矛盾，确保推理步骤的逻辑连贯性")
        
        if "完整性分数过低" in issues:
            suggestions.append("增加必要的推理步骤，确保每个逻辑环节都有充分的论证")
        
        # 基于逻辑缺口的建议
        if logical_gaps:
            suggestions.append("在逻辑缺口处增加中间推理步骤，提供充分的论证过程")
        
        # 基于结构完整性的建议
        if not logic_chain.rule_applications:
            suggestions.append("考虑添加明确的逻辑规则来支持推理过程")
        
        if len(logic_chain.logical_connectives) < 2:
            suggestions.append("增加更多的逻辑连接词来明确推理关系")
        
        return suggestions
    
    def generate_integrity_report(self, validation_result: LogicValidationResult) -> Dict[str, Any]:
        """生成完整性报告"""
        return {
            "validation_summary": {
                "is_valid": validation_result.is_valid,
                "consistency_score": validation_result.consistency_score,
                "completeness_score": validation_result.completeness_score
            },
            "detailed_findings": {
                "logical_gaps": validation_result.logical_gaps,
                "contradictions": validation_result.contradictions,
                "rule_violations": validation_result.rule_violations
            },
            "improvement_suggestions": validation_result.suggested_improvements,
            "detailed_analysis": validation_result.detailed_analysis
        }


async def test_logic_chain_integrity_validation():
    """测试逻辑链完整性验证"""
    print("=== 开始测试逻辑链完整性验证 ===\n")
    
    validator = LogicChainIntegrityValidator()
    
    # 测试1: 完整的逻辑链条
    print("--- 测试1: 完整逻辑链条 ---")
    
    complete_logic_chain = LogicChain(
        chain_id="weather_reasoning_001",
        premises=[
            "天空中有乌云",
            "湿度达到了80%",
            "气压在下降"
        ],
        intermediate_steps=[
            "根据气象学知识，这些条件通常预示着降雨",
            "结合当前的季节和时间，降雨概率进一步增加",
            "考虑到地理位置和气候模式，这种天气变化是合理的"
        ],
        conclusion="很可能会下雨，建议携带雨具",
        logical_connectives=["因此", "进而", "所以"],
        rule_applications=[
            LogicRule(
                rule_id="meteorology_001",
                rule_type="inductive",
                premises=["天空有乌云", "湿度高", "气压下降"],
                conclusion="可能下雨",
                confidence=0.8,
                applicability_conditions=["气象条件", "时间因素"]
            )
        ],
        overall_confidence=0.85,
        consistency_score=0.9,
        completeness_score=0.95
    )
    
    try:
        result = await validator.validate_logic_chain_integrity(complete_logic_chain)
        
        print("✓ 完整逻辑链条验证结果:")
        print(f"  有效性: {result.is_valid}")
        print(f"  一致性分数: {result.consistency_score:.3f}")
        print(f"  完整性分数: {result.completeness_score:.3f}")
        print(f"  逻辑缺口: {len(result.logical_gaps)} 个")
        print(f"  矛盾: {len(result.contradictions)} 个")
        print(f"  规则违反: {len(result.rule_violations)} 个")
        
        if result.suggested_improvements:
            print("  改进建议:")
            for suggestion in result.suggested_improvements:
                print(f"    - {suggestion}")
        
    except Exception as e:
        print(f"✗ 完整逻辑链条验证失败: {e}")
        return False
    
    # 测试2: 有逻辑问题的链条
    print("\n--- 测试2: 有逻辑问题的链条 ---")
    
    problematic_chain = LogicChain(
        chain_id="faulty_reasoning_001",
        premises=[
            "今天天气晴朗",
            "阳光明媚"
        ],
        intermediate_steps=[
            "晴朗的天气通常不会下雨",
            "但是根据某种理论，晴天也可能突然下雨"
        ],
        conclusion="一定会下暴雨",
        logical_connectives=["但是", "因此"],
        rule_applications=[],
        overall_confidence=0.3,
        consistency_score=0.4,
        completeness_score=0.6
    )
    
    try:
        result = await validator.validate_logic_chain_integrity(problematic_chain)
        
        print("✓ 问题逻辑链条验证结果:")
        print(f"  有效性: {result.is_valid}")
        print(f"  一致性分数: {result.consistency_score:.3f}")
        print(f"  完整性分数: {result.completeness_score:.3f}")
        
        if result.contradictions:
            print("  发现的矛盾:")
            for contradiction in result.contradictions:
                print(f"    - {contradiction}")
        
        if result.logical_gaps:
            print("  逻辑缺口:")
            for gap in result.logical_gaps:
                print(f"    - {gap}")
        
    except Exception as e:
        print(f"✗ 问题逻辑链条验证失败: {e}")
        return False
    
    # 测试3: 科学推理链条
    print("\n--- 测试3: 科学推理链条 ---")
    
    scientific_chain = LogicChain(
        chain_id="scientific_reasoning_001",
        premises=[
            "物体在重力作用下会加速下落",
            "空气阻力与速度平方成正比",
            "物体质量为1kg"
        ],
        intermediate_steps=[
            "根据牛顿第二定律，F=ma，物体将受到向下的净力",
            "随着速度增加，空气阻力也会增加",
            "当重力与空气阻力平衡时，物体将达到终端速度",
            "终端速度的大小取决于物体的形状和质量"
        ],
        conclusion="该物体将达到约50m/s的终端速度",
        logical_connectives=["根据", "随着", "当", "因此"],
        rule_applications=[
            LogicRule(
                rule_id="newton_second_law",
                rule_type="deductive",
                premises=["净力", "质量"],
                conclusion="加速度",
                confidence=0.95,
                applicability_conditions=["经典力学", "宏观物体"]
            ),
            LogicRule(
                rule_id="air_resistance",
                rule_type="deductive",
                premises=["速度", "空气密度", "物体形状"],
                conclusion="空气阻力",
                confidence=0.9,
                applicability_conditions=["流体动力学", "合理速度范围"]
            )
        ],
        overall_confidence=0.9,
        consistency_score=0.95,
        completeness_score=0.9
    )
    
    try:
        result = await validator.validate_logic_chain_integrity(scientific_chain)
        
        print("✓ 科学推理链条验证结果:")
        print(f"  有效性: {result.is_valid}")
        print(f"  一致性分数: {result.consistency_score:.3f}")
        print(f"  完整性分数: {result.completeness_score:.3f}")
        
        if result.rule_violations:
            print("  规则违反:")
            for violation in result.rule_violations:
                print(f"    - {violation}")
        
    except Exception as e:
        print(f"✗ 科学推理链条验证失败: {e}")
        return False
    
    # 测试4: 生成完整性报告
    print("\n--- 测试4: 生成完整性报告 ---")
    
    try:
        # 使用第一个测试的结果
        integrity_report = validator.generate_integrity_report(result)
        
        print("✓ 完整性报告:")
        print(f"  验证摘要: {integrity_report['validation_summary']}")
        print(f"  详细发现: {len(integrity_report['detailed_findings'])} 个类别")
        print(f"  改进建议: {len(integrity_report['improvement_suggestions'])} 条")
        
    except Exception as e:
        print(f"✗ 完整性报告生成失败: {e}")
        return False
    
    print("\n=== 逻辑链完整性验证测试完成 ===")
    return True


if __name__ == '__main__':
    success = asyncio.run(test_logic_chain_integrity_validation())
    if success:
        print("\n🎉 逻辑链完整性验证系统工作正常！")
        sys.exit(0)
    else:
        print("\n❌ 逻辑链完整性验证系统存在问题")
        sys.exit(1)
