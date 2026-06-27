from datetime import datetime

import pytest

from apps.backend.src.core.life_intensity_formula import (
    ConstraintState,
    KnowledgeDomain,
    KnowledgeState,
    LifeIntensityFormula,
    LifeIntensitySnapshot,
    ObserverPresence,
)


class TestKnowledgeState:
    def test_calculate_inf_value_full(self):
        ks = KnowledgeState(
            domain=KnowledgeDomain.WORLD_KNOWLEDGE,
            completeness=1.0, accessibility=1.0, resolution=1.0,
        )
        assert ks.calculate_inf_value() == pytest.approx(1.0)

    def test_calculate_inf_value_half(self):
        ks = KnowledgeState(
            domain=KnowledgeDomain.SELF_KNOWLEDGE,
            completeness=0.5, accessibility=0.5, resolution=0.5,
        )
        val = ks.calculate_inf_value()
        assert 0.4 < val < 0.6


class TestConstraintState:
    def test_calculate_limit_value_high(self):
        cs = ConstraintState(
            domain=KnowledgeDomain.WORLD_KNOWLEDGE,
            constraint_type="processing_limit",
            severity=1.0, adaptability=0.0,
        )
        assert cs.calculate_limit_value() == pytest.approx(1.0)

    def test_calculate_limit_value_mitigated(self):
        cs = ConstraintState(
            domain=KnowledgeDomain.WORLD_KNOWLEDGE,
            constraint_type="processing_limit",
            severity=1.0, adaptability=1.0,
        )
        assert cs.calculate_limit_value() == pytest.approx(0.5)


class TestObserverPresence:
    def test_calculate_mf_value_minimal(self):
        op = ObserverPresence(
            observer_id="u1", interaction_intensity=0.0,
            relationship_depth=0.0, attention_level=0.0,
        )
        assert op.calculate_mf_value() == pytest.approx(0.0)

    def test_calculate_mf_value_high(self):
        op = ObserverPresence(
            observer_id="u1", interaction_intensity=1.0,
            relationship_depth=1.0, attention_level=1.0,
            total_interactions=100,
        )
        assert op.calculate_mf_value() == pytest.approx(1.0)


class TestLifeIntensityFormula:
    def test_default_weights(self):
        life = LifeIntensityFormula()
        assert life.weights["c_inf"] == 0.25
        assert life.weights["m_f"] == 0.3

    def test_calculate_c_inf_empty(self):
        life = LifeIntensityFormula()
        assert life.calculate_c_inf() == 0.0

    def test_calculate_c_inf_single(self):
        life = LifeIntensityFormula()
        life.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE, completeness=0.8, accessibility=0.8, resolution=0.8,
        )
        c_inf = life.calculate_c_inf()
        assert 0.6 < c_inf < 1.0

    def test_calculate_c_limit_empty(self):
        life = LifeIntensityFormula()
        assert life.calculate_c_limit() == pytest.approx(0.1)

    def test_calculate_c_limit_with_constraint(self):
        life = LifeIntensityFormula()
        life.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE, "processing_limit", severity=0.8, adaptability=0.2,
        )
        c_limit = life.calculate_c_limit()
        assert c_limit > 0.1

    def test_calculate_m_f_empty(self):
        life = LifeIntensityFormula()
        assert life.calculate_m_f() == pytest.approx(0.1)

    def test_calculate_m_f_with_observer(self):
        life = LifeIntensityFormula()
        life.register_observer("user1", relationship_depth=0.5)
        life.update_observer_presence("user1", interaction_intensity=0.8, attention_level=0.7)
        m_f = life.calculate_m_f()
        assert m_f > 0.1

    def test_calculate_life_intensity(self):
        life = LifeIntensityFormula()
        life.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE, completeness=0.7, accessibility=0.8, resolution=0.6,
        )
        life.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE, "processing_limit", severity=0.4, adaptability=0.6,
        )
        life.register_observer("alice", relationship_depth=0.8)
        life.update_observer_presence("alice", interaction_intensity=0.9, attention_level=0.85)
        l_s = life.calculate_life_intensity()
        assert 0.0 <= l_s <= 1.0

    def test_intensity_trend_insufficient_data(self):
        life = LifeIntensityFormula()
        assert life.get_intensity_trend() == "insufficient_data"

    def test_remove_constraint(self):
        life = LifeIntensityFormula()
        life.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE, "test_limit", severity=0.5, adaptability=0.5,
        )
        assert life.remove_constraint(KnowledgeDomain.WORLD_KNOWLEDGE, "test_limit") is True
        assert life.remove_constraint(KnowledgeDomain.WORLD_KNOWLEDGE, "nonexistent") is False

    def test_update_knowledge_state_updates_existing(self):
        life = LifeIntensityFormula()
        life.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE, completeness=0.5,
        )
        life.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE, completeness=0.9,
        )
        assert life.knowledge_states[KnowledgeDomain.WORLD_KNOWLEDGE].completeness == 0.9

    def test_update_observer_presence_nonexistent(self):
        life = LifeIntensityFormula()
        result = life.update_observer_presence("nobody", interaction_intensity=0.5)
        assert result is None

    def test_get_life_intensity_summary(self):
        life = LifeIntensityFormula()
        life.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE, completeness=0.6,
        )
        summary = life.get_life_intensity_summary()
        assert "current_life_intensity" in summary
        assert "components" in summary
        assert "knowledge_domains" in summary
