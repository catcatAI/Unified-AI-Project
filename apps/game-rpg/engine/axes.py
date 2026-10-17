# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — 軸與實體（計畫 §六 M1，純 stdlib，不動既有 19,982 行）。

AxisSpec 描述單軸（連續/離散/FSM），AxisGroup 聚合一組軸 + 契約 + 掛載率，
Entity 以「群組→軸值字典」表達（§6.1 使用戶文檔資料結構）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Literal, Optional, Tuple, Union

if TYPE_CHECKING:  # pragma: no cover
    from engine.contracts import GroupContract

AxisType = Literal["continuous", "discrete", "fsm"]
Value = Union[float, int, str, bool]

_AXIS_KINDS: Tuple[str, ...] = ("continuous", "discrete", "fsm")


@dataclass
class AxisSpec:
    """單一軸的規格。

    step=0 表連續不量化（M2 量化吸附：step>0 才 round(v/step)*step）；
    fsm 以 states 列舉合法狀態；lo/hi 為數值軸範圍（可省略）。
    """

    name: str
    kind: AxisType
    lo: Optional[float] = None
    hi: Optional[float] = None
    step: float = 0.0
    states: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("AxisSpec.name must not be empty")
        if self.kind not in _AXIS_KINDS:
            raise ValueError(f"unknown axis kind: {self.kind!r}; expected {_AXIS_KINDS}")
        if self.step < 0:
            raise ValueError(f"step must be >= 0, got {self.step}")
        if self.kind == "discrete" and self.step <= 0:
            raise ValueError(f"discrete axis {self.name!r} requires step > 0")
        if self.kind == "fsm" and not self.states:
            raise ValueError(f"fsm axis {self.name!r} requires states")
        if self.kind != "fsm" and self.states:
            raise ValueError(f"states only allowed on fsm axis {self.name!r}")
        if self.lo is not None and self.hi is not None and self.lo > self.hi:
            raise ValueError(f"axis {self.name!r}: lo {self.lo} > hi {self.hi}")

    def contains(self, value: Value) -> bool:
        """值是否在軸範圍/枚舉內（fsm 依 states，數值依 lo/hi）。"""
        if self.kind == "fsm":
            return value in self.states
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False
        if self.lo is not None and value < self.lo:
            return False
        if self.hi is not None and value > self.hi:
            return False
        return True


@dataclass
class AxisGroup:
    """軸群組：掛載率（Hz）+ 軸集 + 輸出契約。

    field 順序依 Python 資料類別約束（non-default 不得跟在 default 後），
    契約 ``group`` 名必須與本群組同名（register 時再驗一次）。
    """

    name: str
    tick_rate: float
    axes: Dict[str, AxisSpec]
    contract: "GroupContract"
    time_scale: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("AxisGroup.name must not be empty")
        if self.tick_rate <= 0:
            raise ValueError(f"tick_rate must be > 0, got {self.tick_rate}")
        if self.time_scale <= 0:
            raise ValueError(f"time_scale must be > 0, got {self.time_scale}")
        if not self.axes:
            raise ValueError(f"group {self.name!r} requires at least one axis")
        for key, spec in self.axes.items():
            if key != spec.name:
                raise ValueError(
                    f"group {self.name!r}: axes key {key!r} != spec.name {spec.name!r}"
                )
        if self.contract.group != self.name:
            raise ValueError(f"group {self.name!r}: contract for {self.contract.group!r} mismatch")


@dataclass
class Entity:
    """實體：群組→軸值字典；parent/local_offset 是非軸連結（§6.1）。"""

    eid: int
    groups: Dict[str, Dict[str, Value]] = field(default_factory=dict)
    parent: Optional[int] = None
    local_offset: Optional[Tuple[float, ...]] = None
