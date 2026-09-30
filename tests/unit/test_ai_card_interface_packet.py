import re
from pathlib import Path

import pytest
import yaml
from ai.hardware.ai_card_reference import AiCardReferenceModel

PACKET_PATH = (
    Path(__file__).resolve().parents[2]
    / "hardware/ai_compute_card/angela_interface_freeze_packet.yaml"
)


def test_interface_packet_separates_conditions_from_pending_decisions() -> None:
    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))

    assert packet["status"] == "decision_verification_pending"
    assert packet["owner"] == "angela"
    assert packet["known_initial_conditions"]["host_link"]["payload_gbs_each_direction"] == 63.015
    assert (
        packet["known_initial_conditions"]["compute_contract"]["main_compute"]["partitions"] == 16
    )
    assert packet["known_initial_conditions"]["hierarchy"]["die_l1"]["target_mb"] == 32
    assert (
        packet["known_initial_conditions"]["terminology_guard"]["labels_are_not_interchangeable"]
        is True
    )
    assert {item["id"] for item in packet["pending_decisions"]} == {
        "die_l1_interface",
        "microarchitecture",
        "card_l2_selection",
        "host_l3_contract",
        "thermal_and_form_factor",
        "acceptance_priority",
        "cim_strip_array_plan",
        "die_l1_sky130_feasibility",
        "cim_package_topology",
        "cim_sensing_chain",
    }
    assert packet["freeze_record"]["status"] == "acceptance_check_pending"
    assert packet["freeze_record"]["decision_ids_frozen"] == []
    assert packet["known_initial_conditions"]["scope"]["automatic_component_ordering"] is False


def test_interface_packet_known_values_match_reference_model() -> None:
    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))
    result = AiCardReferenceModel().run()
    conditions = packet["known_initial_conditions"]

    assert (
        conditions["compute_contract"]["main_compute"]["fabric_width_bits"]
        == result["requirements"]["main_width_bits"]
    )
    assert (
        conditions["compute_contract"]["secondary_compute"]["update_width_bits"]
        == result["requirements"]["weight_update_width_bits"]
    )
    assert (
        conditions["compute_contract"]["main_compute"]["raw_bandwidth_gbps"]
        == result["bandwidth"]["main_internal_raw_gbps"]
    )
    assert (
        conditions["compute_contract"]["main_compute"]["raw_bandwidth_gbs"]
        == result["bandwidth"]["main_internal_raw_gbs"]
    )
    assert (
        conditions["compute_contract"]["secondary_compute"]["raw_bandwidth_gbps"]
        == result["bandwidth"]["weight_update_internal_raw_gbps"]
    )
    assert (
        conditions["compute_contract"]["secondary_compute"]["raw_bandwidth_gbs"]
        == result["bandwidth"]["weight_update_internal_raw_gbs"]
    )
    assert (
        conditions["host_link"]["payload_gbs_each_direction"]
        == result["bandwidth"]["pcie_effective_gbs_each_direction"]
    )
    assert conditions["hierarchy"]["die_l1"]["target_mb"] == result["cache"]["target_mb"]
    assert conditions["budgets"]["prototype_bom_cap_usd"] == result["cost"]["prototype_bom_cap"]
    assert result["design_verification"]["technical_checks_pass"] is True
    assert packet["freeze_record"]["environment_support_may_fill_missing_architecture"] is False


def test_packet_cim_evidence_matches_the_measured_fixture() -> None:
    """The packet must not drift away from what was actually measured.

    The packet previously reported the superseded first strip fixture, whose
    weight response was 1:2.07:4.43:8.95, while describing a defect the current
    gate-strapped fixture had already fixed. Binding the packet to the module
    fixture makes that class of drift a test failure instead of a silent
    contradiction in an architecture document.
    """
    from ai.hardware.cim_strip_reference import WEIGHT_RESPONSE_MEASUREMENT

    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))
    evidence = packet["cim_planning_evidence"]
    measurements = evidence["ngspice_tt_measurements"]

    assert measurements["fixture"] == WEIGHT_RESPONSE_MEASUREMENT["fixture"]
    assert measurements["single_hot_currents_a"] == (
        WEIGHT_RESPONSE_MEASUREMENT["single_hot_currents_a"]
    )
    assert measurements["kcl_sum_word_1111_a"] == (WEIGHT_RESPONSE_MEASUREMENT["word_1111_sum_a"])
    assert measurements["weight_ratio_measured"] == [1.0, 2.0, 4.0, 8.0]
    assert measurements["weight_linearity_within_1_lsb_at_5_bits"] is True
    assert evidence["evidence_correction"]["superseded_fixture"] == "DOT4"
    assert evidence["reproducible_by"].endswith("CimStripReferenceModel")


def test_packet_power_findings_match_the_derived_model() -> None:
    """Recorded power and energy figures must be the ones the model derives."""
    from ai.hardware.cim_strip_reference import CimStripReferenceModel

    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))
    findings = packet["cim_planning_evidence"]["power_and_energy_findings"]
    result = CimStripReferenceModel().run()
    envelope = result["power_envelope"]
    expected = envelope["scenarios"][0]

    assert findings["drafted_energy_pj_per_mac"] == pytest.approx(
        result["published_comparison"]["modelled_energy_pj_per_mac"], rel=1e-3
    )
    assert findings["card_budget_multiple"] == pytest.approx(
        envelope["card_fills_board_budget_x"], rel=1e-3
    )
    assert findings["package_power_w_expected"] == pytest.approx(
        expected["package_power_w"], rel=1e-3
    )
    assert findings["card_power_w_at_4_packages"] == pytest.approx(
        expected["card_power_w"], rel=1e-3
    )
    assert findings["card_budget_w"] == envelope["board_power_budget_w"]
    assert findings["status"].startswith("blocking")


CIM_DRAFT_PATH = (
    Path(__file__).resolve().parents[2] / "hardware/ai_compute_card/cim_freeze_draft.yaml"
)


def test_validated_design_in_draft_matches_the_model() -> None:
    """The draft's recommended design must be the one the model derives.

    Recording a design point in an architecture document without binding it to
    the code that produced it is how the stale-evidence problem started, so the
    numbers are compared rather than trusted.
    """
    from ai.hardware.cim_strip_reference import CimStripReferenceModel

    draft = yaml.safe_load(CIM_DRAFT_PATH.read_text(encoding="utf-8"))
    recorded = draft["validated_current_process_design"]
    result = CimStripReferenceModel().recommended_design()
    point = result["design_point"]

    assert point is not None
    assert recorded["operating_point"]["array_rail_v"] == point["array_vds_v"]
    assert recorded["operating_point"]["input_swing_v"] == point["input_vgs_max_v"]
    assert recorded["operating_point"]["sense_window_ns"] == pytest.approx(
        point["sense_time_s"] * 1e9
    )
    assert recorded["results"]["energy_pj_per_mac"] == pytest.approx(
        point["energy_pj_per_mac"], rel=1e-2
    )
    assert recorded["results"]["card_power_w"] == pytest.approx(point["card_power_w"], rel=1e-2)
    assert recorded["results"]["noise_limited_resolution_bits"] == pytest.approx(
        point["resolution_bits"], rel=1e-2
    )
    assert recorded["gates_all_passed"] is True
    assert point["passes_all_gates"] is True


def test_validated_design_records_its_own_limits() -> None:
    """A design that does not state what is unverified is not yet a design."""
    draft = yaml.safe_load(CIM_DRAFT_PATH.read_text(encoding="utf-8"))
    recorded = draft["validated_current_process_design"]

    assert recorded["status"] == "derived_and_gate_checked_awaiting_acceptance"
    assert recorded["sensitivity"]["remaining_unverified"]
    assert recorded["explicit_non_claims"]
    assert "not yet a decision" in recorded["note"]
    # The bit-slicing correction must stay on record.
    assert "correction_to_bit_slicing" in recorded


def test_draft_gates_distinguish_drafted_from_validated_configuration() -> None:
    """Two gates fail at the drafted point and pass at the validated one.

    Recording only the failure would misrepresent the current process; recording
    only the pass would hide that the drafted numbers were wrong.
    """
    draft = yaml.safe_load(CIM_DRAFT_PATH.read_text(encoding="utf-8"))
    gates = draft["validation_gates_before_decision"]

    power = gates["card_level_array_power_within_300w"]
    assert power["status"] == "not_satisfied_at_drafted_configuration"
    assert power["satisfied_by_validated_design"] is True

    energy = gates["cim_energy_competitive_with_digital"]
    assert energy["status"] == "not_satisfied_at_drafted_configuration"
    assert energy["satisfied_by_validated_design"] is True

    assert gates["weight_linearity_within_1_lsb_at_5_bits"]["status"] == (
        "satisfied_by_measurement"
    )
    assert gates["remaining_unverified"]["status"] == "blocking_decision"


def test_packet_records_that_the_blockers_are_configuration_not_process() -> None:
    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))
    findings = packet["cim_planning_evidence"]["power_and_energy_findings"]
    cause = findings["root_cause_is_configuration_not_process"]

    assert cause["operating_point"].startswith("0.3V array rail")
    assert "CimStripReferenceModel" in cause["note"]
    assert "sense window" in cause["binding_constraint"]


def test_single_die_status_does_not_overclaim() -> None:
    draft = yaml.safe_load(CIM_DRAFT_PATH.read_text(encoding="utf-8"))
    recorded = draft["single_die_status"]

    assert recorded["status"] == "array_designed_drc_clean_extracted_and_simulated"
    # The honest limits have to stay on record next to the result.
    assert recorded["still_open"]
    assert recorded["explicit_non_claims"]
    assert recorded["pdk_constraint_found"]["drafted_cell_width_um"] < (
        recorded["pdk_constraint_found"]["min_characterised_nfet_width_um"]
    )
    # Geometry-fused is not weight-programmable, and the document must say so.
    assert any("geometry-fused" in item for item in recorded["still_open"])


def test_packet_records_that_the_single_die_target_is_not_reachable() -> None:
    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))
    correction = packet["single_die_correction"]

    assert correction["single_die_answer"]["one_megabyte_of_int8_weights_mm2"] > 4.0
    assert "not reachable on a single die" in correction["single_die_answer"]["verdict"]
    assert correction["verified_design_status"]["array_layout"] == "magic DRC 0 errors"
    assert correction["not_proven"]
