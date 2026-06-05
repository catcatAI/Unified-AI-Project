"""Tests for CodeLearningEngine"""
import pytest
try:
    from apps.backend.src.ai.code_inspection.code_learning import (
        CodeLearningEngine, LearnedPattern
    )
except ImportError:
    pytest.skip("CodeLearningEngine not available (stub module)", allow_module_level=True)


class TestCodeLearningEngine:
    def test_import(self):
        from apps.backend.src.ai.code_inspection.code_learning import (
            CodeLearningEngine, LearnedPattern, LearningFeedback
        )
        assert hasattr(CodeLearningEngine, 'learn_from_feedback')
        assert hasattr(CodeLearningEngine, 'get_pattern_by_id')
        assert hasattr(CodeLearningEngine, 'get_all_patterns')
        assert hasattr(CodeLearningEngine, 'get_high_confidence_patterns')
        assert hasattr(CodeLearningEngine, 'get_feedback_stats')

    def test_instantiation(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        assert instance.knowledge_graph is None
        assert instance.max_feedback_history == 500
        assert instance.feedback_history == []

    def test_builtin_patterns_loaded(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        assert len(instance.patterns) == 7
        assert instance.patterns["PAT-001"].name == "除零保護"
        assert instance.patterns["PAT-001"].confidence == 0.95

    def test_get_pattern_by_id_found(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        pat = instance.get_pattern_by_id("PAT-001")
        assert pat is not None
        assert pat.id == "PAT-001"

    def test_get_pattern_by_id_not_found(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        pat = instance.get_pattern_by_id("PAT-999")
        assert pat is None

    def test_get_all_patterns(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        patterns = instance.get_all_patterns()
        assert len(patterns) == 7

    def test_get_high_confidence_patterns(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        all_high = instance.get_high_confidence_patterns(threshold=0.8)
        assert len(all_high) == 7
        top_only = instance.get_high_confidence_patterns(threshold=0.95)
        assert len(top_only) == 3
        assert {p.id for p in top_only} == {"PAT-001", "PAT-006", "PAT-007"}

    def test_learn_from_feedback_accepted(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        pat = instance.learn_from_feedback(
            issue_id="ISS-001", original_fix="f1",
            human_feedback="除零錯誤", accepted=True,
        )
        assert pat.id == "PAT-001"
        assert pat.success_count == 1

    def test_learn_from_feedback_rejected_with_correction(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        pat = instance.learn_from_feedback(
            issue_id="ISS-002", original_fix="f2",
            human_feedback="None check missing", accepted=False,
            correction="add_none_check",
        )
        assert pat.id == "PAT-002"
        assert pat.failure_count == 1
        assert pat.fix_template == "add_none_check"

    def test_learn_from_feedback_no_match_returns_none(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        result = instance.learn_from_feedback(
            issue_id="ISS-003", original_fix="f3",
            human_feedback="completely unrelated text", accepted=True,
        )
        assert result is None

    def test_feedback_stats_empty(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        stats = instance.get_feedback_stats()
        assert stats["total_feedback"] == 0
        assert stats["acceptance_rate"] == 0.0

    def test_feedback_stats_after_learning(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        instance.learn_from_feedback("I1", "f", "除零", accepted=True)
        instance.learn_from_feedback("I2", "f", "None", accepted=False)
        stats = instance.get_feedback_stats()
        assert stats["total_feedback"] == 2
        assert stats["accepted"] == 1
        assert stats["rejected"] == 1
        assert stats["acceptance_rate"] == 0.5

    def test_export_patterns(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        exported = instance.export_patterns()
        assert len(exported) == 7
        assert exported[0]["id"] == "PAT-001"
        assert "success_rate" in exported[0]

    def test_import_patterns(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        exported = instance.export_patterns()
        instance2 = CodeLearningEngine(knowledge_graph=None)
        instance2.patterns.clear()
        instance2.import_patterns(exported)
        assert len(instance2.patterns) == 7
        assert instance2.patterns["PAT-001"].name == "除零保護"

    def test_learned_pattern_success_rate(self):
        pat = LearnedPattern(
            id="T1", name="T", description="D",
            fix_template="t", success_count=3, failure_count=1,
        )
        assert pat.success_rate == 0.75

    def test_learned_pattern_success_rate_no_data(self):
        pat = LearnedPattern(id="T2", name="T", description="D", fix_template="t")
        assert pat.success_rate == 0.0

    def test_max_feedback_history_enforced(self):
        instance = CodeLearningEngine(knowledge_graph=None)
        instance.max_feedback_history = 3
        for i in range(5):
            instance.learn_from_feedback(f"I{i}", "f", "除零", accepted=True)
        assert len(instance.feedback_history) == 3
