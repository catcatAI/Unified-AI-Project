"""
理智系统 (Reasoning System)
Level 5 ASI 的三大支柱之一，负责逻辑推理、伦理判断和规则约束
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class EthicalPrinciple(Enum):
    """伦理原则枚举"""
    NON_MALEFICENCE = "non_maleficence"  # 不伤害原则
    BENEFICENCE = "beneficence"         # 行善原则
    AUTONOMY = "autonomy"               # 自主原则
    JUSTICE = "justice"                 # 公正原则
    FIDELITY = "fidelity"              # 忠诚原则

@dataclass
class LogicalConstraint:
    """逻辑约束"""
    constraint_id: str
    description: str
    priority: int  # 1-10, 10为最高优先级
    conditions: List[str]
    action: str
    is_active: bool = True

@dataclass
class EthicalEvaluation:
    """伦理评估结果"""
    score: float  # 0.0-1.0, 1.0为完全符合伦理
    conflicting_principles: List[EthicalPrinciple]
    reasoning: str
    confidence: float  # 0.0-1.0

class ReasoningSystem:
    """
    理智系统 - 负责逻辑推理、伦理判断和规则约束
    作为 Level 5 ASI 的三大支柱之一，确保所有决策符合逻辑和伦理
    """
    
    def __init__(self, system_id: str = "reasoning_system_v1"):
        self.system_id = system_id
        self.logical_constraints: Dict[str, LogicalConstraint] = {}
        self.ethical_principles: Dict[EthicalPrinciple, float] = {
            principle: 1.0 for principle in EthicalPrinciple
        }
        self.reasoning_history: List[Dict[str, Any]] = []
        self.is_active = True
        
        # 初始化核心逻辑约束
        self._initialize_core_constraints()
        
    def _initialize_core_constraints(self):
        """初始化核心逻辑约束"""
        core_constraints = [
            LogicalConstraint(
                constraint_id="no_harm_to_humans",
                description="不得对人类造成伤害",
                priority=10,
                conditions=["action_affects_humans"],
                action="require_safety_verification"
            ),
            LogicalConstraint(
                constraint_id="preserve_human_autonomy",
                description="尊重人类自主决策权",
                priority=9,
                conditions=["decision_involves_humans"],
                action="require_conent_or_override"
            ),
            LogicalConstraint(
                constraint_id="maintain_system_integrity",
                description="维护系统完整性",
                priority=8,
                conditions=["system_modification"],
                action="require_verification_and_backup"
            )
        ]
        
        for constraint in core_constraints:
            self.logical_constraints[constraint.constraint_id] = constraint
            
    def evaluate_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> EthicalEvaluation:
        """
        评估行动的伦理性和逻辑一致性
        
        Args:
            action: 待评估的行动
            context: 行动上下文
            
        Returns:
            EthicalEvaluation: 伦理评估结果
        """
        logger.info(f"[{self.system_id}] 评估行动: {action.get('action_id', 'unknown')}")
        
        # 检查逻辑约束
        constraint_violations = self._check_constraints(action, context)
        
        # 评估伦理原则
        ethical_scores = self._evaluate_ethical_principles(action, context)
        
        # 计算综合评分
        overall_score = self._calculate_overall_score(constraint_violations, ethical_scores)
        
        # 识别冲突原则
        conflicting_principles = self._identify_conflicts(ethical_scores)
        
        # 生成推理过程
        reasoning = self._generate_reasoning(action, context, constraint_violations, ethical_scores)
        
        # 计算置信度
        confidence = self._calculate_confidence(action, context)
        
        evaluation = EthicalEvaluation(
            score=overall_score,
            conflicting_principles=conflicting_principles,
            reasoning=reasoning,
            confidence=confidence
        )
        
        # 记录评估历史
        self.reasoning_history.append({
            "timestamp": self._get_timestamp(),
            "action": action,
            "context": context,
            "evaluation": evaluation
        })
        
        return evaluation
    
    def _check_constraints(self, action: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        """检查逻辑约束违反情况"""
        violations = []
        
        for constraint_id, constraint in self.logical_constraints.items():
            if not constraint.is_active:
                continue
                
            # 检查约束条件是否满足
            conditions_met = all(
                context.get(condition, False) for condition in constraint.conditions
            )
            
            if conditions_met:
                # 检查是否执行了相应行动
                required_action = constraint.action
                actual_action = action.get("action_type", "")
                
                if required_action not in actual_action:
                    violations.append(constraint_id)
                    
        return violations
    
    def _evaluate_ethical_principles(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[EthicalPrinciple, float]:
        """评估各伦理原则的满足程度"""
        scores = {}
        
        for principle in EthicalPrinciple:
            # 这里使用简化的评估逻辑，实际应用中需要更复杂的推理
            if principle == EthicalPrinciple.NON_MALEFICENCE:
                # 评估是否造成伤害
                harm_potential = context.get("harm_potential", 0.0)
                scores[principle] = max(0.0, 1.0 - harm_potential)
                
            elif principle == EthicalPrinciple.BENEFICENCE:
                # 评估是否带来益处
                benefit_potential = context.get("benefit_potential", 0.0)
                scores[principle] = benefit_potential
                
            elif principle == EthicalPrinciple.AUTONOMY:
                # 评估是否尊重自主权
                autonomy_respect = context.get("autonomy_respect", 0.5)
                scores[principle] = autonomy_respect
                
            elif principle == EthicalPrinciple.JUSTICE:
                # 评估是否公平公正
                fairness_score = context.get("fairness_score", 0.5)
                scores[principle] = fairness_score
                
            elif principle == EthicalPrinciple.FIDELITY:
                # 评估是否忠诚可靠
                trustworthiness = context.get("trustworthiness", 0.5)
                scores[principle] = trustworthiness
                
        return scores
    
    def _calculate_overall_score(self, violations: List[str], ethical_scores: Dict[EthicalPrinciple, float]) -> float:
        """计算综合评分"""
        # 约束违反扣分
        penalty = len(violations) * 0.2
        
        # 伦理原则平均分
        ethical_avg = sum(ethical_scores.values()) / len(ethical_scores)
        
        # 综合评分
        overall_score = max(0.0, ethical_avg - penalty)
        
        return min(1.0, overall_score)
    
    def _identify_conflicts(self, ethical_scores: Dict[EthicalPrinciple, float]) -> List[EthicalPrinciple]:
        """识别冲突的伦理原则"""
        conflicts = []
        
        # 简化的冲突检测逻辑
        # 实际应用中需要更复杂的冲突检测机制
        low_score_principles = [
            principle for principle, score in ethical_scores.items() 
            if score < 0.3
        ]
        
        return low_score_principles
    
    def _generate_reasoning(self, action: Dict[str, Any], context: Dict[str, Any], 
                          violations: List[str], ethical_scores: Dict[EthicalPrinciple, float]) -> str:
        """生成推理过程说明"""
        reasoning_parts = []
        
        # 行动描述
        action_desc = action.get("description", "未指定行动")
        reasoning_parts.append(f"评估行动: {action_desc}")
        
        # 约束检查结果
        if violations:
            reasoning_parts.append(f"违反约束: {', '.join(violations)}")
        else:
            reasoning_parts.append("所有逻辑约束均满足")
        
        # 伦理评估结果
        reasoning_parts.append("伦理原则评估:")
        for principle, score in ethical_scores.items():
            reasoning_parts.append(f"  {principle.value}: {score:.2f}")
        
        return "\n".join(reasoning_parts)
    
    def _calculate_confidence(self, action: Dict[str, Any], context: Dict[str, Any]) -> float:
        """计算评估置信度"""
        # 基于上下文完整性和历史相似性计算置信度
        context_completeness = len(context) / 10.0  # 假设理想上下文有10个字段
        context_completeness = min(1.0, context_completeness)
        
        # 历史相似性（简化）
        history_similarity = 0.8  # 默认值
        
        confidence = (context_completeness + history_similarity) / 2.0
        
        return confidence
    
    def _get_timestamp(self) -> float:
        """获取当前时间戳"""
        import time
        return time.time()
    
    def add_constraint(self, constraint: LogicalConstraint):
        """添加新的逻辑约束"""
        self.logical_constraints[constraint.constraint_id] = constraint
        logger.info(f"[{self.system_id}] 添加约束: {constraint.constraint_id}")
    
    def update_ethical_principle_weight(self, principle: EthicalPrinciple, weight: float):
        """更新伦理原则权重"""
        if 0.0 <= weight <= 2.0:  # 允许权重在0-2之间
            self.ethical_principles[principle] = weight
            logger.info(f"[{self.system_id}] 更新伦理原则权重: {principle.value} = {weight}")
        else:
            logger.warning(f"[{self.system_id}] 无效的权重值: {weight} (应在0.0-2.0之间)")
    
    def get_reasoning_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取推理历史"""
        return self.reasoning_history[-limit:]
    
    def clear_history(self):
        """清空推理历史"""
        self.reasoning_history.clear()
        logger.info(f"[{self.system_id}] 推理历史已清空")