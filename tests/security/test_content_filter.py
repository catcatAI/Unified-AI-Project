import pytest
from security.content_filter import ContentFilter, FilterResult, SafetyLevel, FilterAction


class TestContentFilter:
    def test_default_initialization(self):
        cf = ContentFilter()
        assert cf.config["enabled"] is True
        assert cf.config["block_on_unsafe"] is True
        assert cf.config["max_content_length"] == 10000

    def test_disabled_filter_passes_all(self):
        cf = ContentFilter({"enabled": False})
        result = cf.filter_content("kill murder bomb")
        assert result.action == FilterAction.PASS
        assert result.safety_level == SafetyLevel.SAFE

    def test_blocks_oversized_content(self):
        cf = ContentFilter()
        result = cf.filter_content("x" * 20000)
        assert result.action == FilterAction.BLOCK
        assert result.safety_level == SafetyLevel.UNSAFE

    def test_detects_toxic_keywords(self):
        cf = ContentFilter()
        result = cf.filter_content("this is a kill command")
        assert result.action == FilterAction.BLOCK
        assert result.safety_level == SafetyLevel.UNSAFE
        assert any(i["type"] == "toxicity" for i in result.issues)

    def test_detects_email_pii(self):
        cf = ContentFilter()
        result = cf.filter_content("contact me at test@example.com")
        assert result.issues
        assert any(i["pii_type"] == "email" for i in result.issues if i["type"] == "pii")

    def test_sanitizes_email_pii(self):
        cf = ContentFilter({"pii_detection": True, "block_on_unsafe": False})
        # No toxicity, just PII
        result = cf.filter_content("email: user@domain.com")
        assert result.action == FilterAction.WARN
        assert result.safety_level == SafetyLevel.RISKY

    def test_safe_content_passes(self):
        cf = ContentFilter()
        result = cf.filter_content("hello, how are you today?")
        assert result.action == FilterAction.PASS
        assert result.safety_level == SafetyLevel.SAFE
        assert result.is_safe is True

    def test_custom_rules(self):
        cf = ContentFilter()
        cf.add_rule(lambda c: (True, "custom block"))
        result = cf.filter_content("test content")
        assert any(i["type"] == "custom" for i in result.issues)

    def test_get_filter_stats_empty(self):
        cf = ContentFilter()
        stats = cf.get_filter_stats()
        assert stats["total_filters"] == 0

    def test_get_filter_stats_after_filters(self):
        cf = ContentFilter()
        cf.filter_content("safe content")
        cf.filter_content("kill you")
        stats = cf.get_filter_stats()
        assert stats["total_filters"] == 2
        assert "block" in stats["actions"]

    def test_calculate_confidence_no_issues(self):
        cf = ContentFilter()
        result = cf.filter_content("safe content")
        assert result.confidence == 1.0

    def test_warn_on_risky_disabled(self):
        cf = ContentFilter({"warn_on_risky": False, "pii_detection": True, "block_on_unsafe": False})
        result = cf.filter_content("email: a@b.com")
        assert result.action == FilterAction.PASS
