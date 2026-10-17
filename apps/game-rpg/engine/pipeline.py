# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — 管線（計畫 §6.2 M1：註冊驗證 + 組間訊號下一 tick 可見）。

最小 tick 模型（M3 再接中控時鐘/掛載率累積）：

- ``register_group``：契約建構時已驗，此處查重名與契約/群組一致。
- ``startup()``：解析全部 ``requires`` → 缺訊號 raise MissingSignalError。
- ``tick()``：依註冊序跑各組 handler；handler 內 emit 寫入 **pending**、
  read 讀 **上一 tick 結束後**的快照——同 tick 內不可見、下一 tick 可見。
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from engine.axes import AxisGroup
from engine.contracts import ContractError, GroupContract, MissingSignalError, SignalSpec

Handler = Callable[["TickContext"], None]


class TickContext:
    """單群組單次 tick 的進出介面（emit 要求契約提供；read 語法 ``group.signal``）。"""

    def __init__(self, pipeline: "EnginePipeline", group: str) -> None:
        self._pipeline = pipeline
        self.group = group

    def emit(self, signal: str, value: Any) -> None:
        """寫入本組輸出（本 tick 內不可讀，下一 tick 生效）。"""
        self._pipeline._emit(self.group, signal, value)

    def read(self, ref: str, default: Any = None) -> Any:
        """讀跨組/本組訊號（上一 tick 快照）；未設定回 default。"""
        return self._pipeline._read(ref, default)


class EnginePipeline:
    """註冊群組、啟動驗證、逐 tick 推進的最小管線。"""

    def __init__(self) -> None:
        self._groups: Dict[str, AxisGroup] = {}
        self._handlers: Dict[str, Handler] = {}
        self._specs: Dict[str, Dict[str, SignalSpec]] = {}
        self._current: Dict[str, Dict[str, Any]] = {}
        self._pending: Dict[str, Dict[str, Any]] = {}
        self._started = False
        self.ticks = 0

    # ------------------------------------------------------------------
    # 註冊 / 啟動
    # ------------------------------------------------------------------
    def register_group(self, group: AxisGroup, handler: Handler) -> None:
        """註冊群組（register 時驗證：重名/契約一致已在資料類別與此處齊備）。"""
        if self._started:
            raise ContractError("cannot register_group after startup()")
        if group.name in self._groups:
            raise ContractError(f"group {group.name!r} already registered")
        contract: GroupContract = group.contract
        if contract.group != group.name:
            raise ContractError(f"contract {contract.group!r} mismatch group {group.name!r}")
        self._groups[group.name] = group
        self._handlers[group.name] = handler
        self._specs[group.name] = {s.name: s for s in contract.provides}

    def startup(self) -> None:
        """解析全部契約依賴——缺訊號/未註冊群組 raise MissingSignalError。"""
        if self._started:
            return
        for name, contract in ((g.name, g.contract) for g in self._groups.values()):
            for ref in contract.requires:
                self._resolve(ref, contract_owner=name)
        self._started = True

    @property
    def started(self) -> bool:
        return self._started

    def group_names(self) -> List[str]:
        return list(self._groups)

    def contract_of(self, name: str) -> GroupContract:
        if name not in self._groups:
            raise ContractError(f"unknown group: {name!r}")
        return self._groups[name].contract

    # ------------------------------------------------------------------
    # Tick
    # ------------------------------------------------------------------
    def tick(self) -> None:
        """跑一輪全部 handler，再把 pending 併入快照（訊號下 tick 可見）。"""
        if not self._started:
            raise ContractError("pipeline not started; call startup() first")
        for name in list(self._groups):
            self._handlers[name](TickContext(self, name))
        for gname, values in self._pending.items():
            self._current.setdefault(gname, {}).update(values)
        self._pending.clear()
        self.ticks += 1

    def tick_group(self, name: str) -> None:
        """跑單組一次 fire 並併入該組 pending（M8 執行器：各組 tick_rate 不同步 fire）。"""
        if not self._started:
            raise ContractError("pipeline not started; call startup() first")
        if name not in self._groups:
            raise ContractError(f"unknown group: {name!r}")
        self._handlers[name](TickContext(self, name))
        values = self._pending.pop(name, None)
        if values:
            self._current.setdefault(name, {}).update(values)
        self.ticks += 1

    def signal(self, ref: str, default: Any = None) -> Any:
        """tick 外讀訊號快照（與 TickContext.read 同語意）。"""
        return self._read(ref, default)

    def signal_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """全組訊號表唯讀副本（M8 執行器 snapshot 用；執行緒安全由呼叫端鎖定）。"""
        return {gname: dict(values) for gname, values in self._current.items()}

    # ------------------------------------------------------------------
    # 內部
    # ------------------------------------------------------------------
    def _resolve(self, ref: str, contract_owner: str) -> SignalSpec:
        gname, sig = ref.split(".")
        if gname not in self._groups:
            raise MissingSignalError(
                f"contract {contract_owner!r} requires {ref!r}: group {gname!r} not registered"
            )
        spec = self._specs[gname].get(sig)
        if spec is None:
            raise MissingSignalError(
                f"contract {contract_owner!r} requires {ref!r}: "
                f"group {gname!r} does not provide signal {sig!r} "
                f"(provides {sorted(self._specs[gname])})"
            )
        return spec

    def _emit(self, group: str, signal: str, value: Any) -> None:
        if not self._started:
            raise ContractError("cannot emit before startup()")
        if group not in self._groups:
            raise ContractError(f"unknown group: {group!r}")
        specs = self._specs[group]
        if signal not in specs:
            raise ContractError(
                f"contract {group!r} does not provide signal {signal!r} "
                f"(provides {sorted(specs)})"
            )
        self._pending.setdefault(group, {})[signal] = specs[signal].coerce(value)

    def _read(self, ref: str, default: Any) -> Any:
        if ref.count(".") != 1:
            raise ContractError(f"signal ref must be 'group.signal', got {ref!r}")
        gname, sig = ref.split(".")
        return self._current.get(gname, {}).get(sig, default)
