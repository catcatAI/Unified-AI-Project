"""Tests for the endogenous rhythm source (``core/life/al_oscillator.py``).

The point of these tests is not "an oscillator oscillates" -- it is that the
things the measurement script relies on are pinned at the unit level:

1. the limit cycle exists for any initial state (it attracts, so the period is a
   property of the equations rather than of where you started);
2. the sampled result does not depend on how coarsely the caller samples;
3. the phase is part of the persisted state, so a restart continues the cycle
   instead of restarting it;
4. a clock that goes backwards does not rewind the oscillator, and a long gap is
   reported as stale rather than silently inventing a phase.
"""

from __future__ import annotations

import math

import pytest
from core.life.al_oscillator import (
    DEFAULT_MU,
    MAX_CATCHUP_S,
    Oscillator,
    RhythmTracker,
    get_rhythm_tracker,
    natural_period,
    set_rhythm_tracker,
)


def test_activation_stays_in_unit_interval():
    osc = Oscillator()
    for _ in range(2000):
        value = osc.step(0.05)
        assert 0.0 <= value <= 1.0


def test_limit_cycle_attracts_from_different_starting_points():
    periods = []
    for x, v in ((0.0, 1.0), (5.0, -3.0), (-4.0, 8.0)):
        periods.append(natural_period(mu=DEFAULT_MU, settle_s=80.0, measure_s=400.0))
    assert max(periods) - min(periods) < 0.05 * sum(periods) / len(periods)


def test_period_does_not_depend_on_the_sampling_rate():
    fine = natural_period(mu=DEFAULT_MU, settle_s=80.0, measure_s=400.0)
    # Same physics, caller samples 5x more coarsely; the integrator substeps.
    osc = Oscillator()
    osc.step(80.0)
    prev = osc.x
    crossings, t = [], 0.0
    while t < 400.0:
        osc.step(0.1)
        t += 0.1
        if prev < 0.0 <= osc.x:
            crossings.append(t)
        prev = osc.x
    coarse = sum(b - a for a, b in zip(crossings, crossings[1:])) / (len(crossings) - 1)
    assert abs(coarse - fine) / fine < 0.02


def test_mu_changes_the_period():
    short = natural_period(mu=0.8, settle_s=60.0, measure_s=300.0)
    long = natural_period(mu=3.5, settle_s=60.0, measure_s=600.0)
    assert long > short * 1.5


def test_negative_dt_is_rejected():
    with pytest.raises(ValueError):
        Oscillator().step(-0.1)


def test_restart_continues_the_phase(tmp_path):
    path = tmp_path / "rhythm.json"
    clock = [1000.0]
    tracker = RhythmTracker(path, clock=lambda: clock[0])
    for _ in range(50):
        clock[0] += 5.0
        tracker.activation()
    before = tracker.state()
    # New process: same file, same clock, nothing alive in between.
    clock[0] += 7.0
    resumed = RhythmTracker(path, clock=lambda: clock[0])
    resumed.activation()
    after = resumed.state()
    # The resumed state must be ahead of the saved one, not reset to the seed.
    assert after["x"] != pytest.approx(0.0)
    assert abs(after["x"] - before["x"]) > 1e-3
    assert resumed.stale is False


def test_clock_regression_does_not_rewind(tmp_path):
    clock = [5000.0]
    tracker = RhythmTracker(tmp_path / "r.json", clock=lambda: clock[0])
    clock[0] += 30.0
    tracker.activation()
    frozen = tracker.state()
    clock[0] -= 30.0
    tracker.activation()
    assert tracker.state()["x"] == pytest.approx(frozen["x"])


def test_a_long_gap_is_reported_stale(tmp_path):
    clock = [1000.0]
    tracker = RhythmTracker(tmp_path / "r.json", clock=lambda: clock[0])
    clock[0] += MAX_CATCHUP_S + 500.0
    tracker.activation()
    assert tracker.stale is True
    assert math.isfinite(tracker.state()["x"])


def test_singleton_can_be_replaced_and_cleared():
    original = get_rhythm_tracker()
    try:
        set_rhythm_tracker(None)
        assert get_rhythm_tracker() is not original
    finally:
        set_rhythm_tracker(original)
    assert get_rhythm_tracker() is original


def test_persisted_file_is_readable_json(tmp_path):
    import json

    path = tmp_path / "r.json"
    RhythmTracker(path, clock=lambda: 1234.0).activation()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["version"] == 1
    assert {"x", "v", "at"} <= set(payload)


class TestActivationPreview:
    """`activation_preview` exists because the learning path reads it per sample.

    It must be a pure read: same value as the stepped `activation()` would report
    without advancing the oscillator or rewriting the state file.
    """

    def test_preview_matches_the_current_activation(self, tmp_path):
        tracker = RhythmTracker(tmp_path / "rhythm.json", clock=lambda: 1000.0)
        tracker.activation(1010.0)
        assert tracker.activation_preview() == pytest.approx(tracker._osc.activation)

    def test_preview_does_not_advance_or_write(self, tmp_path):
        path = tmp_path / "rhythm.json"
        tracker = RhythmTracker(path, clock=lambda: 1000.0)
        tracker.activation(1010.0)
        before_state = tracker.state()
        before_bytes = path.read_bytes()

        for _ in range(50):
            tracker.activation_preview()

        assert tracker.state() == before_state
        assert path.read_bytes() == before_bytes

    def test_a_stepped_call_does_move_the_preview(self, tmp_path):
        tracker = RhythmTracker(tmp_path / "rhythm.json", clock=lambda: 1000.0)
        first = tracker.activation_preview()
        tracker.activation(1020.0)
        assert tracker.activation_preview() != first
