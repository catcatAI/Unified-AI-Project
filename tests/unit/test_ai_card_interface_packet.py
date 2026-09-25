from pathlib import Path

import yaml
from ai.hardware.ai_card_reference import AiCardReferenceModel


PACKET_PATH = Path(__file__).resolve().parents[2] / "hardware/ai_compute_card/angela_interface_freeze_packet.yaml"


def test_interface_packet_separates_conditions_from_pending_decisions() -> None:
    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))

    assert packet["status"] == "pending_angela_decisions"
    assert packet["owner"] == "angela"
    assert packet["known_initial_conditions"]["host_link"]["payload_gbs_each_direction"] == 63.015
    assert packet["known_initial_conditions"]["compute_contract"]["main_compute"]["partitions"] == 16
    assert packet["known_initial_conditions"]["hierarchy"]["die_l1"]["target_mb"] == 32
    assert packet["known_initial_conditions"]["terminology_guard"]["labels_are_not_interchangeable"] is True
    assert {item["id"] for item in packet["pending_angela_decisions"]} == {
        "die_l1_interface",
        "microarchitecture",
        "card_l2_selection",
        "host_l3_contract",
        "thermal_and_form_factor",
        "acceptance_priority",
    }
    assert packet["freeze_record"]["status"] == "pending_angela_input"
    assert packet["freeze_record"]["decision_ids_frozen"] == []
    assert packet["known_initial_conditions"]["scope"]["automatic_component_ordering"] is False


def test_interface_packet_known_values_match_reference_model() -> None:
    packet = yaml.safe_load(PACKET_PATH.read_text(encoding="utf-8"))
    result = AiCardReferenceModel().run()
    conditions = packet["known_initial_conditions"]

    assert conditions["compute_contract"]["main_compute"]["fabric_width_bits"] == result[
        "requirements"
    ]["main_width_bits"]
    assert conditions["compute_contract"]["secondary_compute"]["update_width_bits"] == result[
        "requirements"
    ]["weight_update_width_bits"]
    assert conditions["compute_contract"]["main_compute"]["raw_bandwidth_gbps"] == result[
        "bandwidth"
    ]["main_internal_raw_gbps"]
    assert conditions["compute_contract"]["main_compute"]["raw_bandwidth_gbs"] == result[
        "bandwidth"
    ]["main_internal_raw_gbs"]
    assert conditions["compute_contract"]["secondary_compute"]["raw_bandwidth_gbps"] == result[
        "bandwidth"
    ]["weight_update_internal_raw_gbps"]
    assert conditions["compute_contract"]["secondary_compute"]["raw_bandwidth_gbs"] == result[
        "bandwidth"
    ]["weight_update_internal_raw_gbs"]
    assert conditions["host_link"]["payload_gbs_each_direction"] == result["bandwidth"][
        "pcie_effective_gbs_each_direction"
    ]
    assert conditions["hierarchy"]["die_l1"]["target_mb"] == result["cache"]["target_mb"]
    assert conditions["budgets"]["prototype_bom_cap_usd"] == result["cost"][
        "prototype_bom_cap"
    ]
    assert result["design_verification"]["technical_checks_pass"] is True
    assert packet["freeze_record"]["environment_support_may_fill_missing_architecture"] is False
