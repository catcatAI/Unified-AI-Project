"""Comprehensive HTTP-level tests for all API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from services.main_api_server import app

# =============================================================================
# ANGELA-MATRIX: L4 [βδ] [A] [L3]
# Mock services
# =============================================================================

class MockDriveService:
    def is_authenticated(self):
        return True
    def get_storage_info(self):
        return {"used": "1GB", "total": "15GB", "user": "test@example.com"}
    def get_auth_url(self):
        return "https://accounts.google.com/o/oauth2/auth?mock=1"
    def exchange_code(self, code: str) -> bool:
        return True
    def logout(self):
        pass
    def list_files(self, page_size=10, query=None):
        return [{"id": "1", "name": "test.txt", "mimeType": "text/plain"}]
    def get_file_metadata(self, file_id: str):
        return {"id": file_id, "name": "test.txt", "mimeType": "text/plain", "size": "1024"}
    def download_file(self, file_id: str, dest_path: str) -> bool:
        return True


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Drive API (8 endpoints)
# =============================================================================

class TestDriveAPI:
    @pytest.fixture(autouse=True)
    def setup(self):
        from api.v1.endpoints._deps import get_drive_service
        app.dependency_overrides[get_drive_service] = lambda: MockDriveService()
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_drive_status(self, client):
        resp = await client.get("/api/v1/drive/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("connected", "disconnected", "error")
        assert "authenticated" in data
        assert data["service"] == "Google Drive"

    @pytest.mark.asyncio
    async def test_drive_auth_status(self, client):
        resp = await client.get("/api/v1/drive/auth/status")
        assert resp.status_code == 200
        assert resp.json()["authenticated"] is True

    @pytest.mark.asyncio
    async def test_drive_auth_url(self, client):
        resp = await client.get("/api/v1/drive/auth/url")
        assert resp.status_code == 200
        assert "url" in resp.json()

    @pytest.mark.asyncio
    async def test_drive_auth_callback(self, client):
        resp = await client.post("/api/v1/drive/auth/callback", json={"code": "test_code"})
        assert resp.status_code == 200
        assert resp.json()["authenticated"] is True

    @pytest.mark.asyncio
    async def test_drive_auth_callback_missing_code(self, client):
        resp = await client.post("/api/v1/drive/auth/callback", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_drive_auth_logout(self, client):
        resp = await client.post("/api/v1/drive/auth/logout")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_drive_files(self, client):
        resp = await client.get("/api/v1/drive/files")
        assert resp.status_code == 200
        assert "files" in resp.json()

    @pytest.mark.asyncio
    async def test_drive_file_metadata(self, client):
        resp = await client.get("/api/v1/drive/files/doc123/metadata")
        assert resp.status_code == 200
        meta = resp.json()
        assert meta["id"] == "doc123"
        assert meta["name"] == "test.txt"

    @pytest.mark.asyncio
    async def test_drive_files_sync(self, client):
        resp = await client.post(
            "/api/v1/drive/files/sync",
            json={"file_ids": ["f1", "f2"], "store_memory": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "synced" in data
        assert "files" in data


# =============================================================================
# Ops API (3 endpoints)
# =============================================================================

class TestOpsAPI:
    @pytest.mark.asyncio
    async def test_ops_status(self, client):
        resp = await client.get("/api/v1/ops/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "ops"

    @pytest.mark.asyncio
    async def test_ops_health(self, client):
        resp = await client.get("/api/v1/ops/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "ops"
        assert data["status"] in ("healthy", "degraded", "unhealthy")

    @pytest.mark.asyncio
    async def test_ops_maintenance(self, client):
        resp = await client.post("/api/v1/ops/maintenance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "started"
        assert data["task"] == "maintenance"


# =============================================================================
# Desktop API (6 endpoints)
# =============================================================================

class TestDesktopAPI:
    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        from api.lifespan import get_action_executor, get_desktop_interaction

        self.mock_interaction = MagicMock()
        self.mock_interaction.get_desktop_state.return_value = MagicMock(
            total_files=100, total_size=1024, categories={}, clutter_level=0.5
        )
        self.mock_interaction.organize_desktop = AsyncMock(return_value=[])
        self.mock_interaction.cleanup_desktop = AsyncMock(return_value=[])

        self.mock_executor = MagicMock()
        self.mock_executor.get_execution_stats.return_value = {"total_executed": 0, "queue_size": 0}
        self.mock_executor.handle_autonomous_action = AsyncMock(
            return_value={"status": "ok", "action_id": "act_1"}
        )

        app.dependency_overrides[get_desktop_interaction] = lambda: self.mock_interaction
        app.dependency_overrides[get_action_executor] = lambda: self.mock_executor
        yield
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_desktop_state(self, client):
        resp = await client.get("/api/v1/desktop/state")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["state"]["total_files"] == 100
        assert data["state"]["clutter_level"] == 0.5

    @pytest.mark.asyncio
    @patch("api.routes.desktop_routes.get_desktop_interaction")
    async def test_desktop_organize(self, mock_get_di, client):
        mock_get_di.return_value = self.mock_interaction
        resp = await client.post("/api/v1/desktop/organize")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.asyncio
    @patch("api.routes.desktop_routes.get_desktop_interaction")
    async def test_desktop_cleanup(self, mock_get_di, client):
        mock_get_di.return_value = self.mock_interaction
        resp = await client.post("/api/v1/desktop/cleanup?days_old=30")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    @pytest.mark.asyncio
    async def test_actions_status(self, client):
        resp = await client.get("/api/v1/actions/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "stats" in data

    @pytest.mark.asyncio
    @patch("api.routes.desktop_routes.get_action_executor")
    async def test_actions_execute(self, mock_get_ae, client):
        mock_get_ae.return_value = self.mock_executor
        resp = await client.post(
            "/api/v1/actions/execute",
            json={"type": "file_operation", "parameters": {"action": "delete"}, "priority": "high"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["result"]["status"] == "ok"



# =============================================================================
# Other V1 Status stubs (7 endpoints)
# =============================================================================

# Status stub routes with their expected response shape
# (route, service, expected_status)
STATUS_STUBS = [
    ("pet", "pet", "unavailable"),
    ("vision", "vision", "ok"),
    ("audio", "audio", "ok"),
    ("tactile", "tactile", "unavailable"),
    ("trace", "trace", "enabled"),
    ("plugins", "plugins", "ok"),
]


class TestStatusStubs:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("route,service,expected_status", STATUS_STUBS)
    async def test_status_returns_expected(self, client, route, service, expected_status):
        resp = await client.get(f"/api/v1/{route}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == expected_status
        assert data["service"] == service


# =============================================================================
# Mobile API (5 endpoints)
# =============================================================================

class TestMobileAPI:
    @pytest.mark.asyncio
    async def test_mobile_sync(self, client):
        resp = await client.post("/api/v1/mobile/sync", json={"key": "value"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "synchronized"
        assert data["received_data"] == {"key": "value"}

    @pytest.mark.asyncio
    @patch("core.system.cluster_manager.cluster_manager")
    async def test_mobile_status_get(self, mock_cluster, client):
        mock_cluster.get_cluster_status.return_value = {
            "node_count": 3,
            "healthy": True,
        }
        resp = await client.get("/api/v1/mobile/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "metrics" in data
        assert data["metrics"]["nodes"] == 3

    @pytest.mark.asyncio
    @patch("core.sync.realtime_sync.SyncEvent")
    @patch("core.sync.realtime_sync.sync_manager")
    async def test_mobile_module_control(self, mock_sm, mock_se, client):
        mock_sm.broadcast_event = AsyncMock()
        resp = await client.post(
            "/api/v1/mobile/module-control",
            json={"module": "vision", "enabled": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["module"] == "vision"

    @pytest.mark.asyncio
    @patch("core.sync.realtime_sync.SyncEvent")
    @patch("core.sync.realtime_sync.sync_manager")
    async def test_mobile_module_control_missing_fields(self, mock_sm, mock_se, client):
        mock_sm.broadcast_event = AsyncMock()
        resp = await client.post("/api/v1/mobile/module-control", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"

    @pytest.mark.asyncio
    @patch("api.routes.chat_routes._handle_chat_request", new_callable=AsyncMock)
    async def test_mobile_chat(self, mock_handle, client):
        mock_handle.return_value = {"response_text": "Hello!", "source": "test"}
        resp = await client.post(
            "/api/v1/mobile/chat",
            json={"message": "Hi", "user_name": "Tester"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["response_text"] == "Hello!"

    @pytest.mark.asyncio
    @patch("api.routes.chat_routes._handle_chat_request", new_callable=AsyncMock)
    async def test_mobile_chat_empty_message(self, mock_handle, client):
        mock_handle.return_value = {"response_text": "", "source": "stub"}
        resp = await client.post(
            "/api/v1/mobile/chat",
            json={"message": ""},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"


# =============================================================================
# System API (partially implemented — only security/sync-key-c exists)
# =============================================================================

class TestSystemAPI:
    @pytest.mark.asyncio
    @patch("api.routes.chat_routes.get_abc_key_manager")
    async def test_security_sync_key_c(self, mock_get_keys, client):
        mock_mgr = MagicMock()
        mock_mgr.get_key.return_value = "key-c-value"
        mock_get_keys.return_value = mock_mgr
        resp = await client.get("/api/v1/security/sync-key-c")
        assert resp.status_code == 200
        assert resp.json() == {"key_available": True}


class TestMetaControllerEndpoints:
    """Tests for MetaController confidence API endpoints."""

    async def test_confidence_summary(self, client):
        from ai.meta.meta_controller import MetaController
        from api.routes.meta_routes import set_meta_controller
        mc = MetaController()
        mc.record_confidence("test:ed3n", 0.85)
        mc.record_confidence("test:garden", 0.72)
        set_meta_controller(mc)
        try:
            resp = await client.get("/api/v1/meta/confidence/summary")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert "summary" in data
            assert "stats" in data
        finally:
            set_meta_controller(None)

    async def test_confidence_calibration_known_source(self, client):
        from ai.meta.meta_controller import MetaController
        from api.routes.meta_routes import set_meta_controller
        mc = MetaController()
        for i in range(5):
            mc.record_confidence("test:ed3n", 0.85)
        set_meta_controller(mc)
        try:
            resp = await client.get("/api/v1/meta/confidence/calibration/test:ed3n")
            assert resp.status_code == 200
            data = resp.json()
            assert data["source"] == "test:ed3n"
        finally:
            set_meta_controller(None)

    async def test_confidence_calibration_unknown_source(self, client):
        from ai.meta.meta_controller import MetaController
        from api.routes.meta_routes import set_meta_controller
        mc = MetaController()
        set_meta_controller(mc)
        try:
            resp = await client.get("/api/v1/meta/confidence/calibration/unknown")
            assert resp.status_code == 200
            data = resp.json()
            assert data["calibration"] is None
        finally:
            set_meta_controller(None)


# =============================================================================
# Untestable endpoints note
# =============================================================================

# The following 4 endpoints listed in the specification do not exist in the
# codebase and therefore cannot be tested:
#   GET    /api/v1/system/status
#   GET    /api/v1/system/status/detailed
#   POST   /api/v1/system/status
#   POST   /api/v1/system/module-control
# A fifth endpoint listed under "System API" — GET /api/v1/security/sync-key-c
# — does exist and IS tested above.
