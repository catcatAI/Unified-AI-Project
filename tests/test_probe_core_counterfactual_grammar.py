# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§92's contract is the grammar, not the scores.

``CORE_GAP_ANALYSIS.md`` §92 fixes, before any scored run: the grammar that
generates the oracle's hypotheses, the unique-fit rule (equivalent fits count as
one, ambiguous ones are dropped), the corpus-solved constant scale with ``k = 1``
tried first, the perturbation strategies (numerator, all operands, then each
single operand) and the decision rule on the SNN arm.

What is tested here:

* the grammar's size and shape, including the repeated-operand forms that a
  two-slot family needs (kinetic energy is ``0.5*m*v*v``);
* the modulo regression: solving the scale before the ``k = 1`` check used to
  drop ``x0%x1``, whose gold/value ratio varies per row;
* equivalent fits are grouped, not called ambiguous;
* perturbation can move a later operand (``Calculate 981 + 471?`` has a leading
  9 that cannot be bumped without gaining a digit);
* the verdict table, and that GRU arms cannot change the verdict;
* the real corpus: 60/62 families fit, 135/248 rows are selectable, and the
  selection is a strict superset of §91's.

No checkpoint is loaded and no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_counterfactual_grammar.py"
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
    return _load("probe_grammar_under_test", PROBE)


@pytest.fixture(scope="module")
def previous():
    return _load(
        "probe_counterfactual_under_test_92", REPO_ROOT / "scripts" / "probe_core_counterfactual.py"
    )


@pytest.fixture(scope="module")
def corpus(probe):
    train = probe.read_pairs(probe.TRAIN)
    holdout = probe.read_pairs(probe.HOLDOUT)
    families = probe.build_families(train)
    selected, dropped = probe.select_rows(holdout, families)
    return {
        "train": train,
        "holdout": holdout,
        "families": families,
        "selected": selected,
        "dropped": dropped,
    }


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
    # the thresholds are §91's, unchanged: §92 replaces the oracle only
    assert probe.MIN_CORRECT == 10 and probe.MIN_FAMILY_ROWS == 8


def test_grammar_size_is_fixed(probe):
    assert len(probe.build_candidates(2)) == 256
    assert len(probe.build_candidates(3)) == 834
    assert len(probe.build_candidates(4)) == 2200


def test_symmetric_operators_keep_one_order(probe):
    binary = [node for node in probe.build_candidates(2) if node[0] == "op"]
    names = {probe.name_of(node) for node in binary}
    assert "x0*x1" in names and "x1*x0" not in names
    assert "x0+x1" in names and "x1+x0" not in names
    # asymmetric operators keep both orders: acceleration is force / mass
    assert "x0/x1" in names and "x1/x0" in names
    assert "x0-x1" in names and "x1-x0" in names


def test_names_round_trip_through_the_shape(probe):
    node = probe._op("*", probe._op("+", probe._x(0), probe._x(1)), probe._x(2))
    assert probe.name_of(node) == "(x0+x1)*x2"
    assert probe.evaluate(node, [2.0, 3.0, 4.0]) == 20.0


# -- evaluation -------------------------------------------------------------
def test_evaluation_guards(probe):
    assert probe.evaluate(probe._op("/", probe._x(0), probe._x(1)), [1.0, 0.0]) is None
    assert probe.evaluate(probe._op("**", probe._x(0), probe._x(1)), [9.0, 13.0]) is None
    assert probe.evaluate(probe._op("%", probe._x(0), probe._x(1)), [-7.0, 3.0]) == pytest.approx(
        -1.0
    )


# -- fitting ----------------------------------------------------------------
def _family(module, rows):
    return module.fit_family(rows, len(module.base.slot_values(rows[0][0])))


def test_modulo_family_fits_with_k_equals_one(probe):
    """The scale is solved only after ``k = 1`` fails; modulo has no constant k."""
    rows = [
        ("m 7 3", "1"),
        ("m 8 3", "2"),
        ("m 9 4", "1"),
        ("m 10 4", "2"),
        ("m 11 5", "1"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert "%" in got["expression"]
    # fmod(x0 - x1, x1) == fmod(x0, x1) on every row, so several forms fit;
    # they are grouped, not called ambiguous
    assert got["equivalent"] >= 1


def test_constant_scale_is_solved_from_the_corpus(probe):
    rows = [
        ("If mass = 10 kg, what is the weight?", "98"),
        ("If mass = 20 kg, what is the weight?", "196"),
        ("If mass = 5 kg, what is the weight?", "49"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert got["expression"] == "9.8*x0"
    assert probe.evaluate(probe.as_node(got["node"]), [20.0]) == pytest.approx(196.0)


def test_two_slot_family_can_reuse_an_operand(probe):
    """Kinetic energy is ``0.5 * m * v * v``; a two-slot family has no third leaf."""
    rows = [
        ("A 2 kg body moves at 3 m/s.", "9"),
        ("A 4 kg body moves at 5 m/s.", "50"),
        ("A 6 kg body moves at 7 m/s.", "147"),
        ("A 3 kg body moves at 4 m/s.", "24"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert probe.evaluate(probe.as_node(got["node"]), [6.0, 7.0]) == pytest.approx(147.0)
    assert got["equivalent"] >= 1


def test_equivalent_fits_are_one_fit(probe):
    """``(a-b)-c`` and ``(a-c)-b`` agree on every row, so they are not ambiguous."""
    rows = [
        ("n 10 3 2", "5"),
        ("n 12 4 3", "5"),
        ("n 20 5 7", "8"),
        ("n 9 2 4", "3"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert got["equivalent"] >= 2
    assert probe.evaluate(probe.as_node(got["node"]), [10.0, 3.0, 2.0]) == 5.0


def test_every_fitting_candidate_agrees_on_the_training_rows(probe):
    """A fit must reproduce all rows, so the family keeps every fitting node."""
    rows = [
        ("n 10 3 2", "5"),
        ("n 12 4 3", "5"),
        ("n 20 5 7", "8"),
        ("n 9 2 4", "3"),
    ]
    got = _family(probe, rows)
    assert got["status"] == "usable"
    assert len(got["nodes"]) >= 2
    for node in got["nodes"]:
        for prompt, gold in rows:
            x = [float(value) for value in probe.base.slot_values(prompt)]
            assert probe.evaluate(probe.as_node(node), x) == pytest.approx(float(gold))


def test_non_numeric_gold_is_excluded_and_counted(probe):
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
    assert got["non_numeric"] == 1
    assert probe.evaluate(probe.as_node(got["node"]), [15.0, 200.0]) == pytest.approx(30.0)


def test_family_without_numeric_golds_is_dropped(probe):
    rows = [("what is the name of the city?", "Paris")] * 9
    assert _family(probe, rows)["status"] == "no-numeric-gold"


# -- perturbation -----------------------------------------------------------
def _family_node(module, node, constant_slots=()):
    width = max((leaf[1] for leaf in _leaves(node)), default=0) + 1
    return {
        "status": "usable",
        "node": node,
        "expression": module.name_of(node),
        "constant_slots": list(constant_slots),
        "operands": width,
    }


def _leaves(node):
    if node[0] == "x":
        return [node]
    if node[0] == "scale":
        return _leaves(node[2])
    return _leaves(node[2]) + _leaves(node[3])


def test_perturbation_can_move_a_later_operand(probe):
    """Bumping ``981`` would give 5 digits, so the instrument must try the other side."""
    node = probe._op("+", probe._x(0), probe._x(1))
    got = probe.perturb(
        "Calculate 981 + 471?",
        _family_node(probe, node),
        probe.BUMP_LADDER,
        probe.MULTIPLE_LADDER,
        set(),
    )
    assert got is not None
    assert probe.base.slot_values(got["q"]) == ["981", "571"]
    assert got["gold"] == "1552"
    assert got["strategy"] == "only:1"


def test_perturbation_keeps_digit_count_and_class(probe):
    node = probe._op("*", probe._x(0), probe._x(1))
    got = probe.perturb(
        "Compute 375 * 433?",
        _family_node(probe, node),
        probe.BUMP_LADDER,
        probe.MULTIPLE_LADDER,
        set(),
    )
    assert got is not None
    assert probe.base.slot_values(got["q"]) == ["475", "533"]
    assert got["gold"] == "253175"
    assert len(got["gold"]) == 6


def test_ratio_perturbation_moves_the_numerator(probe):
    node = probe._op("/", probe._x(0), probe._x(1))
    got = probe.perturb(
        "Compute the power when work = 1674 and time = 9.",
        _family_node(probe, node),
        probe.BUMP_LADDER,
        probe.MULTIPLE_LADDER,
        set(),
    )
    assert got is not None
    assert got["strategy"] == "numerator"
    assert probe.base.slot_values(got["q"]) == ["1683", "9"]
    assert got["gold"] == "187"


def test_perturbation_refuses_a_point_where_fits_disagree(probe):
    """The gold cannot depend on which fitting expression was picked."""
    node = probe._op("+", probe._x(0), probe._x(1))
    family = _family_node(probe, node)
    family["nodes"] = [node, probe._op("*", probe._x(0), probe._x(1))]
    assert (
        probe.perturb("What is 892 + 517?", family, probe.BUMP_LADDER, probe.MULTIPLE_LADDER, set())
        is None
    )


def test_perturbation_refuses_a_prompt_seen_in_training(probe):
    node = probe._op("+", probe._x(0), probe._x(1))
    family = _family_node(probe, node)
    first = probe.perturb(
        "What is 892 + 517?", family, probe.BUMP_LADDER, probe.MULTIPLE_LADDER, set()
    )
    seen = {first["q"]}
    second = probe.perturb(
        "What is 892 + 517?", family, probe.BUMP_LADDER, probe.MULTIPLE_LADDER, seen
    )
    assert second is not None and second["q"] not in seen


# -- decision ---------------------------------------------------------------
def _run(arm, seed, original, counter, n=135):
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
        (((("snn", 0, 14, 12), ("snn", 1, 12, 11))), "computes"),
        (((("snn", 0, 14, 1), ("snn", 1, 12, 0))), "imitates"),
        (((("snn", 0, 14, 5), ("snn", 1, 12, 4))), "mixed"),
        (((("snn", 0, 9, 0), ("snn", 1, 8, 0))), "underpowered"),
    ],
)
def test_verdict_table(probe, arms, expected):
    runs = [_run(arm, seed, original, counter) for arm, seed, original, counter in arms]
    assert probe.verdict(runs)["verdict"] == expected


def test_verdict_ignores_gru_arms(probe):
    runs = [
        _run("snn", 0, 14, 12),
        _run("snn", 1, 12, 11),
        _run("gru", 0, 10, 0),
        _run("gru", 1, 9, 0),
    ]
    got = probe.verdict(runs)
    assert got["verdict"] == "computes"
    assert got["arm"] == "snn"
    assert [cell["seed"] for cell in got["per_seed"]] == [0, 1]


def test_verdict_needs_the_deciding_arm(probe):
    assert probe.verdict([_run("gru", 0, 10, 0)])["verdict"] == "not-decided-missing-arm"


def test_check_refuses_a_plan_report(probe, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"stage": "plan"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False and "plan" in message


# -- the real corpus --------------------------------------------------------
def test_real_families_fit_without_being_patched(corpus):
    families = corpus["families"]
    assert len(families) == 62
    assert families["what is # % #?"]["expression"] == "x0%x1"
    assert families["what is #% of #?"]["expression"] == "0.01*(x0*x1)"
    assert families["if mass = # kg, what is the weight?"]["expression"] == "9.8*x0"
    assert (
        families["a # kg body moves at # m/s. what kinetic energy does it have in joules?"][
            "expression"
        ]
        == "0.5*((x0*x1)*x1)"
    )
    assert families["what is the name of the city?"]["status"] == "no-numeric-gold"
    assert families["what is the name of the movie?"]["status"] == "no-numeric-gold"
    usable = [family for family in families.values() if family["status"] == "usable"]
    assert len(usable) == 60


def test_real_selection_is_a_superset_of_section_91(corpus, previous):
    old_families = previous.build_families(corpus["train"])
    old_selected, _ = previous.select_rows(corpus["holdout"], old_families)
    old_indices = {row["i"] for row in old_selected}
    new_indices = {row["i"] for row in corpus["selected"]}
    assert len(new_indices) >= 130
    assert old_indices <= new_indices
    assert len(new_indices - old_indices) >= 10


def test_every_selected_row_changes_its_gold(corpus):
    for row in corpus["selected"]:
        assert row["q"].strip() != row["q_cf"].strip()
        assert str(row["gold"]).strip() != str(row["gold_cf"]).strip()
        assert row["strategy"] in ("numerator", "all", "only:0", "only:1", "only:2", "only:3")
