"""Tests for core/non_paradox_existence.py"""
import pytest


class TestNonParadoxExistence:
    """Tests for NonParadoxExistence"""

    def test_import(self):
        """Verify module exposes expected classes and enums"""
        from core.non_paradox_existence import (
            NonParadoxExistence, GrayZoneVariable, GrayZoneVariableType,
            PossibilityState, CoexistenceField,
        )
        assert NonParadoxExistence is not None
        assert hasattr(NonParadoxExistence, 'create_gray_zone')
        assert hasattr(NonParadoxExistence, 'add_possibility')
        assert hasattr(NonParadoxExistence, 'activate_coexistence')
        assert hasattr(NonParadoxExistence, 'update_cognitive_gap')
        assert hasattr(NonParadoxExistence, 'get_non_paradox_summary')
        assert len(GrayZoneVariableType) == 6

    def test_instantiation(self):
        """Verify basic instantiation and default state"""
        from core.non_paradox_existence import NonParadoxExistence
        instance = NonParadoxExistence()
        assert instance.gray_zones == {}
        assert instance.coexistence_fields == {}
        assert instance.global_cognitive_gap == 0.0
        assert instance.coexistence_active is False
        assert instance.min_gap_for_coexistence == 0.6
        assert instance.max_resonance_weights == 10

    def test_instantiation_with_config(self):
        """Verify instantiation with config applies values correctly"""
        from core.non_paradox_existence import NonParadoxExistence
        instance = NonParadoxExistence(config={
            "min_gap_for_coexistence": 0.8,
            "max_resonance_weights": 20,
        })
        assert instance.min_gap_for_coexistence == 0.8
        assert instance.max_resonance_weights == 20

    def test_create_gray_zone_method(self):
        """Verify create_gray_zone method works end-to-end"""
        from core.non_paradox_existence import (
            NonParadoxExistence, GrayZoneVariableType,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Ambiguous emotional state",
        )
        assert gz is not None
        assert gz.variable_id.startswith("gz_")
        assert gz.variable_type == GrayZoneVariableType.EMOTIONAL
        assert gz.description == "Ambiguous emotional state"
        assert gz.coexistence_active is False
        assert gz.cognitive_gap_threshold == 0.6
        assert gz.variable_id in instance.gray_zones
