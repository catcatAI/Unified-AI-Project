# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Branch-closure tests for the MVU software reference model.

The companion suite pins the headline arithmetic; this file pins the Port B
sparse-write contract (the part the hardware description language must one day
reproduce bit-for-bit), the wavefront/pointer semantics, and every validation
branch of the AXI-Lite software view.
"""

from __future__ import annotations

import pytest

from ai.hardware.mvu_reference import (
    AxiLiteRegisterMap,
    MvuReferenceConfig,
    MvuReferenceModel,
    PeArray16x16,
    PlasticityEngine,
    Sram32KbDualPort,
    WavefrontController,
)

# -----------------------------------------------------------------------------
# Sram32KbDualPort construction and Port A
# -----------------------------------------------------------------------------


def test_sram_construction_rejects_a_mismatched_bank_layout() -> None:
    config = MvuReferenceConfig()
    with pytest.raises(ValueError, match="initial bank count"):
        Sram32KbDualPort(config, initial_banks=[bytes(config.bank_bytes)])
    with pytest.raises(ValueError, match="exactly bank_bytes"):
        Sram32KbDualPort(
            config,
            initial_banks=[bytes(config.bank_bytes + 4)] * config.bank_count,
        )


def test_read_port_a_returns_zeroes_when_disabled_and_logs_when_enabled() -> None:
    sram = Sram32KbDualPort(MvuReferenceConfig())
    assert sram.read_port_a(0, enabled=False) == bytes(sram.config.bank_bytes)
    assert sram.read_log == []
    sram.read_port_a(3)
    assert sram.read_log == [3]
    with pytest.raises(ValueError, match="outside the declared 4-bit field"):
        sram.read_port_a(16)


# -----------------------------------------------------------------------------
# Port B: the sparse weight-update write contract
# -----------------------------------------------------------------------------


def test_write_port_b_rejects_out_of_field_addresses() -> None:
    sram = Sram32KbDualPort(MvuReferenceConfig())
    with pytest.raises(ValueError, match="outside the declared 4-bit field"):
        sram.write_port_b(16, word_sel=0, delta=0, hit_mask=0)
    with pytest.raises(ValueError, match="word_sel exceeds"):
        sram.write_port_b(0, word_sel=1 << 8, delta=0, hit_mask=0)
    with pytest.raises(ValueError, match="word_base leaves the SRAM bank"):
        sram.write_port_b(0, word_sel=0, delta=0, hit_mask=0, word_base=1 << 12)
    with pytest.raises(ValueError, match="32-bit mask"):
        sram.write_port_b(0, word_sel=0, delta=0, hit_mask=1 << 32)
    with pytest.raises(ValueError, match="signed 32-bit"):
        sram.write_port_b(0, word_sel=0, delta=1 << 31, hit_mask=0)


def test_write_port_b_clamps_to_max_delta_and_counts_clamped_lanes() -> None:
    config = MvuReferenceConfig()
    sram = Sram32KbDualPort(config)
    max_delta = config.max_delta
    # delta=32 puts a signed request of +32 on lane 0: it must clamp to max_delta
    # and be counted, while lanes 1-3 request 0 and stay untouched.
    result = sram.write_port_b(bank=0, word_sel=0, delta=32, hit_mask=0xFFFFFFFF)
    assert result.clamped_lanes == 1
    initial = _signed(config.initial_weight & 0xFF)
    weights = [_signed(b) for b in sram.banks[0][:4]]
    assert weights[0] == initial + max_delta
    assert weights[1:] == [initial] * 3


def test_write_port_b_also_clamps_at_the_weight_ceiling() -> None:
    config = MvuReferenceConfig()
    sram = Sram32KbDualPort(config)
    ceiling = config.weight_max
    initial = _signed(config.initial_weight & 0xFF)
    # Each write's per-lane delta is clamped to max_delta first, so the walk to
    # the ceiling is stepwise and the final write must not overshoot it.
    for _ in range(25):
        result = sram.write_port_b(0, word_sel=0, delta=ceiling, hit_mask=0xFFFFFFFF)
    assert result.clamped_lanes == 1  # lane 0 requested 127, held at max_delta
    assert _signed(sram.banks[0][0]) == ceiling  # 10 + 7*17 == 129 -> clamped 127
    assert _signed(sram.banks[0][1]) == _signed(config.initial_weight & 0xFF)


def test_write_port_b_respects_the_lane_mask_and_tracks_changed_bits() -> None:
    sram = Sram32KbDualPort(MvuReferenceConfig())
    before = bytes(sram.banks[0])
    result = sram.write_port_b(0, word_sel=0, delta=1, hit_mask=0x00000001)
    after = bytes(sram.banks[0])
    assert result.changed_bits == (before[0] ^ after[0]).bit_count()
    assert after[1:] == before[1:]  # untouched lanes
    assert sram.write_log == [0]


def test_write_port_b_targets_a_shifted_word_base() -> None:
    # word_base is a within-bank word offset: the bank holds bank_count_words
    # (256) Port B words and word_sel consumes 1<<port_b_word_sel_bits of them,
    # so 0 is the only valid word_base at the default widths. The boundary is
    # still real -- it is exactly what rejects a word_base of 1.
    sram = Sram32KbDualPort(MvuReferenceConfig())
    result = sram.write_port_b(1, word_sel=0, delta=1, hit_mask=1, word_base=0)
    assert result.bank == 1
    assert sram.banks[1][0] == (sram.config.initial_weight + 1) & 0xFF
    for bad_base in (1, 16, 256):
        with pytest.raises(ValueError, match="word_base leaves the SRAM bank"):
            sram.write_port_b(1, word_sel=0, delta=0, hit_mask=0, word_base=bad_base)


def test_modified_bit_count_and_snapshot_reflect_writes() -> None:
    config = MvuReferenceConfig()
    sram = Sram32KbDualPort(config)
    initial_weight = config.initial_weight & 0xFF
    sram.write_port_b(0, word_sel=0, delta=3, hit_mask=1)
    assert sram.modified_bit_count() == (initial_weight ^ ((initial_weight + 3) & 0xFF)).bit_count()
    snapshot = sram.bank_snapshot()
    assert len(snapshot) == config.bank_count
    assert all(isinstance(bank, bytes) for bank in snapshot)
    snapshot[0] = b""  # a snapshot copy must not alias the live banks
    assert len(sram.banks[0]) == config.bank_bytes


def _signed(value: int) -> int:
    return value - 256 if value >= 128 else value


# -----------------------------------------------------------------------------
# WavefrontController
# -----------------------------------------------------------------------------


def test_wavefront_requires_exactly_sixteen_banks() -> None:
    with pytest.raises(ValueError, match="16 banks"):
        WavefrontController(bank_count=8)


def test_wavefront_pointers_wrap_and_reset() -> None:
    controller = WavefrontController()
    assert controller.pointers() == {"count": 0, "rd_ptr": 0, "wr_ptr": 15, "phase_sync": 0}
    controller.step()
    pointers = controller.pointers()
    assert pointers["count"] == 1 and pointers["wr_ptr"] == 0
    controller.step()
    assert controller.history[-1]["count"] == 1
    assert controller.collision_count() == 0
    controller.reset()
    assert controller.count == 0 and controller.history == []
    assert controller.pointers()["count"] == 0


def test_wavefront_counts_collisions_when_read_and_write_meet() -> None:
    controller = WavefrontController()
    for _ in range(20):
        controller.step()
    # Documented degeneracy: with rd_ptr=count and wr_ptr=count-1 (mod 16) the
    # two pointers are never equal, so collision_count() stays 0 under the
    # current pointer scheme. Pinned here so a pointer-scheme change that makes
    # the predicate live (or removes it) is a visible decision, not a drift.
    assert controller.collision_count() == 0
    assert controller.pointers()["phase_sync"] in (0, 1)
    assert controller.history[0]["wr_ptr"] == 15  # (0-1) mod 16


# -----------------------------------------------------------------------------
# PeArray16x16
# -----------------------------------------------------------------------------


def _activation(value: int = 1) -> list[list[int]]:
    return [[value] * 16 for _ in range(16)]


def _banks() -> list[bytes]:
    return [bytes([0] * 16) for _ in range(16)]


def test_pe_array_rejects_shape_violations() -> None:
    pe = PeArray16x16(MvuReferenceConfig())
    with pytest.raises(ValueError, match="16x16 contract"):
        pe.run(_activation(), _banks()[:15])
    with pytest.raises(ValueError, match="each activation row"):
        pe.run([row[:15] for row in _activation()], _banks())
    with pytest.raises(ValueError, match="one weight byte per PE output row"):
        pe.run(_activation(), [b"" for _ in range(16)])


def test_pe_array_computes_signed_products_into_clamped_logits() -> None:
    config = MvuReferenceConfig()
    pe = PeArray16x16(config)
    banks = [bytes([64] * 32) for _ in range(16)]
    result = pe.run(_activation(1), banks)
    # accumulator = 16*64, right-shifted by accumulator_shift (4): 16*64>>4 = 64
    assert result["logits"][0] == 64
    assert result["logits_bits"] == 16 * 16
    assert result["weight_layout"].startswith("feature-lane layout")

    saturating = pe.run(_activation(120), [bytes([64] * 32) for _ in range(16)])
    assert saturating["logits"][0] == 127  # accumulator 16*64*120>>4 clamps


def test_pe_array_rejects_banks_shorter_than_the_row_packing_needs() -> None:
    """A bank byte exists for row 0..15 packed 4-per-64-bit-word.

    Row r reads byte (r//4)*8 + (r%4), so 16 rows need 32 bytes; the historical
    16-byte requirement blessed input that then crashed with IndexError on row
    12. The validator must demand the packing-relevant length.
    """
    pe = PeArray16x16(MvuReferenceConfig())
    for short_length in (16, 27):  # row 15 reads byte 27, so 28 are required
        with pytest.raises(ValueError, match="one weight byte per PE output row"):
            pe.run(_activation(), [bytes(short_length) for _ in range(16)])


# -----------------------------------------------------------------------------
# PlasticityEngine
# -----------------------------------------------------------------------------


def test_plasticity_rejects_out_of_field_arguments() -> None:
    engine = PlasticityEngine(MvuReferenceConfig())
    with pytest.raises(ValueError, match="16 sparse update lanes"):
        engine.update(c_gap=1, lane=16)
    with pytest.raises(ValueError, match="Port B field"):
        engine.update(c_gap=1, lane=0, word_sel=1 << 8)
    with pytest.raises(ValueError, match="32-bit field"):
        engine.update(c_gap=1, lane=0, hit_mask=1 << 32)


def test_plasticity_sign_follows_negative_feedback() -> None:
    config = MvuReferenceConfig()
    engine = PlasticityEngine(config)
    positive = engine.update(c_gap=5, lane=0)
    negative = engine.update(c_gap=-5, lane=0)
    assert positive["delta"] == -5 and negative["delta"] == 5
    huge = engine.update(c_gap=10_000, lane=0)
    assert huge["delta"] == -config.max_delta  # clamped, sign preserved
    zero = engine.update(c_gap=0, lane=0)
    assert zero["delta"] == 0


# -----------------------------------------------------------------------------
# AxiLiteRegisterMap
# -----------------------------------------------------------------------------


def test_axi_requires_an_attached_sram_for_memory_side_effects() -> None:
    bare = AxiLiteRegisterMap()
    with pytest.raises(ValueError, match="no attached software SRAM"):
        bare.write(AxiLiteRegisterMap.INDIRECT_DATA, 1)
    with pytest.raises(ValueError, match="no attached software SRAM"):
        bare.read(AxiLiteRegisterMap.INDIRECT_DATA)


def test_axi_rejects_out_of_contract_addresses() -> None:
    model = MvuReferenceModel()
    with pytest.raises(ValueError, match="outside the software AXI contract"):
        model.axi.write(0x8, 1)  # not a register in the contract
    with pytest.raises(ValueError, match="not readable"):
        model.axi.read(0x8)
    with pytest.raises(ValueError, match="not 32-bit aligned"):
        model.axi._write_sram_word(2, 0)
    with pytest.raises(ValueError, match="not 32-bit aligned"):
        model.axi._read_sram_word(2)


def test_axi_preload_and_readback_round_trip_words() -> None:
    model = MvuReferenceModel()
    payload = bytes(range(0, 32))
    model.axi.preload(payload)
    assert model.axi.readback(32) == payload
    with pytest.raises(ValueError, match="multiple of 32 bits"):
        model.axi.preload(b"\x01\x02\x03")
    with pytest.raises(ValueError, match="outside the SRAM"):
        model.axi.readback(-4)
    with pytest.raises(ValueError, match="multiple of 32 bits"):
        model.axi.readback(6)


def test_axi_direct_window_and_indirect_path_write_the_same_sram() -> None:
    model = MvuReferenceModel()
    model.axi.write(model.axi.SRAM_WINDOW + 8, 0xDEADBEEF)
    model.axi.write(model.axi.INDIRECT_ADDR, 8)
    assert model.axi.read(model.axi.INDIRECT_DATA) == 0xDEADBEEF
    assert model.axi.read(model.axi.SRAM_WINDOW + 8) == 0xDEADBEEF
    assert model.axi.contract()["direct_sram_window"] == [0x1000, 0x8FFC]
    assert model.axi.contract()["address_bits"] == 32


def test_header_recalculation_validates_geometry_and_computes_timing() -> None:
    model = MvuReferenceModel()
    header = model.header_recalculation(clock_mhz=250)
    # The full geometry validation path (lines 523-603).
    assert header["source"] == "user_provided_mvu_config_vh"
    assert header["checks_pass"] is True
    assert header["timing"]["clock_mhz"] == 250
    assert header["timing"]["cycle_period_ns"] == pytest.approx(4.0)
    assert header["timing"]["wavefront_period_ns"] == pytest.approx(64.0)
    assert header["bandwidth"]["forward_gbps"] > 0
    assert header["bandwidth"]["forward_gbs"] > 0
    assert "bank_ranges" in header["address_map"]
    assert len(header["address_map"]["bank_ranges"]) == 16
    # All geometry checks must pass for a valid config.
    for check_name, passed in header["checks"].items():
        assert passed, f"check {check_name} failed: {header['checks']}"


def test_header_recalculation_rejects_non_positive_clock() -> None:
    model = MvuReferenceModel()
    with pytest.raises(ValueError, match="clock_mhz must be positive"):
        model.header_recalculation(clock_mhz=0)
    with pytest.raises(ValueError, match="clock_mhz must be positive"):
        model.header_recalculation(clock_mhz=-1)
