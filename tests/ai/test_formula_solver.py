"""
Tests for the physics formula solver (three-axis domain engines).

Covers the MD-identified gap (THREE_AXIS_SCALEUP.md §4.1/§6-D/§8.1): single-
unknown physics word problems — F=ma, kinetic energy, v=at, momentum, work,
power, and weight (F=mg). Pure functions, no network.

Also verifies the parse-level edge cases: unit anchors are case-insensitive,
bare "m" does not shadow "m/s²", keywords shadowed by longer keywords (速度 vs
加速度) are skipped, and the asked quantity is read from the question clause
only (given data must not shadow it).
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

import os
import sys

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "apps", "backend", "src")),
)

from ai.memory.formula_solver import (  # noqa: E402
    extract_known_quantities,
    find_target,
    solve,
)

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================


class TestFormulas:
    def test_force_newton_second_law(self):
        result = solve("an object of mass 5 kg accelerates at 2 m/s², what is the force")
        assert result is not None
        assert result["value"] == 10.0
        assert result["quantity"] == "force"

    def test_kinetic_energy(self):
        result = solve("what is the kinetic energy of a 3 kg object moving at 4 m/s")
        assert result is not None
        assert result["value"] == 24.0
        assert result["quantity"] == "energy"

    def test_velocity_accel_times_time(self):
        result = solve("a car accelerates at 3 m/s² for 4 seconds, what is its velocity")
        assert result is not None
        assert result["value"] == 12.0
        assert result["quantity"] == "velocity"

    def test_momentum(self):
        result = solve("a 2 kg ball moves at 10 m/s, what is its momentum")
        assert result is not None
        assert result["value"] == 20.0
        assert result["quantity"] == "momentum"

    def test_work_force_times_distance(self):
        result = solve("a force of 10 N moves an object 5 meters, what is the work done")
        assert result is not None
        assert result["value"] == 50.0
        assert result["quantity"] == "work"

    def test_power_work_over_time(self):
        result = solve("what is the power if 100 J of work is done in 20 seconds")
        assert result is not None
        assert result["value"] == 5.0
        assert result["quantity"] == "power"

    def test_weight_mass_from_weight(self):
        result = solve("an object falls with weight 49 N, what is its mass")
        assert result is not None
        assert result["value"] == 5.0
        assert result["quantity"] == "mass"

    def test_gravity_from_weight_and_mass(self):
        result = solve("a 100 kg crate weighs 980 N, what is g")
        assert result is not None
        assert result["value"] == 9.8

    def test_acceleration_from_force_and_mass(self):
        result = solve("what is the acceleration of a 200 N force on a 25 kg object")
        assert result is not None
        assert result["value"] == 8.0
        assert result["quantity"] == "acceleration"

    def test_chinese_force_problem(self):
        result = solve("質量 5 kg 加速度 2 m/s², 求力")
        assert result is not None
        assert result["value"] == 10.0
        assert result["quantity"] == "force"


class TestUnderSpecified:
    def test_no_digits_returns_none(self):
        assert solve("what is the force of this object") is None

    def test_plain_chat_returns_none(self):
        assert solve("hello how are you today") is None

    def test_insufficient_quantities_returns_none(self):
        assert solve("a force of 10 N on an object, what is the work") is None

    def test_division_by_zero_returns_none(self):
        # mass = force / acceleration with a = 0 m/s² -> division by zero.
        assert solve("a 10 N force on an object accelerating at 0 m/s², what is the mass") is None


class TestParsing:
    def test_units_are_case_insensitive(self):
        known = extract_known_quantities("a force of 10 N on a 5 kg mass")
        assert known["force"] == 10.0
        assert known["mass"] == 5.0

    def test_bare_m_does_not_shadow_ms2(self):
        known = extract_known_quantities("an object of mass 5 kg accelerates at 2 m/s²")
        assert "distance" not in known  # bare "m" in "m/s²" must not be distance
        assert known["acceleration"] == 2.0

    def test_velocity_keyword_shadowed_by_acceleration(self):
        # "加速度" contains "速度" as a substring; only acceleration may match.
        known = extract_known_quantities("質量 5 kg 加速度 2 m/s², 求力")
        assert known.get("acceleration") == 2.0
        assert "velocity" not in known

    def test_target_read_from_question_clause_only(self):
        # "a force of 10 N" is given data; the ask is work.
        target = find_target("a force of 10 N moves an object 5 meters, what is the work done")
        assert target == "work"

    def test_joule_maps_to_both_energy_and_work(self):
        known = extract_known_quantities("100 J of work is done")
        assert known["work"] == 100.0
        assert known["energy"] == 100.0

    def test_multiword_keyword_separator(self):
        known = extract_known_quantities("a force of 10 N")
        assert known["force"] == 10.0
