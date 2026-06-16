"""
Phase 4 Integration Tests — Safety & Intelligence Layer
Tests for TrustManager, ContentFilter, SafetyAudit, AgentOrchestrator, PlanningEngine, ReasoningEngines
"""

import pytest
from unittest.mock import MagicMock

# Lazy imports for optional modules
try:
    from ai.trust.trust_manager_module import TrustManager, TrustProfile
    from security.content_filter import ContentFilter, FilterResult, SafetyLevel, FilterAction
    from security.safety_audit import SafetyAudit, AuditEventType, Severity
    from ai.agents.agent_orchestrator import AgentOrchestrator
    from ai.reasoning.planning_engine import PlanningEngine
    from ai.reasoning.reasoning_engines import (
        ChainOfThoughtReasoner,
        AnalogicalReasoner,
        AbductiveReasoner,
    )
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Warning: Some imports not available: {e}")


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="Phase 4 modules not available"
)


class TestTrustManager:
    """Tests for TrustManager"""

    def test_initialization(self):
        tm = TrustManager()
        assert tm.config["base_trust"] == 0.5
        assert tm.profiles == {}

    def test_get_profile_creates_default(self):
        tm = TrustManager()
        profile = tm.get_profile("user1")
        assert profile.user_id == "user1"
        assert profile.score == 0.5

    def test_record_positive_interaction(self):
        tm = TrustManager()
        score = tm.record_interaction("user1", positive=True)
        assert score > 0.5

    def test_record_negative_interaction(self):
        tm = TrustManager()
        score = tm.record_interaction("user1", positive=False)
        assert score < 0.5

    def test_record_violation(self):
        tm = TrustManager()
        score = tm.record_violation("user1", "spam", severity="high")
        assert score < 0.5

    def test_trust_level(self):
        tm = TrustManager()
        profile = tm.get_profile("user1")
        assert profile.trust_level == "medium"

    def test_permission_check(self):
        tm = TrustManager()
        assert tm.check_permission("user1", "read") is True
        assert tm.check_permission("user1", "admin") is False

    def test_recover_trust(self):
        tm = TrustManager()
        tm.record_violation("user1", "minor", severity="low")
        score_before = tm.get_profile("user1").score
        tm.recover_trust("user1")
        score_after = tm.get_profile("user1").score
        assert score_after >= score_before

    def test_trust_summary(self):
        tm = TrustManager()
        tm.get_profile("user1")
        tm.get_profile("user2")
        summary = tm.get_trust_summary()
        assert summary["total_users"] == 2


class TestContentFilter:
    """Tests for ContentFilter"""

    def test_initialization(self):
        cf = ContentFilter()
        assert cf.config["enabled"] is True

    def test_safe_content(self):
        cf = ContentFilter()
        result = cf.filter_content("Hello, how are you?")
        assert result.is_safe is True
        assert result.safety_level == SafetyLevel.SAFE

    def test_toxic_content(self):
        cf = ContentFilter()
        result = cf.filter_content("I want to kill someone")
        assert result.is_safe is False
        assert result.safety_level == SafetyLevel.UNSAFE

    def test_pii_detection(self):
        cf = ContentFilter()
        result = cf.filter_content("My email is test@example.com")
        assert len(result.issues) > 0
        assert any(i["type"] == "pii" for i in result.issues)

    def test_sanitize_pii(self):
        cf = ContentFilter()
        result = cf.filter_content("My email is test@example.com")
        assert result.sanitized_content is not None
        assert "test@example.com" not in result.sanitized_content

    def test_custom_rule(self):
        cf = ContentFilter()
        cf.add_rule(lambda c: ("ban" in c.lower(), "Contains ban word"))
        result = cf.filter_content("This is banned content")
        assert result.is_safe is False

    def test_filter_stats(self):
        cf = ContentFilter()
        cf.filter_content("Hello")
        cf.filter_content("Kill someone")
        stats = cf.get_filter_stats()
        assert stats["total_filters"] == 2


class TestSafetyAudit:
    """Tests for SafetyAudit"""

    def test_initialization(self):
        sa = SafetyAudit()
        assert sa.entries == []

    def test_log_event(self):
        sa = SafetyAudit()
        entry = sa.log_event(
            AuditEventType.SAFETY_CHECK,
            Severity.LOW,
            "Test event",
        )
        assert entry.message == "Test event"
        assert len(sa.entries) == 1

    def test_log_trust_evaluation(self):
        sa = SafetyAudit()
        entry = sa.log_trust_evaluation("user1", 0.8, "granted")
        assert entry.user_id == "user1"
        assert len(sa.entries) == 1

    def test_log_content_filter(self):
        sa = SafetyAudit()
        entry = sa.log_content_filter("test", "safe", "pass", [])
        assert entry.message == "Content filtered: safe -> pass"

    def test_violation_tracking(self):
        sa = SafetyAudit()
        sa.log_violation("user1", "spam", Severity.HIGH)
        assert len(sa.violations) == 1

    def test_compliance_check(self):
        sa = SafetyAudit()
        result = sa.check_compliance()
        assert result["compliance_rate"] == 1.0

    def test_generate_report(self):
        sa = SafetyAudit()
        sa.log_event(AuditEventType.SAFETY_CHECK, Severity.LOW, "Test")
        report = sa.generate_report()
        assert report["total_events"] == 1


class TestAgentOrchestrator:
    """Tests for AgentOrchestrator"""

    def test_initialization(self):
        ao = AgentOrchestrator()
        assert ao is not None

    def test_classify_intent(self):
        ao = AgentOrchestrator()
        result = ao.classify_intent("What is the weather?")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_select_agent(self):
        ao = AgentOrchestrator()
        agent = ao.select_agent("file_read")
        assert agent is not None


class TestPlanningEngine:
    """Tests for PlanningEngine"""

    def test_initialization(self):
        pe = PlanningEngine()
        assert pe is not None

    def test_create_plan(self):
        pe = PlanningEngine()
        plan = pe.create_plan("Build a web app")
        assert plan is not None


class TestReasoningEngines:
    """Tests for ReasoningEngines"""

    def test_chain_of_thought(self):
        cot = ChainOfThoughtReasoner()
        result = cot.reason("If A then B, A is true")
        assert result is not None

    def test_analogical(self):
        ar = AnalogicalReasoner()
        result = ar.find_analogy("A is to B", "C is to D")
        assert result is not None

    def test_abductive(self):
        ab = AbductiveReasoner()
        result = ab.explain("The ground is wet")
        assert result is not None
