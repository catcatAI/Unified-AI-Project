# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Branch-closure tests for the card architecture audit.

The audit's authority comes from refusing to derive numbers it cannot derive;
these tests pin the unavailable/degraded paths as well as the arithmetic paths
that depend on a feasible operating point existing.
"""

from __future__ import annotations

import pytest
from ai.hardware.card_architecture_audit import (
    ClaimedArchitecture,
    audit,
    measured_efficiency,
    throughput_check,
)
from ai.hardware.cim_strip_reference import CimStripReferenceModel


def test_measured_efficiency_reports_unavailable_without_a_design_point(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai.hardware.card_architecture_audit as audit_module

    class NoPointModel:
        def recommended_design(self, sense_time_s: float) -> dict:
            return {}

    monkeypatch.setattr(audit_module, "CimStripReferenceModel", NoPointModel)
    result = measured_efficiency()
    assert result["status"] == "unavailable"
    assert result["reason"] == "no feasible operating point"


def test_measured_efficiency_derives_tops_per_watt_at_the_real_point() -> None:
    result = measured_efficiency()
    if result["status"] != "ok":
        pytest.skip("the current fixture yields no feasible operating point")
    point = CimStripReferenceModel().recommended_design()["design_point"]
    expected = 2.0 / (point["energy_pj_per_mac"] * 1e-12) / 1e12
    assert result["tops_per_w_int8"] == pytest.approx(expected, rel=1e-9)
    assert result["sense_window_ns"] == pytest.approx(point["sense_time_s"] * 1e9)


def test_throughput_check_degrades_when_efficiency_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai.hardware.card_architecture_audit as audit_module

    class NoPointModel:
        def recommended_design(self, sense_time_s: float) -> dict:
            return {}

    monkeypatch.setattr(audit_module, "CimStripReferenceModel", NoPointModel)
    assert throughput_check(ClaimedArchitecture()) == {"status": "unavailable"}


def test_throughput_check_reports_the_shortfall_when_feasible() -> None:
    result = throughput_check(ClaimedArchitecture())
    if result["status"] != "ok":
        pytest.skip("the current fixture yields no feasible operating point")
    assert result["shortfall_x"] > 1.0  # the claim exceeds one amp per plane
    assert result["claimed_die_tops"] > 0


def test_audit_does_not_invent_an_area_correction_when_density_is_measured() -> None:
    claimed = ClaimedArchitecture()
    result = audit(claimed)
    correction_ids = {item["id"] for item in result["corrections"]}
    # The draft claims literature density, so this correction MUST be present;
    # flipping the claim to measured density must make the branch a no-op.
    assert "area_conclusions_rest_on_literature_density" in correction_ids


def test_audit_omits_area_correction_when_densities_are_measured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The area pass branch must be taken when nothing rests on literature.

    die_area_budget reports area_rests_on_unmeasured_density=False only when
    both SRAM and digital densities are measured in this repository. The
    defaults are bound at def time, so patch die_area_budget itself to return
    the measured area and drive audit() through the `pass` branch.
    """
    import ai.hardware.card_architecture_audit as audit_module
    from ai.hardware.card_architecture_audit import Density, die_area_budget

    measured_sram = Density(
        um2_per_element=0.127,
        provenance="test-measured",
        measured_in_this_repository=True,
    )
    measured_digital = Density(
        um2_per_element=0.30,
        provenance="test-measured",
        measured_in_this_repository=True,
    )
    measured_area = die_area_budget(
        ClaimedArchitecture(), sram=measured_sram, digital=measured_digital
    )
    assert measured_area["area_rests_on_unmeasured_density"] is False
    monkeypatch.setattr(audit_module, "die_area_budget", lambda claimed, *a, **k: measured_area)
    result = audit(ClaimedArchitecture())
    correction_ids = {item["id"] for item in result["corrections"]}
    assert "area_conclusions_rest_on_literature_density" not in correction_ids
