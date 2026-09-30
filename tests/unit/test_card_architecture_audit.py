# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Tests for the architecture audit.

The audit's job is to re-derive someone else's numbers without quietly
redefining them, so the tests check the arithmetic, the provenance labelling,
and that a correction is always reported against what was actually claimed.
"""

from __future__ import annotations

import math

import pytest
from ai.hardware.card_architecture_audit import (
    ANALOG_CIM_DENSITY,
    DIGITAL_STD_CELL_DENSITY,
    SRAM_6T_BITCELL_DENSITY,
    ClaimedArchitecture,
    Density,
    Interconnect,
    audit,
    die_area_budget,
    l1_residency_requirement,
    leakage_requirement,
    measured_efficiency,
    sense_amplifier_budget,
    throughput_check,
    weight_streaming,
)


# -----------------------------------------------------------------------------
# the claim must be recorded verbatim
# -----------------------------------------------------------------------------
def test_claimed_architecture_derives_consistent_totals() -> None:
    claimed = ClaimedArchitecture()

    assert claimed.dies_per_card == 128
    assert claimed.transistors_per_die == pytest.approx(200.0e6)
    assert claimed.l1_mb_per_die == pytest.approx(1.40625)
    assert claimed.card_tops == pytest.approx(claimed.die_tops * claimed.dies_per_card, rel=0.01)
    assert claimed.model_bytes == 2.0e9
    assert claimed.kv_bytes > 0


def test_claimed_numbers_are_kept_not_overwritten() -> None:
    """A correction has to be a diff, so the claim must survive the audit."""
    report = audit()
    claimed = report["claimed"]

    assert claimed["card_tops"] == 154.0e12
    assert claimed["card_l1_mb"] == 180.0
    assert claimed["claimed_tokens_per_s"] == 4800.0
    assert claimed["power_optimistic_w"] == 25.5
    assert claimed["power_pessimistic_w"] == 381.0


# -----------------------------------------------------------------------------
# provenance
# -----------------------------------------------------------------------------
def test_only_the_analog_density_is_measured_here() -> None:
    assert ANALOG_CIM_DENSITY.measured_in_this_repository is True
    assert "measured" in ANALOG_CIM_DENSITY.provenance
    assert SRAM_6T_BITCELL_DENSITY.measured_in_this_repository is False
    assert "literature" in SRAM_6T_BITCELL_DENSITY.provenance
    assert DIGITAL_STD_CELL_DENSITY.measured_in_this_repository is False


def test_area_report_says_when_it_rests_on_unmeasured_density() -> None:
    area = die_area_budget(ClaimedArchitecture())

    assert area["array"]["density"]["measured_in_this_repository"] is True
    assert area["l1"]["density"]["measured_in_this_repository"] is False
    assert area["area_rests_on_unmeasured_density"] is True


def test_density_record_round_trips() -> None:
    payload = ANALOG_CIM_DENSITY.as_dict()

    assert payload["um2_per_element"] == ANALOG_CIM_DENSITY.um2_per_element
    assert payload["measured_in_this_repository"] is True
    assert "note" in payload


# -----------------------------------------------------------------------------
# the bandwidth finding
# -----------------------------------------------------------------------------
def test_token_rate_is_bandwidth_bound() -> None:
    """The headline rate costs more bandwidth than the card can ever supply."""
    result = weight_streaming(ClaimedArchitecture(), Interconnect())

    assert result["required_weight_bandwidth_gbs"] > 9000.0
    assert result["best_available_gbs"] < 200.0
    assert result["shortfall_x"] > 50.0
    assert result["achievable_tokens_per_s"] < 100.0
    assert result["l1_resident_fraction"] < 0.2
    assert "not resident" in result["verdict"]


def test_bandwidth_shortfall_is_reported_as_blocking() -> None:
    report = audit()
    ids = {item["id"]: item for item in report["corrections"]}

    assert "token_rate_is_bandwidth_bound" in ids
    entry = ids["token_rate_is_bandwidth_bound"]
    assert entry["severity"] == "blocking"
    assert "4800" in entry["claimed"]
    assert "TB/s" in entry["detail"]


def test_interconnect_figures_are_the_measured_ones() -> None:
    links = Interconnect()

    # 63.015 GB/s is the Gen5 x16 payload figure this repository already measures
    assert links.pcie_gbs_per_direction == pytest.approx(63.015)
    assert links.card_pcie_gbs == pytest.approx(126.03)
    assert links.card_ddr_gbs == pytest.approx(102.4)


# -----------------------------------------------------------------------------
# the L1 finding
# -----------------------------------------------------------------------------
def test_l1_is_undersized_for_residency() -> None:
    claimed = ClaimedArchitecture()
    result = l1_residency_requirement(claimed)

    assert result["shortfall_factor"] > 10.0
    assert result["per_die_capacity_mb"] > claimed.l1_mb_per_die * 10
    assert result["density_measured"] is False


def test_residency_area_is_recoverable_not_absurd() -> None:
    """Resisting the tidy conclusion: the area is affordable.

    The tempting reading is that a 2 GB model cannot live on a 130 nm card. It
    can, because SRAM is cheap area and the controller already dominates the
    die. What is unaffordable is the L1 that was budgeted.
    """
    result = l1_residency_requirement(ClaimedArchitecture())
    area = die_area_budget(ClaimedArchitecture())

    assert result["per_die_area_mm2"] < area["controller_and_io"]["area_mm2"]
    assert result["density_measured"] is False


def test_l1_correction_carries_a_fix() -> None:
    report = audit()
    entry = {item["id"]: item for item in report["corrections"]}["l1_undersized_for_residency"]

    assert entry["severity"] == "blocking"
    assert "180" in entry["claimed"]
    assert "memory-sizing" in entry["fix"]


# -----------------------------------------------------------------------------
# area
# -----------------------------------------------------------------------------
def test_die_area_uses_a_different_density_per_block() -> None:
    area = die_area_budget(ClaimedArchitecture())
    blocks = (area["array"], area["l1"], area["controller_and_io"])

    densities = {block["density"]["um2_per_element"] for block in blocks}
    assert len(densities) == 3, "one density for all three blocks is the shortcut"
    assert sum(block["area_fraction"] for block in blocks) == pytest.approx(1.0)
    assert area["total_area_mm2_per_die"] == pytest.approx(
        sum(block["area_mm2"] for block in blocks)
    )


def test_array_is_a_small_share_of_the_die() -> None:
    """Consistent with the summary's own 0.35% array transistor share."""
    area = die_area_budget(ClaimedArchitecture())

    assert area["array"]["area_fraction"] < 0.2
    assert area["controller_and_io"]["area_fraction"] > area["array"]["area_fraction"]


def test_die_exceeds_a_shuttle_die_and_says_so() -> None:
    area = die_area_budget(ClaimedArchitecture())

    assert area["mpw_shuttle_die_mm2"] == 5.0
    assert area["multiple_of_mpw_shuttle_die"] > 1.0


# -----------------------------------------------------------------------------
# the sense-amplifier finding
# -----------------------------------------------------------------------------
def test_bit_serial_pe_needs_one_sense_event_per_weight_bit() -> None:
    """An 8x2T PE is 8 bit-planes, so an int8 MAC costs 8 sense events."""
    budget = sense_amplifier_budget(ClaimedArchitecture())

    assert budget["bit_planes_per_pe"] == 8
    assert budget["window_per_int8_mac_ns"] == pytest.approx(400.0)
    assert budget["one_amp_per_plane_die_tops"] == pytest.approx(0.082, rel=0.01)


def test_per_die_claim_needs_amplifiers_nobody_budgeted() -> None:
    result = throughput_check(ClaimedArchitecture())

    assert result["shortfall_x"] > 10.0
    assert result["required_sense_amps_per_plane"] > 10.0
    assert result["required_sense_amps_per_die"] > 80.0
    assert "amplifiers" in result["note"]


def test_die_and_card_tops_claims_agree_with_each_other() -> None:
    result = throughput_check(ClaimedArchitecture())

    assert result["card_tops_consistent_with_die_claim"] is True


def test_toe_ps_are_reported_in_tops_not_ops_per_second() -> None:
    """A units slip here turns 1.2 TOPS into 1.2e12 and every ratio with it."""
    budget = sense_amplifier_budget(ClaimedArchitecture())

    assert 0.1 < budget["claimed_die_tops"] < 10.0
    assert 0.001 < budget["one_amp_per_plane_die_tops"] < 1.0
    assert budget["required_parallel_sense_amps_per_plane"] < 1e4


# -----------------------------------------------------------------------------
# leakage
# -----------------------------------------------------------------------------
def test_leakage_requirement_is_solved_not_guessed() -> None:
    result = leakage_requirement(ClaimedArchitecture())
    by_label = {case["label"]: case for case in result["cases"]}

    assert by_label["optimistic"]["required_leakage_nA_per_transistor"] < 1.0
    assert by_label["pessimistic"]["required_leakage_nA_per_transistor"] > 5.0
    assert result["spread_x"] == pytest.approx(
        by_label["pessimistic"]["required_leakage_nA_per_transistor"]
        / by_label["optimistic"]["required_leakage_nA_per_transistor"]
    )
    assert "85 C" in result["pdk_number_to_obtain"]


def test_leakage_back_solve_reproduces_the_power_claim() -> None:
    result = leakage_requirement(ClaimedArchitecture())

    for case in result["cases"]:
        implied = (
            case["required_leakage_nA_per_transistor"]
            * 1e-9
            * result["core_vdd_v"]
            * ClaimedArchitecture().card_transistors
        )
        assert implied == pytest.approx(case["watts"], rel=1e-6)


# -----------------------------------------------------------------------------
# measured efficiency
# -----------------------------------------------------------------------------
def test_measured_efficiency_comes_from_the_validated_point() -> None:
    efficiency = measured_efficiency()

    assert efficiency["status"] == "ok"
    assert efficiency["array_vds_v"] == pytest.approx(0.3)
    assert 0.1 < efficiency["energy_pj_per_mac"] < 5.0
    assert 0.5 < efficiency["tops_per_w_int8"] < 20.0


# -----------------------------------------------------------------------------
# the report as a whole
# -----------------------------------------------------------------------------
def test_audit_does_not_claim_completion() -> None:
    report = audit()

    assert report["completion_claim_allowed"] is False
    assert report["schema_version"] == "card-architecture-audit/1"


def test_audit_lists_the_gaps_that_survive() -> None:
    report = audit()
    gaps = " ".join(report["gaps_that_remain_open"]).lower()

    assert "leak" in gaps
    assert "sram" in gaps
    assert "kv cache" in gaps
    assert "yield" in gaps


def test_audit_severities_are_ordered_with_the_blocking_findings_first() -> None:
    report = audit()
    severities = [item["severity"] for item in report["corrections"]]

    assert "blocking" in severities
    assert severities.index("blocking") == 0


def test_audit_is_json_serialisable() -> None:
    import json

    report = audit()

    assert json.loads(json.dumps(report))["schema_version"] == "card-architecture-audit/1"
