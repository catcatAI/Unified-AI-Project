# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================
#
# 職責: 中層「學習協調器」（§5.5.2）— LearningCoordinator
#       （步驟 B5: chat_service 內嵌學習 → CNS 事件驅動）
# 維度: β 認知維度（學習/持續增量寫回）
# 安全: 使用 Key A (後端控制)
# 成熟度: L2+ 等級開始接觸學習協調概念
#
# =============================================================================

"""中層「學習協調器」（§5.5.2 / 步驟 B5）。

學習是**異步、增量、持續**的寫回流程（用完回應後長知識）。統一經中層的
`LearningCoordinator` 接線：訂閱 CNS 事件（`routing.response_generated`）
而非在 `chat_service` 內嵌呼叫。

```python
backbone.register_learning("continuous", ContinuousLearningPipeline)
backbone.register_learning("garden", GARDENLearningPipeline)
# 觸發: CNS 事件 response_generated → coordinator 依序執行 registered learners
```

成對排程（步驟 B4 精神）：每個 learner 執行經 `backbone.io.submit/resolve`
（kind=learning），失敗/逾時標記 ERROR/ORPHAN，學習寫回永不靜默。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional

from core.backbone.contracts import Envelope, EnvelopeKind

logger = logging.getLogger("angela_backbone_learning")

LEARNING_EVENT = "routing.response_generated"


class LearningCoordinator:
    """學習協調器（§5.5.2）。

    Args:
        pair_scheduler: `PairScheduler`（可選，成對追蹤）。
        state_store: CNS `GlobalStateStore`（可選，訂閱事件）。
        pair_kind: 成對 kind（預設 "learning"）。
    """

    def __init__(
        self,
        pair_scheduler: Any = None,
        state_store: Any = None,
        pair_kind: str = EnvelopeKind.LEARNING,
    ) -> None:
        self.pairs = pair_scheduler
        self.state_store = state_store
        self.pair_kind = pair_kind
        self._learners: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self._subscribed = False

    # ------------------------------------------------------------------
    # 註冊
    # ------------------------------------------------------------------
    def register_learning(self, name: str, coroutine_factory: Callable) -> None:
        """註冊學習協調器（async callable）。"""
        self._learners[name] = coroutine_factory

    def unregister(self, name: str) -> bool:
        return self._learners.pop(name, None) is not None

    def names(self) -> list:
        return list(self._learners.keys())

    def has(self, name: str) -> bool:
        return name in self._learners

    # ------------------------------------------------------------------
    # CNS 事件訂閱（§5.5.2）
    # ------------------------------------------------------------------
    def subscribe(self, state_store: Any = None) -> bool:
        """訂閱 CNS `routing.response_generated` 事件。

        事件 payload 預期含 `user_message` / `response` / `context`。
        每次事件觸發時以 background task 依序執行所有已註冊 learners。
        """
        store = state_store or self.state_store
        if store is None or self._subscribed:
            return False
        try:
            store.subscribe_event(LEARNING_EVENT, self._on_response_generated)
            self.state_store = store
            self._subscribed = True
            return True
        except Exception as exc:
            logger.warning("learning coordinator subscribe failed: %s", exc)
            return False

    def unsubscribe(self) -> bool:
        if self.state_store is None or not self._subscribed:
            return False
        try:
            self.state_store.unsubscribe_event(LEARNING_EVENT, self._on_response_generated)
            self._subscribed = False
            return True
        except Exception as exc:
            logger.warning("learning coordinator unsubscribe failed: %s", exc)
            return False

    def _on_response_generated(self, event_type: str, data: Dict[str, Any]) -> None:
        """CNS 事件 callback（fire-and-forget，background task）。"""
        user_message = data.get("user_message", "")
        response = data.get("response")
        context = data.get("context") or {}
        if response is None:
            logger.warning("learning event missing response, skipping")
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.trigger(user_message, response, context))
            else:  # pragma: no cover - 同步 context
                loop.run_until_complete(self.trigger(user_message, response, context))
        except Exception as exc:
            logger.warning("learning event task creation failed: %s", exc)

    # ------------------------------------------------------------------
    # 執行（成對排程，步驟 B4）
    # ------------------------------------------------------------------
    async def trigger(
        self,
        user_message: str,
        response: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """依序執行所有 registered learners。

        每個 learner 執行經 `backbone.io.submit/resolve`（kind=learning）；
        失敗標記 ERROR 但**不中斷**其他 learner（學習寫回永不阻塞主流程）。
        """
        results: Dict[str, Any] = {}
        for name, learner in self._learners.items():
            results[name] = await self._run_one(name, learner, user_message, response, context)
        return results

    async def _run_one(
        self,
        name: str,
        learner: Callable,
        user_message: str,
        response: Any,
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        envelope = Envelope(
            payload={"user_message": user_message, "response": response, "context": context},
            kind=self.pair_kind,
            source=f"learning:{name}",
        )
        pair_id: Optional[str] = None
        if self.pairs is not None:
            pair_id = self.pairs.submit(envelope, timeout=30.0, kind=self.pair_kind)

        try:
            result = await learner(user_message, response, context)
        except Exception as exc:
            logger.warning("learner %s failed: %s", name, exc, exc_info=True)
            if pair_id is not None and self.pairs is not None:
                try:
                    self.pairs.fail(pair_id, reason=str(exc))
                except Exception:
                    pass
            return {"status": "ERROR", "error": str(exc)}
        else:
            if pair_id is not None and self.pairs is not None:
                output = Envelope(
                    payload=result,
                    kind=self.pair_kind,
                    direction="up",
                    correlation_id=envelope.correlation_id,
                    source=f"learning:{name}",
                )
                try:
                    self.pairs.resolve(pair_id, output)
                except Exception:
                    pass
            return {"status": "PAIRED"}

    def clear(self) -> None:
        self._learners.clear()
