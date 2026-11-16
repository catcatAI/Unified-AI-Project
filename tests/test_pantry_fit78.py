# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§78 contract tests: the matched-fit readout and the verdict arithmetic.

Nothing here loads a carrier. The tests pin the registered device (a readout
step ladder, a matching rule chosen from in-sample fit only, the capacity cap)
and the arithmetic that turns stored cells into a branch, so a tampered or
stale report is refused without a trained checkpoint.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIT78 = REPO_ROOT / "scripts" / "probe_pantry_fit78.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fit78():
    return _load_module("pantry_fit78_under_test", FIT78)


def rung(steps, exact, capacity=0.10, *, n=400):
    return {
        "steps": int(steps),
        "in_sample_correct": int(round(exact * n)),
        "in_sample_n": int(n),
        "in_sample_exact": float(exact),
        "capacity_correct": int(round(capacity * n)),
        "capacity_exact": float(capacity),
        "admissible": bool(capacity < 0.50),
    }


def observed(exact, overlap, *, n=200):
    correct = int(round(exact * n))
    overlap_sum = round(overlap * n)
    matched = round(overlap_sum / 2)
    return {
        "n": n,
        "correct": correct,
        "exact": round(correct / n, 4),
        "overlap_sum": overlap_sum,
        "overlap": round(overlap_sum / n, 4),
        "overlap_histogram": {"1": n - matched, "2": matched},
    }


def null_block(p_value=0.002494):
    return {
        "draws": 400,
        "ge": 0,
        "p_value": p_value,
        "exact": {"mean": 0.0, "std": 0.0, "p99": 0.0},
        "overlap": {"mean": 0.0, "std": 0.0, "p99": 0.0},
    }


def cell(steps, *, fit, held, lro_exact, lro_overlap):
    return {
        "steps": int(steps),
        "in_sample": {"observed": observed(fit, 0.5), "null": null_block()},
        "heldout": {"observed": observed(held, 0.6), "null": null_block()},
        "leave_roster_out": {
            "observed": observed(lro_exact, lro_overlap),
            "null": null_block(),
            "rosters": 62,
            "fold_size": {"min": 1, "max": 8, "median": 3},
            "per_fold": [],
        },
        "seen": {"observed": observed(held, 0.6), "null": null_block()},
        "unseen": {"observed": observed(0.0, 0.0), "null": null_block()},
    }


def report(fit78, *, treatment_overlap=1.40, matched_control_overlap=1.30):
    """A coherent minimal report: matching at control@8000 vs treatment@2000."""
    control_ladder = [
        rung(250, 0.10),
        rung(500, 0.25),
        rung(1000, 0.40),
        rung(2000, 0.50),
        rung(4000, 0.60),
        rung(8000, 0.70),
    ]
    treatment_ladder = [
        rung(250, 0.15),
        rung(500, 0.30),
        rung(1000, 0.45),
        rung(2000, 0.65),
        rung(4000, 0.80),
        rung(8000, 0.90),
    ]
    cells = {
        "control": {
            "2000": cell(2000, fit=0.50, held=0.20, lro_exact=0.10, lro_overlap=1.10),
            "8000": cell(
                8000, fit=0.70, held=0.30, lro_exact=0.20, lro_overlap=matched_control_overlap
            ),
        },
        "treatment": {
            "2000": cell(2000, fit=0.65, held=0.40, lro_exact=0.30, lro_overlap=treatment_overlap),
            "8000": cell(8000, fit=0.90, held=0.45, lro_exact=0.35, lro_overlap=treatment_overlap),
        },
    }
    reference = {
        "path": "data/pantry_stage/item77/k2.json",
        "cells": {
            "control": {"in_sample": 0.50, "heldout": 0.20, "lro_exact": 0.10, "lro_overlap": 1.10},
            "treatment": {
                "in_sample": 0.65,
                "heldout": 0.40,
                "lro_exact": 0.30,
                "lro_overlap": treatment_overlap,
            },
        },
    }
    data = {
        "stage": fit78.STAGE,
        "k": 2,
        "probe": {
            "family": fit78.FAMILY,
            "steps_ladder": list(fit78.STEPS_LADDER),
            "anchor_steps": fit78.ANCHOR_STEPS,
            "null_draws": fit78.NULL_DRAWS,
            "null_seed": fit78.NULL_SEED,
            "alpha": fit78.ALPHA,
            "contrast_margin": fit78.CONTRAST_MARGIN,
            "fit_match_tolerance": fit78.FIT_MATCH_TOLERANCE,
            "ladder_span_floor": fit78.LADDER_SPAN_MIN,
            "composition_overlap_fraction": fit78.COMPOSED_OVERLAP_FRACTION,
            "capacity_max": fit78.CAPACITY_MAX,
            "chance": {"exact": 0.0128, "overlap": 0.3077},
        },
        "ladder": {
            arm: {
                "corpus": {"digests_match": True},
                "instrument": {
                    "carrier_unchanged": True,
                    "checkpoint_unchanged": True,
                    "mode_matches": True,
                },
                "ladder": control_ladder if arm == "control" else treatment_ladder,
                "effective": fit78.ladder_effective(
                    control_ladder if arm == "control" else treatment_ladder
                ),
            }
            for arm in ("control", "treatment")
        },
        "match": fit78.match_pair(control_ladder, treatment_ladder),
        "cells": cells,
        "anchor": {
            "steps": fit78.ANCHOR_STEPS,
            "reference": reference,
            "reproduction": fit78.reproduction(cells, reference),
        },
    }
    data["gates"] = fit78.gates(data)
    data["branch"] = fit78.branch(data["gates"])
    return data


# --------------------------------------------------------------------------- #
# the registered device
# --------------------------------------------------------------------------- #
def test_the_ladder_is_registered_and_contains_the_anchor(fit78):
    assert fit78.STEPS_LADDER == (250, 500, 1000, 2000, 4000, 8000)
    assert fit78.ANCHOR_STEPS in fit78.STEPS_LADDER
    assert fit78.STEPS_LADDER == tuple(sorted(fit78.STEPS_LADDER))
    assert fit78.FAMILY == "linear_values"


def test_the_match_tolerance_is_tighter_than_section_77(fit78):
    # §77 made the contrast unreadable at a 0.15 fit gap; this stage may only
    # tighten that, never loosen it.
    assert fit78.FIT_MATCH_TOLERANCE < 0.15
    assert fit78.FIT_MATCH_TOLERANCE == 0.05


def test_the_capacity_cap_is_section_70s(fit78):
    assert fit78.CAPACITY_MAX == 0.50
    assert fit78.LADDER_SPAN_MIN == 0.10


# --------------------------------------------------------------------------- #
# the ladder
# --------------------------------------------------------------------------- #
def test_a_monotone_ladder_with_span_passes(fit78):
    block = fit78.ladder_effective([rung(250, 0.10), rung(2000, 0.40), rung(8000, 0.70)])
    assert block["pass"] is True
    assert block["monotone"] is True
    assert block["span"] == pytest.approx(0.60)


def test_a_flat_ladder_fails_even_when_monotone(fit78):
    block = fit78.ladder_effective([rung(250, 0.40), rung(2000, 0.42), rung(8000, 0.43)])
    assert block["monotone"] is True
    assert block["pass"] is False
    assert block["span"] < fit78.LADDER_SPAN_MIN


def test_a_ladder_that_goes_backwards_fails(fit78):
    block = fit78.ladder_effective([rung(250, 0.10), rung(2000, 0.50), rung(8000, 0.30)])
    assert block["monotone"] is False
    assert block["pass"] is False


# --------------------------------------------------------------------------- #
# the matching rule
# --------------------------------------------------------------------------- #
def test_the_match_takes_the_highest_common_fit(fit78):
    control = [rung(500, 0.30), rung(2000, 0.50), rung(8000, 0.70)]
    treatment = [rung(500, 0.35), rung(2000, 0.65), rung(8000, 0.90)]
    match = fit78.match_pair(control, treatment)
    assert match["found"] is True
    # 0.70 (control@8000) against 0.65 (treatment@2000) is the highest pair
    assert match["control_steps"] == 8000
    assert match["treatment_steps"] == 2000
    assert match["level"] == pytest.approx(0.65)
    assert match["gap"] == pytest.approx(0.05)


def test_an_inadmissible_rung_cannot_be_matched(fit78):
    control = [rung(2000, 0.50), rung(8000, 0.70, capacity=0.60)]
    treatment = [rung(2000, 0.65)]
    match = fit78.match_pair(control, treatment)
    assert match["found"] is False
    assert match["control_ceiling"] == pytest.approx(0.50)
    assert 8000 not in match["control_admissible_steps"]


def test_a_gap_over_the_tolerance_is_not_a_match(fit78):
    control = [rung(2000, 0.40)]
    treatment = [rung(2000, 0.60)]
    assert fit78.match_pair(control, treatment)["found"] is False


def test_the_tie_break_prefers_the_smaller_gap_then_the_smaller_budget(fit78):
    control = [rung(2000, 0.50), rung(4000, 0.54)]
    treatment = [rung(8000, 0.50)]
    match = fit78.match_pair(control, treatment)
    assert match["control_steps"] == 2000  # gap 0.00 beats 0.04 at 4000
    control = [rung(2000, 0.50), rung(4000, 0.50)]
    match = fit78.match_pair(control, treatment)
    assert match["control_steps"] == 2000  # equal gap, smaller total budget


# --------------------------------------------------------------------------- #
# the delta and the branch precedence
# --------------------------------------------------------------------------- #
def test_the_delta_uses_overlap_and_the_composition_floor(fit78):
    gates = fit78.gates(report(fit78, treatment_overlap=1.40))
    delta = gates["delta"]
    assert delta["overlap_delta"] == pytest.approx(0.10)
    assert delta["gain"] is True
    assert delta["above_floor"] is False
    assert delta["floor"] == pytest.approx(1.5)


def test_a_gain_below_the_floor_is_f3(fit78):
    data = report(fit78, treatment_overlap=1.40)
    assert data["branch"]["id"] == "F3-gain-below-floor-at-matched-fit"


def test_a_gain_above_the_floor_is_f2(fit78):
    data = report(fit78, treatment_overlap=1.60)
    assert data["branch"]["id"] == "F2-gain-above-floor-at-matched-fit"


def test_no_gain_is_f4(fit78):
    data = report(fit78, treatment_overlap=1.32)
    assert data["branch"]["id"] == "F4-fit-explains-the-delta"


def test_no_matched_pair_is_f1(fit78):
    data = report(fit78)
    data["ladder"]["control"]["ladder"] = [
        rung(250, 0.10),
        rung(500, 0.15),
        rung(1000, 0.20),
        rung(2000, 0.25),
        rung(4000, 0.30),
        rung(8000, 0.35),
    ]
    data["ladder"]["treatment"]["ladder"] = [
        rung(250, 0.60),
        rung(500, 0.65),
        rung(1000, 0.70),
        rung(2000, 0.75),
        rung(4000, 0.80),
        rung(8000, 0.85),
    ]
    for arm in ("control", "treatment"):
        data["ladder"][arm]["effective"] = fit78.ladder_effective(data["ladder"][arm]["ladder"])
    data["match"] = fit78.match_pair(
        data["ladder"]["control"]["ladder"], data["ladder"]["treatment"]["ladder"]
    )
    data["gates"] = fit78.gates(data)
    data["branch"] = fit78.branch(data["gates"])
    assert data["match"]["found"] is False
    assert data["branch"]["id"] == "F1-fit-not-matchable"


def test_a_broken_instrument_short_circuits_the_branch(fit78):
    data = report(fit78, treatment_overlap=1.60)
    data["ladder"]["treatment"]["instrument"]["carrier_unchanged"] = False
    data["gates"] = fit78.gates(data)
    data["branch"] = fit78.branch(data["gates"])
    assert data["branch"]["id"] == "F0-instrument"


def test_an_ungated_matched_cell_is_f5(fit78):
    data = report(fit78, treatment_overlap=1.60)
    data["cells"]["control"]["8000"]["leave_roster_out"]["null"]["p_value"] = 0.5
    data["gates"] = fit78.gates(data)
    data["branch"] = fit78.branch(data["gates"])
    assert data["branch"]["id"] == "F5-ungated-at-matched-fit"


def test_the_branch_order_is_the_registered_one(fit78):
    assert fit78.BRANCH_ORDER == (
        "F0-instrument",
        "F1-fit-not-matchable",
        "F5-ungated-at-matched-fit",
        "F2-gain-above-floor-at-matched-fit",
        "F3-gain-below-floor-at-matched-fit",
        "F4-fit-explains-the-delta",
    )


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _write(tmp_path, data):
    path = tmp_path / "k2.json"
    path.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_a_coherent_report_passes_the_check(fit78, tmp_path):
    assert fit78.check(_write(tmp_path, report(fit78))) == []


def test_the_check_refuses_another_stage(fit78, tmp_path):
    data = report(fit78)
    data["stage"] = "§77 the content written per turn: one write per list item"
    problems = fit78.check(_write(tmp_path, data))
    assert problems == ["this is not a §78 report"]


def test_the_check_refuses_a_loosened_tolerance(fit78, tmp_path):
    data = report(fit78)
    data["probe"]["fit_match_tolerance"] = 0.15
    problems = fit78.check(_write(tmp_path, data))
    assert any("fit_match_tolerance" in problem for problem in problems)


def test_the_check_refuses_a_tampered_ladder(fit78, tmp_path):
    data = report(fit78)
    data["ladder"]["control"]["ladder"][3]["in_sample_exact"] = 0.99
    problems = fit78.check(_write(tmp_path, data))
    assert any("in-sample exact" in problem for problem in problems)


def test_the_check_refuses_a_stale_match(fit78, tmp_path):
    data = report(fit78)
    data["match"]["control_steps"] = 4000
    problems = fit78.check(_write(tmp_path, data))
    assert any("match does not follow" in problem for problem in problems)


def test_a_missing_matched_cell_fails_the_gate_instead_of_crashing(fit78):
    data = report(fit78)
    del data["cells"]["control"]["8000"]
    block = fit78.gates(data)
    assert block["W1_match_found"]["pass"] is True
    assert block["W2_matched_cells_gated"]["pass"] is False
    assert block["delta"] is None


def test_the_check_refuses_a_stale_branch(fit78, tmp_path):
    data = report(fit78)
    data["branch"] = dict(data["branch"], id="F2-gain-above-floor-at-matched-fit")
    problems = fit78.check(_write(tmp_path, data))
    assert any("branch is stale" in problem for problem in problems)


def test_the_check_refuses_an_inconsistent_cell(fit78, tmp_path):
    data = report(fit78)
    data["cells"]["control"]["2000"]["heldout"]["observed"]["exact"] = 0.99
    problems = fit78.check(_write(tmp_path, data))
    assert any("exact does not equal correct/n" in problem for problem in problems)


def test_the_check_refuses_a_broken_anchor_reproduction(fit78, tmp_path):
    data = report(fit78)
    data["anchor"]["reference"]["cells"]["control"]["in_sample"] = 0.99
    problems = fit78.check(_write(tmp_path, data))
    assert any("anchor reproduction" in problem for problem in problems)


def test_the_check_refuses_a_stale_gate_block(fit78, tmp_path):
    data = copy.deepcopy(report(fit78))
    data["gates"]["W1_match_found"]["pass"] = False
    problems = fit78.check(_write(tmp_path, data))
    assert any("gates do not re-derive" in problem for problem in problems)
