# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""The §85 branch table is the decision, so the branch table is what gets tested.

No training happens here: ``decide()`` takes per-seed rows and applies the rule
frozen in ``CORE_GAP_ANALYSIS.md`` §85.5. A test that only checked "the script
runs" would not notice the one failure that matters — a margin or a priority
silently changed after the numbers were seen.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_ladder85.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_ladder85_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_ladder85_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


def row(arm, seed, start, final, hits, n=248.0, start_train=0.8799, final_train=0.50):
    return {
        "arm": arm,
        "seed": seed,
        "start_val_ce": start,
        "final_val_ce": final,
        "start_train_ce200": start_train,
        "final_train_ce200": final_train,
        "holdout_hits": hits,
        "holdout_n": n,
        "ms_per_row": 30.0,
        "seconds": 300.0,
        "params": 12_069_723.0,
    }


def arms(
    warm_final,
    warm_hits,
    control_final=5.6,
    control_hits=28.0,
    warm_start=5.6963,
    warm_train=0.50,
    seeds=(0, 1, 2),
):
    rows = []
    for seed in seeds:
        rows.append(row("warm", seed, warm_start, warm_final, warm_hits, final_train=warm_train))
        rows.append(row("width_control", seed, 5.6964, control_final, control_hits))
        rows.append(row("cold", seed, 8.3575, 6.4, 4.0, start_train=8.1, final_train=4.2))
    return rows


def test_registered_margins_are_the_documented_ones(probe):
    # §85.5: 0.15 nats (2.5x the measured seed spread) and 5 hold-out items.
    assert probe.MARGIN_CE == 0.15
    assert probe.MARGIN_ITEMS == 5.0


def test_n0_wins_when_the_widened_child_does_not_learn(probe):
    # N0 is the *training* criterion: a child whose train CE never falls did
    # not learn, so its validation numbers cannot be interpreted.
    decision = probe.decide(
        arms(
            warm_final=5.9, warm_hits=20.0, control_final=6.5, control_hits=10.0, warm_train=0.8795
        )
    )
    assert decision["branch"] == "N0-unusable"


def test_n1_requires_both_instruments(probe):
    decision = probe.decide(
        arms(warm_final=5.2, warm_hits=40.0, control_final=5.6, control_hits=28.0)
    )
    assert decision["branch"] == "N1-ladder-pays"


def test_n3_requires_both_instruments(probe):
    decision = probe.decide(
        arms(warm_final=6.0, warm_hits=20.0, control_final=5.6, control_hits=28.0)
    )
    assert decision["branch"] == "N3-ladder-hurts"


def test_n2_is_no_resolvable_gain_not_equality(probe):
    decision = probe.decide(
        arms(warm_final=5.50, warm_hits=28.0, control_final=5.6, control_hits=28.0)
    )
    assert decision["branch"] == "N2-no-resolvable-gain"
    assert "no-resolvable" in decision["branch"]


def test_disagreeing_instruments_do_not_decide(probe):
    # CE says the ladder pays, the hold-out says it costs: that is N4, not N1.
    decision = probe.decide(
        arms(warm_final=5.2, warm_hits=10.0, control_final=5.6, control_hits=28.0)
    )
    assert decision["branch"] == "N4-inconsistent"


def test_one_margin_alone_is_not_enough(probe):
    # CE gain 0.10 nats (< 0.15) with +20 hold-out items: neither branch fires.
    decision = probe.decide(
        arms(warm_final=5.5, warm_hits=48.0, control_final=5.6, control_hits=28.0)
    )
    assert decision["branch"] == "N4-inconsistent"


def test_decision_is_undecided_without_the_control_arm(probe):
    rows = [r for r in arms(5.2, 40.0) if r["arm"] != "width_control"]
    decision = probe.decide(rows)
    assert decision["branch"] == "UNDECIDED"
    assert "width_control" in decision["reason"]


def test_summary_averages_seeds_and_reports_spread(probe):
    rows = arms(5.0, 30.0, seeds=(0, 1, 2))
    for index, value in enumerate((4.9, 5.0, 5.1)):
        rows[index * 3]["final_val_ce"] = value
    summary = probe.summarise(rows)["warm"]
    assert summary["seeds"] == 3
    assert summary["final_val_ce"] == pytest.approx(5.0)
    assert summary["final_val_ce_sd"] == pytest.approx(0.1)
    assert summary["final_val_ce_min"] == pytest.approx(4.9)


def test_cold_is_a_reference_not_a_branch(probe):
    decision = probe.decide(arms(warm_final=5.2, warm_hits=40.0))
    assert decision["cold_reference"]["warm_minus_cold_ce"] > 0
    assert "better than random init" in decision["cold_reference"]["reading"]


def test_shuffle_digest_is_the_train_on_rule(probe):
    import random

    order = list(range(50))
    random.Random(7).shuffle(order)
    digest = probe.shuffle_digest(50, 7, 0)
    assert digest == probe.shuffle_digest(50, 7, 0)
    assert digest != probe.shuffle_digest(50, 8, 0)
    assert digest != probe.shuffle_digest(50, 7, 1)


def test_mean_ce_is_finite_on_a_tiny_model(probe):
    from ai.ed3n.token_snn import CharVocab, TokenConfig, TokenSNN

    vocab = CharVocab.build(["1+1=2", "2+2=4"], min_count=1)
    model = TokenSNN(vocab, TokenConfig(d_emb=8, d_hidden=8, max_len=16, layers=1), device="cpu")
    pairs = [("1+1?", "2"), ("2+2?", "4")]
    assert 0.0 < probe.mean_ce(model, pairs, batch=2) < 100.0
