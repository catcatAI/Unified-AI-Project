# tests/services/test_routing_engine.py
"""路由清單引擎單元測試：清單執行、跳線預算、安全網、遙測與 AI 重排鉤子。"""

import pytest
from core.system.state_store import state_store
from services.llm.routing import (
    DEFAULT_PLAN,
    MAX_HOPS_PER_REQUEST,
    RouteManifest,
    RoutingEngine,
    StepSpec,
)


def _resp(text: str, **meta) -> object:
    from core.interfaces.protocols import LLMResponse

    return LLMResponse(text=text, confidence=0.9, metadata=meta or None)


def _make_engine(hops: int = 12) -> RoutingEngine:
    return RoutingEngine(max_hops=hops)


class TestManifestDefaults:
    def test_default_plan_ends_with_terminal(self):
        assert DEFAULT_PLAN[-1].kind == "terminal"

    def test_reorder_keeps_terminal_last(self):
        m = RouteManifest()
        names = [s.name for s in m.plan]
        m.reorder(list(reversed(names)))
        assert m.plan[-1].kind == "terminal"

    def test_set_enabled_roundtrip(self):
        m = RouteManifest()
        assert m.set_enabled("neural_bridge", False) is True
        assert all(s.name != "neural_bridge" or not s.enabled for s in m.plan)
        assert m.set_enabled("neural_bridge", True) is True

    def test_set_enabled_unknown_step(self):
        m = RouteManifest()
        assert m.set_enabled("no_such_step", False) is False


class TestEngineRun:
    @pytest.mark.asyncio
    async def test_first_hit_returns_and_stops(self):
        eng = _make_engine()

        async def hit(user_message, context):
            return _resp("ok")

        async def never(user_message, context):
            raise AssertionError("should not be called")

        eng.register("a", hit)
        eng.register("b", never)
        plan = [
            StepSpec(name="a", connector="a", tier=0),
            StepSpec(name="b", connector="b", tier=1),
        ]
        resp = await eng.run(plan, "hi", {})
        assert resp.text == "ok"
        assert resp.metadata["routing_trace"] == ["a"]

    @pytest.mark.asyncio
    async def test_miss_falls_through(self):
        eng = _make_engine()

        async def miss(user_message, context):
            return None

        eng.register("a", miss)
        eng.register("b", miss)
        plan = [
            StepSpec(name="a", connector="a", tier=0),
            StepSpec(name="b", connector="b", tier=1),
        ]
        resp = await eng.run(plan, "hi", {})
        # 無 terminal：引擎的 exhausted 防線接住
        assert resp.metadata.get("routing") == "exhausted"

    @pytest.mark.asyncio
    async def test_unregistered_connector_is_error_not_crash(self):
        eng = _make_engine()
        plan = [StepSpec(name="x", connector="missing", tier=0)]
        resp = await eng.run(plan, "hi", {})
        assert resp.metadata.get("routing") == "exhausted"

    @pytest.mark.asyncio
    async def test_budget_skips_non_terminal_but_terminal_still_runs(self):
        eng = _make_engine(hops=2)

        async def miss(user_message, context):
            return None

        async def hit(user_message, context):
            return _resp("terminal-hit")

        eng.register("a", miss)
        eng.register("b", miss)
        eng.register("c", miss)
        eng.register("net", hit)
        plan = [
            StepSpec(name="a", connector="a", tier=0),
            StepSpec(name="b", connector="b", tier=1),
            StepSpec(name="c", connector="c", tier=2),
            StepSpec(name="net", connector="net", tier=9, kind="terminal"),
        ]
        resp = await eng.run(plan, "hi", {})
        assert resp.text == "terminal-hit"

    @pytest.mark.asyncio
    async def test_connector_error_continues(self):
        eng = _make_engine()

        async def boom(user_message, context):
            raise RuntimeError("boom")

        async def hit(user_message, context):
            return _resp("after-error")

        eng.register("a", boom)
        eng.register("b", hit)
        plan = [
            StepSpec(name="a", connector="a", tier=0),
            StepSpec(name="b", connector="b", tier=1),
        ]
        resp = await eng.run(plan, "hi", {})
        assert resp.text == "after-error"

    @pytest.mark.asyncio
    async def test_telemetry_recorded(self):
        state_store.update_state("routing", {"steps": {}}, notify=False)
        eng = _make_engine()

        async def miss(user_message, context):
            return None

        async def hit(user_message, context):
            return _resp("ok")

        eng.register("a", miss)
        eng.register("b", hit)
        plan = [
            StepSpec(name="a", connector="a", tier=0),
            StepSpec(name="b", connector="b", tier=1),
        ]
        await eng.run(plan, "hi", {})
        routing_state = state_store.get_state("routing")
        assert routing_state["steps"]["a"]["miss"] == 1
        assert routing_state["steps"]["b"]["hit"] == 1

    @pytest.mark.asyncio
    async def test_plan_for_ignores_steps_without_history(self):
        state_store.update_state("routing", {"steps": {}}, notify=False)
        eng = _make_engine()
        assert eng.plan_for("hi", {}) is None


class TestManifestPlanOrder:
    @pytest.mark.asyncio
    async def test_engine_respects_manifest_order(self):
        eng = _make_engine()

        calls: list[str] = []

        async def first(user_message, context):
            calls.append("first")
            return None

        async def second(user_message, context):
            calls.append("second")
            return _resp("done")

        eng.register("a", first)
        eng.register("b", second)
        m = RouteManifest(
            [
                StepSpec(name="a", connector="a", tier=0),
                StepSpec(name="b", connector="b", tier=1),
            ]
        )
        resp = await eng.run(m.plan, "hi", {})
        assert calls == ["first", "second"]
        assert resp.text == "done"

    def test_max_hops_env_floor(self):
        # MAX_HOPS_PER_REQUEST 必須涵蓋預設清單長度（否則正常路徑被掐斷）
        assert MAX_HOPS_PER_REQUEST >= len(DEFAULT_PLAN)
