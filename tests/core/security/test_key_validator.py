import pytest
from apps.backend.src.core.security.key_validator import KeyValidator


class TestKeyValidator:
    def test_empty_key_is_critical(self):
        validator = KeyValidator()
        result = validator.validate_key("ANGELA_KEY_A", "")
        assert result.is_valid is False
        assert result.severity == "critical"

    def test_whitespace_key_is_critical(self):
        validator = KeyValidator()
        result = validator.validate_key("ANGELA_KEY_B", "   ")
        assert result.is_valid is False
        assert result.severity == "critical"

    def test_key_too_short(self):
        validator = KeyValidator()
        result = validator.validate_key("ANGELA_KEY_A", "short")
        assert result.is_valid is False
        assert result.severity == "high"

    def test_key_valid_length_and_complexity(self):
        validator = KeyValidator()
        result = validator.validate_key("ANGELA_KEY_A", "a" * 32 + "1")
        assert result.is_valid is True

    def test_weak_pattern_detected(self):
        validator = KeyValidator()
        result = validator.validate_key("ANGELA_KEY_A", "your_key_a_minimum_32_chars")
        assert result.is_valid is False
        assert result.severity == "critical"

    def test_weak_pattern_changeme(self):
        validator = KeyValidator()
        result = validator.validate_key("ANGELA_KEY_A", "changeme")
        assert result.is_valid is False

    def test_api_key_min_length(self):
        validator = KeyValidator()
        result = validator.validate_key("GEMINI_API_KEY", "a" * 20)
        assert result.is_valid is True

    def test_api_key_too_short(self):
        validator = KeyValidator()
        result = validator.validate_key("GEMINI_API_KEY", "short")
        assert result.is_valid is False

    def test_validate_all_keys_from_dict(self):
        validator = KeyValidator()
        env = {
            "ANGELA_KEY_A": "a" * 32 + "1",
            "ANGELA_KEY_B": "b" * 32 + "2",
            "ANGELA_KEY_C": "c" * 32 + "3",
        }
        results = validator.validate_all_keys(env)
        assert len(results) == 3
        assert all(r.is_valid for r in results)

    def test_validate_all_keys_with_api_keys(self):
        validator = KeyValidator()
        env = {
            "ANGELA_KEY_A": "a" * 32 + "1",
            "ANGELA_KEY_B": "b" * 32 + "2",
            "ANGELA_KEY_C": "c" * 32 + "3",
            "GEMINI_API_KEY": "g" * 20,
        }
        results = validator.validate_all_keys(env)
        assert len(results) == 4

    def test_validate_all_keys_with_empty_api_keys(self):
        validator = KeyValidator()
        env = {
            "ANGELA_KEY_A": "a" * 32 + "1",
            "ANGELA_KEY_B": "b" * 32 + "2",
            "ANGELA_KEY_C": "c" * 32 + "3",
            "GEMINI_API_KEY": "",
        }
        results = validator.validate_all_keys(env)
        assert len(results) == 3

    def test_get_critical_issues(self):
        validator = KeyValidator()
        validator.validate_key("TEST_KEY", "")
        validator.validate_key("ANGELA_KEY_B", "b" * 32 + "2")
        validator.validate_key("ANGELA_KEY_C", "c" * 32 + "3")
        validator.validate_all_keys({"ANGELA_KEY_A": ""})
        critical = validator.get_critical_issues()
        assert len(critical) >= 1

    def test_get_high_issues(self):
        validator = KeyValidator()
        validator.validate_all_keys({"ANGELA_KEY_A": "short"})
        high = validator.get_high_issues()
        assert len(high) == 1

    def test_get_validation_summary(self):
        validator = KeyValidator()
        env = {"ANGELA_KEY_A": "a" * 32 + "1"}
        validator.validate_all_keys(env)
        summary = validator.get_validation_summary()
        assert summary["total_keys"] >= 1
        assert summary["total_keys"] == summary["valid_keys"] + summary["invalid_keys"]

    def test_key_complexity_check(self):
        validator = KeyValidator()
        assert validator._check_key_complexity("abcdefgh1234") is True
        assert validator._check_key_complexity("abcdefgh") is False
        assert validator._check_key_complexity("12345678") is False
        assert validator._check_key_complexity("abc!@#$%") is True
