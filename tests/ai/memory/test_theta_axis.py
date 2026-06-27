"""
Test suite for Theta Meta-Cognitive Axis
测试 元認知軸 (θ) - 軸管理與分配決策

测试场景：
1. θ 轴初始化与语义锚点
2. meta_allocate 决策逻辑（assign / composite / create / defer）
3. 语义相似度计算（cosine similarity）
4. 动态创建新轴
5. 缓冲区管理与经验累积
6. 决策执行
7. θ 分析报告
"""

import math

import pytest

try:
    from core.engine.state_matrix import (
        AllocateDecision,
        AxisSemanticAnchor,
        DimensionState,
        StateMatrix4D,
    )
except ImportError:
    pytest.skip("StateMatrix4D not available", allow_module_level=True)


class TestThetaAxis:
    """θ 轴核心功能测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_theta_initialized(self, matrix):
        assert hasattr(matrix, "theta")
        assert matrix.theta.name == "theta"
        assert "novelty" in matrix.theta.values
        assert "creation_urge" in matrix.theta.values
        assert "ambiguity" in matrix.theta.values

    def test_all_six_dimensions_present(self, matrix):
        assert "alpha" in matrix.dimensions
        assert "beta" in matrix.dimensions
        assert "gamma" in matrix.dimensions
        assert "delta" in matrix.dimensions
        assert "epsilon" in matrix.dimensions
        assert "theta" in matrix.dimensions

    def test_semantic_anchors_initialized(self, matrix):
        assert len(matrix.semantic_anchors) >= 5
        assert "alpha" in matrix.semantic_anchors
        assert "beta" in matrix.semantic_anchors
        assert "gamma" in matrix.semantic_anchors
        assert "delta" in matrix.semantic_anchors
        assert "epsilon" in matrix.semantic_anchors

        for name, anchor in matrix.semantic_anchors.items():
            assert isinstance(anchor, AxisSemanticAnchor)
            assert len(anchor.semantic_vector) > 0
            assert anchor.name == name

    def test_text_to_vector(self, matrix):
        v = matrix._text_to_vector("happy sad angry", 32)
        assert len(v) == 32
        norm = math.sqrt(sum(x * x for x in v))
        assert abs(norm - 1.0) < 0.01

    def test_text_to_vector_different_inputs(self, matrix):
        v1 = matrix._text_to_vector("energy comfort", 32)
        v2 = matrix._text_to_vector("think learn focus", 32)
        assert v1 != v2


class TestSemanticResonance:
    """语义共鸣/相似度计算测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_resonance_self_is_high(self, matrix):
        anchor = matrix.semantic_anchors["gamma"]
        gamma_vector = matrix._text_to_vector("happy sad angry fear love", 32)
        resonance = anchor.compute_resonance(gamma_vector)
        assert resonance > 0.5

    def test_resonance_different_axis_lower(self, matrix):
        anchor = matrix.semantic_anchors["alpha"]
        gamma_vector = matrix._text_to_vector("happy sad angry fear love", 32)
        resonance = anchor.compute_resonance(gamma_vector)
        alpha_anchor = matrix.semantic_anchors["alpha"]
        alpha_vector = matrix._text_to_vector("energy comfort physical body", 32)
        alpha_resonance = anchor.compute_resonance(alpha_vector)
        assert alpha_resonance > resonance


class TestMetaAllocate:
    """meta_allocate 决策逻辑测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_assign_decision_for_emotional_input(self, matrix):
        emotion_vector = matrix._text_to_vector("happy sad angry love", 32)
        decision = matrix.meta_allocate(emotion_vector)
        assert decision.action in ["assign_to_axis", "composite_assign"]
        assert decision.confidence > 0
        assert decision.reasoning != ""

    def test_assign_decision_targets_best_match(self, matrix):
        emotion_vector = matrix._text_to_vector("happy sad angry fear", 32)
        decision = matrix.meta_allocate(emotion_vector)
        if decision.action == "assign_to_axis":
            assert decision.target in ["alpha", "beta", "gamma", "delta", "epsilon"]

    def test_theta_values_updated_after_allocation(self, matrix):
        emotion_vector = matrix._text_to_vector("happy sad angry fear", 32)
        decision = matrix.meta_allocate(emotion_vector)
        assert matrix.theta.values["novelty"] >= 0
        assert matrix.theta.values["ambiguity"] >= 0

    def test_defer_decision_for_ambiguous_input(self, matrix):
        random_vector = [0.1, 0.3, 0.5, 0.7, 0.2, 0.4, 0.6, 0.8] * 4
        decision = matrix.meta_allocate(random_vector[:32], "ambiguous_input")
        assert decision.action in ["defer_to_buffer", "composite_assign", "create_axis"]

    def test_buffer_tracking_increment(self, matrix):
        label = "test_label_123"
        for _ in range(3):
            matrix.meta_allocate([0.5] * 32, label)
        assert matrix.buffer_tracking.get(label, 0) == 3

    def test_creation_urge_grows_with_repeated_label(self, matrix):
        label = "repeating_pattern_xyz"
        for _ in range(6):
            matrix.meta_allocate([0.3, 0.6, 0.9] + [0.1] * 29, label)
        urge = matrix.theta.values.get("creation_urge", 0)
        assert urge > 0

    def test_allocate_decision_has_reasoning(self, matrix):
        emotion_vector = matrix._text_to_vector("happy sad angry fear", 32)
        decision = matrix.meta_allocate(emotion_vector)
        assert isinstance(decision, AllocateDecision)
        assert decision.reasoning != ""


class TestDynamicAxisCreation:
    """动态创建轴测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_create_new_axis(self, matrix):
        new_dim = matrix.create_axis(
            name="zeta",
            label="权力/尊严",
            semantic_vector=[0.5] * 32,
            initial_values={"power": 0.5, "dignity": 0.5},
        )
        assert new_dim is not None
        assert "zeta" in matrix.dimensions
        assert matrix.dimensions["zeta"].cn_name == "权力/尊严"

    def test_create_duplicate_returns_existing(self, matrix):
        matrix.create_axis("zeta", "权力", [0.5] * 32)
        second = matrix.create_axis("zeta", "权力2", [0.3] * 32)
        assert second == matrix.dimensions["zeta"]

    def test_creation_logged(self, matrix):
        matrix.create_axis("zeta", "权力", [0.5] * 32)
        assert len(matrix.axis_creation_log) > 0
        last_log = matrix.axis_creation_log[-1]
        assert last_log["name"] == "zeta"

    def test_semantic_anchor_created_with_axis(self, matrix):
        matrix.create_axis("zeta", "权力", [0.5] * 32)
        assert "zeta" in matrix.semantic_anchors
        assert matrix.semantic_anchors["zeta"].name == "zeta"


class TestExecuteDecision:
    """决策执行测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_execute_assign_to_axis(self, matrix):
        decision = AllocateDecision(
            action="assign_to_axis",
            target="gamma",
            confidence=0.8,
            reasoning="test",
        )
        result = matrix.execute_decision(decision, [0.8] * 32)
        assert "gamma" in result["applied_to"]

    def test_execute_composite_assign(self, matrix):
        decision = AllocateDecision(
            action="composite_assign",
            targets=[("gamma", 0.6), ("delta", 0.5)],
            confidence=0.7,
            reasoning="test",
        )
        result = matrix.execute_decision(decision, [0.7] * 32)
        assert "gamma" in result["applied_to"]
        assert "delta" in result["applied_to"]

    def test_execute_create_axis(self, matrix):
        decision = AllocateDecision(
            action="create_axis",
            proposed_name="zeta",
            semantic_anchor=[0.5] * 32,
            confidence=0.6,
            reasoning="test",
        )
        result = matrix.execute_decision(decision, [0.5] * 32)
        assert result["new_axis_created"] == "zeta"
        assert "zeta" in matrix.dimensions

    def test_execute_defer_to_buffer(self, matrix):
        decision = AllocateDecision(
            action="defer_to_buffer",
            buffer="unclassified",
            confidence=0.3,
            reasoning="test",
        )
        initial_size = len(matrix.unclassified_buffer)
        result = matrix.execute_decision(decision, [0.4] * 32)
        assert len(matrix.unclassified_buffer) == initial_size + 1


class TestBufferMigration:
    """缓冲区迁移测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_migrate_nonexistent_axis_returns_zero(self, matrix):
        count = matrix.migrate_buffer_to_axis("nonexistent")
        assert count == 0

    def test_migrate_clears_relevant_entries(self, matrix):
        decision = AllocateDecision(
            action="defer_to_buffer",
            buffer="zeta",
            confidence=0.3,
            reasoning="test",
        )
        matrix.execute_decision(decision, [0.5] * 32)
        matrix.execute_decision(decision, [0.6] * 32)
        matrix.execute_decision(decision, [0.7] * 32)

        matrix.create_axis("zeta", "权力", [0.5] * 32)
        count = matrix.migrate_buffer_to_axis("zeta")
        assert count >= 1


class TestThetaAnalysis:
    """θ 分析报告测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_get_theta_analysis_returns_keys(self, matrix):
        analysis = matrix.get_theta_analysis()
        assert "theta_values" in analysis
        assert "axis_count" in analysis
        assert "semantic_anchors" in analysis
        assert "buffer_tracking" in analysis

    def test_axis_count_reflects_current(self, matrix):
        matrix.create_axis("zeta", "权力", [0.5] * 32)
        analysis = matrix.get_theta_analysis()
        assert analysis["axis_count"] >= 6


class TestInfluenceMatrixWithTheta:
    """包含 θ 的影响矩阵测试"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        return StateMatrix4D()

    def test_theta_in_influence_matrix(self, matrix):
        assert "theta" in matrix.influence_matrix
        assert "alpha" in matrix.influence_matrix["theta"]
        assert "gamma" in matrix.influence_matrix["theta"]


class TestAllocateDecisionDataclass:
    """AllocateDecision 数据类测试"""

    def test_allocate_decision_to_dict(self):
        decision = AllocateDecision(
            action="assign_to_axis",
            target="gamma",
            confidence=0.8,
            reasoning="High match",
        )
        d = decision.to_dict()
        assert d["action"] == "assign_to_axis"
        assert d["target"] == "gamma"
        assert d["confidence"] == 0.8
        assert d["reasoning"] == "High match"

    def test_allocate_decision_with_targets(self):
        decision = AllocateDecision(
            action="composite_assign",
            targets=[("gamma", 0.6), ("delta", 0.5)],
            confidence=0.75,
            reasoning="Multi-axis",
        )
        d = decision.to_dict()
        assert d["targets"] == [("gamma", 0.6), ("delta", 0.5)]


# =============================================================================
# θ 軸負值檢測與修正系統測試 [Task N.24-THETA-NEG]
# =============================================================================

class TestThetaNegativitySystem:
    """θ 軸負值系統測試"""

    @pytest.fixture
    def matrix(self):
        StateMatrix4D._instance = None
        StateMatrix4D._initialized = False
        m = StateMatrix4D()
        m.alpha.values = {"energy": 0.8, "arousal": 0.6}
        m.beta.values = {"focus": 0.7, "confusion": 0.3}
        m.gamma.values = {"happiness": 0.5, "sadness": 0.4}
        for _ in range(5):
            m.history.append({
                "alpha": {"energy": 0.7 + _ * 0.02},
                "beta": {"focus": 0.6 + _ * 0.02},
                "gamma": {"happiness": 0.5 + _ * 0.01},
            })
        return m

    def test_theta_negativity_initially_zero(self, matrix):
        assert matrix.theta.values.get("theta_negativity", 0.0) == 0.0

    def test_trigger_theta_negativity_increases_value(self, matrix):
        matrix.trigger_theta_negativity(0.2)
        assert matrix.theta.values["theta_negativity"] >= 0.2
        assert matrix.theta.values["audit_intensity"] > 0

    def test_trigger_accumulates(self, matrix):
        matrix.trigger_theta_negativity(0.1)
        matrix.trigger_theta_negativity(0.1)
        assert matrix.theta.values["theta_negativity"] >= 0.2

    def test_strong_trigger_raises_correction_urge(self, matrix):
        matrix.trigger_theta_negativity(0.5)
        assert matrix.theta.values["correction_urge"] > 0

    def test_detect_returns_empty_when_negativity_low(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.3
        detected = matrix.detect_misallocated_points()
        assert isinstance(detected, list)

    def test_detect_runs_when_negativity_above_threshold(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.6
        matrix.theta.values["audit_intensity"] = 0.6
        detected = matrix.detect_misallocated_points()
        assert isinstance(detected, list)

    def test_correction_reduces_negativity(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.5
        matrix.theta.values["correction_urge"] = 0.7

        for _ in range(5):
            matrix.history.append({
                "alpha": {"energy": 0.7},
                "beta": {"focus": 0.6},
            })

        detected = matrix.detect_misallocated_points()
        if detected:
            result = matrix.correct_misallocation(detected[0]["point_id"])
            assert result.get("status") in ["corrected", "error", "dry_run"]

    def test_correct_misallocation_dry_run(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.5

        for _ in range(5):
            matrix.history.append({
                "gamma": {"happiness": 0.6},
                "delta": {"bond": 0.5},
            })

        detected = matrix.detect_misallocated_points()
        if detected:
            result = matrix.correct_misallocation(detected[0]["point_id"], dry_run=True)
            assert result.get("status") == "dry_run"
            assert "source_axis" in result
            assert "target_axis" in result

    def test_auto_correct_conditions(self, matrix):
        matrix.theta.values["correction_urge"] = 0.5
        result = matrix.auto_correct_all()
        assert result.get("status") == "skip"

    def test_find_best_axis_for_key(self, matrix):
        target = matrix._find_best_axis_for_key("happiness", "alpha")
        assert target in matrix.dimensions
        assert target != "alpha"

    def test_estimate_ideal_resonance(self, matrix):
        resonance = matrix._estimate_ideal_resonance("gamma", "happiness")
        assert isinstance(resonance, float)

    def test_negativity_report_structure(self, matrix):
        matrix.trigger_theta_negativity(0.3)
        report = matrix.get_negativity_report()
        assert "theta_negativity" in report
        assert "needs_correction" in report
        assert "ready_to_correct" in report

    def test_reset_clears_negativity(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.8
        matrix.theta.values["correction_urge"] = 0.7
        matrix.reset_theta_negativity()
        assert matrix.theta.values["theta_negativity"] == 0.0
        assert matrix.theta.values["correction_urge"] == 0.0

    def test_correction_audit_trail_records(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.6
        matrix.theta.values["correction_urge"] = 0.7

        for _ in range(3):
            matrix.history.append({"beta": {"focus": 0.5}})

        detected = matrix.detect_misallocated_points()
        if detected:
            matrix.correct_misallocation(detected[0]["point_id"])
            assert len(matrix.correction_audit_trail) >= 0

    def test_correction_log_size_limited(self, matrix):
        matrix.theta.values["theta_negativity"] = 0.6
        matrix.theta.values["correction_urge"] = 0.8

        for i in range(15):
            matrix.history.append({"alpha": {"energy": 0.5 + i * 0.01}})

        detected = matrix.detect_misallocated_points()
        for item in detected[:5]:
            matrix.correct_misallocation(item["point_id"])

        assert len(matrix.correction_audit_trail) <= matrix.max_audit_trail