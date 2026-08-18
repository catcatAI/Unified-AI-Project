# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 中層「響應模式選取器」（§5.6 / 步驟 B6）
# 維度: γ 回應維度（回應生成/合成）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸響應合成概念
#
# =============================================================================

"""中層「響應模式選取器」（§5.6 / 步驟 B6）。

統一 `backbone.respond(mode=...)` 入口，請求層級選模式、不中途切換：

- ``mode="1:1"``            → `router.generate_response()`（現有主路徑）
- ``mode="layered"``        → `StreamingPipeline` 逐層 emit（一輸入 → N 層語意片段）
- ``mode="stream"``         → `TokenStream` 逐 token 拼接（同一最終文本分批送達）
- ``mode="layered_stream"`` → `StreamingPipeline` 層內 token 送出（層式⊂流式）

驗收（§5.6.3）：同一請求以四種模式各跑一次，最終組出的回應文本一致
（1:1 == layered 疊合 == stream 拼接 == layered_stream 疊合拼接）。

與 §5.0 成對排程整合：每層輸出都是一個 IOPair 的輸出側（kind=response），
可追蹤、可查、可重試。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.backbone.contracts import Envelope, EnvelopeKind

logger = logging.getLogger("angela_backbone_response")

RESPONSE_MODES = ("1:1", "layered", "stream", "layered_stream")


@dataclass
class ResponseResult:
    """統一響應結果信封（§5.6 收斂多模式輸出）。

    Attributes:
        mode: 使用的響應模式。
        text: 最終組出的完整回應文本。
        layers: (layered) 每層語意片段。
        tokens: (stream) 每個 token 的內容。
        route: 實際走的路徑（"llm" / "pipeline" / "fallback"）。
        metadata: 額外中繼資料。
    """

    mode: str
    text: str
    layers: List[str] = field(default_factory=list)
    tokens: List[str] = field(default_factory=list)
    route: str = "llm"
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseModeSelector:
    """響應模式選取器（§5.6）。

    Args:
        router: 具備 `generate_response(user_message, context)` 的服務
            （1:1 模式 / stream fallback）。
        pipeline: 具備 `stream(query, stream, timeout)` 的 StreamingPipeline
            （layered / layered_stream 模式）。
        pair_scheduler: `PairScheduler`（可選，每層輸出成對追蹤）。
    """

    def __init__(
        self, router: Any = None, pipeline: Any = None, pair_scheduler: Any = None
    ) -> None:
        self.router = router
        self.pipeline = pipeline
        self.pairs = pair_scheduler
        self.current_mode = "default"

    # ------------------------------------------------------------------
    # 統一入口
    # ------------------------------------------------------------------
    async def respond(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        mode: str = "1:1",
        **kwargs: Any,
    ) -> ResponseResult:
        """請求層級選模式、不中途切換（§5.6.3）。

        Args:
            user_message: 使用者輸入。
            context: 請求脈絡（可選）。
            mode: "1:1" | "layered" | "stream" | "layered_stream"。
            **kwargs: 傳遞給後端產生的額外參數。
        """
        mode = self._normalize_mode(mode)
        self.current_mode = mode
        if mode == "1:1":
            return await self._respond_1to1(user_message, context)
        if mode == "layered":
            return await self._respond_layered(user_message, context, stream_mode=False)
        if mode == "layered_stream":
            return await self._respond_layered(user_message, context, stream_mode=True)
        if mode == "stream":
            return await self._respond_stream(user_message, context)
        raise ValueError(f"Unknown response mode: {mode!r}")

    def _normalize_mode(self, mode: str) -> str:
        if mode in ("1:1", "one-to-one", "traditional"):
            return "1:1"
        if mode == "layered":
            return "layered"
        if mode == "stream":
            return "stream"
        if mode == "layered_stream":
            return "layered_stream"
        return "1:1"

    # ------------------------------------------------------------------
    # 1:1 — 傳統對話（§5.6.1）
    # ------------------------------------------------------------------
    async def _respond_1to1(
        self, user_message: str, context: Optional[Dict[str, Any]]
    ) -> ResponseResult:
        router = self._get_router()
        response = await router.generate_response(user_message, context or {})
        text = getattr(response, "text", str(response))
        return ResponseResult(
            mode="1:1",
            text=text,
            route="llm",
            metadata={"response_type": type(response).__name__},
        )

    # ------------------------------------------------------------------
    # layered / layered_stream — StreamingPipeline 逐層 emit（§5.6.1）
    # ------------------------------------------------------------------
    async def _respond_layered(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]],
        stream_mode: bool,
    ) -> ResponseResult:
        pipeline = self._get_pipeline()
        from ai.streaming.pipeline import StreamingPipeline  # noqa: F401 (type guard)
        from ai.streaming.token_stream import StreamToken, TokenStream, TokenType

        stream = TokenStream()
        mode = "layered_stream" if stream_mode else "layered"
        pair_id: Optional[str] = None
        envelope = Envelope(
            payload={"user_message": user_message, "context": context},
            kind=EnvelopeKind.CHAT,
            source="response_selector",
        )
        if self.pairs is not None:
            pair_id = self.pairs.submit(envelope, timeout=30.0, kind=EnvelopeKind.RESPONSE)

        try:
            await pipeline.stream(user_message, stream, timeout=30.0)
        except Exception as exc:
            logger.warning("%s pipeline failed: %s", mode, exc, exc_info=True)
            if pair_id is not None and self.pairs is not None:
                try:
                    self.pairs.fail(pair_id, reason=str(exc))
                except Exception:
                    pass
            return await self._fallback_result(mode, user_message, context)

        layers: List[str] = []
        tokens: List[str] = []
        while True:
            token = await stream.get(timeout=1.0)
            if token is None:
                break
            if token.type == TokenType.CONTROL:
                continue
            tokens.append(token.content)
            if stream_mode:
                layers.append(token.content)
            elif token.content:
                layers.append(token.content)

        text = "".join(tokens).strip()
        if not text and self.router is not None:
            logger.info(
                "%s pipeline produced empty output (no engine inference); "
                "falling back to router for consistent final text",
                mode,
            )
            result = await self._fallback_result(mode, user_message, context)
            if pair_id is not None and self.pairs is not None:
                output = Envelope(
                    payload={"text": result.text, "layers": [result.text]},
                    kind=EnvelopeKind.RESPONSE,
                    direction="up",
                    correlation_id=envelope.correlation_id,
                    source="response_selector",
                )
                try:
                    self.pairs.resolve(pair_id, output)
                except Exception:
                    pass
            return result
        if pair_id is not None and self.pairs is not None:
            output = Envelope(
                payload={"text": text, "layers": layers},
                kind=EnvelopeKind.RESPONSE,
                direction="up",
                correlation_id=envelope.correlation_id,
                source="response_selector",
            )
            try:
                self.pairs.resolve(pair_id, output)
            except Exception:
                pass
        return ResponseResult(
            mode=mode,
            text=text,
            layers=layers,
            tokens=tokens,
            route="pipeline",
        )

    # ------------------------------------------------------------------
    # stream — TokenStream 逐 token（§5.6.1）
    # ------------------------------------------------------------------
    async def _respond_stream(
        self, user_message: str, context: Optional[Dict[str, Any]]
    ) -> ResponseResult:
        # 層式⊂流式：若有明確注入 pipeline 則逐層 emit 到 stream 再拼接；
        # 否則 fallback 到 router 的空白切分（§5.6.1）。
        if self.pipeline is not None:
            return await self._respond_layered(user_message, context, stream_mode=True)

        router = self._get_router()
        response = await router.generate_response(user_message, context or {})
        text = getattr(response, "text", str(response))
        tokens = [t for t in text.split(" ") if t]
        return ResponseResult(
            mode="stream",
            text=text,
            tokens=tokens,
            route="llm",
            metadata={"split": "whitespace"},
        )

    # ------------------------------------------------------------------
    # 內部 helper
    # ------------------------------------------------------------------
    async def _fallback_result(
        self, mode: str, user_message: str, context: Optional[Dict[str, Any]]
    ) -> ResponseResult:
        try:
            router = self._get_router()
            response = await router.generate_response(user_message, context or {})
            text = getattr(response, "text", str(response))
            return ResponseResult(mode=mode, text=text, route="fallback")
        except Exception as exc:
            logger.warning("response fallback failed: %s", exc)
            return ResponseResult(mode=mode, text="", route="error", metadata={"error": str(exc)})

    def _get_router(self) -> Any:
        if self.router is None:
            from services.llm.router import get_llm_service

            self.router = get_llm_service()
        return self.router

    def _get_pipeline(self) -> Any:
        if self.pipeline is None:
            from ai.streaming.pipeline import StreamingPipeline

            self.pipeline = StreamingPipeline(fallback_fn=None)
        return self.pipeline
