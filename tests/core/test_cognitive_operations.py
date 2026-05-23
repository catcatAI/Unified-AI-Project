"""
Tests for cognitive_operations.py — StateMatrix4D spatial reasoning functions
"""

from core.autonomous.cognitive_operations import (
    CognitiveOp,
    compute_spatial_influence_factor,
    perform_spatial_reasoning,
    get_dimension_value,
    get_position,
    execute_thought_chain,
    evaluate_math_spatially,
    apply_intent_gravity,
    set_intent_target,
    apply_inter_dimensional_drag,
)


class DimState:
    def __init__(self):
        self.coordinate = (0.0, 0.0, 0.0)
        self.intent_vector = (0.0, 0.0, 0.0)


def test_cognitive_op_enum():
    assert len(CognitiveOp) == 5
    assert CognitiveOp.ACCUMULATE is not None
    print(f"  PASS: CognitiveOp has {len(CognitiveOp)} operations")


def test_compute_spatial_influence_factor():
    dims = {
        "a": DimState(),
        "b": DimState(),
        "c": DimState(),
    }
    dims["a"].coordinate = (0.0, 0.0, 0.0)
    dims["b"].coordinate = (1.0, 0.0, 0.0)
    dims["c"].coordinate = (5.0, 0.0, 0.0)

    fab = compute_spatial_influence_factor(dims, "a", "b")
    fac = compute_spatial_influence_factor(dims, "a", "c")

    assert 0.5 <= fab <= 2.0, f"factor out of range: {fab}"
    assert 0.5 <= fac <= 2.0, f"factor out of range: {fac}"
    assert fab > fac, f"closer dims should have higher factor: {fab} vs {fac}"
    print(f"  PASS: influence_factor close={fab:.3f}, far={fac:.3f}")


def test_perform_spatial_reasoning():
    dims = {
        "x": DimState(),
        "y": DimState(),
    }
    dims["x"].coordinate = (0.0, 0.0, 0.0)

    # Default SPATIAL_RATIO = (1.0, 0.3, 0.15)
    # ACCUMULATE/DECREMENT: affects all axes via ratio
    # AMPLIFY/DIMINISH: X-only (scaling operations)
    new = perform_spatial_reasoning(dims, "x", CognitiveOp.ACCUMULATE, 5.0)
    assert new == (5.0, 1.5, 0.75), f"got {new}"
    assert dims["x"].coordinate == (5.0, 1.5, 0.75)

    new = perform_spatial_reasoning(dims, "x", CognitiveOp.DECREMENT, 2.0)
    assert new == (3.0, 0.9, 0.45), f"got {new}"

    new = perform_spatial_reasoning(dims, "x", CognitiveOp.AMPLIFY, 2.0)
    assert new == (6.0, 0.9, 0.45), f"got {new}"

    new = perform_spatial_reasoning(dims, "x", CognitiveOp.DIMINISH, 2.0)
    assert new == (3.0, 0.9, 0.45), f"got {new}"

    missing = perform_spatial_reasoning(dims, "missing", CognitiveOp.ACCUMULATE, 1.0)
    assert missing == (0.0, 0.0, 0.0)

    # Explicit ratio=(1,0,0) reproduces old X-only behavior
    dims["x"].coordinate = (0.0, 0.0, 0.0)
    old = perform_spatial_reasoning(dims, "x", CognitiveOp.ACCUMULATE, 5.0, ratio=(1, 0, 0))
    assert old == (5.0, 0.0, 0.0), f"got {old}"
    print(f"  PASS: spatial reasoning works for all ops")


def test_get_dimension_value():
    dims = {
        "a": DimState(),
        "b": DimState(),
    }
    dims["a"].coordinate = (3.5, 1.2, 0.5)
    dims["b"].coordinate = (-1.0, 0.0, 0.0)

    assert get_dimension_value(dims, "a") == 3.5
    assert get_dimension_value(dims, "b") == -1.0
    assert get_dimension_value(dims, "missing") == 0.0
    print(f"  PASS: get_dimension_value returns x-coordinate")


def test_get_position():
    dims = {
        "a": DimState(),
        "b": DimState(),
    }
    dims["a"].coordinate = (1.0, 2.0, 3.0)
    dims["b"].coordinate = (4.0, 5.0, 6.0)

    pos = get_position(dims)
    assert pos["a"] == {"x": 1.0, "y": 2.0, "z": 3.0}
    assert pos["b"] == {"x": 4.0, "y": 5.0, "z": 6.0}
    print(f"  PASS: get_position returns coordinate dict")


def test_execute_thought_chain():
    dims = {"x": DimState()}
    dims["x"].coordinate = (0.0, 0.0, 0.0)

    ops = [(CognitiveOp.ACCUMULATE, 5.0), (CognitiveOp.AMPLIFY, 2.0)]
    result = execute_thought_chain(dims, "x", ops)
    assert result == 10.0
    print(f"  PASS: thought chain result={result}")


def test_evaluate_math_spatially():
    dims = {
        "epsilon": DimState(),
        "alpha": DimState(),
    }
    dims["epsilon"].values = {"complexity": 0.0, "certainty": 0.0, "fatigue": 0.0}

    evaluator = evaluate_math_spatially(dims)

    assert evaluator("2 + 3") == 5.0
    assert abs(evaluator("10 - 3") - 7.0) < 1e-9
    assert abs(evaluator("4 * 5") - 20.0) < 1e-9
    assert abs(evaluator("10 / 2") - 5.0) < 1e-9
    assert abs(evaluator("2 + 3 * 4") - 14.0) < 1e-9

    assert dims["epsilon"].values["complexity"] > 0
    assert dims["epsilon"].values["certainty"] > 0
    print(f"  PASS: evaluate_math_spatially handles +, -, *, /, ( )")


def test_apply_intent_gravity():
    dims = {
        "a": DimState(),
        "b": DimState(),
    }
    dims["a"].coordinate = (5.0, 5.0, 5.0)
    dims["a"].intent_vector = (10.0, 10.0, 10.0)

    dims["b"].coordinate = (5.0, 5.0, 5.0)
    dims["b"].intent_vector = (5.0, 5.0, 5.0)

    apply_intent_gravity(dims, pull_factor=0.1)

    assert dims["a"].coordinate[0] > 5.0, "should move toward intent"
    assert dims["b"].coordinate == (5.0, 5.0, 5.0), "already at intent shouldn't move"
    print(f"  PASS: intent gravity moves coordinates toward intent")


def test_set_intent_target():
    dims = {"x": DimState()}
    set_intent_target(dims, "x", (3.0, 4.0, 5.0))
    assert dims["x"].intent_vector == (3.0, 4.0, 5.0)

    set_intent_target(dims, "missing", (1.0, 1.0, 1.0))
    print(f"  PASS: set_intent_target works for existing, silently ignores missing")


def test_apply_inter_dimensional_drag():
    dims = {
        "a": DimState(),
        "b": DimState(),
        "c": DimState(),
    }
    dims["a"].coordinate = (10.0, 0.0, 0.0)
    dims["b"].coordinate = (0.0, 0.0, 0.0)
    dims["c"].coordinate = (0.0, 0.0, 0.0)

    apply_inter_dimensional_drag(dims, "a", drag_factor=0.1)

    assert dims["a"].coordinate == (10.0, 0.0, 0.0), "trigger dim shouldn't move"
    assert dims["b"].coordinate[0] == 1.0, f"b should be dragged: {dims['b'].coordinate}"
    assert dims["c"].coordinate[0] == 1.0, f"c should be dragged: {dims['c'].coordinate}"
    print(f"  PASS: inter-dim drag moves other dims toward trigger")


if __name__ == "__main__":
    print("=== cognitive_operations.py Tests ===\n")

    test_cognitive_op_enum()
    test_compute_spatial_influence_factor()
    test_perform_spatial_reasoning()
    test_get_dimension_value()
    test_get_position()
    test_execute_thought_chain()
    test_evaluate_math_spatially()
    test_apply_intent_gravity()
    test_set_intent_target()
    test_apply_inter_dimensional_drag()

    print(f"\n============================================================")
    print(f"COGNITIVE OPERATIONS TESTS: 10 passed, 0 failed")
    print(f"============================================================")