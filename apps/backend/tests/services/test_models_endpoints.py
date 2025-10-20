import pytest
from fastapi.testclient import TestClient

from apps.backend.src.services.main_api_server import app as fastapi_app
from apps.backend.src.services import main_api_server
from apps.backend.src.core_services import get_services as real_get_services


@pytest.fixture
def client():
    # Minimal dependency overrides to keep other endpoints stable
    class DialogueManager:
        def __init__(self) -> None:
            self.pending_hsp_task_requests = {}

    class HSPConnector:
        def __init__(self) -> None:
            self.ai_id = "did:hsp:test"
            self.is_connected = False

    class TrustManager:
        def get_all_trust_scores(self):
            return {}

    def fake_get_services():
        return {
            _ = "llm_interface": object(),
            _ = "dialogue_manager": DialogueManager(),
            _ = "ham_manager": object(),
            _ = "service_discovery": object(),
            _ = "hsp_connector": HSPConnector(),
            _ = "trust_manager": TrustManager(),
        }

    fastapi_app.dependency_overrides[real_get_services] = fake_get_services
    with TestClient(fastapi_app) as c:
        yield c
    _ = fastapi_app.dependency_overrides.pop(real_get_services, None)


def test_models_available(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: patch get_multi_llm_service and ModelRegistry
    class FakeMultiLLM:
        def __init__(self) -> None:
            self.model_configs = {
                "gpt-4": {"provider": "openai"},
                "llama3": {"provider": "meta"},
            }

    class FakeRegistry:
        def __init__(self, model_configs) -> None:
            self._cfg = model_configs
        def profiles_dict(self):
            # Return keys with provider names to check pass-through
            return {k: {"provider": v.get("provider")} for k, v in self._cfg.items()}

    _ = monkeypatch.setattr(main_api_server, "get_multi_llm_service", lambda: FakeMultiLLM())
    _ = monkeypatch.setattr(main_api_server, "ModelRegistry", FakeRegistry)

    # Act
    resp = client.get("/api/v1/models/available")

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data
    assert data["models"].get("gpt-4", {}).get("provider") == "openai"
    assert data["models"].get("llama3", {}).get("provider") == "meta"


def test_models_route(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: Patch ModelRegistry and PolicyRouter to be deterministic
    class FakeRegistry:
        def __init__(self, model_configs) -> None:
            self._cfg = model_configs

    class FakeRouter:
        def __init__(self, registry) -> None:
            self._registry = registry
        def route(self, policy):
            # Echo a simplified routing decision using policy fields
            return {
                "selected_model": "gpt-4" if getattr(policy, "needs_tools", False) else "llama3",
                "policy": {
                    _ = "task_type": getattr(policy, "task_type", None),
                    _ = "input_chars": getattr(policy, "input_chars", None),
                    _ = "needs_tools": getattr(policy, "needs_tools", None),
                    _ = "needs_vision": getattr(policy, "needs_vision", None),
                    _ = "latency_target": getattr(policy, "latency_target", None),
                    _ = "cost_ceiling": getattr(policy, "cost_ceiling", None),
                },
            }

    # get_multi_llm_service is used to build a registry; keep minimal config
    class FakeMultiLLM:
        def __init__(self) -> None:
            self.model_configs = {"gpt-4": {}, "llama3": {}}

    _ = monkeypatch.setattr(main_api_server, "get_multi_llm_service", lambda: FakeMultiLLM())
    _ = monkeypatch.setattr(main_api_server, "ModelRegistry", FakeRegistry)
    _ = monkeypatch.setattr(main_api_server, "PolicyRouter", FakeRouter)

    # Act: needs_tools True should select gpt-4
    body = {
        "task_type": "code",
        "input_chars": 1200,
        "needs_tools": True,
        "needs_vision": False,
        "latency_target": "p95<2s",
        "cost_ceiling": 0.01,
    }
    resp = client.post("/api/v1/models/route", json=body)

    # Assert
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("selected_model") == "gpt-4"
    assert data.get("policy", {}).get("task_type") == "code"

    # Act 2: needs_tools False should select llama3
    body["needs_tools"] = False
    resp2 = client.post("/api/v1/models/route", json=body)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2.get("selected_model") == "llama3"