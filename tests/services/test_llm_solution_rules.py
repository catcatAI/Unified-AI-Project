# ANGELA-MATRIX: [L3] [β] [B] [L2]

"""Router-level tests: solution-rule distillation hook + recall connector."""

from __future__ import annotations

import time

import pytest
from ai.rules.solution_rules import RuleStore
from core.interfaces.protocols import LLMResponse
from services.llm.router import AngelaLLMService
from services.llm.routing.manifest import DEFAULT_PLAN


def _bare_service() -> AngelaLLMService:
    service = object.__new__(AngelaLLMService)
    service.stats = {
        "total_requests": 1,
        "total_response_time": 0.0,
        "average_response_time": 0.0,
        "memory_hits": 0,
        "memory_hit_rate": 0.0,
    }
    return service


def _patch_store(monkeypatch: pytest.MonkeyPatch, tmp_path) -> RuleStore:
    store = RuleStore(path=str(tmp_path / "rules.json"))
    monkeypatch.setattr("ai.rules.get_rule_store", lambda: store)
    return store


def _math_response(**overrides) -> LLMResponse:
    payload = {
        "text": "3-1=2，所以還剩2個",
        "backend": "google",
        "model": "gemini-test",
        "confidence": 0.9,
    }
    payload.update(overrides)
    return LLMResponse(**payload)


class TestDistillHook:
    def test_verified_math_answer_admitted(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        service._maybe_distill_solution_rule(
            "小明有3個蘋果，給了弟弟1個，還剩幾個？", _math_response()
        )
        assert store.stats()["total"] == 1

    def test_fallback_backend_rejected(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = _math_response(backend="local-fallback")
        service._maybe_distill_solution_rule("小明有3個蘋果，給了弟弟1個，還剩幾個？", response)
        assert store.stats()["total"] == 0

    def test_refusal_text_rejected(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = _math_response(text="抱歉，3+5=8，答案是8")
        service._maybe_distill_solution_rule("小明有3個蘋果，給了弟弟1個，還剩幾個？", response)
        assert store.stats()["total"] == 0

    def test_low_confidence_rejected(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = _math_response(confidence=0.4)
        service._maybe_distill_solution_rule("小明有3個蘋果，給了弟弟1個，還剩幾個？", response)
        assert store.stats()["total"] == 0

    def test_clock_query_rejected(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = _math_response(text="3+5=8，答案是8")
        service._maybe_distill_solution_rule("今天幾號", response)
        assert store.stats()["total"] == 0

    def test_dynamic_weather_query_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        service._maybe_distill_solution_rule("明天天氣如何", _math_response())
        assert store.stats()["total"] == 0

    def test_error_response_rejected(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = _math_response(error="backend exploded")
        service._maybe_distill_solution_rule("小明有3個蘋果，給了弟弟1個，還剩幾個？", response)
        assert store.stats()["total"] == 0

    def test_unverifiable_answer_rejected(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = _math_response(text="這需要看整體情境來決定")
        service._maybe_distill_solution_rule("小明有3個蘋果，給了弟弟1個，還剩幾個？", response)
        assert store.stats()["total"] == 0

    def test_store_io_failure_is_nonfatal(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        def _boom():
            raise OSError("disk full")

        monkeypatch.setattr("ai.rules.get_rule_store", _boom)
        service = _bare_service()
        service._maybe_distill_solution_rule(
            "小明有3個蘋果，給了弟弟1個，還剩幾個？", _math_response()
        )


class TestSolutionRulesResponse:
    @pytest.mark.asyncio
    async def test_hit_serves_verbatim_with_zero_tokens(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        store = _patch_store(monkeypatch, tmp_path)
        store.remember("小明有3個蘋果，給了弟弟1個，還剩幾個？", "3-1=2，所以還剩2個")
        service = _bare_service()
        response = await service._solution_rules_response(
            "小明有3個蘋果，給了弟弟1個，還剩幾個？", {}, time.time()
        )
        assert response is not None
        assert response.backend == "solution-rule"
        assert response.text == "3-1=2，所以還剩2個"
        assert response.tokens_used == 0
        assert response.metadata["solution_rule"] is True
        assert response.metadata["rule_id"]
        assert service.stats["memory_hits"] == 1

    @pytest.mark.asyncio
    async def test_miss_returns_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        _patch_store(monkeypatch, tmp_path)
        service = _bare_service()
        response = await service._solution_rules_response("完全沒見過的問題", {}, time.time())
        assert response is None

    @pytest.mark.asyncio
    async def test_store_failure_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def _boom():
            raise OSError("disk full")

        monkeypatch.setattr("ai.rules.get_rule_store", _boom)
        service = _bare_service()
        response = await service._solution_rules_response("小明有3個蘋果", {}, time.time())
        assert response is None


class TestManifestPlacement:
    def test_solution_rules_step_in_tier0_cache_layer(self) -> None:
        steps = {step.name: step for step in DEFAULT_PLAN}
        assert "solution_rules" in steps
        step = steps["solution_rules"]
        assert step.connector == "solution_rules"
        assert step.tier == 0
        assert step.priority == 3
        assert steps["clock"].tier == 0
        assert steps["clock"].priority == 2
        assert steps["template_match"].tier == 1

    def test_plan_order_keeps_rules_before_template_match(self) -> None:
        ordered = sorted((s for s in DEFAULT_PLAN if s.enabled), key=lambda s: s.sort_key())
        names = [step.name for step in ordered]
        assert names.index("clock") < names.index("solution_rules")
        assert names.index("solution_rules") < names.index("template_match")
