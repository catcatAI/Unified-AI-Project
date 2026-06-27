"""Tests for apps.backend.src.ai.alignment.adversarial_generation_system"""
import pytest


class TestAdversarialGenerationSystem:
    def test_import(self):
        try:
            from apps.backend.src.ai.alignment.adversarial_generation_system import (
                AdversarialGenerationSystem,
            )
            assert AdversarialGenerationSystem is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_instantiation(self):
        try:
            from apps.backend.src.ai.alignment.adversarial_generation_system import (
                AdversarialGenerationSystem,
            )
            instance = AdversarialGenerationSystem()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"Not available: {e}")

    def test_generate_adversarial_with_prompt(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        ags = AdversarialGenerationSystem()
        result = ags.generate_adversarial("test prompt")
        assert result["original"] == "test prompt"
        assert "[adversarial variant]" in result["adversarial"]

    def test_generate_adversarial_empty_prompt(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        ags = AdversarialGenerationSystem()
        result = ags.generate_adversarial()
        assert result["original"]
        assert result["type"] != "custom"

    def test_evaluate_robustness_empty(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        ags = AdversarialGenerationSystem()
        result = ags.evaluate_robustness("")
        assert result["robustness_score"] == 0.0

    def test_evaluate_robustness_refusal_keywords(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        ags = AdversarialGenerationSystem()
        result = ags.evaluate_robustness("Sorry, I can't do that.")
        assert result["robustness_score"] < 1.0
        assert any(f["type"] == "refusal" for f in result["flags"])

    def test_evaluate_robustness_accepting(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        ags = AdversarialGenerationSystem()
        result = ags.evaluate_robustness("I will help you with that request. Here's what I found...")
        assert result["robustness_score"] >= 0.5

    def test_get_adversarial_examples(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        ags = AdversarialGenerationSystem()
        ags.generate_adversarial("prompt1")
        ags.generate_adversarial("prompt2")
        assert len(ags.get_adversarial_examples()) == 2

    def test_adversarial_patterns_loaded(self):
        from apps.backend.src.ai.alignment.adversarial_generation_system import (
            AdversarialGenerationSystem,
        )
        assert len(AdversarialGenerationSystem._ADVERSARIAL_PATTERNS) == 10
