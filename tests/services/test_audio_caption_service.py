"""
Tests for P40 AudioCaptionService — LLM Audio semantic captioning.

Tests:
  - Service initialization and backend detection
  - Audio duration detection from WAV header
  - Mock Gemini audio caption generation
  - Mock OpenAI Whisper transcription
  - Mock OpenAI combined caption (Whisper + GPT)
  - Fallback when all backends fail
  - Error handling for empty/large data
  - Silence WAV generation utility
  - MultimodalService integration

Total: 15 tests
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch
import struct

import pytest

from services.audio_caption_service import AudioCaptionService, get_audio_caption_service


# =============================================================================
# Fixtures
# =============================================================================


def _make_silence_wav(duration_sec: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Generate a silent WAV file for testing."""
    return AudioCaptionService.generate_silence(duration_sec, sample_rate)


class _AsyncContextManager:
    """Wrap a response object so it can be used with async with."""
    def __init__(self, resp):
        self._resp = resp
    async def __aenter__(self):
        return self._resp
    async def __aexit__(self, *args):
        pass


def _make_mock_post(responses):
    """Create a mock for session.post that returns async context manager wrappers."""
    if isinstance(responses, dict):
        responses = [responses]

    def _make_resp(data):
        resp = MagicMock()
        resp.status = data.get("status", 200)
        resp.json = AsyncMock(return_value=data.get("json", {}))
        resp.text = AsyncMock(return_value=data.get("text", "OK"))
        resp.__aenter__ = AsyncMock(return_value=resp)
        resp.__aexit__ = AsyncMock(return_value=None)
        return resp

    wrapped = [_make_resp(r) for r in responses]
    if len(wrapped) == 1:
        return MagicMock(return_value=_AsyncContextManager(wrapped[0]))
    else:
        return MagicMock(side_effect=[_AsyncContextManager(w) for w in wrapped])


@pytest.fixture(autouse=True)
def clear_env():
    """Clear and restore env vars for each test."""
    old_gemini = os.environ.get("GEMINI_API_KEY")
    old_google = os.environ.get("GOOGLE_API_KEY")
    old_openai = os.environ.get("OPENAI_API_KEY")
    for key in ["GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"]:
        os.environ.pop(key, None)
    yield
    if old_gemini:
        os.environ["GEMINI_API_KEY"] = old_gemini
    if old_google:
        os.environ["GOOGLE_API_KEY"] = old_google
    if old_openai:
        os.environ["OPENAI_API_KEY"] = old_openai


@pytest.fixture
def svc():
    return AudioCaptionService()


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInitialization:
    """Tests for AudioCaptionService initialization and backend detection."""

    def test_init_no_keys(self, svc):
        """No API keys configured -> not available."""
        assert svc._initialized is False
        assert svc.is_available is False

    @pytest.mark.asyncio
    async def test_init_with_gemini_key(self, svc):
        """GEMINI_API_KEY enables Gemini backend."""
        os.environ["GEMINI_API_KEY"] = "test-gemini-key-123"
        ok = await svc.initialize()
        assert ok is True
        assert "gemini" in svc.backends

    @pytest.mark.asyncio
    async def test_init_with_openai_key(self, svc):
        """OPENAI_API_KEY enables OpenAI backend."""
        os.environ["OPENAI_API_KEY"] = "test-openai-key-456"
        ok = await svc.initialize()
        assert ok is True
        assert "openai" in svc.backends

    @pytest.mark.asyncio
    async def test_init_placeholder_key_ignored(self, svc):
        """Placeholder API keys are ignored (not real credentials)."""
        os.environ["GEMINI_API_KEY"] = "your_gemini_api_key_here"
        os.environ["OPENAI_API_KEY"] = "PLACEHOLDER"
        ok = await svc.initialize()
        assert ok is False
        assert len(svc.backends) == 0


# =============================================================================
# Audio Duration Detection Tests
# =============================================================================


class TestDurationDetection:
    """Tests for audio duration detection from WAV header."""

    def test_detect_silence_duration(self):
        """Silence WAV duration matches expected."""
        wav = _make_silence_wav(1.0, 16000)
        duration = AudioCaptionService._detect_audio_duration(wav)
        assert abs(duration - 1.0) < 0.01

    def test_detect_short_duration(self):
        """Short silence has correct duration."""
        wav = _make_silence_wav(0.25, 16000)
        duration = AudioCaptionService._detect_audio_duration(wav)
        assert abs(duration - 0.25) < 0.01

    def test_detect_empty_returns_zero(self):
        """Empty bytes returns 0 duration."""
        duration = AudioCaptionService._detect_audio_duration(b"")
        assert duration == 0.0

    def test_detect_invalid_returns_zero(self):
        """Non-WAV bytes returns 0 duration."""
        duration = AudioCaptionService._detect_audio_duration(b"not a wav file")
        assert duration == 0.0


# =============================================================================
# Silence WAV Generation Tests
# =============================================================================


class TestSilenceGeneration:
    """Tests for the generate_silence utility."""

    def test_generates_valid_wav(self):
        """Generated WAV has valid RIFF header."""
        wav = AudioCaptionService.generate_silence(0.5, 16000)
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"

    def test_correct_sample_count(self):
        """Generated WAV has expected number of samples."""
        wav = AudioCaptionService.generate_silence(1.0, 16000)
        data_size = len(wav) - 44
        assert data_size == 32000  # 16000 samples * 2 bytes

    def test_generates_silence(self):
        """Generated WAV contains only zeros (silence)."""
        wav = AudioCaptionService.generate_silence(0.5, 16000)
        samples = wav[44:]
        assert all(b == 0 for b in samples)


# =============================================================================
# Caption Generation Tests (mocked API)
# =============================================================================


class TestCaptionGeneration:
    """Tests for caption generation with mocked API calls."""

    @pytest.mark.asyncio
    async def test_caption_no_keys(self, svc):
        """No API keys -> returns error without making API call."""
        wav = _make_silence_wav()
        result = await svc.caption(wav)
        assert result["backend"] == "none"
        assert "error" in result
        assert "API keys" in result["error"]

    @pytest.mark.asyncio
    async def test_caption_empty_data(self, svc):
        """Empty data -> returns error."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        await svc.initialize()
        result = await svc.caption(b"")
        assert result["backend"] == "none"
        assert "Empty" in result.get("error", "")

    @pytest.mark.asyncio
    async def test_caption_too_large(self, svc):
        """Data exceeding max size -> returns error."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        await svc.initialize()
        large_data = b"x" * (svc.MAX_AUDIO_SIZE + 1)
        result = await svc.caption(large_data)
        assert result["backend"] == "none"
        assert "too large" in result.get("error", "").lower()

    @pytest.mark.asyncio
    async def test_caption_mock_gemini(self, svc):
        """Mock Gemini Audio API call returns caption."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        await svc.initialize()
        wav = _make_silence_wav()

        mock_post = _make_mock_post({
            "status": 200,
            "json": {
                "candidates": [{
                    "content": {"parts": [{"text": "這段音頻包含一個人的講話聲，語氣平和，背景安靜。"}]}
                }]
            },
        })
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(wav, language="zh")
            assert result["backend"] == "gemini"
            assert "講話" in result["caption"]
            assert result["language"] == "zh"

    @pytest.mark.asyncio
    async def test_caption_mock_openai_transcribe(self, svc):
        """Mock OpenAI Whisper transcription returns text."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        await svc.initialize()
        wav = _make_silence_wav()

        mock_post = _make_mock_post({
            "status": 200,
            "json": {"text": "Hello, this is a test recording."},
        })
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(wav, language="en", mode="transcribe",
                                       preferred_backend="openai")
            assert result["backend"] == "openai"
            assert "Hello" in result["caption"]
            assert result["mode"] == "transcribe"

    @pytest.mark.asyncio
    async def test_caption_mock_openai_describe(self, svc):
        """Mock OpenAI combined describe (Whisper + GPT) returns description."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        await svc.initialize()
        wav = _make_silence_wav()

        # Whisper response + GPT response
        mock_post = _make_mock_post([
            {"status": 200, "json": {"text": "Birds chirping in a forest"}},
            {"status": 200, "json": {
                "choices": [{"message": {
                    "content": "This audio contains birds chirping in a peaceful forest environment."
                }}]
            }},
        ])
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(wav, language="en", mode="describe",
                                       preferred_backend="openai")
            assert result["backend"] == "openai"
            assert "birds" in result["caption"].lower() or "forest" in result["caption"].lower()

    @pytest.mark.asyncio
    async def test_caption_gemini_fallback_to_openai(self, svc):
        """When Gemini fails, falls back to OpenAI (Whisper -> GPT pipeline)."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        os.environ["OPENAI_API_KEY"] = "test-key"
        await svc.initialize()
        assert len(svc.backends) == 2
        wav = _make_silence_wav()

        # Need 3 responses: 1 gemini (fail) + 2 openai (Whisper + GPT)
        mock_post = _make_mock_post([
            {"status": 500, "text": "Gemini error"},
            {"status": 200, "json": {"text": "birds singing in a garden"}},
            {"status": 200, "json": {
                "choices": [{"message": {"content": "The audio contains birds singing in a garden."}}]
            }},
        ])
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(wav, language="en")
            assert result["backend"] == "openai"
            assert "birds" in result["caption"].lower() or "garden" in result["caption"].lower()

    @pytest.mark.asyncio
    async def test_caption_all_backends_fail(self, svc):
        """All backends fail -> returns error."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        await svc.initialize()
        wav = _make_silence_wav()

        mock_post = _make_mock_post({"status": 500, "text": "Server error"})
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(wav)
            assert result["backend"] == "none"
            assert "caption" in result
            assert result["caption"] == ""


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for the get_audio_caption_service singleton."""

    @pytest.mark.asyncio
    async def test_singleton_returns_same_instance(self):
        """get_audio_caption_service returns the same instance on repeated calls."""
        s1 = await get_audio_caption_service()
        s2 = await get_audio_caption_service()
        assert s1 is s2

    @pytest.mark.asyncio
    async def test_singleton_initializes_automatically(self):
        """Singleton auto-initializes on first access."""
        svc = await get_audio_caption_service()
        assert svc._initialized is True
        assert isinstance(svc.is_available, bool)
