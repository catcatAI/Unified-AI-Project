import asyncio
import sys
from pathlib import Path

import pytest
from core.tools.eda_tool_adapter import EdaToolAdapter


def test_rc_netlist_is_bounded_and_deterministic(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)

    first = adapter.build_rc_netlist(4_700, 220e-9, points=20_000)
    second = adapter.build_rc_netlist(4_700, 220e-9, points=20_000)

    assert first == second
    assert "R1 in out 4700" in first
    assert "C1 out 0 2.2e-07" in first
    assert ".ac dec 2000" in first


def test_ngspice_log_parser_finds_cutoff(tmp_path: Path) -> None:
    log = tmp_path / "result.log"
    log.write_text(
        "\n".join(
            [
                "Index   frequency       vdb(out)",
                "0       1.000000e+00   0.000000e+00",
                "1       1.000000e+03  -3.000000e+00",
                "2       1.000000e+04  -20.000000e+00",
            ]
        ),
        encoding="utf-8",
    )

    metrics = EdaToolAdapter._parse_ngspice_log(log)

    assert metrics["point_count"] == 3
    assert metrics["cutoff_hz"] == 1_000.0
    assert metrics["final_gain_db"] == -20.0


def test_workspace_rejects_paths_outside_job(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)
    workspace = adapter.create_workspace("test")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(ValueError, match="inside the job workspace"):
        adapter._ensure_inside_workspace(outside, workspace)


async def test_run_uses_argument_vector_without_shell(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)
    result = await adapter._run([sys.executable, "-c", "print('adapter-ok')"], tmp_path, timeout=5)

    assert result["return_code"] == 0
    assert "adapter-ok" in result["stdout"]
    assert result["argv"][0] == sys.executable


def test_spice_deck_rejects_process_control_directives() -> None:
    with pytest.raises(ValueError, match="prohibited"):
        EdaToolAdapter._validate_spice_deck(".control\nshell touch /tmp/eda-escape\n.endc\n")


def test_spice_deck_rejects_oversized_input(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"max_input_bytes": 16}, output_root=tmp_path)

    with pytest.raises(ValueError, match="input size limit"):
        asyncio.run(adapter.run_ngspice("* oversized *\n.end\n"))


def test_disabled_adapter_returns_unavailable(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(config={"enabled": False}, output_root=tmp_path)

    result = asyncio.run(adapter.run_ngspice("* smoke *\n.end\n"))

    assert result["status"] == "unavailable"


def test_probe_reports_optional_file_and_gui_bridges(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)

    result = asyncio.run(adapter.probe())

    assert result["tools"]["easyeda"]["mode"] == "file_bridge"
    assert result["tools"]["easyeda"]["integration_status"] == "bridge_required"
    assert result["tools"]["jlcone"]["mode"] == "gui"
    assert result["tools"]["jlcone"]["headless"] is False


def test_rtl_artifact_is_written_as_systemverilog(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)
    workspace = adapter.create_workspace("rtl")

    result = adapter.generate_rtl_artifact(
        workspace,
        "mvu_projection",
        "module mvu_projection; endmodule\n",
    )

    assert result["status"] == "generated"
    assert result["source_kind"] == "structural_header_projection"
    assert result["professional_hdl_simulation"] is False
    assert result["artifact"]["type"] == "systemverilog"
    assert result["artifact"]["relative_path"] == "input/mvu_projection.sv"
    assert (workspace.input_dir / "mvu_projection.sv").is_file()


def test_rtl_artifact_rejects_external_load_directives(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)
    workspace = adapter.create_workspace("rtl")

    with pytest.raises(ValueError, match="prohibited"):
        adapter.generate_rtl_artifact(
            workspace,
            "unsafe",
            '`include "outside.svh"\nmodule unsafe; endmodule\n',
        )


def test_kicad_board_template_contains_edge_cut(tmp_path: Path) -> None:
    text = EdaToolAdapter._kicad_board_text(40, 30)

    assert "(kicad_pcb" in text
    assert '"Edge.Cuts"' in text
    assert "(end 50.0 40.0)" in text


def test_easyeda_and_jlcone_handoffs_are_explicit(tmp_path: Path) -> None:
    adapter = EdaToolAdapter(output_root=tmp_path)
    workspace = adapter.create_workspace("handoff")
    board_path = tmp_path / "board.gbr"
    board_path.write_text("G04 test*", encoding="utf-8")
    artifact = {"type": "gerber", "path": str(board_path), "sha256": "abc"}

    easyeda = adapter.prepare_easyeda_handoff(workspace, [artifact])
    jlcone = adapter.prepare_jlcone_handoff(workspace, [artifact])

    assert easyeda["status"] == "ready_for_client"
    assert easyeda["metrics"]["requires_easyeda_client"] is True
    assert jlcone["status"] == "ready_for_client"
    assert jlcone["metrics"]["order_file_count"] == 1
    assert all(item["bytes"] > 0 for item in easyeda["artifacts"] + jlcone["artifacts"])


def test_easyeda_source_is_staged_without_cli(tmp_path: Path) -> None:
    source = tmp_path / "easyeda_project.json"
    source.write_text("{}", encoding="utf-8")
    adapter = EdaToolAdapter(output_root=tmp_path / "runs")

    result = asyncio.run(adapter.stage_easyeda_file(source))

    assert result["status"] == "ready_for_client"
    assert result["metrics"]["requires_easyeda_client"] is True
    assert any(item["type"] == "easyeda-source" for item in result["artifacts"])
