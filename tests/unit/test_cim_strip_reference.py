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

import asyncio
import json
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

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
    _MODEL_LIBRARY_ENV,
    _interpolate_id_a,
    _max_straight_line_deviation,
    build_dot_product_deck,
    evaluate_dot_product_case,
    find_sky130_model_library,
    load_cim_strip_measurement,
    parse_weight_response_outputs,
    run_functional_dot_product_test,
    simulate_weight_response,
    sky130_device_token,
    weight_to_cell_counts,
    DotProductVector,
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


# -----------------------------------------------------------------------------
# configuration validation — every guard must be able to fire
# -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("strips_per_die", 0, "strip and slot counts"),
        ("weight_slots_per_strip", 0, "strip and slot counts"),
        ("cells_per_weight_max", 1, "binary-weighted chain"),
        ("dies_per_package", 0, "dies_per_package and packages_per_card"),
        ("packages_per_card", 0, "dies_per_package and packages_per_card"),
        ("cell_footprint_um2", 0.0, "cell_footprint"),
        ("die_area_budget_mm2", 0.0, "die area budgets"),
        ("die_strip_area_budget_mm2", 0.0, "die area budgets"),
        ("array_vds_v", 0.0, "voltages"),
        ("input_vgs_max_v", 0.0, "voltages"),
        ("input_ones_fraction", 1.5, "probability"),
        ("mean_weight_popcount", 10.0, "popcount"),
        ("sense_time_s", 0.0, "sense time and power"),
        ("board_power_budget_w", 0.0, "sense time and power"),
        ("target_weight_working_set_mb", 0.0, "working set"),
        ("linearity_tolerance_frac", 0.0, "fraction in"),
        ("linearity_tolerance_frac", 1.0, "fraction in"),
        ("effective_bits_v1", 0, "effective_bits_v1"),
        ("min_read_swing_v", 0.0, "feasibility limits"),
        ("min_cell_current_a", 0.0, "feasibility limits"),
        ("weight_bits", 0, "[1, 16]"),
        ("weight_bits", 17, "[1, 16]"),
        ("input_gate_capacitance_f", 0.0, "input_gate_capacitance_f"),
        ("sense_chain_power_w", -1.0, "sense chain power"),
        ("sense_chain_duty", 0.0, "sense chain power"),
        ("sense_chain_duty", 1.5, "sense chain power"),
    ],
)
def test_config_rejects_invalid_fields(field: str, value: object, message: str) -> None:
    with pytest.raises(CimStripError, match=message):
        replace(CimStripConfig(), **{field: value})


def test_config_rejects_a_weight_chain_shorter_than_the_weight_word() -> None:
    with pytest.raises(CimStripError, match="at least one cell per weight bit"):
        replace(CimStripConfig(), cells_per_weight_max=4, weight_bits=8)


# -----------------------------------------------------------------------------
# device characteristic plumbing
# -----------------------------------------------------------------------------


def test_interpolation_clamps_to_the_measured_grid_ends() -> None:
    grid = [0.0, 1.0, 2.0]
    row = [1.0, 2.0, 4.0]
    assert _interpolate_id_a(grid, row, -1.0) == 1.0
    assert _interpolate_id_a(grid, row, 3.0) == 4.0
    assert _interpolate_id_a(grid, row, 0.5) == 1.5
    assert _interpolate_id_a(grid, row, 1.5) == 3.0


def test_interpolation_survives_a_degenerate_zero_span_segment() -> None:
    assert _interpolate_id_a([1.0, 1.0], [2.0, 3.0], 1.0) == 2.0


def test_interpolation_falls_through_for_a_value_that_matches_no_segment() -> None:
    # NaN compares False against everything, so no segment claims it and the
    # loop falls through to the final row.
    assert _interpolate_id_a([0.0, 1.0], [2.0, 3.0], float("nan")) == 3.0


def test_straight_line_deviation_is_zero_for_affine_and_degenerate_rows() -> None:
    grid = [0.0, 1.0, 2.0]
    assert _max_straight_line_deviation(grid, [1.0, 2.0, 3.0]) == 0.0
    assert _max_straight_line_deviation([0.0], [1.0]) == 0.0
    assert _max_straight_line_deviation(grid, [1.0, 2.0]) == 0.0
    assert _max_straight_line_deviation(grid, [3.0, 3.0, 3.0]) == 0.0


def test_straight_line_deviation_detects_curvature() -> None:
    grid = [0.0, 1.0, 2.0]
    # A quadratic row bows away from the two-point straight line.
    worst = _max_straight_line_deviation(grid, [1.0, 1.5, 4.0])
    assert worst > 0.2


def test_device_row_lookup_prefers_the_nearest_measured_vds() -> None:
    measurement = {
        "id_a_by_vds": {
            "0.30": [1.0e-06, 2.0e-06],
            "1.80": [8.0e-06, 9.0e-06],
        },
        "vgs_grid_v": [0.0, 1.8],
    }
    model = CimStripReferenceModel(measurement=measurement)
    assert model._id_row(1.95) == [8.0e-06, 9.0e-06]  # |1.95-1.80| == tolerance


def test_device_row_lookup_refuses_to_extrapolate_beyond_the_sweep(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    measurement = {
        "id_a_by_vds": {
            "0.30": [1.0e-06, 2.0e-06],
        },
        "vgs_grid_v": [0.0, 1.8],
    }
    model = CimStripReferenceModel(measurement=measurement)
    with pytest.raises(CimStripError, match="no measured device row"):
        model._id_row(0.90)


# -----------------------------------------------------------------------------
# measurement provenance loading degrades to the bundled fixture
# -----------------------------------------------------------------------------


def test_load_measurement_falls_back_to_the_bundled_fixture_on_bad_files(
    tmp_path: Path,
) -> None:
    broken_json = tmp_path / "broken.json"
    broken_json.write_text("{not json", encoding="utf-8")
    assert load_cim_strip_measurement(broken_json) == dict(MEASUREMENT_PROVENANCE)

    not_a_mapping = tmp_path / "list.json"
    not_a_mapping.write_text("[1, 2, 3]", encoding="utf-8")
    assert load_cim_strip_measurement(not_a_mapping) == dict(MEASUREMENT_PROVENANCE)

    missing_key = tmp_path / "empty.json"
    missing_key.write_text('{"device": "x"}', encoding="utf-8")
    assert load_cim_strip_measurement(missing_key) == dict(MEASUREMENT_PROVENANCE)

    assert load_cim_strip_measurement(tmp_path / "does-not-exist.json") == dict(
        MEASUREMENT_PROVENANCE
    )


def test_load_measurement_merges_a_valid_payload_over_the_fixture(tmp_path: Path) -> None:
    payload = tmp_path / "measured.json"
    payload.write_text(
        json.dumps({"device": "custom_fixture", "id_a_by_vds": {"0.60": [1e-6]}}),
        encoding="utf-8",
    )
    merged = load_cim_strip_measurement(payload)
    assert merged["device"] == "custom_fixture"
    assert merged["id_a_by_vds"]["0.60"] == [1e-6]
    # fields absent from the payload keep their bundled provenance
    assert merged["cell_w_um"] == MEASUREMENT_PROVENANCE["cell_w_um"]


# -----------------------------------------------------------------------------
# dot-product functional test plumbing
# -----------------------------------------------------------------------------


def test_weight_to_cell_counts_is_binary_not_popcount() -> None:
    assert weight_to_cell_counts(0) == [0, 0, 0, 0, 0, 0, 0, 0]
    assert weight_to_cell_counts(1) == [1, 0, 0, 0, 0, 0, 0, 0]
    assert weight_to_cell_counts(7) == [1, 2, 4, 0, 0, 0, 0, 0]
    assert weight_to_cell_counts(255) == [1, 2, 4, 8, 16, 32, 64, 128]
    assert sum(weight_to_cell_counts(7)) == 7
    assert sum(weight_to_cell_counts(255)) == 255
    with pytest.raises(CimStripError, match="outside"):
        weight_to_cell_counts(256)
    with pytest.raises(CimStripError, match="outside"):
        weight_to_cell_counts(-1)


def test_dot_product_vector_rejects_inconsistent_shapes() -> None:
    with pytest.raises(CimStripError, match="at least one slot"):
        DotProductVector(input_bits=(), strip_weights=((1,),), label="x")
    with pytest.raises(CimStripError, match="at least one strip"):
        DotProductVector(input_bits=(1, 0), strip_weights=(), label="x")
    with pytest.raises(CimStripError, match="one weight per input slot"):
        DotProductVector(input_bits=(1, 0), strip_weights=((1, 2), (3,)), label="x")
    with pytest.raises(CimStripError, match="outside"):
        DotProductVector(input_bits=(1, 0), strip_weights=((1, 300),), label="x")
    vector = DotProductVector(input_bits=(1, 0), strip_weights=((7, 0),), label="ok")
    assert vector.strip_count == 1


def test_evaluate_dot_product_case_rejects_a_dead_calibration() -> None:
    vector = DotProductVector(input_bits=(1, 0), strip_weights=((7, 0),), label="v")
    outcome = evaluate_dot_product_case(vector, 0.0, [7.0e-06])
    assert outcome["status"] == "error"
    assert "calibration current is not positive" in outcome["detail"]


def test_evaluate_dot_product_case_passes_an_exact_array() -> None:
    # input (1,1): each strip decodes the sum of its own weights.
    vector = DotProductVector(input_bits=(1, 1), strip_weights=((7, 0), (0, 5)), label="v")
    outcome = evaluate_dot_product_case(vector, 1.0e-06, [7.0e-06, 5.0e-06])
    assert outcome["status"] == "pass"
    assert outcome["strips"][0]["decoded_value"] == pytest.approx(7.0)
    assert outcome["strips"][1]["decoded_value"] == pytest.approx(5.0)
    assert outcome["strips"][0]["passes"] is True


def test_evaluate_dot_product_case_flags_a_drifted_spine() -> None:
    vector = DotProductVector(input_bits=(1, 0), strip_weights=((7, 0),), label="v")
    outcome = evaluate_dot_product_case(vector, 1.0e-06, [8.0e-06])
    assert outcome["status"] == "fail"
    assert outcome["strips"][0]["passes"] is False
    # zero expected value: the error is absolute, not relative
    zero = evaluate_dot_product_case(
        DotProductVector(input_bits=(0,), strip_weights=((0,),), label="z"),
        1.0e-06,
        [3.0e-06],
    )
    assert zero["status"] == "fail"
    assert zero["strips"][0]["relative_error_frac"] == 3.0
    assert zero["strips"][0]["passes"] is False


def test_dot_product_deck_is_built_only_from_a_real_library(tmp_path: Path) -> None:
    missing = tmp_path / "missing.spice"
    vector = DotProductVector(input_bits=(1, 0), strip_weights=((7, 0),), label="v")
    with pytest.raises(CimStripError, match="not found"):
        build_dot_product_deck(missing, [vector])

    library = tmp_path / "models.spice"
    library.write_text("* model library\n", encoding="utf-8")
    with pytest.raises(CimStripError, match="at least one test vector"):
        build_dot_product_deck(library, [])

    deck, outputs = build_dot_product_deck(library, [vector])
    assert outputs and any(name.endswith(".txt") for name in outputs)
    assert "sky130_fd_pr__nfet_01v8" in deck  # default device token


def test_run_functional_dot_product_test_degrades_without_ngspice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    vector = DotProductVector(input_bits=(1, 0), strip_weights=((7, 0),), label="v")
    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: None)
    outcome = asyncio.run(
        run_functional_dot_product_test(tmp_path, [vector], model_library=tmp_path)
    )
    assert outcome == {"status": "skipped", "reason": "ngspice_not_installed"}


def test_run_functional_dot_product_test_skips_without_a_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    vector = DotProductVector(input_bits=(1, 0), strip_weights=((7, 0),), label="v")
    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.delenv(_MODEL_LIBRARY_ENV, raising=False)
    monkeypatch.setattr(
        strip_ref, "find_sky130_model_library", lambda: None
    )
    outcome = asyncio.run(
        run_functional_dot_product_test(tmp_path, [vector], model_library=None)
    )
    assert outcome["status"] == "skipped"
    assert outcome["reason"] == "sky130_model_library_not_found"
    assert "ANGELA_SKY130_SPICE_LIBRARY" in outcome["hint"]


# -----------------------------------------------------------------------------
# weight-response execution paths (async) and ngspice output parsing
# -----------------------------------------------------------------------------


def test_simulate_weight_response_skips_without_ngspice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: None)
    outcome = asyncio.run(simulate_weight_response(tmp_path))
    assert outcome == {"status": "skipped", "reason": "ngspice_not_installed"}


def test_simulate_weight_response_skips_and_hints_without_a_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.delenv(_MODEL_LIBRARY_ENV, raising=False)
    monkeypatch.setattr(strip_ref, "find_sky130_model_library", lambda: None)
    outcome = asyncio.run(simulate_weight_response(tmp_path))
    assert outcome["status"] == "skipped"
    assert outcome["reason"] == "sky130_model_library_not_found"
    assert "hint" in outcome


def _stub_model_library(tmp_path: Path) -> Path:
    """A real library file: build_weight_response_deck() checks is_file()."""
    library = tmp_path / "sky130.lib.spice"
    library.write_text(".model sky130_fd_pr__nfet_01v8__model nmos\n", encoding="utf-8")
    return library


def test_simulate_weight_response_reports_an_ngspice_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    class FakeProcess:
        returncode = 0

        def __init__(self) -> None:
            self.killed = False

        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio.sleep(10)
            return b"", b""

        def kill(self) -> None:
            self.killed = True

        async def wait(self) -> None:
            return None

    process = FakeProcess()

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return process

    async def fake_wait_for(awaitable: object, timeout: float) -> None:
        raise asyncio.TimeoutError

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(
        strip_ref, "find_sky130_model_library", lambda: _stub_model_library(tmp_path)
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(strip_ref.asyncio, "wait_for", fake_wait_for)

    outcome = asyncio.run(simulate_weight_response(tmp_path, timeout_s=0.05))

    assert outcome["status"] == "error"
    assert "timed out after 0.05s" in outcome["reason"]
    assert process.killed is True


def test_simulate_weight_response_reports_unparseable_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    class FakeProcess:
        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b"ngspice exploded"

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return FakeProcess()

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(
        strip_ref, "find_sky130_model_library", lambda: _stub_model_library(tmp_path)
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)

    outcome = asyncio.run(simulate_weight_response(tmp_path))

    assert outcome["status"] == "error"
    assert outcome["reason"] == "ngspice produced no parseable current output"
    assert "ngspice exploded" in outcome["stderr"]


def test_simulate_weight_response_passes_a_healthy_sweep(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    class FakeProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

    async def fake_exec(*_args: object, **_kwargs: object) -> FakeProcess:
        return FakeProcess()

    # What ngspice would write next to the deck for an exact 1:2:4:8 response.
    def write_outputs() -> None:
        for stem, current in (
            ("w0000", "0.0"),
            ("w1000", "1.0e-06"),
            ("w0100", "2.0e-06"),
            ("w0010", "4.0e-06"),
            ("w0001", "8.0e-06"),
            ("wall", "1.5e-05"),
        ):
            (tmp_path / f"{stem}.txt").write_text(f"v(i) = {current}\n", encoding="utf-8")

    class ExecAfterWriting(FakeProcess):
        async def communicate(self) -> tuple[bytes, bytes]:
            await asyncio.sleep(0)
            write_outputs()
            return b"", b""

    async def fake_exec(*_args: object, **_kwargs: object) -> ExecAfterWriting:
        return ExecAfterWriting()

    monkeypatch.setattr(strip_ref.shutil, "which", lambda name: "/usr/bin/ngspice")
    monkeypatch.setattr(
        strip_ref, "find_sky130_model_library", lambda: _stub_model_library(tmp_path)
    )
    monkeypatch.setattr(strip_ref.asyncio, "create_subprocess_exec", fake_exec)

    outcome = asyncio.run(simulate_weight_response(tmp_path))

    assert outcome["status"] == "pass"
    assert outcome["return_code"] == 0
    assert outcome["measured"]["bin3"] == 8.0e-06
    verdict = outcome["verdict"]
    assert verdict["status"] == "pass"
    assert verdict["max_relative_error_frac"] == 0.0
    assert verdict["kcl_exact"] is True


def test_parse_outputs_reads_labels_and_cell_counts(tmp_path: Path) -> None:
    (tmp_path / "w0000.txt").write_text("v(i) = 0.0\n", encoding="utf-8")
    (tmp_path / "w1000.txt").write_text("v(i) = 1.0e-06\n", encoding="utf-8")
    (tmp_path / "wall.txt").write_text("v(i) = 1.5e-05\n", encoding="utf-8")
    (tmp_path / "w1111.txt").write_text("v(i) = 1.5e-05\n", encoding="utf-8")
    (tmp_path / "unparseable.txt").write_text("nothing here\n", encoding="utf-8")
    (tmp_path / "unrelated.txt").write_text("v(i) = 9.9\n", encoding="utf-8")

    measured = parse_weight_response_outputs(tmp_path)

    assert measured["idle"] == 0.0
    assert measured["bin0"] == 1.0e-06
    assert measured["bin0_cells"] == 1.0
    assert measured["all_hot"] == 1.5e-05
    # "unparseable" does not match the w*.txt glob; "unrelated" does but has no key
    assert "unrelated" not in measured


def test_model_library_lookup_prefers_a_valid_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = tmp_path / "sky130.lib.spice"
    library.write_text(".model sky130_fd_pr__nfet_01v8__model nmos ...\n", encoding="utf-8")
    monkeypatch.setenv(_MODEL_LIBRARY_ENV, str(library))
    assert find_sky130_model_library() == library


def test_model_library_lookup_ignores_a_nonexistent_env_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import ai.hardware.cim_strip_reference as strip_ref

    monkeypatch.setenv(_MODEL_LIBRARY_ENV, str(tmp_path / "missing.spice"))
    monkeypatch.setattr(strip_ref, "_VOLARE_GLOBS", ())
    assert find_sky130_model_library() is None


def test_device_token_detection_covers_both_packagings(tmp_path: Path) -> None:
    subckt = tmp_path / "subckt.spice"
    subckt.write_text(".subckt sky130_fd_pr__nfet_01v8 d g s b\n.ends\n", encoding="utf-8")
    assert sky130_device_token(subckt) == "sky130_fd_pr__nfet_01v8"

    binned = tmp_path / "binned.spice"
    binned.write_text(
        ".model sky130_fd_pr__nfet_01v8__model.0 nmos\n", encoding="utf-8"
    )
    assert sky130_device_token(binned) == "sky130_fd_pr__nfet_01v8__model"

    unreadable = tmp_path / "missing.spice"
    assert sky130_device_token(unreadable) is None

    plain = tmp_path / "plain.spice"
    plain.write_text("* nothing known\n", encoding="utf-8")
    assert sky130_device_token(plain) is None
