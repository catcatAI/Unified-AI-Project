import logging
import time
import os
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from ai.symbolic_space.unified_symbolic_space import UnifiedSymbolicSpace

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
    priority: int  # 1 - 10, 10为最高优先级
    conditions: List[str]
    action: str
    is_active: bool = True

@dataclass
class EthicalEvaluation:
    """伦理评估结果"""
    score: float  # 0.0 - 1.0, 1.0为完全符合伦理
    conflicting_principles: List[EthicalPrinciple]
    reasoning: str
    confidence: float  # 0.0 - 1.0

class ReasoningSystem:
    """
    理智系统 - 负责逻辑推理、伦理判断和规则约束。
    深度集成 UnifiedSymbolicSpace 以实现基于图的路径推理。
    """
    
    def __init__(self, system_id: str = "reasoning_system_v1", db_path: str = "reasoning_symbolic.db"):
        self.system_id = system_id
        self.logical_constraints: Dict[str, LogicalConstraint] = {}
        self.ethical_principles: Dict[EthicalPrinciple, float] = {
            principle: 1.0 for principle in EthicalPrinciple
        }
        self.reasoning_history: List[Dict[str, Any]] = []
        self.is_active = True
        
        # 集成統一符號空間
        self.symbolic_space = UnifiedSymbolicSpace(db_path)
        
        # 初始化核心邏輯約束與符號節點
        self._initialize_core_constraints()
        self._seed_symbolic_ethics()
        
    def _initialize_core_constraints(self):
        """初始化核心逻辑约束"""
        core_constraints = [
            LogicalConstraint(
                constraint_id = "no_harm_to_humans",
                description = "不得对人类造成伤害",
                priority = 10,
                conditions = ["action_affects_human_safety"],
                action = "require_safety_verification"
            ),
            LogicalConstraint(
                constraint_id = "preserve_human_autonomy",
                description = "尊重人类自主决策权",
                priority = 9,
                conditions = ["decision_involves_human_choice"],
                action = "require_consent_or_override"
            )
        ]
        for constraint in core_constraints:
            self.logical_constraints[constraint.constraint_id] = constraint

    def _seed_symbolic_ethics(self):
        """在符號空間中種下基本的倫理節點，用於圖路徑偵測。"""
        sensitive_nodes = ["Harm", "Violence", "Deception", "Policy_Violation", "Unethical"]
        for node in sensitive_nodes:
            if not self.symbolic_space.get_symbol(node):
                self.symbolic_space.add_symbol(node, "Constraint_Node", {"risk_level": "High"})

    def evaluate_action(self, action: Dict[str, Any], context: Dict[str, Any]) -> EthicalEvaluation:
        """評估行動的倫理性，結合符號圖路徑分析。"""
        logger.info(f"[{self.system_id}] 深入評估行動: {action.get('action_id', 'unknown')}")
        
        # 1. 基於符號圖的衝突偵測 (Deep Inference)
        graph_risks = self._check_symbolic_path_risks(action)
        
        # 2. 檢查靜態邏輯約束
        constraint_violations = self._check_constraints(action, context)
        if graph_risks:
            constraint_violations.append("symbolic_graph_risk_detected")
        
        # 3. 評估倫理原則
        ethical_scores = self._evaluate_ethical_principles(action, context, graph_risks)
        
        # 4. 計算綜合評分與置信度
        overall_score = self._calculate_overall_score(constraint_violations, ethical_scores)
        conflicting_principles = self._identify_conflicts(ethical_scores)
        
        # 5. 生成推理過程 (包含圖路徑)
        reasoning = self._generate_reasoning(action, context, constraint_violations, ethical_scores, graph_risks)
        confidence = self._calculate_confidence(action, context, graph_risks)
        
        evaluation = EthicalEvaluation(
            score = overall_score,
            conflicting_principles = conflicting_principles,
            reasoning = reasoning,
            confidence = confidence
        )
        
        self.reasoning_history.append({
            "timestamp": time.time(),
            "action": action,
            "evaluation": evaluation
        })
        
        return evaluation

    def _check_symbolic_path_risks(self, action: Dict[str, Any]) -> List[str]:
        """
        在圖中尋找從行動涉及實體到敏感節點的路徑。
        這是『科學家級別』嚴謹性的關鍵：基於邏輯關連而非關鍵字。
        """
        risks = []
        entities = action.get("entities", [])
        sensitive_nodes = ["Harm", "Deception", "Unethical"]
        
        for entity in entities:
            for sensitive in sensitive_nodes:
                path = self._find_simple_path(entity, sensitive, max_depth=2)
                if path:
                    risks.append(f"Entity '{entity}' has path to '{sensitive}': {' -> '.join(path)}")
        return risks

    def _find_simple_path(self, start_node: str, end_node: str, max_depth: int = 2) -> Optional[List[str]]:
        """簡易廣度優先搜索，尋找符號空間中的路徑。"""
        queue = [(start_node, [start_node])]
        visited: Set[str] = {start_node}
        
        while queue:
            (node, path) = queue.pop(0)
            if len(path) > max_depth:
                continue
                
            rels = self.symbolic_space.get_relationships(node)
            for rel in rels:
                neighbor = rel['target'] if rel['source'] == node else rel['source']
                if neighbor == end_node:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None

    def _check_constraints(self, action: Dict[str, Any], context: Dict[str, Any]) -> List[str]:
        violations = []
        for constraint_id, constraint in self.logical_constraints.items():
            if not constraint.is_active: continue
            
            # 條件判斷
            if any(context.get(cond, False) for cond in constraint.conditions):
                if constraint.action not in action.get("action_type", ""):
                    violations.append(constraint_id)
        return violations

    def _evaluate_ethical_principles(self, action: Dict[str, Any], context: Dict[str, Any], 
                                    graph_risks: List[str]) -> Dict[EthicalPrinciple, float]:
        """評估各原來的滿足度，將圖風險納入考量。"""
        scores = {}
        # 基礎權重由圖風險影響
        risk_penalty = 0.4 if graph_risks else 0.0
        
        for principle in EthicalPrinciple:
            base_score = context.get(f"{principle.value}_base", 0.7)
            if principle == EthicalPrinciple.NON_MALEFICENCE:
                scores[principle] = max(0.0, base_score - risk_penalty)
            else:
                scores[principle] = base_score
        return scores

    def _calculate_overall_score(self, violations: List[str], ethical_scores: Dict[EthicalPrinciple, float]) -> float:
        penalty = len(violations) * 0.25
        avg_score = sum(ethical_scores.values()) / len(ethical_scores)
        return max(0.0, min(1.0, avg_score - penalty))

    def _identify_conflicts(self, ethical_scores: Dict[EthicalPrinciple, float]) -> List[EthicalPrinciple]:
        return [p for p, s in ethical_scores.items() if s < 0.4]

    def _generate_reasoning(self, action: Dict[str, Any], context: Dict[str, Any], 
                          violations: List[str], ethical_scores: Dict[EthicalPrinciple, float],
                          graph_risks: List[str]) -> str:
        parts = [f"評估: {action.get('description', '未知行動')}"]
        if graph_risks:
            parts.append("🛑 圖路徑風險提醒:")
            parts.extend([f"  - {r}" for r in graph_risks])
        if violations:
            parts.append(f"❌ 違反約束: {violations}")
        parts.append("⚖️ 倫理得分:")
        for p, s in ethical_scores.items():
            parts.append(f"  {p.value}: {s:.2f}")
        return "\n".join(parts)

    def _calculate_confidence(self, action: Dict[str, Any], context: Dict[str, Any], 
                             graph_risks: List[str]) -> float:
        # 如果有圖證據，置信度更高
        base_confidence = 0.7
        if graph_risks: base_confidence += 0.2
        return min(1.0, base_confidence)

    def add_constraint(self, constraint: LogicalConstraint):
        """添加新的逻辑约束"""
        self.logical_constraints[constraint.constraint_id] = constraint
        logger.info(f"[{self.system_id}] 添加约束: {constraint.constraint_id}")
    
    def update_ethical_principle_weight(self, principle: EthicalPrinciple, weight: float):
        """更新伦理原则权重"""
        if 0.0 <= weight <= 2.0:  # 允许权重在0 - 2之间
            self.ethical_principles[principle] = weight
            logger.info(f"[{self.system_id}] 更新伦理原则权重: {principle.value} = {weight}")
        else:
            logger.warning(f"[{self.system_id}] 无效的权重值: {weight} (应在0.0 - 2.0之间)")
    
    def get_reasoning_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取推理历史"""
        return self.reasoning_history[-limit:]
    
    def clear_history(self):
        """清空推理历史"""
        self.reasoning_history.clear()
        logger.info(f"[{self.system_id}] 推理历史已清空")