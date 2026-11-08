"""Tests for the AL clock guard (core/life/al_clock_guard.py).

What is pinned here is the *discrimination*, not the plumbing:

1. honest clocks (wall and monotonic advancing together) never raise suspicion,
   including the ordinary drift of a system clock;
2. a backward jump and a forward jump are both caught, and the reported
   disagreement points the right way;
3. a guard that is fed one attack does not treat everything after it as suspect;
4. the first sample is a baseline, not a verdict — with nothing to compare, an
   "ok" is the only honest answer;
5. the boundary is explicit: forging *both* sources is undetectable, because
   there is no third reference. That is the system boundary, not a bug.
"""

from __future__ import annotations

import pytest
from core.life.al_clock_guard import ClockGuard


def _run(guard: ClockGuard, pairs):
    return [guard.sample(now=now, monotonic=mono) for now, mono in pairs]


def test_honest_clocks_never_raise_suspicion():
    guard = ClockGuard()
    verdicts = _run(guard, [(1000.0 + i, 500.0 + i) for i in range(50)])
    assert not any(v.suspicion for v in verdicts)
    assert verdicts[0].reason == "baseline"
    assert guard.drift == pytest.approx(1.0, abs=1e-9)
    assert guard.samples == 50


def test_slow_drift_is_tolerated_but_a_jump_is_not():
    guard = ClockGuard()
    # 2% slow wall clock: normal, must not be flagged.
    pairs = [(1000.0 + 0.98 * i, 500.0 + i) for i in range(30)]
    assert not any(v.suspicion for v in _run(guard, pairs))

    # ...then a week forward in one read: flagged.
    verdict = guard.sample(now=1000.0 + 0.98 * 29 + 7 * 86400, monotonic=500.0 + 30)
    assert verdict.suspicion
    assert verdict.disagreement is not None and verdict.disagreement > 0


def test_backward_jump_is_caught_and_reported_as_negative():
    guard = ClockGuard()
    _run(guard, [(1000.0 + i, 500.0 + i) for i in range(5)])
    verdict = guard.sample(now=1000.0 - 1_000_000.0, monotonic=500.0 + 5)
    assert verdict.suspicion
    assert verdict.disagreement is not None and verdict.disagreement < 0
    assert "backwards" in verdict.reason


def test_one_attack_does_not_poison_later_samples():
    """The baseline advances even on a suspicious reading, and the drift
    estimate is not updated from it."""
    guard = ClockGuard()
    _run(guard, [(1000.0 + i, 500.0 + i) for i in range(5)])
    guard.sample(now=1000.0 + 1e6, monotonic=500.0 + 5)  # attack
    after = guard.sample(now=1000.0 + 1e6 + 1.0, monotonic=500.0 + 6)  # honest again
    assert not after.suspicion
    assert guard.drift == pytest.approx(1.0, abs=0.01)


def test_first_sample_is_a_baseline_not_a_verdict():
    guard = ClockGuard()
    first = guard.sample(now=1e9, monotonic=10.0)
    assert first.ok and not first.suspicion
    assert first.observed is None and first.expected is None


def test_forging_both_sources_is_out_of_scope():
    """No third reference exists: if monotonic is forged too, nothing can tell."""
    guard = ClockGuard()
    _run(guard, [(1000.0 + i, 500.0 + i) for i in range(5)])
    verdict = guard.sample(now=1000.0 + 5 + 1e6, monotonic=500.0 + 5 + 1e6)
    assert not verdict.suspicion


def test_non_finite_readings_are_suspicious():
    guard = ClockGuard()
    _run(guard, [(1000.0, 500.0)])
    verdict = guard.sample(now=float("nan"), monotonic=501.0)
    assert verdict.suspicion
    assert "non-finite" in verdict.reason
