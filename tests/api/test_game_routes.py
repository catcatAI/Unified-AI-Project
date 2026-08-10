"""Tests for game_routes API endpoints.

Covers:
- Route import and registration (10 endpoints)
- Read-only endpoints (status/worlds/characters/cards/axes)
- Session lifecycle (create / state / action / end)
- Error handling (missing session, engine unavailable)
"""

import sys
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
            "/game/worlds",
            "/game/characters",
            "/game/cards",
            "/game/axes",
            "/game/sessions",
            "/game/sessions/{sid}",
            "/game/sessions/{sid}/action",
            "/game/sessions/{sid}/action".replace("/action", ""),
        }
        assert "/game/sessions" in paths
        assert "/game/sessions/{sid}" in paths
        assert "/game/sessions/{sid}/action" in paths
        assert expected.issubset(paths) or all(
            ep in paths
            for ep in [
                "/game/status",
                "/game/worlds",
                "/game/characters",
                "/game/cards",
                "/game/axes",
            ]
        )

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
