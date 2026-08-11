# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""響應模式選取器測試（§5.6 步驟 B6 — 1:1 / layered / stream / layered_stream）。

驗收（§5.6.3）：同一請求以四種模式各跑一次，最終組出的回應文本一致。
"""

import asyncio

import pytest
from core.backbone.contracts import EnvelopeKind
from core.backbone.response import RESPONSE_MODES, ResponseModeSelector, ResponseResult


class _FakeRouter:
    """假 LLM router：同步/非同步皆可的 generate_response。"""

    def __init__(self, text="default answer"):
        self.text = text
        self.calls = []

    async def generate_response(self, user_message, context=None):
        self.calls.append(user_message)
        return type("R", (), {"text": self.text})()


class _FakePipeline:
    """假 StreamingPipeline：把固定文本 emit 成 tokens 到 stream。"""

    def __init__(self, text="layered answer"):
        self.text = text
        self.stream_calls = []

    async def stream(self, query, stream, timeout=5.0):
        from ai.streaming.token_stream import StreamToken, TokenType

        self.stream_calls.append(query)
        for part in self.text.split(" "):
            if part:
                await stream.put(StreamToken(content=part + " ", type=TokenType.SYNTHESIZED))
        await stream.put(StreamToken.create_control("DONE"))


class _FakePairs:
    def __init__(self):
        self.submitted = []
        self.resolved = []
        self.failed = []
        self._n = 0

    def submit(self, envelope, timeout=None, kind=None):
        self._n += 1
        pid = f"p{self._n}"
        self.submitted.append((pid, kind))
        return pid

    def resolve(self, pid, output):
        self.resolved.append(pid)

    def fail(self, pid, reason=None):
        self.failed.append(pid)


@pytest.fixture
def router():
    return _FakeRouter("fixed answer")


@pytest.fixture
def pipeline():
    return _FakePipeline("layered answer")


class TestResponseModeSelector:
    def test_mode_1to1(self, router):
        selector = ResponseModeSelector(router=router)

        async def run():
            return await selector.respond("hi", {}, mode="1:1")

        result = asyncio.run(run())
        assert isinstance(result, ResponseResult)
        assert result.text == "fixed answer"
        assert result.mode == "1:1"
        assert result.route == "llm"

    def test_mode_layered(self, router, pipeline):
        selector = ResponseModeSelector(router=router, pipeline=pipeline)

        async def run():
            return await selector.respond("hi", {}, mode="layered")

        result = asyncio.run(run())
        assert result.mode == "layered"
        assert result.route == "pipeline"
        assert result.text == "layered answer"
        assert len(result.layers) > 0
        assert "".join(result.layers).strip() == "layered answer"

    def test_mode_stream_with_pipeline(self, router, pipeline):
        """pipeline 存在時 stream 走層式⊂流式（同一最終文本）。"""
        selector = ResponseModeSelector(router=router, pipeline=pipeline)

        async def run():
            return await selector.respond("hi", {}, mode="stream")

        result = asyncio.run(run())
        assert result.mode == "layered_stream"
        assert result.text == "layered answer"

    def test_mode_stream_without_pipeline_splits_router(self, router):
        """無 pipeline 時 stream fallback 到 router 的空白切分。"""
        selector = ResponseModeSelector(router=router)

        async def run():
            return await selector.respond("hi", {}, mode="stream")

        result = asyncio.run(run())
        assert result.mode == "stream"
        assert result.route == "llm"
        assert result.text == "fixed answer"
        assert result.tokens == ["fixed", "answer"]

    def test_mode_layered_stream(self, router, pipeline):
        selector = ResponseModeSelector(router=router, pipeline=pipeline)

        async def run():
            return await selector.respond("hi", {}, mode="layered_stream")

        result = asyncio.run(run())
        assert result.mode == "layered_stream"
        assert result.text == "layered answer"
        assert len(result.tokens) > 0

    def test_unknown_mode_falls_back_to_1to1(self, router):
        selector = ResponseModeSelector(router=router)

        async def run():
            return await selector.respond("hi", {}, mode="weird")

        result = asyncio.run(run())
        assert result.mode == "1:1"
        assert result.text == "fixed answer"

    def test_pipeline_failure_falls_back(self, router):
        class _BrokenPipeline:
            async def stream(self, query, stream, timeout=5.0):
                raise RuntimeError("boom")

        selector = ResponseModeSelector(router=router, pipeline=_BrokenPipeline())

        async def run():
            return await selector.respond("hi", {}, mode="layered")

        result = asyncio.run(run())
        assert result.mode == "layered"
        assert result.route == "fallback"
        assert result.text == "fixed answer"

    def test_layered_tracks_iopair(self, router, pipeline):
        pairs = _FakePairs()
        selector = ResponseModeSelector(router=router, pipeline=pipeline, pair_scheduler=pairs)

        async def run():
            return await selector.respond("hi", {}, mode="layered")

        result = asyncio.run(run())
        assert result.text == "layered answer"
        assert pairs.submitted[0][1] == EnvelopeKind.RESPONSE
        assert pairs.resolved  # 成對輸出側已 resolve

    def test_respond_consistent_across_modes(self, router, pipeline):
        """§5.6.3 驗收：同一請求四種模式文本一致。"""
        selector = ResponseModeSelector(router=router, pipeline=pipeline)
        router.text = "the quick brown fox"
        pipeline.text = "the quick brown fox"

        async def run():
            m1 = await selector.respond("q", {}, mode="1:1")
            m2 = await selector.respond("q", {}, mode="layered")
            m3 = await selector.respond("q", {}, mode="stream")
            m4 = await selector.respond("q", {}, mode="layered_stream")
            return m1, m2, m3, m4

        r1, r2, r3, r4 = asyncio.run(run())
        assert r1.text == r2.text == r3.text == r4.text == "the quick brown fox"

    def test_engine_free_pipeline_falls_back_to_router(self, router):
        """無引擎 pipeline（只發 DONE）不再產空輸出，改走 router fallback。

        §5.6.3 一致性要求：layered 模式在沒有 garden/ed3n 推論時，
        仍應回傳與 1:1 相同的完整文本（修復空輸出 bug）。
        """
        from ai.streaming.token_stream import StreamToken, TokenType

        class _EmptyPipeline:
            async def stream(self, query, stream, timeout=5.0):
                await stream.put(StreamToken.create_control("DONE"))

        selector = ResponseModeSelector(router=router, pipeline=_EmptyPipeline())

        async def run():
            return await selector.respond("hi", {}, mode="layered")

        result = asyncio.run(run())
        assert result.route == "fallback"
        assert result.text == "fixed answer"

    def test_engine_free_pipeline_resolves_iopair(self, router):
        """空輸出 fallback 路徑也要 resolve IOPair（不成對遺留）。"""
        from ai.streaming.token_stream import StreamToken, TokenType

        class _EmptyPipeline:
            async def stream(self, query, stream, timeout=5.0):
                await stream.put(StreamToken.create_control("DONE"))

        pairs = _FakePairs()
        selector = ResponseModeSelector(
            router=router, pipeline=_EmptyPipeline(), pair_scheduler=pairs
        )

        async def run():
            return await selector.respond("hi", {}, mode="layered")

        asyncio.run(run())
        assert pairs.submitted  # 輸入側已 submit
        assert pairs.resolved  # fallback 也 resolve 輸出側

    def test_current_mode_tracks_last_used_mode(self, router):
        """structure.dump() 死參考回歸守衛：current_mode 記錄真實模式。

        先前 `structure.py._response_mode()` 讀 `self.bb.response.current_mode`
        不存在常數 → 永遠 fallback "default"。此測試確保 current_mode 更新真實值。
        """
        selector = ResponseModeSelector(router=router)
        assert selector.current_mode == "default"

        async def run():
            await selector.respond("hi", {}, mode="layered")

        asyncio.run(run())
        assert selector.current_mode == "layered"

        async def run2():
            await selector.respond("hi", {}, mode="1:1")

        asyncio.run(run2())
        assert selector.current_mode == "1:1"


class TestBackboneRespond:
    def test_backbone_respond_delegates(self, router, pipeline):
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        bb.response.router = router
        bb.response.pipeline = pipeline

        async def run():
            return await bb.respond("hi", {}, mode="layered")

        result = asyncio.run(run())
        assert result.mode == "layered"
        assert result.text == "layered answer"
        reset_backbone()
