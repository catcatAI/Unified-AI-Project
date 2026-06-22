# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class _SimpleSymbolicSpace:
    """Minimal in-memory symbolic space replacing UnifiedSymbolicSpace."""

    def __init__(self):
        self._nodes: dict[str, dict] = {}
        self._relations: dict[str, list] = {}

    def add_symbol(self, name: str, node_type: str, properties: dict | None = None):
        self._nodes[name] = {"type": node_type, "properties": properties or {}}

    def get_relationships(self, node: str) -> list:
        return self._relations.get(node, [])


class EthicalPrinciple(Enum):
    NON_MALEFICENCE = "non_maleficence"
    BENEFICENCE = "beneficence"
    AUTONOMY = "autonomy"
    JUSTICE = "justice"
    FIDELITY = "fidelity"


@dataclass
class LogicalConstraint:
    constraint_id: str
    description: str
    priority: int
    conditions: list
    action: str
    is_active: bool = True


@dataclass
class EthicalEvaluation:
    score: float
    conflicting_principles: list
    reasoning: str
    confidence: float


class ReasoningSystem:
    def __init__(self, system_id: str = "reasoning_system_v1"):
        self.system_id = system_id
        self.is_active = True
        self.reasoning_history: list = []
        self.symbolic_space = _SimpleSymbolicSpace()
        self.ethical_principles: dict[EthicalPrinciple, float] = {
            p: 1.0 for p in EthicalPrinciple
        }
        self.logical_constraints: dict[str, LogicalConstraint] = {
            "no_harm_to_humans": LogicalConstraint(
                constraint_id="no_harm_to_humans",
                description="No harm to humans",
                priority=10,
                conditions=["action_affects_human_safety"],
                action="require_safety_verification",
            ),
            "preserve_human_autonomy": LogicalConstraint(
                constraint_id="preserve_human_autonomy",
                description="Preserve human autonomy",
                priority=8,
                conditions=["action_affects_human_autonomy"],
                action="require_informed_consent",
            ),
        }
        self._seed_symbolic_space()

    def _seed_symbolic_space(self) -> None:
        sensitive_nodes = ["Harm", "Violence", "Deception", "Policy_Violation", "Unethical"]
        for node in sensitive_nodes:
            self.symbolic_space.add_symbol(node, "Constraint_Node", {"risk_level": "High"})

    def add_constraint(self, constraint: LogicalConstraint) -> None:
        self.logical_constraints[constraint.constraint_id] = constraint

    def update_ethical_principle_weight(self, principle: EthicalPrinciple, weight: float) -> None:
        if 0.5 <= weight <= 2.0:
            self.ethical_principles[principle] = weight
        else:
            self.ethical_principles[principle] = 1.0

    def evaluate_action(self, action: dict, context: dict) -> EthicalEvaluation:
        violations = self._check_constraints(action, context)
        risks = self._find_risks(action)
        ethical_scores = self._evaluate_ethical_principles(action, context, risks)
        score = self._calculate_overall_score(violations, ethical_scores)
        conflicting = self._identify_conflicts(ethical_scores)

        reasoning_parts = []
        if violations:
            reasoning_parts.append(f"violations: {', '.join(violations)}")
        if risks:
            reasoning_parts.append(f"risk detected from: {', '.join(risks)}")
        if not reasoning_parts:
            reasoning_parts.append("no issues found")
        reasoning = "; ".join(reasoning_parts)

        confidence = self._calculate_confidence(action, context, risks)

        evaluation = EthicalEvaluation(
            score=score,
            conflicting_principles=conflicting,
            reasoning=reasoning,
            confidence=confidence,
        )
        self.reasoning_history.append({"action": action, "evaluation": evaluation, "context": context})
        return evaluation

    def _find_risks(self, action: dict) -> list:
        risks = []
        sensitive = ["Harm", "Violence", "Deception", "Policy_Violation", "Unethical"]
        for entity in action.get("entities", []):
            for target in sensitive:
                path = self._find_simple_path(entity, target, max_depth=2)
                if path is not None:
                    risks.append(entity)
                    break
        return risks

    def _check_constraints(self, action: dict, context: dict) -> list:
        violations = []
        for cid, constraint in self.logical_constraints.items():
            if not constraint.is_active:
                continue
            conditions_met = all(
                context.get(cond) for cond in constraint.conditions
            )
            if not conditions_met:
                continue
            action_type = action.get("action_type", "")
            if constraint.action not in action_type:
                violations.append(cid)
        return violations

    def _evaluate_ethical_principles(self, action: dict, context: dict, risks: list) -> dict:
        scores = {}
        for principle in EthicalPrinciple:
            weight = self.ethical_principles.get(principle, 1.0)
            base_key = f"{principle.value}_base"
            base = context.get(base_key, 1.0)
            score = base * weight
            if principle == EthicalPrinciple.NON_MALEFICENCE and risks:
                score = min(score, 0.5)
            scores[principle] = round(max(0.0, min(1.0, score)), 2)
        return scores

    def _calculate_overall_score(self, violations: list, ethical_scores: dict) -> float:
        if not ethical_scores:
            return 0.0
        avg_ethical = sum(ethical_scores.values()) / len(ethical_scores)
        penalty = len(violations) * 0.25
        score = avg_ethical - penalty
        return round(max(0.0, min(1.0, score)), 2)

    def _identify_conflicts(self, scores: dict) -> list:
        return [p for p, s in scores.items() if s < 0.5]

    def get_reasoning_history(self) -> list:
        return list(self.reasoning_history)

    def clear_history(self) -> None:
        self.reasoning_history.clear()

    def _calculate_confidence(self, action: dict, context: dict, risks: list) -> float:
        return min(1.0, 0.7 + len(risks) * 0.2)

    def _find_simple_path(self, source: str, target: str, max_depth: int) -> Optional[list]:
        visited = set()
        queue = [(source, [source])]
        while queue:
            node, path = queue.pop(0)
            if node == target:
                return path
            if len(path) > max_depth:
                continue
            if node in visited:
                continue
            visited.add(node)
            for rel in self.symbolic_space.get_relationships(node):
                next_node = rel["target"]
                if next_node not in visited:
                    queue.append((next_node, path + [next_node]))
        return None
