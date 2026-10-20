"""
ANGELA-MATRIX: [L4] [γ] [B] [L1]
The HTTP providers must support token streaming.

The SSE endpoint (`POST /api/v1/chat/stream`) delivers tokens as the model
produces them — but only the llama.cpp provider implemented streaming, so a
cloud backend answered in one piece and the desktop app could not show a
progressive reply. These tests pin the streaming contract of the OpenAI,
Ollama, Anthropic and Google providers against a fake HTTP response.
"""

import json

import pytest
from services.llm.providers.anthropic import AnthropicAPIBackend
from services.llm.providers.google import GoogleAPIBackend
from services.llm.providers.ollama import OllamaBackend
from services.llm.providers.openai import OpenAIAPIBackend


class _FakeContent:
    """The aiohttp response.content iterator (async)."""

    def __init__(self, lines):
        self._lines = list(lines)

    def __aiter__(self):
        async def _gen():
            for line in self._lines:
                yield line

        return _gen()


class _FakeResponse:
    def __init__(self, lines, status=200):
        self.content = _FakeContent(lines)
        self.status = status

    async def text(self):
        return "error body"

    async def json(self):
        return {}


class _FakeSession:
    """A minimal aiohttp-session stand-in."""

    def __init__(self, response):
        self._response = response
        self.kwargs = None

    def post(self, url, **kwargs):
        self.kwargs = kwargs
        return self._ctx()

    def get(self, url, **kwargs):
        return self._ctx()

    def _ctx(self):
        response = self._response

        class _Ctx:
            async def __aenter__(self):
                return response

            async def __aexit__(self, *exc):
                return False

        return _Ctx()


def _patch_session(backend, response):
    session = _FakeSession(response)
    backend._get_session = lambda: session  # type: ignore[method-assign]
    return session


async def _collect(backend, prompt="hi"):
    pieces = []

    async def _cb(piece):
        pieces.append(piece)

    result = await backend.generate_stream(prompt, _cb)
    return result, pieces


@pytest.mark.asyncio
class TestOpenAIStreaming:
    async def test_deltas_reach_the_callback(self):
        backend = OpenAIAPIBackend(api_key="k")
        _patch_session(
            backend,
            _FakeResponse(
                [
                    'data: {"choices":[{"delta":{"content":"\u4f60"}}]}\n'.encode(),
                    'data: {"choices":[{"delta":{"content":"\u597d"}}]}\n'.encode(),
                    b"data: [DONE]\n",
                ]
            ),
        )
        result, pieces = await _collect(backend)
        assert pieces == ["你", "好"]
        assert result.text == "你好"

    async def test_a_non_200_is_reported_as_an_error(self):
        backend = OpenAIAPIBackend(api_key="k")
        _patch_session(backend, _FakeResponse([], status=500))
        result, pieces = await _collect(backend)
        assert result.error
        assert not pieces

    async def test_generate_without_a_callback_stays_non_streaming(self):
        backend = OpenAIAPIBackend(api_key="k")
        session = _patch_session(backend, _FakeResponse([]))
        # The non-streaming path must not ask for a stream.
        await backend.generate("hi")
        assert session.kwargs["json"].get("stream") is None


@pytest.mark.asyncio
class TestOllamaStreaming:
    async def test_ndjson_deltas_reach_the_callback(self):
        backend = OllamaBackend(base_url="http://localhost:11434", model="qwen")
        _patch_session(
            backend,
            _FakeResponse(
                [
                    '{"message":{"content":"\u54c8"}}\n'.encode(),
                    '{"message":{"content":"\u56c9"}}\n'.encode(),
                ]
            ),
        )
        result, pieces = await _collect(backend)
        assert pieces == ["哈", "囉"]
        assert result.text == "哈囉"


@pytest.mark.asyncio
class TestAnthropicStreaming:
    async def test_content_block_deltas_reach_the_callback(self):
        backend = AnthropicAPIBackend(api_key="k")
        _patch_session(
            backend,
            _FakeResponse(
                [
                    b'event: content_block_delta\ndata: {"delta":{"text":"a"}}\n',
                    b'event: content_block_delta\ndata: {"delta":{"text":"b"}}\n',
                ]
            ),
        )
        result, pieces = await _collect(backend)
        assert pieces == ["a", "b"]
        assert result.text == "ab"


@pytest.mark.asyncio
class TestGoogleStreaming:
    async def test_candidate_parts_reach_the_callback(self):
        backend = GoogleAPIBackend(api_key="k")
        _patch_session(
            backend,
            _FakeResponse(
                [
                    b'data: {"candidates":[{"content":{"parts":[{"text":"x"}]}}]}\n',
                    b'data: {"candidates":[{"content":{"parts":[{"text":"y"}]}}]}\n',
                ]
            ),
        )
        result, pieces = await _collect(backend)
        assert pieces == ["x", "y"]
        assert result.text == "xy"


@pytest.mark.asyncio
class TestStreamingRobustness:
    async def test_a_malformed_chunk_is_skipped_not_fatal(self):
        backend = OpenAIAPIBackend(api_key="k")
        _patch_session(
            backend,
            _FakeResponse(
                [
                    b"data: not-json\n",
                    b'data: {"choices":[{"delta":{"content":"ok"}}]}\n',
                ]
            ),
        )
        result, pieces = await _collect(backend)
        assert pieces == ["ok"]
        assert result.text == "ok"

    async def test_a_failing_callback_does_not_abort_the_stream(self):
        backend = OpenAIAPIBackend(api_key="k")
        _patch_session(
            backend,
            _FakeResponse(
                [
                    b'data: {"choices":[{"delta":{"content":"a"}}]}\n',
                    b'data: {"choices":[{"delta":{"content":"b"}}]}\n',
                ]
            ),
        )

        def _boom(_piece):
            raise RuntimeError("callback exploded")

        result = await backend.generate_stream("hi", _boom)
        assert result.text == "ab"

    async def test_the_shared_delta_extraction_handles_the_shapes(self):
        from services.llm.providers.base import BaseLLMBackend

        payload = json.dumps({"choices": [{"delta": {"content": "hi"}}]})
        assert BaseLLMBackend._extract_delta(payload, ["choices", 0, "delta", "content"]) == "hi"
        assert BaseLLMBackend._extract_delta("nonsense", ["a"]) == ""
        assert BaseLLMBackend._extract_delta(json.dumps({"x": {"y": "z"}}), ["x", "y"]) == "z"
