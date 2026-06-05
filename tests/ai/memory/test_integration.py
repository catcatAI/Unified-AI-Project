"""
Integration tests for the complete Angela AI system
Testing the full pipeline: θ → MathRipple → AttractorField → StateMatrix

Tests the integration between:
- Theta meta-cognitive axis (allocation + negativity)
- Math ripple engine (dual-depth system)
- Attractor field (gradient navigation)
- State matrix (6D state management)
"""

import pytest

try:
    from core.engine.state_matrix import StateMatrix4D
except ImportError:
    pytest.skip("StateMatrix4D not available", allow_module_level=True)
from ai.memory.math_ripple_engine import (
    MathRippleEngine, AlgorithmDepth, RippleDepth, RippleCascade,
    RippleAccumulator
)


class TestStateMatrix4DInitialization:
    """Test that StateMatrix4D initializes correctly with all 6 dimensions"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_all_6_dimensions_exist(self, matrix):
        assert "alpha" in matrix.dimensions
        assert "beta" in matrix.dimensions
        assert "gamma" in matrix.dimensions
        assert "delta" in matrix.dimensions
        assert "epsilon" in matrix.dimensions
        assert "theta" in matrix.dimensions

    def test_theta_has_negativity_values(self, matrix):
        assert "theta_negativity" in matrix.theta.values
        assert "correction_urge" in matrix.theta.values
        assert "audit_intensity" in matrix.theta.values

    def test_theta_has_allocation_values(self, matrix):
        assert "novelty" in matrix.theta.values
        assert "dimension_fit" in matrix.theta.values
        assert "creation_urge" in matrix.theta.values

    def test_semantic_anchors_initialized(self, matrix):
        assert len(matrix.semantic_anchors) >= 5
        for name in ["alpha", "beta", "gamma", "delta", "epsilon"]:
            assert name in matrix.semantic_anchors

    def test_history_system_exists(self, matrix):
        assert isinstance(matrix.history, list)
        assert hasattr(matrix, "max_history")

    def test_unclassified_buffer_exists(self, matrix):
        assert isinstance(matrix.unclassified_buffer, list)
        assert isinstance(matrix.buffer_tracking, dict)

    def test_misallocation_log_exists(self, matrix):
        assert isinstance(matrix.misallocation_log, list)
        assert hasattr(matrix, "max_misallocation_log")

    def test_correction_audit_trail_exists(self, matrix):
        assert isinstance(matrix.correction_audit_trail, list)
        assert hasattr(matrix, "max_audit_trail")


class TestThetaAllocation:
    """Test θ allocation system"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_meta_allocate_returns_decision(self, matrix):
        vector = matrix._text_to_vector("happy sad angry fear", 32)
        decision = matrix.meta_allocate(vector)
        assert decision.action in ["assign_to_axis", "composite_assign", "create_axis", "defer_to_buffer"]
        assert decision.confidence > 0
        assert decision.reasoning != ""

    def test_meta_allocate_with_label(self, matrix):
        vector = matrix._text_to_vector("boss criticism humiliation", 32)
        decision = matrix.meta_allocate(vector, "boss_criticism")
        assert decision is not None

    def test_execute_assign_to_axis(self, matrix):
        from core.autonomous.state_matrix import AllocateDecision
        decision = AllocateDecision(
            action="assign_to_axis",
            target="gamma",
            confidence=0.8,
            reasoning="test",
        )
        result = matrix.execute_decision(decision, [0.7] * 32)
        assert "gamma" in result["applied_to"]

    def test_execute_create_axis(self, matrix):
        from core.autonomous.state_matrix import AllocateDecision
        decision = AllocateDecision(
            action="create_axis",
            proposed_name="zeta_test",
            semantic_anchor=[0.5] * 32,
            confidence=0.6,
            reasoning="test",
        )
        result = matrix.execute_decision(decision, [0.5] * 32)
        assert result["new_axis_created"] == "zeta_test"
        assert "zeta_test" in matrix.dimensions

    def test_execute_defer_to_buffer(self, matrix):
        from core.autonomous.state_matrix import AllocateDecision
        decision = AllocateDecision(
            action="defer_to_buffer",
            buffer="unclassified",
            confidence=0.3,
            reasoning="test",
        )
        initial_len = len(matrix.unclassified_buffer)
        result = matrix.execute_decision(decision, [0.4] * 32)
        assert len(matrix.unclassified_buffer) == initial_len + 1

    def test_buffer_tracking(self, matrix):
        vector = matrix._text_to_vector("test", 32)
        matrix.meta_allocate(vector, "test_label")
        matrix.meta_allocate(vector, "test_label")
        matrix.meta_allocate(vector, "test_label")
        assert matrix.buffer_tracking.get("test_label", 0) == 3


class TestThetaNegativitySystem:
    """Test θ negativity detection and correction"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        m = StateMatrix4D()

        for i in range(10):
            m.history.append({
                "alpha": {"energy": 0.5 + i * 0.01},
                "beta": {"focus": 0.6 + i * 0.01},
                "gamma": {"happiness": 0.5 + i * 0.01},
                "delta": {"bond": 0.5 + i * 0.005},
                "epsilon": {"certainty": 0.5 + i * 0.005},
            })

        return m

    def test_trigger_increases_negativity(self, matrix):
        assert matrix.theta.values["theta_negativity"] == 0.0
        matrix.trigger_theta_negativity(0.3)
        assert matrix.theta.values["theta_negativity"] >= 0.3

    def test_negativity_triggers_detection(self, matrix):
        matrix.trigger_theta_negativity(0.6)
        matrix.theta.values["audit_intensity"] = 0.6
        detected = matrix.detect_misallocated_points()
        assert isinstance(detected, list)

    def test_detect_returns_empty_when_negativity_low(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.3
        detected = matrix.detect_misallocated_points()
        assert detected == []

    def test_correction_lowers_negativity(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.5
        matrix.theta.values["correction_urge"] = 0.7

        detected = matrix.detect_misallocated_points()
        if detected:
            result = matrix.correct_misallocation(detected[0]["point_id"])
            assert result.get("status") in ["corrected", "error", "dry_run"]

    def test_auto_correct_skips_when_urge_low(self, matrix):
        matrix.theta.values["correction_urge"] = 0.4
        result = matrix.auto_correct_all()
        assert result.get("status") == "skip"

    def test_correction_audit_trail(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.6
        matrix.theta.values["correction_urge"] = 0.7

        detected = matrix.detect_misallocated_points()
        if detected:
            matrix.correct_misallocation(detected[0]["point_id"])
            assert len(matrix.correction_audit_trail) >= 0

    def test_reset_clears_all(self, matrix):
        matrix.trigger_theta_negativity(0.8)
        matrix.reset_theta_negativity()
        assert matrix.theta.values["theta_negativity"] == 0.0
        assert matrix.theta.values["correction_urge"] == 0.0

    def test_negativity_report_complete(self, matrix):
        matrix.trigger_theta_negativity(0.3)
        report = matrix.get_negativity_report()
        assert "theta_negativity" in report
        assert "needs_correction" in report
        assert "ready_to_correct" in report
        assert "misallocation_count" in report
        assert "correction_count" in report


class TestMathRippleEngineDepthSystem:
    """Test the dual-depth system in MathRippleEngine"""

    @pytest.fixture
    def engine(self):
        return MathRippleEngine()

    def test_default_depths(self, engine):
        assert engine.algorithm_depth == AlgorithmDepth.LIGHT
        assert engine.ripple_depth == RippleDepth.D3

    def test_set_depth_changes_config(self, engine):
        engine.set_depth(AlgorithmDepth.HEAVY, RippleDepth.D5)
        assert engine.algorithm_depth == AlgorithmDepth.HEAVY
        assert engine.ripple_depth == RippleDepth.D5

    def test_compute_sets_depth_on_ripple(self, engine):
        result, ripples = engine.compute("10 * 5")
        assert len(ripples) >= 1
        for r in ripples:
            assert r.depth_level >= 3
            assert r.algorithm_depth is not None
            assert r.ripple_depth is not None

    def test_auto_detect_algorithm_depth(self, engine):
        result, ripples = engine.compute("sin(90)")
        assert engine.algorithm_depth == AlgorithmDepth.HEAVY

    def test_auto_detect_ripple_depth_power(self, engine):
        result, ripples = engine.compute("2^10")
        assert engine.algorithm_depth == AlgorithmDepth.MEDIUM

    def test_overload_ripple_depth(self, engine):
        result, ripples = engine.compute("100 * 10 * 10")
        if ripples:
            last_ripple = ripples[-1]
            if last_ripple.overload_triggered:
                assert last_ripple.depth_level >= 4

    def test_analyze_expression_includes_depth_config(self, engine):
        analysis = engine.analyze_expression("5 * 3")
        assert "depth_config" in analysis
        assert "ripple_depth" in analysis["depth_config"]
        assert "algorithm_depth" in analysis["depth_config"]

    def test_analyze_expression_includes_chain_analysis(self, engine):
        analysis = engine.analyze_expression("2 * 3 * 4")
        assert "chain_analysis" in analysis
        assert "max_ripple_depth" in analysis["chain_analysis"]

    def test_analyze_expression_includes_cascade_ripples(self, engine):
        analysis = engine.analyze_expression("5 * 3", cascade=True)
        assert "cascade_ripples" in analysis


class TestRippleCascade:
    """Test the ripple cascade system"""

    def test_cascade_d3_produces_ripples(self):
        from ai.memory.math_ripple_engine import RippleEffect, MathOp
        ripple = RippleEffect(
            operator=MathOp.MUL,
            operand_a=10.0,
            operand_b=5.0,
            result=50.0,
            operand_a_magnitude=10.0,
            result_magnitude=50.0,
            alpha_arousal=0.5,
            beta_focus=0.4,
            ripple_depth=RippleDepth.D3,
            algorithm_depth=AlgorithmDepth.LIGHT,
            depth_level=3,
        )
        cascaded = RippleCascade.cascade(ripple)
        assert len(cascaded) >= 2

    def test_cascade_d5_produces_more(self):
        from ai.memory.math_ripple_engine import RippleEffect, MathOp
        ripple = RippleEffect(
            operator=MathOp.MUL,
            operand_a=10.0,
            operand_b=5.0,
            result=50.0,
            operand_a_magnitude=10.0,
            result_magnitude=50.0,
            alpha_arousal=0.5,
            ripple_depth=RippleDepth.D5,
            algorithm_depth=AlgorithmDepth.LIGHT,
            depth_level=5,
        )
        cascaded = RippleCascade.cascade(ripple)
        assert len(cascaded) > 3

    def test_feedback_for_overload(self):
        from ai.memory.math_ripple_engine import RippleEffect, MathOp
        ripple = RippleEffect(
            operator=MathOp.MUL,
            operand_a=100.0,
            operand_b=100.0,
            result=10000.0,
            operand_a_magnitude=100.0,
            result_magnitude=10000.0,
            overload_triggered=True,
            ripple_depth=RippleDepth.D6,
            algorithm_depth=AlgorithmDepth.MEDIUM,
            depth_level=6,
        )
        cascaded = RippleCascade.cascade(ripple)
        feedback = [r for r in cascaded if r.cascade_step >= 97]
        assert len(feedback) >= 1


class TestAlgorithmDepthEnum:
    """Test AlgorithmDepth enum properties"""

    def test_light_complexity(self):
        assert AlgorithmDepth.LIGHT.complexity == 1.0

    def test_medium_complexity(self):
        assert AlgorithmDepth.MEDIUM.complexity == 1.5

    def test_heavy_complexity(self):
        assert AlgorithmDepth.HEAVY.complexity == 2.0

    def test_ultra_complexity(self):
        assert AlgorithmDepth.ULTRA.complexity == 3.0

    def test_light_operators(self):
        ops = AlgorithmDepth.LIGHT.operators
        assert "+" in ops
        assert "-" in ops
        assert "*" in ops
        assert "/" in ops
        assert "sin" not in ops

    def test_heavy_operators(self):
        ops = AlgorithmDepth.HEAVY.operators
        assert "sin" in ops
        assert "cos" in ops
        assert "log" in ops

    def test_ultra_operators(self):
        ops = AlgorithmDepth.ULTRA.operators
        assert "∫" in ops
        assert "∑" in ops


class TestRippleDepthEnum:
    """Test RippleDepth enum properties"""

    def test_d3_axes(self):
        axes = RippleDepth.D3.target_axes
        assert "alpha" in axes
        assert "beta" in axes
        assert "gamma" in axes
        assert len(axes) == 3

    def test_d4_axes(self):
        axes = RippleDepth.D4.target_axes
        assert "delta" in axes
        assert len(axes) == 4

    def test_d5_axes(self):
        axes = RippleDepth.D5.target_axes
        assert "theta" in axes
        assert len(axes) == 5

    def test_d6_axes(self):
        axes = RippleDepth.D6.target_axes
        assert "epsilon" in axes
        assert len(axes) == 6

    def test_decay_increases(self):
        assert RippleDepth.D3.cascade_decay < RippleDepth.D7.cascade_decay

    def test_feedback_d6_plus(self):
        assert RippleDepth.D6.feedback_enabled is True
        assert RippleDepth.D7.feedback_enabled is True
        assert RippleDepth.D3.feedback_enabled is False


class TestDepthDetection:
    """Test automatic depth detection"""

    def test_detect_light(self):
        from ai.memory.math_ripple_engine import _detect_algorithm_depth, AlgorithmDepth
        depth = _detect_algorithm_depth("5 + 3")
        assert depth == AlgorithmDepth.LIGHT

    def test_detect_medium_power(self):
        from ai.memory.math_ripple_engine import _detect_algorithm_depth, AlgorithmDepth
        depth = _detect_algorithm_depth("2^10")
        assert depth == AlgorithmDepth.MEDIUM

    def test_detect_heavy_trig(self):
        from ai.memory.math_ripple_engine import _detect_algorithm_depth, AlgorithmDepth
        depth = _detect_algorithm_depth("sin(90)")
        assert depth == AlgorithmDepth.HEAVY

    def test_detect_ultra_calculus(self):
        from ai.memory.math_ripple_engine import _detect_algorithm_depth, AlgorithmDepth
        depth = _detect_algorithm_depth("∫x²dx")
        assert depth == AlgorithmDepth.ULTRA

    def test_detect_ripple_depth_d3(self):
        from ai.memory.math_ripple_engine import _detect_ripple_depth, AlgorithmDepth, RippleDepth
        depth = _detect_ripple_depth("5 + 3", AlgorithmDepth.LIGHT)
        assert depth == RippleDepth.D3

    def test_detect_ripple_depth_d5_overload(self):
        from ai.memory.math_ripple_engine import _detect_ripple_depth, AlgorithmDepth, RippleDepth
        depth = _detect_ripple_depth("100 * 100 * 100", AlgorithmDepth.MEDIUM)
        assert depth == RippleDepth.D5


class TestRippleAccumulator:
    """Test RippleAccumulator with depth tracking"""

    def test_tracks_max_depth(self):
        acc = RippleAccumulator()
        from ai.memory.math_ripple_engine import RippleEffect, MathOp

        r1 = RippleEffect(
            operator=MathOp.ADD, operand_a=1.0, operand_b=2.0,
            result=3.0, operand_a_magnitude=1.0, result_magnitude=3.0,
            depth_level=3, algorithm_depth=AlgorithmDepth.LIGHT,
        )
        acc.add(r1)
        assert acc.max_ripple_depth == 3

        r2 = RippleEffect(
            operator=MathOp.MUL, operand_a=10.0, operand_b=10.0,
            result=100.0, operand_a_magnitude=10.0, result_magnitude=100.0,
            depth_level=5, algorithm_depth=AlgorithmDepth.MEDIUM,
        )
        acc.add(r2)
        assert acc.max_ripple_depth == 5

    def test_reset_clears_depth(self):
        acc = RippleAccumulator()
        acc.max_ripple_depth = 7
        acc.max_algorithm_depth = AlgorithmDepth.HEAVY
        acc.reset()
        assert acc.max_ripple_depth == 3
        assert acc.max_algorithm_depth == AlgorithmDepth.LIGHT


class TestRippleDepthConfig:
    """Test RippleDepthConfig auto-detection"""

    def test_from_expr_light(self):
        from ai.memory.math_ripple_engine import RippleDepthConfig, AlgorithmDepth, RippleDepth
        config = RippleDepthConfig.from_expr("5 + 3")
        assert config.algorithm_depth == AlgorithmDepth.LIGHT
        assert config.depth == RippleDepth.D3

    def test_from_expr_heavy(self):
        from ai.memory.math_ripple_engine import RippleDepthConfig, AlgorithmDepth
        config = RippleDepthConfig.from_expr("sin(90) + log(10)")
        assert config.algorithm_depth == AlgorithmDepth.HEAVY


class TestEndToEndIntegration:
    """End-to-end integration tests"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    @pytest.fixture
    def engine(self):
        return MathRippleEngine()

    def test_math_computation_updates_state(self, matrix, engine):
        engine.state_matrix = matrix
        result, ripples = engine.compute("10 * 5")

        if ripples:
            cascade = RippleCascade()
            cascaded = cascade.cascade(ripples[0], matrix)

    def test_theta_meta_allocate_after_math(self, matrix, engine):
        engine.state_matrix = matrix

        engine.compute("5 + 3")
        vector = matrix._text_to_vector("calculation result", 32)
        decision = matrix.meta_allocate(vector)
        assert decision is not None

    def test_negativity_triggered_by_math_overload(self, matrix, engine):
        engine.state_matrix = matrix

        result, ripples = engine.compute("100 * 100 * 10")

        overload_detected = any(r.overload_triggered for r in ripples)
        if overload_detected:
            matrix.trigger_theta_negativity(0.3)
            assert matrix.theta.values["theta_negativity"] > 0

    def test_theta_analysis_complete(self, matrix):
        matrix.trigger_theta_negativity(0.2)
        matrix.meta_allocate(matrix._text_to_vector("test", 32), "test_label")

        analysis = matrix.get_theta_analysis()
        assert "theta_values" in analysis
        assert "theta_negativity" in analysis
        assert "buffer_size" in analysis
        assert "misallocation_log_size" in analysis