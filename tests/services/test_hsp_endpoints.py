"""
测试模块 - test_hsp_endpoints

自动生成的测试模块，用于验证系统功能。
"""

import pytest
from fastapi.testclient import TestClient

from apps.backend.src.services.main_api_server import app
from apps.backend.src.core_services import get_services as real_get_services


class FakeDialogueManager:
    def __init__(self) -> None:
        self.pending_hsp_task_requests = {}


class FakeHSPConnector:
    def __init__(self) -> None:
        self.ai_id = "did:hsp:test"
        self.is_connected = True

    async def send_task_request(self, payload, target_ai_id: str):
        # Return a deterministic correlation id for testing
        return "corr-123"


class FakeServiceDiscovery:
    def __init__(self, found: bool = True) -> None:
        self._found = found

    def find_capabilities(self, capability_id_filter: str = ""):
        if not self._found:
            return []
        return [
            {
                "capability_id": capability_id_filter or "cap-1",
                "ai_id": "did:ai:target-xyz",
                "name": "Test Capability",
                "version": "1.0",
            }
        ]


class FakeHAMMemoryManager:
    def __init__(self) -> None:
        self._records = []

    def add_success(self, correlation_id: str, payload: dict):
        self._records.append(
            {
                "data_type": "success",
                "metadata": {
                    "hsp_correlation_id": correlation_id,
                    "hsp_task_service_payload": payload,
                },
            }
        )

    def add_error(self, correlation_id: str, error_details: dict):
        self._records.append(
            {
                "data_type": "error",
                "metadata": {
                    "hsp_correlation_id": correlation_id,
                    "error_details": error_details,
                },
            }
        )

    def query_core_memory(self, metadata_filters: dict | None = None):
        if not metadata_filters:
            return list(self._records)
        cid = metadata_filters.get("hsp_correlation_id")
        if cid is None:
            return list(self._records)
        return [r for r in self._records if r.get("metadata", {}).get("hsp_correlation_id") == cid]


@pytest.fixture
def hsp_fakes():
    fakes = {
        "dialogue_manager": FakeDialogueManager(),
        "hsp_connector": FakeHSPConnector(),
        "service_discovery": FakeServiceDiscovery(found=True),
        "ham_manager": FakeHAMMemoryManager(),
        # Optional placeholders used by other endpoints
        "llm_interface": object(),
        "trust_manager": type("Trust", (), {"get_all_trust_scores": lambda self: {}})(),
    }
    return fakes


@pytest.fixture
def client(hsp_fakes):
    def fake_get_services():
        return hsp_fakes

    app.dependency_overrides[real_get_services] = fake_get_services
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(real_get_services, None)



    def setUp(self):
        """测试前设置"""
        self.test_data = {}
        self.test_config = {}
    
    def tearDown(self):
        """测试后清理"""
        self.test_data.clear()
        self.test_config.clear()
def test_hsp_create_and_pending_then_complete(client: TestClient, hsp_fakes) -> None:
    # Create task
    body = {"target_capability_id": "cap-1", "parameters": {"x": 1}}
    resp = client.post("/api/v1/hsp/tasks", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status_message") in {"HSP Task request sent successfully.", "error"}
    corr_id = data.get("correlation_id") or "corr-123"

    # Immediately check status -> pending (no HAM record yet, but tracked in DialogueManager)
    resp2 = client.get(f"/api/v1/hsp/tasks/{corr_id}")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2.get("status") == "pending"

    # Simulate completion in HAM
    _ = hsp_fakes["ham_manager"].add_success(corr_id, {"ok": True, "echo": {"x": 1}})

    resp3 = client.get(f"/api/v1/hsp/tasks/{corr_id}")
    assert resp3.status_code == 200
    data3 = resp3.json()
    assert data3.get("status") == "completed"
    assert data3.get("result_payload", {}).get("ok") is True


def test_hsp_create_capability_not_found(client: TestClient, hsp_fakes) -> None:
    # Force discovery to return empty
    hsp_fakes["service_discovery"]._found = False

    body = {"target_capability_id": "cap-missing", "parameters": {}}
    resp = client.post("/api/v1/hsp/tasks", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("error") == "Capability not discovered."
    assert "not found" in data.get("status_message", "").lower()


def test_hsp_status_unknown(client: TestClient) -> None:
    resp = client.get("/api/v1/hsp/tasks/unknown-999")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "unknown_or_expired"