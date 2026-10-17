# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple


def _integer(value: Any, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive")
    return parsed


def _require_sections(header: Mapping[str, Any]) -> None:
    """declared 與 address_map 兩段皆須為 dict（先於任何欄位提取）。"""
    if not isinstance(header.get("declared"), dict) or not isinstance(
        header.get("address_map"), dict
    ):
        raise ValueError("header declared and address_map sections are required")


def _extract_declared(header: Mapping[str, Any]) -> Dict[str, int]:
    """取出 declared 段的整數欄位（缺欄/非正整數由 _integer 拋錯）。"""
    declared = header.get("declared")
    if not isinstance(declared, dict):
        raise ValueError("header declared and address_map sections are required")
    return {
        "total_bytes": _integer(declared.get("total_sram_bytes"), "total_sram_bytes"),
        "bank_count": _integer(declared.get("sub_bank_count"), "sub_bank_count"),
        "bank_bytes": _integer(declared.get("sub_bank_bytes"), "sub_bank_bytes"),
        "wavefront_cycles": _integer(declared.get("wavefront_cycles"), "wavefront_cycles"),
        "forward_width": _integer(declared.get("forward_bus_bits"), "forward_bus_bits"),
        "plasticity_width": _integer(
            declared.get("plasticity_bus_bits"), "plasticity_bus_bits"
        ),
        "delta_width": _integer(declared.get("delta_w_bits"), "delta_w_bits"),
        "mask_width": _integer(declared.get("hit_mask_bits"), "hit_mask_bits"),
        "axi_address_width": _integer(
            declared.get("axi_address_width_bits"), "axi_address_width_bits"
        ),
        "axi_data_width": _integer(
            declared.get("axi_data_width_bits"), "axi_data_width_bits"
        ),
        "sram_base": int(declared.get("sram_base_address", 0)),
    }


def _extract_address_ranges(header: Mapping[str, Any]) -> Tuple[List[Any], List[Any], List[Any]]:
    """取出 address_map 三段位域範圍（各須為二元 list）。"""
    address_map = header.get("address_map")
    if not isinstance(address_map, dict):
        raise ValueError("header declared and address_map sections are required")
    bank_bits = address_map.get("bank_select_bits")
    word_bits = address_map.get("word_select_bits")
    byte_bits = address_map.get("byte_select_bits")
    if not (
        isinstance(bank_bits, list)
        and len(bank_bits) == 2
        and isinstance(word_bits, list)
        and len(word_bits) == 2
        and isinstance(byte_bits, list)
        and len(byte_bits) == 2
    ):
        raise ValueError("address_decode bit ranges must be two-element lists")
    return bank_bits, word_bits, byte_bits


def _validate_geometry(
    d: Dict[str, int], bank_bits: List[Any], word_bits: List[Any]
) -> None:
    """校驗 bank/word 幾何、wavefront、封包寬度與 AXI 範圍。"""
    bank_count = d["bank_count"]
    if bank_count != (1 << (bank_bits[0] - bank_bits[1] + 1)):
        raise ValueError("bank count does not match bank address slice")
    if d["bank_bytes"] != (1 << (word_bits[0] - word_bits[1] + 1)) * 8:
        raise ValueError("bank byte size does not match word and byte address slices")
    if d["total_bytes"] != bank_count * d["bank_bytes"]:
        raise ValueError("total SRAM size does not match bank geometry")
    if d["wavefront_cycles"] != bank_count:
        raise ValueError("wavefront cycle count does not match bank count")
    if d["delta_width"] + d["mask_width"] != d["plasticity_width"]:
        raise ValueError("plasticity fields do not fill the declared packet width")
    if d["axi_data_width"] != 32:
        raise ValueError("the current projection requires 32-bit AXI data")
    if d["axi_address_width"] != 32:
        raise ValueError("the current projection requires 32-bit AXI addressing")
    if d["sram_base"] < 0 or d["sram_base"] >= 1 << d["axi_address_width"]:
        raise ValueError("SRAM base address is outside the AXI address width")


def generate_mvu_header_projection(header: Mapping[str, Any]) -> str:
    _require_sections(header)
    d = _extract_declared(header)
    bank_bits, word_bits, byte_bits = _extract_address_ranges(header)
    _validate_geometry(d, bank_bits, word_bits)

    total_bytes = d["total_bytes"]
    bank_count = d["bank_count"]
    bank_bytes = d["bank_bytes"]
    wavefront_cycles = d["wavefront_cycles"]
    forward_width = d["forward_width"]
    plasticity_width = d["plasticity_width"]
    delta_width = d["delta_width"]
    mask_width = d["mask_width"]
    axi_address_width = d["axi_address_width"]
    sram_base = d["sram_base"]
    bank_msb, bank_lsb = (int(value) for value in bank_bits)
    word_msb, word_lsb = (int(value) for value in word_bits)
    byte_msb, byte_lsb = (int(value) for value in byte_bits)
    commit_source = "((hit_mask !== '0) && port_b_we && rst_n && !soft_reset)"
    return f"""`default_nettype none
module mvu_header_projection #(
  parameter int unsigned SRAM_TOTAL_BYTES = {total_bytes},
  parameter int unsigned SUB_BANK_COUNT = {bank_count},
  parameter int unsigned SUB_BANK_BYTES = {bank_bytes},
  parameter int unsigned WAVEFRONT_CYCLES = {wavefront_cycles},
  parameter int unsigned FORWARD_BUS_WIDTH = {forward_width},
  parameter int unsigned PLASTICITY_BUS_WIDTH = {plasticity_width},
  parameter int unsigned DELTA_W_WIDTH = {delta_width},
  parameter int unsigned HIT_MASK_WIDTH = {mask_width},
  parameter int unsigned SRAM_BASE_ADDRESS = {sram_base},
  parameter int unsigned BANK_MSB = {bank_msb},
  parameter int unsigned BANK_LSB = {bank_lsb},
  parameter int unsigned WORD_MSB = {word_msb},
  parameter int unsigned WORD_LSB = {word_lsb},
  parameter int unsigned BYTE_MSB = {byte_msb},
  parameter int unsigned BYTE_LSB = {byte_lsb}
) (
  input logic clk,
  input logic rst_n,
  input logic soft_reset,
  input logic [FORWARD_BUS_WIDTH-1:0] forward_in,
  output logic [FORWARD_BUS_WIDTH-1:0] forward_out,
  input logic [PLASTICITY_BUS_WIDTH-1:0] plasticity_in,
  output logic [PLASTICITY_BUS_WIDTH-1:0] plasticity_out,
  input logic port_b_we,
  input logic [HIT_MASK_WIDTH-1:0] hit_mask,
  output logic [BANK_MSB-BANK_LSB:0] read_bank,
  output logic [BANK_MSB-BANK_LSB:0] write_bank,
  output logic phase_sync,
  output logic commit_pulse
);
  logic [BANK_MSB-BANK_LSB:0] count_reg;
  logic commit_reg;

  assign forward_out = forward_in;
  assign plasticity_out = plasticity_in;
  assign read_bank = count_reg;
  assign write_bank = count_reg - 1'b1;
  assign phase_sync = (count_reg == SUB_BANK_COUNT - 1);

  always_ff @(posedge clk) begin
    if (!rst_n) begin
      count_reg <= '0;
      commit_reg <= 1'b0;
    end else if (soft_reset) begin
      count_reg <= '0;
      commit_reg <= 1'b0;
    end else begin
      count_reg <= count_reg + 1'b1;
      commit_reg <= {commit_source};
    end
  end

  assign commit_pulse = commit_reg;
endmodule
`default_nettype wire
"""


def generate_mvu_header_projection_testbench(header: Mapping[str, Any]) -> str:
    generate_mvu_header_projection(header)
    declared = header["declared"]
    address_map = header["address_map"]
    bank_count = int(declared["sub_bank_count"])
    bank_msb, bank_lsb = (int(value) for value in address_map["bank_select_bits"])
    forward_width = int(declared["forward_bus_bits"])
    plasticity_width = int(declared["plasticity_bus_bits"])
    mask_width = int(declared["hit_mask_bits"])
    return f"""`timescale 1ns/1ps
module mvu_header_projection_tb;
  localparam int unsigned BANK_COUNT = {bank_count};
  localparam int unsigned FORWARD_BUS_WIDTH = {forward_width};
  localparam int unsigned PLASTICITY_BUS_WIDTH = {plasticity_width};
  localparam int unsigned HIT_MASK_WIDTH = {mask_width};
  localparam int unsigned BANK_WIDTH = {bank_msb - bank_lsb + 1};

  logic clk;
  logic rst_n;
  logic soft_reset;
  logic [FORWARD_BUS_WIDTH-1:0] forward_in;
  logic [FORWARD_BUS_WIDTH-1:0] forward_out;
  logic [PLASTICITY_BUS_WIDTH-1:0] plasticity_in;
  logic [PLASTICITY_BUS_WIDTH-1:0] plasticity_out;
  logic port_b_we;
  logic [HIT_MASK_WIDTH-1:0] hit_mask;
  logic [BANK_WIDTH-1:0] read_bank;
  logic [BANK_WIDTH-1:0] write_bank;
  logic phase_sync;
  logic commit_pulse;

  mvu_header_projection dut (
    .clk(clk),
    .rst_n(rst_n),
    .soft_reset(soft_reset),
    .forward_in(forward_in),
    .forward_out(forward_out),
    .plasticity_in(plasticity_in),
    .plasticity_out(plasticity_out),
    .port_b_we(port_b_we),
    .hit_mask(hit_mask),
    .read_bank(read_bank),
    .write_bank(write_bank),
    .phase_sync(phase_sync),
    .commit_pulse(commit_pulse)
  );

  always #1 clk = ~clk;

  initial begin
    clk = 1'b0;
    rst_n = 1'b0;
    soft_reset = 1'b1;
    forward_in = '0;
    plasticity_in = '0;
    port_b_we = 1'b0;
    hit_mask = '0;
    repeat (2) @(posedge clk);
    rst_n = 1'b1;
    soft_reset = 1'b0;
    @(posedge clk);
    #1;
    if (read_bank !== 1) $fatal(1, "wavefront count did not advance");
    if (write_bank !== 0) $fatal(1, "ownership write pointer is not count minus one");
    port_b_we = 1'b1;
    hit_mask = '1;
    @(posedge clk);
    #1;
    if (commit_pulse !== 1'b1) $fatal(1, "commit pulse was not produced");
    soft_reset = 1'b1;
    port_b_we = 1'b0;
    hit_mask = '0;
    @(posedge clk);
    #1;
    if (read_bank !== 0) $fatal(1, "soft reset did not clear the wavefront count");
    if (write_bank !== BANK_COUNT - 1) $fatal(1, "soft reset write pointer is incorrect");
    if (commit_pulse !== 1'b0) $fatal(1, "soft reset did not clear commit state");
    $display("mvu_header_projection_tb PASS");
    $finish;
  end
endmodule
"""
