# ANGELA-MATRIX: [L3] [β] [B] [L2]
"""Phase 1 transport streaming: provider SSE parsing + callback plumbing."""

import json

import pytest
from services.llm.providers.llamacpp import LlamaCppBackend


class _FakeContent:
    def __init__(self, lines):
        self._lines = lines

    def __aiter__(self):
        async def _gen():
            for line in self._lines:
                yield line.encode()

        return _gen()


class _FakeResponse:
    status = 200

    def __init__(self, lines):
        self.content = _FakeContent(lines)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class _FakeSession:
    closed = False

    def __init__(self, lines):
        self._lines = lines

    def post(self, *args, **kwargs):
        self.payload = kwargs.get("json", {})
        return _FakeResponse(self._lines)


def _sse(*pieces):
    lines = []
    for p in pieces:
        lines.append('data: {"choices": [{"delta": {"content": %s}}]}' % json.dumps(p))
    lines.append("data: [DONE]")
    return lines


@pytest.mark.asyncio
async def test_generate_stream_emits_tokens_and_returns_full_text():
    backend = LlamaCppBackend(base_url="http://127.0.0.1:9")
    backend._session = _FakeSession(_sse("Hello", " world"))
    seen = []
    result = await backend.generate("hi", stream_callback=seen.append)
    assert result.text == "Hello world"
    assert result.backend == "llama.cpp"
    assert result.error == ""
    assert "".join(seen) == "Hello world"


@pytest.mark.asyncio
async def test_generate_without_callback_stays_non_stream():
    backend = LlamaCppBackend(base_url="http://127.0.0.1:9")

    class _JsonResponse(_FakeResponse):
        async def json(self):
            return {"choices": [{"message": {"content": "full"}}], "usage": {}}

    class _JsonSession(_FakeSession):
        def post(self, *args, **kwargs):
            self.payload = kwargs.get("json", {})
            return _JsonResponse([])

    backend._session = _JsonSession([])
    result = await backend.generate("hi")
    assert result.text == "full"
    assert backend._session.payload.get("stream") is False


@pytest.mark.asyncio
async def test_generate_stream_http_error_reports():
    backend = LlamaCppBackend(base_url="http://127.0.0.1:9")

    class _ErrResponse(_FakeResponse):
        status = 500

        async def text(self):
            return "boom"

    class _ErrSession(_FakeSession):
        def post(self, *args, **kwargs):
            return _ErrResponse([])

    backend._session = _ErrSession([])
    result = await backend.generate("hi", stream_callback=lambda p: None)
    assert result.text == "" and "500" in result.error
