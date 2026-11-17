# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§86 exists because §85's *instrument* failed, so the instrument is the unit.

No training happens here. What is tested is the rule frozen in
``CORE_GAP_ANALYSIS.md`` §86.5 and the three decisions §86.3 is built on:

* ``N0`` is **gone** — a set of rows in which the widened child's training loss
  rises must never be relabelled "did not learn";
* the item margin is **9**, not 5, so §85's −6.7-item gap reads ``N4``
  (unresolved) rather than a branch;
* the margins are a **parameter**, because ``--check`` must verify an old
  report against the rule it was registered with.

A test that only checked "the script runs" would not notice any of them.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_ladder86.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_ladder86_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_ladder86_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


def row(
    arm,
    seed,
    final,
    hits,
    n=248.0,
    holdout_ce=4.0,
    train_start=0.70,
    train_end=0.60,
):
    return {
        "arm": arm,
        "seed": seed,
        "val_ce": final,
        "holdout_ce": holdout_ce,
        "holdout_hits": hits,
        "holdout_n": n,
        "train_ce_full_start": train_start,
        "train_ce_full_end": train_end,
        "ms_per_row": 30.0,
        "seconds": 300.0,
        "params": 12_069_723.0,
    }


def arms(
    warm_final,
    warm_hits,
    control_final=4.63,
    control_hits=24.67,
    warm_train_start=0.70,
    warm_train_end=0.60,
    seeds=(3, 4, 5),
):
    rows = []
    for seed in seeds:
        rows.append(
            row(
                "warm",
                seed,
                warm_final,
                warm_hits,
                train_start=warm_train_start,
                train_end=warm_train_end,
            )
        )
        rows.append(row("width_control", seed, control_final, control_hits))
        rows.append(row("cold", seed, 2.58, 1.67, holdout_ce=6.0))
    return rows


# -- the registered instrument ----------------------------------------------


def test_registered_margins_are_the_documented_ones(probe):
    # §86.5: CE unchanged at 0.15 (3.6 sd); items tightened 5 -> 9 (2 sd of 4.5).
    assert probe.MARGIN_CE == 0.15
    assert probe.MARGIN_ITEMS == 9.0
    assert probe.MARGINS == {"ce_nats": 0.15, "holdout_items": 9.0}


def test_the_ce_margin_was_not_loosened(probe):
    import probe_ladder85 as p85

    assert probe.MARGIN_CE == p85.MARGIN_CE
    assert probe.MARGIN_ITEMS > p85.MARGIN_ITEMS


def test_n0_is_retired(probe):
    # §86.3: a rising training loss is a *result*, not "the arm did not learn".
    # The §85 branch must not be reachable from any outcome.
    base = arms(warm_final=3.66, warm_hits=18.0)
    rising = arms(warm_final=3.66, warm_hits=18.0, warm_train_start=0.70, warm_train_end=0.95)
    for rows in (base, rising):
        assert probe.decide(rows)["branch"] != "N0-unusable"
    assert probe.decide(rising)["branch"] == probe.decide(base)["branch"]


def test_the_plan_covers_the_new_file_and_the_shared_trainer(probe):
    names = {Path(p).name for p in probe.IMPL_FILES}
    assert "probe_ladder86.py" in names
    assert "probe_ladder85.py" in names  # run_arm is imported, not copied
    assert "token_snn.py" in names


# -- the branch table --------------------------------------------------------


def test_n1_requires_both_instruments(probe):
    decision = probe.decide(arms(warm_final=3.66, warm_hits=44.0, control_final=4.63))
    assert decision["branch"] == "N1-ladder-pays"
    assert decision["ce_ruler"]["state"] == "warm-better"
    assert decision["item_ruler"]["state"] == "warm-better"


def test_n3_requires_both_instruments(probe):
    decision = probe.decide(arms(warm_final=5.80, warm_hits=10.0, control_final=4.63))
    assert decision["branch"] == "N3-ladder-hurts"


def test_n2_is_no_resolvable_gain_not_equality(probe):
    decision = probe.decide(arms(warm_final=4.60, warm_hits=24.0, control_final=4.63))
    assert decision["branch"] == "N2-no-resolvable-gain"
    assert "not equality" in decision["reason"]


def test_the_85_pattern_reads_n4_and_says_which_ruler_resolved(probe):
    # §85 on seeds 0-2: CE +0.97 in warm's favour, items -6.7 (inside 2 sd = 9).
    decision = probe.decide(
        arms(warm_final=3.6641, warm_hits=18.0, control_final=4.6317, control_hits=24.67)
    )
    assert decision["branch"] == "N4-inconsistent"
    assert decision["ce_ruler"]["state"] == "warm-better"
    assert decision["item_ruler"]["state"] == "unresolved"
    assert "unresolved" in decision["reason"]


def test_losing_eleven_items_while_winning_ce_is_still_n4(probe):
    # The item ruler resolves (worse) but the CE ruler resolves the other way.
    decision = probe.decide(arms(warm_final=3.6641, warm_hits=13.0, control_final=4.6317))
    assert decision["branch"] == "N4-inconsistent"
    assert decision["item_ruler"]["state"] == "warm-worse"


def test_eight_items_is_not_enough_for_n3(probe):
    # 9 is 2 sd; 8 items with a resolved CE gap is exactly the "unresolved" case.
    decision = probe.decide(arms(warm_final=5.80, warm_hits=16.67, control_final=4.63))
    assert decision["branch"] == "N4-inconsistent"


def test_decision_is_undecided_without_the_control_arm(probe):
    rows = [r for r in arms(warm_final=3.66, warm_hits=18.0) if r["arm"] != "width_control"]
    decision = probe.decide(rows)
    assert decision["branch"] == "UNDECIDED"
    assert "width_control" in decision["reason"]


def test_margins_are_a_parameter_not_a_module_read(probe):
    # --check must verify an old report against the rule it was registered
    # with; passing margins must change the branch for the same rows.
    rows = arms(warm_final=3.6641, warm_hits=18.0, control_final=4.6317, control_hits=24.67)
    assert probe.decide(rows)["branch"] == "N4-inconsistent"
    relaxed = probe.decide(rows, margins={"ce_nats": 0.15, "holdout_items": 5.0})
    assert relaxed["branch"] == "N4-inconsistent"  # CE positive, items negative
    strict = probe.decide(rows, margins={"ce_nats": 1.20, "holdout_items": 9.0})
    assert strict["branch"] == "N2-no-resolvable-gain"
    assert strict["margins"] == {"ce_nats": 1.20, "holdout_items": 9.0}


# -- the rulers and their spread --------------------------------------------


def test_paired_signs_mean_warm_is_better(probe):
    rows = arms(warm_final=3.66, warm_hits=30.0, control_final=4.63, control_hits=24.67)
    pair = probe.paired(rows)
    assert pair["delta_ce"] == pytest.approx(4.63 - 3.66, abs=1e-9)
    assert pair["delta_items"] == pytest.approx(5.33, abs=1e-9)
    assert pair["sign_agreement"] == {"ce": 3, "items": 3, "n": 3}
    assert [r["seed"] for r in pair["per_seed"]] == [3, 4, 5]


def test_per_seed_spread_is_reported_for_every_ruler(probe):
    rows = arms(warm_final=3.66, warm_hits=30.0)
    rows[0]["val_ce"] = 3.50  # seed 3
    rows[3]["val_ce"] = 3.80  # seed 4
    summary = probe.summarise(rows)
    assert summary["warm"]["val_ce_sd"] > 0.0
    assert {"holdout_ce", "holdout_ce_sd", "train_ce_full_start", "train_ce_full_end"} <= set(
        summary["warm"]
    )
    assert summary["warm"]["train_ce_full_delta"] == pytest.approx(-0.10, abs=1e-9)


def test_holdout_ce_is_the_continuous_version_of_the_item_ruler(probe):
    rows = arms(warm_final=3.66, warm_hits=30.0)
    for r in rows:
        if r["arm"] == "warm":
            r["holdout_ce"] = 3.0  # warm predicts the hold-out better ...
    pair = probe.paired(rows)
    # ... so, like delta_ce, a positive difference means "warm is better".
    assert pair["delta_holdout_ce"] == pytest.approx(1.0, abs=1e-9)
    summary = probe.summarise(rows)
    assert summary["warm"]["holdout_ce"] == pytest.approx(3.0)


def test_measure_ce_returns_finite_rulers_on_a_tiny_model(probe):
    from ai.ed3n.token_snn import CharVocab, TokenConfig, TokenSNN

    vocab = CharVocab.build(["1+1=2", "2+2=4"], min_count=1)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16, layers=1), device="cpu")
    pairs = [("1+1?", "2"), ("2+2?", "4")]
    measured = probe.measure_ce(model, pairs, pairs, pairs, batch=2)
    assert set(measured) == {"val_ce", "holdout_ce", "train_ce_full"}
    for value in measured.values():
        assert 0.0 < value < 100.0


def test_every_ruler_has_a_row_key_and_the_two_lists_agree(probe):
    # --check compares a recomputed ruler against the row field it was written
    # to; train_ce_full is stored as *_end, so a name guess would KeyError.
    assert tuple(probe.RULER_ROW_KEYS) == probe.RULERS
    rows = arms(warm_final=3.66, warm_hits=30.0)
    for ruler, key in probe.RULER_ROW_KEYS.items():
        assert key in rows[0], f"{ruler} is not stored anywhere on the row"


def test_the_two_rulers_are_different_quantities(probe):
    # 86.2: train_ce_full is mean_ce over 5,144 rows, not the curve's
    # token-weighted train_loss. Keeping the names apart is the whole point.
    rows = arms(warm_final=3.66, warm_hits=30.0)
    summary = probe.summarise(rows)
    assert "train_loss" not in summary["warm"]
    assert summary["warm"]["train_ce_full_start"] == pytest.approx(0.70)
