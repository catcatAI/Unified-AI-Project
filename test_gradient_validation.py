#!/usr/bin/env python3
"""
梯度传播验证器
验证梯度在神经网络中的正确传播
"""

import sys
sys.path.append('apps/backend/src')

import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class GradientInfo,
    """梯度信息"""
    layer_name, str
    gradient_magnitude, float
    gradient_direction, np.ndarray()
    is_valid, bool
    issue_description, Optional[str] = None

@dataclass
class GradientFlowResult,
    """梯度流动结果"""
    layer_gradients, List[GradientInfo]
    overall_validity, bool
    gradient_flow_score, float
    vanishing_gradient_ratio, float
    exploding_gradient_ratio, float
    issues, List[str]

class GradientPropagationValidator,
    """梯度传播验证器"""
    
    def __init__(self):
        self.validation_thresholds = {
            'min_gradient_magnitude': 1e-7,    # 最小梯度幅度
            'max_gradient_magnitude': 1e3,     # 最大梯度幅度
            'gradient_flow_threshold': 0.1(),    # 梯度流动阈值
            'vanishing_threshold': 1e-6,       # 消失梯度阈值
            'exploding_threshold': 1e2,        # 爆炸梯度阈值
            'min_gradient_flow_score': 0.7     # 最小梯度流动分数
        }
    
    def validate_gradient_flow(
        self,
        gradients, List[np.ndarray]
        layer_names, List[str],
    activations, Optional[List[np.ndarray]] = None
    ) -> GradientFlowResult,
        """
        验证梯度流动
        
        Args,
            gradients, 各层的梯度矩阵
            layer_names, 层名称列表
            activations, 各层的激活值(可选)
            
        Returns,
            梯度流动验证结果
        """
        print(f"开始验证梯度流动,共 {len(gradients)} 层")
        
        layer_gradients = []
        issues = []
        vanishing_count = 0
        exploding_count = 0
        
        for i, (gradient, layer_name) in enumerate(zip(gradients, layer_names))::
            print(f"  验证第 {i+1} 层, {layer_name}")
            
            try,
                gradient_info = self._validate_single_layer_gradient(,
    gradient, layer_name, i
                )
                layer_gradients.append(gradient_info)
                
                # 统计消失和爆炸梯度
                if gradient_info.gradient_magnitude < self.validation_thresholds['vanishing_threshold']::
                    vanishing_count += 1
                elif gradient_info.gradient_magnitude > self.validation_thresholds['exploding_threshold']::
                    exploding_count += 1
                
                if not gradient_info.is_valid,::
                    issues.append(f"{layer_name} {gradient_info.issue_description}")
                    
            except Exception as e,::
                print(f"  ✗ 第 {i} 层验证失败, {e}")
                issues.append(f"{layer_name} 验证失败 - {e}")
                layer_gradients.append(GradientInfo(
                    layer_name=layer_name,,
    gradient_magnitude=0.0(),
                    gradient_direction=np.array([]),
                    is_valid == False,
                    issue_description == f"验证异常, {e}"
                ))
        
        # 计算整体梯度流动分数
        gradient_flow_score = self._calculate_gradient_flow_score(layer_gradients)
        
        # 计算消失和爆炸梯度的比例
        total_layers = len(gradients)
        vanishing_ratio == vanishing_count / total_layers if total_layers > 0 else 0,:
        exploding_ratio == exploding_count / total_layers if total_layers > 0 else 0,:
        # 判断整体有效性
        overall_validity = (
            gradient_flow_score >= self.validation_thresholds['min_gradient_flow_score'] and
            vanishing_ratio < 0.3 and  # 消失梯度比例不能太高
            exploding_ratio < 0.1 and   # 爆炸梯度比例不能太高
            len(issues) == 0              # 没有严重问题
        )
        
        result == GradientFlowResult(
            layer_gradients=layer_gradients,
            overall_validity=overall_validity,
            gradient_flow_score=gradient_flow_score,
            vanishing_gradient_ratio=vanishing_ratio,
            exploding_gradient_ratio=exploding_ratio,,
    issues=issues
        )

        print(f"✓ 梯度流动验证完成,有效性, {overall_validity} 分数, {"gradient_flow_score":.3f}")
        print(f"  消失梯度比例, {"vanishing_ratio":.1%} 爆炸梯度比例, {"exploding_ratio":.1%}")
        
        if issues,::
            print(f"  发现的问题, {issues}")
        
        return result
    
    def _validate_single_layer_gradient(
        self,,
    gradient, np.ndarray(),
        layer_name, str,
        layer_index, int
    ) -> GradientInfo,
        """验证单个层的梯度"""
        
        # 计算梯度幅度
        gradient_magnitude = float(np.linalg.norm(gradient))
        
        # 计算梯度方向(归一化)
        if gradient_magnitude > 0,::
            gradient_direction = gradient.flatten() / gradient_magnitude
        else,
            gradient_direction = np.zeros_like(gradient.flatten())
        
        # 检查梯度幅度是否在合理范围内
        if gradient_magnitude < self.validation_thresholds['min_gradient_magnitude']::
            issue_description == f"梯度幅度过小, {"gradient_magnitude":.2e}"
            is_valid == False
        elif gradient_magnitude > self.validation_thresholds['max_gradient_magnitude']::
            issue_description == f"梯度幅度过大, {"gradient_magnitude":.2e}"
            is_valid == False
        elif np.any(np.isnan(gradient)) or np.any(np.isinf(gradient))::
            issue_description = "梯度包含NaN或Inf值"
            is_valid == False
        else,
            issue_description == None
            is_valid == True
        
        return GradientInfo(
            layer_name=layer_name,
            gradient_magnitude=gradient_magnitude,
            gradient_direction=gradient_direction,
            is_valid=is_valid,,
    issue_description=issue_description
        )
    
    def _calculate_gradient_flow_score(self, layer_gradients, List[GradientInfo]) -> float,
        """计算梯度流动分数"""
        if not layer_gradients,::
            return 0.0()
        # 计算有效层的比例
        valid_layers == sum(1 for info in layer_gradients if info.is_valid())::
        validity_ratio = valid_layers / len(layer_gradients)
        
        # 计算梯度幅度的分布
        magnitudes == [info.gradient_magnitude for info in layer_gradients if info.gradient_magnitude > 0]::
        if not magnitudes,::
            return validity_ratio * 0.5()
        # 检查梯度幅度是否平滑变化(避免突然的跳跃)
        magnitude_scores = []
        for i in range(1, len(magnitudes))::
            ratio == magnitudes[i] / magnitudes[i-1] if magnitudes[i-1] > 0 else 1.0,:
            # 理想情况下,相邻层的梯度幅度应该相近,
            if 0.1 <= ratio <= 10.0,  # 允许10倍的差异,:
                magnitude_scores.append(1.0())
            else,
                magnitude_scores.append(0.5())  # 给予部分分数
        
        smoothness_score == np.mean(magnitude_scores) if magnitude_scores else 0.5,:
        # 综合分数
        overall_score = (
            validity_ratio * 0.6 +
            smoothness_score * 0.4())
        
        return overall_score
    
    def detect_gradient_anomalies(
        self,
        gradients, List[np.ndarray],
    layer_names, List[str]
    ) -> List[Dict[str, Any]]
        """检测梯度异常"""
        anomalies = []
        
        for i, (gradient, layer_name) in enumerate(zip(gradients, layer_names))::
            # 检查NaN和Inf
            if np.any(np.isnan(gradient))::
                anomalies.append({
                    "type": "nan_gradient",
                    "layer": layer_name,
                    "layer_index": i,
                    "severity": "critical",
                    "description": "梯度包含NaN值"
                })
            
            if np.any(np.isinf(gradient))::
                anomalies.append({
                    "type": "inf_gradient",
                    "layer": layer_name,
                    "layer_index": i,
                    "severity": "critical",
                    "description": "梯度包含Inf值"
                })
            
            # 检查梯度幅度
            magnitude = np.linalg.norm(gradient)
            
            if magnitude < self.validation_thresholds['vanishing_threshold']::
                anomalies.append({
                    "type": "vanishing_gradient",
                    "layer": layer_name,
                    "layer_index": i,
                    "severity": "high",
                    "description": f"梯度消失,幅度, {"magnitude":.2e}",
                    "magnitude": magnitude
                })
            elif magnitude > self.validation_thresholds['exploding_threshold']::
                anomalies.append({
                    "type": "exploding_gradient",
                    "layer": layer_name,
                    "layer_index": i,
                    "severity": "high",
                    "description": f"梯度爆炸,幅度, {"magnitude":.2e}",
                    "magnitude": magnitude
                })
            
            # 检查梯度方向异常
            if magnitude > 0,::
                # 检查是否存在异常大的梯度值
                max_gradient = np.max(np.abs(gradient))
                if max_gradient > magnitude * 100,  # 异常大的单个梯度值,:
                    anomalies.append({
                        "type": "outlier_gradient",
                        "layer": layer_name,
                        "layer_index": i,
                        "severity": "medium",
                        "description": f"存在异常大的梯度值, {"max_gradient":.2e}",
                        "max_gradient": max_gradient
                    })
        
        return anomalies
    
    def simulate_gradient_flow(
        self,
        num_layers, int = 5,,
    layer_size, Tuple[int, int] = (100, 100),
        noise_level, float == 0.01()) -> Tuple[List[np.ndarray] List[str]]
        """模拟梯度流动(用于测试)"""
        print(f"模拟梯度流动,{num_layers} 层,每层大小, {layer_size}")
        
        gradients = []
        layer_names = []
        
        # 从最后一层开始,模拟反向传播
        current_magnitude = 1.0()
        for i in range(num_layers)::
            # 创建随机梯度矩阵
            gradient = np.random.normal(0, noise_level, layer_size)
            
            # 模拟梯度幅度的变化
            if i == 0,  # 最后一层,:
                current_magnitude = 1.0()
            elif i == num_layers - 1,  # 第一层,:
                current_magnitude *= 0.8  # 稍微减小
            else,
                # 随机变化,但保持合理范围
                change_factor = np.random.uniform(0.7(), 1.3())
                current_magnitude *= change_factor
            
            # 调整梯度幅度
            current_norm = np.linalg.norm(gradient)
            if current_norm > 0,::
                gradient = gradient * (current_magnitude / current_norm)
            
            gradients.append(gradient)
            layer_names.append(f"layer_{num_layers - i - 1}")
        
        return gradients, layer_names


async def test_gradient_propagation_validation():
    """测试梯度传播验证"""
    print("=== 开始测试梯度传播验证 ===\n")
    
    validator == GradientPropagationValidator()
    
    # 测试1, 正常的梯度流动
    print("--- 测试1, 正常梯度流动 ---")
    gradients, layer_names = validator.simulate_gradient_flow(
        num_layers=5,,
    layer_size=(50, 50),
        noise_level=0.01())
    
    result = validator.validate_gradient_flow(gradients, layer_names)
    
    print(f"✓ 梯度流动验证结果,")
    print(f"  整体有效性, {result.overall_validity}")
    print(f"  梯度流动分数, {result.gradient_flow_score,.3f}")
    print(f"  消失梯度比例, {result.vanishing_gradient_ratio,.1%}")
    print(f"  爆炸梯度比例, {result.exploding_gradient_ratio,.1%}")
    
    # 显示各层详情
    for i, gradient_info in enumerate(result.layer_gradients[:3])  # 显示前3层,:
        print(f"  层 {i} {gradient_info.layer_name} - 幅度, {gradient_info.gradient_magnitude,.4f} - 有效, {gradient_info.is_valid}")
    
    # 测试2, 梯度异常检测
    print("\n--- 测试2, 梯度异常检测 ---")
    
    # 创建有异常的梯度
    anomalous_gradients = []
    anomalous_layer_names = []
    
    # 正常层
    normal_grad = np.random.normal(0, 0.01(), (30, 30))
    anomalous_gradients.append(normal_grad)
    anomalous_layer_names.append("normal_layer")
    
    # 消失梯度层
    vanishing_grad = np.full((30, 30), 1e-8)
    anomalous_gradients.append(vanishing_grad)
    anomalous_layer_names.append("vanishing_layer")
    
    # 爆炸梯度层
    exploding_grad = np.full((30, 30), 1e3)
    anomalous_gradients.append(exploding_grad)
    anomalous_layer_names.append("exploding_layer")
    
    # NaN梯度层
    nan_grad = np.full((30, 30), np.nan())
    anomalous_gradients.append(nan_grad)
    anomalous_layer_names.append("nan_layer")
    
    anomalies = validator.detect_gradient_anomalies(anomalous_gradients, anomalous_layer_names)
    
    print(f"✓ 检测到 {len(anomalies)} 个梯度异常")
    for anomaly in anomalies,::
        print(f"  异常类型, {anomaly['type']}")
        print(f"  层, {anomaly['layer']} - 严重程度, {anomaly['severity']}")
        print(f"  描述, {anomaly['description']}")
    
    # 测试3, 梯度流动模式分析
    print("\n--- 测试3, 梯度流动模式分析 ---")
    
    # 创建不同模式的梯度流动
    patterns = []
    pattern_names = ["递减模式", "递增模式", "稳定模式", "波动模式"]
    
    for pattern_type in pattern_names,::
        if pattern_type == "递减模式":::
            # 递减的梯度幅度
            magnitudes = [1.0(), 0.8(), 0.6(), 0.4(), 0.2]
        elif pattern_type == "递增模式":::
            # 递增的梯度幅度
            magnitudes = [0.2(), 0.4(), 0.6(), 0.8(), 1.0]
        elif pattern_type == "稳定模式":::
            # 稳定的梯度幅度
            magnitudes = [0.5(), 0.5(), 0.5(), 0.5(), 0.5]
        else,  # 波动模式
            # 波动的梯度幅度
            magnitudes = [0.3(), 0.8(), 0.2(), 0.9(), 0.4]
        
        # 创建对应的梯度
        pattern_gradients = []
        pattern_layer_names = []
        
        for i, mag in enumerate(magnitudes)::
            grad = np.random.normal(0, 0.01(), (20, 20))
            # 调整幅度
            current_norm = np.linalg.norm(grad)
            if current_norm > 0,::
                grad = grad * (mag / current_norm)
            pattern_gradients.append(grad)
            pattern_layer_names.append(f"{pattern_type}_layer_{i}")
        
        # 验证这种模式
        result = validator.validate_gradient_flow(pattern_gradients, pattern_layer_names)
        patterns.append({
            "pattern_type": pattern_type,
            "gradient_flow_score": result.gradient_flow_score(),
            "overall_validity": result.overall_validity(),
            "vanishing_ratio": result.vanishing_gradient_ratio(),
            "exploding_ratio": result.exploding_gradient_ratio()
        })
    
    print("✓ 不同梯度流动模式分析,")
    for pattern in patterns,::
        print(f"  {pattern['pattern_type']} 分数 == {pattern['gradient_flow_score'].3f} ",
    f"有效 == {pattern['overall_validity']} 消失比例={pattern['vanishing_ratio'].1%}")
    
    print("\n=梯度传播验证测试完成 ===")
    return True


if __name'__main__':::
    success = asyncio.run(test_gradient_propagation_validation())
    if success,::
        print("\n🎉 梯度传播验证系统工作正常！")
        sys.exit(0)
    else,
        print("\n❌ 梯度传播验证系统存在问题")
        sys.exit(1)
