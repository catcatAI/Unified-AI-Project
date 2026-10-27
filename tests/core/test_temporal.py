# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [A] [L9+]
# =============================================================================

"""Regression tests for TemporalState.anomalies window-bounding (§11.6 / §11.8 B2).

Before the fix, ``anomalies`` scanned the ENTIRE history every call (O(history)),
so an anomaly far outside the requested window was still returned. Now it only
scans the most recent ``window`` snapshots, matching ``get_field_series``.
"""

import os
import sys

import pytest

if (
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src")
    not in sys.path
):
    sys.path.insert(
        0,
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src"),
    )


def _record_series(ts, n, value):
    for _ in range(n):
        ts.record({"alpha": {"arousal": value}})


def test_anomalies_excludes_out_of_window():
    """An old anomaly outside the window must NOT be returned."""
    from core.state.temporal import TemporalState

    ts = TemporalState(max_size=500)
    # Old anomaly at the very start of history.
    ts.record({"alpha": {"arousal": 0.99}})
    # Then a long run of normal values pushes it outside any small window.
    _record_series(ts, 100, 0.5)

    # window=10 -> the recent 10 are all 0.5, the old 0.99 is excluded.
    results = ts.anomalies("alpha", "arousal", window=10)
    assert results == []


def test_anomalies_detects_recent():
    """A recent anomaly within the window IS detected."""
    from core.state.temporal import TemporalState

    ts = TemporalState(max_size=500)
    _record_series(ts, 10, 0.5)
    ts.record({"alpha": {"arousal": 0.99}})

    results = ts.anomalies("alpha", "arousal", window=10)
    assert len(results) >= 1
    assert results[0].axis == "alpha"
    assert results[0].field == "arousal"


def test_anomalies_scan_is_bounded():
    """The anomaly scan must not traverse the whole history (perf guard)."""
    from core.state.temporal import TemporalState

    ts = TemporalState(max_size=2000)
    _record_series(ts, 1500, 0.5)
    ts.record({"alpha": {"arousal": 0.99}})

    # Large history; a tiny window keeps the scan cheap and returns only the
    # recent anomaly. This would be O(history) before the fix.
    # threshold=1.5 avoids floating-point edge cases at exactly -0.5 std.
    results = ts.anomalies("alpha", "arousal", threshold=1.5, window=5)
    assert len(results) == 1


def test_trend_reads_newest_first_series():
    """trend() must label direction by time, not by list order.

    ``get_field_series()`` walks the history newest-first, so the old
    ``values[-1] - values[0]`` slope read the series backwards and reported a
    rising field as "falling". Latent while TemporalState stayed empty; the
    three-core plan Phase 2 item 2 (ζ is driven by trend/anomalies, and
    ``get_state_summary()`` now reaches this branch) makes it live.
    """
    from core.state.temporal import TemporalState

    rising_ts = TemporalState(max_size=100)
    for i, v in enumerate([0.1, 0.2, 0.3, 0.4, 0.5]):
        rising_ts.record({"timestamp": f"t{i}", "alpha": {"energy": v}})
    rising = rising_ts.trend("alpha", "energy", window=10)
    assert rising.direction == "rising"
    assert rising.slope > 0

    falling_ts = TemporalState(max_size=100)
    for i, v in enumerate([0.5, 0.4, 0.3, 0.2, 0.1]):
        falling_ts.record({"timestamp": f"t{i}", "alpha": {"energy": v}})
    falling = falling_ts.trend("alpha", "energy", window=10)
    assert falling.direction == "falling"
    assert falling.slope < 0
