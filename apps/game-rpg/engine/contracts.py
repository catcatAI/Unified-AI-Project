# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — 訊號契約（計畫 §6.1/§6.2 M1）。

GroupContract 聲明群組**輸出**（provides）與**依賴**（requires，格式
``"group.signal"``）。建構即驗證（訊號名/型別/精度），Pipeline.startup()
再解析跨群組依賴——**缺訊號啟動即 raise**（M1 驗收）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

SIGNAL_DTYPES: Tuple[str, ...] = ("float", "int", "bool", "str")
_INT_LIKE = ("int", "bool", "str")


class ContractError(ValueError):
    """契約違反（重名/型別/精度/掛載順序等）。"""


class MissingSignalError(ContractError):
    """契約依賴的訊號無人提供（startup 即 raise）。"""


@dataclass(frozen=True)
class SignalSpec:
    """單一訊號：名稱 + 型別 + 精度（float 小數位；int/bool/str 恆 0）。"""

    name: str
    dtype: str = "float"
    precision: int = 3

    def __post_init__(self) -> None:
        if not self.name:
            raise ContractError("SignalSpec.name must not be empty")
        if "." in self.name:
            raise ContractError(f"signal name must not contain '.': {self.name!r}")
        if self.dtype not in SIGNAL_DTYPES:
            raise ContractError(f"unknown signal dtype: {self.dtype!r}; expected {SIGNAL_DTYPES}")
        if self.precision < 0:
            raise ContractError(f"precision must be >= 0, got {self.precision}")
        if self.dtype in _INT_LIKE and self.precision != 0:
            raise ContractError(f"dtype {self.dtype!r} requires precision=0, got {self.precision}")

    def coerce(self, value: Any) -> Any:
        """型別檢查 + float 精度捨入；不合 raise ContractError。"""
        if self.dtype == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ContractError(f"signal {self.name!r} expects float, got {value!r}")
            return round(float(value), self.precision)
        if self.dtype == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ContractError(f"signal {self.name!r} expects int, got {value!r}")
            return int(value)
        if self.dtype == "bool":
            if not isinstance(value, bool):
                raise ContractError(f"signal {self.name!r} expects bool, got {value!r}")
            return bool(value)
        if not isinstance(value, str):
            raise ContractError(f"signal {self.name!r} expects str, got {value!r}")
        return str(value)


@dataclass(frozen=True)
class GroupContract:
    """群組輸出契約：provides（本組輸出）+ requires（外部依賴 ``group.signal``）。"""

    group: str
    provides: Tuple[SignalSpec, ...] = ()
    requires: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.group:
            raise ContractError("GroupContract.group must not be empty")
        names = [s.name for s in self.provides]
        if len(names) != len(set(names)):
            raise ContractError(f"duplicate provides in contract {self.group!r}: {sorted(names)}")
        for ref in self.requires:
            parts = ref.split(".")
            if len(parts) != 2 or not all(parts):
                raise ContractError(
                    f"requires must be 'group.signal', got {ref!r} (contract {self.group!r})"
                )

    def provide_names(self) -> Tuple[str, ...]:
        return tuple(s.name for s in self.provides)

    def spec_of(self, signal: str) -> SignalSpec:
        """取 provides 中的訊號規格；不存在 raise ContractError。"""
        for spec in self.provides:
            if spec.name == signal:
                return spec
        raise ContractError(f"contract {self.group!r} does not provide signal {signal!r}")
