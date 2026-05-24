import pytest
from apps.backend.src.core.active_cognition_formula import (
    ActiveCognitionFormula, StressSource, OrderType,
    StressVector, OrderBaseline,
)


class TestStressVector:
    def test_calculate_stress_contribution(self):
        sv = StressVector(
            source=StressSource.NOVELTY_DEMAND,
            intensity=0.8, direction=0.5, persistence=0.5,
        )
        contrib = sv.calculate_stress_contribution()
        assert 0.6 < contrib < 1.0

    def test_calculate_stress_persistence_amplifies(self):
        sv_low = StressVector(
            source=StressSource.NOVELTY_DEMAND,
            intensity=0.5, direction=0.0, persistence=0.0,
        )
        sv_high = StressVector(
            source=StressSource.NOVELTY_DEMAND,
            intensity=0.5, direction=0.0, persistence=1.0,
        )
        assert sv_high.calculate_stress_contribution() > sv_low.calculate_stress_contribution()


class TestOrderBaseline:
    def test_calculate_order_strength_high(self):
        ob = OrderBaseline(
            order_type=OrderType.ALGORITHMIC,
            stability=1.0, flexibility=1.0, complexity=0.0,
        )
        assert ob.calculate_order_strength() > 0.5

    def test_calculate_order_strength_low(self):
        ob = OrderBaseline(
            order_type=OrderType.ALGORITHMIC,
            stability=0.0, flexibility=0.0, complexity=1.0,
        )
        assert ob.calculate_order_strength() < 0.5


class TestActiveCognitionFormula:
    def test_empty_s_stress(self):
        ac = ActiveCognitionFormula()
        assert ac.calculate_s_stress() == 0.0

    def test_empty_o_order(self):
        ac = ActiveCognitionFormula()
        assert ac.calculate_o_order() == pytest.approx(0.5)

    def test_add_stress_vector(self):
        ac = ActiveCognitionFormula()
        sv = ac.add_stress_vector(
            StressSource.CONTRADICTION, intensity=0.7, direction=0.5, persistence=0.6,
        )
        assert len(ac.stress_vectors) == 1
        assert sv.intensity == 0.7

    def test_remove_stress_vector(self):
        ac = ActiveCognitionFormula()
        ac.add_stress_vector(StressSource.NOVELTY_DEMAND, intensity=0.5)
        vid = list(ac.stress_vectors.keys())[0]
        assert ac.remove_stress_vector(vid) is True
        assert ac.remove_stress_vector("nonexistent") is False

    def test_add_order_baseline(self):
        ac = ActiveCognitionFormula()
        ob = ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.8, flexibility=0.3)
        assert len(ac.order_baselines) == 1

    def test_update_order_baseline(self):
        ac = ActiveCognitionFormula()
        ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.5, flexibility=0.5)
        oid = list(ac.order_baselines.keys())[0]
        ac.update_order_baseline(oid, stability=0.9)
        assert ac.order_baselines[oid].stability == 0.9

    def test_update_order_baseline_nonexistent(self):
        ac = ActiveCognitionFormula()
        result = ac.update_order_baseline("nonexistent", stability=0.9)
        assert result is None

    def test_calculate_s_stress_with_vectors(self):
        ac = ActiveCognitionFormula()
        ac.add_stress_vector(StressSource.CONTRADICTION, intensity=0.8, persistence=0.9)
        ac.add_stress_vector(StressSource.AMBIGUITY, intensity=0.6, persistence=0.7)
        s = ac.calculate_s_stress()
        assert s > 0.0

    def test_calculate_o_order_with_baselines(self):
        ac = ActiveCognitionFormula()
        ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.8, flexibility=0.3)
        ac.add_order_baseline(OrderType.PATTERN_BASED, stability=0.7, flexibility=0.5)
        o = ac.calculate_o_order()
        assert 0.0 < o <= 1.0

    def test_calculate_active_cognition_low(self):
        ac = ActiveCognitionFormula()
        ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.9, flexibility=0.9)
        a_c = ac.calculate_active_cognition()
        assert a_c < 1.0

    def test_calculate_active_cognition(self):
        ac = ActiveCognitionFormula()
        ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.5, flexibility=0.3)
        ac.add_stress_vector(StressSource.CONTRADICTION, intensity=0.9, persistence=0.9)
        a_c = ac.calculate_active_cognition()
        assert a_c > 0.0

    def test_construction_statistics_empty(self):
        ac = ActiveCognitionFormula()
        stats = ac.get_construction_statistics()
        assert stats["total_constructions"] == 0
        assert stats["success_rate"] == 0.0

    def test_interpret_a_c_all_levels(self):
        ac = ActiveCognitionFormula()
        assert "comfortable" in ac._interpret_a_c(0.3)["state"]
        assert "balanced" in ac._interpret_a_c(0.7)["state"]
        assert "active_construction" in ac._interpret_a_c(1.2)["state"]
        assert "struggle" in ac._interpret_a_c(1.7)["state"]
        assert "overload" in ac._interpret_a_c(2.1)["state"]

    def test_get_active_cognition_summary(self):
        ac = ActiveCognitionFormula()
        ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.8, flexibility=0.3)
        ac.add_stress_vector(StressSource.NOVELTY_DEMAND, intensity=0.5)
        summary = ac.get_active_cognition_summary()
        assert "a_c" in summary
        assert "s_stress" in summary
        assert "o_order" in summary
        assert "stress_vectors" in summary
        assert "order_baselines" in summary
