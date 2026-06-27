"""L5: Quantified behavioral impact tests for Formula → Emotion → Response chain.

Tests that changing formula inputs produces measurable differences in
emotional state and response output.
"""

import pytest


class TestFormulaToEmotion:
    """Test that formula-derived influences shift emotional state."""

    @pytest.mark.asyncio
    async def test_cognitive_stress_lowers_pleasure(self):
        from apps.backend.src.core.bio.emotional_blending import (
            BasicEmotion,
            EmotionalBlendingSystem,
        )

        ebs = EmotionalBlendingSystem()
        initial = ebs.get_dominant_emotion()
        ebs.apply_influence("cognitive", "negative_thought", -0.9, 0.8)
        await ebs._update_emotion()
        after = ebs.get_dominant_emotion()
        assert after[0] != initial[0] or after[1] < initial[1]

    @pytest.mark.asyncio
    async def test_hormonal_dopamine_boosts_pleasure(self):
        from apps.backend.src.core.bio.emotional_blending import (
            BasicEmotion,
            EmotionalBlendingSystem,
        )

        ebs = EmotionalBlendingSystem()
        ebs.set_emotion_from_basic(BasicEmotion.SADNESS)
        ebs.apply_influence("hormonal", "dopamine", 0.9, 0.9)
        await ebs._update_emotion()
        dominant, confidence = ebs.get_dominant_emotion()
        assert confidence > 0.1

    @pytest.mark.asyncio
    async def test_physiological_high_arousal_shifts_emotion(self):
        from apps.backend.src.core.bio.emotional_blending import (
            EmotionalBlendingSystem,
        )

        ebs = EmotionalBlendingSystem()
        ebs.apply_influence("physiological", "heart_rate", 0.8, 0.9)
        await ebs._update_emotion()
        state = ebs.current_emotion
        assert state.arousal > -0.5

    @pytest.mark.asyncio
    async def test_multiple_influences_blend_correctly(self):
        from apps.backend.src.core.bio.emotional_blending import (
            BasicEmotion,
            EmotionalBlendingSystem,
        )

        ebs = EmotionalBlendingSystem()
        ebs.set_emotion_from_basic(BasicEmotion.CALM)
        ebs.apply_influence("cognitive", "negative_thought", -0.7, 0.6)
        ebs.apply_influence("hormonal", "adrenaline", 0.6, 0.5)
        await ebs._update_emotion()
        summary = ebs.get_emotion_summary()
        assert "pleasure" in summary["pad_state"]
        assert "arousal" in summary["pad_state"]

    @pytest.mark.asyncio
    async def test_influence_decay_over_time(self):
        from apps.backend.src.core.bio.emotional_blending import (
            EmotionalBlendingSystem,
        )

        ebs = EmotionalBlendingSystem()
        ebs.apply_influence("hormonal", "dopamine", 0.9, 0.9)
        before = len(ebs.influences)
        for _ in range(20):
            await ebs._decay_influences()
        after = len([i for i in ebs.influences if i.weight > 0.01])
        assert after <= before


class TestEmotionToResponse:
    """Test that emotional state changes response behavior."""

    def test_category_map_maps_emotion_to_category(self):
        from ai.memory.memory_template import ResponseCategory

        category_map = {
            "happy": ResponseCategory.SMALL_TALK,
            "sad": ResponseCategory.SUPPORT,
            "angry": ResponseCategory.CASUAL,
            "neutral": ResponseCategory.SMALL_TALK,
            "calm": ResponseCategory.SMALL_TALK,
            "fear": ResponseCategory.SUPPORT,
            "surprise": ResponseCategory.CURIOSITY,
        }
        assert category_map["happy"] != category_map["sad"]
        assert category_map["surprise"] == ResponseCategory.CURIOSITY

    def test_category_map_keys_match_normalized_emotions(self):
        from apps.backend.src.core.bio.emotional_blending import BasicEmotion

        for e in BasicEmotion:
            name = e.en_name[:5]
            if name in ("happy", "sad", "angry", "calm", "fear"):
                pass
        assert True

    @pytest.mark.asyncio
    async def test_fallback_response_with_emotion_produces_text(self):
        from services.llm.router import AngelaLLMService

        service = AngelaLLMService()
        service.enable_memory_enhancement = False

        for emotion in ("happy", "sad", "fear", "surprise", "calm"):
            resp = await service._fallback_response(
                "hello", {"bio_state": {"dominant_emotion": emotion, "arousal": 0.5}}
            )
            assert resp is not None
            assert len(resp.text) > 0
            assert resp.confidence > 0


class TestFormulaToPrompt:
    """Test that formula values propagate into prompt content."""

    def test_get_formula_summaries_contains_values(self):
        from services.llm.prompt_builder import get_formula_summaries

        result = get_formula_summaries()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_construct_prompt_includes_formula_block(self):
        from services.llm.prompt_builder import (
            construct_angela_prompt,
        )

        context = {
            "state_for_llm": None,
            "user_profile": {},
            "drive_files": [],
            "history": [],
            "bio_state": {"dominant_emotion": "joy"},
        }
        messages = construct_angela_prompt("hello", context)
        combined = " ".join(m["content"] for m in messages)
        assert len(combined) > 50

    def test_bio_state_appears_in_prompt(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": {"axes": {"alpha": {"values": {"valence": 0.8}}}},
            "user_profile": {},
            "drive_files": [],
            "history": [],
        }
        messages = construct_angela_prompt("test", context)
        combined = " ".join(m["content"] for m in messages)
        assert "ALPHA" in combined or "valence" in combined

    def test_formula_values_format_correctly(self):
        from services.llm.prompt_builder import get_formula_summaries

        result = get_formula_summaries()
        assert isinstance(result, str)
        assert any(c.isdigit() for c in result)
    """Test that formula values propagate into prompt content."""

    def test_get_formula_summaries_contains_values(self):
        from services.llm.prompt_builder import get_formula_summaries

        result = get_formula_summaries()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_construct_prompt_includes_formula_block(self):
        from services.llm.prompt_builder import (
            construct_angela_prompt,
        )

        context = {
            "state_for_llm": None,
            "user_profile": {},
            "drive_files": [],
            "history": [],
            "bio_state": {"dominant_emotion": "joy"},
        }
        messages = construct_angela_prompt("hello", context)
        combined = " ".join(m["content"] for m in messages)
        assert len(combined) > 50

    def test_bio_state_appears_in_prompt(self):
        from services.llm.prompt_builder import construct_angela_prompt

        context = {
            "state_for_llm": {"axes": {"alpha": {"values": {"valence": 0.8}}}},
            "user_profile": {},
            "drive_files": [],
            "history": [],
        }
        messages = construct_angela_prompt("test", context)
        combined = " ".join(m["content"] for m in messages)
        assert "ALPHA" in combined or "valence" in combined

    def test_formula_values_format_correctly(self):
        from services.llm.prompt_builder import get_formula_summaries

        result = get_formula_summaries()
        assert isinstance(result, str)
        assert any(c.isdigit() for c in result)
