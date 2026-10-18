# ANGELA-MATRIX: [L3] [β] [B] [L2]

"""B1 regression: generate_text must not bypass the unified→LLM fusion gate.

Internal callers (research synthesis, ProjectCoordinator, …) used to be routed
straight to the active unified backend, so open-domain prompts silently ate the
18-char n-gram output instead of the same cloud delegation the main chat path
gets (log ``[Research-Synth] … 18 chars``).
"""

from __future__ import annotations

import pytest
from core.interfaces.protocols import LLMResponse
from services.llm.router import AngelaLLMService


def _bare_service() -> AngelaLLMService:
    """AngelaLLMService without running the (heavy) __init__."""
    service = object.__new__(AngelaLLMService)
    service.is_available = True
    service.active_backend = object()
    service.stats = {"llm_calls": 0}
    return service


def _unified_backend_stub(text: str = "UNIFIED-OUT"):
    async def _call(backend, **kwargs):
        return LLMResponse(text=text, backend="unified", model="unified-test")

    return _call


class TestGenerateTextFusion:
    @pytest.mark.asyncio
    async def test_fusion_result_is_returned_verbatim(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()

        async def _must_not_run(*args, **kwargs):
            raise AssertionError("unified path must not run after a fusion hit")

        async def _fused(user_message, context, gen_params):
            return LLMResponse(text="FUSED-ANSWER", backend="google", model="gemini-test")

        monkeypatch.setattr(service, "_submit_backend_call", _must_not_run)
        monkeypatch.setattr(service, "_maybe_cloud_fusion", _fused)
        out = await service.generate_text("寫一段關於蝴蝶的短文")
        assert out == "FUSED-ANSWER"

    @pytest.mark.asyncio
    async def test_gated_prompt_falls_through_to_unified(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()

        async def _fused(user_message, context, gen_params):
            return None

        monkeypatch.setattr(service, "_maybe_cloud_fusion", _fused)
        monkeypatch.setattr(service, "_submit_backend_call", _unified_backend_stub())
        out = await service.generate_text("3+5=?")
        assert out == "UNIFIED-OUT"

    @pytest.mark.asyncio
    async def test_fusion_exception_is_swallowed_not_fatal(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()

        async def _fused(user_message, context, gen_params):
            raise RuntimeError("cloud down")

        monkeypatch.setattr(service, "_maybe_cloud_fusion", _fused)
        monkeypatch.setattr(service, "_submit_backend_call", _unified_backend_stub())
        out = await service.generate_text("hello there")
        assert out == "UNIFIED-OUT"

    @pytest.mark.asyncio
    async def test_unavailable_service_keeps_ed3n_fallback(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()
        service.is_available = False

        async def _fused(*args, **kwargs):
            raise AssertionError("fusion must not run when the service is unavailable")

        monkeypatch.setattr(service, "_maybe_cloud_fusion", _fused)
        monkeypatch.setattr(service, "_ed3n_fallback_text", lambda prompt: "ED3N-FALLBACK")
        out = await service.generate_text("hi")
        assert out == "ED3N-FALLBACK"
