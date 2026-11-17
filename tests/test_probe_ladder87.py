# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§87's one job is to make ``I0``'s tolerances derived, so that is the unit.

No training happens here. What is tested:

* the decision margins are §86's, unchanged (0.15 nats / 9 items), and the
  branch table still reads §85's observed pattern as ``N4``;
* ``I0-7``'s tolerance is **1e-4**, above the widening noise scale and four
  orders of magnitude above the bound it replaces — and a delta that §86 would
  have failed (7.8e-6) now passes, which is the whole point of re-registering;
* a delta *above* the tolerance still fails, so the item is a gate and not a
  decoration;
* the defaults are the registered ones (seeds 6/7/8, stage ``probe_ladder87``),
  and the unit key covers both earlier probes.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_ladder87.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_ladder87_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_ladder87_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


def row(arm, seed, final, hits, holdout_ce=4.0, train_start=0.70, train_end=0.60):
    return {
        "arm": arm,
        "seed": seed,
        "val_ce": final,
        "holdout_ce": holdout_ce,
        "holdout_hits": hits,
        "holdout_n": 248.0,
        "train_ce_full_start": train_start,
        "train_ce_full_end": train_end,
        "ms_per_row": 30.0,
        "seconds": 300.0,
        "params": 12_069_723.0,
    }


def arms(warm_final, warm_hits, control_final=4.63, control_hits=24.67):
    rows = []
    for seed in (6, 7, 8):
        rows.append(row("warm", seed, warm_final, warm_hits))
        rows.append(row("width_control", seed, control_final, control_hits))
        rows.append(row("cold", seed, 2.58, 1.67, holdout_ce=6.0))
    return rows


def identity_point(seed, delta_val, delta_train, tolerance, passes=None):
    if passes is None:
        passes = delta_val <= tolerance and delta_train <= tolerance
    return {
        "seed": seed,
        "init_checkpoint": f"data/ladder87/warm_init_{seed}.pt",
        "parent_val_ce": 5.6964,
        "child_val_ce": 5.6964 + delta_val,
        "parent_train_ce_full": 0.7039,
        "child_train_ce_full": 0.7039 + delta_train,
        "delta_val_ce": delta_val,
        "delta_train_ce_full": delta_train,
        "passes_val_ce": delta_val <= tolerance,
        "passes_train_ce_full": delta_train <= tolerance,
    }


def protocol(probe, train_rows=5144, batch=8, epochs=2):
    steps = int(math.ceil(train_rows / batch) * epochs)
    return {
        "rows": {"train": train_rows, "val": 281, "holdout": 248},
        "batch": batch,
        "epochs": epochs,
        "optimizer_steps_per_arm": steps,
    }


def i0(probe, identity, overlap=None, orders=None, steps=None, proto=None, unchanged=True):
    proto = proto or protocol(probe)
    overlap = overlap or {"train_and_val": 0, "train_and_holdout": 0, "val_and_holdout": 248}
    orders = orders or {"6": "a", "7": "b", "8": "c"}
    steps = proto["optimizer_steps_per_arm"] if steps is None else steps
    return probe._i0_block(identity, overlap, orders, steps, proto, unchanged)


# -- the registered instrument ----------------------------------------------


def test_the_decision_margins_are_unchanged(probe):
    # 87.3: the margins look loose against §86's spreads, and stay put anyway.
    assert probe.MARGIN_CE == 0.15
    assert probe.MARGIN_ITEMS == 9.0
    assert probe.MARGINS == {"ce_nats": 0.15, "holdout_items": 9.0}


def test_the_defaults_are_the_registered_ones(probe):
    args = probe.build_parser().parse_args([])
    assert args.seeds == "6,7,8"
    assert args.epochs == 2
    assert args.batch == 8
    assert args.lr == 1e-3


def test_the_i0_7_tolerance_is_derived_not_guessed(probe):
    # 87.2: noise 1e-3 -> step-0 CE deltas around 1e-5 -> §85.2's 1e-4.
    assert probe.IDENTITY_TOLERANCE == 1e-4
    assert probe.TOLERANCES == {"identity_val_ce": 1e-4, "identity_train_ce_full": 1e-4}
    # Above the observed scale of the perturbation ...
    assert probe.IDENTITY_TOLERANCE >= 1e-5
    # ... and four orders of magnitude above the §86 bound it replaces.
    assert probe.IDENTITY_TOLERANCE == pytest.approx(1e-6 * 100)


def test_the_plan_covers_both_earlier_probes_and_this_one(probe):
    names = {Path(p).name for p in probe.IMPL_FILES}
    assert "probe_ladder87.py" in names  # its own I0 logic is code too
    assert "probe_ladder86.py" in names  # the rulers
    assert "probe_ladder85.py" in names  # the arms
    assert "token_snn.py" in names


def test_the_branch_table_is_still_section_86s(probe):
    # §86 measured CE +1.02 and items -9.33: both rulers resolve, opposite ways.
    decision = probe.p86.decide(
        arms(warm_final=3.6641, warm_hits=17.0, control_final=4.6317, control_hits=26.0)
    )
    assert decision["branch"] == "N4-inconsistent"
    assert decision["ce_ruler"]["state"] == "warm-better"
    assert decision["item_ruler"]["state"] == "warm-worse"


# -- I0: the item that voided §86 -------------------------------------------


def test_the_86_failure_now_passes_under_the_derived_tolerance(probe):
    # §86 measured 7.84e-06 / 5.30e-06 / 4.52e-06 against a registered 1e-6.
    points = [
        identity_point(3, 9.055e-05, 7.843e-06, probe.IDENTITY_TOLERANCE),
        identity_point(4, 7.625e-05, 5.295e-06, probe.IDENTITY_TOLERANCE),
        identity_point(5, 1.688e-05, 4.517e-06, probe.IDENTITY_TOLERANCE),
    ]
    block = i0(probe, points)
    item = {entry["id"]: entry for entry in block["items"]}["I0-7"]
    assert item["passes"] is True
    assert item["tolerance"] == probe.TOLERANCES
    assert block["all_pass"] is True


def test_a_delta_above_the_tolerance_still_fails(probe):
    # The gate must not be decorative: 3e-4 is above 1e-4 and must void it.
    points = [identity_point(6, 9e-05, 3e-04, probe.IDENTITY_TOLERANCE, passes=False)]
    block = i0(probe, points)
    item = {entry["id"]: entry for entry in block["items"]}["I0-7"]
    assert item["passes"] is False
    assert block["all_pass"] is False


def test_a_val_ce_identity_failure_is_also_caught(probe):
    points = [identity_point(6, 2e-04, 1e-06, probe.IDENTITY_TOLERANCE, passes=False)]
    block = i0(probe, points)
    assert {entry["id"]: entry for entry in block["items"]}["I0-1"]["passes"] is False


def test_i0_2_catches_a_leak_and_a_short_holdout(probe):
    points = [identity_point(6, 9e-05, 7e-06, probe.IDENTITY_TOLERANCE)]
    leaked = i0(
        probe, points, overlap={"train_and_val": 3, "train_and_holdout": 0, "val_and_holdout": 248}
    )
    assert leaked["all_pass"] is False
    short = i0(
        probe, points, overlap={"train_and_val": 0, "train_and_holdout": 0, "val_and_holdout": 247}
    )
    assert short["all_pass"] is False


def test_i0_4_catches_a_budget_mismatch(probe):
    points = [identity_point(6, 9e-05, 7e-06, probe.IDENTITY_TOLERANCE)]
    block = i0(probe, points, steps=1285)
    item = {entry["id"]: entry for entry in block["items"]}["I0-4"]
    assert item["passes"] is False
    assert item["tolerance"] == 1286


def test_i0_5_catches_a_moved_parent(probe):
    points = [identity_point(6, 9e-05, 7e-06, probe.IDENTITY_TOLERANCE)]
    block = i0(probe, points, unchanged=False)
    assert block["all_pass"] is False


# -- the report is a claim until checked -------------------------------------


def test_check_refuses_a_report_from_another_stage(probe, tmp_path):
    path = tmp_path / "report.json"
    path.write_text('{"stage": "probe_ladder86"}', encoding="utf-8")
    ok, message = probe.check(path)
    assert ok is False
    assert "probe_ladder87" in message


def test_check_refuses_a_report_with_no_arms(probe, tmp_path):
    path = tmp_path / "report.json"
    path.write_text(
        '{"stage": "probe_ladder87", "protocol": {"parent_sha256": "x"}, '
        '"instrument": {}, "arms": []}',
        encoding="utf-8",
    )
    ok, _message = probe.check(path)
    assert ok is False
