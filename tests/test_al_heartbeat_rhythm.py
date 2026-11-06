"""Tests for the heartbeat rhythm probe (scripts/al_heartbeat_rhythm.py).

The finding it encodes is structural, so the tests are about the structure:

1. the beat interval is a pure function of (stress, arousal) — no state, no
   history, so identical inputs give identical intervals in any order;
2. constant inputs produce a perfectly flat series (CV = 0): the heartbeat does
   not generate a rhythm by itself;
3. a sinusoidal arousal produces variation that is a filtered copy (high lag-1
   autocorrelation), which is why any rhythm claim must name its source;
4. the interval stays inside the configured 5–60 s band for the inputs used.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "al_heartbeat_rhythm.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def rhythm():
    return _load("al_heartbeat_rhythm_test", SCRIPT)


def test_beat_interval_is_a_memoryless_function(rhythm):
    a, b = rhythm.dynamic_interval(0.5, 40.0), rhythm.dynamic_interval(0.5, 40.0)
    assert a == b
    # Same value requested twice from different "histories" is not representable
    # here on purpose: the function has no history parameter. Its signature is the
    # statement that there is nothing to remember.
    import inspect

    assert "history" not in inspect.signature(rhythm.dynamic_interval).parameters


def test_constant_inputs_produce_no_rhythm(rhythm):
    result = rhythm.run(n=120)
    assert result["statistics"]["constant"]["cv"] == 0.0
    assert result["verdict"] == "rhythm-inherited-from-input"


def test_a_sine_input_is_inherited_not_generated(rhythm):
    stats = rhythm.run(n=120)["statistics"]
    assert stats["inherited_sine"]["cv"] > 0.05
    assert stats["inherited_sine"]["lag1"] > 0.9
    assert stats["history_independent"] is True


def test_intervals_stay_in_band(rhythm):
    result = rhythm.run(n=60)
    assert result["within_bounds"] is True
    lo, hi = result["statistics"]["inherited_sine"]["interval_range"]
    assert 5.0 <= lo <= hi <= 60.0
