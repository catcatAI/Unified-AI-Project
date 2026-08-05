# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [B] [L5]
# =============================================================================
"""Tests for the autonomous arithmetic learner (research A+B landing).

The module under test implements the research verdict:
* counting/one-hot digit representation (§3.1 / §5),
* digit cell (digit, digit, carry_in) -> (digit_sum, carry_out) learned from
  deterministic-engine truth (carry0+1 truth table, §B6),
* autonomous loop: auto-generate when sparse, stop when learned /
  unconvergeable, resume via checkpoint,
* dialogue learning hook for ContinuousLearningPipeline.
"""

from __future__ import annotations

import os
import tempfile

import pytest

from ai.arithmetic.arithmetic_learner import (
    ArithmeticLearner,
    DigitRepresentation,
    CellSample,
    _label_add,
)


@pytest.fixture(scope="module")
def learner() -> ArithmeticLearner:
    l = ArithmeticLearner()
    l.run(max_epochs=10, stall_epochs=3)
    return l


def test_label_add_parses_deterministic_result() -> None:
    assert _label_add(2, 3) == 5
    assert _label_add(15, 27) == 42


def test_truth_table_covers_digits_and_carries() -> None:
    l = ArithmeticLearner()
    table = l.generate_cell_truth_table()
    # 10 digits x 10 digits x 2 carries = 200 cells
    assert len(table) == 200
    carries = {s.carry_in for s in table}
    digits = sorted({s.da for s in table} | {s.db for s in table})
    assert carries == {0, 1}
    assert digits == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_cell_truth_semantics() -> None:
    l = ArithmeticLearner()
    table = {("da", s.da, "db", s.db, "cin", s.carry_in): s for s in l.generate_cell_truth_table()}
    s = table[("da", 5, "db", 7, "cin", 0)]
    assert s.digit_sum == 2
    assert s.carry_out == 1
    s2 = table[("da", 5, "db", 4, "cin", 1)]
    assert s2.digit_sum == 0
    assert s2.carry_out == 1


@pytest.mark.parametrize("mode", ["onehot", "counting"])
def test_digit_representation_modes(mode: str) -> None:
    r = DigitRepresentation(mode=mode)
    if mode == "onehot":
        v4 = r.digit_vector(4)
        assert v4.sum() == pytest.approx(1.0)
        assert int(r.numeric_value(v4)) == 4
    else:
        # counting: digit 4 == 4 x digit 1
        v1 = r.digit_vector(1)
        v4 = r.digit_vector(4)
        assert r.numeric_value(v4) == pytest.approx(4.0 * r.numeric_value(v1), rel=0.1)
        # composable: digit 3 + one more unit gives ~4
        assert r.numeric_value(r.digit_vector(3) + v1) == pytest.approx(
            r.numeric_value(v4), rel=0.1
        )


def test_loop_learns_to_perfect_cell_accuracy(learner: ArithmeticLearner) -> None:
    assert learner.snapshot.cell_accuracy == pytest.approx(1.0)
    assert learner.learned
    assert learner.snapshot.stopped_reason in ("learned-optimal", "learned-threshold")


def test_addition_composition(learner: ArithmeticLearner) -> None:
    cases = [(3, 7, 10), (29, 38, 67), (999, 1, 1000), (56, 44, 100), (123, 987, 1110)]
    for a, b, expected in cases:
        assert learner.predict_addition(a, b) == expected, f"{a}+{b}"


def test_random_addition(learner: ArithmeticLearner) -> None:
    import random

    rng = random.Random(5)
    ok = 0
    for _ in range(200):
        a = rng.randrange(0, 5000)
        b = rng.randrange(0, 5000)
        if learner.predict_addition(a, b) == a + b:
            ok += 1
    assert ok == 200


def test_unconvergeable_stops() -> None:
    l = ArithmeticLearner()
    # Cap epochs so the loop must terminate (either by converging, stalling, or
    # hitting the epoch ceiling) rather than running forever.
    snap = l.run(max_epochs=3, stall_epochs=1)
    assert snap.epoch <= 3
    assert snap.stopped_reason in (
        "learned-optimal",
        "learned-threshold",
        "unconvergeable-stall",
        "max-epochs-reached",
    )


def test_save_load_resume(tmp_path: "Any") -> None:
    import numpy as np

    l = ArithmeticLearner()
    l.run(max_epochs=3)
    path = os.path.join(tmp_path, "arith.npz")
    l.save(path)
    l2 = ArithmeticLearner()
    l2.load(path)
    assert l2.predict_addition(3, 7) == 10
    assert l2.snapshot.epoch >= 1
    assert np.array_equal(l2.hidden_w, l.hidden_w)


def test_dialogue_learning() -> None:
    l = ArithmeticLearner()
    snap = l.learn_from_dialogue("what is 12 + 5?", "that is 17")
    assert snap is not None
    assert l.predict_addition(12, 5) == 17
    # non-math dialogue is a no-op
    assert l.learn_from_dialogue("hello there", "hi") is None


def test_dialogue_auto_run_false_queues_only() -> None:
    l = ArithmeticLearner()
    res = l.learn_from_dialogue("3 + 4?", "it is 7", auto_run=False)
    assert res is None
    # cells queued; a later explicit run converges
    l.run(max_epochs=5, stall_epochs=2)
    assert l.predict_addition(3, 4) == 7


def test_cell_sample_hashable() -> None:
    a = CellSample(1, 2, 0, 3, 0)
    b = CellSample(1, 2, 0, 3, 0)
    c = CellSample(1, 2, 0, 4, 0)
    assert hash(a) == hash(b)
    assert a == b
    assert a != c


def test_predict_guard_no_infinite_loop() -> None:
    # Even a fresh/untrained net must terminate (guard on carry chain).
    l = ArithmeticLearner()
    assert l.predict_addition(999999, 999999) >= 0  # should not hang


def test_clp_dialogue_hook() -> None:
    from ai.ed3n.continuous_learning import ContinuousLearningPipeline

    al = ArithmeticLearner()
    # growth_interval doesn't matter; the arithmetic hook fires every interaction.
    p = ContinuousLearningPipeline(growth_interval=100, arithmetic_learner=al)
    p.process_interaction("12 plus 5", "that is 17", {})
    al.run(max_epochs=5, stall_epochs=2)
    assert al.predict_addition(12, 5) == 17
    assert al.learned
