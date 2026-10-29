# -*- coding: utf-8 -*-
"""萬物皆軸引擎（計畫 §六）——Entity/AxisSpec/AxisGroup + 契約 + 最小管線。

M1：軸/實體/契約註冊驗證、空間+戰鬥兩群組、組間訊號下一 tick 可見。
後續里程碑（M2 量化 / M3 中控時鐘 / M4 快照插值）在此目錄疊加，
不動既有 19,982 行 CLI 代碼；失敗可整目錄刪除。
"""

from engine.axes import AxisGroup, AxisSpec, AxisType, Entity, Value
from engine.clock import GroupClock, MasterClock
from engine.contracts import (
    SIGNAL_DTYPES,
    ContractError,
    GroupContract,
    MissingSignalError,
    SignalSpec,
)
from engine.pipeline import EnginePipeline, TickContext
from engine.quantize import (
    from_fixed,
    quantize,
    quantize_auto,
    quantize_axis,
    quantize_fixed,
)
from engine.render_bridge import EntityState, RenderBridge, RenderState
from engine.runner import EngineRunner

__all__ = [
    "AxisGroup",
    "AxisSpec",
    "AxisType",
    "ContractError",
    "EnginePipeline",
    "EngineRunner",
    "Entity",
    "EntityState",
    "GroupClock",
    "GroupContract",
    "MasterClock",
    "MissingSignalError",
    "RenderBridge",
    "RenderState",
    "SIGNAL_DTYPES",
    "SignalSpec",
    "TickContext",
    "Value",
    "from_fixed",
    "quantize",
    "quantize_auto",
    "quantize_axis",
    "quantize_fixed",
]
