"""
Tests for P39 VisionCaptionService — LLM Vision semantic captioning.

Tests:
  - Service initialization and backend detection
  - MIME type detection from image bytes
  - Mock Gemini caption generation
  - Mock OpenAI caption generation
  - Fallback when all backends fail
  - Error handling for empty/missing data
  - MultimodalService integration
  - VisionPipeline integration marker

Total: 12 tests
"""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch


class _AsyncContextManager:
    """Wrap a response object so it can be used with async with."""
    def __init__(self, resp):
        self._resp = resp
    async def __aenter__(self):
        return self._resp
    async def __aexit__(self, *args):
        pass

import pytest

from services.vision_caption_service import VisionCaptionService, get_vision_caption_service


# =============================================================================
# Fixtures
# =============================================================================

_SAMPLE_PNG = (
    b"\x89PNG\r\n\x1a\n"  # PNG header
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

_SAMPLE_JPEG = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c"
    b"\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c"
    b"\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01"
    b"\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01"
    b"\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n"
    b"\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04"
    b"\x00\x00\x00\x00\x00\x01\x02\x03\x11\x04\x12!1A\x06\x13Qa\x07\"q\x142\x81"
    b"\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&'()*"
    b"456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a"
    b"\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa"
    b"\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca"
    b"\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9"
    b"\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x01\x01"
    b"\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06"
    b"\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07"
    b"\x05\x04\x04\x00\x01\x02\x77\x00\x01\x02\x03\x11\x04!1A\x06\x12!1a\x07\"q"
    b"\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19"
    b"\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88"
    b"\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8"
    b"\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8"
    b"\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7"
    b"\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc0\x00\x0f\x01"
    b"\x01\x01\x01\x01\x01\x01\x01\x01\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01"
    b"\x01\x11\x00\xff\xc4\x00\x17\x00\x01\x01\x01\x01\x01\x01\x01\x01\x01\x01"
    b"\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
)


@pytest.fixture(autouse=True)
def clear_env():
    """Clear and restore env vars for each test.

    Clears GEMINI_API_KEY, GOOGLE_API_KEY, and OPENAI_API_KEY to ensure
    test isolation across all caption tests.
    """
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
    return VisionCaptionService()


# =============================================================================
# Initialization Tests
# =============================================================================


class TestInitialization:
    """Tests for VisionCaptionService initialization and backend detection."""

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

    @pytest.mark.asyncio
    async def test_init_google_api_key_alias(self, svc):
        """GOOGLE_API_KEY also enables Gemini backend."""
        os.environ["GOOGLE_API_KEY"] = "test-google-key"
        ok = await svc.initialize()
        assert ok is True
        assert "gemini" in svc.backends


# =============================================================================
# MIME Type Detection Tests
# =============================================================================


class TestMimeDetection:
    """Tests for MIME type detection from raw bytes."""

    def test_detect_png(self):
        """PNG header -> image/png."""
        mime = VisionCaptionService._detect_mime_type(_SAMPLE_PNG)
        assert mime == "image/png"

    def test_detect_jpeg(self):
        """JPEG header -> image/jpeg."""
        mime = VisionCaptionService._detect_mime_type(_SAMPLE_JPEG)
        assert mime == "image/jpeg"

    def test_detect_default(self):
        """Unknown format -> image/png fallback."""
        mime = VisionCaptionService._detect_mime_type(b"some random bytes")
        assert mime == "image/png"


# =============================================================================
# Caption Generation Tests (mocked API)
# =============================================================================


def _make_mock_post(responses):
    """Create a mock for session.post that returns async context manager wrappers.

    Args:
        responses: A response dict or list of response dicts (for side_effect)
                   Each response: {"status": 200, "json": {...}, "text": "..."}
    """
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


class TestCaptionGeneration:
    """Tests for caption generation with mocked API calls."""

    @pytest.mark.asyncio
    async def test_caption_no_keys(self, svc):
        """No API keys -> returns error without making API call."""
        result = await svc.caption(_SAMPLE_PNG)
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
    async def test_caption_mock_gemini(self, svc):
        """Mock Gemini API call returns caption."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        await svc.initialize()

        mock_post = _make_mock_post({
            "status": 200,
            "json": {
                "candidates": [{
                    "content": {"parts": [{"text": "A red apple on a wooden table."}]}
                }]
            },
        })
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(_SAMPLE_PNG, language="en")
            assert result["backend"] == "gemini"
            assert "apple" in result["caption"]
            assert result["language"] == "en"
            assert result["time_ms"] > 0

    @pytest.mark.asyncio
    async def test_caption_mock_openai(self, svc):
        """Mock OpenAI API call returns caption."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        await svc.initialize()

        mock_post = _make_mock_post({
            "status": 200,
            "json": {
                "choices": [{"message": {"content": "A cute cat sitting on a couch."}}]
            },
        })
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(_SAMPLE_PNG, language="en",
                                       preferred_backend="openai")
            assert result["backend"] == "openai"
            assert "cat" in result["caption"]

    @pytest.mark.asyncio
    async def test_caption_gemini_fallback_to_openai(self, svc):
        """When Gemini fails, falls back to OpenAI."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        os.environ["OPENAI_API_KEY"] = "test-key"
        await svc.initialize()
        assert len(svc.backends) == 2

        mock_post = _make_mock_post([
            {"status": 500, "text": "Internal error"},
            {"status": 200, "json": {
                "choices": [{"message": {"content": "A beautiful sunset over the ocean."}}]
            }},
        ])
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(_SAMPLE_PNG, language="en")
            assert result["backend"] == "openai"
            assert "sunset" in result["caption"]

    @pytest.mark.asyncio
    async def test_caption_all_backends_fail(self, svc):
        """All backends fail -> returns error."""
        os.environ["GEMINI_API_KEY"] = "test-key"
        await svc.initialize()

        mock_post = _make_mock_post({"status": 500, "text": "Server error"})
        mock_session = MagicMock()
        mock_session.post = mock_post

        with patch.object(svc, "_get_session", return_value=mock_session):
            result = await svc.caption(_SAMPLE_PNG)
            assert result["backend"] == "none"
            assert "caption" in result
            assert result["caption"] == ""


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for the get_vision_caption_service singleton."""

    @pytest.mark.asyncio
    async def test_singleton_returns_same_instance(self):
        """get_vision_caption_service returns the same instance on repeated calls."""
        s1 = await get_vision_caption_service()
        s2 = await get_vision_caption_service()
        assert s1 is s2

    @pytest.mark.asyncio
    async def test_singleton_initializes_automatically(self):
        """Singleton auto-initializes on first access."""
        svc = await get_vision_caption_service()
        assert svc._initialized is True
        # No keys set in test env -> not available, but not crashed
        assert isinstance(svc.is_available, bool)
