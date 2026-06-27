"""Tests for core/active_cognition_formula.py"""
import pytest


class TestActiveCognitionFormula:
    """Tests for ActiveCognitionFormula"""

    def test_import(self):
        """Verify module exposes expected classes and methods"""
        from core.active_cognition_formula import (
            ActiveCognitionFormula,
            ActiveConstruction,
            OrderBaseline,
            OrderType,
            StressSource,
            StressVector,
        )
        assert ActiveCognitionFormula is not None
        assert hasattr(ActiveCognitionFormula, 'add_stress_vector')
        assert hasattr(ActiveCognitionFormula, 'add_order_baseline')
        assert hasattr(ActiveCognitionFormula, 'calculate_active_cognition')
        assert hasattr(ActiveCognitionFormula, 'calculate_s_stress')
        assert hasattr(ActiveCognitionFormula, 'calculate_o_order')
        assert hasattr(ActiveCognitionFormula, 'get_construction_statistics')

    def test_instantiation(self):
        """Verify basic instantiation and default state"""
        from core.active_cognition_formula import ActiveCognitionFormula
        instance = ActiveCognitionFormula()
        assert instance.stress_vectors == {}
        assert instance.order_baselines == {}
        assert instance.construction_history == []
        assert instance.total_constructions == 0
        assert instance.successful_constructions == 0
        assert instance.stress_decay_rate == 0.05
        assert instance.min_a_c_threshold == 0.5
        assert instance.max_history_size == 5000

    def test_instantiation_with_config(self):
        """Verify instantiation with config applies values correctly"""
        from core.active_cognition_formula import ActiveCognitionFormula
        instance = ActiveCognitionFormula(config={
            "stress_decay_rate": 0.1,
            "min_a_c_threshold": 0.7,
            "max_history_size": 1000,
        })
        assert instance.stress_decay_rate == 0.1
        assert instance.min_a_c_threshold == 0.7
        assert instance.max_history_size == 1000

    def test_stress_vector_import(self):
        """Verify StressVector dataclass and its calculate_stress_contribution"""
        from core.active_cognition_formula import StressSource, StressVector
        sv = StressVector(
            source=StressSource.NOVELTY_DEMAND,
            intensity=0.7,
            direction=0.5,
            persistence=0.3,
        )
        assert sv.source == StressSource.NOVELTY_DEMAND
        assert sv.intensity == 0.7
        assert sv.direction == 0.5
        assert sv.persistence == 0.3
        contribution = sv.calculate_stress_contribution()
        assert contribution == pytest.approx(0.7 * (0.7 + 0.3 * 0.3))

    def test_order_baseline_import(self):
        """Verify OrderBaseline dataclass and its calculate_order_strength"""
        from core.active_cognition_formula import OrderBaseline, OrderType
        ob = OrderBaseline(
            order_type=OrderType.ALGORITHMIC,
            stability=0.8,
            flexibility=0.3,
            complexity=0.5,
        )
        assert ob.order_type == OrderType.ALGORITHMIC
        assert ob.stability == 0.8
        assert ob.flexibility == 0.3
        assert ob.complexity == 0.5
        strength = ob.calculate_order_strength()
        expected = 0.8 * 0.5 + 0.3 * 0.3 + (1.0 - 0.5 * 0.2) * 0.2
        assert strength == pytest.approx(expected)
