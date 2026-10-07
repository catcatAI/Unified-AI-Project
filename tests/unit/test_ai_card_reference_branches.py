# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Branch-closure tests for the AI-card reference model.

The companion suite pins the happy paths and the headline invariants; this file
pins every validation branch and each state machine's edge cases, because these
validators are what stop a bad card spec from being quietly accepted.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ai.hardware.ai_card_reference as ai_card_reference
from ai.hardware.ai_card_reference import AiCardReferenceConfig, AiCardReferenceModel

# -----------------------------------------------------------------------------
# __post_init__ validation matrix — every guard must be able to fire
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("pcie_generation", 0, "PCIe generation and lane count"),
        ("pcie_lanes", 0, "PCIe generation and lane count"),
        ("pcie_signaling_rate_gbps_per_lane", 0.0, "PCIe signaling rate"),
        ("pcie_payload_encoding_ratio", 0.0, "PCIe payload encoding ratio"),
        ("pcie_payload_encoding_ratio", 1.5, "PCIe payload encoding ratio"),
        ("main_width_bits", 0, "internal fabric widths"),
        ("weight_update_width_bits", 0, "internal fabric widths"),
        ("main_compute_partitions", 0, "compute and update partition counts"),
        ("secondary_update_partitions", 0, "compute and update partition counts"),
        ("secondary_update_partition_width_bits", 0, "secondary update partition width"),
        ("target_clock_mhz", 0, "target clock and DMA tile size"),
        ("dma_tile_bytes", 0, "target clock and DMA tile size"),
        ("dma_credit_limit", 0, "DMA credits must be positive"),
        ("cache_target_mb", -1, "DMA credits must be positive"),
        ("external_memory_gb", 0, "external memory and prototype power limit"),
        ("prototype_power_limit_w", 0.0, "external memory and prototype power limit"),
        ("preferred_power_limit_w", 0.0, "preferred power limit must be positive"),
        ("prototype_bom_cap_usd", -1, "preferred power limit must be positive"),
    ],
)
def test_config_rejects_invalid_fields(field: str, value: object, message: str) -> None:
    import dataclasses

    base = AiCardReferenceConfig()
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(base, **{field: value})


def test_config_derives_pcie_effective_bandwidth_when_left_unset() -> None:
    config = AiCardReferenceConfig()
    # 32 GT/s x 16 lanes x 128b/130b
    assert config.pcie_effective_gbps_each_direction == pytest.approx(504.123, rel=1e-3)


def test_config_keeps_an_explicit_matching_bandwidth_and_rejects_a_mismatch() -> None:
    exact = 32.0 * 16.0 * (128.0 / 130.0)
    config = AiCardReferenceConfig(pcie_effective_gbps_each_direction=exact)
    assert config.pcie_effective_gbps_each_direction == pytest.approx(exact, rel=1e-9)
    with pytest.raises(ValueError, match="must match signaling and encoding"):
        AiCardReferenceConfig(pcie_effective_gbps_each_direction=exact + 0.001)


def test_config_defaults_the_cache_partition_map() -> None:
    config = AiCardReferenceConfig()
    assert config.cache_partitions_mb == {"activation": 8, "weights": 16, "staging": 8}


# -----------------------------------------------------------------------------
# cache_report / simulate_dma branches
# -----------------------------------------------------------------------------


def test_cache_report_rejects_a_negative_partition() -> None:
    import dataclasses

    config = dataclasses.replace(
        AiCardReferenceConfig(), cache_partitions_mb={"activation": -1}
    )
    with pytest.raises(ValueError, match="non-negative"):
        AiCardReferenceModel(config).cache_report()


def test_dma_stalls_track_credit_exhaustion() -> None:
    model = AiCardReferenceModel()
    stalled = model.simulate_dma(tile_count=4, credits=1)
    flowing = model.simulate_dma(tile_count=4, credits=4)
    assert stalled["backpressure_events"] == 3
    assert flowing["backpressure_events"] == 0
    assert stalled["completed_tiles"] == 4
    assert stalled["credit_limit"] == 1


# -----------------------------------------------------------------------------
# simulate_weight_updates branches
# -----------------------------------------------------------------------------


def _update(sequence: int, payload: bytes = b"x") -> dict:
    return {"sequence": sequence, "payload": payload}


def test_weight_updates_reject_every_bad_sequence_shape() -> None:
    model = AiCardReferenceModel()
    for bad in (
        [_update(True)],  # bool is not an int here
        [_update("7")],  # not an int at all
        [_update(-1)],  # negative
        [_update(1), _update(1)],  # not strictly increasing
        [_update(2), _update(1)],  # decreasing
        [{"sequence": 1, "payload": "not-bytes"}],  # payload type
    ):
        with pytest.raises(ValueError):
            model.simulate_weight_updates(bad)


def test_weight_updates_commit_in_order_and_report_the_last_sequence() -> None:
    model = AiCardReferenceModel()
    result = model.simulate_weight_updates([_update(1, b"a"), _update(5, b"bb")])
    assert result["update_count"] == 2
    assert result["ordering_validated"] is True
    assert result["committed"][-1]["sequence"] == 5
    assert result["committed"][-1]["bytes"] == 2
    assert result["committed"][-1]["state"] == "committed"


# -----------------------------------------------------------------------------
# simulate_sparse_partition_update branches
# -----------------------------------------------------------------------------


def _sparse_args(payload_len: int = 128, masks: int = 16, deltas: int = 128):
    return (
        bytes(payload_len),
        [0] * masks,
        [0] * deltas,
    )


def test_sparse_update_rejects_width_and_mask_contract_violations() -> None:
    model = AiCardReferenceModel()
    with pytest.raises(ValueError, match="payload width"):
        model.simulate_sparse_partition_update(b"short", [0] * 16, [0] * 128)
    with pytest.raises(ValueError, match="hit mask count"):
        model.simulate_sparse_partition_update(*_sparse_args(masks=8))
    with pytest.raises(ValueError, match="delta count"):
        model.simulate_sparse_partition_update(*_sparse_args(deltas=8))
    with pytest.raises(ValueError, match="8-bit"):
        payload, masks, deltas = _sparse_args()
        masks[0] = 0x1FF
        model.simulate_sparse_partition_update(payload, masks, deltas)
    with pytest.raises(ValueError, match="signed INT8"):
        payload, masks, deltas = _sparse_args()
        deltas[0] = 200
        model.simulate_sparse_partition_update(payload, masks, deltas)


def test_sparse_update_applies_only_masked_bytes_and_counts_them() -> None:
    model = AiCardReferenceModel()
    payload = bytes(128)
    masks = [0] * 16
    deltas = [0] * 128
    masks[0] = 0b11  # partition 0, lanes 0 and 1 -> payload bytes 0 and 1
    deltas[0], deltas[1] = 0x01, -1  # signed INT8 in, written back two's complement
    result = model.simulate_sparse_partition_update(payload, masks, deltas)
    assert result["modified_bytes"] == 2
    assert result["selected_bytes"] == 2
    assert result["unselected_bytes_unchanged"] is True
    updated = bytes.fromhex(result["updated_payload_hex"])
    assert updated[0] == 1 and updated[1] == 0xFF


# -----------------------------------------------------------------------------
# simulate_main_compute validation branches
# -----------------------------------------------------------------------------


def _matrix(value: int = 1) -> list[list[int]]:
    return [[value] * 16 for _ in range(16)]


def test_main_compute_rejects_shape_and_value_violations() -> None:
    model = AiCardReferenceModel()
    with pytest.raises(ValueError, match="inputs must be a 16x16"):
        model.simulate_main_compute(_matrix()[:15], _matrix())
    with pytest.raises(ValueError, match="inputs must be a 16x16"):
        model.simulate_main_compute([[1] * 15] * 16, _matrix())
    with pytest.raises(ValueError, match="weights must be a 16x16"):
        model.simulate_main_compute(_matrix(), [[0] * 16] * 15)
    with pytest.raises(ValueError, match="signed INT8"):
        model.simulate_main_compute([[128] * 16] * 16, _matrix())
    with pytest.raises(ValueError, match="signed INT8"):
        model.simulate_main_compute(_matrix(), [[True] + [0] * 15] * 16)
    with pytest.raises(ValueError, match="signed INT8"):
        model.simulate_main_compute(_matrix(), [[-129] + [0] * 15] * 16)


# -----------------------------------------------------------------------------
# run() / write_json()
# -----------------------------------------------------------------------------


def test_run_is_complete_and_write_json_round_trips(tmp_path: Path) -> None:
    model = AiCardReferenceModel()
    result = model.run()
    for key in (
        "schema_version",
        "status",
        "bandwidth",
        "hierarchy",
        "ownership",
        "cache",
        "power",
        "cost",
        "dma",
        "weight_updates",
        "design_verification",
        "blockers",
    ):
        assert key in result, key

    out = tmp_path / "nested" / "packet.json"
    assert model.write_json(out) == out
    assert "schema_version" in out.read_text(encoding="utf-8")


def test_cost_report_refuses_to_estimate_without_quotes() -> None:
    report = AiCardReferenceModel().cost_report()
    assert report["decision"] == "BLOCKED_PENDING_QUOTES"
    assert report["known_total"] is None
    assert all(item["status"] == "RFQ_REQUIRED" for item in report["items"])


def test_module_exports_are_deliberate() -> None:
    assert set(ai_card_reference.__all__) == {
        "AiCardReferenceConfig",
        "AiCardReferenceModel",
    }


def test_config_rejects_mismatched_secondary_update_partitions() -> None:
    # secondary_update_partitions * secondary_update_partition_width_bits must
    # equal weight_update_width_bits (line 54).
    import dataclasses

    base = AiCardReferenceConfig()
    # 32 weight_update_width_bits = 8 partitions * 4 bits/partition
    with pytest.raises(ValueError, match="secondary update partitions must exactly cover the update bus"):
        dataclasses.replace(
            base,
            weight_update_width_bits=32,
            secondary_update_partitions=8,
            secondary_update_partition_width_bits=3,  # 8*3=24 != 32
        )


def test_simulate_dma_rejects_negative_tile_count() -> None:
    model = AiCardReferenceModel()
    with pytest.raises(ValueError, match="tile_count must be non-negative"):
        model.simulate_dma(tile_count=-1)


def test_simulate_dma_rejects_non_positive_credits() -> None:
    model = AiCardReferenceModel()
    with pytest.raises(ValueError, match="DMA credit limit must be positive"):
        model.simulate_dma(tile_count=1, credits=0)


def test_simulate_dma_rejects_negative_credits() -> None:
    model = AiCardReferenceModel()
    with pytest.raises(ValueError, match="DMA credit limit must be positive"):
        model.simulate_dma(tile_count=1, credits=-1)
