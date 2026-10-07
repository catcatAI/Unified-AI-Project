# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Tests for the CIM weight-strip generator and its magic toolchain glue.

The strip geometry is pure computation and must stay so: these tests pin the
binary-weight layout, the tiling arithmetic and every toolchain branch that
decides between "ran", "skipped" and "timed out", without requiring the magic
layout tool to be installed.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import ai.hardware.cim_weight_strip as weight_strip
import pytest
from ai.hardware.cim_weight_strip import (
    WeightStripGeometry,
    build_strip,
    extract,
    main,
    spine_topology,
    tile_strips,
)

# -----------------------------------------------------------------------------
# geometry properties
# -----------------------------------------------------------------------------


def test_weight_levels_is_the_full_binary_ladder() -> None:
    geometry = WeightStripGeometry()
    assert geometry.weight_levels == 16
    assert geometry.patches_per_column == max(geometry.weight_bins)
    assert geometry.transistors_total == sum(geometry.weight_bins[: geometry.columns])


def test_build_strip_lays_out_a_rect_for_every_patch_row() -> None:
    strip = build_strip()
    assert strip["transistors_total"] > 0
    assert strip["um2_per_transistor"] > 0
    mag = str(strip["mag"])
    assert "<< metal1 >>" in mag
    assert "rect " in mag


# -----------------------------------------------------------------------------
# tile_strips
# -----------------------------------------------------------------------------


def test_tile_rejects_non_positive_copies() -> None:
    with pytest.raises(ValueError, match="copies must be at least 1"):
        tile_strips(build_strip(), 0)


def test_tile_single_copy_is_an_annotated_shallow_copy() -> None:
    strip = build_strip()
    tiled = tile_strips(strip, 1)
    assert tiled["copies"] == 1
    assert tiled["mag"] == strip["mag"]


def test_tile_repeats_the_strip_on_its_column_pitch() -> None:
    strip = build_strip()
    tiled = tile_strips(strip, 3)
    assert tiled["copies"] == 3
    original_rects = str(strip["mag"]).count("rect ")
    assert str(tiled["mag"]).count("rect ") == 3 * original_rects


# -----------------------------------------------------------------------------
# extract() toolchain branches
# -----------------------------------------------------------------------------


def test_extract_reports_skipped_when_magic_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(weight_strip, "find_magic", lambda: None)
    monkeypatch.setattr(weight_strip, "find_magic_tech", lambda: None)
    result = extract(build_strip(), tmp_path)
    assert result == {"status": "skipped", "reason": "magic_or_tech_missing"}


def test_extract_reports_skipped_when_only_the_tech_is_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(weight_strip, "find_magic", lambda: "/usr/bin/magic")
    monkeypatch.setattr(weight_strip, "find_magic_tech", lambda: None)
    result = extract(build_strip(), tmp_path)
    assert result == {"status": "skipped", "reason": "magic_or_tech_missing"}


def test_extract_reports_a_magic_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(weight_strip, "find_magic", lambda: "/usr/bin/magic")
    monkeypatch.setattr(weight_strip, "find_magic_tech", lambda: tmp_path / "sky130A.tech")

    def raise_timeout(*_args: object, **_kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="magic", timeout=900)

    # Rebind the module's subprocess reference, never the stdlib module itself:
    # a cross-file patch of the shared module would leak into other consumers.
    monkeypatch.setattr(
        weight_strip,
        "subprocess",
        SimpleNamespace(run=raise_timeout, TimeoutExpired=subprocess.TimeoutExpired),
    )
    result = extract(build_strip(), tmp_path)
    assert result == {"status": "error", "reason": "magic_timeout"}


# -----------------------------------------------------------------------------
# spine_topology
# -----------------------------------------------------------------------------


def test_spine_topology_groups_cells_by_drain_and_gate(tmp_path: Path) -> None:
    spice = tmp_path / "strip.spice"
    spice.write_text(
        "X0 SP1 W0 VSUBS VSUBS sky130_fd_pr__nfet_01v8 w=0.42 l=0.15\n"
        "X1 SP1 W0 VSUBS VSUBS sky130_fd_pr__nfet_01v8 w=0.42 l=0.15\n"
        "X2 SP2 W1 VSUBS VSUBS sky130_fd_pr__nfet_01v8 w=0.42 l=0.15\n",
        encoding="utf-8",
    )
    topology = spine_topology(spice)
    assert topology["spines"] == 2
    assert topology["cells_per_spine"] == [2, 1]
    assert topology["word_lines"] == 2
    assert topology["spines_per_word_line"] == [2, 1]


# -----------------------------------------------------------------------------
# main() CLI
# -----------------------------------------------------------------------------


def test_main_prints_a_json_report_and_exits_zero_without_magic(
    monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(weight_strip, "extract", lambda strip, workdir: {"status": "skipped"})
    assert main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["strip"]["drc_errors"] is None
    assert "topology" not in report


def test_main_includes_topology_when_the_netlist_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    def fake_extract(strip: dict, workdir: Path) -> dict:
        spice = workdir / "strip.spice"
        spice.write_text(
            "X0 SP1 W0 VSUBS VSUBS sky130_fd_pr__nfet_01v8 w=0.42 l=0.15\n"
            "X1 SP1 W0 VSUBS VSUBS sky130_fd_pr__nfet_01v8 w=0.42 l=0.15\n",
            encoding="utf-8",
        )
        return {"status": "ok", "drc_errors": 0, "extracted": 2}

    monkeypatch.setattr(weight_strip, "extract", fake_extract)
    assert main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["strip"]["drc_errors"] == 0
    assert report["topology"]["spines"] == 1
