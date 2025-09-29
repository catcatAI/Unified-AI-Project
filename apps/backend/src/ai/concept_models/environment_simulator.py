"""
环境模拟器
实现完整的环境模拟功能，包括状态预测、动作效果模型和不确定性估计器
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

logger: Any = logging.getLogger(__name__)

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
    
    def __init__(self) -> None:
        self.model_weights = {} 
        self.learning_rate = 0.01
        # 添加实际的神经网络模型
        self.model = self._build_model
        self.optimizer = optim.Adam(self.model.parameters, lr=self.learning_rate)
        self.criterion = nn.MSELoss
        self.is_trained = False  # 标记模型是否已训练
        
    def _build_model(self):
        """构建神经网络模型"""
        # 简单的全连接网络用于状态预测
        model = nn.Sequential(
            nn.Linear(10, 64),  # 假设有10个输入特征
            nn.ReLU,
            nn.Linear(64, 32),
            nn.ReLU,
            nn.Linear(32, 5)    # 假设预测5个状态变量
        )
        return model
    
    async def predict(self, current_state: State, proposed_action: Action) -> State:
        """预测下一个状态"""
        logger.debug(f"Predicting next state for action {proposed_action.name}")
        _ = await asyncio.sleep(0.01)  # 模拟计算时间
        
        # 基于当前状态和动作预测下一个状态
        next_variables = current_state.variables.copy
        
        # 使用神经网络进行预测（如果模型已训练）
        if self.is_trained:
            input_features = self._state_to_features(current_state, proposed_action)
            with torch.no_grad:
                prediction = self.model(input_features)
            
            # 将预测结果转换为状态变量
            next_variables = self._prediction_to_variables(prediction, next_variables)
        else:
            # 如果模型未训练，使用简单的模拟逻辑
            if proposed_action.name == "increase_temperature":
                temp_change = proposed_action.parameters.get("amount", 1.0)
                next_variables["temperature"] = next_variables.get("temperature", 20.0) + temp_change
            elif proposed_action.name == "decrease_temperature":
                temp_change = proposed_action.parameters.get("amount", 1.0)
                next_variables["temperature"] = next_variables.get("temperature", 20.0) - temp_change
            elif proposed_action.name == "change_light":
                light_level = proposed_action.parameters.get("level", 0.5)
                next_variables["light_level"] = light_level
        
        next_state = State(
            time_step=current_state.time_step + 1,
            variables=next_variables,
            last_action=proposed_action.name
        )
        
        return next_state

    def _state_to_features(self, state: State, action: Action) -> torch.Tensor:
        """将状态和动作转换为模型输入特征"""
        # 简化实现，实际应用中需要更复杂的特征工程
        features = 
        for i in range(5):  # 假设最多5个状态变量
            var_name = f"var_{i}"
            features.append(state.variables.get(var_name, 0.0))
        
        # 添加动作特征
        action_features = [0.0] * 5  # 假设最多5种动作
        if action.name == "increase_temperature":
            action_features[0] = action.parameters.get("amount", 0.0)
        elif action.name == "decrease_temperature":
            action_features[1] = action.parameters.get("amount", 0.0)
        elif action.name == "change_light":
            action_features[2] = action.parameters.get("level", 0.0)
        
        all_features = features + action_features
        return torch.FloatTensor(all_features).unsqueeze(0)
    
    def _prediction_to_variables(self, prediction: torch.Tensor, base_variables: Dict) -> Dict:
        """将模型预测转换为状态变量"""
        variables = base_variables.copy
        pred_values = prediction.squeeze.numpy
        
        # 更新状态变量
        for i, value in enumerate(pred_values[:5]):  # 假设预测5个状态变量
            var_name = f"var_{i}"
            variables[var_name] = float(value)
            
        return variables

    async def predict_optimistic(self, current_state: State, proposed_action: Action) -> State:
        """预测乐观状态"""
        logger.debug("Predicting optimistic state")
        _ = await asyncio.sleep(0.01)
        next_state = await self.predict(current_state, proposed_action)
        # 乐观预测，所有变量增加一个小的正值
        for key in next_state.variables:
            next_state.variables[key] += 0.5
        return next_state

    async def predict_pessimistic(self, current_state: State, proposed_action: Action) -> State:
        """预测悲观状态"""
        logger.debug("Predicting pessimistic state")
        _ = await asyncio.sleep(0.01)
        next_state = await self.predict(current_state, proposed_action)
        # 悲观预测，所有变量减少一个小的正值
        for key in next_state.variables:
            next_state.variables[key] -= 0.5
        return next_state

    async def update(self, state: State, action: Action, next_state: State):
        """更新模型"""
        logger.debug("Updating state predictor model")
        _ = await asyncio.sleep(0.005)
        
        # 准备训练数据
        input_features = self._state_to_features(state, action)
        target_variables = self._state_to_target(next_state)
        
        # 训练模型
        self.model.train
        self.optimizer.zero_grad
        
        prediction = self.model(input_features)
        loss = self.criterion(prediction, target_variables)
        
        loss.backward
        self.optimizer.step
        
        self.model.eval
        self.is_trained = True  # 标记模型已训练
        
        # 简单的模型更新逻辑
        # 在实际实现中，这里会使用更复杂的机器学习算法

    def _state_to_target(self, state: State) -> torch.Tensor:
        """将状态转换为训练目标"""
        target = 
        for i in range(5):  # 假设预测5个状态变量
            var_name = f"var_{i}"
            target.append(state.variables.get(var_name, 0.0))
        return torch.FloatTensor(target).unsqueeze(0)
        
    def train_model(self, training_data: List[Dict[str, Any]], epochs: int = 100):
        """训练模型"""
        logger.info(f"Training state predictor model with {len(training_data)} samples")
        
        # 准备训练数据
        inputs = 
        targets = 
        
        for data in training_data:
            state = State(
                time_step=data["state"]["time_step"],
                variables=data["state"]["variables"]
            )
            action = Action(
                name=data["action"]["name"],
                parameters=data["action"]["parameters"]
            )
            next_state = State(
                time_step=data["next_state"]["time_step"],
                variables=data["next_state"]["variables"]
            )
            
            input_features = self._state_to_features(state, action)
            target_variables = self._state_to_target(next_state)
            
            inputs.append(input_features.squeeze(0))  # 移除批次维度
            targets.append(target_variables.squeeze(0))  # 移除批次维度
        
        # 转换为张量
        inputs_tensor = torch.stack(inputs)
        targets_tensor = torch.stack(targets)
        
        # 创建数据加载器
        dataset = TensorDataset(inputs_tensor, targets_tensor)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # 训练模型
        self.model.train
        for epoch in range(epochs):
            total_loss = 0.0
            for batch_inputs, batch_targets in dataloader:
                self.optimizer.zero_grad
                
                predictions = self.model(batch_inputs)
                loss = self.criterion(predictions, batch_targets)
                
                loss.backward
                self.optimizer.step
                
                total_loss += loss.item
            
            if epoch % 20 == 0:
                avg_loss = total_loss / len(dataloader)
                logger.info(f"Epoch {epoch}, Average Loss: {avg_loss:.4f}")
        
        self.model.eval
        self.is_trained = True
        logger.info("State predictor model training completed")

class ActionEffectModel:
    """动作效果模型"""
    
    def __init__(self) -> None:
        self.effect_weights = 
        self.model = self._build_model
        self.optimizer = optim.Adam(self.model.parameters, lr=0.01)
        self.criterion = nn.MSELoss
        self.is_trained = False
        
    def _build_model(self):
        """构建动作效果预测模型"""
        model = nn.Sequential(
            nn.Linear(8, 32),  # 8个输入特征
            nn.ReLU,
            nn.Linear(32, 16),
            nn.ReLU,
            nn.Linear(16, 3)    # 预测3个效果变量
        )
        return model
    
    async def predict_effect(self, action: Action, current_state: State) -> Dict[str, Any]:
        """预测动作效果"""
        logger.debug(f"Predicting effect for action {action.name}")
        _ = await asyncio.sleep(0.01)
        
        # 使用训练好的模型预测效果（如果已训练）
        if self.is_trained:
            input_features = self._action_state_to_features(action, current_state)
            with torch.no_grad:
                prediction = self.model(input_features)
            effect = self._prediction_to_effect(prediction)
        else:
            # 如果模型未训练，使用简单的模拟逻辑
            effect = 
            if action.name == "increase_temperature":
                effect["temperature_change"] = action.parameters.get("amount", 1.0)
            elif action.name == "decrease_temperature":
                effect["temperature_change"] = -action.parameters.get("amount", 1.0)
            elif action.name == "change_light":
                effect["light_change"] = action.parameters.get("level", 0.5) - \
                    current_state.variables.get("light_level", 0.0)
        
        return effect

    def _action_state_to_features(self, action: Action, state: State) -> torch.Tensor:
        """将动作和状态转换为模型输入特征"""
        features = 
        
        # 动作特征
        action_features = [0.0] * 4  # 假设最多4种动作
        if action.name == "increase_temperature":
            action_features[0] = 1.0
            features.append(action.parameters.get("amount", 0.0))
        elif action.name == "decrease_temperature":
            action_features[1] = 1.0
            features.append(action.parameters.get("amount", 0.0))
        elif action.name == "change_light":
            action_features[2] = 1.0
            features.append(action.parameters.get("level", 0.0))
        else:
            action_features[3] = 1.0
            features.append(0.0)
            
        features.extend(action_features)
        
        # 状态特征
        state_features = [
            state.variables.get("temperature", 0.0),
            state.variables.get("light_level", 0.0),
            state.variables.get("humidity", 0.0),
        ]
        features.extend(state_features)
        
        # 填充到固定长度
        while len(features) < 8:
            features.append(0.0)
            
        return torch.FloatTensor(features).unsqueeze(0)
    
    def _prediction_to_effect(self, prediction: torch.Tensor) -> Dict[str, Any]:
        """将模型预测转换为效果字典"""
        pred_values = prediction.squeeze.numpy
        effect = {
            "temperature_change": float(pred_values[0]),
            "light_change": float(pred_values[1]),
            "humidity_change": float(pred_values[2])
        }
        return effect

    async def update(self, action: Action, effect: Dict[str, Any], actual_effect: Dict[str, Any]):
        """更新动作效果模型"""
        logger.debug("Updating action effect model")
        _ = await asyncio.sleep(0.005)
        
        # 准备训练数据
        # 在实际实现中，这里会使用更复杂的机器学习算法
        pass

    def train_model(self, training_data: List[Dict[str, Any]], epochs: int = 100):
        """训练动作效果模型"""
        logger.info(f"Training action effect model with {len(training_data)} samples")
        
        # 准备训练数据
        inputs = 
        targets = 
        
        for data in training_data:
            action = Action(
                name=data["action"]["name"],
                parameters=data["action"]["parameters"]
            )
            state = State(
                time_step=data["state"]["time_step"],
                variables=data["state"]["variables"]
            )
            actual_effect = data["actual_effect"]
            
            input_features = self._action_state_to_features(action, state)
            target_effect = self._effect_to_target(actual_effect)
            
            inputs.append(input_features.squeeze(0))  # 移除批次维度
            targets.append(target_effect.squeeze(0))  # 移除批次维度
        
        # 转换为张量
        inputs_tensor = torch.stack(inputs)
        targets_tensor = torch.stack(targets)
        
        # 创建数据加载器
        dataset = TensorDataset(inputs_tensor, targets_tensor)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # 训练模型
        self.model.train
        for epoch in range(epochs):
            total_loss = 0.0
            for batch_inputs, batch_targets in dataloader:
                self.optimizer.zero_grad
                
                predictions = self.model(batch_inputs)
                loss = self.criterion(predictions, batch_targets)
                
                loss.backward
                self.optimizer.step
                
                total_loss += loss.item
            
            if epoch % 20 == 0:
                avg_loss = total_loss / len(dataloader)
                logger.info(f"Epoch {epoch}, Average Loss: {avg_loss:.4f}")
        
        self.model.eval
        self.is_trained = True
        logger.info("Action effect model training completed")
        
    def _effect_to_target(self, effect: Dict[str, Any]) -> torch.Tensor:
        """将效果转换为训练目标"""
        target = [
            effect.get("temperature_change", 0.0),
            effect.get("light_change", 0.0),
            effect.get("humidity_change", 0.0)
        ]
        return torch.FloatTensor(target).unsqueeze(0)

class UncertaintyEstimator:
    """不确定性估计器"""
    
    def __init__(self) -> None:
        self.uncertainty_history = 
        self.learning_rate = 0.01
        self.model = self._build_model
        self.optimizer = optim.Adam(self.model.parameters, lr=self.learning_rate)
        self.criterion = nn.MSELoss
        self.is_trained = False
        
    def _build_model(self):
        """构建不确定性估计模型"""
        model = nn.Sequential(
            nn.Linear(12, 32),  # 12个输入特征
            nn.ReLU,
            nn.Linear(32, 16),
            nn.ReLU,
            nn.Linear(16, 1),
            nn.Sigmoid
        )
        return model
    
    async def estimate(self, current_state: State, proposed_action: Action, predicted_state: State) -> float:
        """估计不确定性"""
        logger.debug("Estimating uncertainty")
        _ = await asyncio.sleep(0.01)
        
        # 使用训练好的模型估计不确定性（如果已训练）
        if self.is_trained:
            input_features = self._state_action_state_to_features(current_state, proposed_action, predicted_state)
            with torch.no_grad:
                uncertainty = self.model(input_features)
            return float(uncertainty.item)
        else:
            # 如果模型未训练，使用简单的模拟逻辑
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

    def _state_action_state_to_features(self, state: State, action: Action, predicted_state: State) -> torch.Tensor:
        """将状态、动作和预测状态转换为模型输入特征"""
        features = 
        
        # 当前状态特征
        for i in range(5):  # 假设最多5个状态变量
            var_name = f"var_{i}"
            features.append(state.variables.get(var_name, 0.0))
        
        # 动作特征
        action_features = [0.0] * 4  # 假设最多4种动作
        if action.name == "increase_temperature":
            action_features[0] = 1.0
        elif action.name == "decrease_temperature":
            action_features[1] = 1.0
        elif action.name == "change_light":
            action_features[2] = 1.0
        else:
            action_features[3] = 1.0
        features.extend(action_features)
        
        # 预测状态特征
        for i in range(5):  # 假设最多5个状态变量
            var_name = f"var_{i}"
            features.append(predicted_state.variables.get(var_name, 0.0))
        
        # 转换为张量
        return torch.FloatTensor(features).unsqueeze(0)

    async def update(self, prediction_error: float):
        """更新不确定性估计器"""
        logger.debug("Updating uncertainty estimator")
        _ = await asyncio.sleep(0.005)
        self.uncertainty_history.append(prediction_error)
        # 保持历史记录的大小在合理范围内
        if len(self.uncertainty_history) > 100:
            self.uncertainty_history.pop(0)

    def train_model(self, training_data: List[Dict[str, Any]], epochs: int = 100):
        """训练不确定性估计模型"""
        logger.info(f"Training uncertainty estimator with {len(training_data)} samples")
        
        # 准备训练数据
        inputs = 
        targets = 
        
        for data in training_data:
            state = State(
                time_step=data["state"]["time_step"],
                variables=data["state"]["variables"]
            )
            action = Action(
                name=data["action"]["name"],
                parameters=data["action"]["parameters"]
            )
            predicted_state = State(
                time_step=data["predicted_state"]["time_step"],
                variables=data["predicted_state"]["variables"]
            )
            actual_state = State(
                time_step=data["actual_state"]["time_step"],
                variables=data["actual_state"]["variables"]
            )
            
            # 计算预测误差
            prediction_error = self._calculate_prediction_error(predicted_state, actual_state)
            
            input_features = self._state_action_state_to_features(state, action, predicted_state)
            target_error = torch.FloatTensor([prediction_error]).unsqueeze(0)
            
            inputs.append(input_features.squeeze(0))  # 移除批次维度
            targets.append(target_error.squeeze(0))   # 移除批次维度
        
        # 转换为张量
        inputs_tensor = torch.stack(inputs)
        targets_tensor = torch.stack(targets)
        
        # 创建数据加载器
        dataset = TensorDataset(inputs_tensor, targets_tensor)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
        
        # 训练模型
        self.model.train
        for epoch in range(epochs):
            total_loss = 0.0
            for batch_inputs, batch_targets in dataloader:
                self.optimizer.zero_grad
                
                predictions = self.model(batch_inputs)
                loss = self.criterion(predictions, batch_targets)
                
                loss.backward
                self.optimizer.step
                
                total_loss += loss.item
            
            if epoch % 20 == 0:
                avg_loss = total_loss / len(dataloader)
                logger.info(f"Epoch {epoch}, Average Loss: {avg_loss:.4f}")
        
        self.model.eval
        self.is_trained = True
        logger.info("Uncertainty estimator training completed")
        
    def _calculate_prediction_error(self, predicted_state: State, actual_state: State) -> float:
        """计算预测误差"""
        error = 0.0
        if predicted_state and actual_state:
            # 比较变量值
            for key in predicted_state.variables:
                if key in actual_state.variables:
                    error += abs(predicted_state.variables[key] - actual_state.variables[key]) / 10.0
                    
        return min(error, 1.0)  # 限制误差在0-1之间

class EnvironmentSimulator:
    """环境模拟器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or 
        self.state_predictor = StatePredictor
        self.action_effect_model = ActionEffectModel
        self.uncertainty_estimator = UncertaintyEstimator
        self.logger = logging.getLogger(__name__)
        # 添加训练数据存储
        self.training_data = {
            "state_transitions": ,
            "action_effects": ,
            "uncertainty_data": 
        }
    
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
        _ = await asyncio.sleep(0.005)  # 模拟计算时间
        
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
        scenarios = 
        
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
        _ = await self.uncertainty_estimator.update(prediction_error)
        
        # 存储训练数据用于后续批量训练
        self._store_training_data(experience)
        self.logger.info("Environment model updated from experience.")

    def _store_training_data(self, experience: Dict[str, Any]):
        """存储训练数据"""
        # 存储状态转移数据
        state_transition_data = {
            "state": {
                "time_step": experience["state"].time_step,
                "variables": experience["state"].variables
            },
            "action": {
                "name": experience["action"].name,
                "parameters": experience["action"].parameters
            },
            "next_state": {
                "time_step": experience["next_state"].time_step,
                "variables": experience["next_state"].variables
            }
        }
        self.training_data["state_transitions"].append(state_transition_data)
        
        # 存储动作效果数据
        action_effect_data = {
            "action": {
                "name": experience["action"].name,
                "parameters": experience["action"].parameters
            },
            "state": {
                "time_step": experience["state"].time_step,
                "variables": experience["state"].variables
            },
            "actual_effect": experience["actual_effect"]
        }
        self.training_data["action_effects"].append(action_effect_data)
        
        # 存储不确定性数据
        uncertainty_data = {
            "state": {
                "time_step": experience["state"].time_step,
                "variables": experience["state"].variables
            },
            "action": {
                "name": experience["action"].name,
                "parameters": experience["action"].parameters
            },
            "predicted_state": {
                "time_step": experience["predicted_state"].time_step,
                "variables": experience["predicted_state"].variables
            },
            "actual_state": {
                "time_step": experience["actual_state"].time_step,
                "variables": experience["actual_state"].variables
            }
        }
        self.training_data["uncertainty_data"].append(uncertainty_data)

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
        
    def train_models(self, training_data: Dict[str, List[Dict[str, Any]]] = None, epochs: int = 100):
        """训练所有模型"""
        self.logger.info("Training all environment simulator models")
        
        # 使用传入的训练数据或内部存储的数据
        data_to_use = training_data if training_data is not None else self.training_data
        
        # 训练状态预测器
        if "state_transitions" in data_to_use and data_to_use["state_transitions"]:
            self.state_predictor.train_model(data_to_use["state_transitions"], epochs)
        
        # 训练动作效果模型
        if "action_effects" in data_to_use and data_to_use["action_effects"]:
            self.action_effect_model.train_model(data_to_use["action_effects"], epochs)
        
        # 训练不确定性估计器
        if "uncertainty_data" in data_to_use and data_to_use["uncertainty_data"]:
            self.uncertainty_estimator.train_model(data_to_use["uncertainty_data"], epochs)
        
        # 清空内部存储的训练数据
        if training_data is None:
            self.training_data = {
                "state_transitions": ,
                "action_effects": ,
                "uncertainty_data": 
            }
        
        self.logger.info("All environment simulator models training completed")

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建环境模拟器
    simulator = EnvironmentSimulator
    
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
    async def test_simulation -> None:
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
        
        _ = await simulator.update_model_from_experience(experience)
        print("Model updated from experience")
        
        # 测试模型训练
        training_data = {
            "state_transitions": [
                {
                    "state": {
                        "time_step": 0,
                        "variables": {"temperature": 20.0, "light_level": 0.5, "humidity": 50.0}
                    },
                    "action": {
                        "name": "increase_temperature",
                        "parameters": {"amount": 2.0}
                    },
                    "next_state": {
                        "time_step": 1,
                        "variables": {"temperature": 22.0, "light_level": 0.5, "humidity": 50.0}
                    }
                },
                {
                    "state": {
                        "time_step": 0,
                        "variables": {"temperature": 25.0, "light_level": 0.7, "humidity": 40.0}
                    },
                    "action": {
                        "name": "decrease_temperature",
                        "parameters": {"amount": 3.0}
                    },
                    "next_state": {
                        "time_step": 1,
                        "variables": {"temperature": 22.0, "light_level": 0.7, "humidity": 40.0}
                    }
                }
            ],
            "action_effects": [
                {
                    "action": {
                        "name": "increase_temperature",
                        "parameters": {"amount": 1.0}
                    },
                    "state": {
                        "time_step": 0,
                        "variables": {"temperature": 20.0, "light_level": 0.5, "humidity": 50.0}
                    },
                    "actual_effect": {
                        "temperature_change": 1.0,
                        "light_change": 0.0,
                        "humidity_change": 0.0
                    }
                }
            ],
            "uncertainty_data": [
                {
                    "state": {
                        "time_step": 0,
                        "variables": {"temperature": 20.0, "light_level": 0.5, "humidity": 50.0}
                    },
                    "action": {
                        "name": "increase_temperature",
                        "parameters": {"amount": 2.0}
                    },
                    "predicted_state": {
                        "time_step": 1,
                        "variables": {"temperature": 22.0, "light_level": 0.5, "humidity": 50.0}
                    },
                    "actual_state": {
                        "time_step": 1,
                        "variables": {"temperature": 21.8, "light_level": 0.5, "humidity": 50.0}
                    }
                }
            ]
        }
        
        simulator.train_models(training_data, epochs=50)
        print("Models trained with sample data")
    
    # 运行测试
    asyncio.run(test_simulation)