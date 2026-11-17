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


# -- incremental caching -----------------------------------------------------
# The cache decides what is skipped, so the thing to test is the invalidation
# rule: every input that can change an arm's numbers has to change its key, and
# a prefix is only extendable when it can be continued without starting Adam
# from zero.


def _plan(probe, epochs=2, arm="warm", seed=0):
    import argparse

    return probe.arm_plan(
        "sha256:parent",
        arm,
        seed,
        {"train": "sha256:t", "val": "sha256:v", "holdout": "sha256:h"},
        probe._protocol(argparse.Namespace(batch=8, lr=1e-3), epochs),
        "sha256:impl",
    )


def test_the_plan_is_the_key(probe):
    import incremental

    assert probe.arm_plan is not None
    assert incremental.unit_key(_plan(probe)) == incremental.unit_key(_plan(probe))
    # Dict order is not information; content is.
    reordered = dict(reversed(list(_plan(probe).items())))
    assert incremental.unit_key(reordered) == incremental.unit_key(_plan(probe))


@pytest.mark.parametrize(
    "change",
    [
        {"arm": "cold"},
        {"arm": "width_control"},
        {"seed": 1},
        {"parent": "sha256:other-parent"},
        {"rows": {"train": "sha256:t", "val": "sha256:v", "holdout": "sha256:edited"}},
        {"impl": "sha256:edited-code"},
        {"epochs": 3},
        {"batch": 16},
        {"lr": 3e-4},
        {"factor": 2},
    ],
)
def test_every_input_that_can_change_the_numbers_changes_the_key(probe, change):
    import incremental

    plan = _plan(probe)
    edited = dict(plan)
    for field, value in change.items():
        if field in ("epochs", "batch", "lr", "factor"):
            edited["protocol"] = dict(plan["protocol"], **{field: value})
        else:
            edited[field] = value
    assert incremental.unit_key(edited) != incremental.unit_key(plan)


def _stored(cache, probe, tmp_path, epochs, with_optimizer=True):
    plan = _plan(probe, epochs)
    checkpoint = tmp_path / f"warm_0_{epochs}.pt"
    checkpoint.write_bytes(f"weights-{epochs}".encode())
    artifacts = [("checkpoint", checkpoint)]
    if with_optimizer:
        optimizer = tmp_path / f"warm_0_{epochs}_opt.pt"
        optimizer.write_bytes(f"adam-{epochs}".encode())
        artifacts.append(("opt_state", optimizer))
    cache.store(plan, {"epochs": epochs}, artifacts=artifacts)
    return plan


def test_prefix_unit_picks_the_longest_extendable_prefix(probe, tmp_path):
    from incremental import UnitCache

    cache = UnitCache(tmp_path / "cache", base=tmp_path)
    _stored(cache, probe, tmp_path, 1)
    _stored(cache, probe, tmp_path, 2)
    target = _plan(probe, epochs=3)
    found = probe.prefix_unit(cache, target)
    assert found is not None
    assert found["epochs"] == 2
    assert found["unit"].artifact("opt_state") is not None


def test_a_prefix_without_an_optimizer_state_cannot_be_extended(probe, tmp_path):
    from incremental import UnitCache

    cache = UnitCache(tmp_path / "cache", base=tmp_path)
    _stored(cache, probe, tmp_path, 2, with_optimizer=False)
    # It is still reusable as a result ...
    assert cache.lookup(_plan(probe, epochs=2)) is not None
    # ... but continuing it would restart Adam from zero, so it is not a prefix.
    assert probe.prefix_unit(cache, _plan(probe, epochs=3)) is None


def test_a_unit_at_or_beyond_the_target_is_not_a_prefix(probe, tmp_path):
    from incremental import UnitCache

    cache = UnitCache(tmp_path / "cache", base=tmp_path)
    _stored(cache, probe, tmp_path, 2)
    assert probe.prefix_unit(cache, _plan(probe, epochs=2)) is None
    assert probe.prefix_unit(cache, _plan(probe, epochs=1)) is None


def test_a_prefix_must_match_every_non_epoch_field(probe, tmp_path):
    from incremental import UnitCache

    cache = UnitCache(tmp_path / "cache", base=tmp_path)
    # A one-epoch cold unit exists; a warm run cannot resume from it even
    # though the epoch count is lower.
    plan = _plan(probe, epochs=1, arm="cold")
    checkpoint = tmp_path / "cold_0_1.pt"
    checkpoint.write_bytes(b"cold")
    optimizer = tmp_path / "cold_0_1_opt.pt"
    optimizer.write_bytes(b"adam")
    cache.store(
        plan, {"epochs": 1}, artifacts=[("checkpoint", checkpoint), ("opt_state", optimizer)]
    )
    assert probe.prefix_unit(cache, _plan(probe, epochs=2, arm="warm")) is None
    assert probe.prefix_unit(cache, _plan(probe, epochs=2, seed=1)) is None
    assert probe.prefix_unit(cache, _plan(probe, epochs=2, arm="cold"))["epochs"] == 1


def test_adoption_accepts_a_report_written_before_the_cache_existed(probe, tmp_path, monkeypatch):
    """A pre-cache report has no ``epochs`` per arm and no optimizer state.

    Adopting it must still work (the epoch count comes from the report's
    protocol), and the resulting unit must be reusable but not extendable.
    """
    import json

    from incremental import UnitCache

    checkpoint = tmp_path / "warm_0.pt"
    checkpoint.write_bytes(b"weights")
    report = {
        "stage": "probe_ladder85",
        "protocol": {"batch": 8, "lr": 1e-3, "epochs": 2},
        "arms": [
            {
                "arm": "warm",
                "seed": 0,
                "final_val_ce": 5.0,
                "holdout_hits": 28.0,
                "seconds": 120.0,
                "checkpoint": str(checkpoint),
            }
        ],
    }
    path = tmp_path / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    monkeypatch.setattr(
        probe, "TokenSNN", type("Fake", (), {"load": staticmethod(lambda *a, **k: None)})
    )
    monkeypatch.setattr(probe, "mean_ce", lambda model, pairs, batch=8: 5.0)
    monkeypatch.setattr(
        probe, "exact_count", lambda model, pairs: {"hits": 28.0, "n": 248.0, "rate": 0.113}
    )
    monkeypatch.setattr(probe, "_pairs", lambda parent: ([], [], []))
    monkeypatch.setattr(probe, "_sha256_file", lambda p: "sha256:parent")
    monkeypatch.setattr(probe, "impl_digest", lambda files: "sha256:impl")

    cache_dir = tmp_path / "cache"
    args = probe.argparse.Namespace(cache=str(cache_dir), batch=8, lr=1e-3)
    outcome = probe.adopt(path, args)
    assert outcome["refused"] == []
    assert outcome["adopted"] == ["warm/seed0"]

    cache = UnitCache(cache_dir, base=probe.REPO_ROOT)
    keys = cache.keys()
    assert len(keys) == 1
    unit = cache.load(keys[0])
    assert unit is not None
    assert unit.plan["protocol"]["epochs"] == 2
    assert unit.artifact("opt_state") is None
    assert (
        probe.prefix_unit(
            cache,
            dict(
                unit.plan,
                protocol={
                    "batch": 8,
                    "lr": 1e-3,
                    "epochs": 3,
                    "factor": 4,
                    "noise": 1e-3,
                    "tail_weight": 1.0,
                    "ss_final": 0.0,
                    "guard": True,
                    "optimizer": "adam",
                    "clip_grad_norm": 1.0,
                },
            ),
        )
        is None
    )


def test_arm_selection_refuses_a_typo(probe):
    assert probe.parse_arms("warm, cold") == ["warm", "cold"]
    with pytest.raises(ValueError):
        probe.parse_arms("warm,wram")
    with pytest.raises(ValueError):
        probe.parse_arms(" , ")


def test_the_nested_holdout_is_not_a_leak(probe):
    # §85.2: the hold-out set (248 rows) is inside val (281); only the training
    # corpus touching an evaluation set is a leak.
    clean = {"train_and_val": 0, "train_and_holdout": 0, "val_and_holdout": 248}
    assert probe.overlap_problem(clean, 248) is None
    leaky = dict(clean, train_and_val=3)
    assert "train/val" in probe.overlap_problem(leaky, 248)
    leaky = dict(clean, train_and_holdout=1)
    assert "train/hold-out" in probe.overlap_problem(leaky, 248)
    leaky = dict(clean, val_and_holdout=240)
    assert "not a subset" in probe.overlap_problem(leaky, 248)


def test_a_relative_or_external_out_dir_still_resolves(probe, tmp_path):
    # A relative --out-dir used to crash at relative_to(); the report must be
    # able to name a checkpoint outside the repo as well.
    assert probe.display_path(probe.REPO_ROOT / "data" / "x.pt") == "data/x.pt"
    assert probe.display_path(tmp_path / "x.pt") == str(tmp_path / "x.pt")
    assert probe.resolve_artifact("data/x.pt") == probe.REPO_ROOT / "data" / "x.pt"
    assert probe.resolve_artifact(str(tmp_path / "x.pt")) == tmp_path / "x.pt"
