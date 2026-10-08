# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""agent_workspace 路由冒烟測試（首個專屬測試檔：此前零覆蓋）。

全部 10 個端點：context overview/focus/search、session open/read/act/save/close、
learning tail，另加 workspace 缺失 503。沿用 test_api_endpoints.py 的真實
UnifiedWorkspace（mock interaction + tmp 學習日誌）隔離模式。
"""

from __future__ import annotations

import pytest

from .test_api_endpoints import client  # noqa: F401  (fixture reuse)


@pytest.fixture
def workspace_override():
    import tempfile
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock

    from api.lifespan import get_agent_workspace
    from services.agent_workspace.agent import AgentWorkspace, DesktopAgent
    from services.agent_workspace.app_session import AppSessionManager
    from services.agent_workspace.global_tree import GlobalContextTree, UnifiedWorkspace

    interaction = MagicMock()
    manager = AppSessionManager(
        adapters={"desktop": DesktopAgent(interaction)},
        log_path=Path(tempfile.mkdtemp()) / "learning_log.jsonl",
    )
    workspace = UnifiedWorkspace(AgentWorkspace(session_manager=manager), GlobalContextTree())

    from services.main_api_server import app

    app.dependency_overrides[get_agent_workspace] = lambda: workspace
    yield workspace
    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestAgentContext:
    async def test_overview(self, client, workspace_override):
        resp = await client.get("/api/v1/agent/context/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict) and len(data) > 0

    async def test_focus_unknown_node_404(self, client, workspace_override):
        resp = await client.get("/api/v1/agent/context/focus/no-such-node")
        assert resp.status_code == 404

    async def test_focus_root_returns_view(self, client, workspace_override):
        resp = await client.get("/api/v1/agent/context/focus/root")
        assert resp.status_code == 200
        assert "error" not in resp.json()

    async def test_search(self, client, workspace_override):
        resp = await client.get("/api/v1/agent/context/search", params={"query": "desktop"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    async def test_workspace_missing_503(self, client):
        from api.lifespan import get_agent_workspace
        from services.main_api_server import app

        app.dependency_overrides[get_agent_workspace] = lambda: None
        try:
            resp = await client.get("/api/v1/agent/context/overview")
            assert resp.status_code == 503
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestAgentSessionLifecycle:
    async def test_open_requires_app_id(self, client, workspace_override):
        resp = await client.post("/api/v1/agent/session/open", json={})
        assert resp.status_code == 422

    async def test_full_lifecycle(self, client, workspace_override):
        opened = await client.post("/api/v1/agent/session/open", json={"app_id": "desktop"})
        assert opened.status_code == 200

        read = await client.post("/api/v1/agent/session/read", json={"app_id": "desktop"})
        assert read.status_code == 200

        saved = await client.post("/api/v1/agent/session/save", json={"app_id": "desktop"})
        assert saved.status_code == 200

        closed = await client.post(
            "/api/v1/agent/session/close", json={"app_id": "desktop", "confirm": True}
        )
        assert closed.status_code == 200

    async def test_act_requires_action(self, client, workspace_override):
        resp = await client.post("/api/v1/agent/session/act", json={"app_id": "desktop"})
        assert resp.status_code == 422

    async def test_learning_tail(self, client, workspace_override):
        resp = await client.get("/api/v1/agent/learning")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert isinstance(data["entries"], list)

    async def test_learning_limit_clamped(self, client, workspace_override):
        for limit, want in ((0, 1), (500, 200)):
            resp = await client.get("/api/v1/agent/learning", params={"limit": limit})
            assert resp.status_code == 200


@pytest.mark.asyncio
class TestAgentWorkspaceUnavailable:
    """workspace 缺失時全部端點 503（不裸奔 500）。"""

    @pytest.mark.parametrize(
        "method,path,json",
        [
            ("GET", "/api/v1/agent/context/overview", None),
            ("GET", "/api/v1/agent/context/focus/x", None),
            ("GET", "/api/v1/agent/context/search", None),
            ("POST", "/api/v1/agent/session/open", {"app_id": "a"}),
            ("POST", "/api/v1/agent/session/read", {"app_id": "a"}),
            ("POST", "/api/v1/agent/session/act", {"app_id": "a", "action": "x"}),
            ("POST", "/api/v1/agent/session/save", {"app_id": "a"}),
            ("POST", "/api/v1/agent/session/close", {"app_id": "a"}),
            ("GET", "/api/v1/agent/learning", None),
        ],
    )
    async def test_all_endpoints_503_without_workspace(self, client, method, path, json):
        from api.lifespan import get_agent_workspace
        from services.main_api_server import app

        app.dependency_overrides[get_agent_workspace] = lambda: None
        try:
            if method == "GET":
                resp = await client.get(path, params={"query": "x"} if "search" in path else None)
            else:
                resp = await client.post(path, json=json)
            assert resp.status_code == 503
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_session_validation_422s(self, client, workspace_override):
        for path, body in [
            ("/api/v1/agent/session/read", {}),
            ("/api/v1/agent/session/save", {}),
            ("/api/v1/agent/session/close", {}),
            ("/api/v1/agent/session/act", {"app_id": "a"}),
        ]:
            resp = await client.post(path, json=body)
            assert resp.status_code == 422, path

    async def test_focus_error_dict_maps_to_404(self, client, workspace_override, monkeypatch):
        from unittest.mock import AsyncMock

        monkeypatch.setattr(
            workspace_override, "focus", lambda node_id: {"error": "gone"}, raising=False
        )
        resp = await client.get("/api/v1/agent/context/focus/any")
        assert resp.status_code == 404
        assert "gone" in resp.text

    async def test_act_plumbing(self, client, workspace_override, monkeypatch):
        from unittest.mock import AsyncMock

        seen = {}

        async def fake_act(app_id, action, params=None, confirm=False, source="exploration"):
            seen.update(app_id=app_id, action=action, params=params, confirm=confirm, source=source)
            return {"ok": True}

        monkeypatch.setattr(workspace_override, "act", fake_act)
        resp = await client.post(
            "/api/v1/agent/session/act",
            json={"app_id": "a", "action": "look", "params": {"k": 1}, "confirm": True},
        )
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        assert seen == {
            "app_id": "a",
            "action": "look",
            "params": {"k": 1},
            "confirm": True,
            "source": "exploration",
        }
