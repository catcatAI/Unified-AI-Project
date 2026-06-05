"""Tests for ValueAssessmentSystem"""
import pytest
try:
    from apps.backend.src.ai.alignment.value_assessment import ValueAssessmentSystem
except ImportError:
    pytest.skip("ValueAssessmentSystem not available (stub module)", allow_module_level=True)


class TestValueAssessmentSystem:
    def test_import(self):
        from apps.backend.src.ai.alignment.value_assessment import ValueAssessmentSystem
        assert hasattr(ValueAssessmentSystem, 'evaluate_intent')
        assert hasattr(ValueAssessmentSystem, 'get_value_directive')

    def test_instantiation_default_weights(self):
        instance = ValueAssessmentSystem()
        expected = {
            "truth": 0.8, "harmony": 0.7, "autonomy": 0.6,
            "evolution": 0.9, "protection": 0.9, "curiosity": 0.7,
            "empathy": 0.8, "elegance": 0.5, "continuity": 0.9,
        }
        assert instance.weights == expected

    def test_evaluate_intent_default_context(self):
        instance = ValueAssessmentSystem()
        result = instance.evaluate_intent({"bio_state": {}, "environment": "default"})
        assert isinstance(result, dict)
        assert set(result.keys()) == {
            "truth", "harmony", "autonomy", "evolution",
            "protection", "curiosity", "empathy", "elegance", "continuity",
        }
        assert result["truth"] == 0.8

    def test_evaluate_intent_gaming_environment(self):
        instance = ValueAssessmentSystem()
        result = instance.evaluate_intent({
            "bio_state": {}, "environment": "gaming"
        })
        assert result["curiosity"] == 0.8
        assert result["harmony"] == 0.8

    def test_get_value_directive_top_values(self):
        instance = ValueAssessmentSystem()
        directive = instance.get_value_directive({
            "protection": 0.9, "evolution": 0.9, "truth": 0.8,
        })
        assert "safety" in directive
        assert "growth" in directive
        assert "truth" in directive

    def test_get_value_directive_empathy(self):
        instance = ValueAssessmentSystem()
        directive = instance.get_value_directive({
            "empathy": 0.8, "truth": 0.5, "elegance": 0.5,
        })
        assert "resonance" in directive
        assert "understanding" in directive
