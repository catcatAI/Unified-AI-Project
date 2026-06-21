# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L5]
# =============================================================================
# P41 Tests: ChatService semantic caption injection
#
# Tests ChatService's ability to generate and inject semantic captions
# from VisionCaptionService and AudioCaptionService into chat context.
# =============================================================================

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Minimal valid PNG (1x1 pixel) — used as placeholder image bytes
_SAMPLE_PNG = (
    b"\x89PNG\r\n\x1a\n" + b"\x00" * 4 + b"\x0d\x00\x00\x00\x0d" +
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde" +
    b"\x00" * 20
)

# Silence WAV (1 second, 16-bit mono 16kHz)
_SAMPLE_WAV = (
    b"RIFF\x24\xf0\xff\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
    b"\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\xf0\xff\x00"
    + b"\x00" * 8000  # 1 sec of silence at 16kHz
)


class _AsyncContextManager:
    """Helper: wrap a mock so it can be used with `async with`."""

    def __init__(self, mock_obj):
        self._mock = mock_obj

    async def __aenter__(self):
        return self._mock

    async def __aexit__(self, *args):
        pass


def _make_mock_post(status=200, text="A test caption"):
    """Create a mock for aiohttp.ClientSession.post that supports `async with`.

    Returns a tuple (mock_post, mock_response) so the caller can
    attach additional assertions to the response if needed.
    """
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.text = AsyncMock(return_value=text)
    # For streaming reads (audio)
    mock_resp.read = AsyncMock(return_value=b"mock_transcript")
    mock_post = MagicMock(return_value=_AsyncContextManager(mock_resp))
    return mock_post, mock_resp


async def _make_chat_service(mocked_modules=None):
    """Create a ChatService with all caption services mocked."""
    from services.chat_service import ChatService
    svc = ChatService()
    svc._initialized = True
    svc._llm_service = MagicMock()
    svc._llm_service.generate_response = AsyncMock(
        return_value=MagicMock(text="Test response", metadata={})
    )
    svc._vector_store = None
    svc._ham_memory = None
    svc._cultural_context = None
    svc._continuous_learning = None
    svc._garden_engine = None
    svc._ed3n_learning_integration = None
    return svc


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clear_env():
    """Remove all caption-related env vars before each test."""
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"):
        os.environ.pop(key, None)
    yield
    for key in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY"):
        os.environ.pop(key, nil)


# ===========================================================================
# T1: ChatService — Vision caption injection
# ===========================================================================

class TestChatVisionCaption:
    """ChatService injects VisionCaptionService results into context."""

    @pytest.mark.asyncio
    async def test_vision_caption_injected(self):
        """image_analysis with image_data triggers VisionCaptionService."""
        svc = await _make_chat_service()

        svc._vision_caption_service = AsyncMock()
        svc._vision_caption_service.is_available = True
        svc._vision_caption_service.caption = AsyncMock(return_value="A red apple on a wooden table.")

        ctx = {"image_analysis": {"filename": "test.png", "image_data": _SAMPLE_PNG}}
        await svc.generate_response("What's in this image?", context=ctx)

        assert ctx.get("image_caption") == "A red apple on a wooden table."
        svc._vision_caption_service.caption.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_vision_caption_unavailable(self):
        """When VisionCaptionService is not available, no caption injected."""
        svc = await _make_chat_service()
        svc._vision_caption_service = AsyncMock()
        svc._vision_caption_service.is_available = False

        ctx = {"image_analysis": {"filename": "test.png", "image_data": _SAMPLE_PNG}}
        await svc.generate_response("What's in this image?", context=ctx)

        assert "image_caption" not in ctx

    @pytest.mark.asyncio
    async def test_vision_caption_no_image_data(self):
        """No image_data → no caption attempt."""
        svc = await _make_chat_service()

        ctx = {"image_analysis": {"filename": "test.png"}}
        await svc.generate_response("What's in this image?", context=ctx)

        assert "image_caption" not in ctx

    @pytest.mark.asyncio
    async def test_vision_caption_exception_handled(self):
        """Exception in VisionCaptionService is caught gracefully."""
        svc = await _make_chat_service()
        svc._vision_caption_service = AsyncMock()
        svc._vision_caption_service.is_available = True
        svc._vision_caption_service.caption = AsyncMock(side_effect=RuntimeError("API unavailable"))

        ctx = {"image_analysis": {"filename": "test.png", "image_data": _SAMPLE_PNG}}
        await svc.generate_response("What's in this image?", context=ctx)

        assert "image_caption" not in ctx


# ===========================================================================
# T2: ChatService — Audio caption injection
# ===========================================================================

class TestChatAudioCaption:
    """ChatService injects AudioCaptionService results into context."""

    @pytest.mark.asyncio
    async def test_audio_caption_injected(self):
        """audio_analysis with audio_data triggers AudioCaptionService."""
        svc = await _make_chat_service()

        svc._audio_caption_service = AsyncMock()
        svc._audio_caption_service.is_available = True
        svc._audio_caption_service.caption = AsyncMock(return_value="A person speaking in a quiet room.")

        ctx = {"audio_analysis": {"filename": "test.wav", "audio_data": _SAMPLE_WAV}}
        await svc.generate_response("What's in this audio?", context=ctx)

        assert ctx.get("audio_caption") == "A person speaking in a quiet room."
        svc._audio_caption_service.caption.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_audio_caption_unavailable(self):
        """When AudioCaptionService is not available, no caption injected."""
        svc = await _make_chat_service()
        svc._audio_caption_service = AsyncMock()
        svc._audio_caption_service.is_available = False

        ctx = {"audio_analysis": {"filename": "test.wav", "audio_data": _SAMPLE_WAV}}
        await svc.generate_response("What's in this audio?", context=ctx)

        assert "audio_caption" not in ctx

    @pytest.mark.asyncio
    async def test_audio_caption_no_audio_data(self):
        """No audio_data → no caption attempt."""
        svc = await _make_chat_service()

        ctx = {"audio_analysis": {"filename": "test.wav"}}
        await svc.generate_response("What's in this audio?", context=ctx)

        assert "audio_caption" not in ctx

    @pytest.mark.asyncio
    async def test_audio_caption_exception_handled(self):
        """Exception in AudioCaptionService is caught gracefully."""
        svc = await _make_chat_service()
        svc._audio_caption_service = AsyncMock()
        svc._audio_caption_service.is_available = True
        svc._audio_caption_service.caption = AsyncMock(side_effect=RuntimeError("API unavailable"))

        ctx = {"audio_analysis": {"filename": "test.wav", "audio_data": _SAMPLE_WAV}}
        await svc.generate_response("What's in this audio?", context=ctx)

        assert "audio_caption" not in ctx


# ===========================================================================
# T3: ChatService — Both captions simultaneously
# ===========================================================================

class TestChatDualCaption:
    """Both vision and audio captions injected in a single request."""

    @pytest.mark.asyncio
    async def test_dual_caption(self):
        """Both image and audio captions injected in the same request."""
        svc = await _make_chat_service()

        svc._vision_caption_service = AsyncMock()
        svc._vision_caption_service.is_available = True
        svc._vision_caption_service.caption = AsyncMock(return_value="A cat sitting on a chair.")
        svc._audio_caption_service = AsyncMock()
        svc._audio_caption_service.is_available = True
        svc._audio_caption_service.caption = AsyncMock(return_value="Background music with birds chirping.")

        ctx = {
            "image_analysis": {"filename": "cat.png", "image_data": _SAMPLE_PNG},
            "audio_analysis": {"filename": "nature.wav", "audio_data": _SAMPLE_WAV},
        }
        await svc.generate_response("Describe both", context=ctx)

        assert ctx.get("image_caption") == "A cat sitting on a chair."
        assert ctx.get("audio_caption") == "Background music with birds chirping."

    @pytest.mark.asyncio
    async def test_dual_caption_one_unavailable(self):
        """If one caption service is unavailable, the other still works."""
        svc = await _make_chat_service()
        svc._vision_caption_service = AsyncMock()
        svc._vision_caption_service.is_available = True
        svc._vision_caption_service.caption = AsyncMock(return_value="A cat.")
        svc._audio_caption_service = AsyncMock()
        svc._audio_caption_service.is_available = False

        ctx = {
            "image_analysis": {"filename": "cat.png", "image_data": _SAMPLE_PNG},
            "audio_analysis": {"filename": "nature.wav", "audio_data": _SAMPLE_WAV},
        }
        await svc.generate_response("Describe both", context=ctx)

        assert ctx.get("image_caption") == "A cat."
        assert "audio_caption" not in ctx


# ===========================================================================
# T4: Chat routes — /chat/with-audio endpoint
# ===========================================================================

class TestChatWithAudioRoute:
    """Tests for the /chat/with-audio API endpoint."""

    @pytest.mark.asyncio
    async def test_route_sends_audio_context(self):
        """/chat/with-audio passes audio_analysis to _handle_chat_request."""
        from api.routes.chat_routes import chat_with_audio

        # Create a mock UploadFile
        mock_file = MagicMock()
        mock_file.content_type = "audio/wav"
        mock_file.filename = "test.wav"
        mock_file.read = AsyncMock(return_value=_SAMPLE_WAV)

        with patch("api.routes.chat_routes._handle_chat_request") as mock_handler:
            mock_handler.return_value = {"response_text": "I hear a test audio."}

            result = await chat_with_audio(
                message="What's this?",
                file=mock_file,
                session_id="test-session",
                user_name="TestUser",
            )

            assert result["response_text"] == "I hear a test audio."
            # Verify extra_context contains audio_analysis
            call_kwargs = mock_handler.call_args[1]
            extra = call_kwargs.get("extra_context", {})
            assert "audio_analysis" in extra
            assert extra["audio_analysis"]["filename"] == "test.wav"
            assert extra["audio_analysis"]["audio_data"] == _SAMPLE_WAV

    @pytest.mark.asyncio
    async def test_route_no_file(self):
        """/chat/with-audio works without file (text only)."""
        from api.routes.chat_routes import chat_with_audio

        with patch("api.routes.chat_routes._handle_chat_request") as mock_handler:
            mock_handler.return_value = {"response_text": "Hello back!"}

            result = await chat_with_audio(
                message="Hello",
                file=None,
                session_id="test-session",
                user_name="TestUser",
            )

            assert result["response_text"] == "Hello back!"
            call_kwargs = mock_handler.call_args[1]
            assert call_kwargs.get("extra_context") is None

    @pytest.mark.asyncio
    async def test_route_invalid_content_type(self):
        """/chat/with-audio skips non-audio files."""
        from api.routes.chat_routes import chat_with_audio

        mock_file = MagicMock()
        mock_file.content_type = "text/plain"
        mock_file.filename = "test.txt"

        with patch("api.routes.chat_routes._handle_chat_request") as mock_handler:
            mock_handler.return_value = {"response_text": "Text only response."}

            result = await chat_with_audio(
                message="Hello",
                file=mock_file,
                session_id="test-session",
                user_name="TestUser",
            )

            assert result["response_text"] == "Text only response."
            call_kwargs = mock_handler.call_args[1]
            assert call_kwargs.get("extra_context") is None


# ===========================================================================
# T5: Prompt builder — Caption template rendering
# ===========================================================================

class TestPromptBuilderCaptions:
    """Prompt builder correctly renders image_caption and audio_caption blocks."""

    def test_image_caption_template_present(self):
        """prompt_manager has angela.image_caption key."""
        from core.prompt_manager import get_prompt_manager
        pm = get_prompt_manager()
        tmpl = pm.get_template("angela.image_caption")
        assert tmpl is not None
        assert "zh" in tmpl.templates
        assert "en" in tmpl.templates

    def test_audio_caption_template_present(self):
        """prompt_manager has angela.audio_caption key."""
        from core.prompt_manager import get_prompt_manager
        pm = get_prompt_manager()
        tmpl = pm.get_template("angela.audio_caption")
        assert tmpl is not None
        assert "zh" in tmpl.templates
        assert "en" in tmpl.templates

    def test_image_caption_in_prompt(self):
        """construct_angela_prompt includes image_caption when in context."""
        from services.llm.prompt_builder import construct_angela_prompt

        ctx = {"image_caption": "A cat sitting on a chair."}
        messages = construct_angela_prompt("Test", ctx)

        # image_caption appears in system prompt
        system_content = messages[0]["content"]
        assert "A cat sitting on a chair." in system_content
        assert "Image Caption" in system_content or "語意圖像描述" in system_content

    def test_audio_caption_in_prompt(self):
        """construct_angela_prompt includes audio_caption when in context."""
        from services.llm.prompt_builder import construct_angela_prompt

        ctx = {"audio_caption": "A person speaking in a quiet room."}
        messages = construct_angela_prompt("Test", ctx)

        system_content = messages[0]["content"]
        assert "A person speaking in a quiet room." in system_content
        assert "Audio Caption" in system_content or "語意音頻描述" in system_content

    def test_both_captions_in_prompt(self):
        """Both captions appear in the prompt simultaneously."""
        from services.llm.prompt_builder import construct_angela_prompt

        ctx = {
            "image_caption": "A cat.",
            "audio_caption": "Birds chirping.",
        }
        messages = construct_angela_prompt("Test", ctx)

        system_content = messages[0]["content"]
        assert "A cat." in system_content
        assert "Birds chirping." in system_content
