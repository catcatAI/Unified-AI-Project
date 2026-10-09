from pathlib import Path

import yaml
from ai.hardware.mvu_reference import (
    AxiLiteRegisterMap,
    MvuReferenceConfig,
    MvuReferenceModel,
    PeArray16x16,
    Sram32KbDualPort,
    WavefrontController,
)

HEADER_SPEC_PATH = (
    Path(__file__).resolve().parents[2] / "hardware/components/wip/chip/mvu_header_spec.yaml"
)


def test_reference_config_exposes_spec_blockers() -> None:
    issues = MvuReferenceConfig().issues()
    issue_ids = {issue.issue_id for issue in issues}

    assert "port_b_word_select_width" in issue_ids
    assert "axi_sram_window" in issue_ids


def test_header_recalculation_derives_exact_geometry_and_bandwidth() -> None:
    result = MvuReferenceModel().header_recalculation(clock_mhz=250)

    assert result["scope"] == "one_configured_mvu_sram_instance"
    assert result["derived"]["total_sram_bits"] == 262144
    assert result["derived"]["total_sram_kib"] == 32.0
    assert result["derived"]["words_per_bank"] == 256
    assert result["derived"]["forward_bytes"] == 2048
    assert result["derived"]["forward_int8_values"] == 2048
    assert result["bandwidth"]["forward_gbps"] == 4096.0
    assert result["bandwidth"]["forward_gbs"] == 512.0
    assert result["bandwidth"]["side_per_bank_gbps"] == 16.0
    assert result["bandwidth"]["side_per_bank_gbs"] == 2.0
    assert result["bandwidth"]["side_16_bank_gbps"] == 256.0
    assert result["bandwidth"]["side_16_bank_gbs"] == 32.0
    assert result["checks_pass"] is True
    assert result["reset_and_commit"]["ownership_and_reset_gates_in_predicate"] is False


def test_normalized_header_matches_recalculation_model() -> None:
    spec = yaml.safe_load(HEADER_SPEC_PATH.read_text(encoding="utf-8"))
    result = MvuReferenceModel().header_recalculation(clock_mhz=250)
    declared = spec["declared"]

    assert declared["total_sram_size_bytes"] == result["derived"]["total_sram_bits"] // 8
    assert declared["sub_bank_count"] == 16
    assert declared["sub_bank_size_bytes"] == 2048
    assert declared["forward_bus_width_bits"] == result["bandwidth"]["forward_bus_bits_per_cycle"]
    assert (
        declared["plasticity_bus_width_bits"]
        == result["bandwidth"]["side_packet_bits_per_cycle_per_bank"]
    )
    assert declared["wavefront_cycles"] == result["timing"]["wavefront_cycles"]
    assert spec["status"] == "user_provided_candidate_not_frozen"


def test_wavefront_has_zero_bank_collisions() -> None:
    wavefront = WavefrontController()
    pointers = [wavefront.step() for _ in range(16)]

    assert [item["rd_ptr"] for item in pointers] == list(range(16))
    assert [item["wr_ptr"] for item in pointers] == [15, *range(15)]
    assert [item["phase_sync"] for item in pointers] == [0] * 15 + [1]
    assert wavefront.collision_count() == 0


def test_sram_uses_bounded_sparse_writes() -> None:
    config = MvuReferenceConfig()
    sram = Sram32KbDualPort(config)

    result = sram.write_port_b(
        bank=3,
        word_sel=4,
        delta=-100,
        hit_mask=0x000000FF,
    )

    assert result.bank == 3
    assert result.changed_bits > 0
    assert result.clamped_lanes == 1
    assert sram.modified_bit_count() == result.changed_bits


def test_pe_reference_calculates_expected_initial_logits() -> None:
    config = MvuReferenceConfig()
    pe = PeArray16x16(config)
    banks = [bytes([10]) * config.bank_bytes for _ in range(16)]

    result = pe.run([[1] * 16 for _ in range(16)], banks)

    assert result["logits"] == [10] * 16
    assert result["logits_bits"] == 256
    assert result["c_gap_bits"] == 512


def test_mvu_reference_run_meets_software_acceptance() -> None:
    result = MvuReferenceModel().run()

    assert result["status"] == "partial"
    assert result["validation"]["level"] == "L1"
    assert result["validation"]["professional_hdl_simulation"] is False
    assert result["validation"]["physical_hardware"] is False
    assert result["metrics"]["total_pipeline_stalls"] is None
    assert result["metrics"]["pipeline_stalls_measured"] is False
    assert result["metrics"]["reference_functional_pass"] is True
    assert result["metrics"]["raw_collision_count"] == 0
    assert result["metrics"]["modified_bit_bound_pass"] is True
    assert result["metrics"]["negative_feedback_sign_pass"] is True
    assert result["metrics"]["phase_sync_seen"] is True
    assert result["header_recalculation"]["derived"]["total_sram_kib"] == 32.0
    assert result["header_recalculation"]["timing"]["clock_mhz"] is None
    assert len(result["rounds"]) == 2
    assert all(item["logit_diff"][0] < 0 for item in result["rounds"])
    assert any(item["severity"] == "blocker" for item in result["spec_issues"])


def test_axi_contract_marks_original_window_as_incomplete() -> None:
    contract = AxiLiteRegisterMap().contract()

    assert contract["original_0x10_to_0x1c_window_complete"] is False
    assert contract["direct_sram_window"] == [0x1000, 0x8FFC]


def test_axi_indirect_window_can_preload_and_readback() -> None:
    config = MvuReferenceConfig()
    sram = Sram32KbDualPort(config)
    axi = AxiLiteRegisterMap(sram)
    payload = bytes(range(32))

    axi.preload(payload)

    assert axi.readback(len(payload)) == payload
    assert axi.contract()["indirect_sram_address"] == 0x20


def test_pe_uses_row_major_weights_from_all_banks() -> None:
    config = MvuReferenceConfig()
    pe = PeArray16x16(config)
    banks = [bytearray([0] * config.bank_bytes) for _ in range(16)]
    for feature in range(16):
        banks[feature][0] = feature + 1
        banks[feature][1] = (-(feature + 1)) & 0xFF

    result = pe.run([[1] * 16 for _ in range(16)], banks)

    assert result["logits"][:2] == [8, -9]
    assert result["logits"][2:] == [0] * 14


def test_repeated_runs_reset_reference_state() -> None:
    model = MvuReferenceModel()

    first = model.run()
    second = model.run()

    assert second["metrics"]["modified_bit_count"] == first["metrics"]["modified_bit_count"]
    assert second["metrics"]["negative_feedback_sign_pass"] is True
