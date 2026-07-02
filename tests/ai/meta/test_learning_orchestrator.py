from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_evaluator():
    evaluator = MagicMock()
    evaluator.evaluate_task_execution = AsyncMock(return_value={
        "task_id": "task_1",
        "timestamp": "2026-01-01T00:00:00",
        "metrics": {
            "success_rate": 0.9,
            "duration": 1.5,
            "efficiency": 0.8,
            "coherence_score": 0.75,
            "quality_score": 0.85,
            "cognitive_dividend": 0.6,
            "life_intensity_impact": 0.7,
            "consistency_score": 1.0,
        },
        "consistency_report": {"score": 1.0, "conflicts": []},
        "feedback_analysis": {"sentiment": "positive", "accuracy_gap": 0.0},
        "suggestions": ["性能達標，繼續保持"],
        "overall_rating": 0.88,
    })
    return evaluator


@pytest.fixture
def orchestrator(mock_evaluator):
    from apps.backend.src.ai.meta.learning_orchestrator import LearningOrchestrator
    orc = LearningOrchestrator(config={})
    orc.evaluator = mock_evaluator
    return orc


@pytest.fixture
def orchestrator_with_config(mock_evaluator):
    from apps.backend.src.ai.meta.learning_orchestrator import LearningOrchestrator
    orc = LearningOrchestrator(config={
        "evaluator_config": {"threshold": 0.5},
        "controller_config": {"default_strategy": "aggressive", "initial_learning_rate": 0.1},
    })
    orc.evaluator = mock_evaluator
    return orc


class TestLearningOrchestratorInit:
    def test_init_default_config(self):
        from apps.backend.src.ai.meta.learning_orchestrator import LearningOrchestrator
        orc = LearningOrchestrator()
        assert orc.config == {}
        assert orc.learning_history == []

    def test_init_with_config(self, orchestrator_with_config):
        assert orchestrator_with_config.config["evaluator_config"]["threshold"] == 0.5
        assert orchestrator_with_config.controller.current_strategy == "aggressive"
        assert orchestrator_with_config.controller.learning_rate == 0.1


class TestLearningOrchestratorProcessCycle:
    async def test_process_learning_cycle_returns_expected_keys(self, orchestrator):
        task = {"id": "task_001", "type": "reasoning"}
        execution_result = {"output": "test output", "success": True}
        result = await orchestrator.process_learning_cycle(task, execution_result)
        assert "task_id" in result
        assert "evaluation" in result
        assert "adaptation" in result
        assert "timestamp" in result
        assert result["task_id"] == "task_001"
    async def test_process_learning_cycle_appends_history(self, orchestrator):
        assert len(orchestrator.learning_history) == 0
        await orchestrator.process_learning_cycle(
            {"id": "t1", "type": "test"},
            {"output": "ok", "success": True},
        )
        assert len(orchestrator.learning_history) == 1
    async def test_process_learning_cycle_multiple_cycles(self, orchestrator):
        for i in range(3):
            await orchestrator.process_learning_cycle(
                {"id": f"t{i}", "type": "test"},
                {"output": "ok", "success": True},
            )
        assert len(orchestrator.learning_history) == 3
    async def test_process_learning_cycle_calls_evaluator(self, orchestrator, mock_evaluator):
        task = {"id": "t1", "type": "reasoning"}
        result = {"output": "done", "success": False}
        await orchestrator.process_learning_cycle(task, result)
        mock_evaluator.evaluate_task_execution.assert_called_once_with(task, result)
    async def test_process_learning_cycle_evaluation_in_result(self, orchestrator):
        result = await orchestrator.process_learning_cycle(
            {"id": "t1"},
            {"output": "hello", "success": True},
        )
        assert result["evaluation"]["overall_rating"] == 0.88
        assert result["evaluation"]["metrics"]["success_rate"] == 0.9
    async def test_process_learning_cycle_adaptation_has_strategy(self, orchestrator):
        result = await orchestrator.process_learning_cycle(
            {"id": "t1"},
            {"output": "test", "success": True},
        )
        assert "new_strategy" in result["adaptation"]
        assert "previous_strategy" in result["adaptation"]


class TestLearningOrchestratorStatus:
    def test_get_learning_status_empty(self, orchestrator):
        status = orchestrator.get_learning_status()
        assert status["cycles_completed"] == 0
        assert status["latest_rating"] == 0.0
    async def test_get_learning_status_after_cycle(self, orchestrator):
        await orchestrator.process_learning_cycle(
            {"id": "t1"},
            {"output": "ok", "success": True},
        )
        status = orchestrator.get_learning_status()
        assert status["cycles_completed"] == 1
        assert status["latest_rating"] == 0.88
        assert "strategy" in status["controller_config"]
        assert "learning_rate" in status["controller_config"]
    async def test_get_learning_status_uses_latest_rating(self, orchestrator, mock_evaluator):
        mock_evaluator.evaluate_task_execution = AsyncMock(return_value={
            "task_id": "t2",
            "timestamp": "2026-01-01T00:00:00",
            "metrics": {
                "success_rate": 0.5, "duration": 1.0, "efficiency": 0.5,
                "coherence_score": 0.5, "quality_score": 0.5,
                "cognitive_dividend": 0.5, "life_intensity_impact": 0.5,
                "consistency_score": 0.5,
            },
            "consistency_report": {"score": 0.5, "conflicts": []},
            "feedback_analysis": {"sentiment": "neutral", "accuracy_gap": 0.0},
            "suggestions": ["improve"],
            "overall_rating": 0.55,
        })
        await orchestrator.process_learning_cycle({"id": "t1"}, {"output": "first", "success": True})
        await orchestrator.process_learning_cycle({"id": "t2"}, {"output": "second", "success": False})
        status = orchestrator.get_learning_status()
        assert status["latest_rating"] == 0.55
