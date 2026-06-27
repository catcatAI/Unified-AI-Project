import pytest

from apps.backend.src.core.hsm_formula_system import (
    CognitiveGap,
    ExplorationEvent,
    ExplorationResult,
    GovernanceBlueprint,
    HSMFormulaSystem,
)


class TestCognitiveGap:
    def test_calculate_pressure(self):
        gap = CognitiveGap(
            gap_id="test_1", domain="test",
            uncertainty_level=0.8, information_deficit=0.6,
        )
        pressure = gap.calculate_pressure()
        assert 0.5 < pressure < 1.5

    def test_calculate_pressure_fatigue(self):
        gap = CognitiveGap(
            gap_id="test_1", domain="test",
            uncertainty_level=0.8, information_deficit=0.6,
            exploration_attempts=10,
        )
        pressure = gap.calculate_pressure()
        assert pressure > 0.0


class TestHSMFormulaSystem:
    def test_initial_e_m2(self):
        hsm = HSMFormulaSystem()
        assert hsm.get_e_m2() == 0.1

    def test_hsm_threshold_default(self):
        hsm = HSMFormulaSystem()
        assert hsm.hsm_threshold == 0.5

    def test_calculate_c_gap_empty(self):
        hsm = HSMFormulaSystem()
        assert hsm.calculate_c_gap() == 0.0

    def test_detect_cognitive_gap(self):
        hsm = HSMFormulaSystem()
        gap = hsm.detect_cognitive_gap("test_domain", uncertainty_level=0.7, information_deficit=0.5)
        assert gap.domain == "test_domain"
        assert gap.uncertainty_level == 0.7
        assert len(hsm.cognitive_gaps) == 1

    def test_calculate_c_gap_with_gaps(self):
        hsm = HSMFormulaSystem()
        hsm.detect_cognitive_gap("domain_a", uncertainty_level=0.8, information_deficit=0.6)
        hsm.detect_cognitive_gap("domain_b", uncertainty_level=0.5, information_deficit=0.4)
        c_gap = hsm.calculate_c_gap()
        assert c_gap > 0.0

    def test_calculate_hsm(self):
        hsm = HSMFormulaSystem()
        hsm.detect_cognitive_gap("domain_a", uncertainty_level=0.9, information_deficit=0.9)
        hsm_value = hsm.calculate_hsm()
        assert hsm_value == pytest.approx(hsm.calculate_c_gap() * 0.1)
        assert hsm_value >= 0.0

    def test_trigger_exploration_no_gap(self):
        hsm = HSMFormulaSystem()
        event = hsm.trigger_exploration()
        assert event.triggered_by == "general"
        assert len(hsm.exploration_history) == 1

    def test_trigger_exploration_with_gap(self):
        hsm = HSMFormulaSystem()
        gap = hsm.detect_cognitive_gap("test", uncertainty_level=0.5, information_deficit=0.5)
        event = hsm.trigger_exploration(gap.gap_id)
        assert event.triggered_by == gap.gap_id
        assert hsm.cognitive_gaps[gap.gap_id].exploration_attempts == 1
        assert hsm.cognitive_gaps[gap.gap_id].resolution_status == "exploring"

    def test_update_cognitive_gap(self):
        hsm = HSMFormulaSystem()
        gap = hsm.detect_cognitive_gap("test", uncertainty_level=0.5, information_deficit=0.5)
        updated = hsm.update_cognitive_gap(gap.gap_id, uncertainty_level=0.9)
        assert updated is not None
        assert updated.uncertainty_level == 0.9

    def test_update_cognitive_gap_nonexistent(self):
        hsm = HSMFormulaSystem()
        result = hsm.update_cognitive_gap("nonexistent", uncertainty_level=0.9)
        assert result is None

    def test_activate_governance_rule(self):
        hsm = HSMFormulaSystem()
        gap = hsm.detect_cognitive_gap("test", uncertainty_level=0.5, information_deficit=0.5)
        event = hsm.trigger_exploration(gap.gap_id)
        event.discoveries.append({
            "type": ExplorationResult.RULE_CANDIDATE,
            "confidence": 0.8,
            "description": "test rule",
        })

    def test_activate_governance_rule_nonexistent(self):
        hsm = HSMFormulaSystem()
        assert hsm.activate_governance_rule("nonexistent") is False

    def test_get_governance_summary_empty(self):
        hsm = HSMFormulaSystem()
        summary = hsm.get_governance_summary()
        assert summary["total_rules"] == 0

    def test_get_hsm_status(self):
        hsm = HSMFormulaSystem()
        hsm.detect_cognitive_gap("test", uncertainty_level=0.6, information_deficit=0.5)
        status = hsm.get_hsm_status()
        assert "hsm_value" in status
        assert "c_gap" in status
        assert "explorations" in status
        assert "governance" in status

    def test_initial_running_state(self):
        hsm = HSMFormulaSystem()
        assert hasattr(hsm, "_running")
        assert hsm._running is False
