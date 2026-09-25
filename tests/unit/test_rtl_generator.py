import pytest

from ai.hardware.mvu_reference import MvuReferenceModel
from ai.hardware.rtl_generator import (
    generate_mvu_header_projection,
    generate_mvu_header_projection_testbench,
)


def test_rtl_projection_emits_structural_systemverilog() -> None:
    header = MvuReferenceModel().header_recalculation(clock_mhz=250)
    source = generate_mvu_header_projection(header)

    assert "module mvu_header_projection" in source
    assert "parameter int unsigned SRAM_TOTAL_BYTES = 32768" in source
    assert "parameter int unsigned FORWARD_BUS_WIDTH = 16384" in source
    assert "parameter int unsigned PLASTICITY_BUS_WIDTH = 64" in source
    assert "assign write_bank = count_reg - 1'b1;" in source
    assert "commit_reg <=" in source
    assert "`default_nettype none" in source
    assert "`default_nettype wire" in source
    assert "TODO" not in source
    assert "placeholder" not in source.lower()


def test_rtl_projection_emits_self_checking_testbench() -> None:
    header = MvuReferenceModel().header_recalculation(clock_mhz=250)
    source = generate_mvu_header_projection_testbench(header)

    assert "module mvu_header_projection_tb" in source
    assert "mvu_header_projection dut" in source
    assert "mvu_header_projection_tb PASS" in source
    assert "soft reset did not clear the wavefront count" in source
    assert "commit pulse was not produced" in source


def test_rtl_projection_rejects_inconsistent_header_geometry() -> None:
    header = MvuReferenceModel().header_recalculation()
    header["declared"]["sub_bank_count"] = 8

    with pytest.raises(ValueError, match="bank count"):
        generate_mvu_header_projection(header)
