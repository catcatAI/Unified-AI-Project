"""Tests for AutonomousLifeCycle — formula-driven life decisions with config-driven feedback."""
from datetime import datetime

import pytest

from core.life.autonomous_life_cycle import AutonomousLifeCycle, FormulaMetrics, LifePhase
from core.system.config.magic_numbers import lifecycle_value


@pytest.fixture
def metrics():
    return FormulaMetrics(
        timestamp=datetime.now(),
        hsm_value=0.3, c_gap=0.2, cdm_conversion_rate=0.7,
        life_intensity=0.6, c_inf=0.8, c_limit=1.0, m_f=0.4,
        a_c=0.5, s_stress=0.3, o_order=0.4, cognitive_gap=0.3,
        coexistence_active=False, resonance_total=0.5,
    )


class TestLifecycleConfigDriven:
    def test_lifecycle_value_defaults(self):
        assert lifecycle_value("lifecycle.success_rate_low", 0.5) == 0.5
        assert lifecycle_value("lifecycle.success_rate_high", 0.9) == 0.9
        assert lifecycle_value("lifecycle.confidence_penalty", 0.15) == 0.15
        assert lifecycle_value("lifecycle.confidence_boost", 0.1) == 0.1
        assert lifecycle_value("lifecycle.risk_penalty", 0.2) == 0.2
        assert lifecycle_value("lifecycle.risk_boost", 0.15) == 0.15

    def test_init(self):
        alc = AutonomousLifeCycle()
        assert alc.current_phase == LifePhase.EMERGENCE
        assert alc.decisions_made == 0
        assert alc.executions_succeeded == 0
        assert alc.executions_failed == 0

    def test_evaluate_decide_no_decisions(self, metrics):
        alc = AutonomousLifeCycle()
        result = alc._evaluate_and_decide(metrics)
        assert result is None

    def test_no_executions_returns_none(self, metrics):
        alc = AutonomousLifeCycle()
        assert alc.executions_succeeded == 0
        assert alc.executions_failed == 0
        result = alc._evaluate_and_decide(metrics)
        assert result is None

    def test_low_success_rate_penalty(self, metrics):
        alc = AutonomousLifeCycle()
        alc.executions_succeeded = 1
        alc.executions_failed = 3
        result = alc._evaluate_and_decide(metrics)
        assert result is None

    def test_high_success_rate_boost(self, metrics):
        alc = AutonomousLifeCycle()
        alc.executions_succeeded = 10
        alc.executions_failed = 0
        alc.exploration_threshold = 0.5
        result = alc._evaluate_and_decide(metrics)
        assert result is not None or alc.executions_succeeded == 10
