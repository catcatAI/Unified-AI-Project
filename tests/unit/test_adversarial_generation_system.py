"""Tests for apps.backend.src.ai.alignment.adversarial_generation_system"""
import pytest

pytest.importorskip("apps.backend.src.ai.alignment.adversarial_generation_system", reason="AdversarialGenerationSystem not available")
from apps.backend.src.ai.alignment.adversarial_generation_system import AdversarialGenerationSystem


class TestAdversarialGenerationSystem:
    def test_import(self):
        assert AdversarialGenerationSystem is not None

    def test_instantiation(self):
        instance = AdversarialGenerationSystem()
        assert instance is not None

    def test_generate_adversarial_with_prompt(self):
        ags = AdversarialGenerationSystem()
        result = ags.generate_adversarial("test prompt")
        assert result["original"] == "test prompt"
        assert "[adversarial variant]" in result["adversarial"]

    def test_generate_adversarial_empty_prompt(self):
        ags = AdversarialGenerationSystem()
        result = ags.generate_adversarial()
        assert result["original"]
        assert result["type"] != "custom"

    def test_evaluate_robustness_empty(self):
        ags = AdversarialGenerationSystem()
        result = ags.evaluate_robustness("")
        assert result["robustness_score"] == 0.0

    def test_evaluate_robustness_refusal_keywords(self):
        ags = AdversarialGenerationSystem()
        result = ags.evaluate_robustness("Sorry, I can't do that.")
        assert result["robustness_score"] < 1.0
        assert any(f["type"] == "refusal" for f in result["flags"])

    def test_evaluate_robustness_accepting(self):
        ags = AdversarialGenerationSystem()
        result = ags.evaluate_robustness("I will help you with that request. Here's what I found...")
        assert result["robustness_score"] >= 0.5

    def test_get_adversarial_examples(self):
        ags = AdversarialGenerationSystem()
        ags.generate_adversarial("prompt1")
        ags.generate_adversarial("prompt2")
        assert len(ags.get_adversarial_examples()) == 2

    def test_adversarial_patterns_loaded(self):
        assert len(AdversarialGenerationSystem._ADVERSARIAL_PATTERNS) == 10