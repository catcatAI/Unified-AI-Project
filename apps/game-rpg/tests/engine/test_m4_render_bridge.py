# -*- coding: utf-8 -*-
"""萬物皆軸引擎 M4 測試：快照+時間插值+像素吸附（計畫 §6.3 M4 驗收）。

驗收：30Hz 模擬 / 144Hz 顯示中間幀為線性 lerp。附：像素吸附（半遠離零、
pixel_size=0 連續）、狀態分離（push 複製）、spawn/移除語義、sim_time 倒退
raise、M1 Entity 橋接。
"""

from __future__ import annotations

import pytest
from engine import Entity, EntityState, RenderBridge, RenderState

SIM_HZ = 30.0
DISPLAY_HZ = 144.0
VELOCITY = 720.0  # px/s：30Hz 每模擬幀 24px、144Hz 每顯示幀 5px（皆落整數格）


def make_bridge(pixel_size: float = 1.0) -> RenderBridge:
    return RenderBridge(pixel_size=pixel_size)


class TestLerpAcceptance:
    def test_30hz_sim_144hz_display_linear(self):
        # M4 驗收：30Hz 模擬 / 144Hz 顯示中間幀為線性 lerp
        bridge = make_bridge()

        def sim_frame(k: int):
            t = k / SIM_HZ
            return {"e": EntityState("e", VELOCITY * t, VELOCITY * t)}, t

        xs, ys = [], []
        k = -1
        for m in range(25):  # 顯示幀 t=m/144 ∈ [0, 5/30]
            t = m / DISPLAY_HZ
            # 橋只存前後兩幀：逐顯示幀推進模擬至 curr_time >= t
            while k < 0 or bridge.curr_time < t:
                k += 1
                states, sim_t = sim_frame(k)
                bridge.push(states, sim_time=sim_t)
            st = bridge.sample_at(t)["e"]
            xs.append(st.x)
            ys.append(st.y)

        # 中間幀線性：每顯示幀 +5px（720/144），等步進、無跳變、吸附後精確
        expected = [5.0 * m for m in range(25)]
        assert xs == expected
        assert ys == expected
        diffs = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
        assert diffs == [5.0] * len(diffs)  # 嚴格等速
        assert xs[0] == 0.0 and xs[-1] == 120.0

    def test_endpoints_exact(self):
        bridge = make_bridge()
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=0.0)
        bridge.push({"e": EntityState("e", 10.0, 20.0)}, sim_time=1.0)
        assert bridge.sample_at(0.0)["e"] == RenderState("e", 0.0, 0.0)
        assert bridge.sample_at(1.0)["e"] == RenderState("e", 10.0, 20.0)
        mid = bridge.sample_at(0.5)["e"]
        assert (mid.x, mid.y) == (5.0, 10.0)

    def test_sample_alpha_between_two_frames(self):
        bridge = make_bridge()
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=0.0)
        bridge.push({"e": EntityState("e", 8.0, 4.0)}, sim_time=1.0)
        assert bridge.sample(0.25)["e"].x == 2.0
        assert bridge.sample(0.75)["e"].y == 3.0

    def test_alpha_clamped(self):
        bridge = make_bridge()
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=0.0)
        bridge.push({"e": EntityState("e", 10.0, 10.0)}, sim_time=1.0)
        assert bridge.sample(9.9)["e"].x == 10.0
        assert bridge.sample(-1.0)["e"].x == 0.0

    def test_first_push_renders_at_curr(self):
        bridge = make_bridge()
        bridge.push({"e": EntityState("e", 7.0, 9.0)}, sim_time=0.0)
        assert bridge.sample(0.5)["e"] == RenderState("e", 7.0, 9.0)

    def test_removed_entity_not_rendered(self):
        bridge = make_bridge()
        bridge.push({"a": EntityState("a", 1.0, 1.0)}, sim_time=0.0)
        bridge.push({"b": EntityState("b", 2.0, 2.0)}, sim_time=1.0)
        out = bridge.sample(0.5)
        assert "a" not in out
        assert "b" in out

    def test_sample_empty_bridge(self):
        assert make_bridge().sample(0.5) == {}
        assert make_bridge().sample_at(1.0) == {}


class TestPixelSnap:
    def test_half_away_tie_on_lerp_result(self):
        bridge = make_bridge(pixel_size=1.0)
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=0.0)
        bridge.push({"e": EntityState("e", 10.0, -10.0)}, sim_time=1.0)
        # alpha=0.25 → raw ±2.5 → 半遠離零：+3 / -3
        assert bridge.sample(0.25)["e"].x == 3.0
        assert bridge.sample(0.25)["e"].y == -3.0

    def test_pixel_size_zero_is_continuous(self):
        bridge = make_bridge(pixel_size=0.0)
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=0.0)
        bridge.push({"e": EntityState("e", 10.0, 0.0)}, sim_time=1.0)
        assert bridge.sample(0.333)["e"].x == pytest.approx(3.33, abs=1e-9)

    def test_half_pixel_grid(self):
        bridge = make_bridge(pixel_size=0.5)
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=0.0)
        bridge.push({"e": EntityState("e", 7.3, 0.0)}, sim_time=1.0)
        assert bridge.sample(1.0)["e"].x == 7.5

    @pytest.mark.parametrize("ps", [-0.5, -1.0])
    def test_negative_pixel_size_raises(self, ps):
        with pytest.raises(ValueError):
            make_bridge(pixel_size=ps)


class TestSnapshotSemantics:
    def test_push_copies_state(self):
        bridge = make_bridge()
        src = {"e": EntityState("e", 1.0, 2.0)}
        bridge.push(src, sim_time=0.0)
        src.pop("e")  # 呼叫端改字典不影響已推快照
        bridge.push({"e": EntityState("e", 5.0, 6.0)}, sim_time=1.0)
        assert bridge.prev["e"] == EntityState("e", 1.0, 2.0)

    def test_entities_frozen_after_push(self):
        from dataclasses import FrozenInstanceError

        bridge = make_bridge()
        bridge.push({"e": EntityState("e", 1.0, 2.0)}, sim_time=0.0)
        with pytest.raises(FrozenInstanceError):
            bridge.curr["e"].x = 99.0  # 第一幀在 curr（prev 是推前的空幀）

    def test_sim_time_must_not_decrease(self):
        bridge = make_bridge()
        bridge.push({"e": EntityState("e")}, sim_time=5.0)
        with pytest.raises(ValueError, match="non-decreasing"):
            bridge.push({"e": EntityState("e")}, sim_time=4.0)

    def test_equal_sim_time_latest_frame_wins(self):
        bridge = make_bridge()
        bridge.push({"e": EntityState("e", 0.0, 0.0)}, sim_time=1.0)
        bridge.push({"e": EntityState("e", 10.0, 0.0)}, sim_time=1.0)
        assert bridge.sample_at(1.0)["e"].x == 10.0  # delta=0 → alpha=1 走 curr
        assert bridge.sample(0.0)["e"].x == 0.0  # 明確 alpha=0 仍走 prev

    def test_push_entities_from_m1_entity(self):
        bridge = make_bridge()
        ent = Entity(eid=3, groups={"space": {"x": 4.0, "y": -2.0}})
        bridge.push_entities([ent], group="space", sim_time=0.0)
        st = bridge.sample(1.0)["e3"]
        assert (st.x, st.y) == (4.0, -2.0)

    def test_push_entities_non_numeric_axes_default_zero(self):
        bridge = make_bridge()
        ent = Entity(eid=1, groups={"story": {"x": "go", "y": True}})
        bridge.push_entities([ent], group="story", sim_time=0.0)
        st = bridge.sample(1.0)["e1"]
        assert (st.x, st.y) == (0.0, 0.0)

    def test_push_entities_missing_group_defaults_zero(self):
        bridge = make_bridge()
        bridge.push_entities([Entity(eid=9)], group="space", sim_time=0.0)
        assert bridge.sample(1.0)["e9"] == RenderState("e9", 0.0, 0.0)
