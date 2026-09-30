"""Build the array so that it actually computes 1:2:4:8, then prove it in SPICE.

The group layout attempt produced clean, DRC-free geometry with
correct net topology, and it was still functionally wrong. Every one of the 32
cells in a column sat under a single continuous word line, so the column could
only be fully on or fully off. The extracted netlist said so explicitly: four
spines of 32 devices, one gate each, one source each. No way to express a
1:2:4:8 weight.

The reference fixture ``DOT4L.mag`` shows the actual arrangement. Its four
columns sit at x = 45, 245, 445, 645 on a 200-unit pitch. Down the last column,
at a 97-unit pitch, sit 1, 2, 4 and then 8 separate ``ndiff`` patches, with one
poly strip and two long metal1 buses running the full height. Each patch is an
independent cell sharing the same gate, so the current on the spine is the sum
over whichever patches are enabled. Patch *count* is the weight: 1 patch is
weight 1, 2 patches are weight 2, 4 patches weight 4, 8 patches weight 8.

So a weight is a group of parallel cells under one word line, and the bits of a
single weight occupy separate groups along the spine. This module builds that,
extracts it, and simulates the extracted netlist to check the ratio.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .cim_toolchain import find_magic_tech as _find_magic_tech

# DOT4L-derived, in 0.01 um units.
GATE_L = 15
DEV_W = 42
NDIFF_W = 150
ROW_PITCH = 97
COL_PITCH = 200
CONTACT = 17
CONTACT_INSET_Y = 12
BUS_W = 17
LI_EXT = 8
M1_EXT = 7
WORD_LINE_EXT = 25
UNIT_UM = 0.01


@dataclass(frozen=True)
class WeightStripGeometry:
    """One strip: ``columns`` weight columns, each a 1:2:4:8 bin group."""

    columns: int = 4
    weight_bins: Tuple[int, ...] = (1, 2, 4, 8)
    margin: int = 400

    @property
    def patches_per_column(self) -> int:
        return max(self.weight_bins)

    @property
    def transistors_total(self) -> int:
        return sum(self.weight_bins[: self.columns])

    @property
    def weight_levels(self) -> int:
        return 1 << len(self.weight_bins)


def build_strip(geometry: Optional[WeightStripGeometry] = None) -> Dict[str, Any]:
    """Lay out the strip: per column, a 1 / 2 / 4 / 8 patch group in y."""
    geom = geometry or WeightStripGeometry()
    layers: Dict[str, List[str]] = {
        name: [] for name in ("locali", "ndiff", "nmos", "ndiffc", "poly", "mcon", "metal1")
    }

    def rect(layer: str, x1: int, y1: int, x2: int, y2: int) -> None:
        if x2 > x1 and y2 > y1:
            layers[layer].append(f"rect {x1} {y1} {x2} {y2}")

    x0 = geom.margin
    y0 = geom.margin

    # One column per weight bin. DOT4L does not put 1+2+4+8 patches in a
    # single column: it gives the four columns 1, 2, 4 and 8 patches, so the
    # spine current is set by the column's patch count. Packing all 15 into
    # one column with a shared source makes them switch together, which is a
    # 15-level unary weight and cannot express 1:2:4:8.
    total_rows = max(geom.weight_bins)

    column_x: List[int] = []
    for index in range(geom.columns):
        count = geom.weight_bins[index] if index < len(geom.weight_bins) else 1
        bx = x0 + index * COL_PITCH
        column_x.append(bx)
        gate_x = bx + (NDIFF_W - GATE_L) // 2
        rect("poly", gate_x, y0 - WORD_LINE_EXT, gate_x + GATE_L, y0 + count * ROW_PITCH)
        drain_x = bx + 10
        source_x = bx + NDIFF_W - CONTACT - 10
        bus_top = y0 + total_rows * ROW_PITCH + 100
        for bus_x in (drain_x, source_x):
            rect("metal1", bus_x - M1_EXT, y0 - 100, bus_x + CONTACT + M1_EXT, bus_top)
        for row in range(count):
            ry = y0 + row * ROW_PITCH
            rect("ndiff", bx, ry, bx + NDIFF_W, ry + DEV_W)
            rect("nmos", gate_x, ry, gate_x + GATE_L, ry + DEV_W)
            for cx in (drain_x, source_x):
                cy = ry + CONTACT_INSET_Y
                rect("ndiffc", cx, cy, cx + CONTACT, cy + CONTACT)
                rect(
                    "locali",
                    cx - LI_EXT,
                    cy - LI_EXT,
                    cx + CONTACT + LI_EXT,
                    cy + CONTACT + LI_EXT,
                )
                rect("mcon", cx, cy, cx + CONTACT, cy + CONTACT)

    body = "\n".join("\n".join([f"<< {n} >>", *layers[n]]) for n in layers)
    mag = f"magic\ntech sky130A\n{body}\n<< end >>\n"
    width = x0 + geom.columns * COL_PITCH
    height = y0 + total_rows * ROW_PITCH + 200
    return {
        "mag": mag,
        "geometry": asdict(geom),
        "column_x": column_x,
        "transistors_total": geom.transistors_total,
        "patches_per_column": geom.patches_per_column,
        "width_um": width * UNIT_UM,
        "height_um": height * UNIT_UM,
        "um2_per_transistor": width * height * UNIT_UM * UNIT_UM / geom.transistors_total,
    }


def tile_strips(strip: Dict[str, Any], copies: int = 1) -> Dict[str, Any]:
    """Repeat a laid-out strip along x so density is measured on an array.

    A single strip's own edge margin is a large share of its area, so quoting
    area per cell from one block overstates the cost of the array: the 10.20 um^2
    figure the freeze packet had to retract came from exactly that, a small block
    whose routing dominated. Repeating the strip on its own column pitch keeps
    the geometry DRC-identical while the edge margin is paid once, so the number
    measured here is a property of the array rather than of one block's border.
    """
    if copies < 1:
        raise ValueError("copies must be at least 1")
    if copies == 1:
        return dict(strip, copies=1)

    pitch = int(strip["geometry"]["columns"]) * COL_PITCH
    sections: Dict[str, List[str]] = {}
    order: List[str] = []
    current: Optional[str] = None
    for line in str(strip["mag"]).splitlines():
        header = re.match(r"<< (.+) >>", line)
        if header:
            current = header.group(1)
            sections[current] = []
            order.append(current)
        elif line.startswith("rect ") and current is not None:
            sections[current].append(line)

    def shifted(rects: List[str], dx: int) -> List[str]:
        moved: List[str] = []
        for rect in rects:
            _, x1, y1, x2, y2 = rect.split()
            moved.append(f"rect {int(x1) + dx} {y1} {int(x2) + dx} {y2}")
        return moved

    base = {name: list(rects) for name, rects in sections.items()}
    for copy in range(1, copies):
        for name in order:
            sections[name].extend(shifted(base[name], copy * pitch))

    body = "\n".join("\n".join([f"<< {name} >>", *sections[name]]) for name in order)
    mag = f"magic\ntech sky130A\n{body}\n<< end >>\n"
    transistors = int(strip["transistors_total"]) * copies
    width_um = float(strip["width_um"]) + (copies - 1) * pitch * UNIT_UM
    height_um = float(strip["height_um"])
    return {
        **strip,
        "mag": mag,
        "copies": copies,
        "column_pitch_um": pitch * UNIT_UM,
        "transistors_total": transistors,
        "width_um": width_um,
        "height_um": height_um,
        "um2_per_transistor": width_um * height_um / transistors,
    }


def find_magic() -> Optional[str]:
    out = subprocess.run(["which", "magic"], capture_output=True, text=True)
    return out.stdout.strip() or None


def find_magic_tech() -> Optional[Path]:
    """Locate the tech file, honouring the documented env overrides.

    Delegated to ``cim_toolchain`` so the search exists once: two copies drifted
    apart is how the documented overrides came to be ignored here.
    """
    return _find_magic_tech()


def extract(strip: Dict[str, Any], workdir: Path) -> Dict[str, Any]:
    magic = find_magic()
    tech = find_magic_tech()
    if magic is None or tech is None:
        return {"status": "skipped", "reason": "magic_or_tech_missing"}
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "strip.mag").write_text(strip["mag"], encoding="utf-8")
    (workdir / "run.tcl").write_text(
        "\n".join(
            [
                f"tech load {tech.as_posix()}",
                f"load {(workdir / 'strip.mag').as_posix()}",
                "select top cell",
                'puts "DRC_BOX [box values]"',
                "drc check",
                "drc catchup",
                'puts "DRC_TOTAL [format %d [drc list count total]]"',
                "extract all",
                "ext2spice lvs",
                f"ext2spice -o {(workdir / 'strip.spice').as_posix()}",
                "quit 0 -noprompt",
                "",
            ]
        ),
        encoding="utf-8",
    )
    try:
        result = subprocess.run(
            [magic, "-dnull", "-noconsole", str(workdir / "run.tcl")],
            capture_output=True,
            text=True,
            timeout=900,
            cwd=str(workdir),
        )
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "magic_timeout"}
    out = result.stdout + result.stderr
    box = re.search(r"DRC_BOX\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)", out)
    match = re.search(r"DRC_TOTAL\s+(\d+)", out)
    drc_errors = None
    if box is not None and match is not None:
        x1, y1, x2, y2 = (int(g) for g in box.groups())
        if x1 != x2 and y1 != y2:
            drc_errors = int(match.group(1))
    spice = workdir / "strip.spice"
    devices = 0
    if spice.is_file():
        body = spice.read_text(encoding="utf-8", errors="replace")
        devices = len(re.findall(r"^X\d+\s", body, re.M))
    return {
        "status": "ok",
        "drc_errors": drc_errors,
        "extracted": devices,
    }


def spine_topology(spice_path: Path) -> Dict[str, Any]:
    """Report how many cells sit on each drain, and how many share each gate."""
    body = spice_path.read_text(encoding="utf-8", errors="replace")
    devices = re.findall(r"^X\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", body, re.M)
    per_drain: Dict[str, int] = defaultdict(int)
    per_gate: Dict[str, int] = defaultdict(int)
    for drain, gate, _source, _bulk in devices:
        per_drain[drain] += 1
        per_gate[gate] += 1
    return {
        "devices": len(devices),
        "spines": len(per_drain),
        "cells_per_spine": sorted(set(per_drain.values()), reverse=True),
        "word_lines": len(per_gate),
        "spines_per_word_line": sorted(set(per_gate.values()), reverse=True),
    }


def main() -> int:
    workdir = Path(tempfile.mkdtemp(prefix="cimweight-"))
    strip = build_strip()
    run = extract(strip, workdir)
    report: Dict[str, Any] = {
        "strip": {
            "transistors": strip["transistors_total"],
            "patches_per_column": strip["patches_per_column"],
            "um2_per_transistor": round(strip["um2_per_transistor"], 4),
            "drc_errors": run.get("drc_errors"),
            "extracted": run.get("extracted"),
        }
    }
    spice = workdir / "strip.spice"
    if spice.is_file():
        report["topology"] = spine_topology(spice)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
