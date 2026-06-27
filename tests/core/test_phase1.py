"""
Phase 1 Refactor Smoke Tests
============================

Verifies:
1. AxisField and AxisFieldRegistry work
2. Axis typed access works
3. TemporalState query engine works
4. Integration: Axis uses TemporalState

Author: Angela AI v6.2
Version: 6.2.1
"""

import math

from core.state.axis import Axis
from core.state.axis_field import AxisField, AxisFieldRegistry
from core.state.temporal import SnapshotQuery, TemporalState


def test_axis_field_registry():
    print("=== AxisFieldRegistry ===")
    reg = AxisFieldRegistry()

    alpha_fields = reg.fields_for('alpha')
    print(f"Alpha fields: {len(alpha_fields)}")

    theta_fields = reg.fields_for('theta')
    print(f"Theta fields: {len(theta_fields)}")

    energy = reg.get('alpha', 'energy')
    print(f"Energy field: {energy}")

    assert energy is not None
    assert energy.axis == 'alpha'
    assert energy.name == 'energy'
    assert energy.in_range(0.5) is True
    assert energy.in_range(-0.1) is False

    novelty = reg.get('theta', 'novelty')
    assert novelty is not None

    print(f"All axes: {reg.all_axes()}")
    print(f"Total fields: {reg.count()}")
    print("Registry: PASS\n")


def test_axis_typed_access():
    print("=== Axis Typed Access ===")
    alpha = Axis.create_alpha()

    print(f"Alpha fields: {alpha.field_names()}")
    print(f"Alpha average: {alpha.average():.3f}")
    dom = alpha.dominant()
    print(f"Alpha dominant: {dom[0]}({dom[1]:.3f})")

    assert alpha.field_count() > 0

    reg = AxisFieldRegistry()
    energy_field = reg.get('alpha', 'energy')
    alpha.set(energy_field, 0.8)
    val = alpha.get(energy_field)
    assert abs(val - 0.8) < 0.001

    print(f"Energy via typed access: {val:.3f}")

    alpha.update(focus=0.9, energy=0.6)
    print(f"After update - focus: {alpha.get_str('focus'):.3f}, energy: {alpha.get_str('energy'):.3f}")

    print(f"Coordinate: {alpha.coordinate}")
    alpha.shift(dx=0.1, dy=-0.2, dz=0.0)
    print(f"After shift: {alpha.coordinate}")

    print(f"Distance to beta: {alpha.distance_to(Axis.create_beta()):.3f}")

    snapshot = alpha.snapshot()
    print(f"Snapshot keys: {list(snapshot.keys())[:5]}")

    print("Axis: PASS\n")


def test_axis_from_config():
    print("=== Axis Factory ===")
    alpha = Axis.create_alpha(weight=0.8)
    beta = Axis.create_beta(weight=1.2)
    theta = Axis.create_theta()

    print(f"Alpha: {alpha}, weight={alpha.weight}")
    print(f"Beta: {beta}, weight={beta.weight}")
    print(f"Theta: {theta}, weight={theta.weight}")

    print("Factory: PASS\n")


def test_temporal_state():
    print("=== TemporalState ===")
    timeline = TemporalState(max_size=100)

    for i in range(20):
        timeline.record({
            'timestamp': f'2026-05-13T{10+i//60:02d}:{i%60:02d}:00',
            'beta': {'focus': 0.5 + i * 0.02},
            'alpha': {'energy': 0.7},
        })

    print(f"Timeline size: {timeline.size()}")

    recent = timeline.recent(fraction=0.3)
    print(f"Recent 30%: {len(recent)} snapshots")

    focus_field = AxisFieldRegistry().get('beta', 'focus')
    assert focus_field is not None
    series = timeline.get_field_series('beta', 'focus', window=10)
    print(f"Focus series (n={len(series)}): {[f'{v:.2f}' for v in series[-5:]]}")

    trend = timeline.trend('beta', 'focus', window=15)
    print(f"Trend: {trend.direction}, slope={trend.slope:.4f}, mean={trend.mean:.3f}")

    query = SnapshotQuery(axes=['beta'], limit=5)
    results = timeline.query(query)
    print(f"Query (beta, limit=5): {len(results)} results")

    corr = timeline.correlation('beta', 'focus', 'alpha', 'energy', window=15)
    print(f"Correlation alpha.focus vs alpha.energy: r={corr.correlation:.3f} ({corr.strength})")

    print("TemporalState: PASS\n")


def test_find_drift():
    print("=== Drift Detection (θ Negativity) ===")
    timeline = TemporalState(max_size=100)
    reg = AxisFieldRegistry()

    for i in range(30):
        val = 0.5
        if 10 <= i < 15:
            val = 0.2
        if 20 <= i < 25:
            val = 0.9
        timeline.record({
            'timestamp': f'2026-05-13T10:{i:02d}:00',
            'beta': {'focus': val},
        })

    focus_field = AxisFieldRegistry().get('beta', 'focus')
    assert focus_field is not None

    drift = timeline.find_drift('beta', 'focus', expected_value=0.5, drift_threshold=0.25)
    print(f"Drift from 0.5 (threshold=0.25): {len(drift)} points")

    trend = timeline.trend('beta', 'focus', window=30)
    print(f"Full window trend: {trend.direction}, slope={trend.slope:.4f}")

    print("Drift detection: PASS\n")


def test_integration():
    print("=== Integration: Axis + TemporalState ===")
    alpha = Axis.create_alpha()
    beta = Axis.create_beta()
    timeline = TemporalState(max_size=50)

    reg = AxisFieldRegistry()
    energy_field = reg.get('alpha', 'energy')
    focus_field = reg.get('beta', 'focus')

    for i in range(15):
        alpha.set(energy_field, 0.3 + i * 0.03)
        beta.set(focus_field, 0.6 + i * 0.02)
        timeline.record({
            'timestamp': f'2026-05-13T10:{i*2:02d}:00',
            'alpha': alpha.snapshot(),
            'beta': beta.snapshot(),
        })

    trend_a = timeline.trend('alpha', 'energy', window=10)
    trend_b = timeline.trend('beta', 'focus', window=10)
    print(f"Alpha.energy trend: {trend_a.direction}")
    print(f"Beta.focus trend: {trend_b.direction}")

    corr = timeline.correlation('alpha', 'energy', 'beta', 'focus', window=10)
    print(f"Correlation: {corr.correlation:.3f} ({corr.strength})")

    print("Integration: PASS\n")


if __name__ == '__main__':
    test_axis_field_registry()
    test_axis_typed_access()
    test_axis_from_config()
    test_temporal_state()
    test_find_drift()
    test_integration()
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)