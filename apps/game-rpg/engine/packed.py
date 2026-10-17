# -*- coding: utf-8 -*-
"""萬物皆軸引擎 — M7 熱群組連續記憶體（SoA；§6.3 M7）。

剖析結論的落地形態：空間/表現等熱群組把「每實體一 dict」換成
**每軸一個 ``array('d')``（連續記憶體）**，fsm 軸存狀態索引
（``array('i')`` + 狀態表解碼），冷路徑仍用 M1 Entity dict（未觸群組
零成本）。stdlib 零新依賴（numpy 為後備選項，本批 array 已達幀預算）。

``advance_xy`` 是空間組基準路徑：緊迴圈 x+=vx*dt、y+=vy*dt（1k 實體
預算驗證見 tests/engine/test_m7_perf.py）。
"""

from __future__ import annotations

from array import array
from typing import Dict, Iterable, Mapping, Tuple, Union

from engine.axes import AxisGroup, AxisSpec, Entity, Value

_FSM_KIND = "fsm"


def _zero_array(kind: str, n: int) -> array:
    if kind == _FSM_KIND:
        return array("i", [0]) * n
    return array("d", [0.0]) * n


class PackedGroup:
    """單一群組的 SoA 儲存：軸→array；slot 即實體列（capacity 翻倍成長）。"""

    def __init__(self, group: AxisGroup, capacity: int = 8) -> None:
        if capacity < 1:
            raise ValueError(f"capacity must be >= 1, got {capacity}")
        self.group = group
        self.capacity = capacity
        self.slots = 0
        self._arrays: Dict[str, array] = {}
        self._fsm_states: Dict[str, Tuple[str, ...]] = {}
        self._fsm_index: Dict[str, Dict[str, int]] = {}
        for name, spec in group.axes.items():
            if spec.kind == _FSM_KIND:
                self._arrays[name] = _zero_array(_FSM_KIND, capacity)
                self._fsm_states[name] = spec.states
                self._fsm_index[name] = {s: i for i, s in enumerate(spec.states)}
            else:
                self._arrays[name] = _zero_array("d", capacity)

    # ------------------------------------------------------------------
    # 值編解碼（fsm: str⇄索引；數值: float）+ 域驗證（響亮 raise）
    # ------------------------------------------------------------------
    def _encode(self, axis: str, spec: AxisSpec, value: Value) -> Union[int, float]:
        if spec.kind == _FSM_KIND:
            if not isinstance(value, str) or value not in self._fsm_index[axis]:
                raise ValueError(f"axis {axis!r}: value {value!r} not in states {spec.states}")
            return self._fsm_index[axis][value]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"axis {axis!r} (numeric): got {value!r}")
        v = float(value)
        if not spec.contains(v):
            raise ValueError(f"axis {axis!r}: value {v} outside domain")
        return v

    def _decode(self, axis: str, spec: AxisSpec, encoded) -> Value:
        if spec.kind == _FSM_KIND:
            return self._fsm_states[axis][int(encoded)]
        return float(encoded)

    # ------------------------------------------------------------------
    # 存取
    # ------------------------------------------------------------------
    def _ensure(self, n: int) -> None:
        if n <= self.capacity:
            return
        new_cap = self.capacity
        while new_cap < n:
            new_cap *= 2
        for name, spec in self.group.axes.items():
            deficit = new_cap - self.capacity
            self._arrays[name].extend(_zero_array(spec.kind, deficit)[0:deficit])
        self.capacity = new_cap

    def add(self, values: Mapping[str, Value]) -> int:
        """追加實體（缺軸→該軸型別零值；未知軸 ValueError）。"""
        self._ensure(self.slots + 1)
        for axis in values:
            if axis not in self.group.axes:
                raise ValueError(f"group {self.group.name!r} has no axis {axis!r}")
        slot = self.slots
        for name, spec in self.group.axes.items():
            if name in values:
                enc = self._encode(name, spec, values[name])
            else:
                enc = 0 if spec.kind == _FSM_KIND else 0.0
            self._arrays[name][slot] = enc
        self.slots += 1
        return slot

    def get(self, slot: int, axis: str) -> Value:
        spec = self.group.axes.get(axis)
        if spec is None:
            raise ValueError(f"group {self.group.name!r} has no axis {axis!r}")
        if not 0 <= slot < self.slots:
            raise IndexError(f"slot {slot} out of range 0..{self.slots}")
        return self._decode(axis, spec, self._arrays[axis][slot])

    def set(self, slot: int, axis: str, value: Value) -> None:
        spec = self.group.axes.get(axis)
        if spec is None:
            raise ValueError(f"group {self.group.name!r} has no axis {axis!r}")
        if not 0 <= slot < self.slots:
            raise IndexError(f"slot {slot} out of range 0..{self.slots}")
        self._arrays[axis][slot] = self._encode(axis, spec, value)

    # ------------------------------------------------------------------
    # 熱路徑（空間組基準）
    # ------------------------------------------------------------------
    def advance_xy(
        self,
        dt: float,
        x_axis: str = "x",
        y_axis: str = "y",
        vx_axis: str = "vx",
        vy_axis: str = "vy",
    ) -> None:
        """緊迴圈積分：x += vx*dt、y += vy*dt（1k 實體幀預算熱群組路徑）。"""
        for name in (x_axis, y_axis, vx_axis, vy_axis):
            if name not in self._arrays:
                raise ValueError(f"group {self.group.name!r} has no axis {name!r}")
        xs, ys = self._arrays[x_axis], self._arrays[y_axis]
        vxs, vys = self._arrays[vx_axis], self._arrays[vy_axis]
        n = self.slots
        for i in range(n):
            xs[i] = xs[i] + vxs[i] * dt
            ys[i] = ys[i] + vys[i] * dt

    # ------------------------------------------------------------------
    # 與 M1 Entity 互轉
    # ------------------------------------------------------------------
    @classmethod
    def from_entities(
        cls, group: AxisGroup, entities: Iterable[Entity], capacity: int = 8
    ) -> "PackedGroup":
        """Entity 列表 → SoA（不在本群組的 Entity 跳過；缺軸=零值）。"""
        ents = [e for e in entities if group.name in e.groups]
        packed = cls(group, capacity=max(capacity, len(ents), 1))
        for ent in ents:
            packed.add(ent.groups[group.name])
        return packed

    def entity_at(self, slot: int) -> Entity:
        """slot → M1 Entity（fsm 解碼回狀態字串；gid 用 slot 內聯號）。"""
        values: Dict[str, Value] = {}
        for name, spec in self.group.axes.items():
            values[name] = self._decode(name, spec, self._arrays[name][slot])
        return Entity(eid=slot, groups={self.group.name: values})
