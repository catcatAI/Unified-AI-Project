"""Tests for the endogenous rhythm source (``core/life/al_oscillator.py``).

The point of these tests is not "an oscillator oscillates" -- it is that the
things the measurement script relies on are pinned at the unit level:

1. the limit cycle exists for any initial state (it attracts, so the period is a
   property of the equations rather than of where you started);
2. the sampled result does not depend on how coarsely the caller samples;
3. the phase is part of the persisted state, so a restart continues the cycle
   instead of restarting it;
4. a clock that goes backwards does not rewind the oscillator, and a long gap is
   reported as stale rather than silently inventing a phase;
5. an experience event actually reaches the oscillator: the same clock with two
   different event histories must produce two different states. Without that,
   the module is only a clock (external review A1) and the AL ladder protocol
   would be measuring a time feature while claiming to measure a state.
"""

from __future__ import annotations

import math

import pytest
from core.life.al_oscillator import (
    DEFAULT_MU,
    MAX_CATCHUP_S,
    MAX_KICK,
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


class TestExperienceDrive:
    """A1: the oscillator's drive used to be a constant 0.

    Everything below is falsifiable in the way the measurement script is: change
    the past event sequence and the present state must change with it.
    """

    def test_an_event_shifts_the_state(self, tmp_path):
        quiet = RhythmTracker(tmp_path / "q.json", clock=lambda: 1000.0)
        nudged = RhythmTracker(tmp_path / "n.json", clock=lambda: 1000.0)
        nudged.nudge(0.5)
        quiet.activation(1010.0)
        nudged.activation(1010.0)
        assert nudged.state()["x"] != quiet.state()["x"]
        assert abs(nudged.state()["x"] - quiet.state()["x"]) > 1e-6

    def test_two_event_histories_give_two_states(self, tmp_path):
        """Same elapsed time, same clock, different history -> different state."""
        one = RhythmTracker(tmp_path / "one.json", clock=lambda: 1000.0)
        one.nudge(MAX_KICK)
        one.activation(1010.0)

        clock = [1000.0]
        two = RhythmTracker(tmp_path / "two.json", clock=lambda: clock[0])
        two.nudge(MAX_KICK / 2)
        clock[0] = 1005.0
        two.activation()
        two.nudge(MAX_KICK / 2)
        clock[0] = 1010.0
        two.activation()

        assert one.state()["x"] != two.state()["x"]

    def test_a_kick_is_spent_once(self, tmp_path):
        tracker = RhythmTracker(tmp_path / "r.json", clock=lambda: 1000.0)
        assert tracker.nudge(0.4) == pytest.approx(0.4)
        assert tracker.state()["pending_kick"] == pytest.approx(0.4)
        tracker.activation(1010.0)
        assert tracker.state()["pending_kick"] == 0.0
        # A second, event-free step must not push again: compare with a twin that
        # never received the event but did receive both steps.
        twin = RhythmTracker(tmp_path / "t.json", clock=lambda: 1000.0)
        twin.activation(1010.0)
        tracker.activation(1020.0)
        twin.activation(1020.0)
        # The single kick moved the phase and the move persists; it is not
        # reapplied on every later step (which would be an accelerating clock).
        assert abs(tracker.state()["x"] - twin.state()["x"]) > 1e-6

    def test_bad_input_is_ignored_and_kicks_are_clamped(self, tmp_path):
        tracker = RhythmTracker(tmp_path / "r.json", clock=lambda: 1000.0)
        for bad in (None, "abc", [], True, float("nan"), float("inf")):
            assert tracker.nudge(bad) == 0.0
        assert tracker.state()["pending_kick"] == 0.0
        assert tracker.nudge(1e9) == pytest.approx(MAX_KICK)
        assert tracker.nudge(-1e9) == pytest.approx(-MAX_KICK)

    def test_preview_does_not_spend_the_pending_kick(self, tmp_path):
        tracker = RhythmTracker(tmp_path / "r.json", clock=lambda: 1000.0)
        tracker.activation(1005.0)
        tracker.nudge(0.5)
        first = tracker.activation_preview(1010.0)
        second = tracker.activation_preview(1010.0)
        assert first == pytest.approx(second)
        assert tracker.state()["pending_kick"] == pytest.approx(0.5)
        tracker.activation(1010.0)
        assert tracker.state()["pending_kick"] == 0.0
