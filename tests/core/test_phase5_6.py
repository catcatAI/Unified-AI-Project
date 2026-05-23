"""
Phase 5-6 Smoke Tests: Ripple + Influence
===========================================

Author: Angela AI v6.2
"""

import sys, math
sys.path.insert(0, 'apps/backend/src')

from core.ripple.node import (
    RippleNode, RippleDepth, MathOp,
    LinearCascade, ExponentialCascade, AdaptiveCascade,
    RippleApplicatorRegistry, RippleAccumulator,
)
from core.influence.space import (
    InfluenceSpace, GravityRule, EntropyRule, MemoryRule,
    InfluenceRuleSet, ConflictStrategy,
)
from core.state.axis import Axis


def test_ripple_node():
    print("=== RippleNode ===")
    node = RippleNode(
        operator=MathOp.DIV,
        result=10.0,
        result_magnitude=100.0,
        epsilon_delta=0.5,
        alpha_arousal=0.3,
        beta_focus=0.2,
        gamma_excitement=0.1,
    )

    print(f"RippleNode: {node}")
    print(f"Effect alpha: {node.get_effect('alpha'):.3f}")
    print(f"Effect gamma: {node.get_effect('gamma'):.3f}")
    print(f"Effect unknown: {node.get_effect('zeta'):.3f}")

    cascaded = node.cascade(targets=['alpha', 'beta', 'gamma', 'delta', 'theta'], strategy=LinearCascade())
    print(f"Cascade produced {len(cascaded)} nodes")
    for n in cascaded[:4]:
        print(f"  {n}")

    print("RippleNode: PASS\n")


def test_cascade_strategies():
    print("=== Cascade Strategies ===")
    strategies = [
        LinearCascade(base_decay=0.72),
        ExponentialCascade(rate=0.3),
        AdaptiveCascade(base_decay=0.72),
    ]

    for s in strategies:
        decays = [s.compute_decay(i, 1.0) for i in range(5)]
        print(f"{s.__class__.__name__}: {[f'{d:.3f}' for d in decays]}")

    print("Cascade Strategies: PASS\n")


def test_ripple_applicators():
    print("=== RippleApplicatorRegistry ===")

    class MockAxis:
        def __init__(self):
            self.values = {'arousal': 0.5, 'focus': 0.5, 'happiness': 0.5, 'bond': 0.5, 'logic': 0.5}

    alpha = MockAxis()
    beta = MockAxis()
    gamma = MockAxis()

    ripple = RippleNode(
        operator=MathOp.MUL,
        result=5.0,
        alpha_arousal=0.3,
        beta_focus=0.2,
        gamma_excitement=0.1,
    )

    RippleApplicatorRegistry.apply_node_to_axes(ripple, type('M', (), {'alpha': alpha, 'beta': beta, 'gamma': gamma})())

    print(f"Alpha arousal after: {alpha.values['arousal']:.3f}")
    print(f"Beta focus after: {beta.values['focus']:.3f}")
    print(f"Gamma happiness after: {gamma.values['happiness']:.3f}")

    print("Applicator Registry: PASS\n")


def test_ripple_accumulator():
    print("=== RippleAccumulator ===")
    acc = RippleAccumulator()

    for i in range(5):
        node = RippleNode(
            operator=MathOp.ADD,
            epsilon_delta=0.1 * i,
            alpha_arousal=0.05 * i,
            gamma_excitement=0.02 * i,
        )
        acc.add(node)

    summary = acc.summary()
    print(f"Accumulator: {summary}")
    print(f"Fatigue: {acc.fatigue:.3f}, Max depth: {acc.max_depth}")

    acc.reset()
    print(f"After reset: {len(acc.ripples)} ripples")

    print("RippleAccumulator: PASS\n")


def test_influence_rules():
    print("=== Influence Rules ===")
    alpha = Axis.create_alpha()
    beta = Axis.create_beta()
    gamma = Axis.create_gamma()

    rules = InfluenceRuleSet(strategy=ConflictStrategy.ENTROPY_WEIGHTED)
    rules.add(GravityRule())
    rules.add(EntropyRule(weight=0.2))
    rules.add(MemoryRule(weight=0.15))
    print(f"RuleSet: {rules}")

    base = 0.3
    final, names = rules.compute_all(alpha, beta, base, context={'history_trend': 0.02})
    print(f"Alpha->Beta: {final:.4f} (rules: {names})")

    final2, _ = rules.compute_all(beta, gamma, base, context={'history_trend': -0.03})
    print(f"Beta->Gamma: {final2:.4f}")

    print("Influence Rules: PASS\n")


def test_influence_space():
    print("=== InfluenceSpace ===")
    alpha = Axis.create_alpha(weight=1.0)
    beta = Axis.create_beta(weight=1.0)
    gamma = Axis.create_gamma(weight=1.0)

    base_matrix = {
        'alpha': {'beta': 0.4, 'gamma': 0.2},
        'beta': {'alpha': 0.3, 'gamma': 0.5},
        'gamma': {'alpha': 0.2, 'beta': 0.3},
    }

    space = InfluenceSpace(
        axes={'alpha': alpha, 'beta': beta, 'gamma': gamma},
        base_matrix=base_matrix,
    )
    space.add_rule(GravityRule())

    inf_ab = space.compute('alpha', 'beta')
    inf_ba = space.compute('beta', 'alpha')
    inf_ag = space.compute('alpha', 'gamma')

    print(f"Alpha->Beta: {inf_ab:.4f}")
    print(f"Beta->Alpha: {inf_ba:.4f}")
    print(f"Alpha->Gamma: {inf_ag:.4f}")

    all_inf = space.compute_all()
    print(f"All pairs computed: {len(all_inf)} sources")

    space.invalidate_cache()
    inf_ab2 = space.compute('alpha', 'beta', use_cache=False)
    print(f"Alpha->Beta (uncached): {inf_ab2:.4f}")

    print(f"Space repr: {space}")
    print("InfluenceSpace: PASS\n")


def test_gravity_rule():
    print("=== GravityRule ===")
    alpha = Axis.create_alpha()
    beta = Axis.create_beta()

    g_rule = GravityRule(softening=10.0, gravity_constant=25.0)
    factor = g_rule.compute(alpha, beta, base_strength=0.5)
    print(f"Gravity factor: {factor:.4f}")
    print(f"Alpha coord: {alpha.coordinate}")
    print(f"Beta coord: {beta.coordinate}")

    g_rule2 = GravityRule(softening=1.0, gravity_constant=10.0)
    factor2 = g_rule2.compute(alpha, beta, base_strength=0.5)
    print(f"Custom Gravity factor: {factor2:.4f}")

    print("GravityRule: PASS\n")


def test_conflict_strategy():
    print("=== Conflict Strategies ===")
    from core.influence.space import ConflictStrategy

    strategies = [
        ConflictStrategy.FIRST_WINS,
        ConflictStrategy.LAST_WINS,
        ConflictStrategy.MAX,
        ConflictStrategy.MIN,
        ConflictStrategy.AVERAGE,
        ConflictStrategy.ENTROPY_WEIGHTED,
    ]

    factors = [0.5, 0.8, 0.3, 0.6, 0.9, 0.4]

    for s in strategies:
        rs = InfluenceRuleSet(strategy=s)
        rs.add(GravityRule())
        rs.add(EntropyRule())

        result = rs._resolve(factors[:2], None)
        print(f"{s.value}: {result:.4f}")

    print("Conflict Strategies: PASS\n")


def test_feedback_ripple():
    print("=== Feedback Ripples ===")
    ripple = RippleNode(
        operator=MathOp.DIV,
        result=10000.0,
        result_magnitude=50000.0,
        alpha_arousal=0.8,
        overload_triggered=True,
        fear_triggered=True,
    )

    cascaded = ripple.cascade(targets=['alpha', 'beta', 'gamma'], strategy=LinearCascade())
    feedback = [n for n in cascaded if n.cascade_step >= 97]
    print(f"Feedback ripples: {len(feedback)}")
    for fb in feedback:
        print(f"  {fb.description}")

    print("Feedback Ripples: PASS\n")


def test_integration():
    print("=== Integration: Ripple -> Influence -> Axis ===")

    node = RippleNode(
        operator=MathOp.MUL,
        result=8.0,
        epsilon_delta=0.6,
        alpha_arousal=0.4,
        beta_focus=0.3,
        gamma_excitement=0.2,
    )

    cascaded = node.cascade(targets=['alpha', 'beta', 'gamma', 'delta'], strategy=LinearCascade(base_decay=0.75))

    alpha = Axis.create_alpha(weight=1.0)
    beta = Axis.create_beta(weight=1.0)
    gamma = Axis.create_gamma(weight=0.8)

    space = InfluenceSpace(
        axes={'alpha': alpha, 'beta': beta, 'gamma': gamma},
        base_matrix={'alpha': {'beta': 0.4}, 'beta': {'gamma': 0.5}, 'epsilon': {'alpha': 0.3}},
    )
    space.add_rule(GravityRule())

    for n in cascaded:
        if n.cascade_step == 0:
            RippleApplicatorRegistry.apply_node_to_axes(n, type('M', (), {
                'alpha': alpha, 'beta': beta, 'gamma': gamma, 'delta': Axis.create_delta()
            })())

    print(f"Alpha avg after: {alpha.average():.3f}")
    print(f"Beta avg after: {beta.average():.3f}")
    print(f"Gamma avg after: {gamma.average():.3f}")

    inf = space.compute('epsilon', 'alpha')
    print(f"Influence epsilon->alpha: {inf:.4f}")

    print("Integration: PASS\n")


if __name__ == '__main__':
    test_ripple_node()
    test_cascade_strategies()
    test_ripple_applicators()
    test_ripple_accumulator()
    test_influence_rules()
    test_influence_space()
    test_gravity_rule()
    test_conflict_strategy()
    test_feedback_ripple()
    test_integration()
    print("=" * 60)
    print("ALL PHASE 5-6 TESTS PASSED")
    print("=" * 60)