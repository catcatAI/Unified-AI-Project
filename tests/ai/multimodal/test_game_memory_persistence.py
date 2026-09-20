"""記憶持久化與好奇探索測試。

涵蓋 R71 遊戲輪新增的三個閉環：
1. observe_world: scan/vision 觀察 → 空間記憶
2. save/load: 空間記憶跨重啟持久化
3. find_unexplored: 好奇心選點（年齡加權、危險排除、距離上限）
"""

import time
from unittest.mock import MagicMock

import pytest

from ai.multimodal.game_memory_bridge import GameMemoryBridge
from ai.multimodal.game_structs import GameState, Proprioception


# ==================== observe_world ====================


class TestObserveWorld:
    def test_creates_spatial_entries(self):
        b = GameMemoryBridge()
        n = b.observe_world(
            (0, 5, 0),
            [
                {"node": "default:tree", "x": 3, "y": 5, "z": 2},
                {"node": "default:stone", "x": -2, "y": 5, "z": 7},
            ],
            source="scan",
        )
        assert n == 2
        stats = b.spatial_stats()
        assert stats["total"] == 2
        assert stats["by_type"]["resource"] == 2

    def test_air_ignored_and_dedup_counts(self):
        b = GameMemoryBridge()
        n1 = b.observe_world(
            (0, 5, 0),
            [{"node": "air", "x": 1, "y": 5, "z": 1}, {"node": "default:tree", "x": 2, "y": 5, "z": 1}],
        )
        n2 = b.observe_world(
            (0, 5, 0), [{"node": "default:tree", "x": 2, "y": 5, "z": 1}], source="vision"
        )
        assert n1 == 1
        assert n2 == 0  # 同一位置不重複計新點
        loc = b._spatial_index["2_5_1"]
        assert loc.resources["tree"] == 2
        assert "vision" in loc.notes and "scan" in loc.notes

    def test_vision_rays_carry_world_coords(self):
        # poller 的 vision 射線命中時帶 x/y/z（pointed.under）
        b = GameMemoryBridge()
        b.observe_world(
            (10, 6, 10),
            [{"node": "default:tree", "x": 12, "y": 7, "z": 10, "dist": 2.5, "yaw_off": 0}],
            source="vision",
        )
        assert "12_7_10" in b._spatial_index

    def test_no_nodes_no_crash(self):
        b = GameMemoryBridge()
        assert b.observe_world((0, 0, 0), []) == 0
        assert b.observe_world((0, 0, 0), [{"node": "", "x": 1, "y": 1, "z": 1}]) == 0


# ==================== 持久化 ====================


class TestPersistence:
    def test_save_load_roundtrip(self, tmp_path):
        path = str(tmp_path / "spatial.json")
        b1 = GameMemoryBridge()
        b1.observe_world(
            (0, 5, 0),
            [
                {"node": "default:tree", "x": 3, "y": 5, "z": 2},
                {"node": "default:stone", "x": -2, "y": 5, "z": 7},
            ],
        )
        b1.mark_base((0, 5, 0))
        b1.mark_danger((3, 5, 2), level=0.7)
        assert b1.save_spatial(path)

        b2 = GameMemoryBridge()
        loaded = b2.load_spatial(path)
        assert loaded == 3
        assert b2._spatial_index["3_5_2"].danger_level == pytest.approx(0.7)
        assert b2._spatial_index["3_5_2"].resources["tree"] == 1
        assert b2._spatial_index["0_5_0"].node_type == "base"
        assert b2.spatial_stats()["total"] == 3

    def test_load_missing_file_returns_zero(self, tmp_path):
        b = GameMemoryBridge()
        assert b.load_spatial(str(tmp_path / "nope.json")) == 0

    def test_save_corrupt_dir_not_crash(self):
        b = GameMemoryBridge()
        assert b.save_spatial("/proc/nonexistent_dir/x.json") is False


# ==================== 好奇心選點 ====================


class TestFindUnexplored:
    def test_fresh_spots_excluded(self):
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 5, "y": 0, "z": 0}])
        # 剛寫入，年齡 < min_age_sec
        assert b.find_unexplored((0, 0, 0)) is None

    def test_stale_spot_selected(self):
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 5, "y": 0, "z": 0}])
        b._spatial_index["5_0_0"].last_visited = time.time() - 3600
        spot = b.find_unexplored((0, 0, 0))
        assert spot is not None
        assert spot.location_id == "5_0_0"

    def test_danger_excluded(self):
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 5, "y": 0, "z": 0}])
        node = b._spatial_index["5_0_0"]
        node.last_visited = time.time() - 3600
        node.danger_level = 1.0
        assert b.find_unexplored((0, 0, 0)) is None

    def test_distance_cap(self):
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 500, "y": 0, "z": 0}])
        b._spatial_index["500_0_0"].last_visited = time.time() - 3600
        assert b.find_unexplored((0, 0, 0), max_dist=80) is None
        assert b.find_unexplored((0, 0, 0), max_dist=600) is not None


# ==================== Agent 接線（輕量，不起 LLM/bridge） ====================


class TestAgentWiring:
    def _agent(self):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent, AngelaConfig

        agent = AngelaAutonomousAgent(AngelaConfig())
        agent.memory = GameMemoryBridge()
        agent.current_state = GameState(
            tick=0,
            timestamp=time.time(),
            proprioception=Proprioception(
                position=(0.0, 5.0, 0.0),
                yaw=0.0,
                pitch=0.0,
                health=20,
                max_health=20,
                hunger=20,
                breath=10,
                inventory={},
                wielded_item="",
                is_on_ground=True,
                is_in_water=False,
                is_in_lava=False,
            ),
        )
        agent.current_state.proprioception.max_hunger = 20
        return agent

    def test_curiosity_starts_goto_to_stale_spot(self):
        agent = self._agent()
        agent.memory.observe_world(
            (0, 5, 0), [{"node": "default:tree", "x": 12, "y": 5, "z": 4}]
        )
        agent.memory._spatial_index["12_5_4"].last_visited = time.time() - 3600
        agent._maybe_start_curiosity_exploration()
        assert agent._active_behavior is not None
        assert agent._active_behavior["id"] == "goto"
        assert agent._active_behavior["params"]["pos"] == {"x": 12.0, "y": 5.0, "z": 4.0}
        assert agent._active_behavior["reason"] == "curiosity:stale-spot"

    def test_curiosity_noop_when_no_stale(self):
        agent = self._agent()
        agent._maybe_start_curiosity_exploration()
        assert agent._active_behavior is None

    def test_screen_vision_degrades_silently(self):
        # 無顯示環境：capture/locate 失敗不應拋出，visual 保持 None
        agent = self._agent()
        agent._screen_vision = None  # 模擬初始化失敗
        agent._capture_screen_vision()
        assert agent.current_state.visual is None

    def test_observation_memory_skips_empty(self):
        import asyncio

        agent = self._agent()
        agent._last_scan = {"nodes": [{"node": "air", "x": 1, "y": 1, "z": 1}]}
        agent._last_vision = None
        asyncio.run(agent._store_observation_memory())  # 全空氣 → 不產生記憶
        assert len(agent.memory._experiences) == 0

    def test_observation_memory_records_seen(self):
        import asyncio

        agent = self._agent()
        agent.tick_count = 5
        agent._last_scan = {"nodes": [{"node": "default:tree", "x": 3, "y": 5, "z": 2}]}
        agent._last_vision = None
        asyncio.run(agent._store_observation_memory())
        assert len(agent.memory._experiences) == 1
        exp = agent.memory._experiences[0]
        assert exp.action == "observe"
        assert "default:tree" in exp.context["seen_nodes"]


# ==================== 審查修復回歸（R71b） ====================


class TestSeenVsVisitedSemantics:
    """看過（last_seen）≠ 親訪（last_visited）——好奇心語意核心。"""

    def test_observe_only_touches_last_seen(self):
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 5, "y": 0, "z": 0}])
        spot = b._spatial_index["5_0_0"]
        assert spot.last_seen > 0
        assert spot.last_visited == 0.0  # 看到不等於去過
        assert spot.visit_count == 0

    def test_never_visited_fresh_spot_not_selected(self):
        # 回歸：剛看到的點（last_visited=0）不該被誤選為「很久沒訪」
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 5, "y": 0, "z": 0}])
        assert b.find_unexplored((0, 0, 0)) is None

    def test_seen_long_ago_never_visited_selected(self):
        # 看過很久但從沒去過 → 最值得探索
        b = GameMemoryBridge()
        b.observe_world((0, 0, 0), [{"node": "default:tree", "x": 5, "y": 0, "z": 0}])
        b._spatial_index["5_0_0"].last_seen = time.time() - 3600
        spot = b.find_unexplored((0, 0, 0))
        assert spot is not None and spot.location_id == "5_0_0"

    def test_mark_visited_updates_only_nearby(self):
        b = GameMemoryBridge()
        b.observe_world(
            (0, 0, 0),
            [
                {"node": "default:tree", "x": 2, "y": 0, "z": 0},
                {"node": "default:stone", "x": 50, "y": 0, "z": 0},
            ],
        )
        n = b.mark_visited((0, 0, 0), radius=3.0)
        assert n == 1
        near = b._spatial_index["2_0_0"]
        far = b._spatial_index["50_0_0"]
        assert near.visit_count == 1 and near.last_visited > 0
        assert far.visit_count == 0 and far.last_visited == 0.0


class TestMemoryBounds:
    """記憶體護欄（計畫風險表「記憶體洩漏」對策）。"""

    def test_spatial_index_capped(self):
        b = GameMemoryBridge()
        b.MAX_SPATIAL = 5  # 縮小門檻便於測試
        for i in range(10):
            b.observe_world((0, 0, 0), [{"node": "default:tree", "x": i, "y": 0, "z": 0}])
            b._spatial_index[f"{i}_0_0"].last_seen = 100.0 + i  # 遞增年齡戳
        assert len(b._spatial_index) <= 5

    def test_experiences_capped(self):
        import asyncio

        from ai.multimodal.game_memory_bridge import GameExperience, MemoryType

        b = GameMemoryBridge()
        b.MAX_EXPERIENCES = 5

        async def fill():
            for i in range(12):
                await b.store_experience(
                    GameExperience(
                        exp_id=f"e{i}",
                        memory_type=MemoryType.EPISODIC,
                        timestamp=time.time(),
                        position=(0, 0, 0),
                        action="observe",
                        context={},
                        outcome={},
                        reward=0.0,
                    )
                )

        asyncio.run(fill())
        assert len(b._experiences) <= 5


class TestLoadRobustness:
    def test_bad_row_skipped_not_fatal(self, tmp_path):
        # 回歸：單行壞資料不炸掉整份記憶
        import json

        path = str(tmp_path / "spatial.json")
        payload = {
            "locations": [
                {"location_id": "1_1_1", "position": [1, 1, 1], "node_type": "resource"},
                {"location_id": "bad", "position": ["not", "a", "number"]},
                {"location_id": "2_2_2", "position": [2, 2, 2], "node_type": "resource"},
            ]
        }
        with open(path, "w") as f:
            json.dump(payload, f)
        b = GameMemoryBridge()
        loaded = b.load_spatial(path)
        assert loaded == 2
        assert "1_1_1" in b._spatial_index and "2_2_2" in b._spatial_index

    def test_old_format_still_loads(self, tmp_path):
        # 相容：舊檔（無 last_seen 欄位）載入不炸
        import json

        path = str(tmp_path / "old.json")
        with open(path, "w") as f:
            json.dump(
                {"locations": [{"location_id": "1_1_1", "position": [1, 1, 1], "last_visited": 123.0}]}, f
            )
        b = GameMemoryBridge()
        assert b.load_spatial(path) == 1
        assert b._spatial_index["1_1_1"].last_seen == 0.0


class TestAgentReviewFixes:
    """agent 側修復：視覺退回、觀察去重、到場標記。"""

    def _agent(self):
        from ai.autonomous.angela_agent import AngelaAutonomousAgent, AngelaConfig

        agent = AngelaAutonomousAgent(AngelaConfig())
        agent.memory = GameMemoryBridge()
        agent.current_state = GameState(
            tick=0,
            timestamp=time.time(),
            proprioception=Proprioception(
                position=(0.0, 5.0, 0.0),
                yaw=0.0,
                pitch=0.0,
                health=20,
                max_health=20,
                hunger=20,
                breath=10,
                inventory={},
                wielded_item="",
                is_on_ground=True,
                is_in_water=False,
                is_in_lava=False,
            ),
        )
        agent.current_state.proprioception.max_hunger = 20
        return agent

    def test_observation_dedup_same_spot(self):
        import asyncio

        agent = self._agent()
        agent.tick_count = 5
        agent._last_scan = {"nodes": [{"node": "default:tree", "x": 3, "y": 5, "z": 2}]}
        agent._last_vision = None
        asyncio.run(agent._store_observation_memory())
        asyncio.run(agent._store_observation_memory())  # 同點同物第二次
        assert len(agent.memory._experiences) == 1  # 去重：不重複寫

    def test_observation_dedup_different_spot_writes(self):
        import asyncio

        agent = self._agent()
        agent.tick_count = 5
        agent._last_scan = {"nodes": [{"node": "default:tree", "x": 3, "y": 5, "z": 2}]}
        agent._last_vision = None
        asyncio.run(agent._store_observation_memory())
        agent._last_scan = {"nodes": [{"node": "default:stone", "x": 9, "y": 5, "z": 9}]}
        asyncio.run(agent._store_observation_memory())
        assert len(agent.memory._experiences) == 2

    def test_vision_source_falls_back_to_screen(self):
        # 回歸：無遊戲窗時 select_source 退整屏，capture 不再恆 None
        agent = self._agent()

        class FakeVision:
            active_source = "game_window"

            def select_source(self, want=None):
                self.selected = True
                return "screen"

            def capture(self):
                return None  # 無顯示環境

            def recognize(self, frame):
                return None

        agent._screen_vision = FakeVision()
        agent.tick_count = 20  # 越過截幀節流（tick_count=0 會提前 return）
        agent._capture_screen_vision()
        assert agent._screen_vision.selected is True  # 有呼叫 select_source
