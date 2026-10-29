# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M8 測試（§6.4「生產 tick 迴圈」遠期項落地驗收）。

- step() 確定性：fire 數 == pipeline ticks == handler 呼叫數（1:1:1）
- 子彈時間：time_scale 0.2× ＝ 少跑 fire（M3 語意經執行器）
- 執行緒：start/stop 冪等、牆鐘推進、stop 後凍結、啟動後禁註冊
- story 群組（M5 真檔 351 卡）心跳：首卡播種 → 訊號表可讀 → 重播自持
- 渲染橋外包（M4 契約）：push_states/sample、push_entities
- 訪問器：signal_snapshot() 副本語意、time_scale_of()
- world 線流速外包：time_flow_source + flow_id 覆寫 time_scale
"""

from __future__ import annotations

import time

import pytest
from engine import (
    AxisGroup,
    AxisSpec,
    ContractError,
    EngineRunner,
    Entity,
    EntityState,
    GroupContract,
    SignalSpec,
    content,
)


def make_space(tick_rate: float = 30.0) -> AxisGroup:
    return AxisGroup(
        name="space",
        tick_rate=tick_rate,
        axes={
            "pos_x": AxisSpec("pos_x", "continuous", lo=-1000.0, hi=1000.0),
            "pos_y": AxisSpec("pos_y", "continuous", lo=-1000.0, hi=1000.0),
        },
        contract=GroupContract(
            group="space",
            provides=(SignalSpec("pos_x"), SignalSpec("pos_y")),
        ),
    )


def make_combat(tick_rate: float = 60.0) -> AxisGroup:
    return AxisGroup(
        name="combat",
        tick_rate=tick_rate,
        axes={"hp": AxisSpec("hp", "discrete", lo=0.0, hi=999.0, step=1.0)},
        contract=GroupContract(
            group="combat",
            provides=(SignalSpec("target_hp", "int", 0),),
        ),
    )


class _Counter:
    def __init__(self):
        self.calls = 0

    def __call__(self, ctx) -> None:
        self.calls += 1


class TestStepDeterminism:
    """M8 核心：step 是確定性單 tick 推進。"""

    def test_fires_pipeline_and_handler_1to1(self):
        runner = EngineRunner(master_hz=60.0)
        counter = _Counter()
        runner.register(make_space(tick_rate=30.0), counter)
        runner.startup()
        due = runner.step()
        assert due == {"space": 0}
        runner.run(100)
        snap = runner.snapshot()
        assert snap["groups"]["space"]["fired"] == 50
        assert snap["pipeline_ticks"] == 50
        assert counter.calls == 50

    def test_step_before_startup_raises(self):
        runner = EngineRunner()
        runner.register(make_space(), lambda ctx: None)
        with pytest.raises(ContractError):
            runner.step()

    def test_register_after_start_raises(self):
        runner = EngineRunner()
        runner.register(make_space(), lambda ctx: None)
        runner.startup()
        runner.start()
        try:
            with pytest.raises(RuntimeError):
                runner.register(make_combat(), lambda ctx: None)
        finally:
            runner.stop()

    def test_run_batch_returns_fired(self):
        runner = EngineRunner(master_hz=60.0)
        runner.register(make_space(tick_rate=60.0), lambda ctx: None)
        runner.startup()
        fired = runner.run(60)
        assert fired == {"space": 60}


class TestBulletTime:
    """M3 子彈時間語意經執行器：time_scale 少跑 fire。"""

    def test_time_scale_0_2_reduces_fires(self):
        runner = EngineRunner(master_hz=60.0)
        runner.register(make_combat(tick_rate=60.0), lambda ctx: None)
        runner.startup()
        runner.run(300)
        assert runner.clock.fired("combat") == 300
        runner.clock.set_time_scale("combat", 0.2)
        runner.run(300)
        assert runner.clock.fired("combat") == 360  # +60 = 300×0.2
        assert runner.snapshot()["groups"]["combat"]["time_scale"] == 0.2

    def test_time_scale_zero_pauses_group(self):
        runner = EngineRunner(master_hz=60.0)
        runner.register(make_combat(tick_rate=60.0), lambda ctx: None)
        runner.startup()
        runner.clock.set_time_scale("combat", 0.0)
        runner.run(120)
        assert runner.clock.fired("combat") == 0


class TestWallClockThread:
    """start/stop：冪等、牆鐘推進、stop 凍結。"""

    def test_start_advances_and_stop_freezes(self):
        runner = EngineRunner(master_hz=120.0)
        runner.register(make_combat(tick_rate=120.0), lambda ctx: None)
        runner.startup()
        assert runner.running is False
        runner.start()
        try:
            deadline = time.monotonic() + 2.0
            while runner.snapshot()["master_ticks"] < 5 and time.monotonic() < deadline:
                time.sleep(0.01)
            snap = runner.snapshot()
            assert snap["running"] is True
            assert snap["master_ticks"] >= 5
        finally:
            runner.stop()
        frozen = runner.snapshot()["master_ticks"]
        assert runner.running is False
        time.sleep(0.05)
        assert runner.snapshot()["master_ticks"] == frozen

    def test_start_stop_idempotent(self):
        runner = EngineRunner(master_hz=120.0)
        runner.register(make_combat(tick_rate=120.0), lambda ctx: None)
        runner.startup()
        first = runner.start()
        thread = runner._thread
        second = runner.start()  # 冪等：不重建執行緒
        assert second["running"] is True
        assert runner._thread is thread
        runner.stop()
        third = runner.stop()  # 冪等：未在跑直接回快照
        assert third["running"] is False


class TestStoryHeartbeat:
    """M5 真檔內容經執行器：首卡播種 → 重播自持。"""

    def _seeded_runner(self) -> EngineRunner:
        cards = content.load_cards()
        seed = content.card_to_values(cards[0])
        runner = EngineRunner(master_hz=60.0)

        def handler(ctx) -> None:
            ct = ctx.read("story.card_type")
            role = ctx.read("story.story_role")
            ctx.emit("card_type", ct if isinstance(ct, str) else str(seed["card_type"]))
            ctx.emit("story_role", role if isinstance(role, str) else str(seed["story_role"]))

        runner.register(content.story_group(cards), handler)
        runner.startup()
        return runner

    def test_first_fire_seeds_then_republishes(self):
        runner = self._seeded_runner()
        cards = content.load_cards()
        seed = content.card_to_values(cards[0])
        runner.run(4)
        snap = runner.snapshot()
        assert snap["signals"]["story"]["card_type"] == seed["card_type"]
        assert snap["signals"]["story"]["story_role"] == seed["story_role"]
        runner.run(8)
        snap2 = runner.snapshot()
        assert snap2["signals"]["story"]["card_type"] == seed["card_type"]

    def test_story_group_axes_from_real_deck(self):
        group = content.story_group()
        assert set(group.axes) == {"card_type", "story_role"}
        assert len(group.axes["card_type"].states) == 20
        assert len(group.axes["story_role"].states) == 9


class TestRenderBridgePassthrough:
    """M4 契約經執行器外包。"""

    def test_push_states_and_sample(self):
        runner = EngineRunner()
        runner.push_states({"hero": EntityState(id="hero", x=5.0, y=5.0)}, sim_time=0.0)
        st = runner.sample(1.0)["hero"]
        assert (st.x, st.y) == (5.0, 5.0)

    def test_push_entities_uses_group_axes(self):
        runner = EngineRunner()
        ent = Entity(eid=3, groups={"space": {"pos_x": 4.0, "pos_y": -2.0}})
        runner.push_entities([ent], group="space", sim_time=0.0, x_key="pos_x", y_key="pos_y")
        st = runner.sample(1.0)["e3"]
        assert (st.x, st.y) == (4.0, -2.0)

    def test_sample_at_interpolates_between_pushes(self):
        runner = EngineRunner()
        runner.push_states({"m": EntityState(id="m", x=0.0, y=0.0)}, sim_time=0.0)
        runner.push_states({"m": EntityState(id="m", x=10.0, y=0.0)}, sim_time=1.0)
        st = runner.sample_at(0.5)["m"]
        assert st.x == pytest.approx(5.0)


class TestAccessorsAndFlowSource:
    """訪問器 + world 線流速外包。"""

    def test_signal_snapshot_is_copy(self):
        runner = self._seeded_minimal()
        runner.run(2)
        snap_copy = runner.pipeline.signal_snapshot()
        snap_copy["space"]["pos_x"] = 999.0
        assert runner.snapshot()["signals"]["space"]["pos_x"] != 999.0

    def test_time_scale_of(self):
        runner = self._seeded_minimal()
        assert runner.clock.time_scale_of("space") == 1.0
        runner.clock.set_time_scale("space", 0.5)
        assert runner.clock.time_scale_of("space") == 0.5
        assert runner.snapshot()["groups"]["space"]["dt"] == pytest.approx(1.0 / 30.0)

    def test_flow_source_overrides_time_scale(self):
        runner = EngineRunner(master_hz=60.0, time_flow_source=lambda fid: 0.5)
        runner.register(make_combat(tick_rate=60.0), lambda ctx: None, flow_id="wl1")
        runner.startup()
        assert runner.clock.time_scale_of("combat") == 0.5

    def _seeded_minimal(self) -> EngineRunner:
        runner = EngineRunner(master_hz=60.0)
        counter = _Counter()

        def handler(ctx) -> None:
            counter.calls += 1
            ctx.emit("pos_x", float(counter.calls))
            ctx.emit("pos_y", 0.0)

        runner.register(make_space(tick_rate=30.0), handler)
        runner.startup()
        return runner
