# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M7 測試：熱群組 SoA+幀預算（計畫 §6.3 M7 驗收）。

驗收：基準 1k 實體 60 tick/s 帧預算內（avg/tick < 16.67ms，120 tick 實測）。
附：Entity↔SoA 往返（含 fsm 解碼）、缺軸零值、容量翻倍成長、域/未知軸/
型別響亮 raise、advance_xy 對 dict 手算一致。
"""

from __future__ import annotations

import time
from typing import Dict

import pytest
from engine import AxisGroup, AxisSpec, Entity, GroupContract, SignalSpec
from engine.packed import PackedGroup

FRAME_BUDGET_MS = 1000.0 / 60.0  # 60 tick/s → 16.67ms/tick
N_ENTITIES = 1000
BENCH_TICKS = 120  # 2 秒模擬


def make_space_group() -> AxisGroup:
    axes = {
        "x": AxisSpec("x", "continuous", lo=-1e9, hi=1e9, step=0.0),
        "y": AxisSpec("y", "continuous", lo=-1e9, hi=1e9, step=0.0),
        "vx": AxisSpec("vx", "continuous", step=0.0),
        "vy": AxisSpec("vy", "continuous", step=0.0),
        "facing": AxisSpec("facing", "fsm", states=("E", "N", "S", "W")),
    }
    contract = GroupContract(
        group="space",
        provides=tuple(
            SignalSpec(name, "float", 6) for name, spec in axes.items() if spec.kind != "fsm"
        )
        + (SignalSpec("facing", "str", 0),),
    )
    return AxisGroup(name="space", tick_rate=60.0, axes=axes, contract=contract)


def make_entities(n: int):
    dirs = ("E", "N", "S", "W")
    out = []
    for i in range(n):
        out.append(
            Entity(
                eid=i,
                groups={
                    "space": {
                        "x": float(i % 100),
                        "y": float(i // 100),
                        "vx": 1.5,
                        "vy": -0.5,
                        "facing": dirs[i % 4],
                    }
                },
            )
        )
    return out


class TestSoARoundtrip:
    def test_from_entities_roundtrip_including_fsm(self):
        group = make_space_group()
        ents = make_entities(4)
        packed = PackedGroup.from_entities(group, ents, capacity=4)
        assert packed.slots == 4
        for slot in range(4):
            got = packed.entity_at(slot)
            assert got.groups["space"] == ents[slot].groups["space"]  # fsm 解碼=字串

    def test_entities_without_group_skipped(self):
        group = make_space_group()
        outsider = Entity(eid=9, groups={"story": {"card_type": "角色卡"}})
        packed = PackedGroup.from_entities(group, [outsider])
        assert packed.slots == 0

    def test_missing_axis_defaults_zero(self):
        group = make_space_group()
        packed = PackedGroup(group)
        packed.add({"x": 1.0})  # 缺 y/vx/vy/facing → 零值
        assert packed.get(0, "x") == 1.0
        assert packed.get(0, "y") == 0.0
        assert packed.get(0, "facing") == "E"  # fsm 索引 0


class TestValidationLoud:
    def test_unknown_axis_raises(self):
        packed = PackedGroup(make_space_group())
        with pytest.raises(ValueError, match="no axis"):
            packed.add({"z": 1.0})
        with pytest.raises(ValueError, match="no axis"):
            packed.get(0, "z")

    def test_fsm_out_of_states_raises(self):
        packed = PackedGroup(make_space_group())
        with pytest.raises(ValueError, match="not in states"):
            packed.add({"facing": "UP"})
        packed.add({})
        with pytest.raises(ValueError, match="not in states"):
            packed.set(0, "facing", "sideways")

    def test_numeric_out_of_domain_raises(self):
        packed = PackedGroup(make_space_group())
        with pytest.raises(ValueError, match="outside domain"):
            packed.add({"x": -1e18})  # lo=-1e9

    def test_non_numeric_value_raises(self):
        packed = PackedGroup(make_space_group())
        with pytest.raises(ValueError, match="numeric"):
            packed.add({"x": "left"})

    def test_slot_out_of_range(self):
        packed = PackedGroup(make_space_group())
        with pytest.raises(IndexError, match="out of range"):
            packed.get(0, "x")
        packed.add({})
        with pytest.raises(IndexError, match="out of range"):
            packed.set(5, "x", 1.0)

    @pytest.mark.parametrize("cap", [0, -2])
    def test_invalid_capacity_raises(self, cap):
        with pytest.raises(ValueError, match="capacity"):
            PackedGroup(make_space_group(), capacity=cap)

    def test_advance_unknown_axis_raises(self):
        packed = PackedGroup(make_space_group())
        with pytest.raises(ValueError, match="no axis"):
            packed.advance_xy(0.01, x_axis="nope")


class TestDynamicsCorrectness:
    def test_advance_xy_matches_dict_math(self):
        group = make_space_group()
        ents = make_entities(50)
        packed = PackedGroup.from_entities(group, ents, capacity=64)
        dt, ticks = 1.0 / 60.0, 10
        for _ in range(ticks):
            packed.advance_xy(dt)

        # dict 手算同物理 → 容差比較（array('d') 與 float 同為 IEEE754 雙精度）
        for slot, ent in enumerate(ents):
            v = ent.groups["space"]
            expect_x = v["x"] + v["vx"] * dt * ticks  # 逐步累加 vs 閉式：同浮點序
            # 逐步模擬以完全同序累加
            x, y = v["x"], v["y"]
            for _ in range(ticks):
                x += v["vx"] * dt
                y += v["vy"] * dt
            assert packed.get(slot, "x") == pytest.approx(x, abs=1e-12)
            assert packed.get(slot, "y") == pytest.approx(y, abs=1e-12)
            assert expect_x == pytest.approx(x, abs=1e-6)
            assert packed.get(slot, "facing") == v["facing"]

    def test_capacity_grows_preserving_values(self):
        group = make_space_group()
        packed = PackedGroup(group, capacity=2)
        for i in range(100):
            packed.add({"x": float(i), "facing": "N"})
        assert packed.slots == 100
        assert packed.capacity >= 100
        assert packed.get(0, "x") == 0.0
        assert packed.get(99, "x") == 99.0
        assert packed.get(99, "facing") == "N"


class TestFrameBudgetAcceptance:
    def test_1k_entities_60hz_within_frame_budget(self):
        # M7 驗收：1k 實體 60 tick/s 幀預算內（SoA 熱路徑實測）
        group = make_space_group()
        packed = PackedGroup.from_entities(group, make_entities(N_ENTITIES))
        assert packed.slots == N_ENTITIES

        dt = 1.0 / 60.0
        start = time.perf_counter()
        for _ in range(BENCH_TICKS):
            packed.advance_xy(dt)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        avg_ms = elapsed_ms / BENCH_TICKS

        assert (
            avg_ms < FRAME_BUDGET_MS
        ), f"avg tick {avg_ms:.3f}ms exceeds 60Hz budget {FRAME_BUDGET_MS:.3f}ms"
        # 熱跑後仍有正確性（末幀位置已推進：vx=1.5, 120 ticks）
        last_x = packed.get(N_ENTITIES - 1, "x")
        base_x = float((N_ENTITIES - 1) % 100)
        assert last_x > base_x  # 在動、無 NaN

    def test_dict_baseline_reference_still_measures(self):
        # 對照組：dict 表示同場景也量一次（僅記錄路徑可用性，不設相對
        # 斷言以免 CI 抖動；預算絕對值已在上一測試鎖定）
        ents = make_entities(N_ENTITIES)
        dt, ticks = 1.0 / 60.0, 60
        start = time.perf_counter()
        for _ in range(ticks):
            for e in ents:
                v = e.groups["space"]
                v["x"] = v["x"] + v["vx"] * dt
                v["y"] = v["y"] + v["vy"] * dt
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        avg_ms = elapsed_ms / ticks
        assert avg_ms < FRAME_BUDGET_MS * 10  # 寬鬆防呆：非定時器/死迴圈
