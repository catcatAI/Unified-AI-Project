"""core.autonomous 自主系统子模块测试"""

import asyncio

from apps.backend.src.core.autonomous.feedback_collector import (
    AutonomousFeedbackCollector,
)
from apps.backend.src.core.autonomous.learning_integrator import LearningIntegrator
from apps.backend.src.core.autonomous.strategy_adjuster import StrategyAdjuster


class TestAutonomousFeedbackCollector:
    def test_collect_stores_feedback(self):
        collector = AutonomousFeedbackCollector()
        result = asyncio.run(collector.collect(source="scenario_a", outcome="success"))
        assert isinstance(result, list)
        assert len(collector.get_all_feedback()) == 1
        item = collector.get_all_feedback()[0]
        assert item["source"] == "scenario_a"
        assert item["data"]["outcome"] == "success"

    def test_clear_resets_feedback(self):
        collector = AutonomousFeedbackCollector()
        asyncio.run(collector.collect(source="s1"))
        collector.clear()
        assert collector.get_all_feedback() == []

    def test_unknown_source_default(self):
        collector = AutonomousFeedbackCollector()
        asyncio.run(collector.collect())
        assert collector.get_all_feedback()[0]["source"] == "unknown"


class TestLearningIntegrator:
    def test_integrate_records_data(self):
        integrator = LearningIntegrator()
        ok = asyncio.run(integrator.integrate({"type": "experience", "data": "x"}))
        assert ok is True
        assert integrator.get_integration_count() == 1

    def test_integrate_empty_returns_false(self):
        integrator = LearningIntegrator()
        ok = asyncio.run(integrator.integrate())
        assert ok is False
        assert integrator.get_integration_count() == 0

    def test_integrate_kwargs(self):
        integrator = LearningIntegrator()
        asyncio.run(integrator.integrate(source="agent"))
        assert integrator.get_integration_count() == 1


class TestStrategyAdjuster:
    def test_adjust_merges_overrides(self):
        adjuster = StrategyAdjuster()
        adjusted = asyncio.run(
            adjuster.adjust({"timeout": 5}, timeout=10, retry=3)
        )
        assert adjusted == {"timeout": 10, "retry": 3}

    def test_adjustment_history_tracked(self):
        adjuster = StrategyAdjuster()
        asyncio.run(adjuster.adjust({"a": 1}))
        asyncio.run(adjuster.adjust({"b": 2}))
        assert len(adjuster.get_adjustment_history()) == 2
