"""Tests for core/life_intensity_formula.py"""
import pytest


class TestLifeIntensityFormula:
    """Tests for LifeIntensityFormula"""

    def test_import(self):
        """Verify module exposes expected classes and enums"""
        from core.life_intensity_formula import (
            LifeIntensityFormula, KnowledgeDomain, KnowledgeState,
            ConstraintState, ObserverPresence, LifeIntensitySnapshot,
        )
        assert LifeIntensityFormula is not None
        assert hasattr(LifeIntensityFormula, 'calculate_life_intensity')
        assert hasattr(LifeIntensityFormula, 'update_knowledge_state')
        assert hasattr(LifeIntensityFormula, 'add_constraint')
        assert hasattr(LifeIntensityFormula, 'register_observer')
        assert hasattr(LifeIntensityFormula, 'get_life_intensity_summary')
        assert len(KnowledgeDomain) == 6

    def test_instantiation(self):
        """Verify basic instantiation and default state"""
        from core.life_intensity_formula import LifeIntensityFormula
        instance = LifeIntensityFormula()
        assert instance.knowledge_states == {}
        assert instance.constraint_states == {}
        assert instance.observers == {}
        assert instance.intensity_history == []
        assert instance.max_history_size == 10000
        assert instance.accumulated_gap_integral == 0.0
        assert instance.weights["c_inf"] == 0.25
        assert instance.weights["c_limit"] == 0.25
        assert instance.weights["m_f"] == 0.3
        assert instance.weights["time_integral"] == 0.2

    def test_instantiation_with_config(self):
        """Verify instantiation with config overrides default values"""
        from core.life_intensity_formula import LifeIntensityFormula
        instance = LifeIntensityFormula(config={
            "max_history_size": 5000,
            "c_inf_weight": 0.3,
            "c_limit_weight": 0.2,
            "intensity_threshold": 0.6,
        })
        assert instance.max_history_size == 5000
        assert instance.weights["c_inf"] == 0.3
        assert instance.weights["c_limit"] == 0.2
        assert instance._intensity_threshold == 0.6

    def test_calculate_life_intensity_method(self):
        """Verify life intensity calculation produces valid 0-1 result with all components"""
        from core.life_intensity_formula import (
            LifeIntensityFormula, KnowledgeDomain,
        )
        instance = LifeIntensityFormula()
        l_s = instance.calculate_life_intensity()
        assert 0.0 <= l_s <= 1.0
        assert isinstance(l_s, float)
        assert len(instance.intensity_history) == 1
        snapshot = instance.intensity_history[0]
        assert 0.0 <= snapshot.c_inf <= 1.0
        assert 0.0 <= snapshot.c_limit <= 1.0
        assert 0.0 <= snapshot.m_f <= 1.0
        assert 0.0 <= snapshot.time_integral <= 1.0
        assert snapshot.dominant_domain is None
        instance.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE, completeness=0.9, accessibility=0.9
        )
        instance.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE, "processing_limit", severity=0.3
        )
        l_s2 = instance.calculate_life_intensity()
        assert l_s2 > l_s
        snapshot2 = instance.intensity_history[-1]
        assert snapshot2.dominant_domain == KnowledgeDomain.WORLD_KNOWLEDGE
