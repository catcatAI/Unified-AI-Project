"""
Test suite for MathRippleEngine
测试 数学-认知同构引擎

测试场景：
1. 四则运算基础计算
2. 跨轴漣漪产生（加/减/乘/除）
3. 端點行為（過載/恐懼/混淆）
4. 連續運算鏈分析
5. 認知語義分析
"""

import math

import pytest
from ai.memory.math_ripple_engine import MathOp, MathRippleEngine, RippleAccumulator, RippleEffect


class TestMathRippleEngine:
    """MathRippleEngine 测试类"""

    @pytest.fixture
    def engine(self):
        return MathRippleEngine()

    def test_addition_simple(self, engine):
        result, ripples = engine.compute("3 + 5")
        assert abs(result - 8.0) < 0.001
        assert len(ripples) >= 1
        r = ripples[0]
        assert r.operator == MathOp.ADD
        assert r.operand_a == 3.0
        assert r.operand_b == 5.0

    def test_subtraction_non_commutative(self, engine):
        result, ripples = engine.compute("10 - 3")
        assert abs(result - 7.0) < 0.001
        assert len(ripples) >= 1

        result2, _ = engine.compute("3 - 10")
        assert abs(result2 - (-7.0)) < 0.001

    def test_multiplication_amplify(self, engine):
        result, ripples = engine.compute("100 * 3")
        assert abs(result - 300.0) < 0.001
        r = ripples[0]
        assert r.alpha_arousal > 0
        assert r.beta_focus > 0

    def test_division_near_zero(self, engine):
        result, ripples = engine.compute("5 / 0.001")
        r = ripples[0]
        assert r.fear_triggered is False
        assert r.result_magnitude > 1000

        result2, ripples2 = engine.compute("5 / 0.0001")
        r2 = ripples2[0]
        assert r2.fear_triggered is True

    def test_overload_chain(self, engine):
        result, ripples = engine.compute("100 * 3 * 2 * 5")
        assert abs(result - 3000.0) < 0.001
        has_overload = any(r.overload_triggered for r in ripples)
        assert has_overload is True

    def test_single_operation_compute(self, engine):
        result, ripple = engine._compute_single(10.0, "*", 20.0)
        assert abs(result - 200.0) < 0.001
        assert ripple.alpha_arousal > 0
        assert ripple.beta_focus > 0
        assert ripple.result_magnitude == 200.0

    def test_divide_by_zero(self, engine):
        result, ripple = engine._compute_single(10.0, "/", 0.0)
        assert math.isinf(result)
        assert ripple.fear_triggered is True

    def test_power_operation(self, engine):
        result, ripple = engine._compute_single(2.0, "**", 10.0)
        assert abs(result - 1024.0) < 0.001
        assert ripple.epsilon_delta > 0

    def test_tokenize(self, engine):
        tokens = engine._tokenize("10 + 5 * 3")
        assert "10" in tokens
        assert "+" in tokens

    def test_analyze_expression(self, engine):
        analysis = engine.analyze_expression("100 * 3 * 2")
        assert analysis["result"] is not None
        assert len(analysis["ripples"]) >= 2
        assert analysis["chain_analysis"]["total_operations"] >= 2

    def test_cumulative_effects(self, engine):
        accumulator = RippleAccumulator()
        engine_acc = MathRippleEngine(ripple_accumulator=accumulator)

        result, ripples = engine_acc.compute("10 * 5")
        assert accumulator.cumulative_epsilon > 0
        assert accumulator.cumulative_arousal > 0
        assert len(accumulator.total_ripples) >= 1

    def test_negative_numbers(self, engine):
        result, ripple = engine._compute_single(-5.0, "*", 3.0)
        assert abs(result - (-15.0)) < 0.001

    def test_division_positive_result(self, engine):
        result, ripple = engine._compute_single(20.0, "/", 4.0)
        assert abs(result - 5.0) < 0.001
        assert ripple.description != ""

    def test_sqrt_scenario(self, engine):
        result, ripple = engine._compute_single(4.0, "^", 0.5)
        assert abs(result - 2.0) < 0.1


class TestRippleAccumulator:
    """RippleAccumulator 测试类"""

    def test_add_ripple(self):
        acc = RippleAccumulator()
        ripple = RippleEffect(
            operator=MathOp.MUL,
            operand_a=10.0,
            operand_b=5.0,
            result=50.0,
            operand_a_magnitude=10.0,
            result_magnitude=50.0,
            epsilon_delta=0.5,
            alpha_arousal=0.3,
            gamma_excitement=0.2,
        )
        acc.add(ripple)
        assert len(acc.total_ripples) == 1
        assert acc.cumulative_epsilon > 0
        assert acc.fatigue > 0

    def test_fatigue_accumulation(self):
        acc = RippleAccumulator()
        for i in range(5):
            ripple = RippleEffect(
                operator=MathOp.ADD,
                operand_a=float(i),
                operand_b=1.0,
                result=float(i + 1),
                operand_a_magnitude=float(i),
                result_magnitude=float(i + 1),
            )
            acc.add(ripple)
        assert acc.fatigue > 0

    def test_reset(self):
        acc = RippleAccumulator()
        acc.cumulative_epsilon = 1.0
        acc.chain_broken = True
        acc.reset()
        assert acc.cumulative_epsilon == 0.0
        assert acc.chain_broken is False

    def test_chain_broken_flag(self):
        acc = RippleAccumulator()
        acc.chain_broken_by(MathOp.DIV)
        assert acc.chain_broken is True


# =============================================================================
# 漣漪深度 × 演算法深度 系統測試
# =============================================================================

from ai.memory.math_ripple_engine import (
    AlgorithmDepth,
    MathOp,
    RippleCascade,
    RippleDepth,
    RippleDepthConfig,
    RippleEffect,
    _detect_algorithm_depth,
    _detect_ripple_depth,
    _estimate_result_magnitude,
)


class TestAlgorithmDepth:
    """演算法啟用深度測試"""

    def test_light_operators(self):
        algo = AlgorithmDepth.LIGHT
        assert "+" in algo.operators
        assert "-" in algo.operators
        assert "*" in algo.operators
        assert "/" in algo.operators
        assert "sin" not in algo.operators

    def test_medium_includes_power(self):
        algo = AlgorithmDepth.MEDIUM
        assert "^" in algo.operators
        assert "sqrt" in algo.operators
        assert "sin" not in algo.operators

    def test_heavy_includes_trig(self):
        algo = AlgorithmDepth.HEAVY
        assert "sin" in algo.operators
        assert "cos" in algo.operators
        assert "log" in algo.operators

    def test_ultra_includes_calculus(self):
        algo = AlgorithmDepth.ULTRA
        assert "∫" in algo.operators
        assert "∑" in algo.operators

    def test_complexity_ranking(self):
        assert AlgorithmDepth.LIGHT.complexity < AlgorithmDepth.MEDIUM.complexity
        assert AlgorithmDepth.MEDIUM.complexity < AlgorithmDepth.HEAVY.complexity
        assert AlgorithmDepth.HEAVY.complexity < AlgorithmDepth.ULTRA.complexity


class TestRippleDepth:
    """漣漪深度測試"""

    def test_d3_targets_three_axes(self):
        depth = RippleDepth.D3
        assert depth.value == 3
        assert "alpha" in depth.target_axes
        assert "beta" in depth.target_axes
        assert "gamma" in depth.target_axes
        assert len(depth.target_axes) == 3

    def test_d4_adds_delta(self):
        depth = RippleDepth.D4
        assert "delta" in depth.target_axes
        assert len(depth.target_axes) == 4

    def test_d5_adds_theta(self):
        depth = RippleDepth.D5
        assert "theta" in depth.target_axes
        assert len(depth.target_axes) == 5

    def test_d6_includes_epsilon(self):
        depth = RippleDepth.D6
        assert "epsilon" in depth.target_axes

    def test_decay_increases_with_depth(self):
        assert RippleDepth.D3.cascade_decay < RippleDepth.D7.cascade_decay

    def test_feedback_enabled_only_d6_plus(self):
        assert RippleDepth.D3.feedback_enabled is False
        assert RippleDepth.D5.feedback_enabled is False
        assert RippleDepth.D6.feedback_enabled is True
        assert RippleDepth.D7.feedback_enabled is True


class TestDepthDetection:
    """深度自動檢測測試"""

    def test_detect_light_from_simple_expression(self):
        depth = _detect_algorithm_depth("10 + 5")
        assert depth == AlgorithmDepth.LIGHT

    def test_detect_medium_from_power(self):
        depth = _detect_algorithm_depth("2^10")
        assert depth == AlgorithmDepth.MEDIUM

    def test_detect_medium_from_sqrt(self):
        depth = _detect_algorithm_depth("sqrt(16)")
        assert depth == AlgorithmDepth.MEDIUM

    def test_detect_heavy_from_trig(self):
        depth = _detect_algorithm_depth("sin(90)")
        assert depth == AlgorithmDepth.HEAVY

    def test_detect_heavy_from_log(self):
        depth = _detect_algorithm_depth("log(100)")
        assert depth == AlgorithmDepth.HEAVY

    def test_detect_ultra_from_calculus_keywords(self):
        depth = _detect_algorithm_depth("積分 sin(x)")
        assert depth == AlgorithmDepth.ULTRA

    def test_detect_ultra_from_integral_symbol(self):
        depth = _detect_algorithm_depth("∫x²dx")
        assert depth == AlgorithmDepth.ULTRA

    def test_detect_ripple_depth_d3_for_simple(self):
        algo = AlgorithmDepth.LIGHT
        depth = _detect_ripple_depth("5 + 3", algo)
        assert depth == RippleDepth.D3

    def test_detect_ripple_depth_d4_for_multiplication(self):
        algo = AlgorithmDepth.LIGHT
        depth = _detect_ripple_depth("10 * 5 * 3", algo)
        assert depth == RippleDepth.D4

    def test_detect_ripple_depth_d5_for_overload(self):
        algo = AlgorithmDepth.MEDIUM
        depth = _detect_ripple_depth("100 * 100 * 100", algo)
        assert depth == RippleDepth.D5

    def test_estimate_magnitude_simple(self):
        mag = _estimate_result_magnitude("10 + 5")
        assert 0 < mag < 100

    def test_estimate_magnitude_multiplication(self):
        mag = _estimate_result_magnitude("10 * 5 * 3")
        assert mag > 100


class TestRippleDepthConfig:
    """RippleDepthConfig 測試"""

    def test_from_expr_auto_detects_light(self):
        config = RippleDepthConfig.from_expr("5 + 3")
        assert config.algorithm_depth == AlgorithmDepth.LIGHT
        assert config.depth == RippleDepth.D3

    def test_from_expr_auto_detects_heavy(self):
        config = RippleDepthConfig.from_expr("sin(90) + log(10)")
        assert config.algorithm_depth == AlgorithmDepth.HEAVY


class TestRippleCascade:
    """RippleCascade 級聯引擎測試"""

    def test_cascade_d3_produces_secondary_ripples(self):
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

    def test_cascade_d5_produces_more_ripples(self):
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

    def test_cascade_decay_decreases_per_step(self):
        ripple = RippleEffect(
            operator=MathOp.MUL,
            operand_a=10.0,
            operand_b=5.0,
            result=50.0,
            operand_a_magnitude=10.0,
            result_magnitude=50.0,
            ripple_depth=RippleDepth.D5,
            algorithm_depth=AlgorithmDepth.LIGHT,
            depth_level=5,
        )
        cascaded = RippleCascade.cascade(ripple)
        decays = [r.cascade_decay_factor for r in cascaded if r.cascade_step > 0]
        for i in range(len(decays) - 1):
            assert decays[i] > decays[i + 1]

    def test_feedback_generated_for_overload(self):
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

    def test_feedback_generated_for_fear(self):
        ripple = RippleEffect(
            operator=MathOp.DIV,
            operand_a=5.0,
            operand_b=0.0,
            result=0.0,
            operand_a_magnitude=5.0,
            result_magnitude=0.0,
            fear_triggered=True,
            ripple_depth=RippleDepth.D6,
            algorithm_depth=AlgorithmDepth.LIGHT,
            depth_level=6,
        )
        cascaded = RippleCascade.cascade(ripple)
        feedback = [r for r in cascaded if r.cascade_step >= 98]
        assert len(feedback) >= 1


class TestEngineDepthIntegration:
    """MathRippleEngine 深度整合測試"""

    @pytest.fixture
    def engine(self):
        return MathRippleEngine()

    def test_default_depth_is_light_d3(self, engine):
        assert engine.algorithm_depth == AlgorithmDepth.LIGHT
        assert engine.ripple_depth == RippleDepth.D3

    def test_set_depth_changes_config(self, engine):
        engine.set_depth(AlgorithmDepth.HEAVY, RippleDepth.D5)
        assert engine.algorithm_depth == AlgorithmDepth.HEAVY
        assert engine.ripple_depth == RippleDepth.D5

    def test_auto_detect_upgrades_depth_for_trig(self, engine):
        result, ripples = engine.compute("sin(90)", auto_detect=True)
        assert engine.algorithm_depth == AlgorithmDepth.HEAVY

    def test_auto_detect_upgrades_depth_for_power(self, engine):
        result, ripples = engine.compute("2^10", auto_detect=True)
        assert engine.algorithm_depth == AlgorithmDepth.MEDIUM

    def test_force_depth_overrides_auto_detect(self, engine):
        result, ripples = engine.compute("5 + 3", auto_detect=True, force_depth=RippleDepth.D6)
        assert engine.ripple_depth == RippleDepth.D6

    def test_analyze_expression_includes_depth_config(self, engine):
        analysis = engine.analyze_expression("100 * 5")
        assert "depth_config" in analysis
        assert "ripple_depth" in analysis["depth_config"]
        assert "algorithm_depth" in analysis["depth_config"]

    def test_analyze_expression_includes_cascade_ripples(self, engine):
        analysis = engine.analyze_expression("100 * 5", cascade=True)
        assert "cascade_ripples" in analysis
        assert "depth_config" in analysis

    def test_depth_level_set_on_ripple(self, engine):
        result, ripples = engine.compute("10 * 5")
        for r in ripples:
            assert r.depth_level >= 3
            assert r.algorithm_depth is not None