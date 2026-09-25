# ANGELA-MATRIX: L3 [βδ] [A] [L2-L6]

from types import SimpleNamespace

import pytest

from services.llm.capability_catalog import (
    build_capability_snapshot,
    render_capability_response,
)


class TestRuntimeCapabilityCatalog:
    def test_snapshot_uses_runtime_registries(self, monkeypatch):
        from services.llm.capability_catalog import _collect_core_modules
        from services.llm.capability_catalog import _collect_registered_services

        class Agent:
            capabilities = [
                {"capability_id": "vision", "name": "vision"},
                {"capability_id": "audio", "name": "audio"},
            ]

        class Adapter:
            agent = Agent()

            def get_status(self):
                return {"agent_status": {"enabled": True, "available_methods": ["analyze"]}}

        manager = SimpleNamespace(agents={"vision_agent": Adapter()})
        monkeypatch.setattr("api.lifespan.get_agent_manager", lambda: manager)
        monkeypatch.setattr(
            "services.llm.capability_catalog._collect_core_modules",
            lambda: ["digital_life_instance"],
        )
        monkeypatch.setattr(
            "services.llm.capability_catalog._collect_registered_services",
            lambda: ["global_state_store"],
        )

        service = SimpleNamespace(
            backends={"local": SimpleNamespace(model="test-model")},
            active_backend_type=SimpleNamespace(value="local"),
            model_bus=SimpleNamespace(_handler_map={"file_ops": object()}),
        )
        snapshot = build_capability_snapshot(service)

        assert snapshot["agents"][0]["id"] == "vision_agent"
        assert snapshot["agents"][0]["capabilities"] == ["vision", "audio"]
        assert snapshot["backends"][0]["active"] is True
        assert snapshot["handlers"] == ["file_ops"]
        assert snapshot["core_modules"] == ["digital_life_instance"]
        assert snapshot["services"] == ["global_state_store"]

    def test_response_does_not_claim_unregistered_features(self):
        response = render_capability_response(
            {
                "agents": [
                    {
                        "id": "eda_agent",
                        "state": "registered",
                        "capabilities": ["eda_probe", "rtl_generate"],
                        "methods": [],
                    }
                ],
                "backends": [],
                "handlers": [],
                "services": [],
                "core_modules": [],
            }
        )

        assert "eda_agent" in response
        assert "eda_probe" in response
        assert "global_intelligence" not in response
        assert "未啟用的功能我不會說成已可用" in response


class TestCapabilityRouterShortCircuit:
    @pytest.mark.asyncio
    async def test_capability_question_uses_runtime_catalog(self, monkeypatch):
        from services.llm.router import AngelaLLMService

        service = AngelaLLMService.__new__(AngelaLLMService)
        service.stats = {"total_requests": 0}
        monkeypatch.setattr(
            "services.llm.router.build_capability_snapshot",
            lambda _service: {
                "agents": [
                    {
                        "id": "runtime_agent",
                        "state": "registered",
                        "capabilities": ["actual_task"],
                        "methods": [],
                    }
                ],
                "backends": [],
                "handlers": [],
                "services": [],
                "core_modules": [],
            },
        )

        response = await service.generate_response_full("你會啥？", {})

        assert response.backend == "capability-catalog"
        assert "actual_task" in response.text
        assert service.stats["total_requests"] == 1
