# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Audit tests for hardware/edge_card/edge_card_spec.yaml.

The spec is a decision record written before any hardware exists, so these
tests re-derive every committed number (link payload, working-set envelope,
decode bandwidth bound, power envelope) from first principles instead of
trusting the transcribed digits.
"""

from __future__ import annotations

from pathlib import Path

import yaml

SPEC_PATH = Path(__file__).resolve().parents[2] / "hardware/edge_card/edge_card_spec.yaml"


def _load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# provenance / housekeeping
# -----------------------------------------------------------------------------
def test_spec_status_and_ownership() -> None:
    spec = _load_spec()

    assert spec["status"] == "draft_awaiting_acceptance_check"
    assert spec["owner"] == "angela"
    assert spec["schema_version"] == "edge-card-spec/1"
    assert spec["current_target"].startswith("L0")


def test_spec_sources_carry_url_and_claim() -> None:
    spec = _load_spec()

    assert spec["sources"], "sources section must not be empty"
    for source_id, source in spec["sources"].items():
        assert source_id.startswith("src_"), source_id
        assert source["what"], source_id
        assert source["url"], source_id
        assert source["type"], source_id


def test_spec_declares_no_prices() -> None:
    spec = _load_spec()

    assert spec["component_selection_policy"]["price_status_default"] == "quote_required"
    assert spec["component_selection_policy"]["do_not_purchase_without_human_approval"] is True
    assert any("no prices" in claim for claim in spec["explicit_non_claims"])
    assert not SPEC_PATH.read_text(encoding="utf-8").count("price_usd")


# -----------------------------------------------------------------------------
# product decision: Gen4 x1 endpoint
# -----------------------------------------------------------------------------
def test_product_decision_locks_gen4_x1() -> None:
    spec = _load_spec()
    host = spec["host_interface"]

    assert spec["product_decision"]["host_link"] == "PCIe-Gen4-x1-endpoint"
    assert host["gen"] == 4.0
    assert host["lanes"] == 1
    assert host["signaling_rate_gbps_per_lane"] == 16
    assert host["payload_encoding"] == "128b/130b"
    assert host["endpoint_mechanism"]["module_speed_cap"] == "gen4"
    assert host["endpoint_mechanism"]["flr"] == "required"
    assert host["endpoint_mechanism"]["msi"] == "required"


def test_pcie_gen4_x1_payload_derivation() -> None:
    host = _load_spec()["host_interface"]

    raw_gbps = host["signaling_rate_gbps_per_lane"] * 128 / 130
    payload_gbs = raw_gbps / 8

    assert round(raw_gbps, 3) == host["payload_gbps_each_direction"] == 15.754
    assert round(payload_gbs, 3) == host["payload_gbs_each_direction"] == 1.969
    assert host["achievable_dma_gbs_each_direction_min"] <= payload_gbs


def test_rejected_orin_nano_records_gen3_reason() -> None:
    spec = _load_spec()
    rejected = {c["id"]: c for c in spec["compute"]["rejected_compute_candidates"]}

    nano = rejected["jetson-orin-nano-8gb"]
    assert "Gen3" in nano["reason"]
    assert "v1.7" in nano["reason"]
    assert nano["source"] == "src_orin_nano_ds"
    assert "fpga-path-agilex-versal" in rejected
    assert "discrete-gpu-low-end" in rejected


# -----------------------------------------------------------------------------
# working set: model + KV + OS must fit module memory
# -----------------------------------------------------------------------------
def test_working_set_arithmetic_and_envelope_fit() -> None:
    envelope = _load_spec()["model_target"]["working_set_gb"]
    kv = envelope["kv_cache_budget_gb"]["value"]
    os_reserve = envelope["os_reserve_gb"]

    e2b = 2.9 + kv + os_reserve
    e4b = 4.5 + kv + os_reserve
    twelve_b = 6.7 + kv + os_reserve

    assert kv == 1.5
    assert round(e2b, 1) == envelope["e2b_q4_0_32k"] == 5.4
    assert round(e4b, 1) == envelope["e4b_q4_0_32k"] == 7.0
    assert round(twelve_b, 1) == envelope["twelve_b_q4_0_32k"] == 9.2

    module_gb = _load_spec()["memory"]["module_lpddr5_gb"]
    assert e2b <= 8 <= module_gb, "E2B Q4_0 must fit even the 8GB floor SKU"
    assert twelve_b <= module_gb, "12B stretch goal must fit the 16GB baseline"


def test_model_target_weights_match_google_table() -> None:
    weights = _load_spec()["model_target"]["primary"]["weights_gb"]

    assert weights == {
        "bf16": 11.4,
        "sfp8": 5.7,
        "q4_0": 2.9,
        "mobile_qat": 1.1,
        "mobile_qat_text_only": 0.84,
    }


# -----------------------------------------------------------------------------
# performance budget: decode is bandwidth-bound
# -----------------------------------------------------------------------------
def test_decode_targets_within_bandwidth_bound() -> None:
    budget = _load_spec()["performance_budget"]
    assumptions = budget["decode_assumptions"]
    targets = budget["decode_tok_s"]

    bw = assumptions["memory_bandwidth_gbs"]
    eff_min, eff_max = assumptions["stream_efficiency_range"]
    assert bw == 102.4
    assert eff_min <= eff_max

    q4_derived = [
        round(bw * eff_min / assumptions["e2b_q4_0_weights_read_gb"], 1),
        round(bw * eff_max / assumptions["e2b_q4_0_weights_read_gb"], 1),
    ]
    mobile_derived = [
        round(bw * eff_min / assumptions["e2b_mobile_weights_read_gb"], 1),
        round(bw * eff_max / assumptions["e2b_mobile_weights_read_gb"], 1),
    ]

    assert q4_derived == targets["derived_e2b_q4_0_range"] == [23.5, 27.7]
    assert mobile_derived == targets["derived_e2b_mobile_range"] == [51.2, 60.5]
    assert targets["target_e2b_q4_0_min"] < q4_derived[0]
    assert targets["target_e2b_mobile_min"] < mobile_derived[0]


def test_host_link_load_time_within_target() -> None:
    host = _load_spec()["host_interface"]
    budget = _load_spec()["performance_budget"]["host_link"]

    load_seconds = 2.9 / host["achievable_dma_gbs_each_direction_min"]
    assert load_seconds <= budget["cold_load_e2b_q4_0_from_host_s_max"]


# -----------------------------------------------------------------------------
# power: slot-only, no auxiliary connector
# -----------------------------------------------------------------------------
def test_power_budget_sums_to_cap_within_slot() -> None:
    power = _load_spec()["power_and_thermal"]
    budget = power["board_budget_w"]

    summed = budget["module_maxn"] + budget["m2_nvme"] + budget["fan"]
    summed += budget["rails_and_conversion_overhead"]

    assert summed == budget["tdp_cap"] == 35
    assert budget["tdp_cap"] <= power["slot_power"]["slot_available_12v_w"] == 75
    assert power["slot_power"]["auxiliary_connector"] == "none"
    assert power["default_mode"] == "25W-MAXN"
    assert power["cooling"] == "single-slot-heatsink-plus-fan"


# -----------------------------------------------------------------------------
# acceptance structure mirrors the task-contract style
# -----------------------------------------------------------------------------
def test_acceptance_levels_cover_l0_through_l4() -> None:
    spec = _load_spec()

    assert spec["acceptance_levels"] == {
        "L0": "specification_and_interface_contract",
        "L1": "software_validation_on_devkit",
        "L2": "carrier_schematic_power_thermal_and_mechanical_analysis",
        "L3": "endpoint_driver_and_host_link_validation",
        "L4": "board_validation_sustained_workload",
    }
    for level in ("L0", "L1", "L2", "L3", "L4"):
        assert spec["acceptance"][level], level


def test_open_items_carry_risk_and_blocking_level() -> None:
    spec = _load_spec()

    assert spec["open_items"], "open risks must be listed, not hidden"
    for item in spec["open_items"]:
        assert item["id"]
        assert item["risk"] in {"low", "medium", "high"}
        assert item["blocks"] in {"L0", "L1", "L2", "L3", "L4"}
        assert item["question"].strip()
