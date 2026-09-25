import pytest
from ai.hardware.ai_card_reference import AiCardReferenceConfig, AiCardReferenceModel


def test_pcie_and_internal_datapaths_are_not_conflated() -> None:
    model = AiCardReferenceModel()
    report = model.bandwidth_report()

    assert report["pcie_raw_gbps_each_direction"] == 512.0
    assert report["pcie_effective_gbps_each_direction"] == pytest.approx(504.123, rel=1e-3)
    assert report["pcie_effective_gbs_each_direction"] == pytest.approx(63.015, rel=1e-3)
    assert report["main_internal_raw_gbps"] == 4096.0
    assert report["main_internal_raw_gbs"] == 512.0
    assert report["weight_update_internal_raw_gbps"] == 256.0
    assert report["weight_update_internal_raw_gbs"] == 32.0
    assert report["main_to_host_ratio"] == pytest.approx(512.0 / 63.015, rel=1e-3)
    assert report["main_is_internal_fabric"] is True
    assert report["bandwidth_derivation"].startswith("bits_per_cycle")


def test_die_update_partitions_and_memory_hierarchy_are_explicit() -> None:
    model = AiCardReferenceModel()
    hierarchy = model.hierarchy_report()
    ownership = model.ownership_report()

    assert hierarchy["die"]["secondary_compute"]["partitions"] == 16
    assert hierarchy["die"]["secondary_compute"]["cache_partition_width_bits"] == 64
    assert hierarchy["die"]["secondary_compute"]["input_width_bits"] == 1024
    assert hierarchy["die"]["l1_cache"]["implementation"] == "self_developed_cache"
    assert hierarchy["card"]["l2_memory"]["implementation"] == "purchased_memory"
    assert hierarchy["host"]["l3"]["interface"] == "PCIe"
    assert hierarchy["host"]["l3"]["target"] == "host_memory_or_storage"
    assert ownership["product_architecture"] == "angela"
    assert ownership["environment_and_validation"] == "environment_support"


def test_main_compute_reference_matches_identity_matrix() -> None:
    model = AiCardReferenceModel()
    identity = [[1 if row == column else 0 for column in range(16)] for row in range(16)]

    result = model.simulate_main_compute(identity, identity)

    assert result["outputs"] == identity
    assert result["accumulator_width_bits"] == 32
    assert result["used_llm"] is False


def test_sparse_update_preserves_unselected_bytes() -> None:
    model = AiCardReferenceModel()
    payload = bytes(range(128))

    result = model.simulate_sparse_partition_update(
        payload,
        [0x01] * 16,
        [1] * 128,
    )

    assert result["update_width_bits"] == 1024
    assert result["partition_count"] == 16
    assert result["partition_width_bits"] == 64
    assert result["selected_bytes"] == 16
    assert result["unselected_bytes_unchanged"] is True
    assert result["mapping_status"] == "project_ai_interface_freeze_required"


def test_design_verification_passes_software_usable_checks() -> None:
    result = AiCardReferenceModel().design_verification()

    assert result["status"] == "reference_verified_pending_angela_interface_freeze"
    assert result["technical_checks_pass"] is True
    assert result["gates"]["physical_hardware"] is False
    assert result["gates"]["hdl_gate_level"] is False


def test_cache_and_power_envelopes_fit_prototype_limits() -> None:
    model = AiCardReferenceModel()
    cache = model.cache_report()
    power = model.power_report()

    assert cache["total_mb"] == 32
    assert cache["unallocated_mb"] == 0
    assert cache["address_overlap"] is False
    assert cache["addresses_mb"]["weights"]["start_mb"] == 8
    assert cache["within_target"] is True
    assert power["planning_total_w"] == 300.0
    assert power["within_prototype_limit"] is True
    assert power["measurement_status"] == "planning_only_not_measured"


def test_cost_remains_blocked_until_manufacturer_quotes_exist() -> None:
    report = AiCardReferenceModel().cost_report()

    assert report["prototype_bom_cap"] == 3000
    assert report["known_total"] is None
    assert report["decision"] == "BLOCKED_PENDING_QUOTES"
    assert all(item["unit_cost"] is None for item in report["items"])


def test_weight_update_sequence_is_atomic_and_ordered() -> None:
    result = AiCardReferenceModel().simulate_weight_updates(
        [
            {"sequence": 1, "payload": b"abc"},
            {"sequence": 2, "payload": b"defg"},
        ]
    )

    assert result["update_count"] == 2
    assert result["ordering_validated"] is True
    assert result["per_update_digest_contract"] is True
    assert result["rollback_implemented"] is False
    assert all(item["state"] == "committed" for item in result["committed"])
    with pytest.raises(ValueError, match="strictly increasing"):
        AiCardReferenceModel().simulate_weight_updates(
            [
                {"sequence": 2, "payload": b"abc"},
                {"sequence": 1, "payload": b"defg"},
            ]
        )


def test_ai_card_reference_is_software_only_and_partial_until_quotes() -> None:
    result = AiCardReferenceModel(AiCardReferenceConfig()).run()

    assert result["status"] == "partial"
    assert result["validation"]["level"] == "L1"
    assert result["validation"]["professional_hdl_simulation"] is False
    assert result["validation"]["physical_hardware"] is False
    assert result["checks"]["cost_verified"] is False
    assert result["checks"]["secondary_update_partition_contract"] is True
    assert result["checks"]["design_reference_verified"] is True
    assert result["checks"]["weight_update_contract"] is True
    assert result["hierarchy"]["die"]["l1_cache"]["scope"] == "die_internal"
    assert result["terminology_guard"]["labels_are_not_interchangeable"] is True
    assert result["bandwidth"]["main_internal_raw_gbps"] == 4096.0
    assert result["bandwidth"]["main_internal_raw_gbs"] == 512.0
    assert result["bandwidth"]["weight_update_internal_raw_gbps"] == 256.0
    assert result["bandwidth"]["weight_update_internal_raw_gbs"] == 32.0


def test_invalid_secondary_partition_contract_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly cover"):
        AiCardReferenceConfig(
            secondary_update_partitions=8,
            secondary_update_partition_width_bits=64,
        )


def test_invalid_bandwidth_configuration_is_rejected() -> None:
    with pytest.raises(ValueError, match="effective bandwidth"):
        AiCardReferenceConfig(pcie_effective_gbps_each_direction=64.0)


def test_dma_rejects_zero_credit_limit() -> None:
    with pytest.raises(ValueError, match="credit limit"):
        AiCardReferenceModel().simulate_dma(credits=0)
