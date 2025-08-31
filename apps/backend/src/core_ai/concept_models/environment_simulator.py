"""
环境模拟器
实现完整的环境模拟功能，包括状态预测、动作效果模型和不确定性估计器
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class State:
    """环境状态"""
    time_step: int
    variables: Dict[str, Any]
    last_action: Optional[str] = None

@dataclass
class Action:
    """动作"""
    name: str
    parameters: Dict[str, Any]

@dataclass
class Scenario:
    """场景"""
    type: str  # 'most_likely', 'optimistic', 'pessimistic'
    probability: float
    state: State

class StatePredictor:
    """状态预测器"""
    
    def __init__(self):
        self.model_weights = {}
        self.learning_rate = 0.01
        
    async def predict(self, current_state: State, proposed_action: Action) -> State:
        """预测下一个状态"""
        logger.debug(f"Predicting next state for action {proposed_action.name}")
        await asyncio.sleep(0.01)  # 模拟计算时间
        
        # 基于当前状态和动作预测下一个状态
        next_variables = current_state.variables.copy()
        
        # 简单的状态转换规则
        if proposed_action.name == "increase_temperature":
            next_variables["temperature"] = next_variables.get("temperature", 20.0) + \
                proposed_action.parameters.get("amount", 1.0)
        elif proposed_action.name == "decrease_temperature":
            next_variables["temperature"] = next_variables.get("temperature", 20.0) - \
                proposed_action.parameters.get("amount", 1.0)
        elif proposed_action.name == "change_light":
            next_variables["light_level"] = proposed_action.parameters.get("level", 0.5)
        
        # 添加一些随机性
        for key in next_variables:
            next_variables[key] += np.random.normal(0, 0.1)
        
        next_state = State(
            time_step=current_state.time_step + 1,
            variables=next_variables,
            last_action=proposed_action.name
        )
        
        return next_state

    async def predict_optimistic(self, current_state: State, proposed_action: Action) -> State:
        """预测乐观状态"""
        logger.debug("Predicting optimistic state")
        await asyncio.sleep(0.01)
        next_state = await self.predict(current_state, proposed_action)
        # 乐观预测，所有变量增加一个小的正值
        for key in next_state.variables:
            next_state.variables[key] += 0.5
        return next_state

    async def predict_pessimistic(self, current_state: State, proposed_action: Action) -> State:
        """预测悲观状态"""
        logger.debug("Predicting pessimistic state")
        await asyncio.sleep(0.01)
        next_state = await self.predict(current_state, proposed_action)
        # 悲观预测，所有变量减少一个小的正值
        for key in next_state.variables:
            next_state.variables[key] -= 0.5
        return next_state

    async def update(self, state: State, action: Action, next_state: State):
        """更新模型"""
        logger.debug("Updating state predictor model")
        await asyncio.sleep(0.005)
        # 简单的模型更新逻辑
        # 在实际实现中，这里会使用更复杂的机器学习算法

class ActionEffectModel:
    """动作效果模型"""
    
    def __init__(self):
        self.effect_weights = {}
        
    async def predict_effect(self, action: Action, current_state: State) -> Dict[str, Any]:
        """预测动作效果"""
        logger.debug(f"Predicting effect for action {action.name}")
        await asyncio.sleep(0.01)
        
        effect = {}
        if action.name == "increase_temperature":
            effect["temperature_change"] = action.parameters.get("amount", 1.0)
        elif action.name == "decrease_temperature":
            effect["temperature_change"] = -action.parameters.get("amount", 1.0)
        elif action.name == "change_light":
            effect["light_change"] = action.parameters.get("level", 0.5) - \
                current_state.variables.get("light_level", 0.0)
        
        return effect

    async def update(self, action: Action, effect: Dict[str, Any], actual_effect: Dict[str, Any]):
        """更新动作效果模型"""
        logger.debug("Updating action effect model")
        await asyncio.sleep(0.005)
        # 简单的模型更新逻辑
        # 在实际实现中，这里会使用更复杂的机器学习算法

class UncertaintyEstimator:
    """不确定性估计器"""
    
    def __init__(self):
        self.uncertainty_history = []
        self.learning_rate = 0.01
        
    async def estimate(self, current_state: State, proposed_action: Action, predicted_state: State) -> float:
        """估计不确定性"""
        logger.debug("Estimating uncertainty")
        await asyncio.sleep(0.01)
        
        # 基于历史数据和状态复杂性估计不确定性
        base_uncertainty = 0.1
        
        # 如果是复杂的动作，增加不确定性
        if proposed_action.name in ["complex_action"]:
            base_uncertainty += 0.2
            
        # 如果状态变量很多，增加不确定性
        if len(current_state.variables) > 5:
            base_uncertainty += 0.1
            
        # 添加一些随机性
        uncertainty = base_uncertainty + np.random.normal(0, 0.05)
        
        # 确保不确定性在合理范围内
        return max(0.0, min(1.0, uncertainty))

    async def update(self, prediction_error: float):
        """更新不确定性估计器"""
        logger.debug("Updating uncertainty estimator")
        await asyncio.sleep(0.005)
        self.uncertainty_history.append(prediction_error)
        # 保持历史记录的大小在合理范围内
        if len(self.uncertainty_history) > 100:
            self.uncertainty_history.pop(0)

class EnvironmentSimulator:
    """环境模拟器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.state_predictor = StatePredictor()
        self.action_effect_model = ActionEffectModel()
        self.uncertainty_estimator = UncertaintyEstimator()
        self.logger = logging.getLogger(__name__)
    
    async def simulate_action_consequences(self, current_state: State, proposed_action: Action) -> Dict[str, Any]:
        """模拟动作后果"""
        # 预测下一个状态
        predicted_state = await self.state_predictor.predict(current_state, proposed_action)
        
        # 估计不确定性
        uncertainty = await self.uncertainty_estimator.estimate(current_state, proposed_action, predicted_state)
        
        # 计算预期奖励
        expected_reward = await self._calculate_expected_reward(current_state, proposed_action, predicted_state)
        
        # 生成多个可能的结果场景
        scenarios = await self._generate_scenarios(current_state, proposed_action, uncertainty)
        
        self.logger.info(f"Simulated action consequences for action {proposed_action.name}")
        return {
            'predicted_state': predicted_state,
            'uncertainty': uncertainty,
            'expected_reward': expected_reward,
            'scenarios': scenarios,
            'confidence': 1.0 - uncertainty
        }
    
    async def _calculate_expected_reward(self, current_state: State, proposed_action: Action, 
                                       predicted_state: State) -> float:
        """计算预期奖励"""
        self.logger.debug("Calculating expected reward")
        await asyncio.sleep(0.005)  # 模拟计算时间
        
        # 简单的奖励计算逻辑
        reward = 0.0
        
        # 如果温度在舒适范围内，给予正奖励
        temperature = predicted_state.variables.get("temperature", 20.0)
        if 18.0 <= temperature <= 24.0:
            reward += 1.0
            
        # 如果光线在合适范围内，给予正奖励
        light_level = predicted_state.variables.get("light_level", 0.5)
        if 0.3 <= light_level <= 0.8:
            reward += 0.5
            
        return reward

    async def _generate_scenarios(self, state: State, action: Action, uncertainty: float) -> List[Scenario]:
        """生成多个可能场景"""
        scenarios = []
        
        # 最可能场景
        most_likely = await self.state_predictor.predict(state, action)
        scenarios.append(Scenario(
            type='most_likely',
            probability=0.6,
            state=most_likely
        ))
        
        # 乐观场景
        optimistic = await self.state_predictor.predict_optimistic(state, action)
        scenarios.append(Scenario(
            type='optimistic',
            probability=0.2,
            state=optimistic
        ))
        
        # 悲观场景
        pessimistic = await self.state_predictor.predict_pessimistic(state, action)
        scenarios.append(Scenario(
            type='pessimistic',
            probability=0.2,
            state=pessimistic
        ))
        
        return scenarios
    
    async def update_model_from_experience(self, experience: Dict[str, Any]):
        """从经验更新模型"""
        # 更新状态预测器
        await self.state_predictor.update(
            experience.get("state"), 
            experience.get("action"), 
            experience.get("next_state")
        )
        
        # 更新动作效果模型
        await self.action_effect_model.update(
            experience.get("action"), 
            experience.get("predicted_effect"),
            experience.get("actual_effect")
        )
        
        # 更新不确定性估计器
        prediction_error = self._calculate_prediction_error(
            experience.get("predicted_state"), 
            experience.get("actual_state")
        )
        await self.uncertainty_estimator.update(prediction_error)
        self.logger.info("Environment model updated from experience.")

    def _calculate_prediction_error(self, predicted_state: State, actual_state: State) -> float:
        """计算预测误差"""
        self.logger.debug("Calculating prediction error")
        # 简单的误差计算
        error = 0.0
        if predicted_state and actual_state:
            # 比较时间步
            if predicted_state.time_step != actual_state.time_step:
                error += 0.1
                
            # 比较变量值
            for key in predicted_state.variables:
                if key in actual_state.variables:
                    error += abs(predicted_state.variables[key] - actual_state.variables[key]) / 10.0
                    
        return min(error, 1.0)  # 限制误差在0-1之间

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建环境模拟器
    simulator = EnvironmentSimulator()
    
    # 创建初始状态
    initial_state = State(
        time_step=0,
        variables={
            "temperature": 22.0,
            "light_level": 0.6,
            "humidity": 45.0
        }
    )
    
    # 创建动作
    action = Action(
        name="increase_temperature",
        parameters={"amount": 2.0}
    )
    
    # 运行模拟
    async def test_simulation():
        result = await simulator.simulate_action_consequences(initial_state, action)
        print("Simulation result:")
        print(f"  Predicted state: {result['predicted_state']}")
        print(f"  Uncertainty: {result['uncertainty']:.2f}")
        print(f"  Expected reward: {result['expected_reward']:.2f}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Scenarios: {len(result['scenarios'])}")
        
        # 测试模型更新
        experience = {
            "state": initial_state,
            "action": action,
            "next_state": result['predicted_state'],
            "predicted_state": result['predicted_state'],
            "actual_state": State(
                time_step=1,
                variables={
                    "temperature": 24.5,  # 实际温度略高于预测
                    "light_level": 0.6,
                    "humidity": 45.0
                }
            ),
            "predicted_effect": {"temperature_change": 2.0},
            "actual_effect": {"temperature_change": 2.5}
        }
        
        await simulator.update_model_from_experience(experience)
        print("Model updated from experience")
    
    # 运行测试
    asyncio.run(test_simulation())