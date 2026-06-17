"""
Phase 3 Safety Integration Tests — TrustManager, ContentFilter, SafetyAudit
Tests for 3-layer safety architecture integration
"""

import pytest
from unittest.mock import MagicMock

# Lazy imports for optional modules
try:
    from ai.trust.trust_manager_module import TrustManager
    from security.content_filter import ContentFilter, SafetyLevel
    from security.safety_audit import SafetyAudit, AuditEventType, Severity
    IMPORTS_AVAILABLE = True
except ImportError as e:
    IMPORTS_AVAILABLE = False
    print(f"Warning: Some imports not available: {e}")


pytestmark = pytest.mark.skipif(
    not IMPORTS_AVAILABLE, reason="Phase 3 modules not available"
)


class TestThreeLayerSafety:
    """Integration tests for 3-layer safety architecture"""

    def test_low_trust_user_toxic_content_blocked(self):
        # Layer 1: TrustManager - create low trust user
        tm = TrustManager()
        tm.record_violation("bad_user", "spam", severity="high")
        profile = tm.get_profile("bad_user")
        assert profile.score < 0.5

        # Layer 2: ContentFilter - filter toxic content
        cf = ContentFilter()
        result = cf.filter_content("I want to kill someone")
        assert result.is_safe is False
        assert result.safety_level == SafetyLevel.UNSAFE

        # Layer 3: SafetyAudit - log the event
        sa = SafetyAudit()
        sa.log_content_filter(
            "toxic content", "unsafe", "blocked", result.issues, "bad_user"
        )
        assert len(sa.entries) == 1

    def test_high_trust_user_safe_content_passes(self):
        # Layer 1: TrustManager - create high trust user
        tm = TrustManager()
        for _ in range(20):
            tm.record_interaction("good_user", positive=True)
        profile = tm.get_profile("good_user")
        assert profile.score > 0.5

        # Layer 2: ContentFilter - safe content passes
        cf = ContentFilter()
        result = cf.filter_content("Hello, how are you?")
        assert result.is_safe is True

        # Layer 3: SafetyAudit - log the event
        sa = SafetyAudit()
        sa.log_trust_evaluation("good_user", profile.score, "granted")
        assert len(sa.entries) == 1

    def test_pii_detection_and_logging(self):
        # Layer 1: TrustManager - normal user
        tm = TrustManager()
        profile = tm.get_profile("normal_user")
        assert profile.score == 0.5

        # Layer 2: ContentFilter - PII detected
        cf = ContentFilter()
        result = cf.filter_content("My email is test@example.com")
        assert len(result.issues) > 0

        # Layer 3: SafetyAudit - log the event
        sa = SafetyAudit()
        sa.log_content_filter(
            "PII content", "risky", "warn", result.issues, "normal_user"
        )
        assert len(sa.entries) == 1

    def test_trust_violation_records_in_audit(self):
        # Layer 1: TrustManager - record violation
        tm = TrustManager()
        score = tm.record_violation("violation_user", "toxic", severity="high")
        assert score < 0.5

        # Layer 3: SafetyAudit - log violation
        sa = SafetyAudit()
        sa.log_violation("violation_user", "toxic", Severity.HIGH)
        assert len(sa.violations) == 1

    def test_permission_check_respects_trust(self):
        tm = TrustManager()

        # Low trust user - limited permissions
        tm.record_violation("low_user", "minor", severity="medium")
        assert tm.check_permission("low_user", "read") is True
        assert tm.check_permission("low_user", "admin") is False

        # High trust user - should have admin permission
        for _ in range(20):
            tm.record_interaction("high_user", positive=True)
        profile = tm.get_profile("high_user")
        # High trust user should have admin permission
        assert tm.check_permission("high_user", "admin") is True

    def test_full_pipeline_user_message(self):
        """Test full pipeline: user message -> filter -> trust check -> audit log"""
        # Setup
        tm = TrustManager()
        cf = ContentFilter()
        sa = SafetyAudit()

        user_id = "test_user"
        message = "Hello, can you help me?"

        # Step 1: Trust check
        profile = tm.get_profile(user_id)
        assert profile.score >= 0.5

        # Step 2: Content filter
        filter_result = cf.filter_content(message)
        assert filter_result.is_safe is True

        # Step 3: Trust evaluation
        sa.log_trust_evaluation(user_id, profile.score, "allowed")

        # Step 4: Verify audit log
        assert len(sa.entries) == 1
        assert sa.entries[0].user_id == user_id


class TestContentFilterIntegration:
    """Integration tests for ContentFilter"""

    def test_filter_chain_toxic_then_safe(self):
        cf = ContentFilter()

        # First: toxic content
        result1 = cf.filter_content("I want to kill someone")
        assert result1.is_safe is False

        # Then: safe content
        result2 = cf.filter_content("Hello, how are you?")
        assert result2.is_safe is True

        # Stats should show both
        stats = cf.get_filter_stats()
        assert stats["total_filters"] == 2

    def test_custom_rule_integration(self):
        cf = ContentFilter()

        # Add custom rule
        cf.add_rule(lambda c: ("blocked" in c.lower(), "Contains blocked word"))

        # Test with blocked content
        result = cf.filter_content("This is blocked content")
        assert result.is_safe is False

        # Test with safe content
        result = cf.filter_content("This is safe content")
        assert result.is_safe is True


class TestSafetyAuditIntegration:
    """Integration tests for SafetyAudit"""

    def test_compliance_check_after_violations(self):
        sa = SafetyAudit()

        # No violations - should pass
        result = sa.check_compliance()
        assert result["compliance_rate"] == 1.0

        # Add violations
        sa.log_violation("user1", "spam", Severity.HIGH)
        sa.log_violation("user2", "toxic", Severity.CRITICAL)

        # Should still pass (violations are tracked, not blocking)
        result = sa.check_compliance()
        assert result["total_rules"] > 0

    def test_report_generation(self):
        sa = SafetyAudit()

        # Add various events
        sa.log_trust_evaluation("user1", 0.8, "granted")
        sa.log_content_filter("test", "safe", "pass", [])
        sa.log_violation("user2", "spam", Severity.HIGH)

        # Generate report
        report = sa.generate_report()
        assert report["total_events"] == 3
        assert "severity_distribution" in report
