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
    assert result["research_summary"]["interface_freeze_packet"]["pending_decision_count"] == 10
    assert "待驗決策=10" in result["message"]
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


@pytest.mark.asyncio
async def test_eda_agent_runs_cim_strip_experiment(tmp_path: Path) -> None:
    """The current-process CIM strip must be modelled, not asserted.

    This is the capability the freeze packet lacked: the strip's weight
    linearity, array power, energy per MAC and cell area are all derived from
    the measured device fixture, and the power gate is evaluated at card level
    because one package fits the budget while several do not.
    """
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    coordinator = TrainingCoordinator()
    agent = EdaAgent(
        agent_id="cim_strip_test",
        adapter=adapter,
        training_coordinator=coordinator,
    )

    result = await agent.run_cim_strip_experiment()

    assert result["status"] == "blocked"
    payload = result["result"]
    assert payload["completion_claim_allowed"] is False
    assert payload["config"]["end_state_figures_used"] is False

    # The measured fixture already satisfies the weight-linearity gate.
    assert payload["weight_linearity"]["passes"] is True

    # One package fits 300W; the drafted multi-package card does not.
    envelope = payload["power_envelope"]
    assert envelope["expected_package_fits_board_budget"] is True
    assert envelope["expected_card_fits_board_budget"] is False

    blocker_ids = {item["id"] for item in payload["blockers"]}
    assert "cim_array_power_exceeds_board_budget" in blocker_ids
    assert "cim_energy_density_worse_than_digital_baseline" in blocker_ids

    assert payload["gate_summary"]["all_gates_passed"] is False
    assert result["research_summary"]["next_owner"] == "angela"
    assert result["research_summary"]["completion_claim_allowed"] is False
    assert "不可宣稱最終架構已定案" in result["message"]
    assert coordinator.pending_eda_episode_count() == 1
    assert any(item["type"] == "cim-strip-episode" for item in result["artifacts"])


@pytest.mark.asyncio
async def test_cim_weight_response_verification_is_falsifiable(tmp_path: Path) -> None:
    """The 1:2:4:8 claim must be checkable, and must be able to fail."""
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_verify_test", adapter=adapter)

    result = await agent.verify_cim_weight_response()

    assert result["status"] == "verified"
    static = result["static_check"]
    assert static["status"] == "pass"
    assert static["max_relative_error_frac"] <= 1e-3
    assert static["kcl_exact"] is True
    # Without a sky130 model library the cross-check must say so, not invent one.
    assert result["simulator_cross_check"]["status"] in {"pass", "skipped"}
    assert result["simulator_agrees_with_fixture"] is True


@pytest.mark.asyncio
async def test_cim_weight_response_holds_at_the_reduced_operating_point(
    tmp_path: Path,
    sky130_spice_model: Path,
) -> None:
    """The 1:2:4:8 claim must hold where the design actually runs.

    The recorded fixture measurement was taken at 1.8V, which is the drafted
    rail that the validated design replaces. A claim verified only at the
    abandoned operating point is not verified for the design, so the same
    cross-check is repeated at the recommended point and must reach the same
    verdict while the cell still conducts.
    """
    from ai.hardware.cim_strip_reference import CimStripReferenceModel

    point = CimStripReferenceModel().recommended_design()["design_point"]
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_reduced_rail_test", adapter=adapter)

    result = await agent.verify_cim_weight_response()

    reduced = result["reduced_rail_cross_check"]
    assert reduced["status"] == "pass"
    # It has to be the design's own point, not the 1.8V fixture again.
    assert reduced["array_vds_v"] == point["array_vds_v"]
    assert reduced["input_vgs_max_v"] == point["input_vgs_max_v"]
    assert reduced["array_vds_v"] < 1.8
    verdict = reduced["verdict"]
    assert verdict["max_relative_error_frac"] <= 1e-3
    assert verdict["kcl_relative_error_frac"] <= 1e-6
    # A ratio that passes on a dead cell proves nothing about the operating
    # point, so the cell has to still conduct well above its own idle current.
    measured = reduced["measured"]
    assert measured["bin0"] > 1000 * abs(measured["idle"])
    assert result["reduced_rail_agrees_with_model"] is True
    assert result["status"] == "verified"


@pytest.mark.asyncio
async def test_recorded_reduced_rail_evidence_matches_the_simulation(
    tmp_path: Path,
    sky130_spice_model: Path,
) -> None:
    """The recorded evidence must be the one the simulation produces.

    Writing a figure into an architecture document without binding it to the code
    that produced it is how the stale-evidence problem started, so both the draft
    gate and the packet evidence are compared against a live run, and the two
    genuinely open blockers must still be on the list.
    """
    import yaml

    hardware_dir = Path(__file__).resolve().parents[3] / "hardware/ai_compute_card"
    draft = yaml.safe_load((hardware_dir / "cim_freeze_draft.yaml").read_text(encoding="utf-8"))
    packet = yaml.safe_load(
        (hardware_dir / "angela_interface_freeze_packet.yaml").read_text(encoding="utf-8")
    )

    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_evidence_bind", adapter=adapter)
    result = await agent.verify_cim_weight_response()
    reduced = result["reduced_rail_cross_check"]
    assert reduced["status"] == "pass"

    gate = draft["validation_gates_before_decision"]["weight_response_at_reduced_operating_point"]
    assert gate["status"] == "satisfied_by_measurement"
    assert gate["operating_point"] == "0.3V array rail, 1.0V input swing"
    # The two blockers that a re-run cannot clear must still be blocking.
    remaining = draft["validation_gates_before_decision"]["remaining_unverified"]
    assert remaining["status"] == "blocking_decision"
    assert len(remaining["items"]) == 2

    evidence = packet["cim_planning_evidence"]["ngspice_reduced_rail_recheck"]
    assert evidence["status"] == "pass"
    verdict = reduced["verdict"]
    assert evidence["weight_ratio_max_relative_error_frac"] == pytest.approx(
        verdict["max_relative_error_frac"], rel=0.1
    )
    assert evidence["kcl_relative_error_frac"] == pytest.approx(
        verdict["kcl_relative_error_frac"], rel=0.1
    )
    assert evidence["single_hot_bin0_a"] == pytest.approx(reduced["measured"]["bin0"], rel=1e-6)
    assert evidence["idle_a"] == pytest.approx(reduced["measured"]["idle"], rel=1e-6)


@pytest.mark.asyncio
async def test_cim_strip_experiment_accepts_a_lower_array_rail(tmp_path: Path) -> None:
    """Lowering the rail must show up as a real, quantified power change."""
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_rail_test", adapter=adapter)

    result = await agent.run_cim_strip_experiment(array_vds_v=0.3)

    envelope = result["result"]["power_envelope"]
    assert envelope["array_vds_v"] == 0.3
    # 0.3V rail is 6x below the drafted one and must cost far less power.
    assert envelope["scenarios"][0]["package_power_w"] < 185.5


@pytest.mark.asyncio
async def test_disabled_eda_agent_cim_strip_fails_closed(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(agent_id="eda_test", adapter=adapter)

    result = await agent.run_cim_strip_experiment()

    assert result["status"] == "unavailable"
    assert result["diagnostics"] == ["eda.enabled=false"]


@pytest.mark.asyncio
async def test_cim_experiment_surfaces_a_gate_checked_design_point(tmp_path: Path) -> None:
    """The agent must report a buildable design point, not only blockers.

    Reporting the blockers alone would leave the impression that the current
    process cannot support the topology, when in fact the drafted rail and sense
    window were the problem.
    """
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_design_test", adapter=adapter)

    result = await agent.run_cim_strip_experiment()

    summary = result["research_summary"]
    point = summary["recommended_design_point"]
    assert point is not None
    assert point["passes_all_gates"] is True
    assert point["array_vds_v"] < 1.8
    assert point["energy_pj_per_mac"] < 1.0
    assert point["card_power_w"] < 300.0
    assert point["resolution_bits"] >= 5.0
    assert "可行現行製程設計點" in result["message"]
    assert "不可宣稱最終架構已定案" in result["message"]


@pytest.mark.asyncio
async def test_cim_experiment_reports_sensitivity_of_the_recommendation(
    tmp_path: Path,
) -> None:
    """A recommendation is only useful if its weak assumption is named."""
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_sensitivity_test", adapter=adapter)

    result = await agent.run_cim_strip_experiment()

    sensitivity = result["research_summary"]["recommended_design_sensitivity"]
    sense = sensitivity["sense_time"]
    chain = sensitivity["sense_chain_power"]

    # The sense window is binding, with finite headroom.
    assert sense["headroom_x"] > 1.0
    assert sense["max_sense_time_ns_before_energy_gate_fails"] > sense["chosen_sense_time_ns"]
    # The guessed sense-chain power is not what the result rests on.
    assert chain["sense_chain_power_multiple_that_fails"] >= 10


@pytest.mark.asyncio
async def test_cim_experiment_declares_completion_is_not_claimed(tmp_path: Path) -> None:
    """Even with a passing design point, the architecture is not frozen."""
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_claim_test", adapter=adapter)

    result = await agent.run_cim_strip_experiment()

    assert result["status"] == "blocked"
    assert result["research_summary"]["completion_claim_allowed"] is False
    assert result["result"]["completion_claim_allowed"] is False
    assert result["result"]["recommended_design"]["design_point"] is not None


# The chip workspace holds a flattened sky130 tt corner file that is the same
# model the freeze packet's verified measurement came from. Pointing the lookup
# at it lets the full chain run here; without it the checks skip rather than
# pretend to have simulated anything.
CHIP_WORKSPACE = Path("/home/cxuo/chip/.angela_repair")
CHIP_SPICE_MODEL = CHIP_WORKSPACE / "nfet_model_global.spice"


@pytest.fixture
def sky130_spice_model(monkeypatch: pytest.MonkeyPatch) -> Path:
    if not CHIP_SPICE_MODEL.is_file():
        pytest.skip(f"no sky130 SPICE model at {CHIP_SPICE_MODEL}")
    monkeypatch.setenv("ANGELA_SKY130_SPICE_LIBRARY", str(CHIP_SPICE_MODEL))
    return CHIP_SPICE_MODEL


@pytest.mark.asyncio
async def test_cim_dot_product_experiment_computes_exact_int8_products(
    tmp_path: Path,
    sky130_spice_model: Path,
) -> None:
    """The array must return the right integers, not merely the right ratios."""
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_dot_test", adapter=adapter)

    result = await agent.run_cim_dot_product_experiment(cases=3, strips=4, slots=6)

    assert result["status"] in {"pass", "skipped"}
    if result["status"] == "skipped":
        pytest.skip(result["message"])
    payload = result["result"]
    assert payload["cases_passed"] == payload["case_count"]
    assert payload["case_count"] >= 3
    for case in payload["cases"]:
        for strip in case["strips"]:
            assert strip["passes"] is True
            # abs tolerance matters: a zero dot product has no scale to be
            # relatively close to
            assert strip["decoded_value"] == pytest.approx(
                strip["expected_value"], rel=0.02, abs=0.05
            )
    assert payload["total_cell_count"] > 0


@pytest.mark.asyncio
async def test_cim_dot_product_experiment_rejects_bad_parameters(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_dot_bad", adapter=adapter)

    result = await agent.run_cim_dot_product_experiment(cases=0)

    assert result["status"] == "error"
    assert "cases, strips and slots must be positive" in result["message"]


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_cim_single_die_reports_the_measured_density_not_the_claim(
    tmp_path: Path,
) -> None:
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="cim_density_test", adapter=adapter)

    result = await agent.run_cim_single_die_experiment(
        weight_bits=4, slots=2, simulate_extracted=False
    )

    layout = result["result"]["layout_verification"]
    if layout["status"] == "skipped":
        pytest.skip(layout["reason"])
    findings = result["result"]["density_findings"]
    assert findings["measured_um2_per_cell"] > 0
    assert findings["measured_over_claimed_x"] > 1.0
    assert findings["pdk_min_characterised_w_um"] == 1.255
    assert "bare device W*L" in findings["note"]
    sizing = result["result"]["single_die_sizing"]
    assert sizing["capacity"]["weight_capacity_kb"] > 0


@pytest.mark.asyncio
async def test_disabled_eda_agent_new_cim_capabilities_fail_closed(
    tmp_path: Path,
) -> None:
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(agent_id="eda_test", adapter=adapter)

    for call in (
        agent.run_cim_dot_product_experiment(),
        agent.run_cim_single_die_experiment(),
    ):
        result = await call
        assert result["status"] == "unavailable"
        assert result["diagnostics"] == ["eda.enabled=false"]


@pytest.mark.asyncio
async def test_card_architecture_audit_corrects_the_summary(tmp_path: Path) -> None:
    """The agent must re-derive the claims and label the blocking ones."""
    adapter = EdaToolAdapter(config={"enabled": True}, output_root=tmp_path)
    agent = EdaAgent(agent_id="audit_test", adapter=adapter)

    result = await agent.run_card_architecture_audit()

    assert result["status"] == "corrected"
    assert result["blocking_finding_count"] == 2
    assert result["completion_claim_allowed"] is False
    report = result["result"]
    blocking = [item for item in report["corrections"] if item["severity"] == "blocking"]
    assert {item["id"] for item in blocking} == {
        "token_rate_is_bandwidth_bound",
        "l1_undersized_for_residency",
    }
    # The claim is preserved so every correction is a diff.
    assert report["claimed"]["claimed_tokens_per_s"] == 4800.0
    assert report["claimed"]["card_l1_mb"] == 180.0
    assert "阻斷" in result["message"]


@pytest.mark.asyncio
async def test_card_architecture_audit_needs_no_simulator(tmp_path: Path) -> None:
    """The audit is arithmetic over fixtures, so it must not need magic or ngspice."""
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)
    agent = EdaAgent(agent_id="audit_offline_test", adapter=adapter)

    result = await agent.run_card_architecture_audit()

    assert result["status"] == "corrected"
    assert result["result"]["recomputed"]["measured_efficiency"]["status"] == "ok"
