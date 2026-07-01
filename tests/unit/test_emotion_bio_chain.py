"""Tests for Emotion→Biological cross-component chain (C³ 4.0)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_bio():
    bio = AsyncMock()
    bio.process_stress_event = AsyncMock()
    bio.process_relaxation_event = AsyncMock()
    return bio


class TestEmotionToBiologyMapping:
    """Verify emotion→stress/relaxation intensity mapping correctness."""

    def test_high_stress_emotions(self):
        from api.routes.chat_routes import _EMOTION_TO_STRESS_MAP
        for emotion in ("anger", "fear"):
            assert _EMOTION_TO_STRESS_MAP.get(emotion, 0) >= 0.3

    def test_medium_stress_emotions(self):
        from api.routes.chat_routes import _EMOTION_TO_STRESS_MAP
        for emotion in ("sadness", "disgust"):
            intensity = _EMOTION_TO_STRESS_MAP.get(emotion, 0)
            assert 0.1 <= intensity <= 0.2

    def test_low_stress_emotions(self):
        from api.routes.chat_routes import _EMOTION_TO_STRESS_MAP
        for emotion in ("surprise", "anticipation"):
            intensity = _EMOTION_TO_STRESS_MAP.get(emotion, 0)
            assert 0.0 < intensity <= 0.1

    def test_neutral_no_stress(self):
        from api.routes.chat_routes import _EMOTION_TO_STRESS_MAP
        assert "neutral" not in _EMOTION_TO_STRESS_MAP

    def test_relaxation_emotions(self):
        from api.routes.chat_routes import _EMOTION_TO_RELAXATION_MAP
        for emotion in ("joy", "trust"):
            assert _EMOTION_TO_RELAXATION_MAP.get(emotion, 0) >= 0.1

    def test_no_overlap_between_maps(self):
        from api.routes.chat_routes import _EMOTION_TO_STRESS_MAP, _EMOTION_TO_RELAXATION_MAP
        overlap = set(_EMOTION_TO_STRESS_MAP) & set(_EMOTION_TO_RELAXATION_MAP)
        assert len(overlap) == 0


class TestApplyEmotionToBiology:
    """Test _apply_emotion_to_biology calls correct bio methods."""

    @pytest.mark.parametrize("emotion,expected_method", [
        ("anger", "process_stress_event"),
        ("fear", "process_stress_event"),
        ("sadness", "process_stress_event"),
        ("joy", "process_relaxation_event"),
        ("trust", "process_relaxation_event"),
    ])
    @pytest.mark.asyncio
    async def test_calls_correct_method(self, emotion, expected_method, mock_bio):
        from api.routes.chat_routes import _apply_emotion_to_biology
        await _apply_emotion_to_biology(emotion, 0.8, mock_bio)
        method = getattr(mock_bio, expected_method)
        assert method.await_count == 1

    @pytest.mark.asyncio
    async def test_neutral_no_call(self, mock_bio):
        from api.routes.chat_routes import _apply_emotion_to_biology
        await _apply_emotion_to_biology("neutral", 0.5, mock_bio)
        mock_bio.process_stress_event.assert_not_awaited()
        mock_bio.process_relaxation_event.assert_not_awaited()

    @pytest.mark.parametrize("emotion,intensity,expected", [
        ("anger", 0.5, 0.3),
        ("fear", 1.0, 0.7),
        ("sadness", 0.5, 0.15),
        ("joy", 0.5, 0.15),
    ])
    @pytest.mark.asyncio
    async def test_stress_intensity_scaling(self, emotion, intensity, expected, mock_bio):
        from api.routes.chat_routes import _apply_emotion_to_biology
        await _apply_emotion_to_biology(emotion, intensity, mock_bio)
        if emotion in ("anger", "fear", "sadness"):
            args, _ = mock_bio.process_stress_event.await_args
            assert args[0] == pytest.approx(expected, abs=0.05)
        else:
            args, _ = mock_bio.process_relaxation_event.await_args
            assert args[0] == pytest.approx(expected, abs=0.05)

    @pytest.mark.asyncio
    async def test_intensity_caps_at_1(self, mock_bio):
        from api.routes.chat_routes import _apply_emotion_to_biology
        await _apply_emotion_to_biology("anger", 2.0, mock_bio)
        args, _ = mock_bio.process_stress_event.await_args
        assert args[0] <= 1.0

    @pytest.mark.asyncio
    async def test_stress_event_duration(self, mock_bio):
        from api.routes.chat_routes import _apply_emotion_to_biology
        await _apply_emotion_to_biology("fear", 0.8, mock_bio)
        _args, kwargs = mock_bio.process_stress_event.await_args
        assert kwargs.get("duration") == 15.0


class TestInjectEmotionBehavioralContext:
    """Test _inject_emotion_behavioral_context with bio integration."""

    @pytest.fixture
    def mock_emotion_system(self):
        es = MagicMock()
        es.apply_influence = MagicMock()
        es.get_behavioral_adjustment = MagicMock(return_value={
            "routing_mode": "conservative",
            "response_style": "calming",
            "emotional_state": "anxious",
            "intensity": 0.5,
        })
        return es

    @pytest.fixture
    def patches(self, mock_emotion_system, mock_bio):
        with patch("api.routes.chat_routes._get_emotion_system",
                   return_value=mock_emotion_system):
            yield {"es": mock_emotion_system, "bio": mock_bio}

    @pytest.mark.asyncio
    async def test_bio_called_when_provided(self, patches):
        from api.routes.chat_routes import _inject_emotion_behavioral_context
        context = {}
        await _inject_emotion_behavioral_context(
            {"emotion": "anger", "intensity": 0.8}, context, patches["bio"],
        )
        patches["bio"].process_stress_event.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_bio_not_called_when_none(self, patches):
        from api.routes.chat_routes import _inject_emotion_behavioral_context
        context = {}
        await _inject_emotion_behavioral_context(
            {"emotion": "anger", "intensity": 0.8}, context, None,
        )
        patches["bio"].process_stress_event.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_behavioral_context_injected(self, patches):
        from api.routes.chat_routes import _inject_emotion_behavioral_context
        context = {}
        await _inject_emotion_behavioral_context(
            {"emotion": "anger", "intensity": 0.5}, context, patches["bio"],
        )
        assert "emotional_behavior" in context
        assert context["emotional_behavior"]["routing_mode"] == "conservative"

    @pytest.mark.asyncio
    async def test_angela_emotion_injected(self, patches):
        from api.routes.chat_routes import _inject_emotion_behavioral_context
        context = {}
        await _inject_emotion_behavioral_context(
            {"emotion": "joy", "intensity": 0.7}, context, patches["bio"],
        )
        assert "angela_emotion" in context
        assert context["angela_emotion"]["routing_mode"] == "conservative"

    @pytest.mark.asyncio
    async def test_none_emotion_result_skips_all(self, patches):
        from api.routes.chat_routes import _inject_emotion_behavioral_context
        context = {}
        await _inject_emotion_behavioral_context(None, context, patches["bio"])
        assert context == {}
        patches["bio"].process_stress_event.assert_not_awaited()
        patches["es"].apply_influence.assert_not_called()
