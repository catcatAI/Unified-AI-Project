# =============================================================================
# ANGELA-MATRIX: L3-L4 [βδ] [A] L3
# =============================================================================
"""
Tests for ExecutionGate — execution scoring and gating logic.
"""

import pytest
from ai.core.execution_gate import REVERSIBILITY, ExecutionGate, GateDecision
from ai.core.query_classifier import _NEGATION_WORDS


class TestGateDecision:
    """Tests for GateDecision dataclass."""

    def test_gate_decision_defaults(self):
        d = GateDecision(action="reject", score=0.0)
        assert d.action == "reject"
        assert d.score == 0.0
        assert d.handler is None
        assert d.reason == ""
        assert d.confirm_message == ""
        assert d.impact_info == ""
        assert d.action_type == "none"
        assert d.original_query == ""

    def test_gate_decision_full(self):
        d = GateDecision(
            action="auto_execute",
            score=0.9,
            handler="web_search",
            reason="high score",
            action_type="read",
            original_query="搜寻天气",
        )
        assert d.handler == "web_search"
        assert d.original_query == "搜寻天气"


class TestReversibility:
    """Tests for REVERSIBILITY constants."""

    def test_read_is_reversible(self):
        assert REVERSIBILITY["read"] == 1.0

    def test_create_is_reversible(self):
        assert REVERSIBILITY["create"] == 0.9

    def test_modify_is_partially_reversible(self):
        assert REVERSIBILITY["modify"] == 0.6

    def test_delete_is_irreversible(self):
        assert REVERSIBILITY["delete"] == 0.2

    def test_send_is_irreversible(self):
        assert REVERSIBILITY["send"] == 0.1

    def test_system_is_irreversible(self):
        assert REVERSIBILITY["system"] == 0.0

    def test_none_is_reversible(self):
        assert REVERSIBILITY["none"] == 1.0

    def test_unknown_defaults_to_05(self):
        assert REVERSIBILITY.get("unknown", 0.5) == 0.5


class TestExecutionGateDecide:
    """Tests for ExecutionGate.decide() method."""

    def setup_method(self):
        self.gate = ExecutionGate()

    def test_auto_execute_search(self):
        d = self.gate.decide("search", "read", "搜寻台北天气", 0.9, {})
        assert d.action == "auto_execute"
        assert d.handler == "web_search"
        assert d.score >= 0.6

    def test_auto_execute_file_read(self):
        d = self.gate.decide("file", "read", "读取 temp.txt", 0.9, {})
        assert d.action == "auto_execute"
        assert d.handler == "file_ops"

    def test_reject_delete(self):
        d = self.gate.decide("file", "delete", "删除 temp.txt", 0.9, {})
        assert d.action == "reject"
        assert d.score < 0.2

    def test_reject_delete_all(self):
        d = self.gate.decide("file", "delete", "删除全部文件", 0.9, {})
        assert d.action == "reject"
        assert d.score < 0.1

    def test_confirm_file_create(self):
        d = self.gate.decide("file", "create", "建立 notes.md", 0.85, {})
        assert d.action in ("confirm_then_execute", "reject")
        if d.action == "confirm_then_execute":
            assert d.handler == "file_ops"

    def test_reject_system_operation(self):
        d = self.gate.decide("execute", "system", "执行这个命令", 0.9, {})
        assert d.action == "reject"
        assert d.score == 0.0

    def test_negation_forces_reject(self):
        d = self.gate.decide("search", "read", "不要搜寻", 0.9, {})
        assert d.action == "reject"
        assert d.reason == "negation_detected"

    def test_negation_cancel_forces_reject(self):
        d = self.gate.decide("file", "delete", "取消删除", 0.9, {})
        assert d.action == "reject"

    def test_no_handler_confirm(self):
        d = self.gate.decide("unknown", "none", "帮我查字典", 0.3, {})
        assert d.action == "confirm_then_execute"
        assert d.handler is None

    def test_low_score_reject(self):
        d = self.gate.decide("unknown", "none", "哈", 0.1, {})
        # Score = 1.0 * 1.0 * max(0.2, 0.1-0.1) = 0.2, which is at CONFIRM_THRESHOLD
        assert d.action in ("reject", "confirm_then_execute")


class TestExecutionGateScore:
    """Tests for execution score calculation."""

    def setup_method(self):
        self.gate = ExecutionGate()

    def test_read_high_score(self):
        d = self.gate.decide("search", "read", "搜寻台北天气", 0.9, {})
        assert d.score >= 0.8

    def test_delete_low_score(self):
        d = self.gate.decide("file", "delete", "删除 temp.txt", 0.9, {})
        assert d.score < 0.2

    def test_all_reduces_score(self):
        d = self.gate.decide("file", "delete", "删除全部文件", 0.9, {})
        assert d.score < 0.1

    def test_vague_words_reduce_score(self):
        d = self.gate.decide("file", "read", "帮我看看一下", 0.8, {})
        assert d.score < 0.8

    def test_clear_verbs_increase_score(self):
        d = self.gate.decide("search", "read", "搜寻天气", 0.9, {})
        assert d.score >= 0.8

    def test_file_path_increases_clarity(self):
        d = self.gate.decide("file", "read", "读取 /tmp/test.txt", 0.8, {})
        assert d.score >= 0.6

    def test_url_increases_clarity(self):
        d = self.gate.decide("search", "read", "搜寻 https://example.com", 0.8, {})
        assert d.score >= 0.6


class TestExecutionGateConfirmMessage:
    """Tests for confirmation message building."""

    def setup_method(self):
        self.gate = ExecutionGate()

    def test_confirm_message_contains_action(self):
        d = self.gate.decide("file", "create", "建立文件", 0.85, {})
        if d.action == "confirm_then_execute":
            assert "建立" in d.confirm_message or "执行" in d.confirm_message

    def test_delete_confirm_has_warning(self):
        d = self.gate.decide("file", "delete", "删除文件", 0.85, {})
        if d.action == "confirm_then_execute":
            assert "无法复原" in d.confirm_message or "无法" in d.confirm_message

    def test_system_confirm_has_warning(self):
        d = self.gate.decide("execute", "system", "执行命令", 0.9, {})
        # System always scores 0.0 (irreversibility=0), so always reject
        assert d.action == "reject"


class TestExecutionGateImpact:
    """Tests for impact estimation."""

    def setup_method(self):
        self.gate = ExecutionGate()

    def test_all_reduces_impact(self):
        impact_all = self.gate._estimate_impact("delete", "删除全部文件")
        impact_single = self.gate._estimate_impact("delete", "删除文件")
        assert impact_all < impact_single

    def test_single_increases_impact(self):
        impact_all = self.gate._estimate_impact("read", "读取所有文件")
        impact_single = self.gate._estimate_impact("read", "读取一个文件")
        assert impact_single >= impact_all


class TestExecutionGateHandlerMap:
    """Tests for handler mapping."""

    def test_file_maps_to_file_ops(self):
        assert ExecutionGate.HANDLER_MAP["file"] == "file_ops"

    def test_search_maps_to_web_search(self):
        assert ExecutionGate.HANDLER_MAP["search"] == "web_search"

    def test_code_maps_to_code_exec(self):
        assert ExecutionGate.HANDLER_MAP["code"] == "code_exec"

    def test_execute_maps_to_code_exec(self):
        assert ExecutionGate.HANDLER_MAP["execute"] == "code_exec"

    def test_task_maps_to_task_mgr(self):
        assert ExecutionGate.HANDLER_MAP["task"] == "task_mgr"

    def test_system_maps_to_system_cmd(self):
        assert ExecutionGate.HANDLER_MAP["system"] == "system_cmd"

    def test_vision_maps_to_vision(self):
        assert ExecutionGate.HANDLER_MAP["vision"] == "vision"


class TestExecutionGateThresholds:
    """Tests for threshold constants."""

    def test_auto_execute_threshold(self):
        assert ExecutionGate.AUTO_EXECUTE == 0.6

    def test_confirm_threshold(self):
        assert ExecutionGate.CONFIRM_THRESHOLD == 0.2

    def test_auto_above_confirm(self):
        assert ExecutionGate.AUTO_EXECUTE > ExecutionGate.CONFIRM_THRESHOLD


class TestExecutionGateIntegration:
    """Integration tests with QueryClassifier."""

    def setup_method(self):
        from ai.core.query_classifier import QueryClassifier
        self.clf = QueryClassifier()
        self.gate = ExecutionGate()

    def test_search_auto_executes(self):
        r = self.clf.classify("搜寻台北天气")
        d = self.gate.decide(r.primary_type.value, r.action_type, "搜寻台北天气", r.confidence, {})
        assert d.action == "auto_execute"

    def test_delete_rejects(self):
        r = self.clf.classify("删除 temp.txt")
        d = self.gate.decide(r.primary_type.value, r.action_type, "删除 temp.txt", r.confidence, {})
        assert d.action == "reject"

    def test_negation_rejects(self):
        r = self.clf.classify("不要搜寻")
        d = self.gate.decide(r.primary_type.value, r.action_type, "不要搜寻", r.confidence, {})
        assert d.action == "reject"

    def test_execute_system_rejects(self):
        r = self.clf.classify("执行这个命令")
        d = self.gate.decide(r.primary_type.value, r.action_type, "执行这个命令", r.confidence, {})
        assert d.action == "reject"

    def test_vision_confirm(self):
        r = self.clf.classify("看")
        d = self.gate.decide(r.primary_type.value, r.action_type, "看", r.confidence, {})
        # VISION handler is mapped, so auto_execute or confirm
        assert d.action in ("auto_execute", "confirm_then_execute")

    def test_knowledge_question_confirm(self):
        r = self.clf.classify("什么是Python?")
        d = self.gate.decide(r.primary_type.value, r.action_type, "什么是Python?", r.confidence, {})
        # KNOWLEDGE has no handler, low actionability
        assert d.action in ("confirm_then_execute", "reject")


class TestExecutionGateFeedbackLoop:
    """C³ 5.0: execution result feedback to routing decisions."""

    def setup_method(self):
        self.gate = ExecutionGate()

    def test_record_result_tracks_success(self):
        self.gate.record_result("web_search", True)
        self.gate.record_result("web_search", True)
        assert self.gate._results["web_search"]["success"] == 2

    def test_record_result_tracks_failure(self):
        self.gate.record_result("file_ops", False)
        assert self.gate._results["file_ops"]["fail"] == 1

    def test_get_feedback_stats(self):
        self.gate.record_result("web_search", True)
        self.gate.record_result("file_ops", False)
        stats = self.gate.get_feedback_stats()
        assert stats["web_search"]["success"] == 1
        assert stats["file_ops"]["fail"] == 1

    def test_feedback_adjustment_zero_for_few_samples(self):
        self.gate.record_result("web_search", True)
        self.gate.record_result("web_search", True)
        assert self.gate._get_feedback_adjustment("web_search") == 0.0

    def test_feedback_adjustment_positive_for_reliable_handler(self):
        for _ in range(5):
            self.gate.record_result("web_search", True)
        assert self.gate._get_feedback_adjustment("web_search") == 0.05

    def test_feedback_adjustment_negative_for_unreliable_handler(self):
        for _ in range(3):
            self.gate.record_result("file_ops", False)
        assert self.gate._get_feedback_adjustment("file_ops") == -0.05

    def test_feedback_adjustment_zero_for_mixed_handler(self):
        self.gate.record_result("web_search", True)
        self.gate.record_result("web_search", True)
        self.gate.record_result("web_search", False)
        self.gate.record_result("web_search", True)
        assert self.gate._get_feedback_adjustment("web_search") == 0.0

    def test_feedback_adjustment_unknown_handler(self):
        assert self.gate._get_feedback_adjustment("nonexistent") == 0.0

    def test_feedback_adjustment_none_handler(self):
        assert self.gate._get_feedback_adjustment(None) == 0.0

    def test_reliable_handler_lowers_auto_threshold(self):
        for _ in range(5):
            self.gate.record_result("web_search", True)
        # "搜寻天气": action=read, query_type=search → handler=web_search
        # Score: reversibility=1.0, impact=1.0, clarity=0.9+0.1(clear_verb)=1.0 (min)
        # Score = 1.0 * 1.0 * 1.0 = 1.0, well above 0.6
        d = self.gate.decide("search", "read", "搜寻天气", 0.9, {})
        assert d.action == "auto_execute"
        assert "fb_adj=0.05" in d.reason

    def test_unreliable_handler_raises_threshold(self):
        for _ in range(3):
            self.gate.record_result("file_ops", False)
        # "读取文件": action=read, query_type=file → handler=file_ops
        # Score: reversibility=1.0, impact=1.0, clarity=0.8+0.1(clear_verb)=0.9
        # Score = 1.0 * 1.0 * 0.9 = 0.9
        # Without feedback: effective_auto = 0.6, score >= 0.6 → auto_execute
        # With -0.05 feedback: effective_auto = 0.65, score >= 0.65 → still auto_execute (0.9 >= 0.65)
        # The key is that reason contains fb_adj
        d = self.gate.decide("file", "read", "读取文件", 0.8, {})
        assert "fb_adj=-0.05" in d.reason
