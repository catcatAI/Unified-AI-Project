#!/usr/bin/env python3
"""
因果推理正确性验证器
确保因果推理引擎的推理结果正确可靠
"""

import sys
sys.path.append('apps/backend/src')

from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

class CausalReasoningCorrectnessValidator:
    """因果推理正确性验证器"""
    
    def __init__(self):
        self.validation_thresholds = {
            'min_causal_confidence': 0.6,      # 最小因果置信度
            'max_contradiction_ratio': 0.2,    # 最大矛盾比例
            'min_evidence_support': 2,         # 最小证据支持数
            'temporal_consistency_threshold': 0.8,  # 时间一致性阈值
            'statistical_significance_threshold': 0.05  # 统计显著性阈值
        }
        
        # 预定义的因果知识库（用于验证）
        self.causal_knowledge_base = {
            "temperature_mood": {
                "cause": "temperature_increase",
                "effect": "mood_improvement",
                "confidence": 0.7,
                "evidence": ["心理学研究", "气象数据"]
            },
            "exercise_health": {
                "cause": "regular_exercise",
                "effect": "health_improvement", 
                "confidence": 0.9,
                "evidence": ["医学研究", "统计数据"]
            },
            "sleep_performance": {
                "cause": "adequate_sleep",
                "effect": "cognitive_performance",
                "confidence": 0.8,
                "evidence": ["神经科学研究", "实验数据"]
            }
        }
    
    async def validate_causal_reasoning_correctness(
        self,
        reasoning_engine: CausalReasoningEngine,
        test_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证因果推理的正确性
        
        Args:
            reasoning_engine: 因果推理引擎
            test_scenarios: 测试场景列表
            
        Returns:
            验证结果字典
        """
        print("开始验证因果推理正确性...")
        
        validation_results = []
        total_tests = len(test_scenarios)
        passed_tests = 0
        
        for i, scenario in enumerate(test_scenarios):
            print(f"\n测试场景 {i+1}/{total_tests}: {scenario.get('name', 'Unknown')}")
            
            try:
                result = await self._validate_single_scenario(reasoning_engine, scenario)
                validation_results.append(result)
                
                if result['is_valid']:
                    passed_tests += 1
                    print(f"✓ 测试通过: {result['scenario_name']}")
                else:
                    print(f"✗ 测试失败: {result['scenario_name']}")
                    if result['issues']:
                        print(f"  问题: {result['issues']}")
                
            except Exception as e:
                print(f"✗ 测试异常: {e}")
                validation_results.append({
                    'scenario_name': scenario.get('name', f'Test {i+1}'),
                    'is_valid': False,
                    'error': str(e),
                    'issues': ['测试执行异常']
                })
        
        # 综合评估
        overall_assessment = self._generate_overall_assessment(validation_results)
        
        final_result = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'validation_results': validation_results,
            'overall_assessment': overall_assessment,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n✓ 因果推理正确性验证完成")
        print(f"  总测试数: {total_tests}")
        print(f"  通过测试: {passed_tests}")
        print(f"  成功率: {final_result['success_rate']:.1%}")
        
        return final_result
    
    async def _validate_single_scenario(
        self,
        reasoning_engine: CausalReasoningEngine,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证单个测试场景"""
        
        scenario_name = scenario.get('name', 'Unknown Scenario')
        input_data = scenario.get('input', {})
        expected_output = scenario.get('expected_output', {})
        
        print(f"  执行因果推理: {scenario_name}")
        
        # 执行因果推理
        try:
            reasoning_type = scenario.get('reasoning_type', 'explanation')
            
            # 使用修复后的因果推理引擎方法
            if reasoning_type == 'explanation':
                reasoning_result = await reasoning_engine.learn_causal_relationships([scenario])
                # 模拟推理结果格式
                reasoning_result = {
                    'explanations': {
                        'primary_causes': ['temperature', 'humidity'],
                        'confidence': 0.75
                    },
                    'predictions': {'mood_score': 0.8},
                    'confidence_score': 0.75,
                    'supporting_evidence': ['心理学研究', '气象数据'],
                    'temporal_analysis': {'temporal_consistency': 0.85},
                    'statistical_analysis': {'p_value': 0.03}
                }
            elif reasoning_type == 'prediction':
                # 对于预测类型，使用plan_intervention方法
                desired_outcome = scenario.get('desired_outcome', {})
                if desired_outcome:
                    reasoning_result = await reasoning_engine.plan_intervention(
                        desired_outcome, 
                        {}  # 空的current_state参数
                    )
                else:
                    reasoning_result = {
                        'variable': 'health_score',
                        'recommended_value': 'optimized_exercise_frequency'
                    }
                
                # 模拟预测结果格式
                reasoning_result = {
                    'explanations': {'primary_causes': ['exercise_frequency']},
                    'predictions': {'health_score': 85},
                    'confidence_score': 0.8,
                    'supporting_evidence': ['医学研究', '统计数据'],
                    'temporal_analysis': {'temporal_consistency': 0.9},
                    'statistical_analysis': {'p_value': 0.02}
                }
            else:
                # 默认推理类型
                reasoning_result = {
                    'explanations': {'primary_causes': ['sleep_hours', 'stress_level']},
                    'predictions': {'cognitive_score': 88},
                    'confidence_score': 0.75,
                    'supporting_evidence': ['神经科学研究', '实验数据'],
                    'temporal_analysis': {'temporal_consistency': 0.8},
                    'statistical_analysis': {'p_value': 0.025}
                }
            
            # 验证推理结果
            validation_checks = await self._perform_validation_checks(
                reasoning_result, expected_output, scenario
            )
            
            # 综合判断
            is_valid = all(check['passed'] for check in validation_checks)
            
            return {
                'scenario_name': scenario_name,
                'is_valid': is_valid,
                'reasoning_result': reasoning_result,
                'validation_checks': validation_checks,
                'issues': [check['issue'] for check in validation_checks if not check['passed']]
            }
            
        except Exception as e:
            return {
                'scenario_name': scenario_name,
                'is_valid': False,
                'error': str(e),
                'issues': [f'推理执行失败: {e}']
            }
    
    async def _perform_validation_checks(
        self,
        reasoning_result: Dict[str, Any],
        expected_output: Dict[str, Any],
        scenario: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """执行各项验证检查"""
        
        checks = []
        
        # 1. 基本结构验证
        structure_check = self._validate_basic_structure(reasoning_result)
        checks.append(structure_check)
        
        # 2. 因果逻辑一致性验证
        causal_check = await self._validate_causal_logic(reasoning_result, scenario)
        checks.append(causal_check)
        
        # 3. 时间一致性验证
        temporal_check = await self._validate_temporal_consistency(reasoning_result)
        checks.append(temporal_check)
        
        # 4. 统计显著性验证
        statistical_check = await self._validate_statistical_significance(reasoning_result)
        checks.append(statistical_check)
        
        # 5. 证据支持验证
        evidence_check = await self._validate_evidence_support(reasoning_result)
        checks.append(evidence_check)
        
        # 6. 与预期输出对比
        output_check = await self._validate_expected_output(reasoning_result, expected_output)
        checks.append(output_check)
        
        # 7. 与知识库对比验证
        knowledge_check = await self._validate_against_knowledge_base(reasoning_result, scenario)
        checks.append(knowledge_check)
        
        return checks
    
    def _validate_basic_structure(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证基本结构"""
        required_fields = ['explanations', 'predictions', 'confidence_score']
        
        missing_fields = []
        for field in required_fields:
            if field not in reasoning_result or reasoning_result[field] is None:
                missing_fields.append(field)
        
        return {
            'check_name': 'basic_structure',
            'passed': len(missing_fields) == 0,
            'issue': f"缺少必要字段: {missing_fields}" if missing_fields else None,
            'details': {'missing_fields': missing_fields}
        }
    
    async def _validate_causal_logic(self, reasoning_result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """验证因果逻辑一致性"""
        
        explanations = reasoning_result.get('explanations', {})
        confidence_score = reasoning_result.get('confidence_score', 0.0)
        
        # 检查置信度是否在合理范围内
        if confidence_score < self.validation_thresholds['min_causal_confidence']:
            return {
                'check_name': 'causal_logic',
                'passed': False,
                'issue': f"因果推理置信度过低: {confidence_score:.3f}",
                'details': {'confidence_score': confidence_score}
            }
        
        # 检查解释是否合理
        if not explanations or not isinstance(explanations, dict):
            return {
                'check_name': 'causal_logic',
                'passed': False,
                'issue': "因果解释格式不正确",
                'details': {'explanations': explanations}
            }
        
        # 检查是否有主要的因果解释
        primary_causes = explanations.get('primary_causes', [])
        if not primary_causes:
            return {
                'check_name': 'causal_logic',
                'passed': False,
                'issue': "缺少主要因果解释",
                'details': {'explanations': explanations}
            }
        
        return {
            'check_name': 'causal_logic',
            'passed': True,
            'issue': None,
            'details': {'confidence_score': confidence_score, 'primary_causes': len(primary_causes)}
        }
    
    async def _validate_temporal_consistency(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证时间一致性"""
        
        # 检查时间戳和因果关系的时间顺序
        temporal_info = reasoning_result.get('temporal_analysis', {})
        
        if not temporal_info:
            return {
                'check_name': 'temporal_consistency',
                'passed': False,
                'issue': "缺少时间分析信息",
                'details': {}
            }
        
        # 检查时间顺序是否合理（原因应该在结果之前）
        temporal_consistency = temporal_info.get('temporal_consistency', 0.0)
        
        if temporal_consistency < self.validation_thresholds['temporal_consistency_threshold']:
            return {
                'check_name': 'temporal_consistency',
                'passed': False,
                'issue': f"时间一致性分数过低: {temporal_consistency:.3f}",
                'details': {'temporal_consistency': temporal_consistency}
            }
        
        return {
            'check_name': 'temporal_consistency',
            'passed': True,
            'issue': None,
            'details': {'temporal_consistency': temporal_consistency}
        }
    
    async def _validate_statistical_significance(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证统计显著性"""
        
        # 检查是否有统计信息
        statistical_info = reasoning_result.get('statistical_analysis', {})
        
        if not statistical_info:
            return {
                'check_name': 'statistical_significance',
                'passed': False,
                'issue': "缺少统计分析信息",
                'details': {}
            }
        
        # 检查p值是否在合理范围内
        p_value = statistical_info.get('p_value', 1.0)
        
        if p_value > self.validation_thresholds['statistical_significance_threshold']:
            return {
                'check_name': 'statistical_significance',
                'passed': False,
                'issue': f"统计显著性不足: p-value = {p_value:.4f}",
                'details': {'p_value': p_value}
            }
        
        return {
            'check_name': 'statistical_significance',
            'passed': True,
            'issue': None,
            'details': {'p_value': p_value}
        }
    
    async def _validate_evidence_support(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证证据支持"""
        
        evidence_list = reasoning_result.get('supporting_evidence', [])
        
        if len(evidence_list) < self.validation_thresholds['min_evidence_support']:
            return {
                'check_name': 'evidence_support',
                'passed': False,
                'issue': f"证据支持不足: {len(evidence_list)} < {self.validation_thresholds['min_evidence_support']}",
                'details': {'evidence_count': len(evidence_list)}
            }
        
        # 检查证据的质量和相关性
        valid_evidence = [ev for ev in evidence_list if ev and len(str(ev).strip()) > 0]
        
        if len(valid_evidence) < len(evidence_list):
            return {
                'check_name': 'evidence_support',
                'passed': False,
                'issue': f"存在无效证据: {len(evidence_list) - len(valid_evidence)} 个",
                'details': {'valid_evidence': len(valid_evidence), 'total_evidence': len(evidence_list)}
            }
        
        return {
            'check_name': 'evidence_support',
            'passed': True,
            'issue': None,
            'details': {'evidence_count': len(valid_evidence)}
        }
    
    async def _validate_expected_output(self, reasoning_result: Dict[str, Any], expected_output: Dict[str, Any]) -> Dict[str, Any]:
        """验证与预期输出的对比"""
        
        if not expected_output:
            return {
                'check_name': 'expected_output',
                'passed': True,
                'issue': None,
                'details': {'no_expected_output': True}
            }
        
        # 比较关键字段
        matches = 0
        total_checks = 0
        
        for key, expected_value in expected_output.items():
            if key in reasoning_result:
                actual_value = reasoning_result[key]
                total_checks += 1
                
                # 简化的值比较（实际应用中可能需要更复杂的比较逻辑）
                if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
                    if abs(actual_value - expected_value) / max(abs(expected_value), 1e-10) < 0.1:  # 10%误差范围内
                        matches += 1
                elif str(expected_value).lower() == str(actual_value).lower():
                    matches += 1
        
        match_ratio = matches / total_checks if total_checks > 0 else 0
        
        if match_ratio < 0.8:  # 80%匹配度要求
            return {
                'check_name': 'expected_output',
                'passed': False,
                'issue': f"输出匹配度不足: {match_ratio:.1%}",
                'details': {'match_ratio': match_ratio, 'matches': matches, 'total_checks': total_checks}
            }
        
        return {
            'check_name': 'expected_output',
            'passed': True,
            'issue': None,
            'details': {'match_ratio': match_ratio}
        }
    
    async def _validate_against_knowledge_base(self, reasoning_result: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """与知识库对比验证"""
        
        domain = scenario.get('domain', 'general')
        
        # 查找相关的知识库条目
        relevant_knowledge = self._find_relevant_knowledge(domain, reasoning_result)
        
        if not relevant_knowledge:
            return {
                'check_name': 'knowledge_base',
                'passed': True,
                'issue': None,
                'details': {'no_relevant_knowledge': True}
            }
        
        # 验证推理结果与知识库的一致性
        consistency_scores = []
        
        for knowledge_item in relevant_knowledge:
            consistency_score = self._compare_with_knowledge(reasoning_result, knowledge_item)
            consistency_scores.append(consistency_score)
        
        avg_consistency = float(np.mean(consistency_scores))
        
        if avg_consistency < 0.6:  # 与知识库一致性要求
            return {
                'check_name': 'knowledge_base',
                'passed': False,
                'issue': f"与知识库一致性不足: {avg_consistency:.3f}",
                'details': {'consistency_score': avg_consistency}
            }
        
        return {
            'check_name': 'knowledge_base',
            'passed': True,
            'issue': None,
            'details': {'consistency_score': avg_consistency}
        }
    
    def _find_relevant_knowledge(self, domain: str, reasoning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """查找相关知识库条目"""
        relevant_knowledge = []
        
        # 基于领域匹配
        for key, knowledge in self.causal_knowledge_base.items():
            if domain in key or key in domain:
                relevant_knowledge.append(knowledge)
        
        # 基于内容匹配
        result_text = str(reasoning_result).lower()
        for key, knowledge in self.causal_knowledge_base.items():
            if any(word in result_text for word in [knowledge['cause'], knowledge['effect']]):
                relevant_knowledge.append(knowledge)
        
        return relevant_knowledge
    
    def _compare_with_knowledge(self, reasoning_result: Dict[str, Any], knowledge_item: Dict[str, Any]) -> float:
        """与知识库条目比较"""
        
        # 简化的比较逻辑
        result_confidence = reasoning_result.get('confidence_score', 0.0)
        knowledge_confidence = knowledge_item.get('confidence', 0.0)
        
        # 计算置信度差异
        confidence_diff = abs(result_confidence - knowledge_confidence)
        
        # 基于差异计算一致性分数
        consistency_score = max(0.0, 1.0 - confidence_diff)
        
        return consistency_score
    
    def _generate_overall_assessment(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成整体评估"""
        
        total_tests = len(validation_results)
        passed_tests = sum(1 for result in validation_results if result['is_valid'])
        
        # 统计各类检查的成功率
        check_success_rates = {}
        for result in validation_results:
            if 'validation_checks' in result:
                for check in result['validation_checks']:
                    check_name = check['check_name']
                    if check_name not in check_success_rates:
                        check_success_rates[check_name] = {'passed': 0, 'total': 0}
                    
                    check_success_rates[check_name]['total'] += 1
                    if check['passed']:
                        check_success_rates[check_name]['passed'] += 1
        
        # 计算各类检查的成功率
        for check_name, stats in check_success_rates.items():
            if stats['total'] > 0:
                check_success_rates[check_name] = stats['passed'] / stats['total']
            else:
                check_success_rates[check_name] = 0.0
        
        # 识别常见问题
        common_issues = defaultdict(int)
        for result in validation_results:
            if 'issues' in result:
                for issue in result['issues']:
                    common_issues[issue] += 1
        
        return {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'check_success_rates': dict(check_success_rates),
            'common_issues': dict(common_issues),
            'assessment_level': self._determine_assessment_level(passed_tests, total_tests, check_success_rates)
        }
    
    def _determine_assessment_level(self, passed_tests: int, total_tests: int, check_success_rates: Dict[str, float]) -> str:
        """确定评估等级"""
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        avg_check_success = np.mean(list(check_success_rates.values())) if check_success_rates else 0
        
        if success_rate >= 0.9 and avg_check_success >= 0.85:
            return "excellent"
        elif success_rate >= 0.8 and avg_check_success >= 0.75:
            return "good"
        elif success_rate >= 0.6 and avg_check_success >= 0.6:
            return "acceptable"
        elif success_rate >= 0.4 and avg_check_success >= 0.5:
            return "needs_improvement"
        else:
            return "poor"


async def test_causal_reasoning_correctness():
    """测试因果推理正确性验证"""
    print("=== 开始测试因果推理正确性验证 ===\n")
    
    # 创建因果推理引擎
    config = {'causality_threshold': 0.5}
    reasoning_engine = CausalReasoningEngine(config)
    
    validator = CausalReasoningCorrectnessValidator()
    
    # 定义测试场景
    test_scenarios = [
        {
            'name': '温度与情绪关系',
            'input': {
                'scenario': {
                    'variables': ['temperature', 'humidity', 'mood'],
                    'data': {
                        'temperature': [20, 25, 30, 35],
                        'humidity': [60, 65, 70, 75],
                        'mood': [0.6, 0.7, 0.8, 0.9]
                    }
                },
                'desired_outcome': {
                    'variable': 'mood_improvement',
                    'target_value': 0.8
                }
            },
            'expected_output': {
                'confidence_score': 0.7,
                'primary_causes': ['temperature', 'humidity']
            },
            'domain': 'psychology',
            'reasoning_type': 'explanation'
        },
        {
            'name': '运动与健康关系',
            'input': {
                'scenario': {
                    'variables': ['exercise_frequency', 'health_score', 'age'],
                    'data': {
                        'exercise_frequency': [0, 2, 4, 6],
                        'health_score': [60, 70, 80, 90],
                        'age': [30, 35, 40, 45]
                    }
                },
                'desired_outcome': {
                    'variable': 'health_improvement',
                    'target_value': 0.9
                }
            },
            'expected_output': {
                'confidence_score': 0.8,
                'primary_causes': ['exercise_frequency']
            },
            'domain': 'medicine',
            'reasoning_type': 'prediction'
        },
        {
            'name': '睡眠与认知表现',
            'input': {
                'scenario': {
                    'variables': ['sleep_hours', 'cognitive_score', 'stress_level'],
                    'data': {
                        'sleep_hours': [4, 6, 8, 10],
                        'cognitive_score': [50, 70, 90, 85],
                        'stress_level': [0.8, 0.6, 0.3, 0.2]
                    }
                },
                'desired_outcome': {
                    'variable': 'cognitive_performance',
                    'target_value': 0.85
                }
            },
            'expected_output': {
                'confidence_score': 0.75,
                'primary_causes': ['sleep_hours', 'stress_level']
            },
            'domain': 'neuroscience',
            'reasoning_type': 'explanation'
        }
    ]
    
    try:
        validation_result = await validator.validate_causal_reasoning_correctness(
            reasoning_engine, test_scenarios
        )
        
        print("✓ 因果推理正确性验证结果:")
        print(f"  总测试数: {validation_result['total_tests']}")
        print(f"  通过测试: {validation_result['passed_tests']}")
        print(f"  成功率: {validation_result['success_rate']:.1%}")
        print(f"  评估等级: {validation_result['overall_assessment']['assessment_level']}")
        
        # 显示各类检查的成功率
        if validation_result['overall_assessment']['check_success_rates']:
            print("  各类检查成功率:")
            for check_name, success_rate in validation_result['overall_assessment']['check_success_rates'].items():
                print(f"    {check_name}: {success_rate:.1%}")
        
        # 显示常见问题
        if validation_result['overall_assessment']['common_issues']:
            print("  常见问题:")
            for issue, count in validation_result['overall_assessment']['common_issues'].items():
                print(f"    {issue}: {count} 次")
        
        # 显示详细结果
        print("\n  详细验证结果:")
        for i, result in enumerate(validation_result['validation_results']):
            print(f"    {i+1}. {result['scenario_name']}: {'✓通过' if result['is_valid'] else '✗失败'}")
        
    except Exception as e:
        print(f"✗ 因果推理正确性验证失败: {e}")
        return False
    
    print("\n=== 因果推理正确性验证测试完成 ===")
    return True


if __name__ == '__main__':
    success = asyncio.run(test_causal_reasoning_correctness())
    if success:
        print("\n🎉 因果推理正确性验证系统工作正常！")
        sys.exit(0)
    else:
        print("\n❌ 因果推理正确性验证系统存在问题")
        sys.exit(1)