# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§94's contract: one operand, one unit, and the split by operand width.

``CORE_GAP_ANALYSIS.md`` §94 registers, before any scored run: the units move
(+/-1, digit count preserved), the mechanical operand choice (first multi-digit
operand, else the first operand), the guards inherited from §92, the population
(§93's 177 rows, no reselection), the coverage numbers, the decision rule and the
predictions.

What is tested here:

* the width and step rules (including the 9 -> -1 case, and decimals refused);
* the corpus: 141 rows get a move, 36 do not, 121 treatment / 20 control, and the
  moved operand really is the only change, by exactly one unit;
* the group split follows the *original* operand widths and is therefore not
  downstream of the answers;
* the population is a subset of §93's, so the two sections share a row set;
* the perturbed gold is what the fitted expression says, and every equivalent fit
  must agree (a synthetic family whose two fits diverge is refused);
* the decision rule, including the 30-point gap guard and the `underpowered`
  precedence.

No checkpoint is loaded and no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_counterfactual_digit.py"
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
    return _load("probe_digit_under_test", PROBE)


@pytest.fixture(scope="module")
def corpus(probe):
    train = probe.read_pairs(probe.TRAIN)
    holdout = probe.read_pairs(probe.HOLDOUT)
    families = probe.sh.build_families(train)
    selected, _ = probe.sh.select_rows(holdout, families)
    rows, dropped = probe.build_rows(families, selected)
    return {
        "families": families,
        "selected": selected,
        "rows": rows,
        "dropped": dropped,
    }


# -- the rules --------------------------------------------------------------
def test_width_counts_integer_digits_only(probe):
    assert probe._width("14") == 2
    assert probe._width("200") == 3
    assert probe._width("0.5") == 1
    assert probe._width("9") == 1


def test_step_is_plus_one_unless_the_units_digit_is_nine(probe):
    assert probe._units_step("14") == 1
    assert probe._units_step("10") == 1
    assert probe._units_step("18") == 1
    assert probe._units_step("19") == -1
    assert probe._units_step("9") == -1
    assert probe._units_step("0.5") is None


def test_nine_moves_down_not_up(probe, corpus):
    """19 -> 18: moving up would add a digit, so the rule moves down instead."""
    down = [row for row in corpus["rows"] if row["step"] == -1]
    assert len(down) == 12
    for row in down:
        before = probe.base.slot_values(row["q"])
        after = probe.base.slot_values(row["q_cf"])
        changed = [i for i in range(len(before)) if before[i] != after[i]]
        assert len(changed) == 1
        index = changed[0]
        assert before[index].endswith("9")
        assert after[index].endswith("8")
        assert probe._width(before[index]) == probe._width(after[index])


# -- the corpus -------------------------------------------------------------
def test_coverage_numbers(corpus):
    rows = corpus["rows"]
    groups = {probe_key: 0 for probe_key in ("control", "treatment")}
    for row in rows:
        key = "treatment" if row["moved_width"] >= 2 else "control"
        groups[key] += 1
    assert len(rows) == 141
    assert corpus["dropped"] == {"no-units-move": 36}
    assert groups["treatment"] == 121
    assert groups["control"] == 20


def test_population_is_a_subset_of_section_93(corpus):
    keep = {row["i"] for row in corpus["selected"]}
    assert len(keep) == 177
    assert {row["i"] for row in corpus["rows"]} <= keep
    assert len({row["i"] for row in corpus["rows"]}) == 141


def test_only_the_chosen_operand_changes_and_only_by_one(probe, corpus):
    for row in corpus["rows"]:
        before = probe.base.slot_values(row["q"])
        after = probe.base.slot_values(row["q_cf"])
        assert len(before) == len(after)
        keep = [index for index in range(len(before)) if index not in set(row["constant_slots"])]
        differing = [index for index in keep if before[index] != after[index]]
        assert len(differing) == 1
        index = differing[0]
        assert after[index] == row["moved_slot"]
        assert abs(float(after[index]) - float(before[index])) == 1
        assert probe._width(after[index]) == probe._width(before[index])
        for other in keep:
            if other != index:
                assert after[other] == before[other]


def test_every_row_has_a_truthful_new_gold(probe, corpus):
    for row in corpus["rows"]:
        assert str(row["gold"]) != str(row["gold_cf"])
        slots = probe.base.slot_values(row["q_cf"])
        keep = [index for index in range(len(slots)) if index not in set(row["constant_slots"])]
        x = [float(slots[index]) for index in keep]
        node = probe.gram.as_node(row["node"])
        assert probe.base._agrees(probe.gram.evaluate(node, x), str(row["gold_cf"])), row["q"]


def test_groups_follow_the_original_operand_widths(probe, corpus):
    for row in corpus["rows"]:
        slots = probe.base.slot_values(row["q"])
        widths = [
            probe._width(slot)
            for index, slot in enumerate(slots)
            if index not in set(row["constant_slots"])
        ]
        treatment = max(widths) >= 2
        assert (row["moved_width"] >= 2) == treatment
        assert (row["moved_width"] == 1) == (max(widths) == 1)


def test_the_control_is_the_single_digit_population(probe, corpus):
    control = [row for row in corpus["rows"] if row["moved_width"] == 1]
    assert len(control) == 20
    for row in control:
        slots = probe.base.slot_values(row["q"])
        keep = [i for i in range(len(slots)) if i not in set(row["constant_slots"])]
        assert all(probe._width(slots[i]) == 1 for i in keep)


def test_treatment_covers_two_and_three_digit_operands(probe, corpus):
    widths = {}
    for row in corpus["rows"]:
        if row["moved_width"] >= 2:
            widths[row["moved_width"]] = widths.get(row["moved_width"], 0) + 1
    assert widths == {2: 66, 3: 55}


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
    moved = probe.perturb_units("pair 5 5", family, {"pair 5 5"})
    assert moved is None


def test_a_move_that_changes_the_number_class_is_refused(probe):
    x0 = probe.gram._x(0)
    x1 = probe.gram._x(1)
    family = _family(
        probe.gram._op("/", x0, x1), [probe.gram._op("/", x0, x1)], [], expression="x0/x1"
    )
    assert probe.perturb_units("What is 299 / 13?", family, set()) is None


def test_a_move_into_the_training_set_is_refused(probe):
    x0 = probe.gram._x(0)
    x1 = probe.gram._x(1)
    family = _family(probe.gram._op("+", x0, x1), [probe.gram._op("+", x0, x1)], [])
    moved = probe.perturb_units("pair 14 3", family, {"pair 15 3"})
    assert moved is None


# -- the decision rule ------------------------------------------------------
def _run(probe, treatment, control, arm="snn", seed=0):
    return {
        "arm": arm,
        "seed": seed,
        "groups": {
            probe.TREATMENT: treatment,
            probe.CONTROL: control,
        },
    }


def _cell(original, both):
    return {
        "n": 100,
        "correct": original,
        "both": both,
        "survival": round(both / original, 4) if original else 0.0,
    }


def test_underpowered_comes_first(probe):
    runs = [_run(probe, _cell(9, 9), _cell(14, 14))]
    assert probe.verdict(runs)["verdict"] == "underpowered"


def test_change_size_needs_half_the_treatment(probe):
    runs = [_run(probe, _cell(20, 10), _cell(14, 14))]
    assert probe.verdict(runs)["verdict"] == "change-size"


def test_operand_width_needs_the_control_to_hold(probe):
    runs = [_run(probe, _cell(20, 4), _cell(20, 12))]
    assert probe.verdict(runs)["verdict"] == "operand-width"


def test_operand_width_needs_a_thirty_point_gap(probe):
    runs = [_run(probe, _cell(20, 4), _cell(20, 8))]
    assert probe.verdict(runs)["verdict"] == "mixed"


def test_between_the_two_is_mixed(probe):
    runs = [_run(probe, _cell(20, 6), _cell(20, 12))]
    assert probe.verdict(runs)["verdict"] == "mixed"


def test_seeds_must_agree(probe):
    runs = [
        _run(probe, _cell(20, 4), _cell(20, 12), seed=0),
        _run(probe, _cell(20, 6), _cell(20, 12), seed=1),
    ]
    assert probe.verdict(runs)["verdict"] == "mixed"


def test_gru_does_not_decide(probe):
    runs = [
        _run(probe, _cell(20, 4), _cell(20, 12), arm="snn", seed=0),
        _run(probe, _cell(20, 20), _cell(20, 20), arm="gru", seed=0),
    ]
    assert probe.verdict(runs)["verdict"] == "operand-width"


# -- entry points -----------------------------------------------------------
def test_check_refuses_a_plan_report(probe, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"stage": "plan", "oracle": "digit-units"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False and "plan" in message


def test_registered_constants(probe):
    assert probe.MIN_CORRECT == 10
    assert probe.IMITATES_SHARE == 0.25
    assert probe.COMPUTES_SHARE == 0.50
    assert probe.MIN_GAP == 0.30
    assert probe.DECIDING_ARM == "snn"
    assert probe.ARMS == (("snn", 0), ("snn", 1), ("gru", 0), ("gru", 1))
