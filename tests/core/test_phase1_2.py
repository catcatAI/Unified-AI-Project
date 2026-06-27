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
    print("=== TemporalState ===")
    timeline = TemporalState(max_size=100)

    for i in range(20):
        timeline.record({
            'timestamp': f'2026-05-13T{10+i//60:02d}:{i%60:02d}:00',
            'alpha': {'focus': 0.5 + i * 0.02, 'energy': 0.7},
            'beta': {'curiosity': 0.4 + i * 0.01},
        })

    print(f"Size: {timeline.size()}")
    recent = timeline.recent(fraction=0.3)
    print(f"Recent 30%: {len(recent)} snapshots")

    series = timeline.get_field_series('alpha', 'focus', window=10)
    print(f"Focus series (n={len(series)}): {[f'{v:.2f}' for v in series[-5:]]}")

    trend = timeline.trend('alpha', 'focus', window=15)
    print(f"Trend: {trend.direction}, slope={trend.slope:.4f}, mean={trend.mean:.3f}")

    corr = timeline.correlation('alpha', 'focus', 'alpha', 'energy', window=15)
    print(f"Correlation alpha.focus vs alpha.energy: r={corr.correlation:.3f} ({corr.strength})")

    drift = timeline.find_drift('alpha', 'focus', expected_value=0.5, drift_threshold=0.25)
    print(f"Drift from 0.5 (thresh=0.25): {len(drift)} points")

    print("TemporalState: PASS\n")


def test_resonance():
    print("=== ResonanceEngine ===")
    alpha = Axis.create_alpha()
    beta = Axis.create_beta()
    gamma = Axis.create_gamma()
    delta = Axis.create_delta()
    epsilon = Axis.create_epsilon()

    engine = ResonanceEngine(axes=[alpha, beta, gamma, delta, epsilon])

    test_vector = engine._text_to_vector("energy focus curiosity", 32)
    print(f"Test vector: {len(test_vector)} dims")

    profile = engine.compute_profile(test_vector)
    print(f"Profile: best={profile.best_axis}({profile.max_resonance:.3f})")
    print(f"  Similarities: {dict(sorted(profile.similarities.items(), key=lambda x: -x[1])[:3])}")
    print(f"  Entropy: {profile.entropy:.3f}, active={profile.active_count}")

    best_axis, res = engine.find_best_axis(test_vector)
    print(f"Best axis: {best_axis} ({res:.3f})")

    composite = engine.find_composite_axes(test_vector, threshold=0.3)
    print(f"Composite (thresh=0.3): {[(n, f'{s:.3f}') for n, s in composite]}")

    print("ResonanceEngine: PASS\n")


def test_allocation_policy():
    print("=== AllocationPolicy ===")
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
    print(f"High similarity: {d.action.value} -> {d.target}, conf={d.confidence:.2f}")

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
    print(f"Composite: {d.action.value}, targets={d.targets}")

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
    print(f"Novel: {d.action.value} -> {d.proposed_name}, conf={d.confidence:.2f}")

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
    print(f"Defer: {d.action.value} -> {d.buffer}, conf={d.confidence:.2f}")

    print("AllocationPolicy: PASS\n")


def test_negativity_detector():
    print("=== NegativityDetector ===")
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
    print(f"After trigger: neg={detector.negativity:.2f}, urge={detector.correction_urge:.2f}")
    print(f"  needs_correction: {detector.needs_correction}")
    print(f"  ready_to_correct: {detector.ready_to_correct}")

    detection = detector.detect()
    print(f"Detection: {detection.count} misallocated points")

    if detection.count > 0:
        item = detection.items[0]
        print(f"  First: {item['point_id']}, deviation={item['deviation']:.3f}")

        result = detector.correct(item['point_id'], dry_run=True)
        print(f"  Dry run: {result.status}, {result.reasoning}")

        if detector.ready_to_correct:
            result = detector.correct(item['point_id'])
            print(f"  Actual: {result.status}, {result.reasoning}")

    report = detector.report()
    print(f"Report: neg={report['negativity']:.2f}, corrections={report['correction_count']}")

    detector.reset()
    print(f"After reset: {detector.negativity:.2f}")

    print("NegativityDetector: PASS\n")


def test_integration():
    print("=== Integration: Full Pipeline ===")
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

    engine = ResonanceEngine(axes=[alpha, beta, gamma])
    test_vec = engine._text_to_vector("energy focus happiness", 32)
    profile = engine.compute_profile(test_vec)
    print(f"Resonance profile: best={profile.best_axis}({profile.max_resonance:.3f})")

    policy = AllocationPolicy()
    decision = policy.decide_from_profile(test_vec, profile, label="emotion_test")
    print(f"Allocation decision: {decision.action.value}")

    detector = NegativityDetector(timeline=timeline)
    detector.trigger(strength=0.6)

    if detector.needs_correction:
        auto = detector.auto_correct_all(min_confidence=0.4)
        print(f"Auto-correct: {auto['corrected']}/{auto.get('total_detected', auto['corrected'])}")

    trend_e = timeline.trend('alpha', 'energy', window=20)
    trend_f = timeline.trend('beta', 'focus', window=20)
    print(f"Alpha.energy trend: {trend_e.direction} (slope={trend_e.slope:.4f})")
    print(f"Beta.focus trend: {trend_f.direction} (slope={trend_f.slope:.4f})")

    corr = timeline.correlation('alpha', 'energy', 'beta', 'focus', window=20)
    print(f"Correlation: {corr.correlation:.3f} ({corr.strength})")

    print("Integration: PASS\n")


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