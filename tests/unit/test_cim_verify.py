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
import subprocess
from pathlib import Path
from types import SimpleNamespace

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


class TestGateAndReportSerialization:
    """Gate/GateReport must round-trip: the report is the contract consumers read."""

    def test_gate_as_dict_exposes_every_field(self) -> None:
        gate = Gate("drc_clean", "silent empty extraction", False, "DRC errors = 3")
        assert gate.as_dict() == {
            "name": "drc_clean",
            "guards_against": "silent empty extraction",
            "passed": False,
            "detail": "DRC errors = 3",
        }

    def test_report_as_dict_lists_failed_gate_names(self) -> None:
        report = GateReport()
        report.add(Gate("a", "x", True, "ok"))
        report.add(Gate("b", "y", False, "no"))
        payload = report.as_dict()
        assert payload["ok"] is False
        assert [gate["name"] for gate in payload["gates"]] == ["a", "b"]
        assert payload["failed"] == ["b"]
        assert len(report.failures) == 1 and report.failures[0].name == "b"

    def test_report_summary_marks_failed_gates_with_their_guard(self) -> None:
        report = GateReport()
        report.add(Gate("a", "x", True, "ok"))
        report.add(Gate("b", "the thing that broke", False, "no"))
        text = report.summary()
        assert "[PASS] a" in text
        assert "[FAIL] b" in text
        assert "guards: the thing that broke" in text
        assert "BLOCKED" in text

    def test_empty_report_is_never_ok(self) -> None:
        assert GateReport().ok is False


class TestRunDrcAndExtractBranches:
    """The magic runner must distinguish every failure shape, not just success."""

    @staticmethod
    def _fake_magic(monkeypatch: pytest.MonkeyPatch, stdout: str) -> list[str]:
        commands: list[str] = []

        def run(cmd, capture_output, text, timeout, cwd):  # noqa: ANN001
            commands.append(cmd[-1])
            return SimpleNamespace(stdout=stdout, stderr="")

        monkeypatch.setattr(cim_verify, "find_magic", lambda: "/usr/bin/magic")
        monkeypatch.setattr(
            cim_verify,
            "subprocess",
            SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired),
        )
        return commands

    def test_magic_timeout_is_reported_verbatim(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setattr(cim_verify, "find_magic", lambda: "/usr/bin/magic")

        def run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="magic", timeout=900)

        monkeypatch.setattr(
            cim_verify,
            "subprocess",
            SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired),
        )
        drc, spice, raw = cim_verify._run_drc_and_extract("<< end >>", tmp_path)
        assert (drc, spice, raw) == (None, "", "magic timed out")

    def test_missing_drc_box_returns_raw_output_and_any_netlist(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "block.spice").write_text("* extracted netlist\n", encoding="utf-8")
        self._fake_magic(monkeypatch, "drc said something unrelated")
        drc, spice, raw = cim_verify._run_drc_and_extract("<< end >>", tmp_path)
        assert drc is None
        assert spice == "* extracted netlist\n"
        assert raw == "drc said something unrelated"

    def test_degenerate_drc_box_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._fake_magic(monkeypatch, "DRC_BOX 0 0 0 100\nDRC_TOTAL 0")
        drc, _spice, _raw = cim_verify._run_drc_and_extract("<< end >>", tmp_path)
        assert drc is None

    def test_well_formed_drc_output_is_parsed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        (tmp_path / "block.spice").write_text("* netlist\n", encoding="utf-8")
        self._fake_magic(monkeypatch, "DRC_BOX 0 0 100 100\nDRC_TOTAL 2")
        drc, spice, raw = cim_verify._run_drc_and_extract("<< end >>", tmp_path)
        assert drc == 2
        assert spice == "* netlist\n"
        assert "DRC_TOTAL 2" in raw


class TestSpineGateWithFakeNgspice:
    """The weight-ratio gate is the one that failed last; every branch is pinned.

    ngspice itself is stubbed at the module's own subprocess binding, so the
    deck construction, output parsing and ratio math are all exercised without
    a simulator and without touching the shared stdlib module.
    """

    @staticmethod
    def _device(index: int, drain: str, gate: str, source: str) -> str:
        return (
            f"X{index} {drain} {gate} {source} VSUBS "
            f"sky130_fd_pr__nfet_01v8 w=1.0 l=0.15\n"
        )

    @staticmethod
    def _install_fake_ngspice(
        monkeypatch: pytest.MonkeyPatch, stdout: str
    ) -> list[Path]:
        decks: list[Path] = []

        def run(cmd, capture_output, text, timeout):  # noqa: ANN001
            decks.append(Path(cmd[2]))
            return SimpleNamespace(stdout=stdout, stderr="")

        monkeypatch.setattr(cim_verify, "find_ngspice", lambda: "/usr/bin/ngspice")
        monkeypatch.setattr(
            cim_verify,
            "subprocess",
            SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired),
        )
        return decks

    def test_no_devices_is_an_error_not_a_skip(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "")
        outcome = simulate_spine("* nothing", (1, 2), tmp_path)
        assert outcome == {"status": "error", "reason": "no devices to simulate"}

    def test_a_single_spine_cannot_be_weighed(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "")
        netlist = self._device(0, "SP", "G", "S") + self._device(1, "SP", "G", "S")
        outcome = simulate_spine(netlist, (1, 2), tmp_path)
        assert outcome["status"] == "error"
        assert "only 1 spine(s) with 2+ cells" in outcome["reason"]

    def test_spine_with_mixed_word_lines_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "")
        netlist = (
            self._device(0, "SP1", "G0", "S1")
            + self._device(1, "SP1", "G1", "S1")
            + self._device(2, "SP2", "G2", "S2")
            + self._device(3, "SP2", "G2", "S2")
            + self._device(4, "SP2", "G2", "S2")
        )
        outcome = simulate_spine(netlist, (1, 2), tmp_path)
        assert outcome["status"] == "error"
        assert "spine SP1 has 2 gates" in outcome["reason"]

    def test_ratio_gate_measures_the_binary_ladder(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        netlist = (
            self._device(0, "SP1", "G0", "S1")
            + self._device(1, "SP1", "G0", "S1")
            + self._device(2, "SP2", "G1", "S2")
            + self._device(3, "SP2", "G1", "S2")
            + self._device(4, "SP2", "G1", "S2")
            + self._device(5, "SP2", "G1", "S2")
        )
        stdout = "@vdd0[i] = 1.0e-06\n@vdd1[i] = 2.0e-06\n"
        decks = self._install_fake_ngspice(monkeypatch, stdout)
        library = tmp_path / "models.spice"
        library.write_text("* model library\n", encoding="utf-8")

        outcome = simulate_spine(netlist, (1, 2, 4, 8), library)

        assert outcome["status"] == "ok"
        assert outcome["spine_cell_counts"] == [2, 4]
        assert outcome["currents_a"] == [1.0e-06, 2.0e-06]
        assert outcome["ratios"] == [1.0, 2.0]
        assert outcome["expected"] == [1.0, 2.0]
        assert outcome["worst_error_percent"] == 0.0
        assert outcome["sane_current"] is True

        # The generated deck must really drive the extracted spines.
        deck = decks[0].read_text(encoding="utf-8")
        assert ".include " + library.as_posix() in deck
        assert ".subckt anfet d g s b l=1 w=1" in deck
        assert "vdd0 SP1 0 0.3" in deck
        assert "vg0 G0 0 1.0" in deck
        assert "vsrc0 S1 0 0" in deck
        assert "print @vdd0[i]" in deck

    def test_ngspice_timeout_is_reported(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        def run(*_args, **_kwargs):
            raise subprocess.TimeoutExpired(cmd="ngspice", timeout=600)

        monkeypatch.setattr(cim_verify, "find_ngspice", lambda: "/usr/bin/ngspice")
        monkeypatch.setattr(
            cim_verify,
            "subprocess",
            SimpleNamespace(run=run, TimeoutExpired=subprocess.TimeoutExpired),
        )
        netlist = (
            self._device(0, "SP1", "G1", "S1")
            + self._device(1, "SP1", "G1", "S1")
            + self._device(2, "SP2", "G2", "S2")
            + self._device(3, "SP2", "G2", "S2")
        )
        outcome = simulate_spine(netlist, (1, 2), tmp_path)
        assert outcome == {"status": "error", "reason": "ngspice timed out"}

    def test_a_singular_matrix_names_the_floating_net_problem(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "Error: singular matrix")
        netlist = (
            self._device(0, "SP1", "G1", "S1")
            + self._device(1, "SP1", "G1", "S1")
            + self._device(2, "SP2", "G2", "S2")
            + self._device(3, "SP2", "G2", "S2")
        )
        outcome = simulate_spine(netlist, (1, 2), tmp_path)
        assert outcome["status"] == "error"
        assert "singular matrix" in outcome["reason"]

    def test_missing_spine_currents_are_an_error(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "@vdd0[i] = 1.0e-06\n")
        netlist = (
            self._device(0, "SP1", "G1", "S1")
            + self._device(1, "SP1", "G1", "S1")
            + self._device(2, "SP2", "G2", "S2")
            + self._device(3, "SP2", "G2", "S2")
        )
        outcome = simulate_spine(netlist, (1, 2), tmp_path)
        assert outcome == {
            "status": "error",
            "reason": "read 1 of 2 spine currents",
        }

    def test_a_dead_spine_is_not_a_weight(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "@vdd0[i] = 0.0\n@vdd1[i] = 1.0e-06\n")
        netlist = (
            self._device(0, "SP1", "G1", "S1")
            + self._device(1, "SP1", "G1", "S1")
            + self._device(2, "SP2", "G2", "S2")
            + self._device(3, "SP2", "G2", "S2")
        )
        outcome = simulate_spine(netlist, (1, 2), tmp_path)
        assert outcome["status"] == "error"
        assert "smallest spine carries 0.0 A" in outcome["reason"]

    def test_verify_weights_passes_an_exact_binary_response(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        netlist = (
            self._device(0, "SP1", "G0", "S1")
            + self._device(1, "SP1", "G0", "S1")
            + self._device(2, "SP2", "G1", "S2")
            + self._device(3, "SP2", "G1", "S2")
            + self._device(4, "SP2", "G1", "S2")
            + self._device(5, "SP2", "G1", "S2")
        )
        self._install_fake_ngspice(monkeypatch, "@vdd0[i] = 1.0e-06\n@vdd1[i] = 2.0e-06\n")
        report = verify_weights(netlist, (1, 2, 4, 8), tmp_path)
        assert report.ok is True
        gate = gate_named(report, "weight_ratio")
        assert gate.passed is True
        assert "worst error +0.0000%" in gate.detail

    def test_verify_weights_fails_a_non_binary_response(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        netlist = (
            self._device(0, "SP1", "G0", "S1")
            + self._device(1, "SP1", "G0", "S1")
            + self._device(2, "SP2", "G1", "S2")
            + self._device(3, "SP2", "G1", "S2")
            + self._device(4, "SP2", "G1", "S2")
            + self._device(5, "SP2", "G1", "S2")
        )
        self._install_fake_ngspice(monkeypatch, "@vdd0[i] = 1.0e-06\n@vdd1[i] = 3.0e-06\n")
        report = verify_weights(netlist, (1, 2, 4, 8), tmp_path)
        gate = gate_named(report, "weight_ratio")
        assert gate.passed is False
        assert "vs [1.0, 2.0], worst error +50.0000%" in gate.detail

    def test_verify_weights_folds_a_failed_outcome_into_the_report(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        self._install_fake_ngspice(monkeypatch, "")
        report = verify_weights("* no devices", (1, 2), tmp_path)
        assert report.ok is False
        gate = gate_named(report, "weight_ratio")
        assert gate.passed is False
        assert gate.detail == "error: no devices to simulate"


class TestCanvasRejectsDegenerateRectangles:
    """A zero-area rect must be dropped, not emitted as an invalid magic rect."""

    def test_zero_area_rect_is_ignored(self) -> None:
        canvas = Canvas()
        canvas.rect("ndiff", 10, 10, 10, 20)
        canvas.rect("ndiff", 10, 10, 20, 10)
        canvas.rect("ndiff", 20, 20, 10, 10)
        assert canvas.layers["ndiff"] == []

    def test_positive_area_rect_is_kept(self) -> None:
        canvas = Canvas()
        canvas.rect("ndiff", 10, 10, 20, 30)
        assert canvas.layers["ndiff"] == ["rect 10 10 20 30"]


class TestFindMagicTechEnvOverride:
    """find_magic_tech must honour a real override and reject a fake one."""

    def test_existing_override_is_returned_verbatim(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tech = tmp_path / "sky130A.tech"
        tech.write_text("* tech\n", encoding="utf-8")
        monkeypatch.setenv(cim_toolchain.MAGIC_TECH_ENV, str(tech))
        assert cim_toolchain.find_magic_tech() == tech

    def test_no_candidates_anywhere_returns_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(cim_toolchain.MAGIC_TECH_ENV, raising=False)
        monkeypatch.setenv(cim_toolchain.VOLARE_ROOT_ENV, str(tmp_path / "empty"))
        monkeypatch.setattr(
            cim_toolchain, "DEFAULT_VOLARE_VERSIONS", tmp_path / "no-versions"
        )
        assert cim_toolchain.find_magic_tech() is None
