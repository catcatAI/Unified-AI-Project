"""
因果推理引擎
实现完整的因果推理功能，包括因果图、干预规划器和反事实推理器
"""

import asyncio
import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import random

logger = logging.getLogger(__name__)

@dataclass
class CausalRelationship:
    """因果关系"""
    cause: str
    effect: str
    strength: float  # 因果关系强度 (0-1)
    confidence: float  # 置信度 (0-1)

@dataclass
class Observation:
    """观察数据"""
    id: str
    variables: Dict[str, Any]
    relationships: List[CausalRelationship]
    timestamp: float

@dataclass
class Intervention:
    """干预措施"""
    variable: str
    value: Any
    description: str

@dataclass
class CounterfactualScenario:
    """反事实场景"""
    original_outcome: Any
    counterfactual_outcome: Any
    intervention: Intervention
    confidence: float

class CausalGraph:
    """因果图"""
    
    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}  # 节点信息
        self.edges: Dict[str, Dict[str, CausalRelationship]] = {}  # 边信息
        self.node_types: Dict[str, str] = {}  # 节点类型
        
    async def add_node(self, node_name: str, node_type: str = "unknown", properties: Optional[Dict[str, Any]] = None):
        """添加节点"""
        logger.debug(f"Adding node: {node_name}")
        await asyncio.sleep(0.005)
        
        self.nodes[node_name] = {
            "type": node_type,
            "properties": properties or {}
        }
        self.node_types[node_name] = node_type
        if node_name not in self.edges:
            self.edges[node_name] = {}
            
    async def add_edge(self, cause: str, effect: str, strength: float = 0.5, confidence: float = 0.8):
        """添加边（因果关系）"""
        logger.debug(f"Adding causal edge: {cause} -> {effect}")
        await asyncio.sleep(0.005)
        
        # 确保节点存在
        if cause not in self.nodes:
            await self.add_node(cause)
        if effect not in self.nodes:
            await self.add_node(effect)
            
        # 创建因果关系
        relationship = CausalRelationship(
            cause=cause,
            effect=effect,
            strength=min(1.0, max(0.0, strength)),  # 限制在0-1之间
            confidence=min(1.0, max(0.0, confidence))  # 限制在0-1之间
        )
        
        # 添加边
        if cause not in self.edges:
            self.edges[cause] = {}
        self.edges[cause][effect] = relationship
        
    async def update_edge(self, cause: str, effect: str, strength: Optional[float] = None, 
                         confidence: Optional[float] = None):
        """更新边的属性"""
        logger.debug(f"Updating causal edge: {cause} -> {effect}")
        await asyncio.sleep(0.005)
        
        if cause in self.edges and effect in self.edges[cause]:
            relationship = self.edges[cause][effect]
            if strength is not None:
                relationship.strength = min(1.0, max(0.0, strength))
            if confidence is not None:
                relationship.confidence = min(1.0, max(0.0, confidence))
                
    async def remove_edge(self, cause: str, effect: str):
        """移除边"""
        logger.debug(f"Removing causal edge: {cause} -> {effect}")
        await asyncio.sleep(0.005)
        
        if cause in self.edges and effect in self.edges[cause]:
            del self.edges[cause][effect]
            
    async def get_causes(self, effect_node: str) -> List[str]:
        """获取导致某个效果的所有原因"""
        logger.debug(f"Getting causes for {effect_node}")
        await asyncio.sleep(0.01)
        
        causes = []
        for cause, effects in self.edges.items():
            if effect_node in effects:
                causes.append(cause)
        return causes
        
    async def get_effects(self, cause_node: str) -> List[str]:
        """获取由某个原因导致的所有效果"""
        logger.debug(f"Getting effects for {cause_node}")
        await asyncio.sleep(0.01)
        
        if cause_node in self.edges:
            return list(self.edges[cause_node].keys())
        return []
        
    async def get_paths(self, start_node: str, end_node: str) -> List[List[str]]:
        """获取从起始节点到结束节点的所有路径"""
        logger.debug(f"Getting causal paths from {start_node} to {end_node}")
        await asyncio.sleep(0.01)
        
        paths = []
        visited = set()
        
        async def dfs(current_node: str, path: List[str]):
            if current_node == end_node:
                paths.append(path.copy())
                return
                
            if current_node in visited:
                return
                
            visited.add(current_node)
            
            # 遍历所有直接效果
            if current_node in self.edges:
                for effect_node in self.edges[current_node]:
                    path.append(effect_node)
                    await dfs(effect_node, path)
                    path.pop()
                    
            visited.remove(current_node)
            
        await dfs(start_node, [start_node])
        return paths
        
    def get_relationship(self, cause: str, effect: str) -> Optional[CausalRelationship]:
        """获取两个节点之间的因果关系"""
        if cause in self.edges and effect in self.edges[cause]:
            return self.edges[cause][effect]
        return None

class InterventionPlanner:
    """干预规划器"""
    
    def __init__(self, causal_graph: CausalGraph):
        self.causal_graph = causal_graph
        
    async def optimize(self, target_variable: str, desired_value: Any, 
                      current_state: Dict[str, Any], 
                      constraints: Optional[Dict[str, Any]] = None) -> List[Intervention]:
        """优化干预措施以达到目标值"""
        logger.debug(f"Optimizing intervention for {target_variable} -> {desired_value}")
        await asyncio.sleep(0.01)
        
        interventions = []
        constraints = constraints or {}
        
        # 获取影响目标变量的所有原因
        causes = await self.causal_graph.get_causes(target_variable)
        
        # 对于每个原因，计算需要的干预值
        for cause in causes:
            # 检查约束条件
            if cause in constraints:
                # 如果有约束，使用约束值
                intervention_value = constraints[cause]
            else:
                # 简单的启发式：假设线性关系
                current_value = current_state.get(cause, 0)
                # 计算需要的改变量
                if isinstance(desired_value, (int, float)) and isinstance(current_value, (int, float)):
                    change_amount = (desired_value - current_value) * 0.1  # 简化比例
                    intervention_value = current_value + change_amount
                else:
                    intervention_value = desired_value
                    
            intervention = Intervention(
                variable=cause,
                value=intervention_value,
                description=f"Modify {cause} to influence {target_variable}"
            )
            interventions.append(intervention)
            
        return interventions
        
    async def evaluate_intervention_effect(self, intervention: Intervention, 
                                         current_state: Dict[str, Any]) -> Dict[str, Any]:
        """评估干预措施的效果"""
        logger.debug(f"Evaluating intervention effect for {intervention.variable}")
        await asyncio.sleep(0.01)
        
        effect = {
            "direct_effects": {},
            "indirect_effects": {},
            "confidence": 0.8
        }
        
        # 直接效果
        direct_effects = await self.causal_graph.get_effects(intervention.variable)
        for effect_var in direct_effects:
            relationship = self.causal_graph.get_relationship(intervention.variable, effect_var)
            if relationship:
                effect["direct_effects"][effect_var] = {
                    "strength": relationship.strength,
                    "confidence": relationship.confidence
                }
                
        return effect

class CounterfactualReasoner:
    """反事实推理器"""
    
    def __init__(self, causal_graph: CausalGraph):
        self.causal_graph = causal_graph
        
    async def compute(self, scenario: Dict[str, Any], intervention: Intervention) -> Any:
        """计算反事实结果"""
        logger.debug(f"Computing counterfactual outcome for {intervention.variable}")
        await asyncio.sleep(0.01)
        
        # 获取当前结果
        original_outcome = scenario.get("outcome")
        
        # 简单的反事实计算：基于因果关系强度修改结果
        effects = await self.causal_graph.get_effects(intervention.variable)
        
        # 如果干预变量直接影响结果变量
        if scenario.get("outcome_variable") in effects:
            relationship = self.causal_graph.get_relationship(
                intervention.variable, scenario.get("outcome_variable")
            )
            if relationship:
                # 根据因果关系强度和干预值修改结果
                strength = relationship.strength
                if isinstance(original_outcome, (int, float)):
                    # 数值结果：按比例调整
                    counterfactual_outcome = original_outcome + (intervention.value * strength)
                else:
                    # 非数值结果：简单替换
                    counterfactual_outcome = intervention.value
            else:
                counterfactual_outcome = original_outcome
        else:
            # 没有直接影响，结果不变
            counterfactual_outcome = original_outcome
            
        return counterfactual_outcome
        
    async def estimate_confidence(self, scenario: Dict[str, Any], intervention: Intervention, 
                                counterfactual_outcome: Any) -> float:
        """估计反事实推理的置信度"""
        logger.debug("Estimating counterfactual confidence")
        await asyncio.sleep(0.005)
        
        # 基于因果关系的置信度和路径长度计算总体置信度
        confidence = 0.8  # 默认置信度
        
        # 如果有明确的因果路径，增加置信度
        paths = await self.causal_graph.get_paths(
            intervention.variable, scenario.get("outcome_variable", "")
        )
        if paths:
            # 路径越短，置信度越高
            shortest_path_length = min(len(path) for path in paths)
            confidence += 0.1 / shortest_path_length
            
        return min(1.0, confidence)  # 限制在0-1之间

class CausalReasoningEngine:
    """因果推理引擎"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.causal_graph = CausalGraph()
        self.intervention_planner = InterventionPlanner(self.causal_graph)
        self.counterfactual_reasoner = CounterfactualReasoner(self.causal_graph)
        self.logger = logging.getLogger(__name__)
        
    async def learn_causal_relationships(self, observations: List[Observation]) -> List[CausalRelationship]:
        """从观察数据中学习因果关系"""
        self.logger.info(f"Learning causal relationships from {len(observations)} observations")
        
        learned_relationships = []
        
        try:
            # 处理每个观察数据
            for observation in observations:
                # 添加节点
                for var_name, var_value in observation.variables.items():
                    await self.causal_graph.add_node(var_name, properties={"value": var_value})
                    
                # 添加因果关系
                for relationship in observation.relationships:
                    await self.causal_graph.add_edge(
                        relationship.cause,
                        relationship.effect,
                        relationship.strength,
                        relationship.confidence
                    )
                    learned_relationships.append(relationship)
                    
            self.logger.info(f"Learned {len(learned_relationships)} causal relationships")
            return learned_relationships
            
        except Exception as e:
            self.logger.error(f"Error in causal learning: {e}")
            return []
    
    async def perform_counterfactual_reasoning(self, scenario: Dict[str, Any], 
                                             intervention: Intervention) -> CounterfactualScenario:
        """执行反事实推理"""
        self.logger.info(f"Performing counterfactual reasoning for scenario {scenario.get('name')}")
        
        # 计算反事实结果
        counterfactual_outcome = await self.counterfactual_reasoner.compute(scenario, intervention)
        
        # 估计置信度
        confidence = await self.counterfactual_reasoner.estimate_confidence(
            scenario, intervention, counterfactual_outcome
        )
        
        return CounterfactualScenario(
            original_outcome=scenario.get("outcome"),
            counterfactual_outcome=counterfactual_outcome,
            intervention=intervention,
            confidence=confidence
        )
    
    async def plan_intervention(self, target_variable: str, desired_value: Any, 
                              current_state: Dict[str, Any],
                              constraints: Optional[Dict[str, Any]] = None) -> List[Intervention]:
        """规划干预措施"""
        self.logger.info(f"Planning intervention for {target_variable} -> {desired_value}")
        
        # 计算最优干预策略
        interventions = await self.intervention_planner.optimize(
            target_variable, desired_value, current_state, constraints
        )
        
        return interventions
    
    async def evaluate_intervention(self, intervention: Intervention, 
                                  current_state: Dict[str, Any]) -> Dict[str, Any]:
        """评估干预措施"""
        self.logger.info(f"Evaluating intervention for {intervention.variable}")
        
        # 评估干预效果
        effect = await self.intervention_planner.evaluate_intervention_effect(
            intervention, current_state
        )
        
        return effect
    
    async def update_causal_model(self, new_observations: List[Observation]):
        """更新因果模型"""
        self.logger.info("Updating causal model")
        
        # 学习新的因果关系
        await self.learn_causal_relationships(new_observations)
        
        # 可以添加更多模型更新逻辑
        self.logger.info("Causal model updated")

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建因果推理引擎
    engine = CausalReasoningEngine()
    
    # 创建测试数据
    async def test_causal_reasoning():
        # 创建观察数据
        observation1 = Observation(
            id="obs_1",
            variables={
                "temperature": 25.0,
                "humidity": 60.0,
                "comfort_level": 0.7
            },
            relationships=[
                CausalRelationship("temperature", "comfort_level", 0.8, 0.9),
                CausalRelationship("humidity", "comfort_level", 0.6, 0.8)
            ],
            timestamp=1.0
        )
        
        observation2 = Observation(
            id="obs_2",
            variables={
                "light_level": 0.8,
                "mood": 0.6,
                "productivity": 0.7
            },
            relationships=[
                CausalRelationship("light_level", "mood", 0.7, 0.85),
                CausalRelationship("mood", "productivity", 0.6, 0.8)
            ],
            timestamp=2.0
        )
        
        # 学习因果关系
        relationships = await engine.learn_causal_relationships([observation1, observation2])
        print(f"Learned {len(relationships)} relationships")
        
        # 规划干预措施
        current_state = {
            "temperature": 25.0,
            "humidity": 60.0,
            "light_level": 0.8
        }
        
        interventions = await engine.plan_intervention(
            "comfort_level", 0.9, current_state
        )
        print(f"Planned {len(interventions)} interventions")
        for intervention in interventions:
            print(f"  - {intervention.variable}: {intervention.value}")
        
        # 执行反事实推理
        scenario = {
            "name": "comfort_scenario",
            "outcome": 0.7,
            "outcome_variable": "comfort_level"
        }
        
        intervention = Intervention(
            variable="temperature",
            value=22.0,
            description="Decrease temperature for better comfort"
        )
        
        counterfactual = await engine.perform_counterfactual_reasoning(scenario, intervention)
        print(f"Counterfactual result: {counterfactual.counterfactual_outcome}")
        print(f"Confidence: {counterfactual.confidence:.2f}")
        
        # 评估干预措施
        evaluation = await engine.evaluate_intervention(intervention, current_state)
        print(f"Intervention evaluation: {evaluation}")
    
    # 运行测试
    asyncio.run(test_causal_reasoning())