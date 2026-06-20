"""Tests for core.bio.kinetic_validator — matches actual KineticValidator API"""
import pytest


class TestKineticValidator:
    def test_import(self):
        from core.bio.kinetic_validator import KineticValidator
        instance = KineticValidator()
        assert hasattr(instance, 'validate_action')
        # max_velocity is instance attribute, not class attribute

    def test_instantiation_defaults(self):
        from core.bio.kinetic_validator import KineticValidator
        instance = KineticValidator()
        assert instance.max_velocity == 500.0
        assert instance.max_acceleration == 200.0
        assert instance.last_pos is None
        assert instance.last_time is None

    def test_validate_move(self):
        from core.bio.kinetic_validator import KineticValidator
        instance = KineticValidator()
        valid, msg = instance.validate_action("move", {"x": 100, "y": 0})
        assert valid is True

    def test_validate_unknown_action(self):
        from core.bio.kinetic_validator import KineticValidator
        instance = KineticValidator()
        valid, msg = instance.validate_action("jump", {})
        assert valid is True
        assert msg == ""

    def test_calculate_strain(self):
        from core.bio.kinetic_validator import KineticValidator
        instance = KineticValidator()
        strain = instance.calculate_strain(50.0)
        assert strain == 0.01
        strain = instance.calculate_strain(450.0)
        assert strain == 0.15

    def test_instantiation_with_config(self):
        from core.bio.kinetic_validator import KineticValidator
        instance = KineticValidator(config={"max_velocity": 1000.0})
        assert instance.max_velocity == 1000.0
        assert instance.config == {"max_velocity": 1000.0}

        valid, msg = instance.validate_action("move", {"x": 200, "y": 0})
        assert valid is True
