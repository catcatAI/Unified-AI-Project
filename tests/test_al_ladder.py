"""Tests for the AL time-ladder probe (scripts/al_ladder.py).

The probe is a measuring instrument, so the thing worth pinning is that it
*can* fail and that its verdicts say so:

1. the production rule is exact on elapsed-time questions and the trained
   baseline is not — the instrument separates them;
2. a constant predictor passes the attractor rung, so a rung that the control
   also passes is reported as ``sound-not-evidence`` rather than as a win;
3. the rungs that a "do nothing" function also passes (reslicing time, changing
   the sampling rate) are labelled that way, not counted as evidence;
4. the clock-attack rung reports no suspicion, because there is no clock
   estimate to be suspicious with — ``None`` must not become a pass;
5. the MLP really is out-of-distribution on the outer dt range; if it were not,
   r5 would be measuring nothing.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_ladder.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ladder():
    return _load("al_ladder_test", SCRIPT)


def test_al_is_exact_where_the_mlp_extrapolates_badly(ladder):
    """r5 is the rung that separates designed dynamics from learned ones."""
    al = ladder.ALModel()
    mlp = ladder.MLPModel(steps=400)
    import numpy as np

    rng = np.random.default_rng(3)
    al_err = ladder._dt_sweep(al, *ladder.OUTER_DT, rng)
    mlp_err = ladder._dt_sweep(mlp, *ladder.OUTER_DT, np.random.default_rng(3))
    assert al_err == 0.0
    assert mlp_err > 10 * max(al_err, 1e-12)
    assert mlp_err > ladder.SENSITIVE


def test_a_constant_predictor_is_visible_on_the_attractor_rung(ladder):
    """Endpoint-only scoring let a constant pass; scoring the curve does not."""
    const = ladder.ConstModel()
    err = ladder.rung_attractor([const], None)["const"]
    assert err > ladder.SENSITIVE


def test_control_passing_is_reported_as_sound_not_evidence(ladder):
    assert ladder._verdict(1e-16, 0.32, control=0.0) == "sound-not-evidence"
    assert ladder._verdict(0.0, 0.14, control=0.27) == "al-wins"
    # A rung where nothing misses by more than float noise is not sensitive.
    assert ladder._verdict(0.5, 1e-6, control=0.9) == "not-sensitive"
    # 0.025 is not "close" on an exactness rung: a constant guessing the
    # baseline must not be able to count as a pass by tolerance.
    assert ladder._verdict(0.0, 0.025, control=0.37) == "al-wins"


def test_clock_attack_is_detected_without_false_alarms(ladder, tmp_path):
    """r7 became scoreable when the monotonic reference arrived.

    A guard that flags everything would pass detection and fail the false-alarm
    column, so both have to hold.
    """
    out = ladder.rung_clock_attack(tmp_path)
    assert out["detect_backward"] == 1.0
    assert out["detect_forward"] == 1.0
    assert out["false_alarm"] == 0.0
    # The value is still held on a rollback (that is a separate decision), but
    # now the hold is reported instead of silent.
    assert out["rollback_freeze"] == pytest.approx(0.0, abs=1e-12)


def test_restart_uses_the_elapsed_time(ladder, tmp_path):
    """The forgery keeps the last number and is wrong by the whole decay."""
    out = ladder.rung_restart(None, tmp_path)
    assert out["al"] == pytest.approx(0.0, abs=1e-12)
    assert out["copy"] > ladder.SENSITIVE
