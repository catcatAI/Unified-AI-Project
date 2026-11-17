# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§93's contract is the family key change, and nothing else.

``CORE_GAP_ANALYSIS.md`` §93 fixes, before any scored run: the shape rule
(ASCII letters -> ``w``, digits and punctuation kept, CJK untouched), the fact
that everything else is §92's, the identical thresholds, the coverage table, and
the admission that the population was chosen after §92.9 - so the original leg is
not blind while the counterfactual leg is.

What is tested here:

* the shape rule is mechanical and merges noun variants without merging different
  skeletons;
* the coarse key can merge two formulas - the fit then fails and the family is
  dropped and counted, never guessed;
* the ``rows`` collision regression: a ``too-many-non-numeric`` family must keep
  its row list (the count under the same key would crash selection);
* the real corpus: 66 families, 49 usable, the 286-row word-problem shape fits
  ``x0*x1``, 177/248 rows are selectable;
* §93's row set is **not** a superset of §92's (125 shared, 52 new, 10 lost), so
  it is a different population rather than a re-sample of the same one.

No checkpoint is loaded and no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_counterfactual_shape.py"
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
    return _load("probe_shape_under_test", PROBE)


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


# -- the shape rule ---------------------------------------------------------
def test_shape_rule_keeps_digits_and_punctuation(probe):
    got = probe.shape_template("What is 12 % 5?")
    assert got == "w w # % #?"


def test_shape_rule_does_not_touch_non_ascii(probe):
    got = probe.shape_template("六十一減八十四等於多少？")
    assert got == "六十一減八十四等於多少？"


def test_noun_variants_collapse_to_one_shape(probe):
    a = probe.shape_template("Lina has 7 drawers with 8 seeds in each. How many seeds altogether?")
    b = probe.shape_template("Ken has 8 bins with 3 ribbons in each. How many ribbons altogether?")
    assert a == b == "w w # w w # w w w. w w w w?"


def test_different_skeletons_stay_apart(probe):
    one_step = probe.shape_template(
        "Lina has 7 drawers with 8 seeds in each. How many seeds altogether?"
    )
    two_step = probe.shape_template(
        "Lina fills 7 drawers with 8 seeds each, then adds 3 more seeds. Total seeds?"
    )
    assert one_step != two_step


def test_shape_is_coarser_than_the_digit_template(probe):
    """The same pair of prompts is two templates but one shape."""
    a = "Lina has 7 drawers with 8 seeds in each. How many seeds altogether?"
    b = "Ken has 8 bins with 3 ribbons in each. How many ribbons altogether?"
    assert probe.base.digit_template(a) != probe.base.digit_template(b)
    assert probe.shape_template(a) == probe.shape_template(b)


# -- families ---------------------------------------------------------------
def test_rows_collision_does_not_replace_the_row_list(probe):
    """A family that drops on non-numeric golds must not have ``rows`` -> int."""
    rows = [(f"What is {a} + 2?", str(a + 2)) for a in range(10, 21)]
    rows.append(("What is 5 + 2?", "five plus two"))
    families = probe.build_families(rows)
    family = families[probe.shape_template("What is 5 + 2?")]
    assert family["status"] == "too-many-non-numeric"
    assert isinstance(family["rows"], list)
    assert len(family["rows"]) == len(rows)


def test_merged_formulas_drop_the_family_instead_of_guessing(probe, monkeypatch):
    monkeypatch.setattr(
        probe.gram,
        "build_candidates",
        lambda width: [probe.gram._x(0), probe.gram._op("*", probe.gram._x(0), probe.gram._x(1))],
    )
    rows = [(f"thing {a} {b}", str(a + b)) for a, b in ((10, 3), (12, 5), (20, 7), (9, 4))]
    rows += [(f"thing {a} {b}", str(a * b)) for a, b in ((10, 3), (12, 5), (20, 7), (9, 4))]
    family = probe.build_families(rows)[probe.shape_template("thing 10 3")]
    assert family["status"] in ("no-expression", "inconsistent-fit", "too-many-non-numeric")


def test_real_word_problem_shape_fits_a_product(corpus):
    families = corpus["families"]
    one_step = "w w # w w # w w w. w w w w?"
    two_step = "w w # w w # w w, w w # w w. w w?"
    assert families[one_step]["n"] == 286
    assert families[one_step]["expression"] == "x0*x1"
    assert families[two_step]["n"] == 247
    assert families[two_step]["expression"] == "(x0*x1)+x2"


def test_real_family_counts(corpus):
    families = corpus["families"]
    statuses = {}
    for family in families.values():
        statuses[family["status"]] = statuses.get(family["status"], 0) + 1
    assert len(families) == 66
    assert statuses["usable"] == 49
    assert statuses["too-many-non-numeric"] == 9
    assert statuses["no-numeric-gold"] == 7


# -- selection --------------------------------------------------------------
def test_every_selected_row_is_a_valid_counterfactual(corpus):
    for row in corpus["selected"]:
        assert row["q"].strip() != row["q_cf"].strip()
        assert str(row["gold"]).strip() != str(row["gold_cf"]).strip()
        assert row["strategy"] in ("numerator", "all", "only:0", "only:1", "only:2", "only:3")


def test_selected_count_and_no_perturbation_failures(corpus):
    assert len(corpus["selected"]) == 177
    assert corpus["dropped"] == {"family-not-usable": 71}


def test_selection_is_not_a_superset_of_section_92(corpus, probe):
    """A coarser key loses rows where it merges two formulas; that is counted."""
    other = _load(
        "probe_grammar_for_shape_test",
        REPO_ROOT / "scripts" / "probe_core_counterfactual_grammar.py",
    )
    other_families = other.build_families(corpus["train"])
    old_selected, _ = other.select_rows(corpus["holdout"], other_families)
    old = {row["i"] for row in old_selected}
    new = {row["i"] for row in corpus["selected"]}
    assert len(new) == 177 and len(old) == 135
    assert len(new & old) == 125
    assert len(new - old) == 52
    assert len(old - new) == 10


def test_shape_family_rewrites_only_the_operands(corpus, probe):
    """The perturbed prompt must keep every word, so the shape is unchanged."""
    for row in corpus["selected"][:40]:
        assert probe.shape_template(row["q"]) == probe.shape_template(row["q_cf"])
        assert probe.base.slot_values(row["q"]) != probe.base.slot_values(row["q_cf"])


# -- entry points -----------------------------------------------------------
def test_check_refuses_a_plan_report(probe, tmp_path):
    path = tmp_path / "plan.json"
    path.write_text('{"stage": "plan", "oracle": "shape"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False and "plan" in message


def test_registered_constants_are_section_92s(probe):
    assert probe.MIN_FAMILY_ROWS == 8
    assert probe.MIN_CORRECT == 10
    assert probe.BUMP_LADDER == (1, 2, 3, 4)
    assert probe.MULTIPLE_LADDER == (1, 2, 3, 4, 5)
    assert probe.DECIDING_ARM == "snn"
    assert probe.ARMS == (("snn", 0), ("snn", 1), ("gru", 0), ("gru", 1))
