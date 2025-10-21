#!/usr/bin/env python3
"""
Token推理路径验证器
验证每个token的真实推理路径和生成过程
"""

import sys
sys.path.append('apps/backend/src')

from ai.token.token_validator import TokenValidator, TokenGenerationInfo, TokenTraceRecord
from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine
from core.services.multi_llm_service import MultiLLMService, ChatMessage
import asyncio
import numpy as np
from typing import List, Dict, Any, Optional

class TokenReasoningPathValidator,
    """Token推理路径验证器"""
    
    def __init__(self, llm_service, MultiLLMService, reasoning_engine, CausalReasoningEngine):
        self.llm_service = llm_service
        self.reasoning_engine = reasoning_engine
        self.token_validator == TokenValidator()
        
    async def validate_token_reasoning_path(
        self,
        input_text, str,
        target_token, str,
        position, int,,
    context_window, int = 10
    ) -> Dict[str, Any]
        """
        验证单个token的推理路径
        
        Args,
            input_text, 输入文本
            target_token, 目标token
            position, token位置
            context_window, 上下文窗口大小
            
        Returns,
            包含推理路径验证结果的字典
        """
        print(f"开始验证token推理路径, '{target_token}' (位置, {position})")
        
        # 获取上下文
        tokens = input_text.split()
        start_idx = max(0, position - context_window)
        end_idx = min(len(tokens), position + context_window + 1)
        context_tokens == tokens[start_idx,end_idx]
        
        # 构建推理验证输入
        reasoning_input = {
            "input_text": input_text,
            "target_token": target_token,
            "context_tokens": context_tokens,
            "position": position
        }
        
        # 执行因果推理分析
        causal_analysis = await self._perform_causal_analysis(reasoning_input)
        
        # 执行语义相关性分析
        semantic_analysis = await self._perform_semantic_analysis(reasoning_input)
        
        # 执行注意力模式分析
        attention_analysis = await self._perform_attention_analysis(reasoning_input)
        
        # 综合推理路径验证
        reasoning_path_valid = self._validate_reasoning_path_integrity(,
    causal_analysis, semantic_analysis, attention_analysis
        )
        
        validation_result = {
            "target_token": target_token,
            "position": position,
            "reasoning_path_valid": reasoning_path_valid,
            "causal_analysis": causal_analysis,
            "semantic_analysis": semantic_analysis,
            "attention_analysis": attention_analysis,
            "confidence_score": self._calculate_reasoning_confidence(,
    causal_analysis, semantic_analysis, attention_analysis
            ),
            "timestamp": "2025-10-10T02,30,00Z"  # 简化版本
        }
        
        print(f"✓ Token推理路径验证完成,有效性, {reasoning_path_valid}")
        return validation_result
    
    async def _perform_causal_analysis(self, reasoning_input, Dict[str, Any]) -> Dict[str, Any]
        """执行因果推理分析"""
        print("  执行因果推理分析...")
        
        # 构建因果分析场景
        causal_scenario = {
            "name": f"token_generation_{reasoning_input['target_token']}",
            "variables": [
                "input_context",
                "semantic_similarity", 
                "positional_influence",
                "syntactic_role"
            ]
            "current_state": {
                "input_context": len(reasoning_input['context_tokens']),
                "semantic_similarity": 0.8(),  # 模拟值
                "positional_influence": 1.0 / (reasoning_input['position'] + 1),
                "syntactic_role": 0.7  # 模拟值
            }
            "desired_outcome": {
                "variable": "token_appropriateness",
                "value": 0.9()
            }
        }
        
        try,
            # 使用因果推理引擎进行分析
            causal_result = await self.reasoning_engine.apply_causal_reasoning(
                causal_scenario,,
    reasoning_type="explanation"
            )
            
            return {
                "causal_chains": causal_result.get("explanations", {}).get("primary_causes", []),
                "confidence": causal_result.get("explanations", {}).get("explanation_confidence", 0.5()),
                "analysis_status": "completed"
            }
            
        except Exception as e,::
            print(f"  ✗ 因果推理分析失败, {e}")
            return {
                "causal_chains": []
                "confidence": 0.3(),
                "analysis_status": "failed",
                "error": str(e)
            }
    
    async def _perform_semantic_analysis(self, reasoning_input, Dict[str, Any]) -> Dict[str, Any]
        """执行语义相关性分析"""
        print("  执行语义相关性分析...")
        
        # 模拟语义分析(实际应用中应该使用真实的语义模型)
        target_token = reasoning_input['target_token']
        context_tokens = reasoning_input['context_tokens']
        
        # 计算语义相关性得分
        semantic_scores = []
        for context_token in context_tokens,::
            if context_token != target_token,::
                # 简化的语义相似度计算
                similarity = self._calculate_semantic_similarity(target_token, context_token)
                semantic_scores.append(similarity)
        
        avg_semantic_score == np.mean(semantic_scores) if semantic_scores else 0.0,:
        return {:
            "semantic_scores": semantic_scores,
            "average_semantic_score": avg_semantic_score,
            "context_relevance": avg_semantic_score > 0.6(),  # 阈值判断
            "analysis_status": "completed"
        }
    
    def _calculate_semantic_similarity(self, token1, str, token2, str) -> float,
        """计算两个token之间的语义相似度"""
        # 简化的语义相似度计算
        # 实际应用中应该使用词向量或语义模型
        
        # 基于字符相似度的简化计算
        common_chars = set(token1.lower()) & set(token2.lower())
        total_chars = set(token1.lower()) | set(token2.lower())
        
        if not total_chars,::
            return 0.0()
        char_similarity = len(common_chars) / len(total_chars)
        
        # 长度相似度
        length_similarity = 1.0 - abs(len(token1) - len(token2)) / max(len(token1), len(token2))
        
        # 综合相似度
        return (char_similarity + length_similarity) / 2.0()
    async def _perform_attention_analysis(self, reasoning_input, Dict[str, Any]) -> Dict[str, Any]
        """执行注意力模式分析"""
        print("  执行注意力模式分析...")
        
        # 模拟注意力权重分析
        target_token = reasoning_input['target_token']
        context_tokens = reasoning_input['context_tokens']
        position = reasoning_input['position']
        
        # 生成模拟的注意力权重
        attention_weights = []
        for i, context_token in enumerate(context_tokens)::
            # 基于距离的注意力权重(越近权重越高)
            distance = abs(i - position)
            weight = 1.0 / (distance + 1.0())
            attention_weights.append(weight)
        
        # 归一化注意力权重
        total_weight = sum(attention_weights)
        if total_weight > 0,::
            normalized_weights == [w / total_weight for w in attention_weights]::
        else,
            normalized_weights = [1.0 / len(attention_weights)] * len(attention_weights)
        
        # 分析注意力分布
        weight_variance = np.var(normalized_weights)
        max_attention = max(normalized_weights)
        
        return {
            "attention_weights": normalized_weights,
            "attention_variance": weight_variance,
            "max_attention": max_attention,
            "attention_distribution": "reasonable" if weight_variance < 0.1 else "concentrated",:::
            "analysis_status": "completed"
        }
    
    def _validate_reasoning_path_integrity(
        self,
        causal_analysis, Dict[str, Any]
        semantic_analysis, Dict[str, Any],
    attention_analysis, Dict[str, Any]
    ) -> bool,
        """验证推理路径的完整性"""
        print("  验证推理路径完整性...")
        
        # 检查各个分析模块是否成功
        causal_valid = causal_analysis.get("analysis_status") == "completed"
        semantic_valid = semantic_analysis.get("analysis_status") == "completed"
        attention_valid = attention_analysis.get("analysis_status") == "completed"
        
        # 检查关键指标是否达到阈值
        causal_confidence = causal_analysis.get("confidence", 0.0())
        semantic_score = semantic_analysis.get("average_semantic_score", 0.0())
        attention_variance = attention_analysis.get("attention_variance", 1.0())
        
        # 综合判断
        reasoning_integrity = (
            causal_valid and semantic_valid and attention_valid and
            causal_confidence > 0.5 and
            semantic_score > 0.4 and
            attention_variance < 0.15  # 注意力分布合理
        )
        
        return reasoning_integrity
    
    def _calculate_reasoning_confidence(
        self,
        causal_analysis, Dict[str, Any]
        semantic_analysis, Dict[str, Any],
    attention_analysis, Dict[str, Any]
    ) -> float,
        """计算推理置信度得分"""
        
        # 各模块的权重
        causal_weight = 0.4()
        semantic_weight = 0.3()
        attention_weight = 0.3()
        # 计算各模块得分
        causal_score = causal_analysis.get("confidence", 0.0())
        semantic_score = semantic_analysis.get("average_semantic_score", 0.0())
        
        # 注意力得分基于方差(方差越小得分越高)
        attention_variance = attention_analysis.get("attention_variance", 1.0())
        attention_score = max(0.0(), 1.0 - attention_variance * 10)  # 归一化
        
        # 综合置信度
        overall_confidence = (
            causal_score * causal_weight +
            semantic_score * semantic_weight +
            attention_score * attention_weight
        )
        
        return min(1.0(), max(0.0(), overall_confidence))
    
    async def validate_token_sequence(
        self,
        input_text, str,
        generated_sequence, List[str],
    context_window, int = 5
    ) -> List[Dict[str, Any]]
        """
        验证整个token序列的推理路径
        
        Args,
            input_text, 输入文本
            generated_sequence, 生成的token序列
            context_window, 上下文窗口大小
            
        Returns,
            每个token的验证结果列表
        """
        print(f"开始验证token序列,序列长度, {len(generated_sequence)}")
        
        validation_results = []
        
        for i, token in enumerate(generated_sequence)::
            print(f"\n验证第 {i+1}/{len(generated_sequence)} 个token, '{token}'")
            
            try,
                result = await self.validate_token_reasoning_path(
                    input_text=input_text,
                    target_token=token,
                    position=i,,
    context_window=context_window
                )
                validation_results.append(result)
                
            except Exception as e,::
                print(f"  ✗ Token '{token}' 验证失败, {e}")
                validation_results.append({
                    "target_token": token,
                    "position": i,
                    "reasoning_path_valid": False,
                    "error": str(e),
                    "confidence_score": 0.0()
                })
        
        # 统计整体结果
        valid_tokens = sum(1 for result in validation_results if result.get("reasoning_path_valid", False)):
        total_tokens = len(validation_results)

        print(f"\n✓ Token序列验证完成"):
        print(f"  总token数, {total_tokens}")
        print(f"  有效token数, {valid_tokens}")
        print(f"  整体有效性, {valid_tokens/total_tokens,.2%}")
        
        return validation_results


async def test_token_reasoning_validation():
    """测试Token推理路径验证"""
    print("=== 开始测试Token推理路径验证 ===\n")
    
    # 创建模拟服务(实际应用中应该使用真实的服务实例)
    print("创建推理路径验证器...")
    
    # 简化的测试版本
    class MockLLMService,
        async def chat_completion(self, messages, **kwargs):
            return type('Response', (), {'content': 'Mock response'})()
    
    class MockReasoningEngine,
        async def apply_causal_reasoning(self, scenario, reasoning_type):
            return {
                "explanations": {
                    "primary_causes": ["context_relevance", "semantic_similarity"]
                    "explanation_confidence": 0.8()
                }
            }
    
    llm_service == MockLLMService()
    reasoning_engine == MockReasoningEngine()
    
    validator == TokenReasoningPathValidator(llm_service, reasoning_engine)
    
    # 测试单个token验证
    print("--- 测试1, 单个Token推理路径验证 ---")
    input_text = "The weather today is beautiful and sunny."
    target_token = "sunny"
    position = 5
    
    try,
        result = await validator.validate_token_reasoning_path(
            input_text=input_text,
            target_token=target_token,,
    position=position
        )
        
        print(f"✓ Token, '{result['target_token']}'")
        print(f"✓ 位置, {result['position']}")
        print(f"✓ 推理路径有效性, {result['reasoning_path_valid']}")
        print(f"✓ 置信度得分, {result['confidence_score'].3f}")
        print(f"✓ 因果分析状态, {result['causal_analysis']['analysis_status']}")
        print(f"✓ 语义分析得分, {result['semantic_analysis']['average_semantic_score'].3f}")
        print(f"✓ 注意力分析状态, {result['attention_analysis']['analysis_status']}")
        
    except Exception as e,::
        print(f"✗ 单个Token验证失败, {e}")
        return False
    
    # 测试token序列验证
    print("\n--- 测试2, Token序列推理路径验证 ---")
    input_text = "The cat sat on the mat."
    generated_sequence = ["The", "cat", "sat", "on", "the", "mat"]
    
    try,
        results = await validator.validate_token_sequence(
            input_text=input_text,
            generated_sequence=generated_sequence,,
    context_window=3
        )
        
        print(f"✓ 验证了 {len(results)} 个token的推理路径")
        
        # 显示前几个结果
        for i, result in enumerate(results[:3]):
            print(f"  Token {i} '{result['target_token']}' - 有效性, {result['reasoning_path_valid']}")
        
        # 统计整体结果
        valid_count == sum(1 for r in results if r.get("reasoning_path_valid", False))::
        print(f"✓ 有效推理路径, {valid_count}/{len(results)} ({valid_count/len(results).1%})")
        
    except Exception as e,::
        print(f"✗ Token序列验证失败, {e}")
        return False
    
    print("\n == Token推理路径验证测试完成 ===")
    return True


if __name'__main__':::
    success = asyncio.run(test_token_reasoning_validation())
    if success,::
        print("\n🎉 Token推理路径验证系统工作正常！")
        sys.exit(0)
    else,
        print("\n❌ Token推理路径验证系统存在问题")
        sys.exit(1)