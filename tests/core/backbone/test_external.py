# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""外部閘道測試（§5.5.1 步驟 B3/B4 — call_external + 成對排程套用）。"""

import pytest
from core.backbone.external import ExternalBackend, ExternalGateway


class _FakeProvider:
    """同步/非同步方法混用的假外部服務。"""

    def __init__(self):
        self.calls = []

    async def generate(self, prompt: str, **kwargs):
        self.calls.append(("generate", prompt, kwargs))
        return f"generated:{prompt}"

    async def fail_always(self):
        raise RuntimeError("provider failure")

    async def slow(self, delay: float = 0.05):
        import asyncio

        await asyncio.sleep(delay)
        return "slow-done"

    def sync_method(self, x: int = 1):
        return x * 2


@pytest.fixture
def bb():
    from core.backbone import get_backbone, reset_backbone

    reset_backbone()
    yield get_backbone()
    reset_backbone()


class TestExternalBackend:
    def test_async_method(self):
        backend = ExternalBackend("fake", _FakeProvider())

        async def run():
            return await backend.call("generate", prompt="hi")

        import asyncio

        assert asyncio.run(run()) == "generated:hi"

    def test_sync_method(self):
        backend = ExternalBackend("fake", _FakeProvider())

        async def run():
            return await backend.call("sync_method", x=5)

        import asyncio

        assert asyncio.run(run()) == 10

    def test_missing_method_raises(self):
        backend = ExternalBackend("fake", _FakeProvider())

        async def run():
            return await backend.call("nonexistent")

        import asyncio

        with pytest.raises(AttributeError):
            asyncio.run(run())


class TestExternalGateway:
    @pytest.mark.asyncio
    async def test_register_and_call(self, bb):
        provider = _FakeProvider()
        bb.register_external("llm.openai", provider)
        result = await bb.call_external("llm.openai", "generate", prompt="hello")
        assert result == "generated:hello"
        assert provider.calls == [("generate", "hello", {})]

    @pytest.mark.asyncio
    async def test_call_creates_paired_io(self, bb):
        provider = _FakeProvider()
        bb.register_external("llm.openai", provider)
        await bb.call_external("llm.openai", "generate", prompt="hi")
        # call_external 產生成對：submit → resolve，無殘留 pending
        assert bb.io.pending() == []
        assert len(bb.io.by_kind("external")) == 1

    @pytest.mark.asyncio
    async def test_unregistered_raises_keyerror(self, bb):
        with pytest.raises(KeyError):
            await bb.call_external("nope", "generate")

    @pytest.mark.asyncio
    async def test_failure_marks_pair_error(self, bb):
        provider = _FakeProvider()
        bb.register_external("llm.openai", provider)
        with pytest.raises(RuntimeError):
            await bb.call_external("llm.openai", "fail_always")
        # 失敗對已標記 ERROR，不靜默
        errored = [p for p in bb.io.by_kind("external") if p["status"] == "ERROR"]
        assert len(errored) == 1

    @pytest.mark.asyncio
    async def test_timeout_marks_pair_error(self, bb):
        provider = _FakeProvider()
        bb.register_external("llm.openai", provider)
        with pytest.raises(Exception):
            await bb.call_external("llm.openai", "slow", timeout=0.01, retries=0)
        pairs = bb.io.by_kind("external")
        assert pairs and pairs[0]["status"] in ("ERROR", "ORPHAN")

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        gateway = ExternalGateway(rate_limit=2)

        class _P:
            async def fast(self):
                return "ok"

        gateway.register("fast", _P())
        await gateway.call_external("fast", "fast")
        await gateway.call_external("fast", "fast")
        with pytest.raises(RuntimeError):
            await gateway.call_external("fast", "fast")

    @pytest.mark.asyncio
    async def test_retry_policy(self):
        from shared.network_resilience import RetryPolicy

        gateway = ExternalGateway(retry_policy=RetryPolicy(max_retries=3, base_delay=0.0))

        class _Flaky:
            def __init__(self):
                self.attempts = 0

            async def flaky(self):
                self.attempts += 1
                if self.attempts < 2:
                    raise RuntimeError("transient")
                return "recovered"

        flaky = _Flaky()
        gateway.register("flaky", flaky)
        result = await gateway.call_external("flaky", "flaky", retries=3)
        assert result == "recovered"
        assert flaky.attempts == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker(self):
        from shared.network_resilience import CircuitBreaker

        gateway = ExternalGateway(circuit_breaker=CircuitBreaker(failure_threshold=2))

        class _Bad:
            async def boom(self):
                raise RuntimeError("always fails")

        gateway.register("bad", _Bad())
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await gateway.call_external("bad", "boom", retries=0)
        # 熔斷開啟：CircuitBreaker 拋 Exception（非 RuntimeError）
        with pytest.raises(Exception):
            await gateway.call_external("bad", "boom", retries=0)

    def test_external_names(self, bb):
        bb.register_external("weather", _FakeProvider())
        bb.register_external("drive", _FakeProvider())
        assert set(bb.external_names()) == {"weather", "drive"}

    def test_unregister_external(self, bb):
        bb.register_external("weather", _FakeProvider())
        assert bb.unregister_external("weather") is True
        assert bb.unregister_external("weather") is False


class TestLLMProviderWrapper:
    """步驟 B3：包裝真實 LLM provider 介面（BaseLLMBackend.generate）。"""

    def test_wraps_base_llm_backend_shape(self, bb):
        """LLM backend 具 generate/check_health 方法即可註冊。"""

        class _FakeLLM:
            async def generate(self, prompt: str, **kwargs):
                return prompt

            async def check_health(self):
                return True

        bb.register_external("llm.ed3n", _FakeLLM())
        backend = bb.external.get_backend("llm.ed3n")
        assert backend.has_method("generate")
        assert backend.has_method("check_health")
