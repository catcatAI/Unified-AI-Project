"""
决策论系统 - 将价值观转化为行动的核心引擎

负责在不确定性和混沌环境中, 将理智、感性和存在三大支柱的输出,
转化为最优、最稳健的行动方案。实现从"应该做什么"到"如何做"的转化。
"""

import logging
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DecisionStrategy(Enum):
    """决策策略"""
    MAXIMIZE_UTILITY = "maximize_utility"    # 最大化效用
    MINIMIZE_RISK = "minimize_risk"          # 最小化风险
    BALANCED_APPROACH = "balanced_approach"   # 平衡方法
    SATISFICING = "satisficing"               # 满意即可
    MAXIMIN = "maximin"                       # 最大最小化(悲观策略)
    MAXIMAX = "maximax"                       # 最大最大化(乐观策略)


class UncertaintyLevel(Enum):
    """不确定性级别"""
    CERTAIN = "certain"       # 完全确定 - 信息完整
    LOW = "low"               # 低不确定性 - 少量信息缺失
    MEDIUM = "medium"         # 中等不确定性 - 部分信息缺失
    HIGH = "high"             # 高不确定性 - 严重信息缺失
    CHAOTIC = "chaotic"       # 混沌状态 - 极度不可预测


@dataclass
class DecisionOption:
    """决策选项"""
    id: str
    description: str
    action: Dict[str, Any]  # 具体行动内容
    expected_outcomes: List[Dict[str, Any]]  # 预期结果
    resource_requirements: Dict[str, float]  # 资源需求
    time_horizon: float  # 时间跨度(秒)


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
        outcome_key = str(outcome.get("id", "default"))
        prior = self.prior_beliefs.get(outcome_key, 0.5)
        
        # 计算似然
        likelihood = 1.0
        if outcome_key in self.likelihood_functions:
            likelihood = self.likelihood_functions[outcome_key](context)
        
        # 简化的贝叶斯更新
        if likelihood * prior + (1 - likelihood) * (1 - prior) > 0:
            posterior = (likelihood * prior) / (likelihood * prior + (1 - likelihood) * (1 - prior))
        else:
            posterior = prior
        
        return posterior
    
    async def update_beliefs(self, new_evidence: Dict[str, Any]):
        """根据新证据更新先验信念"""
        for outcome_key in self.prior_beliefs:
            adjustment = 0.1 * new_evidence.get("impact", 0)
            self.prior_beliefs[outcome_key] = max(0.0, min(1.0, self.prior_beliefs[outcome_key] + adjustment))
    
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
        outcome_key = str(outcome.get("id", "default"))
        
        # 基于条件概率计算
        if outcome_key in self.conditional_probabilities:
            conditions = context.get("conditions", {})
            prob = self.conditional_probabilities[outcome_key].get(
                str(conditions), 0.5
            )
            return prob
        
        return 0.5
    
    async def update_beliefs(self, new_evidence: Dict[str, Any]):
        """根据新证据更新因果信念"""
        cause = new_evidence.get("cause")
        effect = new_evidence.get("effect")
        if cause and effect:
            if cause not in self.causal_graph:
                self.causal_graph[cause] = []
            if effect not in self.causal_graph[cause]:
                self.causal_graph[cause].append(effect)
    
    def add_causal_link(self, cause: str, effect: str, probability: float):
        """添加因果链接"""
        if cause not in self.causal_graph:
            self.causal_graph[cause] = []
        if effect not in self.causal_graph[cause]:
            self.causal_graph[cause].append(effect)
        if cause not in self.conditional_probabilities:
            self.conditional_probabilities[cause] = {}
        self.conditional_probabilities[cause][effect] = probability


class DecisionTheorySystem:
    """
    决策论系统 - 将价值观转化为行动的核心引擎
    
    负责在不确定性和混沌环境中, 将理智、感性和存在三大支柱的输出,
    转化为最优、最稳健的行动方案。
    """
    
    def __init__(self, system_id: str = "decision_theory_v1"):
        self.system_id = system_id
        self.decision_history: List[Dict[str, Any]] = []
        self.utility_functions: List[UtilityFunction] = []
        self.risk_tolerance: float = 0.5
        self.confidence_threshold: float = 0.7
        self.probability_models: Dict[str, ProbabilityModel] = {}
        
        # 初始化默认概率模型
        self.probability_models["bayesian"] = BayesianModel()
        self.probability_models["causal"] = CausalModel()
        
        logger.info(f"[{self.system_id}] 决策论系统初始化完成")
    
    def add_utility_function(self, name: str, function: Callable[[Dict[str, Any]], float], 
                           weight: float, constraints: List[Callable[[Dict[str, Any]], bool]] = None):
        """添加效用函数"""
        utility_func = UtilityFunction(
            name=name,
            function=function,
            weight=weight,
            constraints=constraints or []
        )
        self.utility_functions.append(utility_func)
        logger.info(f"[{self.system_id}] 效用函数已添加: {name}")
    
    async def make_decision(self, options: List[DecisionOption], 
                           uncertainty_level: UncertaintyLevel = UncertaintyLevel.MEDIUM,
                           context: Dict[str, Any] = None) -> DecisionResult:
        """
        做出最优决策
        
        Args:
            options: 可选决策方案列表
            uncertainty_level: 不确定性级别
            context: 决策上下文
            
        Returns:
            DecisionResult: 决策结果
        """
        if context is None:
            context = {}
        
        logger.info(f"[{self.system_id}] 开始决策过程, 选项数量: {len(options)}")
        
        # 评估每个选项
        evaluated_options = []
        for option in options:
            evaluation = await self._evaluate_option(option, uncertainty_level, context)
            evaluated_options.append((option, evaluation))
        
        # 根据不确定性级别选择决策策略
        strategy = self._select_strategy(uncertainty_level)
        
        # 选择最佳选项
        chosen_option, evaluation = await self._select_optimal(
            evaluated_options, strategy, context
        )
        
        # 构建决策结果
        result = DecisionResult(
            chosen_option=chosen_option,
            expected_utility=evaluation["utility"],
            risk_assessment=evaluation["risk"],
            confidence_level=evaluation["confidence"],
            reasoning_trace=evaluation["reasoning"],
            alternative_options=[opt for opt, _ in evaluated_options if opt != chosen_option],
            strategy_used=strategy
        )
        
        # 记录决策历史
        self.decision_history.append({
            "timestamp": datetime.now().isoformat(),
            "options_count": len(options),
            "chosen_option": chosen_option.id,
            "expected_utility": evaluation["utility"],
            "strategy": strategy.value,
            "uncertainty_level": uncertainty_level.value
        })
        
        logger.info(f"[{self.system_id}] 决策完成: 选择选项 {chosen_option.id}")
        
        return result
    
    async def _evaluate_option(self, option: DecisionOption, 
                               uncertainty_level: UncertaintyLevel,
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个决策选项"""
        
        # 计算效用
        utility = self._calculate_utility(option, context)
        
        # 评估风险
        risk = self._assess_risk(option, uncertainty_level)
        
        # 计算置信度
        confidence = self._calculate_confidence(option, uncertainty_level)
        
        reasoning = [
            f"评估选项 {option.id}: {option.description}",
            f"预期效用: {utility:.3f}",
            f"风险评估: {risk.get('overall_risk', 'unknown')}",
            f"置信度: {confidence:.3f}"
        ]
        
        return {
            "utility": utility,
            "risk": risk,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    def _calculate_utility(self, option: DecisionOption, context: Dict[str, Any]) -> float:
        """计算决策选项的效用值"""
        if not self.utility_functions:
            return 0.5
        
        total_utility = 0.0
        for utility_func in self.utility_functions:
            # 检查约束
            satisfies_constraints = all(
                constraint(context) for constraint in utility_func.constraints
            )
            if satisfies_constraints:
                utility_value = utility_func.function(context)
                total_utility += utility_value * utility_func.weight
        
        # 归一化
        total_weight = sum(uf.weight for uf in self.utility_functions)
        if total_weight > 0:
            normalized_utility = total_utility / total_weight
        else:
            normalized_utility = 0.5
        
        # 考虑资源限制
        resource_satisfaction = self._check_resource_availability(option, context)
        normalized_utility *= resource_satisfaction
        
        return max(0.0, min(1.0, normalized_utility))
    
    def _assess_risk(self, option: DecisionOption, 
                     uncertainty_level: UncertaintyLevel) -> Dict[str, float]:
        """评估决策风险"""
        
        # 基于不确定性级别的风险因子
        uncertainty_risk = {
            UncertaintyLevel.CERTAIN: 0.1,
            UncertaintyLevel.LOW: 0.25,
            UncertaintyLevel.MEDIUM: 0.5,
            UncertaintyLevel.HIGH: 0.75,
            UncertaintyLevel.CHAOTIC: 0.9
        }
        
        base_risk = uncertainty_risk.get(uncertainty_level, 0.5)
        
        # 考虑资源需求
        resource_risk = sum(option.resource_requirements.values()) / len(option.resource_requirements) if option.resource_requirements else 0.5
        
        # 考虑时间跨度
        time_risk = min(1.0, option.time_horizon / 86400) if option.time_horizon > 0 else 0.1  # 超过一天风险增加
        
        overall_risk = (base_risk + resource_risk + time_risk) / 3.0
        
        return {
            "overall_risk": overall_risk,
            "uncertainty_risk": base_risk,
            "resource_risk": resource_risk,
            "time_risk": time_risk
        }
    
    def _calculate_confidence(self, option: DecisionOption, 
                              uncertainty_level: UncertaintyLevel) -> float:
        """计算决策置信度"""
        
        # 置信度与不确定性成反比
        confidence_map = {
            UncertaintyLevel.CERTAIN: 0.95,
            UncertaintyLevel.LOW: 0.8,
            UncertaintyLevel.MEDIUM: 0.6,
            UncertaintyLevel.HIGH: 0.4,
            UncertaintyLevel.CHAOTIC: 0.2
        }
        
        base_confidence = confidence_map.get(uncertainty_level, 0.5)
        
        # 考虑预期结果数量（更多的结果可能意味着更全面的考虑）
        outcome_diversity = min(1.0, len(option.expected_outcomes) / 5.0)
        
        # 考虑资源需求明确性
        resource_clarity = 1.0 if option.resource_requirements else 0.5
        
        # 综合置信度
        confidence = (base_confidence * 0.6 + outcome_diversity * 0.2 + resource_clarity * 0.2)
        
        return max(0.0, min(1.0, confidence))
    
    def _select_strategy(self, uncertainty_level: UncertaintyLevel) -> DecisionStrategy:
        """根据不确定性级别选择决策策略"""
        
        strategy_map = {
            UncertaintyLevel.CERTAIN: DecisionStrategy.MAXIMIZE_UTILITY,
            UncertaintyLevel.LOW: DecisionStrategy.BALANCED_APPROACH,
            UncertaintyLevel.MEDIUM: DecisionStrategy.BALANCED_APPROACH,
            UncertaintyLevel.HIGH: DecisionStrategy.MINIMIZE_RISK,
            UncertaintyLevel.CHAOTIC: DecisionStrategy.MAXIMIN
        }
        
        return strategy_map.get(uncertainty_level, DecisionStrategy.BALANCED_APPROACH)
    
    async def _select_optimal(self, evaluated_options: List[Tuple[DecisionOption, Dict]], 
                             strategy: DecisionStrategy,
                             context: Dict[str, Any]) -> Tuple[DecisionOption, Dict[str, Any]]:
        """根据策略选择最优选项"""
        
        if not evaluated_options:
            raise ValueError("没有可用的决策选项")
        
        # 根据策略排序
        if strategy == DecisionStrategy.MAXIMIZE_UTILITY:
            sorted_options = sorted(evaluated_options, key=lambda x: x[1]["utility"], reverse=True)
        elif strategy == DecisionStrategy.MINIMIZE_RISK:
            sorted_options = sorted(evaluated_options, key=lambda x: x[1]["risk"]["overall_risk"])
        elif strategy == DecisionStrategy.MAXIMIN:
            sorted_options = sorted(evaluated_options, key=lambda x: x[1]["utility"])
        elif strategy == DecisionStrategy.MAXIMAX:
            sorted_options = sorted(evaluated_options, key=lambda x: x[1]["utility"], reverse=True)
        elif strategy == DecisionStrategy.SATISFICING:
            threshold = 0.7
            sorted_options = sorted(
                [opt for opt in evaluated_options if opt[1]["utility"] >= threshold],
                key=lambda x: x[1]["utility"],
                reverse=True
            )
            if not sorted_options:
                sorted_options = [min(evaluated_options, key=lambda x: x[1]["utility"])]
        else:  # BALANCED_APPROACH
            sorted_options = sorted(
                evaluated_options,
                key=lambda x: x[1]["utility"] * (1 - x[1]["risk"]["overall_risk"]) * x[1]["confidence"],
                reverse=True
            )
        
        return sorted_options[0]
    
    def _check_resource_availability(self, option: DecisionOption, context: Dict[str, Any]) -> float:
        """检查资源可用性"""
        available = context.get("available_resources", {})
        
        if not option.resource_requirements:
            return 1.0
        
        satisfaction_count = 0
        total_requirements = len(option.resource_requirements)
        
        for resource, required in option.resource_requirements.items():
            available_amount = available.get(resource, 0)
            if available_amount >= required:
                satisfaction_count += 1
            elif available_amount > 0:
                satisfaction_count += available_amount / required
            # 如果完全不可用，不增加满足度
        
        return satisfaction_count / total_requirements if total_requirements > 0 else 1.0
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history
    
    def clear_history(self):
        """清空决策历史"""
        self.decision_history = []
        logger.info(f"[{self.system_id}] 决策历史已清空")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取决策统计信息"""
        if not self.decision_history:
            return {"message": "没有决策历史"}
        
        total_decisions = len(self.decision_history)
        strategies_used = {}
        avg_utility = 0.0
        
        for decision in self.decision_history:
            strategy = decision.get("strategy", "unknown")
            strategies_used[strategy] = strategies_used.get(strategy, 0) + 1
            avg_utility += decision.get("expected_utility", 0)
        
        avg_utility /= total_decisions
        
        return {
            "total_decisions": total_decisions,
            "strategies_used": strategies_used,
            "average_utility": avg_utility
        }
