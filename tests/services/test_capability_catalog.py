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

        # Use a real dispatchable agent id: the catalog now intersects the
        # registry with the orchestrator's dispatch table, so a made-up id would
        # (correctly) be reported as unreachable.
        manager = SimpleNamespace(agents={"vision_processing_agent": Adapter()})
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
            model_bus=SimpleNamespace(
                _handlers={"file_ops": object()},
                _handler_map={"file": "file_ops"},
            ),
        )
        snapshot = build_capability_snapshot(service)

        assert snapshot["agents"][0]["id"] == "vision_processing_agent"
        assert snapshot["agents"][0]["capabilities"] == ["vision", "audio"]
        assert snapshot["backends"][0]["active"] is True
        # handlers are now reported as {id, intents, dispatchable}
        assert [item["id"] for item in snapshot["handlers"]] == ["file_ops"]
        assert snapshot["handlers"][0]["intents"] == ["file"]
        assert snapshot["handlers"][0]["dispatchable"] is True
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
                        "dispatchable": True,
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
        assert "未啟用或無入口的功能我不會說成已可用" in response


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
                        "id": "eda_agent",
                        "state": "registered",
                        "capabilities": ["actual_task"],
                        "methods": [],
                        "dispatchable": True,
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


class TestCatalogHonesty:
    """The catalog must never advertise something a user cannot reach.

    Verified against the live runtime before the fix: the capability answer
    listed fantasy_dm_agent (3 capabilities), web_search_agent and
    vision_processing_agent, yet no intent maps to any of them, so no message
    could ever select them.
    """

    def test_registered_but_unreachable_ids_are_the_reference(self):
        """Reachability is the reference the catalog is compared against.

        This test used to assert that fantasy_dm / web_search /
        vision_processing were NOT reachable — which was the honest state while no
        intent selected them. They now have intents (`roleplay`,
        `web_research`, `image_detail`), so the premise is inverted: the three must
        be reachable, and the honesty requirement moves to "every registered agent
        id is either dispatchable or explicitly labelled".
        """
        from ai.agents.agent_orchestrator import dispatchable_agent_ids

        reachable = dispatchable_agent_ids()
        assert "eda_agent" in reachable
        assert "knowledge_graph_agent" in reachable
        for wired in ("fantasy_dm_agent", "web_search_agent", "vision_processing_agent"):
            assert wired in reachable, f"{wired} has an intent and must be dispatchable"

    def test_unreachable_agents_are_labelled_not_listed(self):
        response = render_capability_response(
            {
                "agents": [
                    {
                        "id": "eda_agent",
                        "state": "registered",
                        "capabilities": ["eda_probe"],
                        "methods": [],
                        "dispatchable": True,
                    },
                    {
                        "id": "fantasy_dm_agent",
                        "state": "registered",
                        "capabilities": ["create_character"],
                        "methods": [],
                        "dispatchable": False,
                    },
                ],
                "backends": [],
                "handlers": [],
                "services": [],
                "core_modules": [],
            }
        )
        assert "可從對話直接觸發的專業代理（1）" in response
        assert "已註冊但沒有對話入口" in response
        assert "fantasy_dm_agent" in response, "must be disclosed, just not as usable"
        # create_character must not appear as a usable capability
        usable_line = response.split("• 已註冊但沒有對話入口")[0]
        assert "create_character" not in usable_line

    def test_handlers_report_reachability(self):
        response = render_capability_response(
            {
                "agents": [],
                "backends": [],
                "handlers": [
                    {"id": "file_ops", "intents": ["file"], "dispatchable": True},
                    {"id": "orphan_handler", "intents": [], "dispatchable": False},
                ],
                "services": [],
                "core_modules": [],
            }
        )
        assert "可呼叫的工具／handlers：file_ops" in response
        assert "無法被路由到的 handler：orphan_handler" in response

    def test_gate_reports_every_dispatchable_handler(self):
        from ai.core.execution_gate import ExecutionGate

        reachable = ExecutionGate.dispatchable_handler_ids()
        # QueryType-keyed handlers
        for handler in ("file_ops", "web_search", "code_exec", "vision", "civil"):
            assert handler in reachable
        # registry-dispatched handlers
        for handler in ("learning", "image_generate"):
            assert handler in reachable
