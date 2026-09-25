# ANGELA-MATRIX: [L3] [β] [B] [L0]

import pytest

from services.llm.providers.llamacpp import LlamaCppBackend


class _Response:
    def __init__(self, status: int, payload: dict | None = None):
        self.status = status
        self._payload = payload or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False

    async def json(self):
        return self._payload


class _Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requested_urls = []

    def get(self, url, **kwargs):
        self.requested_urls.append(url)
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_health_prefers_openai_compatible_model_endpoint(monkeypatch) -> None:
    session = _Session(
        [_Response(200, {"data": [{"id": "qwen-local"}]})]
    )
    backend = LlamaCppBackend(model=None)
    monkeypatch.setattr(backend, "_get_session", lambda: session)

    assert await backend.check_health() is True
    assert backend.model == "qwen-local"
    assert session.requested_urls == ["http://127.0.0.1:8080/v1/models"]


@pytest.mark.asyncio
async def test_health_falls_back_to_legacy_endpoint(monkeypatch) -> None:
    session = _Session([_Response(404), _Response(200)])
    backend = LlamaCppBackend(model="configured-model")
    monkeypatch.setattr(backend, "_get_session", lambda: session)

    assert await backend.check_health() is True
    assert session.requested_urls == [
        "http://127.0.0.1:8080/v1/models",
        "http://127.0.0.1:8080/health",
    ]


def test_context_window_defaults_to_server_safe_value():
    backend = LlamaCppBackend()
    assert backend.context_window == 4096


def test_context_window_can_be_overridden():
    backend = LlamaCppBackend(context_window=8192)
    assert backend.context_window == 8192


@pytest.mark.asyncio
async def test_context_overflow_response_is_not_retried():
    from core.interfaces.protocols import LLMResponse
    from services.llm.router import _call_with_retry

    calls = 0

    async def backend_call():
        nonlocal calls
        calls += 1
        return LLMResponse(error="HTTP 400: maximum context length is 4096 tokens")

    response = await _call_with_retry(backend_call, max_retries=2, base_delay=0)
    assert calls == 1
    assert response is not None
    assert "maximum context length" in response.error


@pytest.mark.asyncio
async def test_local_llama_is_not_registered_as_cloud(monkeypatch):
    from services.llm.providers.registry import LLMBackend
    from services.llm.router import AngelaLLMService

    service = AngelaLLMService.__new__(AngelaLLMService)
    backend = LlamaCppBackend(model="local")
    service.active_backend = backend
    service.active_backend_type = LLMBackend.LLAMA_CPP
    service.backends = {LLMBackend.LLAMA_CPP: backend}
    service.meta_controller = None
    service.query_classifier = None
    service.model_bus = None
    monkeypatch.setattr(service, "_register_model_bus_handlers", lambda: None)

    await service._init_model_bus()

    assert service.model_bus is not None
    assert "cloud" not in service.model_bus._registry
