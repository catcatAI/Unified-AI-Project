"""Tests for the power-cycle continuity probe (scripts/al_power_cycle.py).

r6 restarts a tracker inside one interpreter; this one restarts the interpreter.
What is pinned:

1. a fresh process continues from the persisted state by the elapsed wall-clock
   time, to float precision;
2. the two forgeries are visibly wrong in the same units — "hold the last value"
   and "reset to baseline" both miss by ~1e-1 after a short gap, so the rung is
   not passing by tolerance;
3. the measurement's gap comes from the persisted timestamp, so interpreter
   start-up time is not silently charged to the code (an earlier version did
   exactly that and reported a 3e-3 error that was really import time).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_power_cycle.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def power_cycle():
    return _load("al_power_cycle_test", SCRIPT)


def test_a_new_process_continues_from_the_elapsed_time(power_cycle, tmp_path):
    result = power_cycle.run(0.4, path=tmp_path / "affect.json")
    assert result["passed"], result
    assert result["error"] < 1e-5
    # The gap is measured from the persisted timestamp, so it is at least the sleep.
    assert result["gap_seconds"] >= 0.4


def test_the_forgeries_are_wrong_by_a_visible_margin(power_cycle, tmp_path):
    result = power_cycle.run(0.4, path=tmp_path / "affect2.json")
    assert result["forgery_hold_error"] > 1e-2
    assert result["forgery_reset_error"] > 1e-2


def test_the_state_file_carries_a_timestamp(power_cycle, tmp_path):
    result = power_cycle.run(0.3, path=tmp_path / "affect3.json")
    assert set(result["stored"]) >= {"arousal", "target", "at"}
