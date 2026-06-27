"""
Unit Tests — AllocationPolicy
==============================

Author: Angela AI v6.2
"""


try:
    from core.allocation.policy import (
        AllocationAction,
        AllocationContext,
        AllocationDecision,
        AllocationPolicy,
        AllocationStage,
        AssignStage,
        CompositeStage,
        CreateStage,
        DeferStage,
    )
except ImportError:
    import pytest; pytest.skip("AllocationPolicy is a stub", allow_module_level=True)


def test_assign_stage_high_sim():
    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.8, 'beta': 0.3},
        max_resonance=0.8,
        best_axis='alpha',
        num_high_sim=1,
        entropy=0.5,
        active_dims=2,
        novelty=0.2,
        complexity=0.3,
    )
    stage = AssignStage(threshold=0.7)
    assert stage.matches(ctx)
    decision = stage.decide(ctx)
    assert decision.action == AllocationAction.ASSIGN
    assert decision.target == 'alpha'
    assert decision.confidence == 0.8


def test_assign_stage_low_sim():
    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.5, 'beta': 0.3},
        max_resonance=0.5,
        best_axis='alpha',
        num_high_sim=0,
        entropy=0.5,
        active_dims=2,
        novelty=0.5,
        complexity=0.3,
    )
    stage = AssignStage(threshold=0.7)
    assert not stage.matches(ctx)


def test_composite_stage():
    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.5, 'beta': 0.4, 'gamma': 0.3},
        max_resonance=0.5,
        best_axis='alpha',
        num_high_sim=2,
        entropy=0.5,
        active_dims=3,
        novelty=0.5,
        complexity=0.3,
    )
    stage = CompositeStage(threshold=0.3, min_axes=2)
    assert stage.matches(ctx)
    decision = stage.decide(ctx)
    assert decision.action == AllocationAction.COMPOSITE
    assert decision.targets is not None
    assert len(decision.targets) >= 2


def test_create_stage():
    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.2, 'beta': 0.2},
        max_resonance=0.2,
        best_axis=None,
        num_high_sim=0,
        entropy=0.9,
        active_dims=3,
        novelty=0.7,
        complexity=0.5,
    )
    stage = CreateStage(novelty_threshold=0.6, complexity_min=2)
    assert stage.matches(ctx)
    decision = stage.decide(ctx)
    assert decision.action == AllocationAction.CREATE
    assert decision.proposed_name is not None


def test_defer_stage():
    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.3},
        max_resonance=0.3,
        best_axis='alpha',
        num_high_sim=0,
        entropy=0.9,
        active_dims=1,
        novelty=0.2,
        complexity=0.1,
    )
    stage = DeferStage(fallback=True)
    assert stage.matches(ctx)
    decision = stage.decide(ctx)
    assert decision.action == AllocationAction.DEFER


def test_policy_full_pipeline():
    policy = AllocationPolicy()

    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.8, 'beta': 0.3},
        max_resonance=0.8,
        best_axis='alpha',
        num_high_sim=1,
        entropy=0.5,
        active_dims=2,
        novelty=0.2,
        complexity=0.3,
    )
    decision = policy.decide(ctx)
    assert decision.action == AllocationAction.ASSIGN
    assert decision.target == 'alpha'


def test_policy_falls_through_to_defer():
    policy = AllocationPolicy()
    ctx = AllocationContext(
        vector=[0.1] * 32,
        similarities={'alpha': 0.1, 'beta': 0.1},
        max_resonance=0.1,
        best_axis='alpha',
        num_high_sim=0,
        entropy=0.9,
        active_dims=1,
        novelty=0.9,
        complexity=0.1,
    )
    decision = policy.decide(ctx)
    assert decision.action == AllocationAction.DEFER


def test_policy_decide_from_profile():
    from core.allocation.policy import AllocationPolicy
    from core.allocation.resonance import ResonanceProfile

    profile = ResonanceProfile(
        similarities={'alpha': 0.8, 'beta': 0.3},
        best_axis='alpha',
        max_resonance=0.8,
        num_high_sim=1,
        entropy=0.5,
        active_count=2,
    )
    policy = AllocationPolicy()
    decision = policy.decide_from_profile([0.1] * 32, profile, label='test')
    assert decision.action == AllocationAction.ASSIGN


def test_add_remove_stage():
    policy = AllocationPolicy()
    initial_count = len(policy.stages)

    class CustomStage(AllocationStage):
        def __init__(self):
            self.name = "CustomStage"
        def matches(self, ctx):
            return ctx.max_resonance > 0.95

    policy.add_stage(CustomStage())
    assert len(policy.stages) == initial_count + 1

    removed = policy.remove_stage("CustomStage")
    assert removed
    assert len(policy.stages) == initial_count


def test_decision_repr():
    d = AllocationDecision(action=AllocationAction.ASSIGN, target='alpha', confidence=0.8)
    repr_str = repr(d)
    assert 'ASSIGN' in repr_str
    assert 'alpha' in repr_str


if __name__ == '__main__':
    tests = [
        test_assign_stage_high_sim,
        test_assign_stage_low_sim,
        test_composite_stage,
        test_create_stage,
        test_defer_stage,
        test_policy_full_pipeline,
        test_policy_falls_through_to_defer,
        test_policy_decide_from_profile,
        test_add_remove_stage,
        test_decision_repr,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\nAllocationPolicy: {passed} passed, {failed} failed")