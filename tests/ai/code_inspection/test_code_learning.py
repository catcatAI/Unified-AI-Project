"""
 * =============================================================================
 * ANGELA-MATRIX: [L4-Test] [α-Test] [A-Validation] [L0-L3]
 * =============================================================================
"""

from datetime import datetime

import pytest
try:
    from apps.backend.src.ai.code_inspection.code_learning import (
        LearnedPattern,
        LearningFeedback,
        CodeLearningEngine,
    )
except ImportError:
    pytest.skip("LearnedPattern not available (stub module)", allow_module_level=True)


class TestLearnedPattern:
    def test_default_confidence(self):
        p = LearnedPattern(id="P1", name="test", description="d", fix_template="t")
        assert p.confidence == 0.5
        assert p.success_rate == 0.0

    def test_success_rate_no_tries(self):
        p = LearnedPattern(id="P1", name="test", description="d", fix_template="t")
        assert p.success_rate == 0.0

    def test_success_rate_all_ok(self):
        p = LearnedPattern(id="P1", name="test", description="d", fix_template="t",
                           success_count=5, failure_count=0)
        assert p.success_rate == 1.0

    def test_success_rate_mixed(self):
        p = LearnedPattern(id="P1", name="test", description="d", fix_template="t",
                           success_count=3, failure_count=1)
        assert p.success_rate == 0.75


class TestCodeLearningEngine:
    def setup_method(self):
        self.engine = CodeLearningEngine()

    def test_init_has_builtin_patterns(self):
        assert len(self.engine.patterns) == 7

    def test_init_empty_feedback(self):
        assert self.engine.feedback_history == []

    def test_get_pattern_by_id_exists(self):
        p = self.engine.get_pattern_by_id("PAT-001")
        assert p is not None
        assert p.name == "除零保護"

    def test_get_pattern_by_id_missing(self):
        assert self.engine.get_pattern_by_id("PAT-999") is None

    def test_get_all_patterns(self):
        all_p = self.engine.get_all_patterns()
        assert len(all_p) == 7

    def test_get_high_confidence_patterns_default(self):
        high = self.engine.get_high_confidence_patterns()
        assert len(high) == 7

    def test_get_high_confidence_patterns_custom_threshold(self):
        high = self.engine.get_high_confidence_patterns(threshold=0.99)
        assert len(high) == 0

    def test_learn_from_feedback_accepted(self):
        result = self.engine.learn_from_feedback(
            "issue-1", "fix1", "除零錯誤修復成功", True
        )
        assert result is not None
        assert result.id == "PAT-001"
        assert result.success_count == 1
        assert result.failure_count == 0
        assert result.confidence == 1.0

    def test_learn_from_feedback_rejected_with_correction(self):
        old_template = self.engine.patterns["PAT-001"].fix_template
        result = self.engine.learn_from_feedback(
            "issue-2", "fix1", "除零錯誤處理不當", False,
            correction="use_try_except"
        )
        assert result.fix_template == "use_try_except"
        assert result.failure_count == 1

    def test_learn_from_feedback_no_pattern_match(self):
        result = self.engine.learn_from_feedback(
            "issue-3", "fix1", "完全無關的反饋", True
        )
        assert result is None

    def test_learn_from_feedback_adds_to_history(self):
        self.engine.learn_from_feedback("i1", "fix", "除零", True)
        assert len(self.engine.feedback_history) == 1

    def test_learn_from_feedback_trims_history(self):
        self.engine.max_feedback_history = 5
        for i in range(10):
            self.engine.learn_from_feedback(f"i{i}", "fix", "除零", True)
        assert len(self.engine.feedback_history) == 5

    def test_infer_pattern_id_zero_division(self):
        assert self.engine._infer_pattern_id("除零錯誤", None) == "PAT-001"
        assert self.engine._infer_pattern_id("divisor is zero", None) == "PAT-001"
        assert self.engine._infer_pattern_id("zero division", None) == "PAT-001"

    def test_infer_pattern_id_null_value(self):
        assert self.engine._infer_pattern_id("none value", None) == "PAT-002"
        assert self.engine._infer_pattern_id("空值檢查", None) == "PAT-002"
        assert self.engine._infer_pattern_id("null reference", None) == "PAT-002"

    def test_infer_pattern_id_index(self):
        assert self.engine._infer_pattern_id("index out of range", None) == "PAT-003"
        assert self.engine._infer_pattern_id("索引越界", None) == "PAT-003"

    def test_infer_pattern_id_sync(self):
        assert self.engine._infer_pattern_id("type 一致", None) == "PAT-004"
        assert self.engine._infer_pattern_id("sync required", None) == "PAT-004"
        assert self.engine._infer_pattern_id("frontend mismatch", None) == "PAT-004"

    def test_infer_pattern_id_exception(self):
        assert self.engine._infer_pattern_id("except block", None) == "PAT-005"
        assert self.engine._infer_pattern_id("異常處理", None) == "PAT-005"

    def test_infer_pattern_id_history(self):
        assert self.engine._infer_pattern_id("history missing", None) == "PAT-006"
        assert self.engine._infer_pattern_id("快照不完整", None) == "PAT-006"

    def test_infer_pattern_id_theta(self):
        assert self.engine._infer_pattern_id("axis init", None) == "PAT-007"
        assert self.engine._infer_pattern_id("theta axis", None) == "PAT-007"

    def test_infer_pattern_id_no_match(self):
        assert self.engine._infer_pattern_id("something else", None) is None

    def test_get_feedback_stats_empty(self):
        stats = self.engine.get_feedback_stats()
        assert stats["total_feedback"] == 0
        assert stats["acceptance_rate"] == 0.0

    def test_get_feedback_stats_after_feedback(self):
        self.engine.learn_from_feedback("i1", "fix", "除零", True)
        self.engine.learn_from_feedback("i2", "fix", "索引", False)
        stats = self.engine.get_feedback_stats()
        assert stats["total_feedback"] == 2
        assert stats["accepted"] == 1
        assert stats["rejected"] == 1
        assert stats["acceptance_rate"] == 0.5

    def test_export_patterns(self):
        exported = self.engine.export_patterns()
        assert len(exported) == 7
        assert exported[0]["id"] == "PAT-001"
        assert "success_rate" in exported[0]

    def test_import_patterns(self):
        new_engine = CodeLearningEngine()
        data = [{"id": "CUSTOM-1", "name": "Custom", "description": "d",
                 "fix_template": "t", "confidence": 0.7}]
        new_engine.import_patterns(data)
        assert "CUSTOM-1" in new_engine.patterns
        assert new_engine.patterns["CUSTOM-1"].confidence == 0.7

    def test_import_patterns_merges_with_builtin(self):
        new_engine = CodeLearningEngine()
        assert len(new_engine.patterns) == 7
        new_engine.import_patterns([{
            "id": "NEW-1", "name": "New", "description": "d", "fix_template": "t"
        }])
        assert len(new_engine.patterns) == 8

    def test_learn_updates_confidence_correctly(self):
        pat = self.engine.patterns["PAT-001"]
        self.engine.learn_from_feedback("i1", "fix", "除零error", True)
        assert pat.confidence == 1.0
        self.engine.learn_from_feedback("i2", "fix", "除零error again", False)
        assert pat.confidence == 0.75
