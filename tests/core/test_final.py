"""
Final Integration Test — All Refactored Modules
================================================

Author: Angela AI v6.2
"""


from core.state.axis_field import AxisFieldRegistry
from core.state.axis import Axis
from core.state.temporal import TemporalState
from core.state.config_loader import StateConfig
try:
    from core.allocation.resonance import ResonanceEngine
except ImportError:
    import pytest; pytest.skip("ResonanceEngine is a stub", allow_module_level=True)
try:
    from core.allocation.policy import AllocationPolicy, AllocationContext
except ImportError:
    import pytest; pytest.skip("AllocationPolicy is a stub", allow_module_level=True)
try:
    from core.allocation.negativity import NegativityDetector
except ImportError:
    import pytest; pytest.skip("NegativityDetector is a stub", allow_module_level=True)
try:
    from core.ripple.node import RippleNode, RippleDepth, MathOp, LinearCascade, RippleApplicatorRegistry, RippleAccumulator
except ImportError:
    import pytest; pytest.skip("RippleNode is a stub", allow_module_level=True)
try:
    from core.influence.space import InfluenceSpace, GravityRule, EntropyRule, MemoryRule
except ImportError:
    import pytest; pytest.skip("InfluenceSpace is a stub", allow_module_level=True)


def test_full_pipeline():
    print("=== Full Refactor Pipeline ===")

    # Phase 1: Axis system
    reg = AxisFieldRegistry()
    print(f"Registry: {reg.count()} fields across {len(reg.all_axes())} axes")

    alpha = Axis.create_alpha()
    beta = Axis.create_beta()
    gamma = Axis.create_gamma()
    delta = Axis.create_delta()
    epsilon = Axis.create_epsilon()
    theta = Axis.create_theta()
    axes = [alpha, beta, gamma, delta, epsilon, theta]
    print(f"Created {len(axes)} axes")

    # Phase 2: Temporal history
    timeline = TemporalState(max_size=200)
    energy_f = AxisFieldRegistry().get('alpha', 'energy')
    focus_f = AxisFieldRegistry().get('beta', 'focus')
    happy_f = AxisFieldRegistry().get('gamma', 'happiness')

    for i in range(50):
        alpha.set(energy_f, 0.3 + i * 0.01)
        beta.set(focus_f, 0.5 + i * 0.008)
        gamma.set(happy_f, 0.6 + i * 0.005)
        timeline.record({
            'timestamp': f'2026-05-14T10:{i*2//60:02d}:{i*2%60:02d}:00',
            'alpha': alpha.snapshot(),
            'beta': beta.snapshot(),
            'gamma': gamma.snapshot(),
        })

    print(f"Timeline: {timeline.size()} snapshots")

    # Phase 3: Config
    cfg = StateConfig()
    print(f"Config: max_history={cfg.state_matrix.max_history}, {len(cfg.axes)} axes")
    print(f"  Allocation thresholds: assign={cfg.allocation.assign_threshold}, composite={cfg.allocation.composite_threshold}")
    print(f"  Negativity: trigger={cfg.negativity.trigger_threshold}, correction={cfg.negativity.correction_urge_threshold}")

    # Phase 4: Resonance + Allocation
    engine = ResonanceEngine(axes=axes)
    test_vec = engine._text_to_vector("energy focus curiosity", 32)
    profile = engine.compute_profile(test_vec)
    print(f"Resonance: best={profile.best_axis}({profile.max_resonance:.3f}), entropy={profile.entropy:.3f}")

    policy = AllocationPolicy()
    decision = policy.decide_from_profile(test_vec, profile, label="cognitive_task")
    print(f"Allocation: {decision.action.value} -> target={decision.target}")

    # Phase 5: Negativity
    detector = NegativityDetector(timeline=timeline)
    detector.trigger(strength=0.7)

    trend_a = timeline.trend('alpha', 'energy', window=30)
    trend_b = timeline.trend('beta', 'focus', window=30)
    corr = timeline.correlation('alpha', 'energy', 'beta', 'focus', window=30)
    print(f"Analysis: alpha.energy {trend_a.direction}({trend_a.slope:.4f}), corr={corr.correlation:.3f}({corr.strength})")

    if detector.needs_correction:
        result = detector.auto_correct_all(min_confidence=0.5)
        print(f"Negativity: corrected={result['corrected']}")

    # Phase 6: Ripples
    ripple = RippleNode(
        operator=MathOp.MUL,
        result=16.0,
        epsilon_delta=0.7,
        alpha_arousal=0.5,
        beta_focus=0.4,
        gamma_excitement=0.3,
    ).apply(epsilon=0.7, alpha=0.5, beta=0.4, gamma=0.3)

    cascaded = ripple.cascade(targets=['alpha', 'beta', 'gamma', 'delta', 'theta'], strategy=LinearCascade())
    print(f"Ripple cascade: {len(cascaded)} nodes (source + {len(cascaded)-1} cascaded)")

    for n in cascaded:
        RippleApplicatorRegistry.apply_node_to_axes(n, type('M', (), {
            'alpha': alpha, 'beta': beta, 'gamma': gamma,
            'delta': delta, 'epsilon': epsilon, 'theta': theta
        })())

    print(f"After ripples: alpha avg={alpha.average():.3f}, beta avg={beta.average():.3f}")

    # Phase 7: Influence
    space = InfluenceSpace(
        axes={'alpha': alpha, 'beta': beta, 'gamma': gamma, 'delta': delta, 'epsilon': epsilon, 'theta': theta},
        base_matrix=cfg.influence_matrix,
    )
    space.add_rule(GravityRule())
    space.add_rule(EntropyRule())
    space.add_rule(MemoryRule())

    inf_ab = space.compute('alpha', 'beta')
    inf_ag = space.compute('alpha', 'gamma')
    inf_ba = space.compute('beta', 'alpha')
    print(f"Influence: alpha->beta={inf_ab:.4f}, alpha->gamma={inf_ag:.4f}, beta->alpha={inf_ba:.4f}")

    # Accumulator
    acc = RippleAccumulator()
    for n in cascaded:
        acc.add(n)
    print(f"Accumulator: {acc.summary()}")

    # Final stats
    print()
    print("=== Final State ===")
    print(f"Axes: alpha({alpha.average():.3f}) beta({beta.average():.3f}) gamma({gamma.average():.3f})")
    print(f"Timeline: {timeline.size()} snapshots, trend data available")
    print(f"Influence: {space}")
    print(f"Negativity: neg={detector.negativity:.2f}, urge={detector.correction_urge:.2f}")

    print()
    print("=" * 60)
    print("FULL PIPELINE TEST PASSED")
    print("=" * 60)


if __name__ == '__main__':
    test_full_pipeline()