# ANGELA-MATRIX: [L3] [β] [B] [L2]

"""P1 closed loop: rule hit → chat_routes feedback → RuleStore.record_outcome.

The store previously admitted rules but never received serving outcomes, so
confidence could never adapt (the two-strikes demotion path was dead code).
These tests walk the full loop with real classes: router hit writes the
per-turn ``_solution_rule_hit`` marker, ``_record_post_response_feedback``
consumes it exactly once and records success/failure.
"""

from __future__ import annotations

import time

import pytest
from ai.rules.solution_rules import RuleStore
from services.llm.router import AngelaLLMService

_QUERY = "小明有3個蘋果，給了弟弟1個，還剩幾個？"
_ANSWER = "3-1=2，所以還剩2個"


def _bare_service() -> AngelaLLMService:
    """AngelaLLMService without running the (heavy) __init__."""
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


class TestSolutionRuleFeedbackLoop:
    @pytest.mark.asyncio
    async def test_hit_then_verbatim_serve_records_success(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        from api.routes.chat_routes import _record_post_response_feedback

        store = _patch_store(monkeypatch, tmp_path)
        rule = store.remember(_QUERY, _ANSWER)
        assert rule is not None

        service = _bare_service()
        context: dict = {}
        resp = await service._solution_rules_response(_QUERY, context, time.time())
        assert resp is not None
        assert resp.backend == "solution-rule"
        assert context["_solution_rule_hit"]["rule_id"] == rule.id

        _record_post_response_feedback(context, resp.text, _QUERY, was_truncated=False)
        assert "_solution_rule_hit" not in context  # consume-once
        stored = store.recall(_QUERY)
        assert stored is not None
        assert stored.feedback_count == 1
        assert stored.successes == 1
        assert stored.confidence > 0.66  # 3/4 after one success (0.666→0.75)

    @pytest.mark.asyncio
    async def test_truncated_serve_records_failure(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        from api.routes.chat_routes import _record_post_response_feedback

        store = _patch_store(monkeypatch, tmp_path)
        rule = store.remember(_QUERY, _ANSWER)
        assert rule is not None

        service = _bare_service()
        context: dict = {}
        resp = await service._solution_rules_response(_QUERY, context, time.time())
        assert resp is not None

        _record_post_response_feedback(context, resp.text, _QUERY, was_truncated=True)
        stored = store.recall(_QUERY)
        assert stored is not None
        assert stored.feedback_count == 1
        assert stored.successes == 0
        assert stored.confidence < 0.67  # demoted: (2+0)/(3+1) = 0.5

    @pytest.mark.asyncio
    async def test_marker_is_not_double_counted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        from api.routes.chat_routes import _record_post_response_feedback

        store = _patch_store(monkeypatch, tmp_path)
        rule = store.remember(_QUERY, _ANSWER)
        assert rule is not None

        service = _bare_service()
        context: dict = {}
        resp = await service._solution_rules_response(_QUERY, context, time.time())
        assert resp is not None

        _record_post_response_feedback(context, resp.text, _QUERY, was_truncated=False)
        # second call in the same turn: marker already consumed → no more records
        _record_post_response_feedback(context, resp.text, _QUERY, was_truncated=False)
        stored = store.recall(_QUERY)
        assert stored is not None
        assert stored.feedback_count == 1
        assert stored.successes == 1

    @pytest.mark.asyncio
    async def test_miss_leaves_no_marker_and_no_record(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        from api.routes.chat_routes import _record_post_response_feedback

        store = _patch_store(monkeypatch, tmp_path)
        _patched = store  # admitted rule is unrelated to the queried text
        assert _patched.remember(_QUERY, _ANSWER) is not None

        service = _bare_service()
        context: dict = {}
        resp = await service._solution_rules_response("完全不同的問題甲乙丙", context, time.time())
        assert resp is None
        assert "_solution_rule_hit" not in context

        _record_post_response_feedback(context, "任何回覆", "完全不同的問題甲乙丙", False)
        stored = store.recall(_QUERY)
        assert stored is not None
        assert stored.feedback_count == 0
        assert stored.successes == 0
