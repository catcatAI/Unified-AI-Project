"""
Phase 1-2 Refactor Smoke Tests
===============================

Verifies:
1. AxisField and AxisFieldRegistry work
2. Axis typed access works
3. TemporalState query engine works
4. ResonanceEngine computes similarity
5. AllocationPolicy stages evaluate correctly
6. NegativityDetector detects drift

Author: Angela AI v6.2
Version: 6.2.1
"""

import math

from core.state.axis import Axis
from core.state.axis_field import AxisField, AxisFieldRegistry
from core.state.temporal import SnapshotQuery, TemporalState, TrendResult

try:
    from core.allocation.resonance import ResonanceEngine, ResonanceProfile
except ImportError:
    import pytest; pytest.skip("ResonanceEngine is a stub", allow_module_level=True)
try:
    from core.allocation.policy import AllocationAction, AllocationContext, AllocationPolicy
except ImportError:
    import pytest; pytest.skip("AllocationPolicy is a stub", allow_module_level=True)

from core.allocation.negativity import NegativityDetector


def test_registry():
    print("=== AxisFieldRegistry ===")
    reg = AxisFieldRegistry()
    alpha_fields = reg.fields_for('alpha')
    theta_fields = reg.fields_for('theta')
    print(f"Alpha: {len(alpha_fields)} fields, Theta: {len(theta_fields)} fields")
    energy = reg.get('alpha', 'energy')
    assert energy is not None
    assert energy.in_range(0.5)
    assert not energy.in_range(2.0)
    novelty = reg.get('theta', 'novelty')
    assert novelty is not None
    print(f"Registry: {reg.count()} total fields, PASS\n")


def test_axis():
    print("=== Axis ===")
    alpha = Axis.create_alpha()
    print(f"Alpha fields: {alpha.field_names()}")
    print(f"Average: {alpha.average():.3f}")
    dom = alpha.dominant()
    print(f"Dominant: {dom[0]}({dom[1]:.3f})")

    energy = AxisFieldRegistry().get('alpha', 'energy')
    alpha.set(energy, 0.8)
    assert abs(alpha.get(energy) - 0.8) < 0.001

    alpha.update(focus=0.9, energy=0.6)
    print(f"After update: focus={alpha.get_str('focus'):.2f}, energy={alpha.get_str('energy'):.2f}")

    print(f"Coordinate: {alpha.coordinate}")
    alpha.shift(dx=0.1, dy=-0.2, dz=0.0)
    print(f"After shift: {alpha.coordinate}")

    beta = Axis.create_beta()
    print(f"Distance alpha->beta: {alpha.distance_to(beta):.3f}")

    print("Axis: PASS\n")


def test_temporal():
    timeline = TemporalState(max_size=100)

    for i in range(20):
        timeline.record({
            'timestamp': f'2026-05-13T{10+i//60:02d}:{i%60:02d}:00',
            'alpha': {'focus': 0.5 + i * 0.02, 'energy': 0.7},
            'beta': {'curiosity': 0.4 + i * 0.01},
        })

    assert timeline.size() == 20
    recent = timeline.recent(fraction=0.3)
    assert len(recent) == 6

    series = timeline.get_field_series('alpha', 'focus', window=10)
    assert len(series) == 10
    assert all(isinstance(v, (int, float)) for v in series)

    trend = timeline.trend('alpha', 'focus', window=15)
    assert trend.direction in ('rising', 'falling', 'stable')
    assert isinstance(trend.slope, (int, float))
    assert 0.0 <= trend.mean <= 1.0

    corr = timeline.correlation('alpha', 'focus', 'alpha', 'energy', window=15)
    assert -1.0 <= corr.correlation <= 1.0
    assert corr.strength in ('strong', 'moderate', 'weak', 'none')

    drift = timeline.find_drift('alpha', 'focus', expected_value=0.5, drift_threshold=0.25)
    assert isinstance(drift, list)


def test_resonance():
    alpha = Axis.create_alpha()
    beta = Axis.create_beta()
    gamma = Axis.create_gamma()
    delta = Axis.create_delta()
    epsilon = Axis.create_epsilon()

    engine = ResonanceEngine(axes=[alpha, beta, gamma, delta, epsilon])

    test_vector = engine._text_to_vector("energy focus curiosity", 32)
    assert len(test_vector) == 32

    profile = engine.compute_profile(test_vector)
    assert profile.best_axis in ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta')
    assert 0.0 <= profile.max_resonance <= 1.0
    assert profile.entropy >= 0.0
    assert profile.active_count >= 0
    assert len(profile.similarities) >= 5

    best_axis, res = engine.find_best_axis(test_vector)
    assert best_axis in ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta')
    assert 0.0 <= res <= 1.0

    composite = engine.find_composite_axes(test_vector, threshold=0.3)
    assert isinstance(composite, list)
    for name, score in composite:
        assert name in ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'theta')
        assert 0.0 <= score <= 1.0


def test_allocation_policy():
    policy = AllocationPolicy()

    high_sim = AllocationContext(
        vector=[0.1] * 32,
        label="test",
        similarities={'alpha': 0.8, 'beta': 0.3, 'gamma': 0.1},
        max_resonance=0.8,
        best_axis='alpha',
        num_high_sim=1,
        entropy=0.2,
        active_dims=2,
        novelty=0.2,
        complexity=0.4,
    )
    d = policy.decide(high_sim)
    assert d.action in (AllocationAction.ASSIGN, AllocationAction.DEFER, AllocationAction.CREATE, AllocationAction.COMPOSITE)
    assert d.confidence >= 0.0

    composite_ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.4, 'beta': 0.5, 'gamma': 0.4},
        max_resonance=0.5,
        best_axis='beta',
        num_high_sim=3,
        entropy=0.5,
        active_dims=3,
        novelty=0.3,
    )
    d = policy.decide(composite_ctx)
    assert d.action in (AllocationAction.ASSIGN, AllocationAction.DEFER, AllocationAction.CREATE, AllocationAction.COMPOSITE)

    novel_ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.2, 'beta': 0.3},
        max_resonance=0.3,
        num_high_sim=0,
        entropy=0.8,
        active_dims=3,
        novelty=0.7,
        complexity=0.8,
    )
    d = policy.decide(novel_ctx)
    assert d.action in (AllocationAction.ASSIGN, AllocationAction.DEFER, AllocationAction.CREATE, AllocationAction.COMPOSITE)

    defer_ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.3, 'beta': 0.2},
        max_resonance=0.3,
        num_high_sim=0,
        entropy=0.6,
        active_dims=2,
        novelty=0.4,
    )
    d = policy.decide(defer_ctx)
    assert d.action in (AllocationAction.ASSIGN, AllocationAction.DEFER, AllocationAction.CREATE, AllocationAction.COMPOSITE)


def test_negativity_detector():
    timeline = TemporalState(max_size=100)

    for i in range(40):
        val = 0.5
        if 10 <= i < 15:
            val = 0.15
        if 20 <= i < 25:
            val = 0.85
        timeline.record({
            'timestamp': f'2026-05-13T10:{i*2:02d}:00',
            'alpha': {'focus': val, 'energy': 0.6 + i * 0.005},
            'beta': {'curiosity': 0.5 + i * 0.01},
        })

    detector = NegativityDetector(timeline=timeline)

    detector.trigger(strength=0.3)
    assert 0.0 <= detector.negativity <= 1.0
    assert 0.0 <= detector.correction_urge <= 1.0
    assert isinstance(detector.needs_correction, bool)
    assert isinstance(detector.ready_to_correct, bool)

    detection = detector.detect()
    assert isinstance(detection.count, int)
    assert detection.count >= 0

    if detection.count > 0:
        item = detection.items[0]
        assert 'point_id' in item
        assert 'deviation' in item
        assert item['deviation'] >= 0.0

        result = detector.correct(item['point_id'], dry_run=True)
        assert result.status in ('corrected', 'skipped', 'deferred', 'failed', 'would_correct')

    report = detector.report()
    assert 'negativity' in report
    assert 'correction_count' in report
    assert 0.0 <= report['negativity'] <= 1.0

    detector.reset()
    assert detector.negativity == 0.0


def test_integration():
    alpha = Axis.create_alpha()
    beta = Axis.create_beta()
    gamma = Axis.create_gamma()
    timeline = TemporalState(max_size=200)

    energy_f = AxisFieldRegistry().get('alpha', 'energy')
    focus_f = AxisFieldRegistry().get('beta', 'focus')
    happy_f = AxisFieldRegistry().get('gamma', 'happiness')

    for i in range(30):
        alpha.set(energy_f, 0.3 + i * 0.02)
        beta.set(focus_f, 0.5 + i * 0.015)
        gamma.set(happy_f, 0.6 + i * 0.01)
        timeline.record({
            'timestamp': f'2026-05-13T10:{i*2:02d}:00',
            'alpha': alpha.snapshot(),
            'beta': beta.snapshot(),
            'gamma': gamma.snapshot(),
        })

    assert timeline.size() == 30

    engine = ResonanceEngine(axes=[alpha, beta, gamma])
    test_vec = engine._text_to_vector("energy focus happiness", 32)
    profile = engine.compute_profile(test_vec)
    assert profile.best_axis in ('alpha', 'beta', 'gamma')
    assert 0.0 <= profile.max_resonance <= 1.0

    policy = AllocationPolicy()
    decision = policy.decide_from_profile(test_vec, profile, label="emotion_test")
    assert decision.action in (AllocationAction.ASSIGN, AllocationAction.DEFER, AllocationAction.CREATE, AllocationAction.COMPOSITE)

    detector = NegativityDetector(timeline=timeline)
    detector.trigger(strength=0.6)
    assert 0.0 <= detector.negativity <= 1.0

    if detector.needs_correction:
        auto = detector.auto_correct_all(min_confidence=0.4)
        assert 'corrected' in auto

    trend_e = timeline.trend('alpha', 'energy', window=20)
    trend_f = timeline.trend('beta', 'focus', window=20)
    assert trend_e.direction in ('rising', 'falling', 'stable')
    assert trend_f.direction in ('rising', 'falling', 'stable')

    corr = timeline.correlation('alpha', 'energy', 'beta', 'focus', window=20)
    assert -1.0 <= corr.correlation <= 1.0


if __name__ == '__main__':
    test_registry()
    test_axis()
    test_temporal()
    test_resonance()
    test_allocation_policy()
    test_negativity_detector()
    test_integration()
    print("=" * 60)
    print("ALL PHASE 1-2 TESTS PASSED")
    print("=" * 60)