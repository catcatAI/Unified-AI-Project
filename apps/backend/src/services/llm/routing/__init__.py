"""services.llm.routing — 路由清單＋連接器＋引擎。

把 router 的 if-else 決策瀑布整理成：
  manifest（清單）→ engine（執行/預算/遙測）→ connectors（連接器）。
"""

from .engine import MAX_HOPS_PER_REQUEST, RoutingEngine
from .manifest import DEFAULT_PLAN, RouteManifest
from .spec import ConnectorFn, RouteConnector, StepOutcome, StepSpec

__all__ = [
    "DEFAULT_PLAN",
    "MAX_HOPS_PER_REQUEST",
    "ConnectorFn",
    "RouteConnector",
    "RouteManifest",
    "RoutingEngine",
    "StepOutcome",
    "StepSpec",
]
