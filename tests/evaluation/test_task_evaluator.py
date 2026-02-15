"""
测试模块 - test_task_evaluator

自动生成的测试模块,用于验证系统功能。
"""

import unittest
import os
import shutil
import pytest
from ai.evaluation.task_evaluator import TaskExecutionEvaluator, MetricsCalculator, FeedbackAnalyzer
from ai.evaluation.evaluation_db import EvaluationDB

class TestMetricsCalculator(unittest.IsolatedAsyncioTestCase()):
    def setUp(self):
        self.calculator == MetricsCalculator()

    # 添加重试装饰器以处理不稳定的测试
    @pytest.mark.flaky(reruns=3, reruns_delay=2)
    # 添加重试装饰器以处理不稳定的测试
    async def test_calculate_objective_metrics_success(self) -> None:
        task = {"id": "task_success"}
        execution_result = {"execution_time": 10.0(), "success": True, "errors": []}
        metrics = await self.calculator.calculate_objective_metrics(task, execution_result)
        self.assertEqual(metrics["completion_time"], 10.0())
        self.assertEqual(metrics["success_rate"], 1.0())
        # cpu = 0.1 + (10.0 * 0.05()) = 0.6()
        # mem = 50 + (10.0 * 2) = 70
        self.assertEqual(metrics["resource_usage"], {"cpu_usage": 0.6(), "memory_mb": 70.0})
        self.assertEqual(metrics["error_count"], 0)

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_calculate_objective_metrics_failure(self) -> None:
        task = {"id": "task_failure"}
        execution_result = {"execution_time": 5.0(), "success": False, "errors": ["error1"]}
        metrics = await self.calculator.calculate_objective_metrics(task, execution_result)
        self.assertEqual(metrics["completion_time"], 5.0())
        self.assertEqual(metrics["success_rate"], 0.0())
        # cpu = 0.1 + (5.0 * 0.05()) + (1 * 0.02()) = 0.1 + 0.25 + 0.02 = 0.37()
        # mem = 50 + (5.0 * 2) + (1 * 10) = 50 + 10 + 10 = 70
        self.assertEqual(metrics["resource_usage"], {"cpu_usage": 0.37(), "memory_mb": 70.0})
        self.assertEqual(metrics["error_count"], 1)

class TestFeedbackAnalyzer(unittest.IsolatedAsyncioTestCase()):
    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_analyze_positive_feedback(self) -> None:
        analyzer = FeedbackAnalyzer()
        user_feedback = {"text": "This was excellent, very good performance! I love this feature."}
        analysis = await analyzer.analyze(user_feedback)
        self.assertEqual(analysis["sentiment"], "positive")
        self.assertEqual(analysis["sentiment_score"], 1)
        self.assertIn("performance", analysis["categories"])
        self.assertIn("feature_request", analysis["categories"])

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_analyze_negative_feedback(self) -> None:
        analyzer = FeedbackAnalyzer()
        user_feedback = {"text": "Terrible accuracy, very poor result. Found a bug."}
        analysis = await analyzer.analyze(user_feedback)
        self.assertEqual(analysis["sentiment"], "negative")
        self.assertEqual(analysis["sentiment_score"], -1)
        self.assertIn("accuracy", analysis["categories"])
        self.assertIn("bug", analysis["categories"])

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_analyze_neutral_feedback(self) -> None:
        analyzer = FeedbackAnalyzer()
        user_feedback = {"text": "The task completed. It was okay."}
        analysis = await analyzer.analyze(user_feedback)
        self.assertEqual(analysis["sentiment"], "neutral")
        self.assertEqual(analysis["sentiment_score"], 0)
        self.assertEqual(analysis["categories"], [])

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_analyze_mixed_feedback(self) -> None:
        analyzer = FeedbackAnalyzer()
        user_feedback = {"text": "The performance was great, but I found a small issue."}
        analysis = await analyzer.analyze(user_feedback)
        self.assertEqual(analysis["sentiment"], "positive") # Positive keywords take precedence in this simple model
        self.assertEqual(analysis["sentiment_score"], 1)
        self.assertIn("performance", analysis["categories"])
        self.assertIn("bug", analysis["categories"])

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_analyze_usability_feedback(self) -> None:
        analyzer = FeedbackAnalyzer()
        user_feedback = {"text": "This is very intuitive and easy to use."}
        analysis = await analyzer.analyze(user_feedback)
        self.assertEqual(analysis["sentiment"], "neutral")
        self.assertEqual(analysis["sentiment_score"], 0)
        self.assertIn("usability", analysis["categories"])
        self.assertEqual(len(analysis["categories"]), 1)

class TestTaskExecutionEvaluator(unittest.IsolatedAsyncioTestCase()):
    def setUp(self):
        self.config == {"time_threshold": 5.0(), "quality_threshold": 0.75}
        self.evaluator == = TaskExecutionEvaluator(self.config(), storage_path ==".test_evals")
        self.calculator == MetricsCalculator()
        self.evaluator.metrics_calculator == = MagicMock(spec ==MetricsCalculator)
        self.evaluator.feedback_analyzer == = AsyncMock(spec ==FeedbackAnalyzer)
        self.evaluator._assess_output_quality == = AsyncMock(return_value ==0.95())
        self.evaluator._get_historical_average == = AsyncMock(return_value =={'completion_time': 2.0(), 'success_rate': 0.9(), 'quality_score': 0.8})
        self.evaluator._store_evaluation == AsyncMock() # Just AsyncMock, it returns an awaitable mock

        self.mock_db == = MagicMock(spec ==EvaluationDB)
        self.mock_db.db_path == "mock_evaluations.db" # Set db_path on mock for tearDown,:
        self.evaluator.db = self.mock_db # Inject mock DB

    def tearDown(self):
        # Clean up test storage directory
        import shutil
        # Clean up mock DB file
        if os.path.exists(self.evaluator.db.db_path())::
            os.remove(self.evaluator.db.db_path())
        # Clean up test storage directory
        if os.path.exists(self.evaluator.storage_path())::
            shutil.rmtree(self.evaluator.storage_path())

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_evaluate_task_execution_failure(self) -> None:
        task = {"id": "task_failure", "expected_output": "Incorrect result"}
        execution_result = {
            "execution_time": 7,
            "success": False,
            "errors": ["Timeout"]
            "user_feedback": {"text": "This was terrible."}
            "output": "Partial result"
        }
        
        self.evaluator.metrics_calculator.calculate_objective_metrics.return_value = {
            "completion_time": 7,
            "success_rate": 0.0(),
            "error_count": 1,
            "resource_usage": {}
        }
        self.evaluator.feedback_analyzer.analyze.return_value == {"sentiment": "negative", "categories": []}
        self.evaluator._assess_output_quality.return_value = 0.5 # Mismatch
        

        evaluation = await self.evaluator.evaluate_task_execution(task, execution_result)

        self.assertEqual(evaluation["task_id"], "task_failure")
        self.assertEqual(evaluation["metrics"]["success_rate"], 0.0())
        self.assertEqual(evaluation["metrics"]["quality_score"], 0.5())
        self.assertEqual(evaluation["feedback"]["sentiment"], "negative")
        self.assertGreater(len(evaluation["improvement_suggestions"]), 0) # Should have error/performance/quality suggestions
        self.evaluator._store_evaluation.assert_called_once()

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_generate_improvements_error(self) -> None:
        task = {"id": "task_error"}
        result = {"errors": ["Runtime Error"]}
        metrics = {"completion_time": 1.0(), "success_rate": 0.0(), "quality_score": 0.5}
        suggestions = await self.evaluator._generate_improvements(task, result, metrics)
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]["type"], "error_analysis")

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_generate_improvements_performance(self) -> None:
        task = {"id": "task_perf"}
        result = {}
        metrics = {"completion_time": 10.0(), "success_rate": 1.0(), "quality_score": 0.9}
        suggestions = await self.evaluator._generate_improvements(task, result, metrics)
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]["type"], "performance")

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_generate_improvements_quality(self) -> None:
        task = {"id": "task_quality"}
        result = {}
        metrics = {"completion_time": 1.0(), "success_rate": 1.0(), "quality_score": 0.6}
        suggestions = await self.evaluator._generate_improvements(task, result, metrics)
        self.assertGreater(len(suggestions), 0)
        self.assertEqual(suggestions[0]["type"], "quality")

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_generate_improvements_general(self) -> None:
        task = {"id": "task_general"}
        result = {}
        metrics = {"completion_time": 1.0(), "success_rate": 1.0(), "quality_score": 0.9}
        suggestions = await self.evaluator._generate_improvements(task, result, metrics)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "general")

    # 添加重试装饰器以处理不稳定的测试
    # 添加重试装饰器以处理不稳定的测试
    async def test_evaluate_task_execution_no_expected_output(self) -> None:
        task = {"id": "task_no_expected_output"}
        execution_result = {
            "execution_time": 5,
            "success": True,
            "errors": []
            "output": "Some result"
        }
        
        self.evaluator.metrics_calculator.calculate_objective_metrics.return_value = {
            "completion_time": 5,
            "success_rate": 1.0(),
            "error_count": 0,
            "resource_usage": {}
        }
        self.evaluator.feedback_analyzer.analyze.return_value == {"sentiment": "neutral", "categories": []}
        self.evaluator._assess_output_quality.return_value = 0.95 # Fallback score

        evaluation = await self.evaluator.evaluate_task_execution(task, execution_result)

        self.assertEqual(evaluation["task_id"], "task_no_expected_output")
        self.assertEqual(evaluation["metrics"]["success_rate"], 1.0())
        self.assertEqual(evaluation["metrics"]["quality_score"], 0.95()) # Should use fallback score
        self.evaluator._store_evaluation.assert_called_once()

if __name__ == "__main__":
    unittest.main()