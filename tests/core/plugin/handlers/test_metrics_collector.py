"""Tests for MetricsCollectorHandler — hook invocation counting."""
import pytest
from core.plugin.handlers.metrics_collector import MetricsCollectorHandler


class TestMetricsCollectorHandler:
    def test_init_metrics_empty(self):
        mch = MetricsCollectorHandler()
        assert mch.get_metrics() == {"counts": {}}

    @pytest.mark.asyncio
    async def test_handler_for_records_invocation(self):
        mch = MetricsCollectorHandler()
        handler = mch.handler_for("on_start")
        result = await handler()
        assert result is None
        metrics = mch.get_metrics()
        assert metrics["counts"]["on_start"] == 1

    @pytest.mark.asyncio
    async def test_multiple_invocations_accumulate(self):
        mch = MetricsCollectorHandler()
        handler = mch.handler_for("on_message")
        for _ in range(5):
            await handler()
        metrics = mch.get_metrics()
        assert metrics["counts"]["on_message"] == 5

    @pytest.mark.asyncio
    async def test_multiple_hooks_independent(self):
        mch = MetricsCollectorHandler()
        h1 = mch.handler_for("hook_a")
        h2 = mch.handler_for("hook_b")
        await h1()
        await h1()
        await h2()
        metrics = mch.get_metrics()
        assert metrics["counts"]["hook_a"] == 2
        assert metrics["counts"]["hook_b"] == 1

    @pytest.mark.asyncio
    async def test_handler_passes_data_through(self):
        mch = MetricsCollectorHandler()
        handler = mch.handler_for("passthrough")
        result = await handler({"msg": "hello"})
        assert result == {"msg": "hello"}

    def test_get_metrics_returns_copy(self):
        mch = MetricsCollectorHandler()
        metrics_ref = mch.get_metrics()
        metrics_ref["counts"]["injected"] = 99
        real = mch.get_metrics()
        assert "injected" not in real["counts"]
