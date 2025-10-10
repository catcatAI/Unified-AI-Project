#!/usr/bin/env python3
"""
中间推理步骤验证器
验证推理过程中的每个中间步骤
"""

import sys
sys.path.append('apps/backend/src')

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: int
    step_type: str  # 'premise', 'inference', 'conclusion', 'verification'
    input_data: Any
    output_data: Any
    reasoning_method: str
    confidence_score: float
    supporting_evidence: List[str]
    contradictions: List[str]
    timestamp: datetime
    is_valid: bool = True
    validation_issues: List[str] = None

@dataclass
class ReasoningChain:
    """推理链条"""
    chain_id: str
    steps: List[ReasoningStep]
    overall_confidence: float
    logical_consistency: float
    completeness_score: float
    is_complete: bool = False

class IntermediateReasoningValidator:
    """中间推理步骤验证器"""
    
    def __init__(self):
        self.validation_rules = {
            'min_step_confidence': 0.3,        # 最小步骤置信度
            'max_contradiction_ratio': 0.2,    # 最大矛盾比例
            'min_evidence_support': 1,         # 最小证据支持数
            'logical_consistency_threshold': 0.7,  # 逻辑一致性阈值
            'completeness_threshold': 0.8      # 完整性阈值
        }
    
    async def validate_reasoning_chain(
        self,
        reasoning_chain: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningChain:
        """
        验证整个推理链条
        
        Args:
            reasoning_chain: 推理步骤列表
            context: 上下文信息
            
        Returns:
            验证后的推理链条
        """
        print(f"开始验证推理链条，共 {len(reasoning_chain)} 个步骤")
        
        validated_steps = []
        total_contradictions = 0
        
        for i, step_data in enumerate(reasoning_chain):
            print(f"\n验证第 {i+1} 个推理步骤:")
            
            try:
                validated_step = await self._validate_single_step(step_data, i, context)
                validated_steps.append(validated_step)
                
                # 统计矛盾
                total_contradictions += len(validated_step.contradictions)
                
            except Exception as e:
                print(f"  ✗ 第 {i} 步验证失败: {e}")
                # 创建失败的推理步骤
                failed_step = ReasoningStep(
                    step_id=i,
                    step_type="validation_failed",
                    input_data=step_data,
                    output_data=None,
                    reasoning_method="unknown",
                    confidence_score=0.0,
                    supporting_evidence=[],
                    contradictions=[],
                    timestamp=datetime.now(),
                    is_valid=False,
                    validation_issues=[f"验证异常: {e}"]
                )
                validated_steps.append(failed_step)
        
        # 验证推理链条的连贯性
        logical_consistency = await self._validate_chain_coherence(validated_steps)
        
        # 验证推理链条的完整性
        completeness_score = self._calculate_completeness_score(validated_steps)
        
        # 计算整体置信度
        overall_confidence = self._calculate_overall_confidence(validated_steps)
        
        # 创建验证后的推理链条
        validated_chain = ReasoningChain(
            chain_id=f"chain_{datetime.now().timestamp()}",
            steps=validated_steps,
            overall_confidence=overall_confidence,
            logical_consistency=logical_consistency,
            completeness_score=completeness_score,
            is_complete=(completeness_score >= self.validation_rules['completeness_threshold'])
        )
        
        print(f"\n✓ 推理链条验证完成")
        print(f"  总步骤数: {len(validated_steps)}")
        print(f"  有效步骤数: {sum(1 for step in validated_steps if step.is_valid)}")
        print(f"  整体置信度: {overall_confidence:.3f}")
        print(f"  逻辑一致性: {logical_consistency:.3f}")
        print(f"  完整性得分: {completeness_score:.3f}")
        print(f"  链条完整性: {validated_chain.is_complete}")
        
        return validated_chain
    
    async def _validate_single_step(
        self,
        step_data: Dict[str, Any],
        step_id: int,
        context: Optional[Dict[str, Any]]
    ) -> ReasoningStep:
        """验证单个推理步骤"""
        
        step_type = step_data.get("step_type", "unknown")
        input_data = step_data.get("input", step_data.get("input_data", {}))
        output_data = step_data.get("output", step_data.get("output_data", {}))
        reasoning_method = step_data.get("reasoning_method", "unknown")
        
        print(f"  步骤类型: {step_type}, 推理方法: {reasoning_method}")
        
        # 基本结构验证
        validation_issues = []
        
        if not input_data:
            validation_issues.append("缺少输入数据")
        
        if output_data is None:
            validation_issues.append("缺少输出数据")
        
        if reasoning_method == "unknown":
            validation_issues.append("推理方法未指定")
        
        # 逻辑一致性验证
        logical_consistency = await self._check_logical_consistency(step_data, context)
        if not logical_consistency:
            validation_issues.append("逻辑不一致")
        
        # 证据支持验证
        evidence_support = await self._validate_evidence_support(step_data)
        
        # 矛盾检测
        contradictions = await self._detect_contradictions(step_data, context)
        
        # 置信度评估
        confidence_score = self._calculate_step_confidence(
            step_data, len(evidence_support), len(contradictions), len(validation_issues)
        )
        
        # 判断步骤有效性
        is_valid = (
            confidence_score >= self.validation_rules['min_step_confidence'] and
            len(contradictions) <= self.validation_rules['max_contradiction_ratio'] * len(evidence_support) and
            len(validation_issues) == 0
        )
        
        return ReasoningStep(
            step_id=step_id,
            step_type=step_type,
            input_data=input_data,
            output_data=output_data,
            reasoning_method=reasoning_method,
            confidence_score=confidence_score,
            supporting_evidence=evidence_support,
            contradictions=contradictions,
            timestamp=datetime.now(),
            is_valid=is_valid,
            validation_issues=validation_issues if validation_issues else None
        )
    
    async def _check_logical_consistency(
        self,
        step_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """检查逻辑一致性"""
        
        # 检查输入输出的逻辑关系
        input_data = step_data.get("input", step_data.get("input_data", {}))
        output_data = step_data.get("output", step_data.get("output_data", {}))
        
        # 简化的逻辑一致性检查
        if isinstance(input_data, dict) and isinstance(output_data, dict):
            # 检查是否有明显的逻辑矛盾
            for key in input_data:
                if key in output_data:
                    input_val = input_data[key]
                    output_val = output_data[key]
                    
                    # 检查数值逻辑的合理性
                    if isinstance(input_val, (int, float)) and isinstance(output_val, (int, float)):
                        # 简单的数值逻辑检查
                        if "probability" in key and (output_val < 0 or output_val > 1):
                            return False
                        if "count" in key and output_val < 0:
                            return False
        
        return True
    
    async def _validate_evidence_support(self, step_data: Dict[str, Any]) -> List[str]:
        """验证证据支持"""
        evidence = step_data.get("supporting_evidence", step_data.get("evidence", []))
        
        if not isinstance(evidence, list):
            return []
        
        # 过滤掉无效的证据
        valid_evidence = []
        for item in evidence:
            if item and len(str(item)) > 0:  # 简单的有效性检查
                valid_evidence.append(str(item))
        
        return valid_evidence
    
    async def _detect_contradictions(
        self,
        step_data: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """检测矛盾"""
        contradictions = []
        
        # 检查内部矛盾
        input_data = step_data.get("input", step_data.get("input_data", {}))
        output_data = step_data.get("output", step_data.get("output_data", {}))
        
        # 简化的矛盾检测
        if isinstance(input_data, dict) and isinstance(output_data, dict):
            # 检查数值矛盾
            for key in set(input_data.keys()) & set(output_data.keys()):
                input_val = input_data[key]
                output_val = output_data[key]
                
                if isinstance(input_val, (int, float)) and isinstance(output_val, (int, float)):
                    # 检查不合理的数值变化
                    if abs(output_val - input_val) > abs(input_val) * 10:  # 变化过大
                        contradictions.append(f"数值 '{key}' 变化不合理: {input_val} -> {output_val}")
        
        # 检查与上下文的矛盾
        if context:
            context_data = context.get("previous_outputs", [])
            current_output = output_data
            
            # 检查与之前输出的矛盾
            for prev_output in context_data:
                if self._has_contradiction(current_output, prev_output):
                    contradictions.append("与之前的输出存在矛盾")
                    break
        
        return contradictions
    
    def _has_contradiction(self, data1: Any, data2: Any) -> bool:
        """检查两个数据是否存在矛盾"""
        # 简化的矛盾检测逻辑
        if isinstance(data1, dict) and isinstance(data2, dict):
            for key in set(data1.keys()) & set(data2.keys()):
                val1 = data1[key]
                val2 = data2[key]
                
                # 检查数值矛盾
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    if val1 != 0 and abs(val2 - val1) / abs(val1) > 0.9:  # 90%的差异
                        return True
        
        return False
    
    def _calculate_step_confidence(
        self,
        step_data: Dict[str, Any],
        evidence_count: int,
        contradiction_count: int,
        issue_count: int
    ) -> float:
        """计算步骤置信度"""
        
        # 基础分数
        base_score = 1.0
        
        # 证据支持加分
        evidence_bonus = min(0.3, evidence_count * 0.1)  # 最多0.3分
        
        # 矛盾扣分
        contradiction_penalty = min(0.5, contradiction_count * 0.2)  # 最多扣0.5分
        
        # 问题扣分
        issue_penalty = min(0.7, issue_count * 0.3)  # 最多扣0.7分
        
        # 计算最终分数
        confidence = base_score + evidence_bonus - contradiction_penalty - issue_penalty
        
        return max(0.0, min(1.0, confidence))
    
    async def _validate_chain_coherence(self, steps: List[ReasoningStep]) -> float:
        """验证推理链条的连贯性"""
        
        if len(steps) < 2:
            return 1.0  # 单步骤默认为连贯
        
        coherence_scores = []
        
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            # 检查步骤间的逻辑连贯性
            coherence_score = self._check_step_transition(current_step, next_step)
            coherence_scores.append(coherence_score)
        
        return float(np.mean(coherence_scores)) if coherence_scores else 1.0
    
    def _check_step_transition(self, current_step: ReasoningStep, next_step: ReasoningStep) -> float:
        """检查步骤间的过渡逻辑"""
        
        # 检查步骤类型的合理性
        valid_transitions = {
            ("premise", "inference"): 1.0,
            ("premise", "verification"): 0.8,
            ("inference", "conclusion"): 1.0,
            ("inference", "verification"): 0.9,
            ("verification", "conclusion"): 0.9,
            ("conclusion", "verification"): 0.7
        }
        
        transition_key = (current_step.step_type, next_step.step_type)
        transition_score = valid_transitions.get(transition_key, 0.5)
        
        # 检查置信度的平滑变化
        confidence_diff = abs(next_step.confidence_score - current_step.confidence_score)
        if confidence_diff > 0.5:  # 置信度变化过大
            transition_score *= 0.7
        
        # 检查数据连贯性
        if (isinstance(current_step.output_data, dict) and 
            isinstance(next_step.input_data, dict)):
            
            # 检查是否有数据传递
            common_keys = set(current_step.output_data.keys()) & set(next_step.input_data.keys())
            if len(common_keys) == 0:
                transition_score *= 0.8  # 没有明显的数据传递
        
        return transition_score
    
    def _calculate_completeness_score(self, steps: List[ReasoningStep]) -> float:
        """计算完整性得分"""
        
        if not steps:
            return 0.0
        
        # 检查是否有完整的推理流程
        step_types = [step.step_type for step in steps]
        
        # 检查必要的步骤类型
        has_premise = any(step_type in ["premise", "input"] for step_type in step_types)
        has_inference = any(step_type in ["inference", "reasoning"] for step_type in step_types)
        has_conclusion = any(step_type in ["conclusion", "output"] for step_type in step_types)
        
        completeness_components = [
            has_premise,
            has_inference,
            has_conclusion
        ]
        
        base_completeness = sum(completeness_components) / len(completeness_components)
        
        # 考虑步骤的有效性
        valid_steps_ratio = sum(1 for step in steps if step.is_valid) / len(steps)
        
        # 综合完整性得分
        overall_completeness = (base_completeness + valid_steps_ratio) / 2
        
        return overall_completeness
    
    def _calculate_overall_confidence(self, steps: List[ReasoningStep]) -> float:
        """计算整体置信度"""
        if not steps:
            return 0.0
        
        # 平均步骤置信度
        avg_step_confidence = np.mean([step.confidence_score for step in steps])
        
        # 考虑有效步骤的比例
        valid_steps_ratio = sum(1 for step in steps if step.is_valid) / len(steps)
        
        # 综合置信度
        overall_confidence = (avg_step_confidence + valid_steps_ratio) / 2
        
        return overall_confidence
    
    def generate_validation_report(self, reasoning_chain: ReasoningChain) -> Dict[str, Any]:
        """生成验证报告"""
        return {
            "chain_id": reasoning_chain.chain_id,
            "total_steps": len(reasoning_chain.steps),
            "valid_steps": sum(1 for step in reasoning_chain.steps if step.is_valid),
            "overall_confidence": reasoning_chain.overall_confidence,
            "logical_consistency": reasoning_chain.logical_consistency,
            "completeness_score": reasoning_chain.completeness_score,
            "is_complete": reasoning_chain.is_complete,
            "step_breakdown": {
                step.step_type: {
                    "count": sum(1 for s in reasoning_chain.steps if s.step_type == step.step_type),
                    "avg_confidence": np.mean([s.confidence_score for s in reasoning_chain.steps if s.step_type == step.step_type]) if any(s.step_type == step.step_type for s in reasoning_chain.steps) else 0.0
                }
                for step in reasoning_chain.steps
            },
            "common_issues": self._extract_common_issues(reasoning_chain.steps)
        }
    
    def _extract_common_issues(self, steps: List[ReasoningStep]) -> Dict[str, int]:
        """提取常见问题"""
        issue_counts = {}
        
        for step in steps:
            if step.validation_issues:
                for issue in step.validation_issues:
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        return issue_counts


async def test_intermediate_reasoning_validation():
    """测试中间推理步骤验证"""
    print("=== 开始测试中间推理步骤验证 ===\n")
    
    validator = IntermediateReasoningValidator()
    
    # 测试1: 完整的推理链条
    print("--- 测试1: 完整推理链条 ---")
    complete_reasoning_chain = [
        {
            "step_type": "premise",
            "input": {"observation": "天空中有乌云", "time": "下午3点"},
            "output": {"premise": "可能有雨", "confidence": 0.7},
            "reasoning_method": "observation_to_premise",
            "supporting_evidence": ["气象学常识", "历史数据"]
        },
        {
            "step_type": "inference",
            "input": {"premise": "可能有雨", "additional_info": "湿度80%"},
            "output": {"inference": "很可能会下雨", "confidence": 0.85},
            "reasoning_method": "probabilistic_inference",
            "supporting_evidence": ["湿度数据", "气压变化"]
        },
        {
            "step_type": "conclusion",
            "input": {"inference": "很可能会下雨", "urgency": "high"},
            "output": {"conclusion": "应该带伞", "confidence": 0.9},
            "reasoning_method": "decision_making",
            "supporting_evidence": ["风险评估", "预防措施"]
        }
    ]
    
    try:
        validated_chain = await validator.validate_reasoning_chain(complete_reasoning_chain)
        
        print("✓ 完整推理链条验证结果:")
        print(f"  总步骤数: {len(validated_chain.steps)}")
        print(f"  有效步骤数: {sum(1 for step in validated_chain.steps if step.is_valid)}")
        print(f"  整体置信度: {validated_chain.overall_confidence:.3f}")
        print(f"  逻辑一致性: {validated_chain.logical_consistency:.3f}")
        print(f"  完整性得分: {validated_chain.completeness_score:.3f}")
        print(f"  链条完整性: {validated_chain.is_complete}")
        
        # 显示各步骤详情
        for i, step in enumerate(validated_chain.steps):
            print(f"  步骤 {i}: {step.step_type} - 置信度: {step.confidence_score:.3f} - 有效: {step.is_valid}")
            if step.contradictions:
                print(f"    矛盾: {step.contradictions}")
        
    except Exception as e:
        print(f"✗ 完整推理链条验证失败: {e}")
        return False
    
    # 测试2: 有问题的推理链条
    print("\n--- 测试2: 有问题的推理链条 ---")
    problematic_chain = [
        {
            "step_type": "premise",
            "input": {"observation": "天空晴朗"},
            "output": {"premise": "一定会下雨", "confidence": 0.95},  # 逻辑矛盾
            "reasoning_method": "faulty_observation",
            "supporting_evidence": []  # 缺少证据
        },
        {
            "step_type": "inference",
            "input": {"premise": "一定会下雨"},
            "output": {"inference": "不需要带伞", "confidence": 0.8},  # 与前提矛盾
            "reasoning_method": "contradictory_inference"
        }
    ]
    
    try:
        validated_chain = await validator.validate_reasoning_chain(problematic_chain)
        
        print("✓ 问题推理链条验证结果:")
        print(f"  整体置信度: {validated_chain.overall_confidence:.3f}")
        print(f"  逻辑一致性: {validated_chain.logical_consistency:.3f}")
        print(f"  有效步骤比例: {sum(1 for step in validated_chain.steps if step.is_valid)}/{len(validated_chain.steps)}")
        
        # 显示发现的问题
        validation_report = validator.generate_validation_report(validated_chain)
        if validation_report["common_issues"]:
            print("  发现的问题:")
            for issue, count in validation_report["common_issues"].items():
                print(f"    {issue}: {count} 次")
        
    except Exception as e:
        print(f"✗ 问题推理链条验证失败: {e}")
        return False
    
    # 测试3: 验证报告生成
    print("\n--- 测试3: 验证报告生成 ---")
    try:
        # 使用第一个测试的结果
        report = validator.generate_validation_report(validated_chain)
        
        print("✓ 验证报告:")
        print(f"  链条ID: {report['chain_id']}")
        print(f"  步骤统计: {report['step_breakdown']}")
        print(f"  常见问题: {report['common_issues']}")
        
    except Exception as e:
        print(f"✗ 验证报告生成失败: {e}")
        return False
    
    # 测试4: 复杂推理场景
    print("\n--- 测试4: 复杂推理场景 ---")
    complex_chain = [
        {
            "step_type": "premise",
            "input": {"market_data": "股价上涨10%", "volume": "增加50%"},
            "output": {"premise": "市场乐观", "confidence": 0.6},
            "reasoning_method": "market_analysis",
            "supporting_evidence": ["技术指标", "成交量分析"]
        },
        {
            "step_type": "inference",
            "input": {"premise": "市场乐观", "news": "公司发布新产品"},
            "output": {"inference": "股价可能继续上涨", "confidence": 0.75},
            "reasoning_method": "fundamental_analysis",
            "supporting_evidence": ["产品创新性", "市场反应"]
        },
        {
            "step_type": "verification",
            "input": {"inference": "股价可能继续上涨", "risk_factors": ["市场波动", "竞争加剧"]},
            "output": {"verification": "推理基本合理，但需注意风险", "confidence": 0.7},
            "reasoning_method": "risk_assessment",
            "contradictions": ["市场波动性"]
        },
        {
            "step_type": "conclusion",
            "input": {"verified_inference": "股价可能继续上涨", "risk_level": "medium"},
            "output": {"conclusion": "建议买入，但需设置止损", "confidence": 0.65},
            "reasoning_method": "investment_decision"
        }
    ]
    
    try:
        validated_chain = await validator.validate_reasoning_chain(complex_chain)
        
        print("✓ 复杂推理场景验证结果:")
        print(f"  整体置信度: {validated_chain.overall_confidence:.3f}")
        print(f"  逻辑一致性: {validated_chain.logical_consistency:.3f}")
        print(f"  完整性得分: {validated_chain.completeness_score:.3f}")
        
        # 显示步骤类型的分布
        step_types = {}
        for step in validated_chain.steps:
            step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
        
        print("  步骤类型分布:")
        for step_type, count in step_types.items():
            print(f"    {step_type}: {count}")
        
    except Exception as e:
        print(f"✗ 复杂推理场景验证失败: {e}")
        return False
    
    print("\n=== 中间推理步骤验证测试完成 ===")
    return True


if __name__ == '__main__':
    success = asyncio.run(test_intermediate_reasoning_validation())
    if success:
        print("\n🎉 中间推理步骤验证系统工作正常！")
        sys.exit(0)
    else:
        print("\n❌ 中间推理步骤验证系统存在问题")
        sys.exit(1)
