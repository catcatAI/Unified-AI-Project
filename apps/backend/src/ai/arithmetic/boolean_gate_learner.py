# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from services.math_verifier import evaluate_logic


@dataclass(frozen=True)
class GateExample:
    a: int
    b: int
    output: int


@dataclass(frozen=True)
class GateHypothesis:
    name: str
    expression: str
    function: Callable[[int, int], int]
    complexity: int


def _bit(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int) and value in {0, 1}:
        return value
    raise ValueError("logic gate inputs and outputs must be 0 or 1")


def _hypotheses() -> Tuple[GateHypothesis, ...]:
    return (
        GateHypothesis("constant_0", "0", lambda _a, _b: 0, 0),
        GateHypothesis("constant_1", "1", lambda _a, _b: 1, 0),
        GateHypothesis("a", "a", lambda a, _b: a, 1),
        GateHypothesis("b", "b", lambda _a, b: b, 1),
        GateHypothesis("not_a", "not a", lambda a, _b: 1 - a, 1),
        GateHypothesis("not_b", "not b", lambda _a, b: 1 - b, 1),
        GateHypothesis("and", "a and b", lambda a, b: a & b, 2),
        GateHypothesis("or", "a or b", lambda a, b: a | b, 2),
        GateHypothesis("xor", "a xor b", lambda a, b: a ^ b, 2),
        GateHypothesis("xnor", "a == b", lambda a, b: int(a == b), 2),
        GateHypothesis("nand", "not (a and b)", lambda a, b: 1 - (a & b), 3),
        GateHypothesis("nor", "not (a or b)", lambda a, b: 1 - (a | b), 3),
    )


class BooleanGateLearner:
    """Infer a small Boolean hypothesis from labeled examples."""

    def __init__(self) -> None:
        self.hypothesis: Optional[GateHypothesis] = None
        self.examples: list[GateExample] = []

    def fit(self, examples: Iterable[Mapping[str, Any] | GateExample]) -> "BooleanGateLearner":
        normalized = [
            (
                example
                if isinstance(example, GateExample)
                else GateExample(
                    a=_bit(example["a"]),
                    b=_bit(example["b"]),
                    output=_bit(example["output"]),
                )
            )
            for example in examples
        ]
        if not normalized:
            raise ValueError("at least one logic gate example is required")
        self.examples = normalized
        matches = [
            hypothesis
            for hypothesis in _hypotheses()
            if all(
                hypothesis.function(example.a, example.b) == example.output
                for example in normalized
            )
        ]
        if not matches:
            raise ValueError("no supported Boolean hypothesis matches the teaching examples")
        self.hypothesis = min(matches, key=lambda item: (item.complexity, item.name))
        return self

    def predict(self, a: Any, b: Any) -> int:
        if self.hypothesis is None:
            raise RuntimeError("BooleanGateLearner.fit must run before predict")
        return int(self.hypothesis.function(_bit(a), _bit(b)))

    @property
    def expression(self) -> str:
        if self.hypothesis is None:
            raise RuntimeError("BooleanGateLearner.fit must run before expression")
        return self.hypothesis.expression

    @property
    def name(self) -> str:
        if self.hypothesis is None:
            raise RuntimeError("BooleanGateLearner.fit must run before name")
        return self.hypothesis.name


def _eval_oracle_node(node: ast.AST, values: Mapping[str, int]) -> int:
    if isinstance(node, ast.Expression):
        return _eval_oracle_node(node.body, values)
    if isinstance(node, ast.Name):
        if node.id not in values:
            raise ValueError(f"oracle references unknown input: {node.id}")
        return values[node.id]
    if isinstance(node, ast.Constant):
        return _bit(node.value)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return int(all(_eval_oracle_node(value, values) for value in node.values))
        if isinstance(node.op, ast.Or):
            return int(any(_eval_oracle_node(value, values) for value in node.values))
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return 1 - _eval_oracle_node(node.operand, values)
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and len(node.comparators) == 1:
        left = _eval_oracle_node(node.left, values)
        right = _eval_oracle_node(node.comparators[0], values)
        if isinstance(node.ops[0], ast.Eq):
            return int(left == right)
        if isinstance(node.ops[0], ast.NotEq):
            return int(left != right)
    raise ValueError("oracle expression contains an unsupported operation")


def _oracle(expression: str, a: int, b: int) -> int:
    normalized = "".join(expression.lower().split())
    application_text = {
        "a==b": f"{bool(a)} XNOR {bool(b)}",
        "a!=b": f"{bool(a)} XOR {bool(b)}",
        "aandb": f"{bool(a)} and {bool(b)}",
        "aorb": f"{bool(a)} or {bool(b)}",
        "nota": f"not {bool(a)}",
    }.get(normalized)
    if application_text is not None:
        application_result = evaluate_logic(application_text)
        if application_result is not None:
            return int(application_result == "true")
    try:
        tree = ast.parse(expression, mode="eval")
        return _eval_oracle_node(tree, {"a": a, "b": b})
    except (SyntaxError, ValueError) as exc:
        raise ValueError(f"oracle evaluation failed: {exc}") from exc


def run_active_logic_gate_experiment(
    seed_rows: Sequence[Mapping[str, Any] | GateExample],
    query_rows: Sequence[Mapping[str, Any]],
    oracle_expression: str,
) -> Dict[str, Any]:
    """Let the learner request oracle feedback only when its hypothesis is wrong."""
    examples = [
        (
            example
            if isinstance(example, GateExample)
            else GateExample(
                a=_bit(example["a"]),
                b=_bit(example["b"]),
                output=_bit(example["output"]),
            )
        )
        for example in seed_rows
    ]
    if not examples:
        raise ValueError("at least one seed logic gate example is required")
    learner = BooleanGateLearner().fit(examples)
    active_queries: list[Dict[str, Any]] = []
    corrections: list[Dict[str, Any]] = []
    for raw in query_rows:
        a = _bit(raw["a"])
        b = _bit(raw["b"])
        predicted = learner.predict(a, b)
        oracle = _oracle(oracle_expression, a, b)
        query_passed = predicted == oracle
        active_queries.append(
            {
                "a": a,
                "b": b,
                "predicted_before_feedback": predicted,
                "oracle": oracle,
                "pass": query_passed,
            }
        )
        if not query_passed:
            examples.append(GateExample(a=a, b=b, output=oracle))
            learner = BooleanGateLearner().fit(examples)
            corrections.append(
                {
                    "a": a,
                    "b": b,
                    "old_prediction": predicted,
                    "oracle": oracle,
                    "new_hypothesis": learner.name,
                }
            )
    final_rows: list[Dict[str, Any]] = []
    for raw in query_rows:
        a = _bit(raw["a"])
        b = _bit(raw["b"])
        predicted = learner.predict(a, b)
        oracle = _oracle(oracle_expression, a, b)
        final_rows.append(
            {
                "a": a,
                "b": b,
                "learner": predicted,
                "oracle": oracle,
                "pass": predicted == oracle,
            }
        )
    passed = sum(1 for row in final_rows if row["pass"])
    return {
        "schema_version": "logic-gate-active-experiment/1",
        "hypothesis": learner.name,
        "expression": learner.expression,
        "oracle_expression": oracle_expression,
        "seed_rows": [
            {"a": example.a, "b": example.b, "output": example.output}
            for example in examples[: len(seed_rows)]
        ],
        "active_queries": active_queries,
        "corrections": corrections,
        "final_training_rows": [
            {"a": example.a, "b": example.b, "output": example.output}
            for example in learner.examples
        ],
        "evaluation_rows": final_rows,
        "evaluation_count": len(final_rows),
        "passed_count": passed,
        "accuracy": round(passed / len(final_rows), 4) if final_rows else 0.0,
        "all_rows_pass": bool(final_rows) and passed == len(final_rows),
        "used_llm": False,
    }


def run_logic_gate_experiment(
    training_rows: Sequence[Mapping[str, Any] | GateExample],
    evaluation_rows: Sequence[Mapping[str, Any]],
    oracle_expression: str,
) -> Dict[str, Any]:
    """Fit from teaching rows and verify unseen rows with an independent oracle."""
    learner = BooleanGateLearner().fit(training_rows)
    evaluated: list[Dict[str, Any]] = []
    for raw in evaluation_rows:
        a = _bit(raw["a"])
        b = _bit(raw["b"])
        expected = _bit(raw["output"]) if "output" in raw else None
        predicted = learner.predict(a, b)
        oracle = _oracle(oracle_expression, a, b)
        evaluated.append(
            {
                "a": a,
                "b": b,
                "expected": expected,
                "learner": predicted,
                "oracle": oracle,
                "pass": predicted == oracle and (expected is None or predicted == expected),
            }
        )
    passed = sum(1 for row in evaluated if row["pass"])
    return {
        "schema_version": "logic-gate-experiment/1",
        "hypothesis": learner.name,
        "expression": learner.expression,
        "oracle_expression": oracle_expression,
        "training_rows": [
            {"a": example.a, "b": example.b, "output": example.output}
            for example in learner.examples
        ],
        "evaluation_rows": evaluated,
        "evaluation_count": len(evaluated),
        "passed_count": passed,
        "accuracy": round(passed / len(evaluated), 4) if evaluated else 0.0,
        "all_rows_pass": bool(evaluated) and passed == len(evaluated),
        "used_llm": False,
    }


__all__ = [
    "BooleanGateLearner",
    "GateExample",
    "run_active_logic_gate_experiment",
    "run_logic_gate_experiment",
]
