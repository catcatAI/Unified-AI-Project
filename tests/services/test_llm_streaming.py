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
async def test_select_light_backend_routes_chitchat_to_qwen():
    """Dual-model slice: greeting/reflex without questions → executor slot."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from services.llm.providers.registry import LLMBackend
    from services.llm.router import AngelaLLMService

    service = object.__new__(AngelaLLMService)
    qwen_backend = SimpleNamespace(check_health=AsyncMock(return_value=True))
    service.backends = {LLMBackend.LLAMA_CPP_QWEN: qwen_backend}
    service._qwen_last_check = 0.0
    service._qwen_healthy = False

    async def fake_submit(coro, **kwargs):
        return await coro

    service._submit_waiting = fake_submit
    backend, btype = await service._select_light_backend("hey there friend")
    assert backend is qwen_backend
    assert btype == LLMBackend.LLAMA_CPP_QWEN
    # Questions stay on the thinker even when phrased as greetings.
    backend2, _ = await service._select_light_backend("hi, what is quantum physics")
    assert backend2 is None
    # No qwen slot → thinker.
    service.backends = {}
    backend3, _ = await service._select_light_backend("hey there friend")
    assert backend3 is None


@pytest.mark.asyncio
async def test_demote_unhealthy_active_backend():
    """A backend that just failed is probed; if down it is demoted at once."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from services.llm.providers.registry import LLMBackend
    from services.llm.router import AngelaLLMService

    dead = SimpleNamespace(check_health=AsyncMock(return_value=False))
    live = SimpleNamespace(check_health=AsyncMock(return_value=True))
    service = object.__new__(AngelaLLMService)
    service.backends = {LLMBackend.LLAMA_CPP: dead, LLMBackend.UNIFIED: live}
    service._pruned_backends = {}
    service.active_backend = dead
    service.active_backend_type = LLMBackend.LLAMA_CPP
    service.is_available = True
    service._qwen_last_check = 0.0
    service._qwen_healthy = False

    async def fake_submit(coro, **kwargs):
        return await coro

    service._submit_waiting = fake_submit
    picked = []
    service._pick_best_backend = lambda available: picked.append(list(available))

    demoted = await service._demote_unhealthy_active({"_used_backend_type": LLMBackend.LLAMA_CPP})
    assert demoted is True
    assert LLMBackend.LLAMA_CPP not in service.backends
    assert LLMBackend.LLAMA_CPP in service._pruned_backends
    assert picked and LLMBackend.UNIFIED in picked[0]


@pytest.mark.asyncio
async def test_demote_keeps_healthy_backend():
    from types import SimpleNamespace
    from unittest.mock import AsyncMock

    from services.llm.providers.registry import LLMBackend
    from services.llm.router import AngelaLLMService

    healthy = SimpleNamespace(check_health=AsyncMock(return_value=True))
    service = object.__new__(AngelaLLMService)
    service.backends = {LLMBackend.LLAMA_CPP: healthy}
    service._pruned_backends = {}
    service._submit_waiting = lambda coro, **kwargs: coro
    assert (
        await service._demote_unhealthy_active({"_used_backend_type": LLMBackend.LLAMA_CPP})
        is False
    )
    assert LLMBackend.LLAMA_CPP in service.backends


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
