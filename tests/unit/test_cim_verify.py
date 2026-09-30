# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Verification gates for laid-out sky130 CIM blocks.

A verification suite that has only ever seen a good block proves nothing. Every
gate here is exercised against a block that is known to be broken in exactly the
way that gate exists to catch, because that is the failure mode this project
kept hitting: a block that reported clean on every check that was actually being
run, and was still functionally dead.

The layout files that were removed
----------------------------------
Four modules were deleted because they were laid out before the cell spec was
understood and before the routing could be verified end to end:

* ``cim_cell_layout``: a 32-cell fixture whose 10.20 um^2 per cell was a
  small-block artefact, carried forward as if it were a property of the
  topology. Superseded by the dense array measurement.
* ``cim_array_layout``: a dense 1T array. The spec is 2T select+weight, so the
  cell was wrong even though the density measurement was real.
* ``cim_group_layout``: a whole group whose sense chain never cascaded. Four
  tests stayed red because the 1x weight column and the sense devices shared
  nets.
* ``cim_sense_chain``: a sense chain that never decoded. Roughly ten wiring
  faults, each of which produced a plausible-looking result.

What is kept
------------
* ``cim_primitives``: the verified building blocks, one diffusion patch per
  device, a pfet that needs its n-well and its mcon cuts, and a CMOS inverter
  with one shared gate and one joined output.
* ``cim_weight_strip``: the 1:2:4:8 weight strip, verified on the extracted
  netlist to 0.0001%.
* ``cim_verify``: the gate set, each gate proven able to fail.
"""

import shutil
from pathlib import Path

import pytest

from apps.backend.src.ai.hardware import cim_toolchain, cim_verify, cim_weight_strip
from apps.backend.src.ai.hardware.cim_primitives import Canvas
from apps.backend.src.ai.hardware.cim_toolchain import MODEL_LIBRARY
from apps.backend.src.ai.hardware.cim_verify import (
    Gate,
    GateReport,
    parse_devices,
    simulate_spine,
    verify_block,
    verify_weights,
)
from apps.backend.src.ai.hardware.cim_weight_strip import build_strip, extract

MAGIC = shutil.which("magic")
NGSPICE = shutil.which("ngspice")
needs_magic = pytest.mark.skipif(MAGIC is None, reason="magic not installed")
needs_sim = pytest.mark.skipif(
    MAGIC is None or NGSPICE is None or not MODEL_LIBRARY.is_file(),
    reason="needs magic, ngspice and the flattened model library",
)


def gate_named(report, name):
    for gate in report.gates:
        if gate.name == name:
            return gate
    raise AssertionError(f"gate {name} was never run; gates: {[g.name for g in report.gates]}")


class TestParseDevices:
    def test_reads_geometry_and_nets(self) -> None:
        text = (
            "X0 a_1# a_2# a_3# VSUBS sky130_fd_pr__nfet_01v8 "
            "ad=0.28 pd=2.2 as=0.28 ps=2.1 w=0.42 l=0.15\n"
        )
        devices = parse_devices(text)
        assert len(devices) == 1
        assert devices[0]["drain"] == "a_1#"
        assert devices[0]["w"] == 0.42
        assert devices[0]["l"] == 0.15

    def test_ignores_lines_without_the_model(self) -> None:
        assert parse_devices("* comment\n.subckt x\n.ends\n") == []


class TestGatesRejectKnownBadBlocks:
    """Each block below is broken in one specific way and must be caught."""

    def test_empty_mag_is_blocked(self, tmp_path: Path) -> None:
        empty = "magic\ntech sky130A\n<< ndiff >>\n<< end >>\n"
        report = verify_block(empty, expected_transistors=4, workdir=tmp_path)
        assert not report.ok
        assert not gate_named(report, "netlist_written").passed
        assert "device_count" not in [g.name for g in report.gates]

    @needs_magic
    def test_drc_gate_reads_a_nonzero_count(self, monkeypatch, tmp_path: Path) -> None:
        """The gate must be able to fail, not just pass.

        A hand-built minimal cell never trips sky130 DRC because the tap
        hierarchy is absent, so this drives the reader with a known count and
        checks the gate reports the failure. Without this, a gate that always
        returns 0 errors would look identical to a clean block.
        """
        from apps.backend.src.ai.hardware import cim_verify

        monkeypatch.setattr(
            cim_verify,
            "_run_drc_and_extract",
            lambda *a, **k: (7, "* x\n", "DRC_TOTAL 7"),
        )
        report = cim_verify.verify_block("magic\n", 0, workdir=tmp_path)
        drc = gate_named(report, "drc_clean")
        assert drc.passed is False
        assert "7" in drc.detail

    def test_drc_gate_reports_none_when_magic_is_silent(self, monkeypatch, tmp_path):
        from apps.backend.src.ai.hardware import cim_verify

        monkeypatch.setattr(
            cim_verify, "_run_drc_and_extract", lambda *a, **k: (None, "", "no count")
        )
        report = cim_verify.verify_block("magic\n", 0, workdir=tmp_path)
        assert gate_named(report, "drc_clean").passed is False

    @needs_magic
    def test_geometry_sanity_catches_a_trimmed_gate(self, tmp_path: Path) -> None:
        mag = (
            "magic\ntech sky130A\n<< ndiff >>\n"
            "rect 400 400 550 442\n"
            "<< nmos >>\n"
            "rect 470 400 471 442\n"
            "<< ndiffc >>\n"
            "rect 410 410 427 427\n"
            "rect 520 410 537 427\n"
            "<< end >>\n"
        )
        report = verify_block(mag, expected_transistors=1, workdir=tmp_path)
        names = [g.name for g in report.gates]
        if "device_geometry_sane" not in names:
            pytest.skip("magic refused to extract a sub-minimum gate")
        assert not gate_named(report, "device_geometry_sane").passed


class TestPrimitives:
    @needs_magic
    def test_nfet_extracts(self, tmp_path: Path) -> None:
        canvas = Canvas()
        canvas.nmos(1000, 500)
        report = verify_block(canvas.to_mag(), expected_transistors=1, workdir=tmp_path)
        assert report.ok, report.summary()
        devices = parse_devices((tmp_path / "block.spice").read_text())
        assert devices[0]["model"] == "sky130_fd_pr__nfet_01v8"
        assert devices[0]["w"] == 0.42
        assert devices[0]["l"] == 0.15

    @needs_magic
    def test_pfet_in_an_nwell_extracts(self, tmp_path: Path) -> None:
        """A pfet does not compose from poly over pdiff alone.

        ``compose pfet poly pdiff`` appears in sky130A.tech, so drawing poly over
        pdiff should be enough. Extracted, it yields nothing at all. Adding an
        ``nwell`` rectangle around the same geometry extracts one pfet.
        """
        canvas = Canvas()
        canvas.pfet(1000, 500)
        report = verify_block(canvas.to_mag(), expected_transistors=1, workdir=tmp_path)
        assert report.ok, report.summary()
        devices = parse_devices((tmp_path / "block.spice").read_text())
        assert devices[0]["model"] == "sky130_fd_pr__pfet_01v8"
        assert devices[0]["w"] == 0.42
        assert devices[0]["l"] == 0.15

    @needs_magic
    def test_inverter_pair_extracts_both_device_types(self, tmp_path: Path) -> None:
        canvas = Canvas()
        canvas.inverter(1000, 500)
        report = verify_block(
            canvas.to_mag(), expected_transistors=2, min_inverter_gates=1, workdir=tmp_path
        )
        assert report.ok, report.summary()
        models = {d["model"] for d in parse_devices((tmp_path / "block.spice").read_text())}
        assert any("nfet" in m for m in models)
        assert any("pfet" in m for m in models)

    @needs_magic
    def test_a_pfet_drain_needs_its_own_mcon(self, tmp_path: Path) -> None:
        """A pfet contact without the mcon cut is not a node.

        The mcon sits under every diffusion contact in DOT4L and under the
        nfet here. Leaving it off the pfet left the pfet's drain without a cut,
        so the metal1 bus above it connected to nothing: the pair extracted as
        a shared gate with two floating drains. Device count, device geometry,
        DRC and the shared-gate check all passed, because the devices were both
        present and plausible. Only a check on the joined output catches it.
        """
        canvas = Canvas()
        canvas.inverter(1000, 500)
        mag = canvas.to_mag()
        stripped = mag.replace("rect 1270 512 1287 529\n", "").replace(
            "rect 1383 512 1400 529\n", ""
        )
        good = verify_block(mag, expected_transistors=2, min_inverter_gates=1, workdir=tmp_path)
        assert good.ok, good.summary()
        bad_dir = tmp_path / "stripped"
        bad_dir.mkdir()
        report = verify_block(
            stripped, expected_transistors=2, min_inverter_gates=1, workdir=bad_dir
        )
        if not report.gates:
            pytest.skip("magic refused the stripped geometry outright")
        assert not report.ok
        assert not gate_named(report, "cmos_inverters_present").passed

    @needs_magic
    def test_inverters_do_not_merge_wells(self, tmp_path: Path) -> None:
        """Two inverters closer than one pitch share a well and lose a device.

        The failure is invisible in the drawn tile count: the rectangles are
        distinct, so the layout looks right, but magic merges the two gates and
        extracts one transistor per shared channel instead of two.
        """
        canvas = Canvas()
        canvas.inverter(1000, 500)
        canvas.inverter(1200, 500)
        report = verify_block(
            canvas.to_mag(), expected_transistors=4, min_inverter_gates=2, workdir=tmp_path
        )
        assert not report.ok


class TestWeightStrip:
    @needs_magic
    def test_strip_extracts_every_cell(self, tmp_path: Path) -> None:
        strip = build_strip()
        run = extract(strip, tmp_path)
        assert run["drc_errors"] == 0
        assert run["extracted"] == strip["transistors_total"] == 15

    @needs_magic
    def test_strip_topology_has_four_distinct_spines(self, tmp_path: Path) -> None:
        strip = build_strip()
        extract(strip, tmp_path)
        report = verify_block(
            strip["mag"],
            expected_transistors=strip["transistors_total"],
            expected_spine_sizes=sorted(strip["geometry"]["weight_bins"], reverse=True),
            expected_columns=4,
            workdir=tmp_path,
        )
        assert report.ok, report.summary()

    @needs_sim
    def test_weight_ratio_on_the_extracted_netlist(self, tmp_path: Path) -> None:
        strip = build_strip()
        extract(strip, tmp_path)
        report = verify_weights(
            (tmp_path / "strip.spice").read_text(),
            strip["geometry"]["weight_bins"],
            MODEL_LIBRARY,
        )
        assert report.ok, report.summary()
        outcome = simulate_spine(
            (tmp_path / "strip.spice").read_text(),
            strip["geometry"]["weight_bins"],
            MODEL_LIBRARY,
        )
        assert outcome["worst_error_percent"] < 1.0
        assert outcome["sane_current"] is True


class TestReportIsHonest:
    def test_summary_names_the_failure_and_its_guard(self) -> None:
        report = GateReport()
        report.add(Gate("a", "the thing it catches", False, "detail"))
        text = report.summary()
        assert "FAIL" in text
        assert "the thing it catches" in text
        assert "BLOCKED" in text
        assert report.ok is False

    def test_empty_report_is_not_ok(self) -> None:
        assert GateReport().ok is False

    def test_verify_weights_reports_a_failure_reason(self) -> None:
        report = verify_weights("", [1, 2], MODEL_LIBRARY)
        assert not report.ok
        assert report.failures[0].name == "weight_ratio"


class TestDocumentedToolOverrides:
    """The knobs .env.example writes down have to actually be read.

    Both settings were documented as enabling layout DRC and extraction while
    nothing in the code looked at them, so an operator could point the tooling at
    their own PDK, watch it silently ignore the path, and only find out when DRC
    reported a skip.
    """

    def test_magic_tech_override_is_honoured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tech = tmp_path / "sky130A.tech"
        tech.write_text("* stub tech\n", encoding="utf-8")
        monkeypatch.setenv("ANGELA_SKY130_MAGIC_TECH", str(tech))

        assert cim_toolchain.find_magic_tech() == tech
        # every caller has to see it, not just the module that resolves it
        assert cim_verify.find_magic_tech() == tech
        assert cim_weight_strip.find_magic_tech() == tech

    def test_volare_root_is_searched(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANGELA_SKY130_MAGIC_TECH", raising=False)
        versions = tmp_path / "versions"
        nested = versions / "c6d73a35" / "sky130A/libs.tech/magic"
        nested.mkdir(parents=True)
        tech = nested / "sky130A.tech"
        tech.write_text("* stub tech\n", encoding="utf-8")
        monkeypatch.setenv("VOLARE_ROOT", str(versions))

        assert cim_toolchain.find_magic_tech() == tech

    def test_a_configured_path_that_does_not_exist_is_not_returned(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        missing = tmp_path / "missing.tech"
        monkeypatch.setenv("ANGELA_SKY130_MAGIC_TECH", str(missing))
        monkeypatch.setenv("VOLARE_ROOT", str(tmp_path / "no-such-volare"))

        # A wrong override falls back to auto-discovery rather than being handed
        # on as a path magic would fail to load.
        resolved = cim_toolchain.find_magic_tech()
        assert resolved != missing
        assert resolved is None or resolved.is_file()
