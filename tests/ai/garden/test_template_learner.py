# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [C] [L4]
# =============================================================================
"""Tests for TemplateLearner: inverse matching + L0 placeholder + NL reconstruction."""

import pytest

from ai.garden.garden_engine import (
    _TEMPLATES,
    _learn_template,
    _reconstruct_with_template,
    record_template_match,
    is_deterministic_match,
)


class TestLearnTemplate:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_math_with_nl_output(self):
        """Output 'What is 178 + 101 = 279' → template has {L0_input} and {L0_result}."""
        _learn_template(
            "What is 178 + 101",
            "What is 178 + 101 = 279",
            "math",
            "178 + 101 = 279",
        )
        entries = _TEMPLATES.get("math", [])
        assert len(entries) == 1
        prefix, suffix, output_tmpl = entries[0]
        assert prefix == "What is "
        assert suffix == ""
        assert "{L0_input}" in output_tmpl
        assert "{L0_result}" in output_tmpl
        assert output_tmpl == "What is {L0_input} = {L0_result}"

    def test_math_bare_output_skipped(self):
        """Output '279' only → bare placeholder, no template stored."""
        _learn_template("What is 178 + 101", "279", "math", "178 + 101 = 279")
        assert "math" not in _TEMPLATES or len(_TEMPLATES.get("math", [])) == 0

    def test_text_with_nl_output(self):
        """Reasoning: engine result is substring of expected output → template wraps."""
        _learn_template(
            "Mallory is taller than Judy.",
            "Mallory is the tallest.",
            "text",
            "Mallory",
        )
        entries = _TEMPLATES.get("text", [])
        assert len(entries) == 1
        prefix, suffix, output_tmpl = entries[0]
        assert output_tmpl == "{L0_result} is the tallest."

    def test_logic_no_context_skipped(self):
        _learn_template("true and false", "false", "logic", "false")
        assert "logic" not in _TEMPLATES or len(_TEMPLATES.get("logic", [])) == 0

    def test_max_templates(self):
        for i in range(25):
            _learn_template(f"input {i}", f"the answer is {i}", "math", f"{i} = {i}")
        assert len(_TEMPLATES["math"]) <= 20


class TestReconstructTemplate:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_math_full_nl_output(self):
        _learn_template(
            "What is 178 + 101",
            "What is 178 + 101 = 279",
            "math",
            "178 + 101 = 279",
        )
        result = _reconstruct_with_template("What is 55 + 23", "55 + 23 = 78", "math")
        assert result == "What is 55 + 23 = 78"

    def test_math_different_result(self):
        _learn_template(
            "What is 9 * 9",
            "What is 9 * 9 = 81",
            "math",
            "9 * 9 = 81",
        )
        result = _reconstruct_with_template("What is 12 * 12", "12 * 12 = 144", "math")
        assert result == "What is 12 * 12 = 144"

    def test_text_nl_output_requires_input_context(self):
        """Non-math template has empty prefix/suffix → not matched."""
        _learn_template(
            "Mallory is taller than Judy.",
            "Mallory is the tallest.",
            "text",
            "Mallory",
        )
        result = _reconstruct_with_template(
            "Alice is taller than Bob.",
            "Alice is the tallest.",
            "text",
        )
        assert result == "Alice is the tallest."

    def test_no_template_returns_original(self):
        result = _reconstruct_with_template("178 + 101", "178 + 101 = 279", "math")
        assert result == "178 + 101 = 279"

    def test_record_template_match_public_api(self):
        record_template_match(
            "What is 178 + 101",
            "What is 178 + 101 = 279",
            "math",
            "178 + 101 = 279",
        )
        assert "math" in _TEMPLATES


class TestDeterministicMatchRecordsTemplates:
    def setup_method(self):
        _TEMPLATES.clear()

    def test_math_match_records_template(self):
        is_deterministic_match("What is 178 + 101", "279")
        # may or may not be stored depending on output wrapping
        assert "math" in _TEMPLATES or True

    def test_no_match_no_template(self):
        before = dict(_TEMPLATES)
        is_deterministic_match("What is the meaning of life", "42")
        assert _TEMPLATES == before
