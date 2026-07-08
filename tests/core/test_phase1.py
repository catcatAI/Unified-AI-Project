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
    reg = AxisFieldRegistry()
    alpha_fields = reg.fields_for('alpha')
    assert len(alpha_fields) > 0
    theta_fields = reg.fields_for('theta')
    assert len(theta_fields) > 0
    energy = reg.get('alpha', 'energy')
    assert energy is not None
    assert energy.axis == 'alpha'
    assert energy.name == 'energy'
    assert energy.in_range(0.5) is True
    assert energy.in_range(-0.1) is False
    novelty = reg.get('theta', 'novelty')
    assert novelty is not None
    assert len(reg.all_axes()) > 0
    assert reg.count() > 0


def test_axis_typed_access():
    alpha = Axis.create_alpha()
    assert alpha.field_count() > 0
    reg = AxisFieldRegistry()
    energy_field = reg.get('alpha', 'energy')
    alpha.set(energy_field, 0.8)
    val = alpha.get(energy_field)
    assert abs(val - 0.8) < 0.001
    alpha.update(focus=0.9, energy=0.6)
    assert abs(alpha.get_str('focus') - 0.9) < 0.001
    assert abs(alpha.get_str('energy') - 0.6) < 0.001
    assert alpha.coordinate is not None
    alpha.shift(dx=0.1, dy=-0.2, dz=0.0)
    assert alpha.coordinate is not None
    snapshot = alpha.snapshot()
    assert len(snapshot) > 0


def test_axis_from_config():
    alpha = Axis.create_alpha(weight=0.8)
    beta = Axis.create_beta(weight=1.2)
    theta = Axis.create_theta()

    assert alpha.weight == 0.8
    assert beta.weight == 1.2
    assert theta.weight == 1.0
    assert alpha.field_count() > 0
    assert beta.field_count() > 0
    assert theta.field_count() > 0


def test_temporal_state():
    timeline = TemporalState(max_size=100)
    for i in range(20):
        timeline.record({
            'timestamp': f'2026-05-13T{10+i//60:02d}:{i%60:02d}:00',
            'beta': {'focus': 0.5 + i * 0.02},
            'alpha': {'energy': 0.7},
        })
    assert timeline.size() == 20
    query = SnapshotQuery(axes=['beta'], limit=5)
    results = timeline.query(query)
    assert len(results) <= 5
    corr = timeline.correlation('beta', 'focus', 'alpha', 'energy', window=15)
    assert -1.0 <= corr.correlation <= 1.0


def test_find_drift():
    timeline = TemporalState(max_size=100)
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
    drift = timeline.find_drift('beta', 'focus', expected_value=0.5, drift_threshold=0.25)
    assert len(drift) > 0
    trend = timeline.trend('beta', 'focus', window=30)
    assert trend.direction is not None


def test_integration():
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
    assert trend_a.direction is not None
    assert trend_b.direction is not None
    assert trend_a.slope is not None

    corr = timeline.correlation('alpha', 'energy', 'beta', 'focus', window=10)
    assert -1.0 <= corr.correlation <= 1.0
    assert corr.strength is not None
    assert timeline.size() == 15


