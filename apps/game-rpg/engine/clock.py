# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — 中控時鐘（計畫 §6.2/§6.3/§6.4 M3）。

master tick 固定推進牆鐘 dt；各組以「本組週期 1/tick_rate」累積
``dt × time_scale`` → 到期即 fire（子彈時間=縮慢累積，不改週期長度）。

§6.4：**外包** `world_clock` 的 world_lines 索引（不重寫其曆法/時間線）——
``MasterClock(..., time_flow_source=world_clock.get_time_flow_ratio)`` 以
`flow_id` 查該世界線流速比當 time_scale；查無（None/未掛）回群組建構值。
`group_dt()` 即「group_dt 分發 API」：回傳該組單次 fire 的本地 dt（=週期）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from engine.axes import AxisGroup

TimeFlowSource = Callable[[str], Optional[float]]


@dataclass
class GroupClock:
    """單組時鐘狀態：週期累積器 + 統計。"""

    tick_rate: float
    time_scale: float = 1.0
    acc: float = 0.0  # 累積秒數 [0, period)
    fired: int = 0
    flow_id: Optional[str] = None

    @property
    def period(self) -> float:
        return 1.0 / self.tick_rate


@dataclass
class MasterClock:
    """中控時鐘：master tick → 各組 dt 累積 → 到期次數分發。"""

    master_hz: float = 60.0
    time_flow_source: Optional[TimeFlowSource] = None
    master_ticks: int = 0
    _groups: Dict[str, GroupClock] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if self.master_hz <= 0:
            raise ValueError(f"master_hz must be > 0, got {self.master_hz}")

    # ------------------------------------------------------------------
    # 註冊 / 覆寫
    # ------------------------------------------------------------------
    def register_group(self, group: AxisGroup, flow_id: Optional[str] = None) -> None:
        """註冊群組；``flow_id`` 經 time_flow_source 查世界線流速比覆寫 time_scale。"""
        if group.name in self._groups:
            raise ValueError(f"group {group.name!r} already registered on clock")
        scale = group.time_scale
        if flow_id is not None and self.time_flow_source is not None:
            ratio = self.time_flow_source(flow_id)
            if ratio is not None:
                if ratio < 0:
                    raise ValueError(f"time flow ratio for {flow_id!r} must be >= 0, got {ratio}")
                scale = float(ratio)
        if scale < 0:
            raise ValueError(f"time_scale must be >= 0, got {scale}")
        self._groups[group.name] = GroupClock(
            tick_rate=group.tick_rate, time_scale=scale, flow_id=flow_id
        )

    def set_time_scale(self, group_name: str, scale: float) -> None:
        """執行期覆寫子彈時間（0=暫停該組）。"""
        gc = self._clock_of(group_name)
        if scale < 0:
            raise ValueError(f"time_scale must be >= 0, got {scale}")
        gc.time_scale = scale

    def fired(self, group_name: str) -> int:
        """該組累積 fire 次數（M3 驗收以 tick 計數）。"""
        return self._clock_of(group_name).fired

    def time_scale_of(self, group_name: str) -> float:
        """該組當前 time_scale（M8 執行器快照用；含世界線流速覆寫後值）。"""
        return self._clock_of(group_name).time_scale

    def group_dt(self, group_name: str) -> float:
        """group_dt 分發 API：該組單次 fire 的本地 dt（= 1/tick_rate）。"""
        return self._clock_of(group_name).period

    def group_names(self) -> list:
        return list(self._groups)

    # ------------------------------------------------------------------
    # 推進
    # ------------------------------------------------------------------
    def tick(self) -> Dict[str, int]:
        """推進一個 master tick；回傳本輪各組到期 fire 次數 ``{group: n}``。"""
        dt = 1.0 / self.master_hz
        due: Dict[str, int] = {}
        for name, gc in self._groups.items():
            if gc.time_scale == 0:
                due[name] = 0
                continue
            gc.acc += dt * gc.time_scale
            n = 0
            while gc.acc >= gc.period:
                gc.acc -= gc.period
                n += 1
            if n:
                gc.fired += n
            due[name] = n
        self.master_ticks += 1
        return due

    def run(self, master_ticks: int) -> Dict[str, int]:
        """跑 N 個 master tick；回傳各組累積 fire 次數（測試/批次便利）。"""
        if master_ticks < 0:
            raise ValueError(f"master_ticks must be >= 0, got {master_ticks}")
        for _ in range(master_ticks):
            self.tick()
        return {name: gc.fired for name, gc in self._groups.items()}

    # ------------------------------------------------------------------
    def _clock_of(self, group_name: str) -> GroupClock:
        if group_name not in self._groups:
            raise KeyError(f"unknown clock group: {group_name!r}")
        return self._groups[group_name]
