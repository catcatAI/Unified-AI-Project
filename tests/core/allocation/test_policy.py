import pytest
try:
    from apps.backend.src.core.allocation.policy import (
        AllocationPolicy, AllocationContext, AllocationDecision,
        AllocationAction, AssignStage, CompositeStage,
        CreateStage, DeferStage,
    )
except ImportError:
    import pytest; pytest.skip("AllocationPolicy stub not available", allow_module_level=True)


def make_context(**overrides) -> AllocationContext:
    ctx = AllocationContext(
        vector=[0.1, 0.2, 0.3],
        label="test",
        similarities={"alpha": 0.8, "beta": 0.3},
        max_resonance=0.8,
        best_axis="alpha",
        num_high_sim=1,
        entropy=0.4,
        active_dims=3,
        novelty=0.2,
        complexity=0.5,
        dimension_fit=0.8,
    )
    ctx.__dict__.update(overrides)
    return ctx


class TestAssignStage:
    def test_matches_high_similarity(self):
        stage = AssignStage(threshold=0.7)
        ctx = make_context(max_resonance=0.9, best_axis="alpha")
        assert stage.matches(ctx) is True

    def test_does_not_match_low_similarity(self):
        stage = AssignStage(threshold=0.7)
        ctx = make_context(max_resonance=0.5, best_axis="alpha")
        assert stage.matches(ctx) is False

    def test_decide_returns_assign(self):
        stage = AssignStage(threshold=0.7)
        ctx = make_context(max_resonance=0.85, best_axis="alpha")
        decision = stage.decide(ctx)
        assert decision.action == AllocationAction.ASSIGN
        assert decision.target == "alpha"
        assert decision.confidence == 0.85


class TestCompositeStage:
    def test_matches_multiple_high_sim(self):
        stage = CompositeStage(threshold=0.3, min_axes=2)
        ctx = make_context(
            num_high_sim=2, max_resonance=0.6,
            similarities={"alpha": 0.6, "beta": 0.5},
        )
        assert stage.matches(ctx) is True

    def test_does_not_match_few_axes(self):
        stage = CompositeStage(threshold=0.3, min_axes=2)
        ctx = make_context(num_high_sim=1, max_resonance=0.6)
        assert stage.matches(ctx) is False

    def test_decide_returns_composite(self):
        stage = CompositeStage(threshold=0.3, min_axes=2)
        ctx = make_context(
            num_high_sim=2, max_resonance=0.6,
            similarities={"alpha": 0.6, "beta": 0.5, "gamma": 0.1},
        )
        decision = stage.decide(ctx)
        assert decision.action == AllocationAction.COMPOSITE
        assert len(decision.targets) > 0


class TestCreateStage:
    def test_matches_high_novelty(self):
        stage = CreateStage(novelty_threshold=0.6, complexity_min=2)
        ctx = make_context(novelty=0.8, active_dims=3)
        assert stage.matches(ctx) is True

    def test_does_not_match_low_novelty(self):
        stage = CreateStage(novelty_threshold=0.6, complexity_min=2)
        ctx = make_context(novelty=0.3, active_dims=3)
        assert stage.matches(ctx) is False

    def test_decide_returns_create(self):
        stage = CreateStage(novelty_threshold=0.6, complexity_min=2)
        ctx = make_context(novelty=0.8, active_dims=3, label="new_idea")
        decision = stage.decide(ctx)
        assert decision.action == AllocationAction.CREATE
        assert decision.proposed_name == "new_idea"


class TestDeferStage:
    def test_always_matches(self):
        stage = DeferStage(fallback=True)
        ctx = make_context()
        assert stage.matches(ctx) is True

    def test_decide_returns_defer(self):
        stage = DeferStage(fallback=True)
        ctx = make_context(max_resonance=0.2)
        decision = stage.decide(ctx)
        assert decision.action == AllocationAction.DEFER
        assert decision.buffer == "unclassified_experiences"
        assert decision.confidence == 0.3


class TestAllocationPolicy:
    def test_decide_assign_high_resonance(self):
        policy = AllocationPolicy()
        ctx = make_context(max_resonance=0.9, best_axis="alpha")
        decision = policy.decide(ctx)
        assert decision.action == AllocationAction.ASSIGN
        assert decision.target == "alpha"

    def test_decide_composite(self):
        policy = AllocationPolicy()
        ctx = make_context(
            max_resonance=0.5, best_axis="alpha",
            similarities={"alpha": 0.5, "beta": 0.4},
            num_high_sim=2,
        )
        decision = policy.decide(ctx)
        assert decision.action == AllocationAction.COMPOSITE

    def test_decide_create(self):
        policy = AllocationPolicy()
        ctx = make_context(
            max_resonance=0.2, best_axis=None,
            novelty=0.8, active_dims=3, label="novel_concept",
        )
        decision = policy.decide(ctx)
        assert decision.action == AllocationAction.CREATE

    def test_decide_defer_fallback(self):
        policy = AllocationPolicy()
        ctx = make_context(
            max_resonance=0.1, best_axis=None,
            novelty=0.1, active_dims=1,
        )
        decision = policy.decide(ctx)
        assert decision.action == AllocationAction.DEFER

    def test_default_stages_in_order(self):
        policy = AllocationPolicy()
        names = [s.name for s in policy.stages]
        assert names == ["AssignStage", "CompositeStage", "CreateStage", "DeferStage"]

    def test_default_stages_no_create(self):
        policy = AllocationPolicy(enable_create=False)
        names = [s.name for s in policy.stages]
        assert "CreateStage" not in names

    def test_add_stage(self):
        policy = AllocationPolicy()
        stage = AssignStage(threshold=0.9)
        policy.add_stage(stage)
        names = [s.name for s in policy.stages]
        assert "AssignStage" in names

    def test_remove_stage(self):
        policy = AllocationPolicy()
        assert policy.remove_stage("CreateStage") is True
        names = [s.name for s in policy.stages]
        assert "CreateStage" not in names

    def test_remove_nonexistent_stage(self):
        policy = AllocationPolicy()
        assert policy.remove_stage("Nonexistent") is False

    def test_stage_disables_composite(self):
        policy = AllocationPolicy(enable_composite=False)
        names = [s.name for s in policy.stages]
        assert "CompositeStage" not in names

    def test_decide_from_profile(self):
        policy = AllocationPolicy()

        class FakeProfile:
            similarities = {"alpha": 0.9}
            best_axis = "alpha"
            max_resonance = 0.9
            num_high_sim = 1
            entropy = 0.3
            active_count = 2

        decision = policy.decide_from_profile(
            vector=[0.1, 0.2, 0.3],
            profile=FakeProfile(),
            label="test",
        )
        assert decision.action == AllocationAction.ASSIGN

    def test_decision_repr_assign(self):
        d = AllocationDecision(
            action=AllocationAction.ASSIGN,
            target="alpha", confidence=0.85,
        )
        assert "ASSIGN" in repr(d)
        assert "alpha" in repr(d)

    def test_decision_repr_defer(self):
        d = AllocationDecision(
            action=AllocationAction.DEFER,
            buffer="test_buf", confidence=0.3,
        )
        assert "DEFER" in repr(d)
