from pathlib import Path
from types import SimpleNamespace

import pytest
from ai.agents.agent_adapter import AgentAdapter
from ai.agents.agent_orchestrator import AgentOrchestrator
from ai.agents.specialized.eda_agent import EdaAgent, _query_numbers
from ai.core.training_coordinator import TrainingCoordinator
from core.tools.eda_tool_adapter import EdaToolAdapter


def test_eda_queries_route_to_specialized_agent() -> None:
    orchestrator = AgentOrchestrator()

    assert orchestrator.classify_intent("請用 ngspice 模擬 RC 濾波器") == "eda"
    assert orchestrator.select_agent("eda") == "eda_agent"
    assert orchestrator.classify_intent("用 Magic 和 KLayout 生成 layout") == "eda"
    assert orchestrator.classify_intent("幫我寫一首詩") == "creative_write"
    assert orchestrator.classify_intent("用 KiCad 生成 PCB Gerber") == "eda"
    assert orchestrator.classify_intent("把 EasyEDA 檔案交給 Angela") == "eda"
    assert orchestrator.classify_intent("準備 JLCONE 下單 handoff") == "eda"


@pytest.mark.asyncio
async def test_ai_card_request_uses_reference_method_on_eda_agent() -> None:
    calls = []

    class FakeManager:
        async def execute_agent(self, agent_id, task):
            calls.append((agent_id, task))
            return SimpleNamespace(
                success=True,
                result_data={"status": "partial", "message": "reference pending"},
                error=None,
            )

    result = await AgentOrchestrator(agent_manager=FakeManager()).route_task(
        "請執行 AI 計算卡 software-only reference，檢查 interface freeze"
    )

    assert result["primary_intent"] == "eda"
    assert calls[0][0] == "eda_agent"
    assert calls[0][1]["method"] == "run_ai_card_reference_experiment"
    assert result["results"][0]["result"]["result"]["status"] == "partial"


@pytest.mark.asyncio
async def test_hardware_standard_request_uses_eda_catalog_method() -> None:
    calls = []

    class FakeManager:
        async def execute_agent(self, agent_id, task):
            calls.append((agent_id, task))
            return SimpleNamespace(
                success=True,
                result_data={"status": "ok", "count": 1},
                error=None,
            )

    result = await AgentOrchestrator(agent_manager=FakeManager()).route_task(
        "請查 PCIe 5.0 標準與 CEM 版本"
    )

    assert result["primary_intent"] == "eda"
    assert calls[0][0] == "eda_agent"
    assert calls[0][1]["method"] == "get_hardware_standards"


def test_ai_card_terms_are_eda_intents() -> None:
    assert AgentOrchestrator.is_eda_request("研究 AI 計算卡的 PCIe 架構")
    assert AgentOrchestrator.is_eda_execution_request("請執行 AI 計算卡 reference")
    assert AgentOrchestrator().classify_intent("硬體工程師繼續研究計算卡") == "eda"


@pytest.mark.asyncio
async def test_eda_agent_generates_rtl_projection(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    coordinator = TrainingCoordinator()
    agent = EdaAgent(
        agent_id="rtl_test",
        adapter=adapter,
        training_coordinator=coordinator,
    )

    result = await agent.run_rtl_experiment(clock_mhz=250)

    assert result["status"] == "generated_structural_projection"
    assert result["result"]["professional_hdl_simulation"] is False
    assert result["result"]["physical_hardware"] is False
    assert result["result"]["rtl_artifact"]["type"] == "systemverilog"
    assert result["result"]["rtl_artifact"]["relative_path"].endswith(".sv")
    assert result["result"]["testbench_artifact"]["type"] == "systemverilog"
    assert result["result"]["testbench_artifact"]["relative_path"].endswith(".sv")
    assert result["learning"]["status"] == "queued"
    assert coordinator.pending_eda_episode_count() == 1


@pytest.mark.asyncio
async def test_rtl_generation_request_uses_eda_method() -> None:
    calls = []

    class FakeManager:
        async def execute_agent(self, agent_id, task):
            calls.append((agent_id, task))
            return SimpleNamespace(
                success=True,
                result_data={"status": "generated_structural_projection"},
                error=None,
            )

    result = await AgentOrchestrator(agent_manager=FakeManager()).route_task(
        "請生成 SystemVerilog RTL 結構投影"
    )

    assert result["primary_intent"] == "eda"
    assert calls[0][0] == "eda_agent"
    assert calls[0][1]["method"] == "run_rtl_experiment"


@pytest.mark.asyncio
async def test_eda_followup_context_reuses_reference_method() -> None:
    calls = []

    class FakeManager:
        async def execute_agent(self, agent_id, task):
            calls.append((agent_id, task))
            return SimpleNamespace(
                success=True,
                result_data={"status": "partial", "message": "follow-up reference"},
                error=None,
            )

    result = await AgentOrchestrator(agent_manager=FakeManager()).route_task(
        "請解釋這個結果的原因。", {"_eda_followup": True}
    )

    assert result["primary_intent"] == "eda"
    assert calls[0][1]["method"] == "run_ai_card_reference_experiment"
    assert result["results"][0]["result"]["result"]["message"] == "follow-up reference"


def test_eda_followup_requires_context_marker() -> None:
    assert AgentOrchestrator.is_eda_followup_request("請整理剛才的結果")
    assert not AgentOrchestrator.is_eda_followup_request("請解釋數學公式")


def test_query_parser_reads_engineering_sweep_lists() -> None:
    values = _query_numbers("R=1k,4.7k,10k C=100n,220n,1u", "R")

    assert values == [1_000.0, 4_700.0, 10_000.0]


def test_eda_agent_exposes_official_hardware_standards() -> None:
    agent = EdaAgent(agent_id="eda_test", adapter=EdaToolAdapter(config={"enabled": False}))

    result = agent.get_hardware_standards("PCIe")

    assert result["status"] == "ok"
    assert result["count"] == 3
    assert {item["standard_id"] for item in result["standards"]} == {
        "pcie_base_5.0",
        "pcie_cem_5.0",
        "pcie_12v_2x6_ecn",
    }
    assert "hardware_standards" in [item["name"] for item in agent.capabilities]


def test_eda_agent_uses_run_experiment_as_primary_method(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(agent_id="eda_test", adapter=adapter)
    wrapped = AgentAdapter(agent, agent_id="eda_test")

    assert wrapped._primary_method == "run_experiment"
    assert set(agent.get_status()) == {
        "agent_id",
        "enabled",
        "output_root",
        "tools",
        "learning_episodes",
    }


def test_eda_learning_collection_can_be_disabled(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(
        config={"enabled": False, "collect_learning_episodes": False},
        output_root=tmp_path,
    )
    agent = EdaAgent(agent_id="eda_test", adapter=adapter)

    assert agent.get_status()["learning_episodes"]["enabled"] is False


@pytest.mark.asyncio
async def test_eda_agent_runs_boolean_gate_experiment(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    coordinator = TrainingCoordinator()
    agent = EdaAgent(
        agent_id="logic_gate_test",
        adapter=adapter,
        training_coordinator=coordinator,
    )

    result = await agent.run_logic_gate_experiment(
        training_rows=[
            {"a": 0, "b": 0, "output": 1},
            {"a": 0, "b": 1, "output": 0},
            {"a": 1, "b": 0, "output": 0},
        ],
        evaluation_rows=[{"a": 1, "b": 1}],
        oracle_expression="a == b",
    )

    assert result["status"] == "success"
    assert result["result"]["hypothesis"] == "xnor"
    assert result["result"]["all_rows_pass"] is True
    assert result["learning"]["status"] == "queued"
    assert coordinator.pending_logic_episode_count() == 1
    assert any(item["type"] == "logic-gate-episode" for item in result["artifacts"])


@pytest.mark.asyncio
async def test_eda_agent_runs_active_boolean_experiment(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="logic_active_test", adapter=adapter)

    result = await agent.run_logic_gate_experiment(
        training_rows=[{"a": 0, "b": 0, "output": 1}],
        evaluation_rows=[
            {"a": 0, "b": 0},
            {"a": 0, "b": 1},
            {"a": 1, "b": 0},
            {"a": 1, "b": 1},
        ],
        oracle_expression="a == b",
        active=True,
    )

    assert result["status"] == "success"
    assert result["result"]["hypothesis"] == "xnor"
    assert result["result"]["corrections"]
    assert result["result"]["all_rows_pass"] is True


@pytest.mark.asyncio
async def test_eda_agent_runs_mvu_reference_experiment(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="mvu_reference_test", adapter=adapter)

    result = await agent.run_mvu_reference_experiment(clock_mhz=250)

    assert result["status"] == "partial"
    assert result["result"]["metrics"]["total_pipeline_stalls"] is None
    assert result["result"]["metrics"]["pipeline_stalls_measured"] is False
    assert result["result"]["metrics"]["raw_collision_count"] == 0
    assert result["result"]["header_recalculation"]["bandwidth"]["forward_gbs"] == 512.0
    assert any(item["type"] == "mvu-reference-episode" for item in result["artifacts"])


@pytest.mark.asyncio
async def test_eda_agent_runs_ai_card_reference_experiment(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    coordinator = TrainingCoordinator()
    agent = EdaAgent(
        agent_id="ai_card_reference_test",
        adapter=adapter,
        training_coordinator=coordinator,
    )

    result = await agent.run_ai_card_reference_experiment()

    assert result["status"] == "partial"
    assert result["result"]["bandwidth"]["main_internal_raw_gbs"] == 512.0
    assert result["result"]["cost"]["decision"] == "BLOCKED_PENDING_QUOTES"
    assert result["learning"]["status"] == "queued"
    assert result["research_summary"]["next_owner"] == "angela"
    assert result["research_summary"]["completion_claim_allowed"] is False
    assert result["research_summary"]["interface_freeze_packet"]["pending_decision_count"] == 6
    assert "待凍結決策=6" in result["message"]
    assert "不可宣稱完成最終設計" in result["message"]
    assert coordinator.pending_eda_episode_count() == 1
    assert any(item["type"] == "ai-compute-card-reference-episode" for item in result["artifacts"])


async def test_disabled_eda_agent_fails_closed(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(agent_id="eda_test", adapter=adapter)

    result = await agent.run_experiment("generate a layout")

    assert result["status"] == "unavailable"
    assert result["diagnostics"] == ["eda.enabled=false"]


def test_spec_keeps_explicit_sweep_values(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(agent_id="eda_test", adapter=adapter)

    spec = agent._spec_from_query("sweep R=1k,4.7k C=100n,220n", 1_000, 1e-6, 20, 10, True)

    assert spec["resistances"] == [1_000.0, 4_700.0]
    assert spec["capacitances"] == pytest.approx([1e-7, 2.2e-7])
    assert spec["sweep"] is True


def test_design_request_detection() -> None:
    assert EdaAgent._is_design_request("KiCad PCB Gerber")
    assert EdaAgent._is_design_request("EasyEDA source")
    assert EdaAgent._is_design_request("JLCONE order")
    assert not EdaAgent._is_design_request("ngspice RC filter")


def test_eda_execution_requires_explicit_action() -> None:
    assert AgentOrchestrator.is_eda_execution_request("用 KiCad 生成 PCB")
    assert AgentOrchestrator.is_eda_execution_request("請跑 ngspice 模擬")
    assert AgentOrchestrator.is_eda_execution_request("把 EasyEDA 檔案交給 Angela")
    assert not AgentOrchestrator.is_eda_execution_request("什麼是 PCB？")
    assert not AgentOrchestrator.is_eda_execution_request("解釋 EasyEDA")


@pytest.mark.asyncio
async def test_eda_agent_records_sanitized_episode(tmp_path: Path) -> None:
    class Coordinator:
        def __init__(self) -> None:
            self.episodes = []

        async def enqueue_eda_episode(self, episode):
            self.episodes.append(episode)
            return True

    coordinator = Coordinator()
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(
        agent_id="eda_test",
        adapter=adapter,
        training_coordinator=coordinator,
    )

    result = await agent._record_learning_episode(
        workflow="pcb",
        parameters={"width_mm": 40.0, "account": "hidden"},
        tools={"kicad": {"version": "10.0.6"}},
        results={
            "kicad": {
                "status": "success",
                "metrics": {
                    "drc_parsed": True,
                    "violation_count": 0,
                    "unconnected_count": 0,
                    "gerber_count": 4,
                    "component_count": 1,
                    "track_count": 1,
                    "template_only": False,
                },
            }
        },
        artifacts=[],
    )

    assert result["status"] == "queued"
    assert result["eligible"] is True
    assert len(coordinator.episodes) == 1
    assert "account" not in coordinator.episodes[0]["parameters"]
