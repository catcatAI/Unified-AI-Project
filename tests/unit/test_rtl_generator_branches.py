# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Branch-closure tests for the RTL generator and the standards catalog.

Every ValueError branch in ``generate_mvu_header_projection`` is a geometry
contract the SystemVerilog silently bakes into constants; if one of them stops
firing, a wrong constant ships without a check. These tests keep each one live.
"""

from __future__ import annotations

import pytest

from ai.hardware.mvu_reference import MvuReferenceModel
from ai.hardware.rtl_generator import _integer, generate_mvu_header_projection
from ai.hardware.standards_catalog import search_standards


def _header() -> dict:
    """A geometrically consistent header, derived from the reference model."""
    return MvuReferenceModel().header_recalculation(clock_mhz=250)


def _mutate(**overrides: object) -> dict:
    header = _header()
    for dotted, value in overrides.items():
        section, key = dotted.split(".", 1)
        header[section][key] = value
    return header


# -----------------------------------------------------------------------------
# _integer
# -----------------------------------------------------------------------------


def test_integer_parses_numeric_strings_and_rejects_the_rest() -> None:
    assert _integer("4096", "x") == 4096
    assert _integer(3.0, "x") == 3
    with pytest.raises(ValueError, match="x must be an integer"):
        _integer("abc", "x")
    with pytest.raises(ValueError, match="x must be an integer"):
        _integer(None, "x")
    with pytest.raises(ValueError, match="x must be positive"):
        _integer(0, "x")
    with pytest.raises(ValueError, match="x must be positive"):
        _integer(-4, "x")


# -----------------------------------------------------------------------------
# header validation branches
# -----------------------------------------------------------------------------


def test_header_requires_both_sections() -> None:
    with pytest.raises(ValueError, match="sections are required"):
        generate_mvu_header_projection({"declared": {}})
    with pytest.raises(ValueError, match="sections are required"):
        generate_mvu_header_projection({"address_map": {}})


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"declared.total_sram_bytes": "not-an-int"}, "total_sram_bytes must be an integer"),
        ({"declared.sub_bank_bytes": 0}, "sub_bank_bytes must be positive"),
        (
            {"address_map.bank_select_bits": 4},
            "address_decode bit ranges must be two-element lists",
        ),
        ({"declared.sub_bank_count": 8}, "bank count does not match bank address slice"),
        (
            {"declared.sub_bank_bytes": 4096},
            "bank byte size does not match word and byte address slices",
        ),
        (
            {"declared.total_sram_bytes": 16384},
            "total SRAM size does not match bank geometry",
        ),
        (
            {"declared.wavefront_cycles": 8},
            "wavefront cycle count does not match bank count",
        ),
        (
            {"declared.delta_w_bits": 40},
            "plasticity fields do not fill the declared packet width",
        ),
        ({"declared.axi_data_width_bits": 64}, "requires 32-bit AXI data"),
        ({"declared.axi_address_width_bits": 16}, "requires 32-bit AXI addressing"),
        (
            {"declared.sram_base_address": 1 << 32},
            "SRAM base address is outside the AXI address width",
        ),
    ],
)
def test_header_validation_branches(overrides: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        generate_mvu_header_projection(_mutate(**overrides))


def test_negative_sram_base_is_rejected_too() -> None:
    with pytest.raises(ValueError, match="outside the AXI address width"):
        generate_mvu_header_projection(_mutate(**{"declared.sram_base_address": -1}))


def test_valid_header_still_projects() -> None:
    source = generate_mvu_header_projection(_header())
    assert "module mvu_header_projection" in source


# -----------------------------------------------------------------------------
# standards catalog: the two query modes
# -----------------------------------------------------------------------------


def test_search_matches_every_term_in_phrase_mode() -> None:
    # two terms: both must be present (AND), token-bounded -- every PCIe
    # document mentions "PCIe" and "base", so all three match, while a
    # single distinctive term narrows to one.
    result = search_standards("pcie base")
    assert result["count"] == 3
    ids = {item["standard_id"] for item in result["standards"]}
    assert "pcie_base_5.0" in ids
    assert search_standards("12V-2x6")["count"] == 1


def test_search_query_with_no_match_reports_zero() -> None:
    result = search_standards("usb4")
    assert result["status"] == "ok"
    assert result["count"] == 0
    assert result["standards"] == []


def test_search_empty_query_returns_the_whole_catalog() -> None:
    result = search_standards("   ")
    assert result["count"] == 5


def test_search_is_case_and_punctuation_tolerant() -> None:
    assert search_standards("axi")["count"] == 1
    assert search_standards("PCIe!")["count"] >= 1


# -----------------------------------------------------------------------------
# testbench generation
# -----------------------------------------------------------------------------


def test_testbench_extraction_reads_all_header_fields() -> None:
    from ai.hardware.rtl_generator import generate_mvu_header_projection_testbench

    header = _header()
    source = generate_mvu_header_projection_testbench(header)
    assert "`timescale 1ns/1ps" in source
    assert "module mvu_header_projection_tb" in source
    # The testbench reads every field from the header (lines 129-137).
    declared = header["declared"]
    address_map = header["address_map"]
    bank_count = int(declared["sub_bank_count"])
    bank_msb, bank_lsb = (int(value) for value in address_map["bank_select_bits"])
    bank_width = bank_msb - bank_lsb + 1
    assert f"BANK_COUNT = {bank_count}" in source
    assert f"BANK_WIDTH = {bank_width}" in source
    assert f"FORWARD_BUS_WIDTH = {declared['forward_bus_bits']}" in source
    assert f"PLASTICITY_BUS_WIDTH = {declared['plasticity_bus_bits']}" in source
    assert f"HIT_MASK_WIDTH = {declared['hit_mask_bits']}" in source
