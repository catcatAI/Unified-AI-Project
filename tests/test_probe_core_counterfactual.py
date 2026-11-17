# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§91's contract is the oracle and the perturbation, not the scores.

``CORE_GAP_ANALYSIS.md`` §91 fixes, before any scored run: the corpus-derived
oracle (a family is usable only when exactly one declared expression reproduces
every training row), the perturbation rules (digit-count preserving; ratio
numerators move by a multiple of the denominator; differences move one side),
the guards (gold must change, integer class preserved, prompt unseen in
training), and the decision rule on the SNN arm.

What is tested here:

* the declared constants and the hypothesis set's shape;
* family fitting: unique fit, no fit, ambiguity, constant slots, non-numeric
  golds (the one ``"30% of 200 is 60."`` row) and the 5% cutoff;
* the constant-factor form (``weight = 9.8 * mass``) is *solved* from the corpus;
* perturbation: digit counts and integer class preserved, gold changes, ratio
  numerators move by a multiple of the denominator, differences move one side;
* the verdict table, including that GRU arms cannot change the verdict;
* ``--check`` refuses a ``--plan`` report.

No checkpoint is loaded and no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_counterfactual.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_core_counterfactual_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_core_counterfactual_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


# -- registration -----------------------------------------------------------
def test_registered_constants(probe):
    assert probe.MIN_FAMILY_ROWS == 8
    assert probe.MIN_CORRECT == 10
    assert probe.BUMP_LADDER == (1, 2, 3, 4)
    assert probe.MULTIPLE_LADDER == (1, 2, 3, 4, 5)
    assert probe.MAX_NON_NUMERIC_SHARE == 0.05
    assert probe.CONTROL_ROWS == 60
    assert probe.DECIDING_ARM == "snn"
    assert probe.ARMS == (("snn", 0), ("snn", 1), ("gru", 0), ("gru", 1))
    assert probe.CHECKPOINTS.name == "checkpoints"
    assert probe.HOLDOUT.name == "distill_val_holdout.jsonl"


def test_hypothesis_set_is_closed_and_ordered(probe):
    names = [name for name, _ in probe._candidates()]
    assert names[0] == "x0+x1"
    assert "x0/x1" in names and "x1/x0" in names and "x0%x1" in names
    assert "x0*x1/100" in names
    assert "x0+x1+x2" in names and "x0-x1-x2" in names and "x0-x1*x2" in names
    assert len(names) == len(set(names))


def test_template_and_slots(probe):
    prompt = "Compute the power when work = 1674 and time = 9."
    assert probe.digit_template(prompt) == "compute the power when work = # and time = #."
    assert probe.slot_values(prompt) == ["1674", "9"]


# -- the oracle -------------------------------------------------------------
def _family(module, rows):
    return module.fit_family(rows)


def test_unique_fit_division(probe):
    rows = [
        ("What is 768 / 24?", "32"),
        ("What is 888 / 24?", "37"),
        ("What is 324 / 12?", "27"),
        ("What is 100 / 4?", "25"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert got["expression"] == "x0/x1"
    assert got["constant_slots"] == []


def test_no_expression_is_dropped_not_patched(probe):
    rows = [("What is 3 ** 2?", "9"), ("What is 4 ** 2?", "16"), ("What is 5 ** 2?", "25")]
    got = _family(probe, rows)
    assert got["status"] == "no-expression"


def test_ambiguous_fit_is_dropped(probe, monkeypatch):
    monkeypatch.setattr(
        probe,
        "_candidates",
        lambda extra=None: [
            ("x0*x1", lambda x: x[0] * x[1]),
            ("x1*x0", lambda x: x[1] * x[0]),
        ],
    )
    rows = [("a 2 3", "6"), ("a 4 5", "20"), ("a 6 7", "42")]
    assert _family(probe, rows)["status"] == "ambiguous"


def test_constant_slot_is_removed(probe):
    """A literal that never varies is not an operand: ``3 kg`` is a constant here."""
    rows = [
        ("A 3 kg body moves 5 m.", "15"),
        ("A 3 kg body moves 7 m.", "21"),
        ("A 3 kg body moves 9 m.", "27"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert got["constant_slots"] == [0]
    assert got["operands"] == 1
    assert got["expression"] == "x0*3"


def test_units_are_not_treated_as_operands(probe):
    """``m/s2`` keeps its digit: the token is preceded by a word character."""
    prompt = "Calculate the velocity after 7s at acceleration 19 m/s2."
    assert probe.slot_values(prompt) == ["7", "19"]
    assert probe.digit_template(prompt).endswith("m/s2.")


def test_non_numeric_gold_is_excluded_and_counted(probe):
    """One prose gold in twenty is 5% — inside the cutoff, so the family survives.

    The bad row must not be repaired (it cannot be scored numerically), only
    excluded and counted; that is what makes the ``#% of #`` family usable.
    """
    rows = [
        ("What is 10% of 60?", "6"),
        ("What is 30% of 200?", "30% of 200 is 60."),
        ("What is 50% of 360?", "180"),
        ("What is 5% of 40?", "2"),
        ("What is 20% of 240?", "48"),
        ("What is 20% of 120?", "24"),
        ("What is 10% of 120?", "12"),
        ("What is 5% of 480?", "24"),
        ("What is 30% of 480?", "144"),
        ("What is 50% of 20?", "10"),
        ("What is 20% of 60?", "12"),
        ("What is 75% of 480?", "360"),
        ("What is 25% of 360?", "90"),
        ("What is 50% of 80?", "40"),
        ("What is 25% of 20?", "5"),
        ("What is 40% of 80?", "32"),
        ("What is 60% of 160?", "96"),
        ("What is 20% of 80?", "16"),
        ("What is 40% of 120?", "48"),
        ("What is 15% of 480?", "72"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert got["expression"] == "x0*x1/100"
    assert got["non_numeric"] == 1
    assert got["non_numeric"] / len(rows) <= probe.MAX_NON_NUMERIC_SHARE


def test_too_many_non_numeric_golds_drop_the_family(probe):
    rows = [
        ("What is 10% of 60?", "6"),
        ("What is 30% of 200?", "thirty percent of two hundred"),
        ("What is 50% of 360?", "half of three sixty"),
        ("What is 5% of 40?", "2"),
    ]
    assert _family(probe, rows)["status"] == "too-many-non-numeric"


def test_constant_factor_is_solved_from_the_corpus(probe):
    rows = [
        ("If mass = 10 kg, what is the weight?", "98"),
        ("If mass = 20 kg, what is the weight?", "196"),
        ("If mass = 5 kg, what is the weight?", "49"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert got["expression"] == "x0*9.8"
    assert probe.expression_value(got["expression"], [20.0]) == pytest.approx(196.0)


def test_families_below_min_rows_are_not_considered(probe):
    train = [("What is 1 / 1?", "1")] * 7
    assert probe.build_families(train) == {}


# -- perturbation -----------------------------------------------------------
def _usable(expression, constant_slots=(), operands=2):
    return {
        "status": "usable",
        "expression": expression,
        "constant_slots": list(constant_slots),
        "operands": operands,
        "template": "t",
    }


def test_perturbation_keeps_digit_count_and_class(probe):
    family = _usable("x0*x1")
    got = probe.perturb("Compute 375 * 433?", family, probe.BUMP_LADDER, set())
    assert got is not None
    assert got["gold"] != "162375"
    assert probe.slot_values(got["q"]) == ["475", "533"]
    assert len(got["gold"]) == 6 and got["gold"].isdigit()


def test_perturbation_refuses_a_prompt_seen_in_training(probe):
    family = _usable("x0+x1")
    original = "What is 892 + 517?"
    first = probe.perturb(original, family, probe.BUMP_LADDER, set())
    seen = {first["q"]}
    second = probe.perturb(original, family, probe.BUMP_LADDER, seen)
    assert second is not None and second["q"] not in seen


def test_ratio_perturbation_moves_the_numerator_by_a_multiple(probe):
    family = _usable("x0/x1")
    got = probe.perturb(
        "Compute the power when work = 1674 and time = 9.", family, probe.MULTIPLE_LADDER, set()
    )
    assert got is not None
    assert probe.slot_values(got["q"]) == ["1683", "9"]
    assert got["step"] == 1 and got["strategy"] == "numerator"
    assert got["gold"] == "187"


def test_difference_perturbation_moves_one_side_only(probe):
    """Bumping both sides leaves ``a - b`` unchanged, so the gold would not move."""
    family = _usable("x0-x1")
    got = probe.perturb("Calculate 130 - 335?", family, probe.BUMP_LADDER, set())
    assert got is not None
    assert got["strategy"] == "first"
    assert probe.slot_values(got["q"])[1] == "335"
    assert got["gold"] != "-205"


def test_perturbation_can_give_up(probe):
    """A single-digit operand that would gain a digit has no admissible step."""
    family = _usable("x0*9.8", operands=1)
    assert probe.perturb("If mass = 9 kg, what is the weight?", family, (1,), set()) is None


# -- decision ---------------------------------------------------------------
def _run(arm, seed, original, counter, n=123):
    return {
        "arm": arm,
        "seed": seed,
        "original": {"n": n, "correct": original, "rate": original / n},
        "counterfactual": {"n": n, "correct": counter, "rate": counter / n},
        "answer_changed": {"n": n, "changed": n},
    }


@pytest.mark.parametrize(
    "arms,expected",
    [
        ((("snn", 0, 17, 16), ("snn", 1, 15, 14)), "computes"),
        ((("snn", 0, 17, 1), ("snn", 1, 15, 0)), "imitates"),
        ((("snn", 0, 17, 6), ("snn", 1, 15, 5)), "mixed"),
        ((("snn", 0, 9, 0), ("snn", 1, 8, 0)), "underpowered"),
    ],
)
def test_verdict_table(probe, arms, expected):
    runs = [_run(arm, seed, original, counter) for arm, seed, original, counter in arms]
    assert probe.verdict(runs)["verdict"] == expected


def test_verdict_ignores_gru_arms(probe):
    runs = [
        _run("snn", 0, 17, 16),
        _run("snn", 1, 15, 14),
        _run("gru", 0, 12, 0),
        _run("gru", 1, 10, 0),
    ]
    got = probe.verdict(runs)
    assert got["verdict"] == "computes"
    assert got["arm"] == "snn"
    assert [cell["seed"] for cell in got["per_seed"]] == [0, 1]


def test_verdict_needs_the_deciding_arm(probe):
    assert probe.verdict([_run("gru", 0, 12, 0)])["verdict"] == "not-decided-missing-arm"


def test_check_refuses_a_plan_report(probe, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"stage": "plan"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False and "plan" in message


# -- the real corpus --------------------------------------------------------
def test_real_families_fit_without_being_patched(probe):
    families = probe.build_families(probe.read_pairs(probe.TRAIN))
    usable = {name for name, family in families.items() if family["status"] == "usable"}
    assert families["what is # / #?"]["expression"] == "x0/x1"
    assert families["what is # % #?"]["expression"] == "x0%x1"
    assert families["compute the power when work = # and time = #."]["expression"] == "x0/x1"
    assert families["what is #% of #?"]["expression"] == "x0*x1/100"
    assert (
        families["calculate the velocity after #s at acceleration # m/s2."]["constant_slots"] == []
    )
    assert (
        families["calculate the velocity after #s at acceleration # m/s2."]["expression"] == "x0*x1"
    )
    assert len(usable) >= 45
