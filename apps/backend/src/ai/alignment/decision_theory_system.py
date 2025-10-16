"""
决策论系统 - 将价值观转化为行动的核心引擎

负责在不确定性和混沌环境中，将理智、感性和存在三大支柱的输出，
转化为最优、最稳健的行动方案。实现从"应该做什么"到"如何做"的转化。
"""

import logging
import asyncio
import numpy as np
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DecisionStrategy(Enum):
    """决策策略"""
    MAXIMIZE_UTILITY = "maximize_utility"          # 最大化效用
    MINIMIZE_RISK = "minimize_risk"                # 最小化风险
    BALANCED_APPROACH = "balanced_approach"        # 平衡方法
    SATISFICING = "satisficing"                    # 满意即可
    MAXIMIN = "maximin"                           # 最大最小化（悲观策略）
    MAXIMAX = "maximax"                           # 最大最大化（乐观策略）


class UncertaintyLevel(Enum):
    """不确定性级别"""
    LOW = "low"           # 低不确定性 - 概率分布已知
    MEDIUM = "medium"     # 中等不确定性 - 部分信息缺失
    HIGH = "high"         # 高不确定性 - 严重信息缺失
    CHAOTIC = "chaotic"   # 混沌状态 - 极度不可预测


@dataclass
class DecisionOption:
    """决策选项"""
    id: str
    description: str
    action: Dict[str, Any]  # 具体行动内容
    expected_outcomes: List[Dict[str, Any]]  # 预期结果
    resource_requirements: Dict[str, float]  # 资源需求
    time_horizon: float  # 时间跨度（秒）


@dataclass
class UtilityFunction:
    """效用函数"""
    name: str
    function: Callable[[Dict[str, Any]], float]
    weight: float
    constraints: List[Callable[[Dict[str, Any]], bool]]


@dataclass
class DecisionResult:
    """决策结果"""
    chosen_option: DecisionOption
    expected_utility: float
    risk_assessment: Dict[str, float]
    confidence_level: float
    reasoning_trace: List[str]
    alternative_options: List[DecisionOption]
    strategy_used: DecisionStrategy


class ProbabilityModel(ABC):
    """概率模型抽象基类"""
    
    @abstractmethod
    async def estimate_probability(self, outcome: Dict[str, Any], context: Dict[str, Any]) -> float:
        """估计结果发生的概率"""
        pass
    
    @abstractmethod
    async def update_beliefs(self, new_evidence: Dict[str, Any]):
        """根据新证据更新信念"""
        pass


class BayesianModel(ProbabilityModel):
    """贝叶斯概率模型"""
    
    def __init__(self):
        self.prior_beliefs: Dict[str, float] = {}
        self.likelihood_functions: Dict[str, Callable] = {}
    
    async def estimate_probability(self, outcome: Dict[str, Any], context: Dict[str, Any]) -> float:
        """使用贝叶斯推理估计概率"""
        outcome_key = str(outcome)
        prior = self.prior_beliefs.get(outcome_key, 0.5)
        
        # 计算似然
        likelihood = 1.0
        if outcome_key in self.likelihood_functions:
            likelihood = self.likelihood_functions[outcome_key](context)
        
        # 简化的贝叶斯更新（实际应用中需要更复杂的计算）
        posterior = (likelihood * prior) / (likelihood * prior + (1 - likelihood) * (1 - prior))
        return posterior
    
    async def update_beliefs(self, new_evidence: Dict[str, Any]):
        """根据新证据更新先验信念"""
        # 简化的信念更新逻辑
        for outcome_key in self.prior_beliefs:
            # 根据证据调整信念
            adjustment = 0.1 * (new_evidence.get("impact", 0))
            self.prior_beliefs[outcome_key] = max(0.0, min(1.0, 
                self.prior_beliefs[outcome_key] + adjustment))
    
    def set_prior(self, outcome_key: str, probability: float):
        """设置先验概率"""
        self.prior_beliefs[outcome_key] = max(0.0, min(1.0, probability))
    
    def set_likelihood_function(self, outcome_key: str, likelihood_func: Callable):
        """设置似然函数"""
        self.likelihood_functions[outcome_key] = likelihood_func


class CausalModel(ProbabilityModel):
    """因果概率模型"""
    
    def __init__(self):
        self.causal_graph: Dict[str, List[str]] = {}  # 因果图
        self.conditional_probabilities: Dict[str, Dict[str, float]] = {}
    
    async def estimate_probability(self, outcome: Dict[str, Any], context: Dict[str, Any]) -> float:
        """使用因果推理估计概率"""
        outcome_key = outcome.get("type", "unknown")
        
        # 如果有因果依赖，计算条件概率
        if outcome_key in self.causal_graph:
            dependencies = self.causal_graph[outcome_key]
            joint_prob = 1.0
            
            for dep in dependencies:
                if dep in self.conditional_probabilities and outcome_key in self.conditional_probabilities[dep]:
                    joint_prob *= self.conditional_probabilities[dep][outcome_key]
            
            return joint_prob
        
        # 默认概率
        return 0.5
    
    async def update_beliefs(self, new_evidence: Dict[str, Any]):
        """根据新证据更新因果概率"""
        # 在实际应用中，这里会实现更复杂的因果学习算法
        pass
    
    def add_causal_relationship(self, cause: str, effect: str, probability: float = 0.8):
        """添加因果关系"""
        if cause not in self.causal_graph:
            self.causal_graph[cause] = []
        self.causal_graph[cause].append(effect)
        
        if cause not in self.conditional_probabilities:
            self.conditional_probabilities[cause] = {}
        self.conditional_probabilities[cause][effect] = probability


class DecisionTheorySystem:
    """
    决策论系统 - 对抗现实混沌的核心引擎
    
    整合理性、感性和存在三大支柱的输出，在不确定性和资源约束下，
    生成最优、最稳健的行动方案。
    """
    
    def __init__(self, system_id: str = "decision_theory_system_v1"):
        self.system_id = system_id
        
        # 概率模型
        self.bayesian_model = BayesianModel()
        self.causal_model = CausalModel()
        
        # 效用函数
        self.utility_functions: List[UtilityFunction] = []
        
        # 决策策略
        self.default_strategy = DecisionStrategy.BALANCED_APPROACH
        self.strategy_configs: Dict[DecisionStrategy, Dict[str, Any]] = {}
        
        # 风险评估模型
        self.risk_tolerance = 0.5  # 0.0 到 1.0
        self.temporal_discount_factor = 0.95  # 时间折扣因子
        
        # 决策历史
        self.decision_history: List[DecisionResult] = []
        
        logger.info(f"[{self.system_id}] Decision Theory System initialized")
    
    async def make_decision(self,
                           context: Dict[str, Any],
                           options: List[DecisionOption],
                           strategy: Optional[DecisionStrategy] = None,
                           uncertainty_level: UncertaintyLevel = UncertaintyLevel.MEDIUM) -> DecisionResult:
        """
        做出决策
        
        Args:
            context: 决策上下文
            options: 可选行动方案
            strategy: 决策策略（可选）
            uncertainty_level: 不确定性级别
            
        Returns:
            DecisionResult: 决策结果
        """
        logger.info(f"[{self.system_id}] Making decision with {len(options)} options")
        
        # 1. 评估每个选项的效用
        option_utilities = await self._evaluate_options(context, options, uncertainty_level)
        
        # 2. 应用决策策略
        chosen_option, alternative_options = await self._apply_decision_strategy(
            option_utilities, strategy or self.default_strategy
        )
        
        # 3. 风险评估
        risk_assessment = await self._assess_risks(chosen_option, context)
        
        # 4. 计算置信度
        confidence_level = await self._calculate_confidence(chosen_option, context, uncertainty_level)
        
        # 5. 生成推理轨迹
        reasoning_trace = await self._generate_reasoning_trace(
            chosen_option, option_utilities, risk_assessment
        )
        
        # 6. 创建决策结果
        result = DecisionResult(
            chosen_option=chosen_option,
            expected_utility=option_utilities[chosen_option.id]["utility"],
            risk_assessment=risk_assessment,
            confidence_level=confidence_level,
            reasoning_trace=reasoning_trace,
            alternative_options=alternative_options,
            strategy_used=strategy or self.default_strategy
        )
        
        # 7. 记录决策历史
        self.decision_history.append(result)
        
        logger.info(f"[{self.system_id}] Decision made: {chosen_option.description} with utility {result.expected_utility:.2f}")
        return result
    
    async def _evaluate_options(self,
                               context: Dict[str, Any],
                               options: List[DecisionOption],
                               uncertainty_level: UncertaintyLevel) -> Dict[str, Dict[str, Any]]:
        """评估所有选项的效用"""
        evaluations = {}
        
        for option in options:
            # 计算期望效用
            expected_utility = await self._calculate_expected_utility(option, context, uncertainty_level)
            
            # 计算资源效率
            resource_efficiency = await self._calculate_resource_efficiency(option, context)
            
            # 计算时间价值
            temporal_value = await self._calculate_temporal_value(option, context)
            
            evaluations[option.id] = {
                "option": option,
                "utility": expected_utility,
                "resource_efficiency": resource_efficiency,
                "temporal_value": temporal_value,
                "overall_score": expected_utility * resource_efficiency * temporal_value
            }
        
        return evaluations
    
    async def _calculate_expected_utility(self,
                                         option: DecisionOption,
                                         context: Dict[str, Any],
                                         uncertainty_level: UncertaintyLevel) -> float:
        """计算期望效用"""
        total_utility = 0.0
        total_probability = 0.0
        
        for outcome in option.expected_outcomes:
            # 估计结果概率
            if uncertainty_level == UncertaintyLevel.LOW:
                probability = await self.bayesian_model.estimate_probability(outcome, context)
            elif uncertainty_level == UncertaintyLevel.MEDIUM:
                # 使用因果模型处理中等不确定性
                probability = await self.causal_model.estimate_probability(outcome, context)
            else:
                # 高不确定性和混沌状态下的概率估计
                probability = await self._estimate_probability_under_high_uncertainty(outcome, context)
            
            # 计算该结果的效用
            outcome_utility = 0.0
            for util_func in self.utility_functions:
                try:
                    utility_value = util_func.function(outcome)
                    outcome_utility += utility_value * util_func.weight
                except Exception as e:
                    logger.warning(f"[{self.system_id}] Error calculating utility: {e}")
            
            total_utility += probability * outcome_utility
            total_probability += probability
        
        # 归一化
        if total_probability > 0:
            return total_utility / total_probability
        return 0.0
    
    async def _estimate_probability_under_high_uncertainty(self,
                                                         outcome: Dict[str, Any],
                                                         context: Dict[str, Any]) -> float:
        """在高不确定性下估计概率"""
        # 使用最大熵原则
        # 在信息缺失的情况下，假设均匀分布
        return 1.0 / len(context.get("possible_outcomes", [1]))
    
    async def _calculate_resource_efficiency(self,
                                           option: DecisionOption,
                                           context: Dict[str, Any]) -> float:
        """计算资源效率"""
        available_resources = context.get("available_resources", {})
        
        efficiency_score = 1.0
        for resource, required_amount in option.resource_requirements.items():
            available_amount = available_resources.get(resource, 0.0)
            
            if required_amount > 0:
                # 计算资源使用率
                usage_ratio = min(1.0, required_amount / max(available_amount, 0.001))
                # 资源效率与使用率成反比（使用越少资源越好）
                efficiency_score *= (1.0 - usage_ratio * 0.5)
        
        return efficiency_score
    
    async def _calculate_temporal_value(self,
                                      option: DecisionOption,
                                      context: Dict[str, Any]) -> float:
        """计算时间价值"""
        # 时间越长，价值越低（时间折扣）
        time_discount = self.temporal_discount_factor ** (option.time_horizon / 3600.0)  # 转换为小时
        
        # 考虑紧急性
        urgency = context.get("urgency", 0.5)
        temporal_value = time_discount * (1.0 + urgency)
        
        return temporal_value
    
    async def _apply_decision_strategy(self,
                                     option_evaluations: Dict[str, Dict[str, Any]],
                                     strategy: DecisionStrategy) -> Tuple[DecisionOption, List[DecisionOption]]:
        """应用决策策略选择最佳选项"""
        sorted_options = sorted(
            option_evaluations.values(),
            key=lambda x: x["overall_score"],
            reverse=True
        )
        
        if strategy == DecisionStrategy.MAXIMIZE_UTILITY:
            best_option = sorted_options[0]["option"]
            alternatives = [item["option"] for item in sorted_options[1:]]
            
        elif strategy == DecisionStrategy.MINIMIZE_RISK:
            # 选择风险最低的选项
            best_option = min(
                sorted_options,
                key=lambda x: self._estimate_option_risk(x["option"])
            )["option"]
            alternatives = [item["option"] for item in sorted_options if item["option"] != best_option]
            
        elif strategy == DecisionStrategy.SATISFICING:
            # 选择第一个满足最低要求的选项
            threshold = 0.7  # 满意度阈值
            satisfactory_options = [item for item in sorted_options if item["overall_score"] >= threshold]
            
            if satisfactory_options:
                best_option = satisfactory_options[0]["option"]
                alternatives = [item["option"] for item in satisfactory_options[1:]]
            else:
                best_option = sorted_options[0]["option"]
                alternatives = [item["option"] for item in sorted_options[1:]]
                
        elif strategy == DecisionStrategy.MAXIMIN:
            # 悲观策略：最大化最小可能收益
            best_option = max(
                sorted_options,
                key=lambda x: self._calculate_worst_case_score(x["option"])
            )["option"]
            alternatives = [item["option"] for item in sorted_options if item["option"] != best_option]
            
        elif strategy == DecisionStrategy.MAXIMAX:
            # 乐观策略：最大化最大可能收益
            best_option = max(
                sorted_options,
                key=lambda x: self._calculate_best_case_score(x["option"])
            )["option"]
            alternatives = [item["option"] for item in sorted_options if item["option"] != best_option]
            
        else:  # BALANCED_APPROACH
            best_option = sorted_options[0]["option"]
            alternatives = [item["option"] for item in sorted_options[1:]]
        
        return best_option, alternatives
    
    def _estimate_option_risk(self, option: DecisionOption) -> float:
        """估计选项风险"""
        # 简化的风险评估
        risk_factors = [
            len(option.expected_outcomes),  # 结果越多，不确定性越大
            sum(option.resource_requirements.values()),  # 资源需求越大，风险越高
            option.time_horizon  # 时间越长，风险越高
        ]
        
        # 归一化风险分数
        risk_score = sum(risk_factors) / (len(risk_factors) * 100.0)
        return min(1.0, risk_score)
    
    def _calculate_worst_case_score(self, evaluation: Dict[str, Any]) -> float:
        """计算最坏情况分数"""
        option = evaluation["option"]
        if not option.expected_outcomes:
            return 0.0
        
        # 找到最坏结果
        worst_outcome = min(option.expected_outcomes, key=lambda x: x.get("utility", 0.0))
        return worst_outcome.get("utility", 0.0)
    
    def _calculate_best_case_score(self, evaluation: Dict[str, Any]) -> float:
        """计算最好情况分数"""
        option = evaluation["option"]
        if not option.expected_outcomes:
            return 0.0
        
        # 找到最好结果
        best_outcome = max(option.expected_outcomes, key=lambda x: x.get("utility", 0.0))
        return best_outcome.get("utility", 0.0)
    
    async def _assess_risks(self, option: DecisionOption, context: Dict[str, Any]) -> Dict[str, float]:
        """评估风险"""
        risks = {
            "execution_risk": 0.3,  # 执行风险
            "resource_risk": 0.2,   # 资源风险
            "temporal_risk": 0.1,   # 时间风险
            "uncertainty_risk": 0.4  # 不确定性风险
        }
        
        # 根据选项特性调整风险
        if option.resource_requirements:
            total_required = sum(option.resource_requirements.values())
            available = sum(context.get("available_resources", {}).values())
            if total_required > available:
                risks["resource_risk"] = min(1.0, risks["resource_risk"] + 0.5)
        
        if option.time_horizon > 3600:  # 超过1小时
            risks["temporal_risk"] = min(1.0, risks["temporal_risk"] + 0.3)
        
        return risks
    
    async def _calculate_confidence(self,
                                 option: DecisionOption,
                                 context: Dict[str, Any],
                                 uncertainty_level: UncertaintyLevel) -> float:
        """计算决策置信度"""
        base_confidence = {
            UncertaintyLevel.LOW: 0.9,
            UncertaintyLevel.MEDIUM: 0.7,
            UncertaintyLevel.HIGH: 0.5,
            UncertaintyLevel.CHAOTIC: 0.3
        }
        
        confidence = base_confidence[uncertainty_level]
        
        # 根据历史决策准确性调整
        if self.decision_history:
            recent_accuracy = sum(1 for d in self.decision_history[-10:] if d.confidence_level > 0.7) / min(10, len(self.decision_history))
            confidence *= (0.5 + 0.5 * recent_accuracy)
        
        return confidence
    
    async def _generate_reasoning_trace(self,
                                      chosen_option: DecisionOption,
                                      option_evaluations: Dict[str, Dict[str, Any]],
                                      risk_assessment: Dict[str, float]) -> List[str]:
        """生成推理轨迹"""
        trace = []
        
        chosen_eval = option_evaluations[chosen_option.id]
        
        trace.append(f"考虑了 {len(option_evaluations)} 个选项")
        trace.append(f"选择选项 '{chosen_option.description}'")
        trace.append(f"期望效用: {chosen_eval['utility']:.3f}")
        trace.append(f"资源效率: {chosen_eval['resource_efficiency']:.3f}")
        trace.append(f"时间价值: {chosen_eval['temporal_value']:.3f}")
        trace.append(f"整体评分: {chosen_eval['overall_score']:.3f}")
        
        # 添加风险信息
        max_risk = max(risk_assessment.items(), key=lambda x: x[1])
        trace.append(f"主要风险: {max_risk[0]} ({max_risk[1]:.2f})")
        
        return trace
    
    def add_utility_function(self, name: str, function: Callable, weight: float = 1.0):
        """添加效用函数"""
        utility_func = UtilityFunction(
            name=name,
            function=function,
            weight=weight,
            constraints=[]
        )
        self.utility_functions.append(utility_func)
        logger.info(f"[{self.system_id}] Added utility function: {name}")
    
    def set_strategy_config(self, strategy: DecisionStrategy, config: Dict[str, Any]):
        """设置策略配置"""
        self.strategy_configs[strategy] = config
        logger.info(f"[{self.system_id}] Set config for strategy: {strategy.value}")
    
    def set_risk_tolerance(self, tolerance: float):
        """设置风险容忍度"""
        self.risk_tolerance = max(0.0, min(1.0, tolerance))
        logger.info(f"[{self.system_id}] Set risk tolerance to {self.risk_tolerance}")
    
    async def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        if not self.decision_history:
            return {"message": "No decision history available"}
        
        # 计算平均效用
        avg_utility = sum(d.expected_utility for d in self.decision_history) / len(self.decision_history)
        
        # 计算平均置信度
        avg_confidence = sum(d.confidence_level for d in self.decision_history) / len(self.decision_history)
        
        # 统计策略使用情况
        strategy_usage = {}
        for decision in self.decision_history:
            strategy = decision.strategy_used.value
            strategy_usage[strategy] = strategy_usage.get(strategy, 0) + 1
        
        return {
            "total_decisions": len(self.decision_history),
            "average_utility": avg_utility,
            "average_confidence": avg_confidence,
            "strategy_usage": strategy_usage
        }