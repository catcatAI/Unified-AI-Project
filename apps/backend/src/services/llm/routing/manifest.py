"""路由清單（Route Manifest）：聲明式的步驟清單與連接器註冊。

預設清單 = 舊版 if-else 瀑布的精確順序（行為不變）。
AI 模式下，引擎可在執行期依回饋重排清單（plan_for 鉤子）。
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .spec import StepSpec

# 預設清單：與 legacy generate_response_full 的決策順序一一對應。
# tier 越小越先執行；kind="terminal" 的步驟拒絕時落往下一段。
DEFAULT_PLAN: List[StepSpec] = [
    # tier 0：快取層（前置哨兵，總是最先）
    StepSpec(name="pipeline_math", connector="pipeline_math", tier=0, priority=0),
    StepSpec(name="math_backup", connector="math_backup", tier=0, priority=1),
    StepSpec(name="clock", connector="clock", tier=0, priority=2),
    # tier 1：高確定性確定路徑
    StepSpec(name="template_match", connector="template_match", tier=1, priority=0),
    StepSpec(name="ensemble", connector="ensemble", tier=1, priority=1),
    StepSpec(name="memory_retrieval", connector="memory_retrieval", tier=1, priority=2),
    StepSpec(name="knowledge", connector="knowledge", tier=1, priority=3),
    StepSpec(name="neural_bridge", connector="neural_bridge", tier=1, priority=4),
    # tier 2：主 LLM 生成路徑（拒絕時由 fallback 接手）
    StepSpec(name="main_llm", connector="main_llm", tier=2, priority=0),
    # tier 9：安全網（誠實回退，必須永遠在最後）
    StepSpec(name="fallback", connector="fallback", tier=9, priority=0, kind="terminal"),
]

# 安全網檢查：清單尾端必須有 terminal，否則引擎的 exhausted 防線會常駐。
assert DEFAULT_PLAN[-1].kind == "terminal", "manifest must end with a terminal step"


class RouteManifest:
    """路由清單：持有計畫並提供執行期重排（AI 依需求接通資訊流）。"""

    def __init__(self, plan: Optional[List[StepSpec]] = None) -> None:
        self._plan: List[StepSpec] = list(plan) if plan is not None else list(DEFAULT_PLAN)

    @property
    def plan(self) -> List[StepSpec]:
        return list(self._plan)

    def reorder(self, order: List[str]) -> None:
        """依名稱順序重排（未列出的步驟保持相對順序接在後面）。"""
        rank = {name: i for i, name in enumerate(order)}
        terminal = [s for s in self._plan if s.kind == "terminal"]
        self._plan.sort(key=lambda s: rank.get(s.name, len(order)))

        # 安全網（terminal）恆在尾端：AI 重排不得把它提前
        non_terminal = [s for s in self._plan if s.kind != "terminal"]
        self._plan = non_terminal + terminal

    def set_enabled(self, name: str, enabled: bool) -> bool:
        for step in self._plan:
            if step.name == name:
                step.enabled = enabled
                return True
        return False

    def to_dict(self) -> Dict[str, object]:
        return {
            "steps": [
                {
                    "name": s.name,
                    "connector": s.connector,
                    "kind": s.kind,
                    "tier": s.tier,
                    "priority": s.priority,
                    "enabled": s.enabled,
                }
                for s in self._plan
            ]
        }
