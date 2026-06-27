"""Tests for core/non_paradox_existence.py"""
import pytest


class TestNonParadoxExistence:
    """Tests for NonParadoxExistence"""

    def test_import(self):
        """Verify module exposes expected classes and enums"""
        from core.non_paradox_existence import (
            CoexistenceField,
            GrayZoneVariable,
            GrayZoneVariableType,
            NonParadoxExistence,
            PossibilityState,
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
            GrayZoneVariableType,
            NonParadoxExistence,
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

    def test_add_possibility(self):
        """Verify add_possibility adds and normalizes weights"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        p = instance.add_possibility(gz.variable_id, "joy", "Joy", 0.5, 0.4)
        assert p is not None
        assert p.possibility_id == "joy"
        assert p.probability == 0.5
        assert p.resonance_weight == 1.0  # normalized since only one

    def test_add_possibility_nonexistent_variable(self):
        """Verify add_possibility returns None for missing variable"""
        from core.non_paradox_existence import NonParadoxExistence
        instance = NonParadoxExistence()
        result = instance.add_possibility("nonexistent", "joy")
        assert result is None

    def test_update_cognitive_gap_threshold_crossing(self):
        """Verify threshold crossing activates coexistence"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "a")
        instance.add_possibility(gz.variable_id, "b")
        instance.update_cognitive_gap(0.8)
        assert instance.coexistence_active is True
        assert gz.coexistence_active is True
        instance.update_cognitive_gap(0.2)
        assert instance.coexistence_active is False
        assert gz.coexistence_active is False

    def test_activate_deactivate_coexistence(self):
        """Verify activate/deactivate coexistence methods"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "a")
        instance.add_possibility(gz.variable_id, "b")
        instance.update_cognitive_gap(0.8)
        assert instance.activate_coexistence(gz.variable_id) is True
        assert gz.coexistence_active is True
        assert instance.deactivate_coexistence(gz.variable_id) is True
        assert gz.coexistence_active is False

    def test_activate_coexistence_insufficient_gap(self):
        """Verify activation fails when gap is below threshold"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "a")
        instance.add_possibility(gz.variable_id, "b")
        result = instance.activate_coexistence(gz.variable_id)
        assert result is False
        assert gz.coexistence_active is False

    def test_activate_coexistence_insufficient_possibilities(self):
        """Verify activation fails with only one possibility"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "a")
        instance.update_cognitive_gap(0.8)
        result = instance.activate_coexistence(gz.variable_id)
        assert result is False

    def test_activate_coexistence_nonexistent_variable(self):
        """Verify activation returns False for missing variable"""
        from core.non_paradox_existence import NonParadoxExistence
        instance = NonParadoxExistence()
        assert instance.activate_coexistence("nonexistent") is False

    def test_calculate_coexistence_state(self):
        """Verify coexistence state calculation"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "joy", "Joy", 0.6, 0.5)
        instance.add_possibility(gz.variable_id, "sadness", "Sadness", 0.4, 0.5)
        instance.update_cognitive_gap(0.8)
        instance.activate_coexistence(gz.variable_id)
        state = instance.calculate_coexistence_state(gz.variable_id)
        assert state is not None
        assert state["variable_id"] == gz.variable_id
        assert "joy" in state["coexisting_possibilities"]
        assert "sadness" in state["coexisting_possibilities"]
        assert "resonance_weights" in state
        assert "effective_weights" in state
        assert "global_cognitive_gap" in state

    def test_calculate_coexistence_state_not_active(self):
        """Verify None returned when coexistence is not active"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        state = instance.calculate_coexistence_state(gz.variable_id)
        assert state is None

    def test_create_coexistence_field(self):
        """Verify creating a coexistence field from multiple gray zones"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz1 = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "emo")
        gz2 = instance.create_gray_zone(GrayZoneVariableType.COGNITIVE, "cog")
        for gz in (gz1, gz2):
            instance.add_possibility(gz.variable_id, "a")
            instance.add_possibility(gz.variable_id, "b")
        instance.update_cognitive_gap(0.8)
        field = instance.create_coexistence_field([gz1.variable_id, gz2.variable_id])
        assert field is not None
        assert field.field_id.startswith("field_")
        assert len(field.gray_zones) == 2
        assert field.coherence_score > 0.0
        assert field.field_id in instance.coexistence_fields

    def test_create_coexistence_field_too_few(self):
        """Verify field creation fails with fewer than 2 variables"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        assert instance.create_coexistence_field([gz.variable_id]) is None

    def test_update_resonance_weight(self):
        """Verify updating resonance weight renormalizes"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "a", resonance_weight=0.3)
        instance.add_possibility(gz.variable_id, "b", resonance_weight=0.7)
        assert instance.update_resonance_weight(gz.variable_id, "a", 0.9) is True
        assert gz.possibilities["a"].resonance_weight > 0.5
        assert gz.possibilities["b"].resonance_weight > 0.0

    def test_update_resonance_weight_nonexistent(self):
        """Verify update_resonance_weight returns False for missing var/poss"""
        from core.non_paradox_existence import NonParadoxExistence
        instance = NonParadoxExistence()
        assert instance.update_resonance_weight("no_var", "no_poss", 0.5) is False

    def test_get_non_paradox_summary(self):
        """Verify full summary contains all expected keys"""
        from core.non_paradox_existence import (
            GrayZoneVariableType,
            NonParadoxExistence,
        )
        instance = NonParadoxExistence()
        summary = instance.get_non_paradox_summary()
        assert "global_cognitive_gap" in summary
        assert "coexistence_active" in summary
        assert "gray_zones" in summary
        assert "coexistence_fields" in summary
        assert "resonance" in summary
        assert summary["gray_zones"]["total"] == 0
        gz = instance.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "test")
        instance.add_possibility(gz.variable_id, "a")
        instance.add_possibility(gz.variable_id, "b")
        instance.update_cognitive_gap(0.8)
        instance.activate_coexistence(gz.variable_id)
        summary2 = instance.get_non_paradox_summary()
        assert summary2["coexistence_active"] is True
        assert summary2["gray_zones"]["active_coexistence"] == 1

    def test_gray_zone_can_coexist(self):
        """Verify GrayZoneVariable.can_coexist logic"""
        from core.non_paradox_existence import GrayZoneVariable, GrayZoneVariableType
        gz = GrayZoneVariable(variable_id="gz_1", variable_type=GrayZoneVariableType.EMOTIONAL, description="",
                              cognitive_gap_threshold=0.6)
        assert gz.can_coexist(0.8) is True
        assert gz.can_coexist(0.5) is False

    def test_coexistence_field_calculate_coherence(self):
        """Verify CoexistenceField.calculate_coherence edge cases"""
        from core.non_paradox_existence import CoexistenceField, GrayZoneVariable
        field = CoexistenceField(field_id="f1")
        assert field.calculate_coherence() == 0.0
        gz = GrayZoneVariable(variable_id="gz_1", variable_type=None, description="")
        field.gray_zones["gz_1"] = gz
        # not active, so coherence is 0
        assert field.calculate_coherence() == 0.0
