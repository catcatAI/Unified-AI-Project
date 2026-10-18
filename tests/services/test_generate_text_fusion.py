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
from services.llm.providers.registry import LLMBackend
from services.llm.router import AngelaLLMService, GenerationParams


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


class TestGenerateTextEditorial:
    """editorial=True（潤色/改寫）旁路封閉域閘門，並把 system_prompt 直達後端。"""

    @pytest.mark.asyncio
    async def test_editorial_marks_bypass_and_carries_system(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()
        captured: dict = {}

        async def _fused(user_message, context, gen_params):
            captured["context"] = dict(context)
            return LLMResponse(text="EDITED", backend="google", model="gemini-test")

        monkeypatch.setattr(service, "_maybe_cloud_fusion", _fused)
        out = await service.generate_text(
            "bench_20260922-091107.json（generated_at=…）基準段落",
            system_prompt="只潤色行文，不得改數字",
            editorial=True,
        )
        assert out == "EDITED"
        assert captured["context"]["bypass_fusion_gate"] is True
        assert captured["context"]["system_prompt"] == "只潤色行文，不得改數字"

    @pytest.mark.asyncio
    async def test_default_keeps_empty_context(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()
        captured: dict = {}

        async def _fused(user_message, context, gen_params):
            captured["context"] = dict(context)
            return LLMResponse(text="OUT", backend="google", model="gemini-test")

        monkeypatch.setattr(service, "_maybe_cloud_fusion", _fused)
        await service.generate_text("open-domain 段落", system_prompt="SYS")
        assert captured["context"] == {}

    @pytest.mark.asyncio
    async def test_editorial_bypass_skips_closed_domain_gate(self, monkeypatch: pytest.MonkeyPatch):
        service = _bare_service()
        service.active_backend_type = LLMBackend.UNIFIED
        service.config = {"deployment": {"mode": "local+llm"}}
        gate_calls: list = []

        def _gate_closed(text: str) -> bool:
            gate_calls.append(text)
            return True

        monkeypatch.setattr(service, "_fusion_open_domain_gate", _gate_closed)
        monkeypatch.setattr(service, "_fusion_candidates", lambda allowed: [])

        await service._maybe_cloud_fusion("rules=0 段落", {}, GenerationParams(5.0, 0.2, 64))
        assert len(gate_calls) == 1  # 預設：封閉域判定照跑 → 走 unified

        await service._maybe_cloud_fusion(
            "rules=0 段落", {"bypass_fusion_gate": True}, GenerationParams(5.0, 0.2, 64)
        )
        assert len(gate_calls) == 1  # editorial 旁路：封閉域判定不執行

    @pytest.mark.asyncio
    async def test_fusion_attempt_sends_system_prompt_verbatim(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        service = _bare_service()
        service.backends = {LLMBackend.GOOGLE: object()}
        captured: dict = {}

        async def _submit(backend, **kwargs):
            captured.update(kwargs)
            return LLMResponse(text="OK", backend="google", model="gemini-test")

        def _angela(*args, **kwargs):
            raise AssertionError("editorial 路徑不得做 Angela 風格包裝")

        monkeypatch.setattr(service, "_submit_backend_call", _submit)
        monkeypatch.setattr(service, "_construct_angela_prompt", _angela)
        resp = await service._fusion_attempt(
            LLMBackend.GOOGLE,
            "原文段落",
            {"system_prompt": "SYS", "bypass_fusion_gate": True},
            GenerationParams(5.0, 0.2, 64),
        )
        assert resp is not None and resp.text == "OK"
        msgs = captured["messages"]
        assert msgs[0] == {"role": "system", "content": "SYS"}
        assert msgs[1] == {"role": "user", "content": "原文段落"}
