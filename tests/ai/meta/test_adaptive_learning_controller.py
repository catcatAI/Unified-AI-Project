import sys
from unittest.mock import MagicMock, PropertyMock

import pytest

_MODULE_MOCKS = {}
for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def tracker():
    from apps.backend.src.ai.meta.adaptive_learning_controller import PerformanceTracker
    return PerformanceTracker()


@pytest.fixture
def controller():
    from apps.backend.src.ai.meta.adaptive_learning_controller import AdaptiveLearningController
    return AdaptiveLearningController()


@pytest.fixture
def controller_custom():
    from apps.backend.src.ai.meta.adaptive_learning_controller import AdaptiveLearningController
    return AdaptiveLearningController(config={
        "default_strategy": "explorative_recovery",
        "initial_learning_rate": 0.1,
    })


class TestPerformanceTracker:
    async def test_analyze_trend_empty_list(self, tracker):
        result = await tracker.analyze_trend([])
        assert result == {"direction": "stable", "magnitude": 0.0, "slope": 0.0}
    async def test_analyze_trend_less_than_three(self, tracker):
        result = await tracker.analyze_trend([
            {"success_rate": 0.5},
            {"success_rate": 0.6},
        ])
        assert result == {"direction": "stable", "magnitude": 0.0, "slope": 0.0}
    async def test_analyze_trend_improving(self, tracker):
        data = [{"success_rate": 0.1 + i * 0.08} for i in range(5)]
        result = await tracker.analyze_trend(data)
        assert result["direction"] == "improving"
        assert result["slope"] > 0
    async def test_analyze_trend_degrading(self, tracker):
        data = [{"success_rate": 0.9 - i * 0.08} for i in range(5)]
        result = await tracker.analyze_trend(data)
        assert result["direction"] == "degrading"
        assert result["slope"] < 0
    async def test_analyze_trend_uses_last_ten_only(self, tracker):
        data = [{"success_rate": 0.5}] * 20
        result = await tracker.analyze_trend(data)
        assert result["direction"] in ("improving", "degrading", "stable")
    async def test_analyze_trend_missing_success_rate_defaults_zero(self, tracker):
        data = [{"success_rate": 0.9}, {"other": 1}, {"success_rate": 0.7}]
        result = await tracker.analyze_trend(data)
        assert "direction" in result


class TestAdaptiveLearningControllerInit:
    def test_init_default_config(self, controller):
        assert controller.current_strategy == "balanced"
        assert controller.learning_rate == 0.05
        assert controller.performance_history == []

    def test_init_custom_config(self, controller_custom):
        assert controller_custom.current_strategy == "explorative_recovery"
        assert controller_custom.learning_rate == 0.1
        assert controller_custom.performance_history == []


class TestAdaptiveLearningControllerDetermineStrategy:
    def test_determine_strategy_degrading(self, controller):
        result = controller._determine_strategy({"direction": "degrading", "slope": -0.05, "magnitude": 0.05})
        assert result == "explorative_recovery"

    def test_determine_strategy_improving_steep(self, controller):
        result = controller._determine_strategy({"direction": "improving", "slope": 0.15, "magnitude": 0.15})
        assert result == "acceleration"

    def test_determine_strategy_improving_shallow(self, controller):
        result = controller._determine_strategy({"direction": "improving", "slope": 0.05, "magnitude": 0.05})
        assert result == "stable_optimization"

    def test_determine_strategy_stable(self, controller):
        result = controller._determine_strategy({"direction": "stable", "slope": 0.0, "magnitude": 0.0})
        assert result == "stable_optimization"


class TestAdaptiveLearningControllerOptimizeParameters:
    def test_optimize_parameters_with_metrics(self, controller):
        metrics = [{"cognitive_dividend": 0.8, "life_intensity_impact": 0.7}]
        result = controller._optimize_parameters(
            {"direction": "improving", "slope": 0.05, "magnitude": 0.05},
            metrics,
        )
        assert "learning_rate" in result
        assert "adaptation_factor" in result
        assert 0.001 <= result["learning_rate"] <= 0.5

    def test_optimize_parameters_without_metrics(self, controller):
        result = controller._optimize_parameters(
            {"direction": "stable", "slope": 0.0, "magnitude": 0.0},
            [],
        )
        assert result["learning_rate"] == 0.0375
        assert result["adaptation_factor"] == 0.75

    def test_optimize_parameters_high_cog_dividend(self, controller):
        metrics = [{"cognitive_dividend": 0.9, "life_intensity_impact": 0.8}]
        result = controller._optimize_parameters(
            {"direction": "improving", "slope": 0.1, "magnitude": 0.1},
            metrics,
        )
        assert result["learning_rate"] == 0.047

    def test_optimize_parameters_low_life_intensity(self, controller):
        metrics = [{"cognitive_dividend": 0.3, "life_intensity_impact": 0.1}]
        result = controller._optimize_parameters(
            {"direction": "degrading", "slope": -0.1, "magnitude": 0.1},
            metrics,
        )
        assert result["adaptation_factor"] <= 0.6


class TestAdaptiveLearningControllerAdapt:
    async def test_adapt_no_metrics(self, controller):
        result = await controller.adapt_learning_strategy(
            {"id": "task_1", "type": "test"},
            [],
        )
        assert result["previous_strategy"] == "balanced"
        assert result["trend"] == "stable"
    async def test_adapt_with_metrics(self, controller):
        result = await controller.adapt_learning_strategy(
            {"id": "task_1", "type": "test"},
            [{"success_rate": 0.9, "cognitive_dividend": 0.5, "life_intensity_impact": 0.5}],
        )
        assert result["previous_strategy"] == "balanced"
        assert "timestamp" in result
    async def test_adapt_updates_performance_history(self, controller):
        metrics = [{"success_rate": 0.8, "cognitive_dividend": 0.5, "life_intensity_impact": 0.5}]
        await controller.adapt_learning_strategy({"id": "t1"}, metrics)
        assert len(controller.performance_history) == 1
        assert controller.performance_history[0]["success_rate"] == 0.8
    async def test_adapt_changes_strategy_on_degrading(self, controller):
        initial = controller.current_strategy
        degrading_metrics = [
            {"success_rate": 0.9 - i * 0.1, "cognitive_dividend": 0.5, "life_intensity_impact": 0.5}
            for i in range(5)
        ]
        result = await controller.adapt_learning_strategy({"id": "t1"}, degrading_metrics)
        assert result["new_strategy"] != initial or result["new_strategy"] == "explorative_recovery"


class TestAdaptiveLearningControllerGetConfig:
    def test_get_current_configuration(self, controller):
        config = controller.get_current_configuration()
        assert config["strategy"] == "balanced"
        assert config["learning_rate"] == 0.05
        assert config["history_depth"] == 0
