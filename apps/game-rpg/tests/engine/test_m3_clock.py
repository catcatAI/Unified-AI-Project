# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M3 測試：中控時鐘/子彈時間（計畫 §6.3 M3 驗收）。

驗收：戰鬥組 0.2× 時心理組 UI 不受影響（用 tick 計數驗證）。
附：time_scale=0 暫停、group_dt 分發、world_lines 流速比外包（fake source）、
執行期覆寫。
"""

from __future__ import annotations

import pytest
from engine import AxisGroup, AxisSpec, GroupContract, MasterClock, SignalSpec


def make_group(name: str, tick_rate: float, time_scale: float = 1.0) -> AxisGroup:
    return AxisGroup(
        name=name,
        tick_rate=tick_rate,
        time_scale=time_scale,
        axes={"v": AxisSpec("v", "continuous", step=0.0)},
        contract=GroupContract(group=name, provides=(SignalSpec("v", "float", 3),)),
    )


class TestMasterClockBasics:
    @pytest.mark.parametrize("hz", [0.0, -60.0])
    def test_invalid_master_hz_raises(self, hz):
        with pytest.raises(ValueError):
            MasterClock(master_hz=hz)

    def test_duplicate_register_raises(self):
        clock = MasterClock()
        clock.register_group(make_group("combat", 60.0))
        with pytest.raises(ValueError, match="already registered"):
            clock.register_group(make_group("combat", 60.0))

    def test_unknown_group_access_raises(self):
        clock = MasterClock()
        with pytest.raises(KeyError):
            clock.group_dt("nope")

    def test_master_ticks_increment(self):
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("space", 60.0))
        clock.run(10)
        assert clock.master_ticks == 10


class TestFiringRates:
    def test_one_to_one_at_equal_rate(self):
        # 60Hz 組掛 60Hz master：每 master tick fire 一次
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("space", 60.0))
        due = clock.run(60)
        assert due["space"] == 60

    def test_half_rate_group_fires_every_other_tick(self):
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("ui", 30.0))
        assert clock.run(60)["ui"] == 30

    def test_group_dt_is_period(self):
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("combat", 60.0))
        clock.register_group(make_group("ui", 30.0))
        assert clock.group_dt("combat") == pytest.approx(1 / 60)
        assert clock.group_dt("ui") == pytest.approx(1 / 30)


class TestBulletTime:
    def test_combat_02x_leaves_mind_unaffected(self):
        # M3 驗收：戰鬥組 0.2× 時心理組不受影響（tick 計數）
        def build(combat_scale):
            clock = MasterClock(master_hz=60.0)
            clock.register_group(make_group("combat", 60.0, combat_scale))
            clock.register_group(make_group("mind", 30.0, 1.0))
            return clock

        slowed = build(0.2)
        normal = build(1.0)
        slowed.run(600)
        normal.run(600)

        # 心理組兩邊完全一樣（不受戰鬥組子彈時間影響）
        assert slowed.fired("mind") == normal.fired("mind") == 300
        # 戰鬥組 0.2× ≈ 120 vs 600（±2 浮點容差）
        assert slowed.fired("combat") == pytest.approx(120, abs=2)
        assert normal.fired("combat") == pytest.approx(600, abs=1)
        assert slowed.fired("combat") < normal.fired("combat")

    def test_zero_time_scale_pauses_group(self):
        # 暫停 = 執行期覆寫（AxisGroup 建構期仍強制 time_scale>0，M1 契約）
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("combat", 60.0))
        clock.set_time_scale("combat", 0.0)
        assert clock.run(120)["combat"] == 0
        assert clock.fired("combat") == 0

    def test_runtime_set_time_scale_override(self):
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("combat", 60.0))
        clock.run(60)
        assert clock.fired("combat") == 60
        clock.set_time_scale("combat", 0.5)
        clock.run(60)
        assert clock.fired("combat") == pytest.approx(90, abs=1)  # 後 60 期只跑一半
        clock.set_time_scale("combat", 0.0)
        clock.run(60)
        assert clock.fired("combat") == pytest.approx(90, abs=1)  # 暫停不再增加

    def test_negative_set_time_scale_raises(self):
        clock = MasterClock()
        clock.register_group(make_group("combat", 60.0))
        with pytest.raises(ValueError):
            clock.set_time_scale("combat", -0.1)

    def test_run_negative_raises(self):
        clock = MasterClock()
        with pytest.raises(ValueError):
            clock.run(-1)


class TestWorldLineFlowSource:
    """§6.4 外包 world_clock 的 world_lines 索引（以 fake source 驗機制）。"""

    def test_flow_id_ratio_overrides_time_scale(self):
        flows = {"W01-A": 0.5, "W01-B": None}
        clock = MasterClock(master_hz=60.0, time_flow_source=flows.get)
        clock.register_group(make_group("a", 60.0, 1.0), flow_id="W01-A")
        clock.register_group(make_group("b", 60.0, 1.0), flow_id="W01-B")
        clock.register_group(make_group("c", 60.0, 1.0))  # 未掛 flow
        clock.run(60)
        assert clock.fired("a") == pytest.approx(30, abs=1)  # 0.5× 流速
        assert clock.fired("b") == 60  # None → 回群組建構值 1.0
        assert clock.fired("c") == 60

    def test_negative_ratio_raises_at_register(self):
        clock = MasterClock(master_hz=60.0, time_flow_source=lambda _wid: -1.0)
        with pytest.raises(ValueError, match="time flow ratio"):
            clock.register_group(make_group("a", 60.0), flow_id="W01")

    def test_no_source_keeps_group_time_scale(self):
        clock = MasterClock(master_hz=60.0)
        clock.register_group(make_group("a", 60.0, 0.2), flow_id="W01-A")
        clock.run(60)
        assert clock.fired("a") == pytest.approx(12, abs=1)
