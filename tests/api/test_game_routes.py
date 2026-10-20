"""Tests for game_routes API endpoints.

Covers:
- Route import and registration (read-only + session + M8 runner endpoints)
- Read-only endpoints (status/worlds/characters/cards/axes)
- Session lifecycle (create / state / action / end)
- M8 resident tick loop (start/stop/snapshot + status runner block)
- Error handling (missing session, engine unavailable)
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


@pytest.mark.asyncio
class TestGameRoutesImport:
    """Verify module imports and route registration."""

    async def test_module_importable(self):
        from api.routes import game_routes

        assert game_routes is not None

    async def test_router_exported(self):
        from api.routes.game_routes import router

        assert router is not None
        assert len(router.routes) >= 8

    async def test_router_has_expected_paths(self):
        from api.routes.game_routes import router

        paths = {r.path for r in router.routes}
        expected = {
            "/game/status",
            "/game/engine/status",
            "/game/engine/start",
            "/game/engine/stop",
            "/game/engine/snapshot",
            "/game/worlds",
            "/game/characters",
            "/game/cards",
            "/game/axes",
            "/game/validate",
            "/game/sessions",
            "/game/sessions/{sid}",
            "/game/sessions/{sid}/action",
        }
        missing = expected - paths
        assert not missing, f"missing routes: {sorted(missing)}"

    async def test_router_prefix(self):
        from api.routes.game_routes import router

        assert router.prefix == "/game"
        assert router.tags == ["Game"]


@pytest.mark.asyncio
class TestGameReadOnly:
    """Test read-only endpoints."""

    async def test_status_available(self):
        from api.routes import game_routes

        result = game_routes.game_status()
        assert result["available"] is True
        assert result["total_cards"] > 0

    async def test_worlds_shape(self):
        from api.routes import game_routes

        result = game_routes.game_worlds()
        assert "worlds" in result
        assert len(result["worlds"]) >= 1
        assert {"id", "name", "desc"}.issubset(result["worlds"][0].keys())

    async def test_characters_shape(self):
        from api.routes import game_routes

        result = game_routes.game_characters()
        assert "characters" in result
        assert len(result["characters"]) >= 1
        assert {"card_id", "name", "description"}.issubset(result["characters"][0].keys())

    async def test_cards_shape(self):
        from api.routes import game_routes

        result = game_routes.game_cards()
        assert "cards" in result
        assert result["total"] > 0
        first = result["cards"][0]
        assert {"card_id", "card_type", "name"}.issubset(first.keys())

    async def test_cards_filter(self):
        from api.routes import game_routes

        result = game_routes.game_cards(card_type="角色卡")
        assert result["total"] > 0
        assert all(c["card_type"] == "角色卡" for c in result["cards"])

    async def test_axes_shape(self):
        from api.routes import game_routes

        result = game_routes.game_axes()
        assert "axes" in result
        assert "物種" in result["axes"]
        assert "AI" in result["axes"]


@pytest.mark.asyncio
class TestGameSession:
    """Test session lifecycle."""

    async def test_new_session(self):
        from api.routes import game_routes

        game_routes._SESSIONS.clear()
        result = game_routes.game_session_new(pc_card_id="CC-01", scene_card_id="S15")
        assert result["session_id"]
        state = result["state"]
        assert state["pc"]["name"]
        assert isinstance(state["choices"], list) and len(state["choices"]) > 0
        assert len(state["messages"]) > 0

    async def test_state_get(self):
        from api.routes import game_routes

        game_routes._SESSIONS.clear()
        sid = game_routes.game_session_new()["session_id"]
        result = game_routes.game_session_state(sid)
        assert result["session_id"] == sid
        assert result["state"]["turn"] == 0

    async def test_action_advances_state(self):
        from api.routes import game_routes

        game_routes._SESSIONS.clear()
        sid = game_routes.game_session_new()["session_id"]
        result = game_routes.game_session_action(sid, "3")
        assert result["state"]["turn"] == 1
        assert len(result["state"]["messages"]) > 0

    async def test_session_end(self):
        from api.routes import game_routes

        game_routes._SESSIONS.clear()
        sid = game_routes.game_session_new()["session_id"]
        ended = game_routes.game_session_end(sid)
        assert ended["status"] == "ended"
        assert sid not in game_routes._SESSIONS

    async def test_session_eviction_at_cap(self):
        from api.routes import game_routes

        game_routes._SESSIONS.clear()
        original = game_routes._SESSION_MAX
        game_routes._SESSION_MAX = 3
        try:
            for _ in range(5):
                game_routes.game_session_new()
            assert len(game_routes._SESSIONS) == 3
        finally:
            game_routes._SESSION_MAX = original
            game_routes._SESSIONS.clear()

    async def test_action_missing_session(self):
        from api.routes import game_routes
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            game_routes.game_session_action("nonexistent", "3")
        assert exc.value.status_code == 404

    async def test_state_missing_session(self):
        from api.routes import game_routes
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc:
            game_routes.game_session_state("nonexistent")
        assert exc.value.status_code == 404


@pytest.mark.asyncio
class TestGameDegraded:
    """Graceful degradation when the engine cannot load."""

    async def test_status_unavailable(self):
        from api.routes import game_routes

        with patch.object(game_routes, "_get_engine", side_effect=RuntimeError("no cards")):
            result = game_routes.game_status()
            assert result["available"] is False
            assert result["total_cards"] == 0

    async def test_worlds_unavailable_raises_503(self):
        from api.routes import game_routes
        from fastapi import HTTPException

        with patch.object(game_routes, "_get_engine", side_effect=RuntimeError("no cards")):
            with pytest.raises(HTTPException) as exc:
                game_routes.game_worlds()
            assert exc.value.status_code == 503

    async def test_axes_unavailable_raises_503(self):
        from api.routes import game_routes
        from fastapi import HTTPException

        with patch.object(game_routes, "_load_axis_system", side_effect=RuntimeError("no axes")):
            with pytest.raises(HTTPException) as exc:
                game_routes.game_axes()
            assert exc.value.status_code == 503

    async def test_router_includes_game(self):
        from api.router import router as main_router

        paths = set()
        for r in getattr(main_router, "routes", []):
            if hasattr(r, "original_router"):
                ctx = getattr(r, "include_context", None)
                sub_prefix = getattr(ctx, "prefix", "") or ""
                for sub in getattr(r.original_router, "routes", []):
                    if hasattr(sub, "path"):
                        paths.add(sub_prefix + sub.path)
            elif hasattr(r, "path"):
                paths.add(r.path)
        assert "/api/v1/game/status" in paths
        assert "/api/v1/game/engine/status" in paths


@pytest.mark.asyncio
class TestAxisEngineStatus:
    """§6.4 萬物皆軸引擎只讀端點（master tick/組清單）。"""

    async def test_engine_status_shape(self):
        from api.routes import game_routes

        result = game_routes.game_engine_status()
        assert result["available"] is True
        assert result["engine"] == "axis-v1"
        assert result["master_hz"] == 60.0
        assert result["master_ticks"] == 0  # 只讀：不啟動任何迴圈
        assert len(result["groups"]) == 1
        group = result["groups"][0]
        assert group["name"] == "story"
        assert group["tick_rate"] == 30.0
        assert group["time_scale"] == 1.0
        assert set(group["axes"]) == {"card_type", "story_role"}
        assert group["axes"]["card_type"] == {"kind": "fsm", "states": 20}
        assert group["axes"]["story_role"] == {"kind": "fsm", "states": 9}
        assert set(group["signals"]) == {"card_type", "story_role"}

    async def test_engine_status_idempotent_read_only(self):
        from api.routes import game_routes

        first = game_routes.game_engine_status()
        second = game_routes.game_engine_status()
        assert first == second  # 兩次全等=tick 未前進、無副作用

    async def test_engine_status_unavailable_degrades(self):
        from api.routes import game_routes

        with patch.object(
            game_routes, "_get_axis_engine", side_effect=RuntimeError("no axis engine")
        ):
            result = game_routes.game_engine_status()
        assert result["available"] is False
        assert result["groups"] == []
        assert result["master_ticks"] == 0


@pytest.mark.asyncio
class TestAxisEngineRunnerM8:
    """M8 常駐 tick 迴圈端點（§6.4「生產 tick 迴圈」遠期項；輪詢消費介面）。"""

    async def test_status_includes_runner_block(self):
        from api.routes import game_routes

        result = game_routes.game_engine_status()
        runner = result["runner"]
        assert runner["running"] is False
        assert set(runner["groups"]) == {"story"}

    async def test_snapshot_idempotent_and_read_only(self):
        from api.routes import game_routes

        first = game_routes.game_engine_snapshot()
        second = game_routes.game_engine_snapshot()
        assert first["available"] is True
        assert first["engine"] == "axis-v1"
        assert first["running"] is False
        assert first == second  # 兩次全等=未啟動執行緒、無副作用
        assert set(first["groups"]) == {"story"}
        group = first["groups"]["story"]
        assert set(group) == {"fired", "dt", "time_scale"}
        assert group["dt"] == pytest.approx(1.0 / 30.0)
        assert set(first["signals"]) == set()  # 未 fire 前訊號表為空

    async def test_start_ticks_seeds_story_then_stop_freezes(self):
        from api.routes import game_routes

        start = game_routes.game_engine_start()
        assert start["available"] is True
        assert start["running"] is True
        try:
            deadline = time.monotonic() + 2.0
            snap = start
            while snap["master_ticks"] < 3 and time.monotonic() < deadline:
                time.sleep(0.02)
                snap = game_routes.game_engine_snapshot()
            assert snap["master_ticks"] >= 3
            assert snap["running"] is True
            story = snap["signals"].get("story", {})
            assert story.get("card_type")
            assert story.get("story_role")
            from engine import content as _content

            seed = _content.card_to_values(_content.load_cards()[0])
            assert story["card_type"] == seed["card_type"]
            assert story["story_role"] == seed["story_role"]
        finally:
            stop = game_routes.game_engine_stop()
        assert stop["running"] is False
        frozen = stop["master_ticks"]
        time.sleep(0.05)
        assert game_routes.game_engine_snapshot()["master_ticks"] == frozen

    async def test_start_stop_idempotent(self):
        from api.routes import game_routes

        first = game_routes.game_engine_start()
        second = game_routes.game_engine_start()
        try:
            assert first["running"] is True
            assert second["running"] is True
        finally:
            game_routes.game_engine_stop()
            again = game_routes.game_engine_stop()
        assert again["running"] is False

    async def test_snapshot_unavailable_degrades(self):
        from api.routes import game_routes

        with patch.object(game_routes, "_get_axis_runner", side_effect=RuntimeError("no runner")):
            result = game_routes.game_engine_snapshot()
        assert result["available"] is False
        assert result["running"] is False
        assert result["signals"] == {}

    async def test_start_unavailable_raises_503(self):
        from api.routes import game_routes
        from fastapi import HTTPException

        with patch.object(game_routes, "_get_axis_runner", side_effect=RuntimeError("no runner")):
            with pytest.raises(HTTPException) as exc:
                game_routes.game_engine_start()
        assert exc.value.status_code == 503
