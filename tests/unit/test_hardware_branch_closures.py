# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Cross-module branch closures for the hardware package.

These pin the residual toolchain-failure branches (magic/tech absent, giant
nets, missing ngspice, deck-builder rejections) and the result-shaping branches
that the module suites leave open.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import ai.hardware.cim_verify as cim_verify
import ai.hardware.cim_strip_reference as strip_ref
from ai.hardware.cim_verify import GateReport, simulate_spine, verify_block
from ai.hardware.cim_strip_reference import (
    _MODEL_LIBRARY_ENV,
    DotProductVector,
    evaluate_dot_product_case,
    run_functional_dot_product_test,
    simulate_weight_response,
)


# -----------------------------------------------------------------------------
# cim_verify residual branches
# -----------------------------------------------------------------------------


def test_verify_block_runs_all_gates_even_without_magic_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A gate set that vanishes when a tool is absent can never fail loudly."""
    monkeypatch.setattr(cim_verify, "find_magic", lambda: None)
    monkeypatch.setattr(cim_verify, "find_magic_tech", lambda: None)
    report = verify_block("<< end >>", expected_transistors=4, workdir=tmp_path)
    names = [gate.name for gate in report.gates]
    assert "drc_clean" in names and "netlist_written" in names
    assert report.ok is False


def test_verify_block_always_allocates_a_workdir_when_none_given(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr(cim_verify, "find_magic", lambda: None)
    monkeypatch.setattr(cim_verify, "find_magic_tech", lambda: None)
    report = verify_block("<< end >>", expected_transistors=4)
    assert not report.ok  # ran without raising on the temp workdir


def test_simulate_spine_skips_without_ngspice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(cim_verify, "find_ngspice", lambda: None)
    assert simulate_spine("* empty", (1, 2), tmp_path) == {
        "status": "skipped",
        "reason": "ngspice_not_found",
    }


def test_giant_net_gate_can_fail(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """expected_spine_sizes=None + expected_columns>0 activates the giant gate."""

    # 12 devices all share one gate on one drain net: the extract parses, the
    # columns gate sees a single array net whose cells make the "largest net"
    # comparison meaningful, and the giant-net gate must not bless it.
    netlist = "".join(
        f"X{i} NET GW S VSUBS sky130_fd_pr__nfet_01v8 w=0.42 l=0.15\n"
        for i in range(12)
    )
    monkeypatch.setattr(
        cim_verify,
        "_run_drc_and_extract",
        lambda mag_text, workdir, timeout_s=900.0: (0, netlist, "DRC_TOTAL 0"),
    )
    report = verify_block(
        "<mag>", expected_transistors=12, expected_columns=6, workdir=tmp_path
    )
    gate = next(g for g in report.gates if g.name == "no_giant_net")
    assert gate.passed is False, report.summary()
    assert "12 of 12" in gate.detail


# -----------------------------------------------------------------------------
# AXI register masks
# -----------------------------------------------------------------------------


def test_axi_register_write_masks() -> None:
    from ai.hardware.mvu_reference import AxiLiteRegisterMap, MvuReferenceModel

    model = MvuReferenceModel()
    model.axi.write(AxiLiteRegisterMap.CR, 0b1111)  # 3-bit field (start/reset/mode)
    assert model.axi.read(AxiLiteRegisterMap.CR) == 0b111
    model.axi.write(AxiLiteRegisterMap.SR, 0b1111)  # 2-bit field
    assert model.axi.read(AxiLiteRegisterMap.SR) == 0b11
    model.axi.write(AxiLiteRegisterMap.INDIRECT_ADDR, 0xFFFF)  # 15-bit field
    assert model.axi.read(AxiLiteRegisterMap.INDIRECT_ADDR) == 0x7FFF


# -----------------------------------------------------------------------------
# cim_strip_reference residual result-shaping branches
# -----------------------------------------------------------------------------


def _library(tmp_path: Path) -> Path:
    library = tmp_path / "sky130.lib.spice"
    library.write_text(".model sky130_fd_pr__nfet_01v8__model nmos\n", encoding="utf-8")
    return library


def test_simulate_weight_response_skips_when_the_deck_builder_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> str:
        raise strip_ref.CimStripError("degenerate deck request")

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: _library(tmp_path))
    monkeypatch.setattr(strip_ref, "build_weight_response_deck", refuse)
    outcome = asyncio_run(simulate_weight_response(tmp_path))
    assert outcome == {"status": "skipped", "reason": "degenerate deck request"}


def test_run_functional_dot_product_test_skips_when_the_deck_builder_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> str:
        raise strip_ref.CimStripError("degenerate vector request")

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: _library(tmp_path))
    monkeypatch.setattr(strip_ref, "build_dot_product_deck", refuse)
    vector = DotProductVector(input_bits=(1,), strip_weights=((7,),), label="v")
    outcome = asyncio_run(run_functional_dot_product_test(tmp_path, [vector]))
    assert outcome == {"status": "skipped", "reason": "degenerate vector request"}


def test_run_functional_dot_product_test_reports_a_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeProcess:
        killed = False

        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio_sleep(10)
            return b"", b""

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> None:
            return None

    process = FakeProcess()

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return process

    async def fake_wait_for(awaitable: object, timeout: float) -> None:
        raise asyncio_timeout_error()

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: _library(tmp_path))
    vector = DotProductVector(input_bits=(1,), strip_weights=((7,),), label="v")
    monkeypatch.setattr(
        strip_ref,
        "build_dot_product_deck",
        lambda *a, **k: ("* deck", ["case0_cal.txt"]),
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(strip_ref.asyncio, "wait_for", fake_wait_for)

    outcome = asyncio_run(run_functional_dot_product_test(tmp_path, [vector], timeout_s=0.01))

    assert outcome["status"] == "error"
    assert "timed out after 0.01s" in outcome["reason"]
    assert process.killed is True


def test_run_functional_dot_product_test_passes_with_fake_ngspice_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vector = DotProductVector(input_bits=(1, 1), strip_weights=((7, 0),), label="v")

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            (tmp_path / "case0_cal.txt").write_text("v(i) = 1.0e-06\n", encoding="utf-8")
            (tmp_path / "case0_s0.txt").write_text("v(i) = 7.0e-06\n", encoding="utf-8")
            return b"", b""

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: _library(tmp_path))
    monkeypatch.setattr(
        strip_ref, "build_dot_product_deck", lambda *a, **k: ("* deck", ["case0_cal.txt", "case0_s0.txt"])
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)

    outcome = asyncio_run(run_functional_dot_product_test(tmp_path, [vector]))

    assert outcome["status"] == "pass"
    assert outcome["cases_passed"] == 1
    assert outcome["strip_count"] == 1


def test_run_functional_dot_product_reports_no_parseable_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vector = DotProductVector(input_bits=(1, 1), strip_weights=((7, 0),), label="v")

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: _library(tmp_path))
    monkeypatch.setattr(
        strip_ref, "build_dot_product_deck", lambda *a, **k: ("* deck", ["case0_cal.txt"])
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)

    outcome = asyncio_run(run_functional_dot_product_test(tmp_path, [vector]))

    assert outcome["status"] == "error"
    assert outcome["reason"] == "ngspice produced no parseable dot-product output"


def test_parse_weight_output_without_a_known_label_is_kept_verbatim(
    tmp_path: Path,
) -> None:
    (tmp_path / "wXD.txt").write_text("v(i) = 3.5\n", encoding="utf-8")
    measured = strip_ref.parse_weight_response_outputs(tmp_path)
    assert measured == {"wXD": 3.5}


def test_evaluate_weight_response_rejects_a_dead_baseline() -> None:
    outcome = strip_ref.evaluate_weight_response(
        {
            "bin0": 0.0,
            "bin0_cells": 1.0,
            "bin1": 2.0e-06,
            "bin1_cells": 2.0,
        }
    )
    assert outcome["status"] == "insufficient_data"
    assert "not positive" in outcome["detail"]


def test_run_functional_dot_product_flags_nan_strip_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A strip whose output file never appears must fail, not silently pass."""
    vector = DotProductVector(input_bits=(1, 1), strip_weights=((7, 0),), label="v")

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            (tmp_path / "case0_cal.txt").write_text("v(i) = 1.0e-06\n", encoding="utf-8")
            # case0_s0.txt is missing: measured.s0 becomes NaN
            return b"", b""

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: _library(tmp_path))
    monkeypatch.setattr(
        strip_ref, "build_dot_product_deck", lambda *a, **k: ("* deck", ["case0_cal.txt", "case0_s0.txt"])
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)

    outcome = asyncio_run(run_functional_dot_product_test(tmp_path, [vector]))

    assert outcome["status"] == "fail"
    import math

    row = outcome["cases"][0]["strips"][0]
    assert math.isnan(row["measured_current_a"])
    assert row["passes"] is False


def asyncio_run(awaitable):
    import asyncio

    return asyncio.run(awaitable)


def asyncio_sleep(seconds: float):
    import asyncio

    return asyncio.sleep(seconds)


def asyncio_timeout_error():
    import asyncio

    return asyncio.TimeoutError()
