import pytest
from ai.arithmetic.boolean_gate_learner import (
    BooleanGateLearner,
    GateExample,
    run_active_logic_gate_experiment,
    run_logic_gate_experiment,
)


def test_learner_infers_xnor_from_three_teaching_rows() -> None:
    result = run_logic_gate_experiment(
        training_rows=[
            {"a": 0, "b": 0, "output": 1},
            {"a": 0, "b": 1, "output": 0},
            {"a": 1, "b": 0, "output": 0},
        ],
        evaluation_rows=[{"a": 1, "b": 1}],
        oracle_expression="a == b",
    )

    assert result["hypothesis"] == "xnor"
    assert result["used_llm"] is False
    assert result["all_rows_pass"] is True
    assert result["accuracy"] == 1.0
    assert result["evaluation_rows"][0]["expected"] is None
    assert result["evaluation_rows"][0]["learner"] == 1
    assert result["evaluation_rows"][0]["oracle"] == 1


@pytest.mark.parametrize(
    ("training_rows", "evaluation_row", "oracle", "expected_name"),
    [
        (
            [
                {"a": 0, "b": 1, "output": 0},
                {"a": 1, "b": 0, "output": 0},
                {"a": 1, "b": 1, "output": 1},
            ],
            {"a": 0, "b": 0},
            "a and b",
            "and",
        ),
        (
            [
                {"a": 0, "b": 0, "output": 0},
                {"a": 0, "b": 1, "output": 1},
                {"a": 1, "b": 0, "output": 1},
            ],
            {"a": 1, "b": 1},
            "a or b",
            "or",
        ),
    ],
)
def test_learner_generalizes_to_unseen_row(
    training_rows: list[dict],
    evaluation_row: dict,
    oracle: str,
    expected_name: str,
) -> None:
    result = run_logic_gate_experiment(training_rows, [evaluation_row], oracle)

    assert result["hypothesis"] == expected_name
    assert result["all_rows_pass"] is True


def test_active_learner_uses_oracle_only_after_failed_predictions() -> None:
    result = run_active_logic_gate_experiment(
        seed_rows=[{"a": 0, "b": 0, "output": 1}],
        query_rows=[
            {"a": 0, "b": 0},
            {"a": 0, "b": 1},
            {"a": 1, "b": 0},
            {"a": 1, "b": 1},
        ],
        oracle_expression="a == b",
    )

    assert result["hypothesis"] == "xnor"
    assert result["corrections"]
    assert result["all_rows_pass"] is True
    assert result["used_llm"] is False
    assert all(row["oracle"] in {0, 1} for row in result["evaluation_rows"])


def test_learner_rejects_non_binary_examples() -> None:
    with pytest.raises(ValueError, match="0 or 1"):
        BooleanGateLearner().fit([{"a": 2, "b": 0, "output": 1}])


def test_gate_example_is_hashable_and_serializable() -> None:
    example = GateExample(0, 1, 1)

    assert hash(example) == hash(GateExample(0, 1, 1))
    assert example.__dict__ == {"a": 0, "b": 1, "output": 1}
