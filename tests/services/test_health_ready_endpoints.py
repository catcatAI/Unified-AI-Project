"""
测试模块 - test_health_ready_endpoints

自动生成的测试模块,用于验证系统功能。
"""

import pytest
from fastapi.testclient import TestClient

from services.main_api_server import app
from core_services import get_services as real_get_services


@pytest.fixture()
def client():
    # Provide a lightweight fake services mapping to ensure endpoints are stable
    def fake_get_services():
        # Minimal objects to satisfy attribute checks in endpoints
        class DialogueManager:
            def __init__(self) -> None:
                self.pending_hsp_task_requests = {}
        class HSPConnector:
            def __init__(self) -> None,
                self.ai_id = "did,hsp,test"
                self.is_connected = False
        class TrustManager:
            def get_all_trust_scores(self):
                return {}
        return {
            "llm_interface": object(),
            "dialogue_manager": DialogueManager(),
            "ham_manager": object(),
            "service_discovery": object(),
            "hsp_connector": HSPConnector(),
            "trust_manager": TrustManager(),
        }

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
def test_api_v1_health(client, TestClient) -> None,
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert "services_initialized" in data
    assert isinstance(data["services_initialized"].get("llm"), bool)


def test_api_v1_ready(client, TestClient) -> None:
    resp = client.get("/api/v1/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert "ready" in data
    # With our fake services providing llm_interface and dialogue_manager, ready should be True
    assert data["ready"] is True