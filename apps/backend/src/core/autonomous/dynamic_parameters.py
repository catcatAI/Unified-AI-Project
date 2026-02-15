"""
Angela AI v6.0 - 动态参数系统
Dynamic Parameter System

将硬编码的固定参数改为动态调整，模拟生命的不确定性。

核心概念：
- 参数不是固定的，而是随时间、状态、经验动态变化
- 人类有时容易高兴，有时不容易（情绪阈值动态变化）
- 行为有时成功，有时失败（执行成功率动态变化）
- 能力有时觉得能做到，有时觉得不能（自我效能感动态变化）
- 通过其他参数的干涉，效果有大有小

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
import random
import math
import asyncio
import logging
logger = logging.getLogger(__name__)


@dataclass
class ParameterState:
    """参数状态 / Parameter state with dynamic variation"""
    base_value: float  # 基础值
    current_value: float  # 当前值（动态变化）
    variation_range: Tuple[float, float]  # 变化范围 (min, max)
    volatility: float  # 波动性 (0-1)
    last_update: datetime = field(default_factory=datetime.now)
    update_interval: float = 60.0  # 更新间隔（秒）
    history: List[float] = field(default_factory=list)  # 历史值
    influence_map: Dict[str, float] = field(default_factory=dict)  # 因素对该参数的影响权重
    
    def __post_init__(self):
        if not self.history:
            self.history = [self.base_value]
    
    def get_value(self, context: Dict[str, float] = None) -> float:
        """
        获取当前值（考虑上下文影响）
        Get current value considering context effects
        """
        # 基础当前值
        value = self.current_value
        
        # 添加上下文影响
        if context:
            for factor_name, factor_value in context.items():
                # 每个因素对参数的影响程度不同
                influence = self._calculate_influence(factor_name, factor_value)
                value += influence
        
        # 添加随机波动（模拟不确定性）
        noise = random.gauss(0, self.volatility * 0.1)
        value += noise
        
        # 限制在范围内
        return max(self.variation_range[0], min(self.variation_range[1], value))
    
    def _calculate_influence(self, factor_name: str, factor_value: float) -> float:
        """计算外部因素对参数的影响"""
        # 优先使用该参数特定的影响权重
        if factor_name in self.influence_map:
            weight = self.influence_map[factor_name]
        else:
            # 不同因素对不同参数的影响权重
            influence_weights = {
                'energy': 0.3,  # 精力影响大
                'mood': 0.2,    # 情绪影响中等
                'stress': -0.25, # 压力有负面影响
                'confidence': 0.15,  # 信心有正面影响
                'fatigue': -0.2,  # 疲劳有负面影响
                'recent_success': 0.35,  # 最近成功大幅提升
                'recent_failure': -0.3,  # 最近失败大幅降低
            }
            weight = influence_weights.get(factor_name, 0.1)
        
        return factor_value * weight * self.volatility
    
    def update(self, time_delta: Optional[float] = None):
        """
        更新参数值（模拟自然波动）
        Update parameter value (simulate natural fluctuation)
        """
        if time_delta is None:
            time_delta = (datetime.now() - self.last_update).total_seconds()
        
        # 只有超过更新间隔才更新
        if time_delta < self.update_interval:
            return
        
        # 向基础值回归的趋势（homeostasis）
        drift_to_base = (self.base_value - self.current_value) * 0.1
        
        # 随机游走
        random_walk = random.gauss(0, self.volatility * 0.05)
        
        # 应用变化
        self.current_value += drift_to_base + random_walk
        
        # 确保在范围内
        self.current_value = max(
            self.variation_range[0], 
            min(self.variation_range[1], self.current_value)
        )
        
        # 记录历史
        self.history.append(self.current_value)
        if len(self.history) > 100:  # 只保留最近100个值
            self.history.pop(0)
        
        self.last_update = datetime.now()
    
    def get_trend(self, window: int = 10) -> float:
        """获取参数趋势（上升/下降）"""
        if len(self.history) < window:
            return 0.0
        
        recent = self.history[-window:]
        earlier = self.history[-window*2:-window] if len(self.history) >= window*2 else self.history[:window]
        
        if not earlier:
            return 0.0
        
        return (sum(recent) / len(recent)) - (sum(earlier) / len(earlier))


class DynamicThresholdManager:
    """
    动态阈值管理器
    
    管理所有动态变化的阈值参数：
    - 情绪触发阈值（有时容易高兴，有时不容易）
    - 行为执行成功率（有时成功，有时失败）
    - 决策置信度阈值（有时觉得能做到，有时觉得不能）
    - 社交活跃度阈值（有时想互动，有时不想）
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化动态阈值系统 - 支持配置驱动"""
        self.config = config or {}
        self.parameters: Dict[str, ParameterState] = {}
        self._initialize_default_parameters()
        self._update_task: Optional[asyncio.Task] = None
        self._running = False
        # Configurable update interval (default 60 seconds)
        self._update_interval = self.config.get('update_interval', 60.0)
    
    def _initialize_default_parameters(self):
        """初始化默认的动态参数"""
        
        # 1. 情绪触发阈值
        self.parameters['emotion_happiness_threshold'] = ParameterState(
            base_value=0.6,
            current_value=0.6,
            variation_range=(0.3, 0.9),
            volatility=0.4,
            influence_map={
                'stress': 0.5,           # 压力大更难高兴 (threshold increase)
                'recent_success': -0.6,  # 成功了容易高兴 (threshold decrease)
                'mood': -0.4             # 心情好容易更高兴
            }
        )
        
        self.parameters['emotion_sadness_threshold'] = ParameterState(
            base_value=0.4,
            current_value=0.4,
            variation_range=(0.2, 0.7),
            volatility=0.3,
            influence_map={
                'stress': -0.4,          # 压力大容易难过
                'recent_failure': -0.5   # 失败了容易难过
            }
        )
        
        self.parameters['emotion_anger_threshold'] = ParameterState(
            base_value=0.7,
            current_value=0.7,
            variation_range=(0.4, 0.95),
            volatility=0.35,
            influence_map={
                'stress': -0.6,          # 压力大容易生气 (threshold decrease)
                'fatigue': -0.4          # 疲劳容易生气
            }
        )
        
        # 2. 行为执行成功率
        self.parameters['action_success_rate'] = ParameterState(
            base_value=0.85,
            current_value=0.85,
            variation_range=(0.5, 0.98),
            volatility=0.25,
            influence_map={
                'energy': 0.4,
                'confidence': 0.3,
                'fatigue': -0.5
            }
        )
        
        self.parameters['action_speed_factor'] = ParameterState(
            base_value=1.0,
            current_value=1.0,
            variation_range=(0.3, 2.0),
            volatility=0.3,
            influence_map={
                'energy': 0.6,
                'fatigue': -0.7
            }
        )
        
        # 3. 决策置信度
        self.parameters['decision_confidence_threshold'] = ParameterState(
            base_value=0.7,
            current_value=0.7,
            variation_range=(0.4, 0.95),
            volatility=0.2,
            influence_map={
                'confidence': -0.6,      # 信心足则门槛低
                'recent_success': -0.4,
                'recent_failure': 0.5
            }
        )
        
        self.parameters['risk_tolerance'] = ParameterState(
            base_value=0.5,
            current_value=0.5,
            variation_range=(0.1, 0.9),
            volatility=0.4,
            influence_map={
                'confidence': 0.5,
                'mood': 0.3,
                'stress': -0.4
            }
        )
        
        # 4. 社交活跃度
        self.parameters['social_initiative_threshold'] = ParameterState(
            base_value=0.5,
            current_value=0.5,
            variation_range=(0.1, 0.9),
            volatility=0.35,
            influence_map={
                'mood': -0.6,            # 心情好降低门槛 (threshold decrease)
                'energy': -0.4           # 精力足降低门槛
            }
        )
        
        self.parameters['social_sensitivity'] = ParameterState(
            base_value=0.6,
            current_value=0.6,
            variation_range=(0.2, 0.95),
            volatility=0.3,
        )
        
        # 5. 学习和记忆参数
        self.parameters['learning_rate'] = ParameterState(
            base_value=0.1,
            current_value=0.1,
            variation_range=(0.01, 0.3),
            volatility=0.2,
        )
        
        self.parameters['memory_retention'] = ParameterState(
            base_value=0.8,
            current_value=0.8,
            variation_range=(0.4, 0.98),
            volatility=0.15,
        )
        
        # 6. 生理参数
        self.parameters['energy_decay_rate'] = ParameterState(
            base_value=0.05,
            current_value=0.05,
            variation_range=(0.01, 0.15),
            volatility=0.2,
        )
        
        self.parameters['rest_recovery_rate'] = ParameterState(
            base_value=0.1,
            current_value=0.1,
            variation_range=(0.02, 0.25),
            volatility=0.25,
        )
    
    async def start(self):
        """启动动态更新循环"""
        if self._update_task is None:
            self._running = True
            self._update_task = asyncio.create_task(self._update_loop())
    
    async def stop(self):
        """停止动态更新循环"""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
    
    async def _update_loop(self):
        """后台更新循环 - Configurable"""
        while self._running:
            try:
                # 使用可配置的更新间隔（默认60秒）
                await asyncio.sleep(self._update_interval)
                
                # 为每个参数构建上下文（基于其他参数）
                context = self._build_context()
                
                # 更新所有参数
                for param_name, param_state in self.parameters.items():
                    # 为当前参数构建特定的上下文
                    param_context = self._build_context_for_parameter(param_name, context)
                    param_state.update()
                    
                    # 记录参数变化（用于调试）
                    if abs(param_state.current_value - param_state.base_value) > 0.2:
                        print(f"[DynamicParams] {param_name}: {param_state.current_value:.2f} "
                              f"(base: {param_state.base_value:.2f}, "
                              f"trend: {param_state.get_trend():+.3f})")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[DynamicParams] Update error: {e}")
                await asyncio.sleep(10)
    
    def _build_context(self) -> Dict[str, float]:
        """构建全局上下文"""
        def get_val(name: str, default: float = 0.5) -> float:
            param = self.parameters.get(name)
            return param.current_value if param else default

        return {
            'energy': get_val('energy_decay_rate', 0.05),
            'mood': get_val('emotion_happiness_threshold', 0.6),
            'stress': 1.0 - get_val('emotion_anger_threshold', 0.7),
            'confidence': get_val('decision_confidence_threshold', 0.7),
            'fatigue': 1.0 - get_val('rest_recovery_rate', 0.1),
            'recent_success': get_val('action_success_rate', 0.85),
            'recent_failure': 1.0 - get_val('action_success_rate', 0.85),
        }
    
    def _build_context_for_parameter(self, param_name: str, global_context: Dict[str, float]) -> Dict[str, float]:
        """为特定参数构建上下文（参数间相互影响）"""
        context = global_context.copy()
        
        # 参数间的特定影响关系
        if param_name == 'emotion_happiness_threshold':
            # 最近成功会让高兴阈值降低（更容易高兴）
            context['recent_success'] = context.get('recent_success', 0.5) * 1.5
            # 疲劳会让高兴阈值升高（更不容易高兴）
            context['fatigue'] = context.get('fatigue', 0.5) * 1.3
            
        elif param_name == 'action_success_rate':
            # 精力影响成功率
            context['energy'] = context.get('energy', 0.5) * 1.2
            # 信心直接影响成功率
            context['confidence'] = context.get('confidence', 0.5) * 1.4
            
        elif param_name == 'decision_confidence_threshold':
            # 最近失败会降低信心
            context['recent_failure'] = context.get('recent_failure', 0.5) * 1.3
            # 能量影响决策信心
            context['energy'] = context.get('energy', 0.5) * 1.1
        
        return context
    
    def get_parameter(self, name: str, context: Optional[Dict[str, float]] = None) -> float:
        """获取参数当前值"""
        if name not in self.parameters:
            return 0.5  # 默认值
        
        return self.parameters[name].get_value(context)
    
    def set_parameter_base(self, name: str, base_value: float):
        """设置参数基础值（长期调整）"""
        if name in self.parameters:
            self.parameters[name].base_value = base_value
    
    def adjust_parameter_volatility(self, name: str, delta: float):
        """调整参数波动性（例如：压力大时波动性增加）"""
        if name in self.parameters:
            self.parameters[name].volatility = max(0.0, min(1.0, 
                self.parameters[name].volatility + delta))
    
    def record_outcome(self, action_type: str, success: bool, intensity: float = 1.0):
        """
        记录行为结果，影响相关参数
        
        Args:
            action_type: 行为类型
            success: 是否成功
            intensity: 影响强度 (0-1)
        """
        # 根据行为结果调整参数
        if success:
            # 成功会提升action_success_rate的基础值
            param = self.parameters.get('action_success_rate')
            if param:
                param.base_value = min(0.98, param.base_value + 0.02 * intensity)
            
            # 成功会降低decision_confidence_threshold（更容易有信心）
            param = self.parameters.get('decision_confidence_threshold')
            if param:
                param.base_value = max(0.3, param.base_value - 0.02 * intensity)
                
        else:
            # 失败会降低action_success_rate
            param = self.parameters.get('action_success_rate')
            if param:
                param.base_value = max(0.3, param.base_value - 0.03 * intensity)
            
            # 失败会增加波动性（变得更加不稳定）
            for param_name in ['emotion_happiness_threshold', 'action_success_rate']:
                self.adjust_parameter_volatility(param_name, 0.05 * intensity)
    
    def get_all_parameters_summary(self) -> Dict[str, Any]:
        """获取所有参数摘要"""
        return {
            name: {
                'base': param.base_value,
                'current': param.current_value,
                'range': param.variation_range,
                'volatility': param.volatility,
                'trend': param.get_trend(),
            }
            for name, param in self.parameters.items()
        }


# 使用示例和演示
async def demo_dynamic_parameters():
    """动态参数系统演示"""
    logger.info("=" * 60)
    logger.info("Angela AI 动态参数系统演示")
    logger.info("=" * 60)
    
    manager = DynamicThresholdManager()
    
    # 启动更新循环
    await manager.start()
    
    logger.info("\n1. 初始参数状态：")
    for name, param in manager.parameters.items():
        print(f"   {name}: {param.current_value:.2f} "
              f"(base: {param.base_value:.2f}, "
              f"volatility: {param.volatility:.2f})")
    
    # 模拟一些行为结果
    logger.info("\n2. 模拟成功行为：")
    manager.record_outcome('conversation', success=True, intensity=0.8)
    logger.info(f"   action_success_rate base: {manager.parameters['action_success_rate'].base_value:.2f}")
    
    logger.info("\n3. 模拟失败行为：")
    manager.record_outcome('file_operation', success=False, intensity=0.6)
    logger.info(f"   action_success_rate base: {manager.parameters['action_success_rate'].base_value:.2f}")
    logger.info(f"   volatility increased: {manager.parameters['action_success_rate'].volatility:.2f}")
    
    # 等待并观察参数变化
    logger.info("\n4. 等待参数自然波动（60秒）...")
    await asyncio.sleep(60)
    
    logger.info("\n5. 参数变化后：")
    for name, param in manager.parameters.items():
        if abs(param.current_value - param.base_value) > 0.05:
            print(f"   {name}: {param.current_value:.2f} "
                  f"(changed from base: {param.base_value:.2f})")
    
    # 获取当前情绪阈值
    logger.info("\n6. 当前情绪阈值（考虑上下文）：")
    context = {
        'energy': 0.7,
        'recent_success': 0.8,
        'fatigue': 0.3,
    }
    happiness_threshold = manager.get_parameter('emotion_happiness_threshold', context)
    print(f"   高兴阈值: {happiness_threshold:.2f} "
          f"(当前状态下{'容易' if happiness_threshold < 0.5 else '不容易'}高兴)")
    
    # 停止更新循环
    await manager.stop()
    
    logger.info("\n演示完成！")
    logger.info("=" * 60)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_dynamic_parameters())
