"""路由清單規格（Route Manifest Spec）。

路由不再是一長串 if-else 瀑布，而是一份聲明式清單：每一步描述
「用哪個連接器、是嘗試性還是終結性、屬於哪一層」。引擎依清單執行，
AI 可在執行期依需求重排清單（set_plan / plan_for）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional, Protocol, runtime_checkable

from core.interfaces.protocols import LLMResponse


@dataclass
class StepSpec:
    """路由清單中的一列。

    Attributes:
        name: 步驟唯一名稱（遙測與學習回饋的主鍵）。
        connector: 連接器鍵名（對應 connectors registry）。
        kind: "attempt"（可拒絕，回傳 None 落到下一步）或
              "terminal"（必須給出答案；拒絕則觸發安全網）。
        tier: 層級，數字越小越先執行（清單主排序鍵）。
        priority: 同層內的次要排序鍵。
        enabled: 關閉的步驟被引擎跳過（用於 A/B 或功能開關）。
    """

    name: str
    connector: str
    kind: str = "attempt"  # "attempt" | "terminal"
    tier: int = 0
    priority: int = 0
    enabled: bool = True

    def sort_key(self) -> tuple[int, int, int]:
        return (self.tier, self.priority, 0)


@runtime_checkable
class RouteConnector(Protocol):
    """連接器統一介面：接收 (訊息, 上下文)，回應或拒絕（None）。

    連接器包裝既有決策方法（_try_*、fallback、主路徑），
    引擎只認得這個介面——新增路徑＝註冊一個連接器＋清單加一列。
    """

    async def __call__(
        self, user_message: str, context: Dict[str, Any]
    ) -> Optional[LLMResponse]: ...


ConnectorFn = Callable[[str, Dict[str, Any]], Awaitable[Optional[LLMResponse]]]


@dataclass
class StepOutcome:
    """單步執行結果（遙測與學習的最小單位）。"""

    step: str
    connector: str
    outcome: str  # "hit" | "miss" | "error" | "skipped" | "budget"
    elapsed_ms: float
    error: Optional[str] = None
