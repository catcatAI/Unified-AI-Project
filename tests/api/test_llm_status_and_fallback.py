"""Regression tests for the LLM fallback/status fixes (workspace-2 run).

Covers three defects found by actually running the project on Linux Mint:

1. ``_try_fallback_chain`` matched configured fallback ids by raw substring, so
   ``llamacpp-local`` never matched ``LLAMA_CPP`` (separator mismatch).  A
   backend hiccup therefore degraded straight to "I can't do that" while other
   healthy local models sat idle.  The chain now also appends registered
   backends the configured chain does not mention.
2. A successful fallback set ``active_backend`` but not ``active_backend_type``,
   so ``/llm/status`` reported the wrong active backend afterwards.
3. ``/llm/status`` reported ``type: "unknown"`` (read a non-existent
   ``_backend_type`` attribute) and ``health: "unknown"`` always, and hid
   configured-but-pruned backends entirely.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))

from core.interfaces.protocols import LLMResponse  # noqa: E402
from services.llm.providers.registry import LLMBackend  # noqa: E402
from services.llm.router import AngelaLLMService  # noqa: E402


def _bare_service() -> AngelaLLMService:
    """AngelaLLMService without running the (heavy) __init__."""
    return object.__new__(AngelaLLMService)


class _FakeBackend:
    """Stands in for a real backend; generate() is driven by the test."""

    def __init__(self, text: str = "ok", error: str = "") -> None:
        self.text = text
        self.error = error

    async def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        return LLMResponse(text=self.text, error=self.error, backend="fake")


class TestBackendNameMatching:
    ALL = [
        LLMBackend.LLAMA_CPP,
        LLMBackend.LLAMA_CPP_QWEN,
        LLMBackend.OLLAMA,
        LLMBackend.GOOGLE,
        LLMBackend.ANTHROPIC,
        LLMBackend.UNIFIED,
        LLMBackend.GARDEN,
    ]

    def _plan(self, chain: List[str], backends: List[Any], exclude: Any = None) -> List[Any]:
        svc = _bare_service()
        svc.backends = {bt: _FakeBackend() for bt in backends}
        return svc._plan_fallback_backends(chain, exclude=exclude)

    @pytest.mark.parametrize(
        ("configured", "expected_first"),
        [
            ("llamacpp-local", LLMBackend.LLAMA_CPP),
            ("llamacpp-qwen", LLMBackend.LLAMA_CPP_QWEN),
            ("ollama-llama3", LLMBackend.OLLAMA),
            ("google-gemini", LLMBackend.GOOGLE),
            ("anthropic-claude", LLMBackend.ANTHROPIC),
            ("unified-1g", LLMBackend.UNIFIED),
            ("garden-1g", LLMBackend.GARDEN),
        ],
    )
    def test_configured_id_resolves_to_the_right_slot(
        self, configured: str, expected_first: Any
    ) -> None:
        """Config ids carry separators; enum values do not — both must match."""
        got = self._plan([configured], list(self.ALL))
        assert got[0] is expected_first
        # pass 3 guarantees every registered backend stays reachable
        assert set(got) == set(self.ALL)

    @pytest.mark.parametrize(
        ("configured", "expected_first"),
        [
            # exact match wins over prefix, so a slot never lands on its sibling
            ("llamacpp-qwen", LLMBackend.LLAMA_CPP_QWEN),
            ("llamacpp-local", LLMBackend.LLAMA_CPP),
        ],
    )
    def test_sibling_slots_do_not_cross_match(self, configured: str, expected_first: Any) -> None:
        got = self._plan([configured], [LLMBackend.LLAMA_CPP, LLMBackend.LLAMA_CPP_QWEN])
        assert got[0] is expected_first

    def test_prefix_match_when_no_exact_slot_exists(self) -> None:
        got = self._plan(["llamacpp-local"], [LLMBackend.LLAMA_CPP])
        assert got == [LLMBackend.LLAMA_CPP]

    def test_unknown_id_still_reaches_registered_backends(self) -> None:
        """A chain naming only disabled backends must not end in a refusal."""
        got = self._plan(
            ["ollama-llama3", "anthropic-claude", "google-gemini"],
            [LLMBackend.LLAMA_CPP, LLMBackend.LLAMA_CPP_QWEN],
        )
        assert LLMBackend.LLAMA_CPP in got
        assert LLMBackend.LLAMA_CPP_QWEN in got

    def test_failed_backend_is_excluded(self) -> None:
        got = self._plan(
            ["llamacpp-local"],
            [LLMBackend.LLAMA_CPP, LLMBackend.UNIFIED],
            exclude=LLMBackend.LLAMA_CPP,
        )
        assert LLMBackend.LLAMA_CPP not in got
        assert got[0] is LLMBackend.UNIFIED

    def test_planned_once_only(self) -> None:
        got = self._plan(
            ["llamacpp-local", "llamacpp", "llama"],
            [LLMBackend.LLAMA_CPP],
        )
        assert got == [LLMBackend.LLAMA_CPP]

    @pytest.mark.parametrize("chain", ([], ["nope-1"], ["ollama-llama3"]))
    def test_empty_or_unmatched_chain_still_returns_candidates(self, chain: List[str]) -> None:
        assert self._plan(chain, [LLMBackend.GARDEN, LLMBackend.UNIFIED]) == [
            LLMBackend.GARDEN,
            LLMBackend.UNIFIED,
        ]

    def test_empty_inputs_never_match(self) -> None:
        assert AngelaLLMService._backend_token("") == ""
        assert AngelaLLMService._backend_token("llamacpp-local") == "llamacpplocal"


@pytest.mark.asyncio
class TestFallbackChainResilience:
    def _service(
        self,
        backends: Dict[Any, _FakeBackend],
        attempts: List[str],
        fallback_calls: List[str],
    ) -> AngelaLLMService:
        svc = _bare_service()
        svc.backends = backends
        svc.active_backend = None
        svc.active_backend_type = None

        def _prompt(user_message: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
            return [{"role": "user", "content": user_message}]

        async def _submit(backend: Any, *, label: str, **kwargs: Any) -> LLMResponse:
            attempts.append(label)
            return await backend.generate(kwargs["prompt"])

        async def _fallback(user_message: str, context: Dict[str, Any]) -> LLMResponse:
            fallback_calls.append(user_message)
            return LLMResponse(text="fallback-answer", backend="local-fallback")

        svc._construct_angela_prompt = _prompt
        svc._submit_backend_call = _submit
        svc._fallback_response = _fallback
        return svc

    @pytest.mark.parametrize(
        ("failed", "configured_chain"),
        [
            # configured chain names only disabled backends (the original bug)
            (LLMBackend.UNIFIED, ["ollama-llama3", "anthropic-claude", "google-gemini"]),
            # chain names the already-failed backend only
            (LLMBackend.LLAMA_CPP, ["llamacpp-local"]),
            # empty chain
            (LLMBackend.UNIFIED, []),
        ],
    )
    async def test_degrades_to_a_healthy_model_not_a_refusal(
        self, failed: Any, configured_chain: List[str]
    ) -> None:
        healthy_type = (
            LLMBackend.LLAMA_CPP if failed is not LLMBackend.LLAMA_CPP else LLMBackend.UNIFIED
        )
        attempts: List[str] = []
        fallback_calls: List[str] = []
        svc = self._service(
            {failed: _FakeBackend(error="boom"), healthy_type: _FakeBackend("from-other")},
            attempts,
            fallback_calls,
        )
        ctx = {"_used_backend_type": failed}

        res = await svc._try_fallback_chain("hello", ctx, configured_chain)

        assert res.text == "from-other"
        assert res.error == ""
        assert fallback_calls == []
        # the backend that just failed is never retried in this pass
        assert not any(f"fallback:{failed.name}" == label for label in attempts)
        # ... and the winning backend becomes BOTH active handles
        assert svc.active_backend_type is healthy_type
        assert svc.active_backend is svc.backends[healthy_type]

    async def test_falls_through_when_response_is_empty(self) -> None:
        attempts: List[str] = []
        fallback_calls: List[str] = []
        svc = self._service(
            {
                LLMBackend.UNIFIED: _FakeBackend(text=""),
                LLMBackend.LLAMA_CPP: _FakeBackend("second-choice"),
            },
            attempts,
            fallback_calls,
        )
        res = await svc._try_fallback_chain(
            "hi", {"_used_backend_type": LLMBackend.UNIFIED}, ["unified-1g"]
        )
        assert res.text == "second-choice"

    async def test_refusal_only_when_nothing_left_to_try(self) -> None:
        attempts: List[str] = []
        fallback_calls: List[str] = []
        svc = self._service(
            {LLMBackend.UNIFIED: _FakeBackend(error="boom")}, attempts, fallback_calls
        )
        res = await svc._try_fallback_chain("hi", {"_used_backend_type": LLMBackend.UNIFIED}, [])

        assert fallback_calls == ["hi"]
        assert res.backend == "local-fallback"


class TestBackendCategoryAndHealth:
    @pytest.mark.parametrize(
        ("btype", "category"),
        [
            (LLMBackend.LLAMA_CPP, "local"),
            (LLMBackend.LLAMA_CPP_QWEN, "local"),
            (LLMBackend.OLLAMA, "local"),
            (LLMBackend.UNIFIED, "local"),
            (LLMBackend.GARDEN, "local"),
            (LLMBackend.ED3N, "local"),
            (LLMBackend.GOOGLE, "cloud"),
            (LLMBackend.OPENAI, "cloud"),
            (LLMBackend.ANTHROPIC, "cloud"),
        ],
    )
    def test_backend_category(self, btype: Any, category: str) -> None:
        assert AngelaLLMService.backend_category(btype) == category

    def test_health_cache_roundtrip(self) -> None:
        svc = _bare_service()
        svc._health_cache = {}
        assert svc.backend_health(LLMBackend.GOOGLE) == "unknown"
        svc.record_backend_health(LLMBackend.GOOGLE, True)
        assert svc.backend_health(LLMBackend.GOOGLE) == "healthy"
        svc.record_backend_health(LLMBackend.GOOGLE, False)
        assert svc.backend_health(LLMBackend.GOOGLE) == "unhealthy"


@pytest.mark.asyncio
class TestLLMStatusEndpoint:
    async def test_status_reports_type_health_and_pruned_backends(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from api.routes import llm_routes

        svc = _bare_service()
        svc._health_cache = {}
        svc.backends = {
            LLMBackend.LLAMA_CPP: _FakeBackend(),
            LLMBackend.GOOGLE: _FakeBackend(),
        }
        svc._pruned_backends = {LLMBackend.OPENAI: _FakeBackend(error="bad key")}
        svc.active_backend_type = LLMBackend.LLAMA_CPP
        svc.is_available = True
        svc.llm_mode = "local+llm"
        svc.stats = {"total_requests": 0}

        async def _fake_get() -> Any:
            return svc

        monkeypatch.setattr(llm_routes, "_get_llm", _fake_get)
        svc.record_backend_health(LLMBackend.LLAMA_CPP, True)
        svc.record_backend_health(LLMBackend.GOOGLE, True)
        svc.record_backend_health(LLMBackend.OPENAI, False)

        out = await llm_routes.llm_status()

        by_name = {b["name"]: b for b in out["backends"]}
        assert out["active"] == "LLAMA_CPP"
        assert out["mode"] == "local+llm"

        assert by_name["LLAMA_CPP"]["type"] == "local"
        assert by_name["LLAMA_CPP"]["health"] == "healthy"
        assert by_name["LLAMA_CPP"]["active"] is True
        assert by_name["LLAMA_CPP"]["available"] is True

        assert by_name["GOOGLE"]["type"] == "cloud"
        assert by_name["GOOGLE"]["health"] == "healthy"

        # configured-but-pruned backends must be visible, not silently dropped
        assert by_name["OPENAI"]["available"] is False
        assert by_name["OPENAI"]["health"] == "unhealthy"
        assert by_name["OPENAI"]["type"] == "cloud"
        assert by_name["OPENAI"]["active"] is False

    async def test_status_survives_a_service_without_the_new_helpers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Older/shim services lacking backend_category/backend_health still work."""

        class Legacy:
            backends = {LLMBackend.LLAMA_CPP: _FakeBackend()}
            _pruned_backends: Dict[Any, Any] = {}
            active_backend_type = None
            is_available = False
            llm_mode = "standard"
            stats: Dict[str, Any] = {}

        from api.routes import llm_routes

        async def _fake_get() -> Any:
            return Legacy()

        monkeypatch.setattr(llm_routes, "_get_llm", _fake_get)
        out = await llm_routes.llm_status()
        assert out["backends"][0]["type"] == "local"
        assert out["backends"][0]["health"] == "unknown"
