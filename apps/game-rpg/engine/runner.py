# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — M8 常駐 tick 迴圈（§6.4「生產 tick 迴圈」遠期項落地）。

`EngineRunner` 把 M1 管線（組間訊號下一 tick 可見）＋ M3 中控時鐘
（master tick→組 dt 累積→time_scale 子彈時間）＋ M4 渲染橋（快照插值）
串成可 start/stop 的執行器；生產端接線＝backend `game_routes` 的
`/game/engine/{start,stop,snapshot}`。

- ``step()``：同步推進一個 master tick——確定性核心，測試直接驅動；
  時鐘到期 n 次的群組跑 n 次 handler（M3 語意：time_scale 0.2×＝少跑
  fire，不是快跑 handler）。
- ``start()/stop()``：牆鐘 master_hz 常駐 daemon 執行緒；stop 事件喚醒
  等待、落後不連發（resync 防突發）、start/stop 皆冪等。
- ``push_states/push_entities/sample/sample_at``：外包 M4 RenderBridge
  ——pixel-angela 由 ``snapshot()``/``sample()`` 輪詢取數（ws 推送仍為
  §6.4 遠期項）。
- ``snapshot()``：執行緒安全唯讀快照（running/master_ticks/組 fire 與
  dt/time_scale/訊號表），輪詢消費介面的資料形狀。
"""

from __future__ import annotations

import threading
import time
from typing import Any, Callable, Dict, Mapping, Optional

from engine.axes import AxisGroup
from engine.clock import MasterClock
from engine.contracts import ContractError
from engine.pipeline import EnginePipeline, Handler
from engine.render_bridge import RenderBridge

TimeFlowSource = Callable[[str], Optional[float]]


class EngineRunner:
    """常駐 tick 執行器：確定性 step 核心 + 可選牆鐘執行緒。"""

    def __init__(
        self,
        master_hz: float = 60.0,
        time_flow_source: Optional[TimeFlowSource] = None,
    ) -> None:
        self._pipeline = EnginePipeline()
        self._clock = MasterClock(master_hz=master_hz, time_flow_source=time_flow_source)
        self._bridge = RenderBridge()
        self._lock = threading.RLock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    # ------------------------------------------------------------------
    # 組態（唯讀）
    # ------------------------------------------------------------------
    @property
    def clock(self) -> MasterClock:
        return self._clock

    @property
    def pipeline(self) -> EnginePipeline:
        return self._pipeline

    @property
    def bridge(self) -> RenderBridge:
        return self._bridge

    @property
    def running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    # 註冊 / 啟動
    # ------------------------------------------------------------------
    def register(self, group: AxisGroup, handler: Handler, flow_id: Optional[str] = None) -> None:
        """註冊群組到管線+時鐘（flow_id 經 time_flow_source 查世界線流速）。

        執行緒啟動後不得再註冊（避免執行中結構變更）。
        """
        if self._thread is not None:
            raise RuntimeError("cannot register groups after start()")
        self._pipeline.register_group(group, handler)
        self._clock.register_group(group, flow_id=flow_id)

    def startup(self) -> None:
        """解析契約依賴（缺訊號 raise MissingSignalError）；重複呼叫無害。"""
        self._pipeline.startup()

    # ------------------------------------------------------------------
    # 推進
    # ------------------------------------------------------------------
    def step(self) -> Dict[str, int]:
        """推進一個 master tick；回傳本輪各組到期 fire 次數。"""
        if not self._pipeline.started:
            raise ContractError("runner not started; call startup() first")
        with self._lock:
            due = self._clock.tick()
            for name, n in due.items():
                if n <= 0:
                    continue
                for _ in range(n):
                    self._pipeline.tick_group(name)
            return due

    def run(self, master_ticks: int) -> Dict[str, int]:
        """跑 N 個 master tick；回傳各組累積 fire 次數（測試/批次便利）。"""
        for _ in range(master_ticks):
            self.step()
        return {name: self._clock.fired(name) for name in self._clock.group_names()}

    def start(self) -> Dict[str, Any]:
        """啟動牆鐘執行緒（冪等：已在跑則直接回快照）。"""
        if self._running and self._thread is not None and self._thread.is_alive():
            return self.snapshot()
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="axis-engine-runner", daemon=True)
        self._running = True
        self._thread.start()
        return self.snapshot()

    def stop(self, timeout: float = 5.0) -> Dict[str, Any]:
        """停止執行緒（冪等：未在跑直接回快照）；join 有界超時防掛死。"""
        self._stop.set()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout)
        self._thread = None
        self._running = False
        return self.snapshot()

    def _loop(self) -> None:
        period = 1.0 / self._clock.master_hz
        next_deadline = time.monotonic()
        while not self._stop.is_set():
            self.step()
            next_deadline += period
            delay = next_deadline - time.monotonic()
            if delay > 0:
                self._stop.wait(delay)
            else:
                # 落後（GC/排程尖峰）：重設基準不補發，避免子彈式追幀
                next_deadline = time.monotonic()

    # ------------------------------------------------------------------
    # 渲染橋外包（M4）
    # ------------------------------------------------------------------
    def push_states(self, states: Mapping[str, Any], sim_time: Optional[float] = None) -> None:
        """推表現狀態進渲染橋（EntityState 映射，M4 push 契約）。"""
        with self._lock:
            self._bridge.push(states, sim_time=sim_time)

    def push_entities(
        self,
        entities: Any,
        group: str,
        sim_time: Optional[float] = None,
        x_key: str = "x",
        y_key: str = "y",
    ) -> None:
        """推 M1 Entity 序列進渲染橋（取指定群組 x/y 軸，同 M4 契約）。"""
        with self._lock:
            self._bridge.push_entities(entities, group, sim_time=sim_time, x_key=x_key, y_key=y_key)

    def sample(self, alpha: float) -> Dict[str, Any]:
        with self._lock:
            return self._bridge.sample(alpha)

    def sample_at(self, display_time: float) -> Dict[str, Any]:
        with self._lock:
            return self._bridge.sample_at(display_time)

    # ------------------------------------------------------------------
    # 快照
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """執行緒安全唯讀快照（輪詢消費介面，M8）。"""
        with self._lock:
            return {
                "running": self._running,
                "master_hz": self._clock.master_hz,
                "master_ticks": self._clock.master_ticks,
                "pipeline_ticks": self._pipeline.ticks,
                "groups": {
                    name: {
                        "fired": self._clock.fired(name),
                        "dt": self._clock.group_dt(name),
                        "time_scale": self._clock.time_scale_of(name),
                    }
                    for name in self._clock.group_names()
                },
                "signals": self._pipeline.signal_snapshot(),
            }
