# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Tests for the current-mode CIM strip reference model.

The point of these tests is not that the model returns numbers, but that the
numbers it derives from the measured device fixture are the ones the current
process actually supports, and that a regression in the fixture's linearity
fails loudly rather than being absorbed.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from ai.hardware.cim_strip_reference import (
    MEASUREMENT_PROVENANCE,
    SUPERSEDED_WEIGHT_RESPONSE,
    WEIGHT_RESPONSE_MEASUREMENT,
    CimStripConfig,
    CimStripError,
    CimStripReferenceModel,
    build_weight_response_deck,
    evaluate_weight_response,
    find_sky130_model_library,
    parse_weight_response_outputs,
    sky130_device_token,
)


def _fixture_measurement() -> dict:
    return {
        "device": MEASUREMENT_PROVENANCE["device"],
        "cell_w_um": MEASUREMENT_PROVENANCE["cell_w_um"],
        "cell_l_um": MEASUREMENT_PROVENANCE["cell_l_um"],
        "vgs_grid_v": MEASUREMENT_PROVENANCE["vgs_grid_v"],
        "id_a_by_vds": MEASUREMENT_PROVENANCE["id_a_by_vds"],
    }


# -----------------------------------------------------------------------------
# configuration validation
# -----------------------------------------------------------------------------
def test_config_rejects_non_power_of_two_weight_chain() -> None:
    with pytest.raises(CimStripError, match="power of two"):
        CimStripConfig(cells_per_weight_max=6)


def test_config_rejects_strip_budget_larger_than_die() -> None:
    with pytest.raises(CimStripError, match="cannot exceed"):
        CimStripConfig(die_strip_area_budget_mm2=2.0, die_area_budget_mm2=1.5)


def test_config_rejects_impossible_popcount() -> None:
    with pytest.raises(CimStripError, match="popcount"):
        CimStripConfig(cells_per_weight_max=8, mean_weight_popcount=9.0)


def test_config_derives_die_geometry_consistently() -> None:
    config = CimStripConfig()

    assert config.cells_per_die == 8 * 2048 * 8
    assert config.macs_per_pass_per_die == 8 * 2048
    assert config.weight_bytes_per_die == 8 * 2048


# -----------------------------------------------------------------------------
# weight linearity: the gate the freeze packet already satisfies
# -----------------------------------------------------------------------------
def test_current_fixture_measures_exact_parallel_cell_response() -> None:
    result = CimStripReferenceModel().weight_linearity_gate()

    assert result["passes"] is True
    current = result["fixtures"]["current"]
    assert current["fixture"] == "DOT4L"
    for measured, ideal in zip(current["measured_ratio"], current["ideal_ratio"]):
        assert math.isclose(measured, ideal, rel_tol=1e-3)
    assert current["passes_kcl_gate"] is True
    assert current["kcl_relative_error_frac"] <= 1e-6


def test_superseded_fixture_is_retained_and_still_fails_the_gate() -> None:
    """The first fixture used a different W per bin and never scaled 1:2:4:8.

    Keeping it in the model is what stops the fixed defect from being
    forgotten: the packet must not quietly re-report the old numbers.
    """
    result = CimStripReferenceModel().weight_linearity_gate()

    superseded = result["fixtures"]["superseded"]
    assert superseded["fixture"] == "DOT4"
    assert superseded["passes_current_gate"] is False
    assert superseded["max_relative_error_frac"] > 0.1
    assert "superseded" in SUPERSEDED_WEIGHT_RESPONSE["status"]


def test_linearity_gate_fails_when_the_fixture_regresses(monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken fixture must fail the gate, not be silently tolerated."""
    import ai.hardware.cim_strip_reference as module

    broken = dict(WEIGHT_RESPONSE_MEASUREMENT)
    broken["single_hot_currents_a"] = [1.0e-4, 2.5e-4, 6.0e-4, 1.4e-3]
    monkeypatch.setattr(module, "WEIGHT_RESPONSE_MEASUREMENT", broken)

    assert CimStripReferenceModel().weight_linearity_gate()["passes"] is False


# -----------------------------------------------------------------------------
# power and energy: the gap the current design had no model for
# -----------------------------------------------------------------------------
def test_unit_cell_current_matches_the_recorded_single_hot_measurement() -> None:
    model = CimStripReferenceModel()

    measured = model.unit_cell_current_a(1.8, 1.8)

    assert math.isclose(
        measured, WEIGHT_RESPONSE_MEASUREMENT["single_hot_currents_a"][0], rel_tol=1e-3
    )


def test_one_package_fits_but_the_drafted_card_does_not() -> None:
    """A single 16-die package fits 300W; the drafted card holds several.

    The decision-relevant gate is the card, and conflating the two is exactly
    the error that would let an unbuildable card pass review.
    """
    result = CimStripReferenceModel().power_envelope()

    assert result["packages_per_card"] == 4
    assert result["expected_package_fits_board_budget"] is True
    assert result["expected_card_fits_board_budget"] is False
    assert result["card_fills_board_budget_x"] > 1.0
    expected = result["scenarios"][0]
    assert expected["scenario"] == "expected"
    assert expected["package_power_w"] < 300.0
    assert expected["card_power_w"] > 300.0
    assert expected["card_power_w"] == pytest.approx(expected["package_power_w"] * 4, rel=1e-9)
    worst = next(row for row in result["scenarios"] if row["scenario"] == "worst_case")
    assert worst["card_power_w"] > expected["card_power_w"]


def test_energy_per_mac_is_worse_than_the_same_process_digital_baseline() -> None:
    comparison = CimStripReferenceModel().published_comparison()

    assert comparison["beats_best_published_reference"] is False
    worst_reference = max(float(item["energy_pj_per_mac"]) for item in comparison["references"])
    assert comparison["modelled_energy_pj_per_mac"] > worst_reference


def test_lowering_the_array_rail_dominates_the_power_budget() -> None:
    """Array power is Icell*Vds, so the drain rail is the main lever.

    This is the quantitative reason the drafted 1.8V rail is a choice rather
    than a physical limit, and it is what a lower-rail redesign has to bank on.
    The best point must still be usable by the sense chain.
    """
    search = CimStripReferenceModel().operating_point_search()

    assert search["best_vs_baseline_energy_reduction_x"] > 1.0
    best = search["best_feasible_point"]
    baseline = search["baseline_point"]
    assert best is not None
    assert best["feasible"] is True
    assert best["read_swing_ok"] is True
    assert best["column_current_ok"] is True
    assert best["package_energy_pj_per_mac"] < baseline["package_energy_pj_per_mac"]
    assert best["unit_cell_power_w"] < baseline["unit_cell_power_w"]


def test_energy_search_rejects_degenerate_low_rail_points() -> None:
    """A pure energy minimiser would always pick a near-zero rail.

    The search must refuse points whose read swing or column current cannot
    support the declared effective resolution, otherwise it recommends a die
    that cannot be read.
    """
    search = CimStripReferenceModel().operating_point_search()

    assert search["feasible_point_count"] > 0
    assert search["feasible_point_count"] < len(search["points"])
    lowest_rail = min(search["points"], key=lambda item: item["array_vds_v"])
    assert lowest_rail["feasible"] is False
    assert lowest_rail["infeasible_reasons"]
    infeasible = [item for item in search["points"] if not item["feasible"]]
    assert all(item["infeasible_reasons"] for item in infeasible)


def test_operating_point_search_reports_device_curvature() -> None:
    search = CimStripReferenceModel().operating_point_search()

    curvatures = [point["curvature_max_relative_deviation"] for point in search["points"]]
    assert all(value > 0.0 for value in curvatures)
    assert max(curvatures) > 0.2


# -----------------------------------------------------------------------------
# area: the self-inconsistency in the drafted die budget
# -----------------------------------------------------------------------------
def test_die_strip_budget_is_underfilled_by_the_drafted_cell_count() -> None:
    area = CimStripReferenceModel().area_and_capacity()

    assert area["die_strip_budget_is_self_inconsistent"] is True
    assert area["die_underfilled_by_x"] > 5.0
    # The packet's "1MB ~ 3.6mm2" derives from the 0.42um^2 cell footprint,
    # not from the bare 0.42x0.15um device area.
    assert area["unit_cell_device_area_um2"] == pytest.approx(0.063, abs=1e-6)
    assert area["unit_cell_footprint_um2"] == pytest.approx(0.42, abs=1e-6)
    assert area["footprint_over_device_ratio"] == pytest.approx(0.42 / 0.063, rel=1e-3)
    assert area["area_per_mb_of_weights_mm2"] == pytest.approx(3.52, abs=0.05)


def test_filling_the_die_budget_shrinks_the_working_set_package_count() -> None:
    area = CimStripReferenceModel().area_and_capacity()

    assert area["packages_for_working_set_with_budget_filled"] < (
        area["packages_for_working_set_as_drafted"] / 5.0
    )
    assert area["silicon_area_for_working_set_with_budget_filled_mm2"] < (
        area["silicon_area_for_working_set_as_drafted_mm2"] / 5.0
    )


# -----------------------------------------------------------------------------
# verdict
# -----------------------------------------------------------------------------
def test_run_reports_blockers_and_refuses_a_completion_claim() -> None:
    result = CimStripReferenceModel().run()

    assert result["completion_claim_allowed"] is False
    assert result["config"]["end_state_figures_used"] is False
    assert result["gate_summary"]["all_gates_passed"] is False
    blocker_ids = {item["id"] for item in result["blockers"]}
    assert "cim_array_power_exceeds_board_budget" in blocker_ids
    assert "cim_energy_density_worse_than_digital_baseline" in blocker_ids
    assert "cell_iv_curvature_exceeds_two_point_calibration" in blocker_ids
    assert "die_strip_area_budget_underfilled" in blocker_ids
    assert result["warnings"]


def test_run_is_json_serialisable() -> None:
    import json

    payload = CimStripReferenceModel().run()

    assert json.loads(json.dumps(payload))["schema_version"] == "cim-strip-reference/1"


def test_missing_measured_bias_is_rejected_rather_than_extrapolated() -> None:
    model = CimStripReferenceModel(measurement=_fixture_measurement())

    with pytest.raises(CimStripError, match="no measured device row"):
        model.unit_cell_current_a(1.5, 1.0)


# -----------------------------------------------------------------------------
# SPICE cross-check helpers
# -----------------------------------------------------------------------------
def test_evaluate_weight_response_detects_a_healthy_response() -> None:
    measured = {
        "bin0": 1.0e-4,
        "bin0_cells": 1.0,
        "bin1": 2.0e-4,
        "bin1_cells": 2.0,
        "bin2": 4.0e-4,
        "bin2_cells": 4.0,
        "bin3": 8.0e-4,
        "bin3_cells": 8.0,
        "all_hot": 1.5e-3,
    }

    result = evaluate_weight_response(measured)

    assert result["status"] == "pass"
    assert result["kcl_exact"] is True


def test_evaluate_weight_response_rejects_sublinear_weights() -> None:
    measured = {
        "bin0": 1.0e-4,
        "bin0_cells": 1.0,
        "bin1": 2.07e-4,
        "bin1_cells": 2.0,
        "bin2": 4.43e-4,
        "bin2_cells": 4.0,
        "bin3": 8.95e-4,
        "bin3_cells": 8.0,
        "all_hot": 1.765e-3,
    }

    result = evaluate_weight_response(measured)

    assert result["status"] == "fail"
    assert result["max_relative_error_frac"] > 0.1


def test_evaluate_weight_response_reports_insufficient_data() -> None:
    assert evaluate_weight_response({"idle": 0.0})["status"] == "insufficient_data"


def test_build_deck_uses_identical_parallel_cells(tmp_path: Path) -> None:
    library = tmp_path / "models.spice"
    library.write_text(".subckt sky130_fd_pr__nfet_01v8 d g s b\n.ends\n", encoding="utf-8")

    deck = build_weight_response_deck(library)
    instances = [
        line
        for line in deck.splitlines()
        if line.startswith("m") and "sky130_fd_pr__nfet_01v8" in line
    ]
    assert ".include" in deck
    assert "w=0.42u l=0.15u" in deck
    # 1+2+4+8 identical cells, all tied to one shared drain spine.
    assert len(instances) == 15
    assert all(line.split()[1] == "spine" for line in instances)
    assert "alter vg0 = 1.8" in deck
    assert deck.rstrip().endswith(".end")


def test_build_deck_detects_the_binned_model_form(tmp_path: Path) -> None:
    """A flattened corner file exposes .model, not a .subckt wrapper.

    Referencing the subcircuit name against such a library silently produces
    "could not find a valid modelname", so the token must be discovered.
    """
    library = tmp_path / "corner.spice"
    library.write_text(
        ".model sky130_fd_pr__nfet_01v8__model.0 nmos\n"
        "+ lmin = 2.0e-05 lmax = 0.0001 wmin = 7.0e-06 wmax = 0.0001\n",
        encoding="utf-8",
    )

    assert sky130_device_token(library) == "sky130_fd_pr__nfet_01v8__model"
    deck = build_weight_response_deck(library)
    assert "sky130_fd_pr__nfet_01v8__model w=0.42u" in deck


def test_build_deck_reasserts_every_gate_before_the_all_hot_word(tmp_path: Path) -> None:
    """The all-hot word must not inherit the cleared gates from the sweep.

    Measuring it without re-asserting records the idle current, which makes the
    additivity check pass vacuously instead of testing anything.
    """
    library = tmp_path / "models.spice"
    library.write_text(".subckt sky130_fd_pr__nfet_01v8 d g s b\n.ends\n", encoding="utf-8")

    deck = build_weight_response_deck(library)
    _, _, control = deck.partition(".control")
    lines = [line.strip() for line in control.splitlines() if line.strip()]

    wall_index = lines.index("print -i(vvdd) > wall.txt")
    before_wall = lines[:wall_index]
    # Find the last gate clear inside the single-hot sweep, then require every
    # gate to be re-asserted between that clear and the all-hot measurement.
    last_clear = max(
        index
        for index, line in enumerate(before_wall)
        if line.startswith("alter vg") and "= 0" in line
    )
    preceding = [line for line in before_wall[last_clear + 1 :] if line.startswith("alter vg")]
    assert len(preceding) == 4
    assert all(line.endswith("= 1.8") for line in preceding)
    assert lines[wall_index - 1] == "op"


def test_build_deck_rejects_a_missing_model_library(tmp_path: Path) -> None:
    with pytest.raises(CimStripError, match="not found"):
        build_weight_response_deck(tmp_path / "absent.spice")


def test_parse_outputs_reads_ngspice_print_files(tmp_path: Path) -> None:
    (tmp_path / "w0000.txt").write_text("i0 = 2.753076e-11\n", encoding="utf-8")
    (tmp_path / "w0001.txt").write_text("i8 = 1.572156e-03\n", encoding="utf-8")
    (tmp_path / "w1111.txt").write_text("iall = 2.947793e-03\n", encoding="utf-8")

    measured = parse_weight_response_outputs(tmp_path)

    assert measured["bin3"] == pytest.approx(1.572156e-3)
    assert measured["bin3_cells"] == 8.0
    assert measured["all_hot"] == pytest.approx(2.947793e-3)
    assert measured["idle"] == pytest.approx(2.753076e-11)


def test_model_library_lookup_never_raises() -> None:
    assert find_sky130_model_library() is None or Path(find_sky130_model_library()).is_file()


# -----------------------------------------------------------------------------
# energy accounting normalisation
# -----------------------------------------------------------------------------
def test_bit_slicing_is_charged_for_every_pass_it_needs() -> None:
    """A binary bit-slice pass resolves one weight *bit*, not a whole weight.

    Comparing the two schemes per pass would make bit-slicing look
    ``weight_bits`` times cheaper than it is. This is the guard for that
    normalisation error.
    """
    model = CimStripReferenceModel()
    config = model.config

    weighted = model.energy_accounting(0.3, 1.0, 50e-9, False, config.mean_weight_popcount)
    binary = model.energy_accounting(0.3, 1.0, 50e-9, True, 1.0)

    assert weighted["passes_per_weight"] == 1
    assert binary["passes_per_weight"] == config.weight_bits
    # Both report per completed weight product, so the extra passes are charged.
    assert binary["energy_pj_per_mac"] > weighted["energy_pj_per_mac"]
    ratio = binary["energy_pj_per_mac"] / weighted["energy_pj_per_mac"]
    assert 1.5 < ratio < 3.0


def test_energy_accounting_names_every_term() -> None:
    """Array power alone understates cost, so every term must be present."""
    point = CimStripReferenceModel().energy_accounting(0.3, 1.0, 50e-9, False, 4.0)

    split = point["energy_pj_per_weight_product"]
    assert set(split) == {"array", "input_drive", "sense_chain", "total"}
    assert split["total"] == pytest.approx(
        split["array"] + split["input_drive"] + split["sense_chain"], rel=1e-9
    )
    assert split["array"] > split["sense_chain"] > split["input_drive"]


def test_energy_per_mac_is_independent_of_array_size() -> None:
    """A bigger array buys throughput, never energy per MAC.

    This is why the design search does not treat die size as an energy lever,
    and why the earlier fix of under-filling the die budget is about weight
    capacity rather than about efficiency.
    """
    model = CimStripReferenceModel()
    small = model.energy_accounting(0.3, 1.0, 50e-9, False, 4.0)

    import dataclasses

    big = CimStripReferenceModel(
        dataclasses.replace(model.config, strips_per_die=16, dies_per_package=32)
    ).energy_accounting(0.3, 1.0, 50e-9, False, 4.0)

    assert big["energy_pj_per_mac"] == pytest.approx(small["energy_pj_per_mac"], rel=1e-9)
    assert big["package_gmacs_per_s"] > small["package_gmacs_per_s"]


def test_energy_is_linear_in_the_sense_window() -> None:
    """The drafted 1us sense window is the dominant energy term.

    The array and sense-chain terms scale exactly with the window, while input
    drive is a fixed cost per pass, so the total is monotonic but *sub*-linear:
    a longer window costs less than proportionally more. That asymmetry is
    itself a reason to prefer a short window.
    """
    model = CimStripReferenceModel()

    short = model.energy_accounting(0.3, 1.0, 10e-9, False, 4.0)
    long = model.energy_accounting(0.3, 1.0, 100e-9, False, 4.0)

    # The array term, which dominates, is exactly linear.
    assert long["energy_pj_per_weight_product"]["array"] == pytest.approx(
        10.0 * short["energy_pj_per_weight_product"]["array"], rel=1e-9
    )
    # The total grows, but by less than the 10x window increase.
    assert long["energy_pj_per_mac"] > short["energy_pj_per_mac"]
    assert long["energy_pj_per_mac"] < 10.0 * short["energy_pj_per_mac"]


# -----------------------------------------------------------------------------
# noise-limited resolution
# -----------------------------------------------------------------------------
def test_resolution_is_derived_from_measured_transconductance() -> None:
    """Resolution must fall out of the device data, not be asserted."""
    model = CimStripReferenceModel()

    low = model.noise_limited_resolution_bits(0.3, 1.0)
    high = model.noise_limited_resolution_bits(1.8, 1.0)

    assert low["transconductance_s"] > 0
    assert high["transconductance_s"] > 0
    # More bias gives more transconductance, so more noise-limited resolution.
    assert high["resolution_bits"] > low["resolution_bits"]
    assert low["resolution_bits"] >= model.config.effective_bits_v1


def test_resolution_aggregates_over_passes() -> None:
    """Averaging more independent passes must improve resolution."""
    model = CimStripReferenceModel()

    one = model.noise_limited_resolution_bits(0.3, 1.0, aggregate_passes=1)
    many = model.noise_limited_resolution_bits(0.3, 1.0, aggregate_passes=64)

    assert many["resolution_bits"] > one["resolution_bits"]


def test_resolution_reports_an_unusable_bias_instead_of_dividing_by_zero() -> None:
    """A dead bias must return a reason, not a number derived from noise."""
    dead = {
        "device": "test",
        "cell_w_um": 0.42,
        "cell_l_um": 0.15,
        "vgs_grid_v": [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8],
        "id_a_by_vds": {"0.30": [0.0] * 8},
    }
    model = CimStripReferenceModel(measurement=dead)

    result = model.noise_limited_resolution_bits(0.3, 1.0)

    assert result["resolution_bits"] == 0.0
    assert "reason" in result


# -----------------------------------------------------------------------------
# feasible design search and recommendation
# -----------------------------------------------------------------------------
def test_design_search_finds_candidates_that_pass_every_gate() -> None:
    search = CimStripReferenceModel().feasible_design_search()

    assert search["candidate_count"] > 0
    assert search["passing_count"] > 0
    best = search["best_passing_candidate"]
    assert best is not None
    assert best["passes_all_gates"] is True
    assert best["card_fits_board_budget"] is True
    assert best["beats_published_reference"] is True
    assert best["resolution_ok"] is True
    assert best["read_swing_ok"] is True
    assert best["column_current_ok"] is True
    assert search["drafted_point"]["passes_all_gates"] is False


def test_drafted_configuration_is_never_the_recommendation() -> None:
    """The whole point is that the drafted numbers are not the achievable ones."""
    result = CimStripReferenceModel().recommended_design()
    point = result["design_point"]
    drafted = result["drafted_point_for_comparison"]

    assert point is not None
    assert point["array_vds_v"] < drafted["array_vds_v"]
    assert point["sense_time_s"] < drafted["sense_time_s"]
    assert point["card_power_w"] < drafted["card_power_w"]
    assert result["improvement_vs_drafted"]["card_power_w"] > 10.0


def test_recommendation_sense_window_is_buildable_not_just_optimal() -> None:
    """The recommendation must not sit at the 5ns energy-optimal corner.

    That corner is unreachable, so recommending it would be the same class of
    error as the original 1us assertion: an unbuildable number presented as a
    design target.
    """
    result = CimStripReferenceModel().recommended_design()
    point = result["design_point"]

    assert point["sense_time_s"] >= 20e-9
    sensitivity = result["sense_time_sensitivity"]
    assert sensitivity["headroom_x"] > 1.0
    assert (
        sensitivity["max_sense_time_ns_before_energy_gate_fails"]
        > sensitivity["chosen_sense_time_ns"]
    )


def test_recommendation_is_robust_to_the_assumed_sense_chain_power() -> None:
    """The assumed sense-chain power must not be load-bearing.

    If the recommendation only passes because of a guessed comparator power, it
    is not yet a design; the array rail and the sense window are what decide it.
    """
    result = CimStripReferenceModel().recommended_design()
    tolerance = result["sense_chain_power_sensitivity"]

    assert tolerance is not None
    assert tolerance["sense_chain_power_multiple_that_fails"] >= 10


def test_recommendation_declares_which_inputs_are_measured() -> None:
    search = CimStripReferenceModel().feasible_design_search()
    provenance = search["assumption_provenance"]

    assert "Icell(Vds, Vgs) from the ngspice device sweep" in provenance["measured"]
    assert provenance["assumed_not_yet_measured"]
    assert "caveat" in provenance
