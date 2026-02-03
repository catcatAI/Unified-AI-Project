import logging
import random
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculates objective task metrics based on execution results."""

    def calculate_metrics(
        self,
        task: Any,
        execution_result: dict[str, Any],
    ) -> dict[str, Any]:
        task_id = task.id if hasattr(task, "id") else "N/A"
        logger.info(f"MetricsCalculator: Calculating metrics for task {task_id}")

        # Simulate completion time (e.g., based on task complexity or actual duration)
        completion_time = execution_result.get("duration", random.uniform(1.0, 60.0))

        # Simulate success rate (e.g., based on a 'status' field or error presence)
        status = execution_result.get("status", "unknown").lower()
        success_rate = (
            1.0
            if status == "success"
            else (0.0 if status == "failed" else random.uniform(0.4, 0.9))
        )
        if "error" in execution_result:
            success_rate = max(0.0, success_rate - random.uniform(0.1, 0.3))

        # Simulate resource usage (placeholder for more detailed metrics)
        resource_usage = {
            "cpu_percent": random.uniform(10.0, 90.0),
            "memory_mb": random.randint(100, 1024),
        }

        # Simulate error count
        error_count = len(execution_result.get("errors", []))

        return {
            "completion_time": round(completion_time, 2),
            "success_rate": round(success_rate, 2),
            "resource_usage": resource_usage,
            "error_count": error_count,
        }


class FeedbackAnalyzer:
    """Analyzes subjective feedback for sentiment and categorization."""

    def analyze_feedback(self, feedback: str) -> dict[str, Any]:
        logger.info(f"FeedbackAnalyzer: Analyzing feedback: {feedback[:50]}...")
        feedback_lower = feedback.lower()

        sentiment = "neutral"
        if any(
            word in feedback_lower
            for word in ["good", "great", "excellent", "satisfied", "happy"]
        ):
            sentiment = "positive"
        elif any(
            word in feedback_lower
            for word in ["bad", "poor", "failed", "frustrated", "unhappy"]
        ):
            sentiment = "negative"

        categories = []
        if "performance" in feedback_lower or "speed" in feedback_lower:
            categories.append("performance")
        if "accuracy" in feedback_lower or "correctness" in feedback_lower:
            categories.append("accuracy")
        if "usability" in feedback_lower or "interface" in feedback_lower:
            categories.append("usability")

        return {
            "sentiment": sentiment,
            "categories": categories,
            "raw_feedback": feedback,
        }


class TaskExecutionEvaluator:
    """Evaluates the execution of AI tasks by calculating objective metrics,
    analyzing subjective feedback, and generating actionable improvement suggestions.
    """

    def __init__(self):
        logger.info("TaskExecutionEvaluator initialized.")
        self.metrics_calculator = MetricsCalculator()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.evaluation_history: list[dict[str, Any]] = []  # Stores evaluation results

    async def evaluate_task(
        self,
        task: Any,
        execution_result: dict[str, Any],
        feedback: str = None,
    ) -> dict[str, Any]:
        """Evaluates a task's execution based on objective metrics and subjective feedback."""
        task_id = task.id if hasattr(task, "id") else "N/A"
        logger.info(f"Evaluating task {task_id}...")

        # 1. Calculate Objective Metrics
        objective_metrics = self.metrics_calculator.calculate_metrics(
            task,
            execution_result,
        )

        # 2. Analyze Subjective Feedback
        subjective_analysis = {}
        if feedback:
            subjective_analysis = self.feedback_analyzer.analyze_feedback(feedback)

        # 3. Assess Output Quality
        output_quality_assessment = self._assess_output_quality(
            execution_result,
            objective_metrics,
        )

        # 4. Generate Improvement Suggestions
        improvement_suggestions = self._generate_improvement_suggestions(
            objective_metrics,
            subjective_analysis,
            output_quality_assessment,
        )

        evaluation_result = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "objective_metrics": objective_metrics,
            "subjective_analysis": subjective_analysis,
            "output_quality_assessment": output_quality_assessment,
            "improvement_suggestions": improvement_suggestions,
        }
        self.evaluation_history.append(evaluation_result)
        logger.info(f"Task evaluation completed for task {task_id}.")
        return evaluation_result

    def _assess_output_quality(
        self,
        execution_result: dict[str, Any],
        objective_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Assesses the quality of the task's output based on various factors.
        This is where the bug fix mentioned in GEMINI.md would have been applied.
        """
        logger.debug("Assessing output quality.")
        output = execution_result.get("output", "")
        quality_score = 0.7  # Base score

        # Deduct points for errors
        if objective_metrics.get("error_count", 0) > 0:
            quality_score -= 0.3

        # Adjust based on keywords in output
        output_lower = output.lower()
        if "incomplete" in output_lower or "partial" in output_lower:
            quality_score -= 0.2
        if "irrelevant" in output_lower:
            quality_score -= 0.4
        if "perfect" in output_lower or "excellent" in output_lower:
            quality_score += 0.1

        quality_score = max(0.0, min(1.0, quality_score))  # Clamp between 0 and 1

        details = "Output quality assessed based on execution status and content."
        if objective_metrics.get("error_count", 0) > 0:
            details += f" {objective_metrics['error_count']} errors detected."

        return {"score": round(quality_score, 2), "details": details}

    def _generate_improvement_suggestions(
        self,
        objective_metrics: dict[str, Any],
        subjective_analysis: dict[str, Any],
        output_quality_assessment: dict[str, Any],
    ) -> list[str]:
        """Generates actionable improvement suggestions based on evaluation results."""
        suggestions = []

        # Suggestions based on objective metrics
        if objective_metrics.get("success_rate", 0) < 0.6:
            suggestions.append(
                "Focus on improving task success rate. Analyze common failure points.",
            )
        if objective_metrics.get("completion_time", 0) > 30.0:  # Example threshold
            suggestions.append("Optimize task execution time. Look for bottlenecks.")
        if objective_metrics.get("error_count", 0) > 0:
            suggestions.append(
                "Investigate and resolve recurring errors in task execution.",
            )

        # Suggestions based on subjective feedback
        if subjective_analysis.get("sentiment") == "negative":
            suggestions.append(
                f"Address negative user feedback: '{subjective_analysis.get('raw_feedback', '')[:50]}...'.",
            )
            if "accuracy" in subjective_analysis.get("categories", []):
                suggestions.append("Improve accuracy/correctness of task outputs.")
            if "performance" in subjective_analysis.get("categories", []):
                suggestions.append("Enhance perceived performance/speed.")

        # Suggestions based on output quality
        if output_quality_assessment.get("score", 0) < 0.6:
            suggestions.append(
                "Enhance output quality. Review output generation process for relevance and completeness.",
            )

        if not suggestions:
            suggestions.append(
                "Task performance is satisfactory. Maintain current strategies.",
            )

        return list(set(suggestions))  # Return unique suggestions

    def get_evaluation_history(self) -> list[dict[str, Any]]:
        """Returns the stored evaluation history."""
        return self.evaluation_history

    def save_evaluation_results(self, file_path: str = "data/evaluation_history.json"):
        """Saves evaluation results to a JSON file."""
        import json
        import os
        
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.evaluation_history, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved evaluation results to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save evaluation results: {e}")
