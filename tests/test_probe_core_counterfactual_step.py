# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§95's contract: the same rows, the same operand, and only the step size changes.

``CORE_GAP_ANALYSIS.md`` §95 registers, before any scored run: the joint support
(x0 in 2..9, x1 in 3..15), the mechanical signed step (delta 1 or 10, chosen so
that *both* endpoints stay inside support), the guards inherited from §92/§94, the
population (24 paired rows of §93's 177), the coverage numbers, the decision rule
and the predictions.

What is tested here:

* the support is joint, not per-axis - ``(10, 3)`` is outside even though each
  number individually is not;
* ``step_sign`` returns a *signed step* (``+10``/``-10``/``+1``/``-1``), not a
  sign that a caller must multiply - the bug this stage had to fix;
* delta 10 is impossible for x1 in 6..12 (both endpoints cannot stay inside);
* the corpus: 24 paired rows, 13 descriptive leaves-support rows, 105
  non-multiplication rows dropped, 35 originally outside support;
* on every paired row, both moves touch the same operand (x1) and only that
  operand, by exactly 1 and exactly 10, and both stay inside support;
* every one of the 24 perturbed pairs was actually seen in training;
* the new gold is what the fitted expression says, and every equivalent fit must
  agree;
* the decision rule: `underpowered` first, `support` at >= 50%, `jump-size` at
  <= 25% *and* the 1-unit arm holding at >= 50%, `mixed` in between, seeds must
  agree, GRU never decides;
* `--check` refuses a plan report and a report from another oracle.

No checkpoint is loaded and no measured score is asserted. In particular the
originally-correct counts (15, 20) depend on the gitignored report and are *not*
asserted here.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_counterfactual_step.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load("probe_step_under_test", PROBE)


@pytest.fixture(scope="module")
def corpus(probe):
    train = probe.read_pairs(probe.TRAIN)
    holdout = probe.read_pairs(probe.HOLDOUT)
    families = probe.sh.build_families(train)
    selected, _ = probe.sh.select_rows(holdout, families)
    paired, leaves, dropped = probe.build_rows(families, selected)
    return {
        "families": families,
        "selected": selected,
        "paired": paired,
        "leaves": leaves,
        "dropped": dropped,
    }


# -- the support and the step rule -----------------------------------------
def test_support_is_a_joint_box_not_two_ranges(probe):
    assert probe.in_support(2, 3)
    assert probe.in_support(9, 15)
    assert probe.in_support(5, 9)
    # each number is individually plausible, but the pair is outside the box
    assert not probe.in_support(10, 3)
    assert not probe.in_support(2, 16)
    assert not probe.in_support(1, 3)
    assert not probe.in_support(2, 2)


def test_step_sign_returns_a_signed_step_not_a_sign(probe):
    """The bug this stage fixes: delta 10 used to return +1 instead of +10."""
    assert probe.step_sign(3, 10) == 10
    assert probe.step_sign(4, 10) == 10
    assert probe.step_sign(5, 10) == 10
    assert probe.step_sign(13, 10) == -10
    assert probe.step_sign(14, 10) == -10
    assert probe.step_sign(15, 10) == -10


def test_ten_units_is_impossible_in_the_middle(probe):
    for x1 in range(6, 13):
        assert probe.step_sign(x1, 10) is None


def test_one_unit_always_has_a_direction(probe):
    for x1 in range(3, 16):
        step = probe.step_sign(x1, 1)
        assert step in (1, -1)
        assert probe.in_support(2, x1 + step)
    assert probe.step_sign(14, 1) == 1
    assert probe.step_sign(15, 1) == -1


def test_both_endpoints_stay_inside_support(probe, corpus):
    for row in corpus["paired"]:
        assert probe.in_support(row["x0"], row["x1"])
        assert probe.in_support(row["x0"], row["x1"] + row["delta1"])
        assert probe.in_support(row["x0"], row["x1"] + row["delta10"])


# -- the corpus -------------------------------------------------------------
def test_coverage_numbers(corpus):
    assert len(corpus["paired"]) == 24
    assert len(corpus["leaves"]) == 13
    assert corpus["dropped"] == {"not-multiplication": 105, "outside-support": 35}


def test_population_is_a_subset_of_section_93(corpus):
    keep = {row["i"] for row in corpus["selected"]}
    assert len(keep) == 177
    assert {row["i"] for row in corpus["paired"]} <= keep
    assert {row["i"] for row in corpus["leaves"]} <= keep
    assert len({row["i"] for row in corpus["paired"]}) == 24


def test_delta_ten_uses_both_directions(corpus):
    signs = {}
    for row in corpus["paired"]:
        signs[row["delta10"]] = signs.get(row["delta10"], 0) + 1
    assert signs == {10: 13, -10: 11}


def test_only_the_multiplicand_changes_and_by_exactly_the_step(probe, corpus):
    for row in corpus["paired"]:
        before = probe.base.slot_values(row["q"])
        one = probe.base.slot_values(row["q1"])
        ten = probe.base.slot_values(row["q10"])
        assert len(before) == len(one) == len(ten)
        changed_one = [i for i in range(len(before)) if before[i] != one[i]]
        changed_ten = [i for i in range(len(before)) if before[i] != ten[i]]
        assert changed_one == changed_ten == [1]
        assert abs(float(one[1]) - float(before[1])) == 1
        assert abs(float(ten[1]) - float(before[1])) == 10
        # the other operand and every constant stay put
        assert one[0] == ten[0] == before[0]
        for index in range(2, len(before)):
            assert one[index] == ten[index] == before[index]


def test_every_perturbed_pair_was_seen_in_training(probe, corpus):
    observed = probe._observed_pairs(corpus["families"])
    for row in corpus["paired"]:
        assert (row["x0"], row["x1"] + row["delta1"]) in observed
        assert tuple(row["pair10"]) in observed
        assert row["pair10"] == [row["x0"], row["x1"] + row["delta10"]]


def test_every_row_has_two_truthful_new_golds(probe, corpus):
    for row in corpus["paired"]:
        family = corpus["families"][row["template"]]
        node = probe.gram.as_node(family["node"])
        for text, gold in ((row["q1"], row["gold1"]), (row["q10"], row["gold10"])):
            slots = probe.base.slot_values(text)
            x = [float(slots[i]) for i in range(len(slots))]
            assert probe.base._agrees(probe.gram.evaluate(node, x), str(gold)), text
        assert str(row["gold1"]) != str(row["gold"])
        assert str(row["gold10"]) != str(row["gold"])
        assert str(row["gold1"]) != str(row["gold10"])


def test_leaves_support_rows_really_leave(probe, corpus):
    assert corpus["leaves"]
    for row in corpus["leaves"]:
        assert row["delta_out"] in (10, -10)
        assert probe.in_support(row["x0"], row["x1"])
        assert not probe.in_support(row["x0"], row["x1"] + row["delta_out"])
        assert str(row["gold_out"]) != str(row["gold"])


# -- refusals ---------------------------------------------------------------
def _family(node, nodes, rows, expression="x0+x1"):
    return {
        "status": "usable",
        "node": node,
        "nodes": nodes,
        "constant_slots": [],
        "expression": expression,
        "rows": rows,
    }


def test_a_fit_that_disagrees_on_the_new_point_is_refused(probe):
    """a+b and 2*a both fit the training rows (a == b), then diverge."""
    x0 = probe.gram._x(0)
    x1 = probe.gram._x(1)
    family = _family(
        probe.gram._op("+", x0, x1),
        [probe.gram._op("+", x0, x1), ("scale", 2.0, x0)],
        [("pair 5 5", "10")],
    )
    assert probe.move("pair 5 5", family, 1, 1, {"pair 5 5"}) is None


def test_a_move_that_changes_the_number_class_is_refused(probe):
    x0 = probe.gram._x(0)
    x1 = probe.gram._x(1)
    family = _family(
        probe.gram._op("/", x0, x1), [probe.gram._op("/", x0, x1)], [], expression="x0/x1"
    )
    # 299 / 13 is 23 exactly; 300 / 13 is not an integer
    assert probe.move("What is 299 / 13?", family, 0, 1, set()) is None


def test_a_move_into_the_training_set_is_refused(probe):
    x0 = probe.gram._x(0)
    x1 = probe.gram._x(1)
    family = _family(probe.gram._op("+", x0, x1), [probe.gram._op("+", x0, x1)], [])
    assert probe.move("pair 14 3", family, 0, 1, {"pair 15 3"}) is None


def test_a_decimal_operand_is_refused(probe):
    x0 = probe.gram._x(0)
    x1 = probe.gram._x(1)
    family = _family(probe.gram._op("+", x0, x1), [probe.gram._op("+", x0, x1)], [])
    assert probe.move("pair 0.5 3", family, 0, 1, set()) is None


# -- the decision rule ------------------------------------------------------
def _run(probe, original, one, ten, arm="snn", seed=0):
    cell = {
        "n": 24,
        "original": original,
        "one": one,
        "ten": ten,
        "survival_one": round(one / original, 4) if original else 0.0,
        "survival_ten": round(ten / original, 4) if original else 0.0,
    }
    return {"arm": arm, "seed": seed, probe.PAIRED: cell}


def test_underpowered_comes_first(probe):
    runs = [_run(probe, 9, 9, 9)]
    assert probe.verdict(runs)["verdict"] == "underpowered"


def test_support_needs_half_the_ten_unit_arm(probe):
    assert probe.verdict([_run(probe, 20, 12, 10)])["verdict"] == "support"
    assert probe.verdict([_run(probe, 20, 12, 9)])["verdict"] != "support"


def test_jump_size_needs_ten_to_die_and_one_to_live(probe):
    assert probe.verdict([_run(probe, 20, 12, 5)])["verdict"] == "jump-size"


def test_jump_size_needs_the_one_unit_arm_to_hold(probe):
    # ten dies (<= 25%) but one also dies -> not jump-size
    assert probe.verdict([_run(probe, 20, 4, 4)])["verdict"] == "mixed"


def test_between_the_two_is_mixed(probe):
    assert probe.verdict([_run(probe, 20, 12, 7)])["verdict"] == "mixed"


def test_seeds_must_agree(probe):
    runs = [
        _run(probe, 20, 12, 12, seed=0),
        _run(probe, 20, 12, 7, seed=1),
    ]
    assert probe.verdict(runs)["verdict"] == "mixed"


def test_gru_does_not_decide(probe):
    runs = [
        _run(probe, 20, 12, 7, arm="snn", seed=0),
        _run(probe, 20, 20, 20, arm="gru", seed=0),
    ]
    assert probe.verdict(runs)["verdict"] == "mixed"


def test_wilson_contains_the_point_estimate(probe):
    low, high = probe.wilson(6, 15)
    assert 0.0 <= low < 6 / 15 < high <= 1.0
    assert probe.wilson(0, 0) == (0.0, 0.0)


# -- entry points -----------------------------------------------------------
def test_check_refuses_a_plan_report(probe, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"stage": "plan", "oracle": "step-size"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False and "plan" in message


def test_check_refuses_another_oracle(probe, tmp_path):
    path = tmp_path / "other.json"
    path.write_text('{"stage": "scored", "oracle": "digit-units"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False and "step-size" in message


def test_registered_constants(probe):
    assert probe.MIN_CORRECT == 10
    assert probe.SURVIVES_SHARE == 0.50
    assert probe.DIES_SHARE == 0.25
    assert probe.DECIDING_ARM == "snn"
    assert probe.ARMS == (("snn", 0), ("snn", 1), ("gru", 0), ("gru", 1))
    assert probe.SUPPORT_X0 == (2, 9)
    assert probe.SUPPORT_X1 == (3, 15)
    assert probe.PAIRED == "paired-in-support"
    assert probe.LEAVES == "leaves-support"
