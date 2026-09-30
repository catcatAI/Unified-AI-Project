"""路由引擎（Routing Engine）：清單驅動的執行者。

- 依清單（tier → priority）逐連接器執行：attempt 命中即返、miss 落下一列；
  terminal 拒絕則落下一列（安全網保證最後必有 terminal）。
- 預算：每一輪 generate 最多允許 N 次跨連接器「跳線」——資訊流在
  清單上的串接次數有上限，防止 AI 重排把管線接成無限迴圈。
- 遙測：每次執行把逐步 outcome（hit/miss/error/…）上報 StateStore
  （routing.telemetry 事件＋routing 持久狀態），作為 AI 學習回饋。
- AI 重排：``plan_for()`` 提供執行期調整鉤子（目前是保守的歷史命中率
  啟發式；未來可接學習器）。
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

from core.interfaces.protocols import LLMResponse
from core.system.state_store import state_store

from .spec import ConnectorFn, StepOutcome, StepSpec

logger = logging.getLogger(__name__)

# 單輪 generate 允許的最大跨連接器跳線次數。
# 必須 >= 預設清單的步驟數（否則正常 miss 串就會被預算掐斷）；
# 同時為 AI 動態重排／AI↔AI 接通保留上限（防資訊流被接成迴圈）。
MAX_HOPS_PER_REQUEST = 12


class RoutingEngine:
    """依路由清單（RouteManifest）執行連接器的唯一執行者。"""

    def __init__(self, max_hops: Optional[int] = None) -> None:
        self._connectors: Dict[str, ConnectorFn] = {}
        self._max_hops = (
            max_hops
            if max_hops is not None
            else max(4, int(os.environ.get("ANGELA_ROUTING_MAX_HOPS", MAX_HOPS_PER_REQUEST)))
        )
        self._stats: Dict[str, Dict[str, int]] = {}

    # ---------- 連接器註冊 ----------

    def register(self, name: str, fn: ConnectorFn) -> None:
        if name in self._connectors:
            raise ValueError(f"duplicate connector: {name}")
        self._connectors[name] = fn

    # ---------- 清單執行 ----------

    async def run(
        self,
        plan: List[StepSpec],
        user_message: str,
        context: Dict[str, Any],
    ) -> LLMResponse:
        """依清單順序執行；回傳第一個命中連接器的回應。

        終結步驟（kind="terminal"）拒絕時繼續往下找（清單尾端必須有
        安全網 terminal）。超過跳線預算後直接跳到安全網。
        """
        ordered = sorted((s for s in plan if s.enabled), key=lambda s: s.sort_key())
        outcomes: List[StepOutcome] = []
        hops = 0
        start = time.time()

        for step in ordered:
            fn = self._connectors.get(step.connector)
            if fn is None:
                outcomes.append(
                    StepOutcome(
                        step=step.name,
                        connector=step.connector,
                        outcome="error",
                        elapsed_ms=0.0,
                        error="connector not registered",
                    )
                )
                logger.error("[routing] connector %r not registered", step.connector)
                continue

            if hops >= self._max_hops and step.kind != "terminal":
                outcomes.append(
                    StepOutcome(
                        step=step.name, connector=step.connector, outcome="budget", elapsed_ms=0.0
                    )
                )
                continue

            t0 = time.perf_counter()
            try:
                response = await fn(user_message, context)
            except Exception as exc:  # noqa: BLE001 — 單步故障不拖垮整輪路由
                outcomes.append(
                    StepOutcome(
                        step=step.name,
                        connector=step.connector,
                        outcome="error",
                        elapsed_ms=(time.perf_counter() - t0) * 1000,
                        error=str(exc),
                    )
                )
                logger.warning("[routing] step %s error: %s", step.name, exc)
                continue

            hops += 1
            elapsed = (time.perf_counter() - t0) * 1000
            if response is not None:
                outcomes.append(
                    StepOutcome(
                        step=step.name, connector=step.connector, outcome="hit", elapsed_ms=elapsed
                    )
                )
                md = response.metadata or {}
                md["routing_trace"] = [o.step for o in outcomes]
                md["routing_hops"] = hops
                response.metadata = md
                self._record(outcomes, total_ms=(time.time() - start) * 1000)
                return response
            outcomes.append(
                StepOutcome(
                    step=step.name, connector=step.connector, outcome="miss", elapsed_ms=elapsed
                )
            )

        # 清單沒有任何 terminal 接住（配置錯誤）——最後的誠實防線
        logger.error("[routing] manifest exhausted without terminal hit")
        self._record(outcomes, total_ms=(time.time() - start) * 1000)
        return LLMResponse(
            text="我目前無法正確處理這個請求，請稍後再試或換個說法。",
            backend="routing-engine",
            model="manifest-exhausted",
            confidence=0.3,
            metadata={"routing_trace": [o.step for o in outcomes], "routing": "exhausted"},
        )

    # ---------- 觀測與學習 ----------

    def _record(self, outcomes: List[StepOutcome], total_ms: float) -> None:
        """上報逐步遙測：事件（即時）＋持久狀態（學習回饋用）。"""
        for o in outcomes:
            bucket = self._stats.setdefault(o.step, {"hit": 0, "miss": 0, "error": 0, "budget": 0})
            if o.outcome in bucket:
                bucket[o.outcome] += 1

        trace = [o.outcome if o.outcome != "hit" else "HIT" for o in outcomes]
        state_store.emit_event(
            "routing.telemetry",
            {
                "trace": trace,
                "hops": len(outcomes),
                "total_ms": round(total_ms, 1),
                "hit_step": next((o.step for o in outcomes if o.outcome == "hit"), None),
            },
        )
        try:
            routing_state = state_store.get_state("routing")
            steps_state = routing_state.get("steps", {})
            for o in outcomes:
                b = steps_state.setdefault(o.step, {"hit": 0, "miss": 0, "error": 0, "budget": 0})
                if o.outcome in b:
                    b[o.outcome] += 1
            state_store.update_state(
                "routing", {"steps": steps_state, "last_trace": trace}, notify=False
            )
        except Exception as exc:  # 遙測失敗不影響路由本身
            logger.debug("routing telemetry persist failed: %s", exc)

    def plan_for(self, user_message: str, context: Dict[str, Any]) -> Optional[List[str]]:
        """AI 重排鉤子（保守啟發式）：回傳建議的步驟順序，None 表示不調整。

        目前依歷史命中率把「幾乎總是 miss」的步驟後移。未來可替換為
        真正的學習器（讀 routing.steps 統計＋訊息特徵）。
        """
        try:
            steps_state = state_store.get_state("routing").get("steps", {})
        except Exception:
            return None
        if not steps_state:
            return None
        cold = [
            name
            for name, b in steps_state.items()
            if b.get("miss", 0) >= 50 and b.get("hit", 0) == 0
        ]
        return cold if cold else None

    def get_step_stats(self) -> Dict[str, Dict[str, int]]:
        return dict(self._stats)
