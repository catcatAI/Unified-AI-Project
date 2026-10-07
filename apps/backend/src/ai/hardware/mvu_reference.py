# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class MvuSpecIssue:
    issue_id: str
    severity: str
    description: str
    resolution: str


@dataclass(frozen=True)
class MvuReferenceConfig:
    bank_count: int = 16
    bank_bytes: int = 2048
    bank_word_bytes: int = 8
    port_b_word_sel_bits: int = 8
    pe_rows: int = 16
    pe_columns: int = 16
    activation_bus_bits: int = 1024
    weight_bus_bits: int = 16384
    c_gap_bits: int = 512
    logits_bits: int = 256
    weight_max: int = 127
    plasticity_ratio: float = 0.0588
    accumulator_shift: int = 4
    rounds: int = 2
    initial_weight: int = 10
    sparse_target_bytes: int = 16
    declared_total_sram_bytes: int = 32768
    wavefront_cycles: int = 16
    int8_width_bits: int = 8
    mac_array_size: int = 256
    plasticity_bus_bits: int = 64
    delta_w_bits: int = 32
    hit_mask_bits: int = 32
    endianness: str = "little"
    axi_address_width_bits: int = 32
    axi_data_width_bits: int = 32
    sram_base_address: int = 0x1000
    csr_control_offset: int = 0x0000
    csr_status_offset: int = 0x0004
    csr_cycle_counter_offset: int = 0x0008
    bank_select_msb: int = 14
    bank_select_lsb: int = 11
    word_select_msb: int = 10
    word_select_lsb: int = 3
    byte_select_msb: int = 2
    byte_select_lsb: int = 0

    @property
    def bank_count_words(self) -> int:
        return self.bank_bytes // self.bank_word_bytes

    @property
    def max_delta(self) -> int:
        return int(math.floor(self.plasticity_ratio * self.weight_max))

    @property
    def total_bytes(self) -> int:
        return self.bank_count * self.bank_bytes

    @property
    def total_bits(self) -> int:
        return self.total_bytes * 8

    @property
    def max_modified_bits(self) -> int:
        return int(math.floor(self.total_bits * 0.03125))

    def issues(self) -> List[MvuSpecIssue]:
        issues = [
            MvuSpecIssue(
                "port_b_word_select_width",
                "resolved",
                "The header address map uses an 8-bit word select for all 256 64-bit words in each 2 KB bank.",
                "Keep the 8-bit word select aligned with address bits [10:3].",
            ),
            MvuSpecIssue(
                "weight_bus_width",
                "warning",
                "The 16,384-bit weight bus is larger than the 2,048-bit 16x16 INT8 tile.",
                "Define the bank-to-tile mapping and mark the remaining bits as reserved/future.",
            ),
            MvuSpecIssue(
                "activation_bus_width",
                "warning",
                "The 1,024-bit activation bus carries 16x64 values but the PE consumes 16x16.",
                "Define a 16-value feature slice per token or widen the PE to 64 columns.",
            ),
            MvuSpecIssue(
                "delta_encoding",
                "warning",
                "A 32-bit delta and 32-bit mask do not define how they map into a 64-bit weight word.",
                "Use four packed signed INT8 lanes plus an explicit byte-lane mask.",
            ),
            MvuSpecIssue(
                "axi_sram_window",
                "blocker",
                "Registers 0x10..0x1C cannot directly map a complete 32 KB SRAM.",
                "Add an indirect SRAM address/data window or map 0x1000..0x8FFF.",
            ),
            MvuSpecIssue(
                "fixed_point_weight_range",
                "blocker",
                "The 5.88% clamp requires a defined W_max and fixed-point format.",
                "Declare signed INT8 Q-format, W_max=127, and integer clamp floor(0.0588*W_max).",
            ),
            MvuSpecIssue(
                "convergence_sign",
                "warning",
                "The sign convention for C_Gap and Logit_Diff is not defined.",
                "Declare C_Gap = Logit - Target before implementing negative feedback.",
            ),
            MvuSpecIssue(
                "pipeline_stall_model",
                "warning",
                "The software model has no AXI/FIFO backpressure source, so zero stalls is assumed.",
                "Add ready/valid and AXI transaction models before using stall counts as evidence.",
            ),
            MvuSpecIssue(
                "timing_signoff",
                "blocker",
                "A sequential Python model cannot prove a 250 MHz timing target.",
                "Generate RTL/HDL and run generic synthesis plus static timing analysis later.",
            ),
            MvuSpecIssue(
                "physical_netlist",
                "blocker",
                "The reference model does not yet produce a gate-level netlist or waveform.",
                "Add a digital netlist/HDL builder and transient waveform comparator.",
            ),
        ]
        return issues


@dataclass
class SparseWriteResult:
    bank: int
    word_sel: int
    hit_mask: int
    delta: int
    changed_bits: int
    clamped_lanes: int


class Sram32KbDualPort:
    def __init__(self, config: MvuReferenceConfig, initial_banks: Optional[Sequence[bytes]] = None):
        self.config = config
        if initial_banks is None:
            initial_banks = []
            for _bank in range(config.bank_count):
                bank = bytearray([config.initial_weight & 0xFF]) * config.bank_bytes
                initial_banks.append(bytes(bank))
        if len(initial_banks) != config.bank_count:
            raise ValueError("initial bank count does not match the SRAM configuration")
        if any(len(bank) != config.bank_bytes for bank in initial_banks):
            raise ValueError("each SRAM bank must contain exactly bank_bytes")
        self.banks = [bytearray(bank) for bank in initial_banks]
        self.initial = tuple(bytes(bank) for bank in self.banks)
        self.read_log: List[int] = []
        self.write_log: List[int] = []

    def read_port_a(self, bank: int, enabled: bool = True) -> bytes:
        if not enabled:
            return bytes(self.config.bank_bytes)
        self._validate_bank(bank)
        self.read_log.append(bank)
        return bytes(self.banks[bank])

    def write_port_b(
        self,
        bank: int,
        word_sel: int,
        delta: int,
        hit_mask: int,
        word_base: int = 0,
    ) -> SparseWriteResult:
        self._validate_bank(bank)
        max_word = 1 << self.config.port_b_word_sel_bits
        if not 0 <= word_sel < max_word:
            raise ValueError("word_sel exceeds the declared Port B field")
        if not 0 <= word_base <= self.config.bank_count_words - max_word:
            raise ValueError("word_base leaves the SRAM bank")
        if not 0 <= hit_mask < 1 << 32:
            raise ValueError("hit_mask must be a 32-bit mask")
        if not -(1 << 31) <= delta < (1 << 31):
            raise ValueError("delta must be a signed 32-bit value")
        target_word = word_base + word_sel
        offset = target_word * self.config.bank_word_bytes
        before = bytes(self.banks[bank][offset : offset + self.config.bank_word_bytes])
        delta_bytes = (delta & 0xFFFFFFFF).to_bytes(4, "little", signed=False)
        current = bytearray(before)
        changed_bits = 0
        clamped_lanes = 0
        for byte_index in range(4):
            lane_mask = (hit_mask >> (byte_index * 8)) & 0xFF
            if not lane_mask:
                continue
            old_value = _signed_int8(before[byte_index])
            requested = _signed_int8(delta_bytes[byte_index])
            bounded = max(-self.config.max_delta, min(self.config.max_delta, requested))
            if bounded != requested:
                clamped_lanes += 1
            new_value = max(
                -self.config.weight_max, min(self.config.weight_max, old_value + bounded)
            )
            new_byte = new_value & 0xFF
            current[byte_index] = new_byte
            changed_bits += (old_value ^ new_value).bit_count()
        self.banks[bank][offset : offset + self.config.bank_word_bytes] = current
        self.write_log.append(bank)
        return SparseWriteResult(
            bank=bank,
            word_sel=word_sel,
            hit_mask=hit_mask,
            delta=delta,
            changed_bits=changed_bits,
            clamped_lanes=clamped_lanes,
        )

    def modified_bit_count(self) -> int:
        total = 0
        for current, initial in zip(self.banks, self.initial):
            for current_byte, initial_byte in zip(current, initial):
                total += (current_byte ^ initial_byte).bit_count()
        return total

    def bank_snapshot(self) -> List[bytes]:
        return [bytes(bank) for bank in self.banks]

    def _validate_bank(self, bank: int) -> None:
        if not 0 <= bank < self.config.bank_count:
            raise ValueError("bank address is outside the declared 4-bit field")


class WavefrontController:
    def __init__(self, bank_count: int = 16):
        if bank_count != 16:
            raise ValueError("the current contract requires 16 banks")
        self.bank_count = bank_count
        self.count = 0
        self.history: List[Dict[str, int]] = []

    def reset(self) -> None:
        self.count = 0
        self.history = []

    def pointers(self) -> Dict[str, int]:
        return {
            "count": self.count,
            "rd_ptr": self.count,
            "wr_ptr": (self.count - 1) % self.bank_count,
            "phase_sync": int(self.count == self.bank_count - 1),
        }

    def step(self) -> Dict[str, int]:
        pointers = self.pointers()
        self.history.append(pointers)
        self.count = (self.count + 1) % self.bank_count
        return pointers

    def collision_count(self) -> int:
        return sum(1 for item in self.history if item["rd_ptr"] == item["wr_ptr"])


class PeArray16x16:
    def __init__(self, config: MvuReferenceConfig):
        self.config = config

    def run(
        self,
        activation: Sequence[Sequence[int]],
        banks: Sequence[bytes],
    ) -> Dict[str, Any]:
        self._validate_inputs(activation, banks)
        logits: List[int] = []
        for row_index, row in enumerate(activation):
            accumulator = 0
            packed_row_offset = (row_index // 4) * 8 + (row_index % 4)
            for feature_index, feature_value in enumerate(row):
                weight = _signed_int8(banks[feature_index][packed_row_offset])
                accumulator += weight * feature_value
            logits.append(_clamp_int(accumulator >> self.config.accumulator_shift, -128, 127))
        return {
            "logits": logits,
            "logits_bits": len(logits) * 16,
            "c_gap": logits,
            "c_gap_bits": len(logits) * 32,
            "weight_layout": "feature-lane layout: each bank stores four signed INT8 rows per 64-bit word",
        }

    def _validate_inputs(
        self,
        activation: Sequence[Sequence[int]],
        banks: Sequence[bytes],
    ) -> None:
        if len(activation) != self.config.pe_rows or len(banks) != self.config.bank_count:
            raise ValueError("PE input dimensions do not match the 16x16 contract")
        if any(len(row) != self.config.pe_columns for row in activation):
            raise ValueError("each activation row must contain 16 values")
        required_bank_bytes = (
            (self.config.pe_rows - 1) // 4
        ) * 8 + ((self.config.pe_rows - 1) % 4) + 1
        if any(len(bank) < required_bank_bytes for bank in banks):
            raise ValueError(
                "each SRAM bank must provide one weight byte per PE output row"
            )


class PlasticityEngine:
    def __init__(self, config: MvuReferenceConfig):
        self.config = config

    def update(
        self,
        c_gap: int,
        lane: int,
        word_sel: int = 0,
        hit_mask: int = 0xFFFFFFFF,
    ) -> Dict[str, Any]:
        if not 0 <= lane < self.config.bank_count:
            raise ValueError("lane is outside the 16 sparse update lanes")
        if not 0 <= word_sel < 1 << self.config.port_b_word_sel_bits:
            raise ValueError("word_sel is outside the Port B field")
        if not 0 <= hit_mask < 1 << 32:
            raise ValueError("hit_mask is outside the 32-bit field")
        delta = 0
        if c_gap > 0:
            delta = -min(abs(c_gap), self.config.max_delta)
        elif c_gap < 0:
            delta = min(abs(c_gap), self.config.max_delta)
        lane_delta = delta & 0xFF
        packed_delta = lane_delta | (lane_delta << 8) | (lane_delta << 16) | (lane_delta << 24)
        return {
            "delta_w": _to_signed_int32(packed_delta),
            "hit_mask": hit_mask,
            "word_sel": word_sel,
            "delta": delta,
            "delta_encoding": "packed_signed_int8x4",
        }


class AxiLiteRegisterMap:
    CR = 0x00
    SR = 0x04
    INDIRECT_ADDR = 0x20
    INDIRECT_DATA = 0x24
    SRAM_WINDOW = 0x1000

    def __init__(self, sram: Optional[Sram32KbDualPort] = None) -> None:
        self.registers = {self.CR: 0, self.SR: 0, self.INDIRECT_ADDR: 0}
        self.sram = sram
        self.spec_window_complete = False

    def write(self, address: int, value: int) -> None:
        value &= 0xFFFFFFFF
        if address == self.CR:
            self.registers[self.CR] = value & 0x7
        elif address == self.SR:
            self.registers[self.SR] = value & 0x3
        elif address == self.INDIRECT_ADDR:
            self.registers[self.INDIRECT_ADDR] = value & 0x7FFF
        elif address == self.INDIRECT_DATA:
            self._require_sram()
            offset = self.registers[self.INDIRECT_ADDR]
            self._write_sram_word(offset, value)
        elif self.SRAM_WINDOW <= address <= self.SRAM_WINDOW + 0x7FFC:
            self._require_sram()
            self._write_sram_word(address - self.SRAM_WINDOW, value)
        else:
            raise ValueError("address is outside the software AXI contract")

    def read(self, address: int) -> int:
        if address == self.INDIRECT_DATA:
            self._require_sram()
            return self._read_sram_word(self.registers[self.INDIRECT_ADDR])
        if self.SRAM_WINDOW <= address <= self.SRAM_WINDOW + 0x7FFC:
            self._require_sram()
            return self._read_sram_word(address - self.SRAM_WINDOW)
        if address not in self.registers:
            raise ValueError("address is not readable in the software AXI contract")
        return self.registers[address]

    def preload(self, data: bytes) -> None:
        self._require_sram()
        if len(data) % 4:
            raise ValueError("AXI preload data must be a multiple of 32 bits")
        for offset in range(0, len(data), 4):
            self.write(self.INDIRECT_ADDR, offset)
            self.write(self.INDIRECT_DATA, int.from_bytes(data[offset : offset + 4], "little"))

    def readback(self, byte_count: int) -> bytes:
        sram = self._require_sram()
        if byte_count < 0 or byte_count > sram.config.total_bytes:
            raise ValueError("AXI readback length is outside the SRAM")
        if byte_count % 4:
            raise ValueError("AXI readback length must be a multiple of 32 bits")
        output = bytearray()
        for offset in range(0, byte_count, 4):
            self.write(self.INDIRECT_ADDR, offset)
            output.extend(self.read(self.INDIRECT_DATA).to_bytes(4, "little"))
        return bytes(output)

    def _write_sram_word(self, offset: int, value: int) -> None:
        sram = self._require_sram()
        if offset % 4 or offset + 4 > sram.config.total_bytes:
            raise ValueError("AXI SRAM word address is not 32-bit aligned")
        bank, bank_offset = divmod(offset, sram.config.bank_bytes)
        sram.banks[bank][bank_offset : bank_offset + 4] = value.to_bytes(4, "little")

    def _read_sram_word(self, offset: int) -> int:
        sram = self._require_sram()
        if offset % 4 or offset + 4 > sram.config.total_bytes:
            raise ValueError("AXI SRAM word address is not 32-bit aligned")
        bank, bank_offset = divmod(offset, sram.config.bank_bytes)
        return int.from_bytes(sram.banks[bank][bank_offset : bank_offset + 4], "little")

    def _require_sram(self) -> Sram32KbDualPort:
        if self.sram is None:
            raise ValueError("AXI register map has no attached software SRAM")
        return self.sram

    def contract(self) -> Dict[str, Any]:
        return {
            "address_bits": 32,
            "data_bits": 32,
            "cr": {"address": self.CR, "start": 0, "reset": 1, "mode": 2},
            "sr": {"address": self.SR, "busy": 0, "phase_done": 1},
            "indirect_sram_address": self.INDIRECT_ADDR,
            "indirect_sram_data": self.INDIRECT_DATA,
            "direct_sram_window": [self.SRAM_WINDOW, self.SRAM_WINDOW + 0x7FFC],
            "direct_sram_window_end_semantics": "last 32-bit word address",
            "original_0x10_to_0x1c_window_complete": self.spec_window_complete,
        }


class MvuReferenceModel:
    def __init__(self, config: Optional[MvuReferenceConfig] = None):
        self.config = config or MvuReferenceConfig()
        self._reset_state()

    def _reset_state(self) -> None:
        self.sram = Sram32KbDualPort(self.config)
        self.pe = PeArray16x16(self.config)
        self.plasticity = PlasticityEngine(self.config)
        self.wavefront = WavefrontController(self.config.bank_count)
        self.axi = AxiLiteRegisterMap(self.sram)
        self.round_results: List[Dict[str, Any]] = []

    def _activation(self) -> List[List[int]]:
        return [[1 for _ in range(self.config.pe_columns)] for _ in range(self.config.pe_rows)]

    def _read_phase(self) -> List[bytes]:
        self.wavefront.reset()
        banks: List[bytes] = []
        for _cycle in range(self.config.bank_count):
            pointers = self.wavefront.step()
            banks.append(self.sram.read_port_a(pointers["rd_ptr"]))
        return banks

    def _write_phase(self, c_gap: Sequence[int]) -> Tuple[int, int]:
        self.wavefront.reset()
        changed_bits = 0
        clamped_lanes = 0
        for row in range(self.config.bank_count):
            self.wavefront.step()
            word_sel = row // 4
            hit_mask = 1 << ((row % 4) * 8)
            for feature in range(self.config.bank_count):
                update = self.plasticity.update(
                    c_gap[row], feature, word_sel=word_sel, hit_mask=hit_mask
                )
                write = self.sram.write_port_b(
                    bank=feature,
                    word_sel=update["word_sel"],
                    delta=update["delta_w"],
                    hit_mask=update["hit_mask"],
                )
                changed_bits += write.changed_bits
                clamped_lanes += write.clamped_lanes
        return changed_bits, clamped_lanes

    def run_round(self, round_index: int) -> Dict[str, Any]:
        read_banks = self._read_phase()
        first = self.pe.run(self._activation(), read_banks)
        c_gap = first["c_gap"]
        changed_bits, clamped_lanes = self._write_phase(c_gap)
        second_banks = self._read_phase()
        second = self.pe.run(self._activation(), second_banks)
        logit_diff = [after - before for before, after in zip(first["logits"], second["logits"])]
        sign_pass = all(
            (gap == 0 and diff == 0) or (gap > 0 and diff < 0) or (gap < 0 and diff > 0)
            for gap, diff in zip(c_gap, logit_diff)
        )
        return {
            "round": round_index,
            "logits_before": first["logits"],
            "c_gap": c_gap,
            "logits_after": second["logits"],
            "logit_diff": logit_diff,
            "negative_feedback_sign_pass": sign_pass,
            "changed_bits": changed_bits,
            "clamped_lanes": clamped_lanes,
            "phase_sync": self.wavefront.history[-1]["phase_sync"] if self.wavefront.history else 0,
            "raw_collision_count": self.wavefront.collision_count(),
            "pipeline_stalls": None,
            "pipeline_stalls_measured": False,
        }

    def header_recalculation(self, clock_mhz: Optional[float] = None) -> Dict[str, Any]:
        if clock_mhz is not None and clock_mhz <= 0:
            raise ValueError("clock_mhz must be positive")
        total_bytes = self.config.total_bytes
        total_bits = self.config.total_bits
        bank_words = self.config.bank_count_words
        forward_bytes = self.config.weight_bus_bits // 8
        forward_values = forward_bytes // (self.config.int8_width_bits // 8)
        side_packet_bytes = self.config.plasticity_bus_bits // 8
        bank_ranges = []
        for bank in range(self.config.bank_count):
            relative_start = bank * self.config.bank_bytes
            relative_end = relative_start + self.config.bank_bytes - 1
            axi_start = self.config.sram_base_address + relative_start
            axi_end = self.config.sram_base_address + relative_end
            bank_ranges.append(
                {
                    "bank": bank,
                    "relative_start": relative_start,
                    "relative_end": relative_end,
                    "axi_start": axi_start,
                    "axi_end": axi_end,
                }
            )
        timing: Dict[str, Any] = {
            "wavefront_cycles": self.config.wavefront_cycles,
            "clock_mhz": clock_mhz,
            "cycle_period_ns": None,
            "wavefront_period_ns": None,
        }
        bandwidth: Dict[str, Any] = {
            "forward_bus_bits_per_cycle": self.config.weight_bus_bits,
            "forward_bytes_per_cycle": forward_bytes,
            "forward_int8_values_per_cycle": forward_values,
            "side_packet_bits_per_cycle_per_bank": self.config.plasticity_bus_bits,
            "side_packet_bytes_per_cycle_per_bank": side_packet_bytes,
            "aggregate_16_bank_side_bandwidth": None,
            "forward_gbps": None,
            "forward_gbs": None,
            "side_per_bank_gbps": None,
            "side_per_bank_gbs": None,
            "side_16_bank_gbps": None,
            "side_16_bank_gbs": None,
        }
        if clock_mhz is not None:
            clock_hz = clock_mhz * 1_000_000
            forward_gbps = self.config.weight_bus_bits * clock_hz / 1_000_000_000
            side_gbps = self.config.plasticity_bus_bits * clock_hz / 1_000_000_000
            side_aggregate_gbps = side_gbps * self.config.bank_count
            timing["cycle_period_ns"] = 1_000_000_000 / clock_hz
            timing["wavefront_period_ns"] = self.config.wavefront_cycles * 1_000_000_000 / clock_hz
            bandwidth.update(
                {
                    "forward_gbps": forward_gbps,
                    "forward_gbs": forward_gbps / 8.0,
                    "side_per_bank_gbps": side_gbps,
                    "side_per_bank_gbs": side_gbps / 8.0,
                    "side_16_bank_gbps": side_aggregate_gbps,
                    "side_16_bank_gbs": side_aggregate_gbps / 8.0,
                }
            )
        checks = {
            "declared_total_matches_geometry": total_bytes == self.config.declared_total_sram_bytes,
            "bank_geometry_matches_total": (
                self.config.bank_count * bank_words * self.config.bank_word_bytes == total_bytes
            ),
            "forward_bus_matches_full_bank": self.config.weight_bus_bits
            == self.config.bank_bytes * 8,
            "wavefront_matches_bank_count": self.config.wavefront_cycles == self.config.bank_count,
            "word_selector_covers_bank": (
                1 << (self.config.word_select_msb - self.config.word_select_lsb + 1) == bank_words
            ),
            "byte_selector_covers_word": (
                1 << (self.config.byte_select_msb - self.config.byte_select_lsb + 1)
                == self.config.bank_word_bytes
            ),
            "side_packet_fields_fill_declared_width": (
                self.config.delta_w_bits + self.config.hit_mask_bits
                == self.config.plasticity_bus_bits
            ),
        }
        return {
            "source": "user_provided_mvu_config_vh",
            "scope": "one_configured_mvu_sram_instance",
            "declared": {
                "total_sram_bytes": self.config.declared_total_sram_bytes,
                "sub_bank_count": self.config.bank_count,
                "sub_bank_bytes": self.config.bank_bytes,
                "wavefront_cycles": self.config.wavefront_cycles,
                "forward_bus_bits": self.config.weight_bus_bits,
                "plasticity_bus_bits": self.config.plasticity_bus_bits,
                "delta_w_bits": self.config.delta_w_bits,
                "hit_mask_bits": self.config.hit_mask_bits,
                "mac_array_size": self.config.mac_array_size,
                "endianness": self.config.endianness,
                "axi_address_width_bits": self.config.axi_address_width_bits,
                "axi_data_width_bits": self.config.axi_data_width_bits,
                "sram_base_address": self.config.sram_base_address,
                "csr_offsets": {
                    "control": self.config.csr_control_offset,
                    "status": self.config.csr_status_offset,
                    "cycle_counter": self.config.csr_cycle_counter_offset,
                },
            },
            "derived": {
                "total_sram_bits": total_bits,
                "total_sram_kib": total_bytes / 1024,
                "bank_bits": self.config.bank_bytes * 8,
                "words_per_bank": bank_words,
                "total_64_bit_words": self.config.bank_count * bank_words,
                "forward_bytes": forward_bytes,
                "forward_int8_values": forward_values,
                "side_packet_bytes": side_packet_bytes,
                "max_delta_from_ratio": self.config.max_delta,
                "max_modified_bits_at_three_point_one_two_five_percent": self.config.max_modified_bits,
            },
            "timing": timing,
            "bandwidth": bandwidth,
            "address_map": {
                "relative_byte_address_bits": "[14:0]",
                "bank_select_bits": [self.config.bank_select_msb, self.config.bank_select_lsb],
                "word_select_bits": [self.config.word_select_msb, self.config.word_select_lsb],
                "byte_select_bits": [self.config.byte_select_msb, self.config.byte_select_lsb],
                "bank_ranges": bank_ranges,
                "direct_axi_window_bytes": [
                    self.config.sram_base_address,
                    self.config.sram_base_address + total_bytes - 1,
                ],
                "last_32_bit_word_address": self.config.sram_base_address + total_bytes - 4,
            },
            "reset_and_commit": {
                "hard_reset_clears": ["csr", "control_fsm", "counters", "sram"],
                "soft_reset_clears": ["control_fsm", "counters"],
                "soft_reset_retains": ["sram_weights"],
                "commit_predicate": "posedge(clock) && port_b_we && bit_mask != 0",
                "ownership_and_reset_gates_in_predicate": False,
                "requires_rtl_review": True,
            },
            "checks": checks,
            "checks_pass": all(checks.values()),
            "unresolved_scope": [
                "number of MVU instances and mapping to the die L1",
                "clock frequency is not declared by the header",
                "forward bank-to-16x16-PE weight layout",
                "whether 64-bit side packets are emitted once per bank or aggregated across banks",
                "Q-format, saturation, and accumulator contract",
                "AXI transaction behavior beyond address and data widths",
            ],
        }

    def run(self, clock_mhz: Optional[float] = None) -> Dict[str, Any]:
        self._reset_state()
        self.round_results = [self.run_round(index + 1) for index in range(self.config.rounds)]
        modified_bits = self.sram.modified_bit_count()
        modified_ratio = modified_bits / self.config.total_bits
        max_delta = self.config.max_delta
        functional_pass = all(
            result["negative_feedback_sign_pass"] and result["raw_collision_count"] == 0
            for result in self.round_results
        )
        modified_pass = 0 < modified_bits <= self.config.max_modified_bits
        unresolved_blockers = any(issue.severity == "blocker" for issue in self.config.issues())
        reference_pass = functional_pass and modified_pass
        return {
            "schema_version": "mvu-reference/1",
            "status": "pass" if reference_pass and not unresolved_blockers else "partial",
            "validation": {
                "level": "L1",
                "mode": "software_only",
                "professional_hdl_simulation": False,
                "physical_hardware": False,
                "install_new_tools": False,
                "evidence_rule": "reference results are not gate-level or timing sign-off",
            },
            "config": {
                "bank_count": self.config.bank_count,
                "bank_bytes": self.config.bank_bytes,
                "total_bytes": self.config.total_bytes,
                "pe": "16x16-int8-reference",
                "port_b_word_sel_bits": self.config.port_b_word_sel_bits,
                "weight_bus_bits": self.config.weight_bus_bits,
                "activation_bus_bits": self.config.activation_bus_bits,
                "max_delta": max_delta,
            },
            "rounds": self.round_results,
            "metrics": {
                "total_pipeline_stalls": None,
                "pipeline_stalls_measured": False,
                "pipeline_stalls_status": "not_modeled_without_AXI_FIFO_ready_valid",
                "raw_collision_count": sum(
                    result["raw_collision_count"] for result in self.round_results
                ),
                "modified_bit_count": modified_bits,
                "modified_bit_ratio": round(modified_ratio, 8),
                "max_modified_bit_count": self.config.max_modified_bits,
                "modified_bit_bound_pass": modified_pass,
                "negative_feedback_sign_pass": functional_pass,
                "phase_sync_seen": all(result["phase_sync"] == 1 for result in self.round_results),
                "reference_functional_pass": reference_pass,
            },
            "contract": {
                "wavefront": "cnt_next=(cnt+1)%16; rd_ptr=cnt; wr_ptr=(cnt-1)%16",
                "sram_word_window": "8-bit Port B selector covers all 256 64-bit words per bank; this reference exercises the packed low words",
                "pe_weight_layout": "feature-lane: four signed INT8 rows per 64-bit word; high 32 bits reserved",
                "delta_encoding": "packed signed INT8x4; one byte lane selected per row update",
                "c_gap_definition": "logit - target, target=0 in this reference run",
                "pipeline_stalls": "not measured; no AXI/FIFO ready-valid model exists",
            },
            "header_recalculation": self.header_recalculation(clock_mhz),
            "spec_issues": [issue.__dict__ for issue in self.config.issues()],
            "axi_contract": self.axi.contract(),
        }

    def write_json(self, path: os.PathLike[str] | str) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.run(), ensure_ascii=False, indent=2), encoding="utf-8")
        return output


def _signed_int8(value: int) -> int:
    value &= 0xFF
    return value - 256 if value >= 128 else value


def _to_signed_int32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value >= (1 << 31) else value


def _clamp_int(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


__all__ = [
    "AxiLiteRegisterMap",
    "MvuReferenceConfig",
    "MvuReferenceModel",
    "MvuSpecIssue",
    "PeArray16x16",
    "PlasticityEngine",
    "Sram32KbDualPort",
    "WavefrontController",
]
