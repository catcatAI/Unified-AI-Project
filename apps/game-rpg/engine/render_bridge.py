# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — 表現層 render bridge（計畫 §6.2/§6.3 M4）。

**狀態分離**：模擬層只 `push()` 快照；渲染層 `sample()`/`sample_at()` 只讀
前後快照做時間插值（**30Hz 模擬 / 144Hz 顯示中間幀=線性 lerp**）。

像素吸附：lerp 結果過 M2 `quantize(x, pixel_size)`（半遠離零落格，避免
子像素抖動）；`pixel_size=0` 關吸附=連續值。純數值渲染器，M6 才接
PyQt6/SDL。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional

from engine.axes import Entity
from engine.quantize import quantize


@dataclass(frozen=True)
class EntityState:
    """快照內的實體表現狀態（frozen：push 後不可變，狀態分離）。"""

    id: str
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True)
class RenderState:
    """sample() 輸出：像素吸附後的表現座標。"""

    id: str
    x: float
    y: float


class RenderBridge:
    """前後快照 lerp 橋：只讀模擬層，渲染端以 alpha/時間取樣。"""

    def __init__(self, pixel_size: float = 1.0) -> None:
        if pixel_size < 0:
            raise ValueError(f"pixel_size must be >= 0, got {pixel_size}")
        self.pixel_size = pixel_size
        self.prev: Dict[str, EntityState] = {}
        self.curr: Dict[str, EntityState] = {}
        self.prev_time: float = 0.0
        self.curr_time: float = 0.0

    # ------------------------------------------------------------------
    # 模擬層 → 快照（寫入端）
    # ------------------------------------------------------------------
    def push(self, states: Mapping[str, EntityState], sim_time: Optional[float] = None) -> None:
        """推一幀模擬快照；``sim_time`` 需非遞減（防倒退插值）。"""
        t = self.curr_time if sim_time is None else float(sim_time)
        if self.curr and t < self.curr_time:
            raise ValueError(f"sim_time must be non-decreasing: {t} < {self.curr_time}")
        new = {eid: EntityState(s.id, s.x, s.y) for eid, s in states.items()}
        self.prev, self.prev_time = self.curr, self.curr_time
        self.curr, self.curr_time = new, t

    def push_entities(
        self,
        entities: Iterable[Entity],
        group: str,
        sim_time: Optional[float] = None,
        x_key: str = "x",
        y_key: str = "y",
    ) -> None:
        """M1 Entity → 快照：取指定群組的 x/y 軸值（非數值→0.0）。"""
        states: Dict[str, EntityState] = {}
        for ent in entities:
            vals = ent.groups.get(group, {})
            x, y = vals.get(x_key), vals.get(y_key)
            states[f"e{ent.eid}"] = EntityState(
                id=f"e{ent.eid}",
                x=float(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else 0.0,
                y=float(y) if isinstance(y, (int, float)) and not isinstance(y, bool) else 0.0,
            )
        self.push(states, sim_time)

    # ------------------------------------------------------------------
    # 渲染層（只讀）
    # ------------------------------------------------------------------
    def sample(self, alpha: float) -> Dict[str, RenderState]:
        """前後快照間取樣：兩幀皆活 → 線性 lerp；僅 curr（新生成）→ curr 位；
        不在 curr（已移除）→ 不渲染。lerp 後像素吸附。"""
        a = min(max(float(alpha), 0.0), 1.0)
        out: Dict[str, RenderState] = {}
        for eid, cs in self.curr.items():
            ps = self.prev.get(eid)
            if ps is not None:
                x = ps.x + (cs.x - ps.x) * a
                y = ps.y + (cs.y - ps.y) * a
            else:
                x, y = cs.x, cs.y
            out[eid] = RenderState(id=eid, x=self._snap(x), y=self._snap(y))
        return out

    def sample_at(self, display_time: float) -> Dict[str, RenderState]:
        """以顯示端時間取樣（30Hz 模擬 / 144Hz 顯示入口）：
        alpha = (t - prev_time) / (curr_time - prev_time)，clamp [0,1]。"""
        if not self.curr:
            return {}
        if self.curr_time == self.prev_time:
            a = 1.0
        else:
            a = (display_time - self.prev_time) / (self.curr_time - self.prev_time)
        return self.sample(a)

    def _snap(self, v: float) -> float:
        return quantize(v, self.pixel_size)
