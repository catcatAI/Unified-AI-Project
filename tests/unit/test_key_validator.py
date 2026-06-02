"""Tests for core/security/key_validator.py"""
import pytest


class TestKeyValidator:
    """Tests for KeyValidator"""

    def test_import(self):
        from core.security.key_validator import KeyValidator
        assert KeyValidator is not None

    def test_validate_key_empty(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        result = instance.validate_key("ANGELA_KEY_A", "")
        assert result.is_valid is False
        assert result.severity == "critical"
        assert len(result.issues) > 0

    def test_validate_key_weak_pattern(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        result = instance.validate_key("ANGELA_KEY_A", "password123")
        assert result.is_valid is False
        assert result.severity == "critical"

    def test_validate_key_too_short(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        result = instance.validate_key("ANGELA_KEY_A", "short")
        assert result.is_valid is False
        assert any("長度不足" in i for i in result.issues)

    def test_validate_key_valid(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        result = instance.validate_key("ANGELA_KEY_A", "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6")
        assert result.is_valid is True
        assert result.severity == "low"

    def test_validate_all_keys(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        env = {
            "ANGELA_KEY_A": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "ANGELA_KEY_B": "b2c3d4e5f6g7h8i9j0k1l2m3n4o5p67",
            "ANGELA_KEY_C": "c3d4e5f6g7h8i9j0k1l2m3n4o5p678",
        }
        results = instance.validate_all_keys(env)
        assert len(results) == 3
        for r in results:
            assert r.is_valid is True

    def test_get_validation_summary(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        env = {
            "ANGELA_KEY_A": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
            "ANGELA_KEY_B": "",
            "ANGELA_KEY_C": "c3d4e5f6g7h8i9j0k1l2m3n4o5p678",
        }
        instance.validate_all_keys(env)
        summary = instance.get_validation_summary()
        assert summary["total_keys"] == 3
        assert summary["invalid_keys"] >= 1
        assert "all_valid" in summary

    def test_check_key_complexity(self):
        from core.security.key_validator import KeyValidator
        instance = KeyValidator()
        assert instance._check_key_complexity("abc123") is True
        assert instance._check_key_complexity("abc!!!") is True
        assert instance._check_key_complexity("abcdef") is False
