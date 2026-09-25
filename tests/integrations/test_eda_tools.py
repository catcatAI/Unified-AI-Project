import shutil
from pathlib import Path

import pytest
from ai.agents.specialized.eda_agent import EdaAgent
from ai.core.training_coordinator import TrainingCoordinator
from core.tools.eda_tool_adapter import EdaToolAdapter


@pytest.mark.integration
@pytest.mark.slow
async def test_real_eda_pipeline_generates_and_explores(tmp_path: Path) -> None:
    missing = [name for name in ("ngspice", "klayout", "magic") if shutil.which(name) is None]
    if missing:
        pytest.skip("EDA executables not installed: " + ", ".join(missing))

    adapter = EdaToolAdapter(config={"max_sweep_points": 4}, output_root=tmp_path)
    agent = EdaAgent(agent_id="eda_integration", adapter=adapter)
    result = await agent.run_experiment("generate a layout and explore R=1k,4.7k with C=100n,220n")

    assert result["status"] in {"success", "partial"}
    assert result["layout"]["status"] == "success"
    assert result["simulation"]["status"] == "success"
    assert result["exploration"]["successful_count"] == 4
    assert any(item["type"] == "gds" for item in result["artifacts"])
    assert result["magic"]["status"] in {"success", "degraded", "missing_pdk"}


@pytest.mark.integration
@pytest.mark.slow
async def test_real_kicad_and_client_handoff_workflow(tmp_path: Path) -> None:
    if shutil.which("kicad-cli") is None:
        pytest.skip("kicad-cli is not installed")

    adapter = EdaToolAdapter(output_root=tmp_path)
    coordinator = TrainingCoordinator()
    agent = EdaAgent(
        agent_id="eda_kicad_integration",
        adapter=adapter,
        training_coordinator=coordinator,
    )
    result = await agent.run_experiment(
        "用 KiCad 生成 PCB、跑 DRC、輸出 Gerber，並準備 EasyEDA/JLCONE handoff"
    )

    assert result["status"] == "success"
    assert result["kicad"]["status"] == "success"
    assert result["kicad"]["metrics"]["violation_count"] == 0
    assert result["kicad"]["metrics"]["gerber_count"] > 0
    assert result["easyeda"]["status"] == "ready_for_client"
    assert result["jlcone"]["status"] == "ready_for_client"
    assert any(item["type"] == "kicad-pcb" for item in result["artifacts"])
    assert any(item["type"] == "easyeda-handoff" for item in result["artifacts"])
    assert any(item["type"] == "jlcone-handoff" for item in result["artifacts"])
    assert any(item["type"] == "jlcone-package" for item in result["artifacts"])
    assert result["learning"]["status"] == "queued"
    assert result["learning"]["eligible"] is False
    assert "pcb_template_only" in result["learning"]["reasons"]
    assert any(item["type"] == "eda-episode" for item in result["artifacts"])
    assert coordinator.pending_eda_episode_count() == 1
