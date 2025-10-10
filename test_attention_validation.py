#!/usr/bin/env python3
"""
注意力机制验证器
验证注意力权重的正确性和合理性
"""

import sys
sys.path.append('apps/backend/src')

import numpy as np
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AttentionValidationResult:
    """注意力验证结果"""
    is_valid: bool
    attention_entropy: float
    attention_variance: float
    max_attention_weight: float
    min_attention_weight: float
    attention_concentration: float
    validation_score: float
    issues: List[str]

class AttentionMechanismValidator:
    """注意力机制验证器"""
    
    def __init__(self):
        self.validation_thresholds = {
            'max_entropy': 3.0,           # 最大熵值
            'min_entropy': 0.1,           # 最小熵值
            'max_variance': 0.15,         # 最大方差
            'min_max_attention': 0.1,     # 最大注意力权重的最小值
            'max_concentration': 0.8,     # 最大集中度
            'min_validation_score': 0.6   # 最小验证分数
        }
    
    def validate_attention_weights(
        self,
        attention_weights: np.ndarray,
        tokens: List[str],
        layer_info: Optional[Dict[str, Any]] = None
    ) -> AttentionValidationResult:
        """
        验证注意力权重
        
        Args:
            attention_weights: 注意力权重矩阵 [num_heads, seq_len, seq_len]
            tokens: token列表
            layer_info: 层信息
            
        Returns:
            验证结果
        """
        print(f"开始验证注意力权重，权重形状: {attention_weights.shape}")
        
        issues = []
        
        # 基本检查
        if attention_weights.size == 0:
            issues.append("注意力权重为空")
            return AttentionValidationResult(
                is_valid=False,
                attention_entropy=0.0,
                attention_variance=0.0,
                max_attention_weight=0.0,
                min_attention_weight=0.0,
                attention_concentration=0.0,
                validation_score=0.0,
                issues=issues
            )
        
        # 检查权重范围
        if np.any(attention_weights < 0):
            issues.append("存在负的注意力权重")
        
        if np.any(attention_weights > 1):
            issues.append("注意力权重大于1")
        
        # 检查权重和是否为1（归一化检查）
        weight_sums = np.sum(attention_weights, axis=-1)
        if not np.allclose(weight_sums, 1.0, atol=1e-6):
            issues.append("注意力权重未正确归一化")
        
        # 计算注意力统计特征
        attention_entropy = self._calculate_attention_entropy(attention_weights)
        attention_variance = self._calculate_attention_variance(attention_weights)
        max_attention_weight = np.max(attention_weights)
        min_attention_weight = np.min(attention_weights)
        attention_concentration = self._calculate_attention_concentration(attention_weights)
        
        # 验证各个指标
        validation_score = self._calculate_validation_score(
            attention_entropy, attention_variance, max_attention_weight, 
            min_attention_weight, attention_concentration, issues
        )
        
        # 判断整体有效性
        is_valid = (
            validation_score >= self.validation_thresholds['min_validation_score'] and
            len(issues) == 0  # 没有严重问题
        )
        
        result = AttentionValidationResult(
            is_valid=is_valid,
            attention_entropy=attention_entropy,
            attention_variance=attention_variance,
            max_attention_weight=max_attention_weight,
            min_attention_weight=min_attention_weight,
            attention_concentration=attention_concentration,
            validation_score=validation_score,
            issues=issues
        )
        
        print(f"✓ 注意力验证完成，有效性: {is_valid}, 验证分数: {validation_score:.3f}")
        if issues:
            print(f"  发现的问题: {issues}")
        
        return result
    
    def _calculate_attention_entropy(self, attention_weights: np.ndarray) -> float:
        """计算注意力熵"""
        # 避免log(0)
        weights_clipped = np.clip(attention_weights, 1e-10, 1.0)
        
        # 计算每个位置的熵
        entropy_per_position = -np.sum(weights_clipped * np.log(weights_clipped), axis=-1)
        
        # 返回平均熵
        return float(np.mean(entropy_per_position))
    
    def _calculate_attention_variance(self, attention_weights: np.ndarray) -> float:
        """计算注意力方差"""
        return float(np.var(attention_weights))
    
    def _calculate_attention_concentration(self, attention_weights: np.ndarray) -> float:
        """计算注意力集中度"""
        # 计算每个位置的最大注意力权重
        max_weights_per_position = np.max(attention_weights, axis=-1)
        
        # 返回平均最大权重作为集中度指标
        return float(np.mean(max_weights_per_position))
    
    def _calculate_validation_score(
        self,
        entropy: float,
        variance: float,
        max_weight: float,
        min_weight: float,
        concentration: float,
        issues: List[str]
    ) -> float:
        """计算验证分数"""
        
        # 熵值评分（适中为好）
        if entropy < self.validation_thresholds['min_entropy']:
            entropy_score = 0.3
        elif entropy > self.validation_thresholds['max_entropy']:
            entropy_score = 0.5
        else:
            entropy_score = 1.0
        
        # 方差评分（越小越好）
        if variance > self.validation_thresholds['max_variance']:
            variance_score = 0.3
        else:
            variance_score = 1.0 - (variance / self.validation_thresholds['max_variance'])
        
        # 最大权重评分（不能太小也不能太大）
        if max_weight < self.validation_thresholds['min_max_attention']:
            max_weight_score = 0.2
        elif max_weight > 0.9:  # 过于集中
            max_weight_score = 0.6
        else:
            max_weight_score = 0.8
        
        # 集中度评分（适中为好）
        if concentration > self.validation_thresholds['max_concentration']:
            concentration_score = 0.3
        else:
            concentration_score = 1.0 - (concentration / self.validation_thresholds['max_concentration'])
        
        # 综合分数
        base_score = (
            entropy_score * 0.3 +
            variance_score * 0.25 +
            max_weight_score * 0.25 +
            concentration_score * 0.2
        )
        
        # 根据问题数量调整分数
        issue_penalty = len(issues) * 0.2
        final_score = max(0.0, base_score - issue_penalty)
        
        return final_score
    
    def analyze_attention_patterns(
        self,
        attention_weights: np.ndarray,
        tokens: List[str],
        layer_idx: int = 0
    ) -> Dict[str, Any]:
        """分析注意力模式"""
        print(f"分析第{layer_idx}层注意力模式...")
        
        num_heads, seq_len, _ = attention_weights.shape
        
        # 计算各种注意力模式指标
        patterns = {
            "layer_index": layer_idx,
            "num_heads": num_heads,
            "sequence_length": seq_len,
            "attention_heads_analysis": []
        }
        
        for head_idx in range(num_heads):
            head_weights = attention_weights[head_idx]
            
            # 计算该注意力头的统计特征
            head_entropy = self._calculate_attention_entropy(head_weights[np.newaxis, :, :])
            head_variance = self._calculate_attention_variance(head_weights[np.newaxis, :, :])
            head_concentration = self._calculate_attention_concentration(head_weights[np.newaxis, :, :])
            
            # 判断注意力头类型
            if head_concentration > 0.8:
                head_type = "highly_concentrated"
            elif head_entropy < 1.0:
                head_type = "focused"
            elif head_entropy > 2.5:
                head_type = "dispersed"
            else:
                head_type = "balanced"
            
            patterns["attention_heads_analysis"].append({
                "head_index": head_idx,
                "entropy": head_entropy,
                "variance": head_variance,
                "concentration": head_concentration,
                "head_type": head_type,
                "is_valid": head_entropy >= self.validation_thresholds['min_entropy'] and
                           head_variance <= self.validation_thresholds['max_variance']
            })
        
        # 整体模式分析
        entropies = [head["entropy"] for head in patterns["attention_heads_analysis"]]
        variances = [head["variance"] for head in patterns["attention_heads_analysis"]]
        
        patterns["overall_analysis"] = {
            "average_entropy": float(np.mean(entropies)),
            "entropy_std": float(np.std(entropies)),
            "average_variance": float(np.mean(variances)),
            "variance_std": float(np.std(variances)),
            "valid_heads_ratio": sum(1 for head in patterns["attention_heads_analysis"] if head["is_valid"]) / num_heads
        }
        
        return patterns
    
    def detect_attention_anomalies(
        self,
        attention_weights: np.ndarray,
        tokens: List[str]
    ) -> List[Dict[str, Any]]:
        """检测注意力异常"""
        anomalies = []
        
        num_heads, seq_len, _ = attention_weights.shape
        
        for head_idx in range(num_heads):
            head_weights = attention_weights[head_idx]
            
            # 检查异常模式
            if np.allclose(head_weights, 1.0 / seq_len):
                anomalies.append({
                    "type": "uniform_attention",
                    "head_index": head_idx,
                    "description": "注意力权重完全均匀分布",
                    "severity": "medium"
                })
            
            # 检查是否有过高的注意力权重
            max_attention = np.max(head_weights)
            if max_attention > 0.95:
                max_positions = np.where(head_weights == max_attention)
                anomalies.append({
                    "type": "excessive_attention",
                    "head_index": head_idx,
                    "description": f"注意力权重过高 ({max_attention:.3f})",
                    "max_positions": list(zip(max_positions[0], max_positions[1])),
                    "severity": "high"
                })
            
            # 检查是否有过低的注意力权重
            min_attention = np.min(head_weights)
            if min_attention < 0.01:
                anomalies.append({
                    "type": "insufficient_attention",
                    "head_index": head_idx,
                    "description": f"注意力权重过低 ({min_attention:.3f})",
                    "severity": "medium"
                })
        
        return anomalies


async def test_attention_mechanism_validation():
    """测试注意力机制验证"""
    print("=== 开始测试注意力机制验证 ===\n")
    
    validator = AttentionMechanismValidator()
    
    # 测试1: 正常的注意力权重
    print("--- 测试1: 正常注意力权重 ---")
    normal_weights = np.array([
        [[0.1, 0.2, 0.3, 0.4],
         [0.15, 0.25, 0.35, 0.25],
         [0.2, 0.2, 0.3, 0.3],
         [0.25, 0.25, 0.25, 0.25]]
    ])
    tokens = ["The", "cat", "sat", "mat"]
    
    result = validator.validate_attention_weights(normal_weights, tokens)
    print(f"✓ 正常权重验证结果: 有效性={result.is_valid}, 分数={result.validation_score:.3f}")
    print(f"  熵值: {result.attention_entropy:.3f}, 方差: {result.attention_variance:.3f}")
    print(f"  最大权重: {result.max_attention_weight:.3f}, 集中度: {result.attention_concentration:.3f}")
    
    # 测试2: 过度集中的注意力
    print("\n--- 测试2: 过度集中的注意力 ---")
    concentrated_weights = np.array([
        [[0.01, 0.01, 0.95, 0.03],
         [0.02, 0.02, 0.94, 0.02],
         [0.01, 0.01, 0.96, 0.02],
         [0.02, 0.02, 0.94, 0.02]]
    ])
    
    result = validator.validate_attention_weights(concentrated_weights, tokens)
    print(f"✓ 集中权重验证结果: 有效性={result.is_valid}, 分数={result.validation_score:.3f}")
    if result.issues:
        print(f"  问题: {result.issues}")
    
    # 测试3: 注意力模式分析
    print("\n--- 测试3: 注意力模式分析 ---")
    multi_head_weights = np.random.dirichlet(np.ones(4), size=(4, 4))  # 随机但有效的注意力权重
    
    patterns = validator.analyze_attention_patterns(multi_head_weights, tokens)
    print(f"✓ 分析了 {patterns['num_heads']} 个注意力头")
    print(f"✓ 平均熵值: {patterns['overall_analysis']['average_entropy']:.3f}")
    print(f"✓ 有效注意力头比例: {patterns['overall_analysis']['valid_heads_ratio']:.1%}")
    
    # 测试4: 异常检测
    print("\n--- 测试4: 异常检测 ---")
    # 创建有异常的注意力权重
    anomalous_weights = np.array([
        [[0.25, 0.25, 0.25, 0.25],  # 正常
         [0.99, 0.003, 0.003, 0.004],  # 过度集中
         [0.0, 0.0, 0.0, 1.0],  # 完全集中
         [0.25, 0.25, 0.25, 0.25]]  # 正常
    ])
    
    anomalies = validator.detect_attention_anomalies(anomalous_weights, tokens)
    print(f"✓ 检测到 {len(anomalies)} 个异常")
    for anomaly in anomalies:
        print(f"  异常类型: {anomaly['type']}, 严重程度: {anomaly['severity']}")
    
    print("\n=== 注意力机制验证测试完成 ===")
    return True


if __name__ == '__main__':
    success = asyncio.run(test_attention_mechanism_validation())
    if success:
        print("\n🎉 注意力机制验证系统工作正常！")
        sys.exit(0)
    else:
        print("\n❌ 注意力机制验证系统存在问题")
        sys.exit(1)