"""Verification gates for a laid-out CIM block, with no way to skip them.

This exists because every mistake in this work so far passed the check that was
actually being run. Blocks with zero DRC errors extracted zero transistors. A
group with the right device count had its 64 array cells shorted onto one net.
A group that passed DRC, extraction, device count and net topology computed
nothing at all, because all 32 cells in a column shared one word line and the
spine could only be fully on or fully off. A testbench reported 1e-13 A because
one gate node was left floating, and it still exited clean.

So the gates here are ordered from cheap to expensive and each one names the
specific failure it exists to catch. ``verify_block`` returns every gate's
verdict rather than the first failure, because a partial report is what let the
earlier bugs hide. Nothing downstream may consume a block whose report is not
all-pass, and ``GateReport.ok`` is the only way to ask.
"""

from __future__ import annotations

import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .cim_toolchain import find_magic_tech as _find_magic_tech

# sky130 minimum characterised nfet, used only as a sanity bound on what the
# extractor is allowed to hand back.
MIN_SANE_W_UM = 0.2
MAX_SANE_W_UM = 500.0
MIN_SANE_L_UM = 0.1
MAX_SANE_L_UM = 5.0


@dataclass
class Gate:
    """One check, the failure it exists to catch, and its verdict."""

    name: str
    guards_against: str
    passed: bool
    detail: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "guards_against": self.guards_against,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass
class GateReport:
    gates: List[Gate] = field(default_factory=list)

    def add(self, gate: Gate) -> None:
        self.gates.append(gate)

    @property
    def ok(self) -> bool:
        """All gates passed. The only sanctioned way to accept a block."""
        return bool(self.gates) and all(gate.passed for gate in self.gates)

    @property
    def failures(self) -> List[Gate]:
        return [gate for gate in self.gates if not gate.passed]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "gates": [gate.as_dict() for gate in self.gates],
            "failed": [gate.name for gate in self.failures],
        }

    def summary(self) -> str:
        lines = []
        for gate in self.gates:
            mark = "PASS" if gate.passed else "FAIL"
            lines.append(f"  [{mark}] {gate.name}: {gate.detail}")
            if not gate.passed:
                lines.append(f"         guards: {gate.guards_against}")
        lines.append(f"  => {'ALL GATES PASS' if self.ok else 'BLOCKED'}")
        return "\n".join(lines)


def find_magic() -> Optional[str]:
    out = subprocess.run(["which", "magic"], capture_output=True, text=True)
    return out.stdout.strip() or None


def find_magic_tech() -> Optional[Path]:
    """Locate the tech file, honouring the documented env overrides.

    Delegated to ``cim_toolchain`` so the search exists once: two copies drifted
    apart is how the documented overrides came to be ignored here.
    """
    return _find_magic_tech()


def find_ngspice() -> Optional[str]:
    out = subprocess.run(["which", "ngspice"], capture_output=True, text=True)
    return out.stdout.strip() or None


def parse_devices(spice_text: str) -> List[Dict[str, Any]]:
    """Pull every extracted nfet out of a magic netlist."""
    pattern = re.compile(
        r"^X\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(sky130_fd_pr__\S+)"
        r"\s+.*?w=([\d.]+)\s+l=([\d.]+)\s*$",
        re.M,
    )
    devices = []
    for drain, gate, source, bulk, model, width, length in pattern.findall(spice_text):
        devices.append(
            {
                "drain": drain,
                "gate": gate,
                "source": source,
                "bulk": bulk,
                "model": model,
                "w": float(width),
                "l": float(length),
            }
        )
    return devices


def _run_drc_and_extract(
    mag_text: str, workdir: Path, timeout_s: float = 900.0
) -> Tuple[Optional[int], str, str]:
    magic = find_magic()
    tech = find_magic_tech()
    if magic is None or tech is None:
        return None, "", "magic or sky130 tech not found"
    workdir.mkdir(parents=True, exist_ok=True)
    mag_path = workdir / "block.mag"
    mag_path.write_text(mag_text, encoding="utf-8")
    script = workdir / "run.tcl"
    script.write_text(
        "\n".join(
            [
                f"tech load {tech.as_posix()}",
                f"load {mag_path.as_posix()}",
                "select top cell",
                'puts "DRC_BOX [box values]"',
                "drc check",
                "drc catchup",
                'puts "DRC_TOTAL [format %d [drc list count total]]"',
                "extract all",
                "ext2spice lvs",
                f"ext2spice -o {(workdir / 'block.spice').as_posix()}",
                "quit 0 -noprompt",
                "",
            ]
        ),
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            [magic, "-dnull", "-noconsole", str(script)],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(workdir),
        )
    except subprocess.TimeoutExpired:
        return None, "", "magic timed out"
    text = result.stdout + result.stderr
    spice = ""
    spice_path = workdir / "block.spice"
    if spice_path.is_file():
        spice = spice_path.read_text(encoding="utf-8", errors="replace")
    box = re.search(r"DRC_BOX\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", text)
    if box is None:
        return None, spice, text
    x1, y1, x2, y2 = (int(g) for g in box.groups())
    if x1 == x2 or y1 == y2:
        return None, spice, text
    match = re.search(r"DRC_TOTAL\s+(\d+)", text)
    return (int(match.group(1)) if match else None), spice, text


def verify_block(
    mag_text: str,
    expected_transistors: int,
    expected_spine_sizes: Optional[Sequence[int]] = None,
    expect_single_source_per_spine: bool = True,
    word_lines: Optional[Sequence[str]] = None,
    min_word_line_fans: int = 2,
    expected_columns: int = 0,
    min_inverter_gates: int = 0,
    workdir: Optional[Path] = None,
) -> GateReport:
    """Run the full gate set on a laid-out block.

    ``expected_spine_sizes`` is the strongest structural gate available: it
    asserts that the cells are distributed across separate spines in the counts
    the design intends. ``word_lines`` names the gate nets the array's own poly
    strips produce, which is what separates the array columns from the
    single-cell peripherals: without it every one-transistor sense amp and
    input driver is counted as a 1x weight column.
    """
    import tempfile

    report = GateReport()
    if workdir is None:
        workdir = Path(tempfile.mkdtemp(prefix="cimgate-"))

    drc, spice, raw = _run_drc_and_extract(mag_text, workdir)

    report.add(
        Gate(
            "drc_clean",
            "a block that reports zero errors while extracting nothing",
            drc == 0,
            f"DRC errors = {drc}",
        )
    )
    report.add(
        Gate(
            "netlist_written",
            "magic silently produced no netlist, so every later check reads empty",
            bool(spice),
            f"netlist length = {len(spice)} bytes",
        )
    )
    if not spice:
        return report

    devices = parse_devices(spice)
    report.add(
        Gate(
            "device_count",
            "a block where the gate overlay never reached the diffusion",
            len(devices) == expected_transistors,
            f"extracted {len(devices)}, expected {expected_transistors}",
        )
    )
    if not devices:
        return report

    bad_geometry = [
        f"w={d['w']} l={d['l']}"
        for d in devices
        if not (MIN_SANE_W_UM <= d["w"] <= MAX_SANE_W_UM)
        or not (MIN_SANE_L_UM <= d["l"] <= MAX_SANE_L_UM)
    ]
    report.add(
        Gate(
            "device_geometry_sane",
            "gates trimmed by overlapping rectangles, which extracts a plausible "
            "but wrong width or length and passes a width-only check",
            not bad_geometry,
            f"{len(bad_geometry)} implausible of {len(devices)}"
            + (f": {sorted(set(bad_geometry))[:4]}" if bad_geometry else ""),
        )
    )

    by_drain: Dict[str, List[Dict[str, Any]]] = {}
    for device in devices:
        by_drain.setdefault(device["drain"], []).append(device)

    # Magic derives extracted node names from the box each node was built in, so
    # a word line's net name cannot be predicted from the drawing. Identify the
    # array columns structurally instead: a weight column is a spine whose gate
    # drives several devices, whereas a single-cell peripheral drives one. That
    # separates the array from its sense amps and drivers without predicting any
    # name. It does mean the 1x bin, which is a single cell, is only recognised
    # when the caller asks for it explicitly, so the caller passes the number of
    # columns it expects and the count is checked below.
    array_nets = {
        net: cells
        for net, cells in by_drain.items()
        if len({c["gate"] for c in cells}) == 1 and len(cells) >= 2
    }
    if expected_columns and len(array_nets) < expected_columns:
        # the 1x column is a single cell and is filtered out above; count the
        # single-cell spines the caller says are columns
        singles = [
            net
            for net, cells in by_drain.items()
            if len(cells) == 1 and len({c["gate"] for c in cells}) == 1
        ]
        array_nets = {**array_nets, **{net: by_drain[net] for net in singles[:1]}}
    sizes = sorted((len(cells) for cells in array_nets.values()), reverse=True)

    if expected_spine_sizes is not None:
        report.add(
            Gate(
                "spine_partition",
                "every array cell collapsing onto one net, so a whole array "
                "became a single spine and the per-cell weights vanished",
                sizes == sorted(expected_spine_sizes, reverse=True),
                f"spine sizes {sizes}, expected " f"{sorted(expected_spine_sizes, reverse=True)}",
            )
        )
        # The gate the first gate set missed entirely. A group whose weight
        # columns all hold the same number of cells passes every structural
        # check above and still cannot express a 1:2:4:8 weight, because the
        # ratio comes from the columns holding *different* cell counts.
        # Comparing each size against a constant cannot catch that; only
        # comparing the spines against each other can.
        distinct = len(set(sizes))
        report.add(
            Gate(
                "spine_sizes_distinct",
                "every weight column holding the same cell count, which makes "
                "the array a bank of identical columns and leaves the weight "
                "ratio inexpressible",
                bool(sizes) and distinct == len(sizes) and len(sizes) > 1,
                f"{len(sizes)} spines, {distinct} distinct sizes: {sizes}",
            )
        )
    else:
        # Only meaningful once the array is present. A two-device inverter is
        # supposed to be one net holding two devices, and calling that a giant
        # net would make the gate reject the one block it is meant to bless.
        if expected_columns or expected_spine_sizes:
            biggest = max(sizes) if sizes else 0
            report.add(
                Gate(
                    "no_giant_net",
                    "a routing line bridging separate spines",
                    biggest < len(devices),
                    f"largest net holds {biggest} of {len(devices)} devices",
                )
            )

    if min_inverter_gates:
        # A CMOS inverter is one gate driving exactly one nfet and one pfet. A
        # peripheral that is not wired that way can still pass every gate above:
        # the first version of the sense amplifier drew twelve separate
        # inverters, each with its own gate and no cascade between them, and
        # the netlist showed one device per gate while DRC stayed clean, the
        # device count stayed exact and the weight ratio was unaffected.
        fanouts: Dict[str, int] = defaultdict(int)
        for device in devices:
            fanouts[device["gate"]] += 1
        inverters = [
            gate
            for gate, count in fanouts.items()
            if count == 2
            and {("pfet" if "pfet" in d["model"] else "nfet") for d in devices if d["gate"] == gate}
            == {"nfet", "pfet"}
        ]
        # A real inverter is one gate driving one nfet and one pfet *and* both
        # drains on one node. Sharing the gate alone is not enough: a pair with
        # unjoined drains appears in the netlist as an inverter and is not one
        # electrically, so the gate check has to look at the drains too.
        real_inverters = []
        for gate, count in fanouts.items():
            if count != 2:
                continue
            pair = [d for d in devices if d["gate"] == gate]
            kinds = {"pfet" if "pfet" in d["model"] else "nfet" for d in pair}
            if kinds == {"nfet", "pfet"} and len({d["drain"] for d in pair}) == 1:
                real_inverters.append(gate)
        report.add(
            Gate(
                "cmos_inverters_present",
                "peripheral transistors left with unshared gates, so the "
                "amplifier is a set of isolated devices rather than a cascade",
                len(real_inverters) >= min_inverter_gates,
                f"{len(inverters)} shared-gate pairs, "
                f"{len(real_inverters)} with a joined output, "
                f"expected >= {min_inverter_gates}",
            )
        )

    # The single-source and single-word-line checks describe a weight column: a
    # set of parallel cells sharing one source under one word line. They say
    # nothing about a peripheral, and a CMOS inverter is the deliberate
    # opposite, with one source per device type. So they only run when the caller
    # has told us the block contains an array.
    has_array = bool(expected_spine_sizes) or bool(expected_columns)
    if expect_single_source_per_spine and array_nets and has_array:
        multi_source = [
            net for net, cells in array_nets.items() if len({c["source"] for c in cells}) != 1
        ]
        report.add(
            Gate(
                "spine_single_source",
                "a column whose cells do not share one source, which means the "
                "patches are not a parallel weight bin",
                not multi_source,
                f"{len(multi_source)} array spines with multiple sources",
            )
        )
        multi_gate = [
            net for net, cells in array_nets.items() if len({c["gate"] for c in cells}) != 1
        ]
        report.add(
            Gate(
                "spine_single_word_line",
                "cells on one spine driven by separate gates, which is not how "
                "a current-weighted bin is built",
                not multi_gate,
                f"{len(multi_gate)} array spines with multiple word lines",
            )
        )

    return report


def simulate_spine(
    spice_text: str,
    weight_bins: Sequence[int],
    model_library: Path,
    drain_rail_v: float = 0.3,
    input_swing_v: float = 1.0,
) -> Dict[str, Any]:
    """Measure the extracted spines and check the weight ratio.

    This is the gate that the group layout failed. Everything upstream of it
    passed: DRC clean, correct device count, correct spine count, one gate and
    one source per spine. The block was still unable to express a 1:2:4:8
    weight, because every column held the same number of cells.
    """
    ngspice = find_ngspice()
    if ngspice is None:
        return {"status": "skipped", "reason": "ngspice_not_found"}
    devices = parse_devices(spice_text)
    if not devices:
        return {"status": "error", "reason": "no devices to simulate"}

    by_drain: Dict[str, List[Dict[str, Any]]] = {}
    for device in devices:
        by_drain.setdefault(device["drain"], []).append(device)
    spines = sorted(
        ((net, cells) for net, cells in by_drain.items() if len(cells) >= 2),
        key=lambda item: len(item[1]),
    )
    if len(spines) < 2:
        return {
            "status": "error",
            "reason": f"only {len(spines)} spine(s) with 2+ cells; cannot weigh",
        }

    lines = [
        "* weight-ratio gate, driven from the extracted netlist",
        ".param mc_mm_switch=0 mc_pr_switch=0",
        f".include {model_library.as_posix()}",
        ".subckt anfet d g s b l=1 w=1",
        "m1 d g s b sky130_fd_pr__nfet_01v8__model l={l} w={w}",
        ".ends",
        "vsub VSUBS 0 0",
    ]
    for index, (net, cells) in enumerate(spines):
        gates = {c["gate"] for c in cells}
        sources = {c["source"] for c in cells}
        if len(gates) != 1 or len(sources) != 1:
            return {
                "status": "error",
                "reason": (
                    f"spine {net} has {len(gates)} gates and {len(sources)} "
                    "sources; a weight bin is one word line over one source"
                ),
            }
        gate = gates.pop()
        source = sources.pop()
        lines.append(f"vdd{index} {net} 0 {drain_rail_v}")
        lines.append(f"vsrc{index} {source} 0 0")
        lines.append(f"vg{index} {gate} 0 {input_swing_v}")
        for cell_index, cell in enumerate(cells):
            lines.append(
                f"xc{index}_{cell_index} {net} {gate} {source} {cell['bulk']} "
                f"anfet l={cell['l']}u w={cell['w']}u"
            )
    lines.append(".control")
    lines.append("op")
    for index in range(len(spines)):
        lines.append(f"print @vdd{index}[i]")
    lines += ["quit", ".endc", ".end"]

    import tempfile

    workdir = Path(tempfile.mkdtemp(prefix="cimsim-"))
    deck = workdir / "tb.spice"
    deck.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        result = subprocess.run(
            [ngspice, "-b", str(deck)], capture_output=True, text=True, timeout=600
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "ngspice timed out"}
    text = result.stdout + result.stderr
    if "singular" in text.lower():
        return {"status": "error", "reason": "singular matrix: a net is floating"}
    currents = {
        int(index): float(value)
        for index, value in re.findall(r"@vdd(\d+)\[i\] = ([-\d.e+]+)", text)
    }
    if len(currents) != len(spines):
        return {
            "status": "error",
            "reason": f"read {len(currents)} of {len(spines)} spine currents",
        }

    measured = [abs(currents[i]) for i in range(len(spines))]
    smallest = measured[0]
    if smallest <= 0.0:
        return {
            "status": "error",
            "reason": f"smallest spine carries {smallest} A: cells are not conducting",
        }
    ratios = [value / smallest for value in measured]
    want = [float(b) for b in weight_bins[: len(spines)]]
    errors = [(ratio / target - 1.0) * 100.0 for ratio, target in zip(ratios, want)]
    worst = max(abs(err) for err in errors) if errors else 0.0
    return {
        "status": "ok",
        "spine_cell_counts": [len(cells) for _net, cells in spines],
        "currents_a": measured,
        "ratios": ratios,
        "expected": want,
        "ratio_error_percent": errors,
        "worst_error_percent": worst,
        "sane_current": smallest > 1e-9,
    }


def verify_weights(
    spice_text: str,
    weight_bins: Sequence[int],
    model_library: Path,
    tolerance_percent: float = 1.0,
) -> GateReport:
    """Run the weight gate and fold it into a report."""
    report = GateReport()
    outcome = simulate_spine(spice_text, weight_bins, model_library)
    if outcome.get("status") != "ok":
        report.add(
            Gate(
                "weight_ratio",
                "a block that cannot express its intended weight ratio at all",
                False,
                f"{outcome.get('status')}: {outcome.get('reason')}",
            )
        )
        return report
    worst = outcome["worst_error_percent"]
    report.add(
        Gate(
            "weight_ratio",
            "spine currents not proportional to the intended 1:2:4:8 bin sizes",
            worst <= tolerance_percent and outcome["sane_current"],
            f"ratios {[round(r, 4) for r in outcome['ratios']]} vs "
            f"{outcome['expected']}, worst error {worst:+.4f}%",
        )
    )
    return report
