# =============================================================================
# ANGELA-MATRIX: L1-L6[全层] αβγδεθζη [A] L2+
# =============================================================================
#
# 職責: send_up / send_down 信封路由 + backbone.io 成對入口（§5.1/§5.0）
# 維度: ζ 連通維度（跨層傳遞不丟失語意）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸信封路由概念
#
# =============================================================================

"""信封路由（§6 io.py）。

- `send_down(envelope)`：上層 → 下層（使用者請求進入，經中層到 LLM/外部）。
- `send_up(envelope)`：下層 → 上層（回應輸出返回）。

所有輸入輸出**必須成對**（§5.0）：send_down 會自動建立 IOPair（透過
`backbone.io.submit`），send_up 可選以 `resolve_pair_id` 直接配對既有對。
未配對的輸入不得靜默消失。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from core.backbone.contracts import Envelope

logger = logging.getLogger("angela_backbone_io")

# 登錄處理器型別：接收 Envelope，回傳 Envelope 或任意結果
DownHandler = Callable[[Envelope], Any]
UpHandler = Callable[[Envelope], Any]


class BackboneIO:
    """主幹線信封路由 + 成對入口。

    Args:
        pair_scheduler: `PairScheduler`（§5.0.2）。為 None 時可關閉成對追蹤。
        registries: `BackboneRegistries`（用於路由至已註冊模組）。
        state: `BackboneState`（可選，供 CNS 事件/狀態記錄）。
    """

    def __init__(
        self,
        pair_scheduler: Any = None,
        registries: Any = None,
        state: Any = None,
    ) -> None:
        self.pairs = pair_scheduler
        self.registries = registries
        self.state = state
        self._down_handlers: Dict[str, DownHandler] = {}
        self._up_handlers: Dict[str, UpHandler] = {}
        self._default_down: Optional[DownHandler] = None
        self._default_up: Optional[UpHandler] = None

    # ------------------------------------------------------------------
    # 處理器註冊
    # ------------------------------------------------------------------
    def register_down(self, kind: str, handler: DownHandler) -> None:
        """註冊下行（輸入）處理器。"""
        self._down_handlers[kind] = handler

    def register_up(self, kind: str, handler: UpHandler) -> None:
        """註冊上行（輸出）處理器。"""
        self._up_handlers[kind] = handler

    def set_default_down(self, handler: DownHandler) -> None:
        self._default_down = handler

    def set_default_up(self, handler: UpHandler) -> None:
        self._default_up = handler

    def down_handlers(self) -> Dict[str, DownHandler]:
        return dict(self._down_handlers)

    def up_handlers(self) -> Dict[str, UpHandler]:
        return dict(self._up_handlers)

    # ------------------------------------------------------------------
    # 路由（§5.1）
    # ------------------------------------------------------------------
    def send_down(self, envelope: Envelope, **kwargs: Any) -> Any:
        """下層→中層→上層（使用者請求進入）。

        自動建立 IOPair（若成對追蹤啟用），pair_id 存入 envelope.meta 供
        回應時配對。處理結果為 Envelope 時自動配對。
        """
        pair_id: Optional[str] = None
        if self.pairs is not None:
            pair_id = self.pairs.submit(envelope, kind=envelope.kind)
            envelope.meta["pair_id"] = pair_id

        handler = self._down_handlers.get(envelope.kind) or self._default_down
        if handler is None:
            if pair_id and self.pairs is not None:
                self.pairs.fail(pair_id, reason="no down handler")
            raise ValueError(f"No down handler for kind={envelope.kind}")

        try:
            result = handler(envelope, **kwargs)
        except Exception as exc:
            logger.warning("down handler failed for %s: %s", envelope.kind, exc)
            if pair_id and self.pairs is not None:
                self.pairs.fail(pair_id, reason=str(exc))
            raise

        if pair_id and self.pairs is not None:
            self._auto_pair(pair_id, result, envelope)

        return result

    def send_up(self, envelope: Envelope, **kwargs: Any) -> Any:
        """下層→中層→上層（回應輸出返回）。

        若 envelope.meta 帶 `pair_id`，自動配對該 IOPair。
        """
        pair_id = envelope.meta.get("pair_id") or kwargs.get("pair_id")
        if pair_id and self.pairs is not None:
            self._auto_pair(pair_id, envelope, envelope)

        handler = self._up_handlers.get(envelope.kind) or self._default_up
        if handler is None:
            return envelope
        return handler(envelope, **kwargs)

    def _auto_pair(self, pair_id: str, result: Any, source: Envelope) -> None:
        """若結果為 Envelope 則配對；否則以結果包成輸出 Envelope。"""
        try:
            if self.pairs is None:
                return
            existing = self.pairs.get_pair(pair_id)
            if existing is None or existing.is_terminal:
                return
            if isinstance(result, Envelope):
                self.pairs.resolve(pair_id, result)
            else:
                output = Envelope(
                    payload=result,
                    kind=source.kind,
                    direction="up",
                    correlation_id=source.correlation_id,
                    source=source.target or "io",
                )
                self.pairs.resolve(pair_id, output)
        except Exception:  # noqa: BLE001 - 配對失敗不中斷主流程
            logger.warning("auto-pair failed for %s", pair_id, exc_info=True)

    # ------------------------------------------------------------------
    # 成對排程委派（§5.0.2 公開介面）
    # ------------------------------------------------------------------
    def submit(self, input_envelope: Envelope, timeout: float = 8.0) -> str:
        if self.pairs is None:
            raise RuntimeError("pair scheduler disabled")
        return self.pairs.submit(input_envelope, timeout=timeout)

    def resolve(self, pair_id: str, output_envelope: Envelope) -> None:
        if self.pairs is None:
            raise RuntimeError("pair scheduler disabled")
        self.pairs.resolve(pair_id, output_envelope)

    def cancel(self, pair_id: str) -> None:
        if self.pairs is None:
            raise RuntimeError("pair scheduler disabled")
        self.pairs.cancel(pair_id)

    def retry(self, pair_id: str) -> None:
        if self.pairs is None:
            raise RuntimeError("pair scheduler disabled")
        self.pairs.retry(pair_id)

    def status(self, pair_id: str) -> Optional[Dict[str, Any]]:
        if self.pairs is None:
            return None
        return self.pairs.status(pair_id)

    def pending(self) -> list:
        if self.pairs is None:
            return []
        return self.pairs.pending()

    def orphans(self) -> list:
        if self.pairs is None:
            return []
        return self.pairs.orphans()

    def by_kind(self, kind: str) -> list:
        if self.pairs is None:
            return []
        return self.pairs.by_kind(kind)

    def sweep(self) -> list:
        if self.pairs is None:
            return []
        return self.pairs.sweep()
