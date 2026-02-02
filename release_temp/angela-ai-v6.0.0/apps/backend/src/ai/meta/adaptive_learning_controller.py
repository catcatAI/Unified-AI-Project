import json
import logging
import random
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Define the path for logging strategy improvements
STRATEGY_IMPROVEMENT_LOG_FILE = Path(__file__).parent / "strategy_improvement_log.jsonl"


class PerformanceTracker:
    """Tracks and analyzes AI performance trends based on task evaluations."""

    def __init__(self):
        self.task_evaluation_history: list[dict[str, Any]] = []
        self.max_history_size = 100  # Keep a rolling window of evaluations

    def add_evaluation_result(self, evaluation: dict[str, Any]):
        self.task_evaluation_history.append(evaluation)
        if len(self.task_evaluation_history) > self.max_history_size:
            self.task_evaluation_history.pop(0)  # Remove oldest

    def get_performance_trends(self) -> dict[str, Any]:
        logger.info("PerformanceTracker: Getting performance trends.")

        if not self.task_evaluation_history:
            return {
                "overall_success_rate": 0.75,
                "recent_task_success_rate": 0.6,
                "learning_speed": "medium",
                "areas_of_difficulty": ["complex_reasoning", "long_term_planning"],
                "trend": "stable",
            }

        # Calculate recent success rate (e.g., last 10 tasks)
        recent_evaluations = self.task_evaluation_history[-10:]
        successful_tasks = sum(
            1
            for eval_res in recent_evaluations
            if eval_res.get("objective_metrics", {}).get("success_rate", 0) >= 0.8
        )
        recent_success_rate = (
            successful_tasks / len(recent_evaluations) if recent_evaluations else 0.0
        )

        # Calculate overall success rate
        overall_successful_tasks = sum(
            1
            for eval_res in self.task_evaluation_history
            if eval_res.get("objective_metrics", {}).get("success_rate", 0) >= 0.8
        )
        overall_success_rate = overall_successful_tasks / len(
            self.task_evaluation_history,
        )

        # Simulate trend
        trend = "stable"
        if recent_success_rate > overall_success_rate + 0.05:
            trend = "improving"
        elif recent_success_rate < overall_success_rate - 0.05:
            trend = "declining"

        # Simulate areas of difficulty (could be derived from failed tasks' characteristics)
        areas_of_difficulty = random.sample(
            [
                "complex_reasoning",
                "long_term_planning",
                "novel_situations",
                "resource_management",
            ],
            k=random.randint(0, 2),
        )

        # Calculate learning speed based on trend
        learning_speed = "medium"
        if trend == "improving":
            learning_speed = "fast"
        elif trend == "declining":
            learning_speed = "slow"

        return {
            "overall_success_rate": round(overall_success_rate, 2),
            "recent_task_success_rate": round(recent_success_rate, 2),
            "learning_speed": learning_speed,
            "areas_of_difficulty": areas_of_difficulty,
            "trend": trend,
        }


class StrategySelector:
    """Selects optimal learning strategies based on performance trends and strategy effectiveness."""

    def select_strategy(
        self,
        performance_trends: dict[str, Any],
        available_strategies: dict[str, dict[str, Any]],
    ) -> str:
        logger.info("StrategySelector: Selecting learning strategy.")

        # Prioritize strategies with high effectiveness
        sorted_strategies = sorted(
            available_strategies.items(),
            key=lambda item: item[1].get("effectiveness", 0),
            reverse=True,
        )

        # If performance is declining, try a more exploratory strategy
        if (
            performance_trends.get("trend") == "declining"
            or performance_trends.get("recent_task_success_rate", 0) < 0.5
        ):
            # Look for an exploratory strategy or one with lower effectiveness to try something new
            for name, details in sorted_strategies:
                if "exploratory" in name:  # Simple keyword check
                    return name
            # If no explicit exploratory, pick a less effective one to try
            if (
                sorted_strategies
                and sorted_strategies[-1][0] != sorted_strategies[0][0]
            ):  # Don't pick the best if only one
                return sorted_strategies[-1][
                    0
                ]  # Pick the least effective to try something new

        # Otherwise, stick with the most effective strategy
        if sorted_strategies:
            return sorted_strategies[0][0]

        return "exploratory_learning"  # Default fallback


class AdaptiveLearningController:
    """Dynamically adjusts the AI's learning strategies based on observed performance trends
    and task context to optimize the learning process.
    """

    def __init__(self):
        logger.info("AdaptiveLearningController initialized.")
        self.performance_tracker = PerformanceTracker()
        self.strategy_selector = StrategySelector()
        self.available_strategies: dict[str, dict[str, Any]] = {
            "exploratory_learning": {
                "params": {"learning_rate": 0.01, "exploration_rate": 0.3},
                "effectiveness": 0.7,
            },
            "refinement_learning": {
                "params": {"learning_rate": 0.001, "exploration_rate": 0.1},
                "effectiveness": 0.85,
            },
            "meta_learning": {
                "params": {"learning_rate": 0.005, "exploration_rate": 0.2},
                "effectiveness": 0.6,
            },
        }

    def add_evaluation_result(self, evaluation: dict[str, Any]):
        """Adds a task evaluation result to the performance tracker."""
        self.performance_tracker.add_evaluation_result(evaluation)

    async def adapt_learning_strategy(
        self,
        task_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyzes current performance and task context to select and optimize a learning strategy."""
        logger.info("Adapting learning strategy...")
        performance_trends = self.performance_tracker.get_performance_trends()

        selected_strategy_name = self.strategy_selector.select_strategy(
            performance_trends,
            self.available_strategies,
        )
        selected_strategy = self.available_strategies.get(selected_strategy_name, {})

        # Optimize learning parameters
        optimized_params = self._optimize_learning_parameters(
            selected_strategy.get("params", {}),
            task_context,
            performance_trends,
        )

        adaptation_result = {
            "selected_strategy": selected_strategy_name,
            "optimized_parameters": optimized_params,
            "current_performance_trends": performance_trends,
        }
        logger.info(f"Learning strategy adapted: {adaptation_result}")
        return adaptation_result

    def update_strategy_effectiveness(
        self,
        strategy_name: str,
        outcome: str,
        performance_delta: float,
    ):
        """Updates the effectiveness metric of a given learning strategy based on its outcome.
        If a strategy consistently performs poorly, it's logged for review.
        """
        logger.info(
            f"Updating effectiveness for strategy '{strategy_name}' with outcome '{outcome}' and delta {performance_delta}.",
        )
        if strategy_name in self.available_strategies:
            current_effectiveness = self.available_strategies[strategy_name].get(
                "effectiveness",
                0.0,
            )

            # Simple update rule (placeholder)
            if outcome == "success":
                self.available_strategies[strategy_name]["effectiveness"] = min(
                    1.0,
                    current_effectiveness + performance_delta,
                )
            elif outcome == "failure":
                self.available_strategies[strategy_name]["effectiveness"] = max(
                    0.0,
                    current_effectiveness - performance_delta,
                )

            logger.debug(
                f"New effectiveness for {strategy_name}: {self.available_strategies[strategy_name]['effectiveness']}",
            )

            if self.available_strategies[strategy_name]["effectiveness"] < 0.5:
                self._log_strategy_for_improvement(
                    strategy_name,
                    self.available_strategies[strategy_name],
                )
        else:
            logger.warning(f"Attempted to update unknown strategy: {strategy_name}")

    def _optimize_learning_parameters(
        self,
        base_params: dict[str, Any],
        task_context: dict[str, Any],
        performance_trends: dict[str, Any],
    ) -> dict[str, Any]:
        """Optimizes learning parameters based on context and performance trends."""
        optimized_params = base_params.copy()

        # Adjust exploration based on performance trend and difficulty
        if performance_trends.get(
            "trend",
        ) == "declining" or "novel_situations" in performance_trends.get(
            "areas_of_difficulty",
            [],
        ):
            optimized_params["exploration_rate"] = min(
                0.5,
                optimized_params.get("exploration_rate", 0.2) * 1.5,
            )
            optimized_params["learning_rate"] = max(
                0.005,
                optimized_params.get("learning_rate", 0.01) * 1.2,
            )  # Increase learning rate for exploration
        elif (
            performance_trends.get("trend") == "improving"
            and task_context.get("complexity") == "low"
        ):
            optimized_params["exploration_rate"] = max(
                0.05,
                optimized_params.get("exploration_rate", 0.2) * 0.8,
            )
            optimized_params["learning_rate"] = min(
                0.001,
                optimized_params.get("learning_rate", 0.01) * 0.9,
            )  # Refine learning rate

        # Further adjustments based on task complexity
        if task_context.get("complexity") == "high":
            optimized_params["learning_rate"] = max(
                0.001,
                optimized_params.get("learning_rate", 0.01) * 0.9,
            )  # Slower learning for complex tasks
            optimized_params["exploration_rate"] = min(
                0.4,
                optimized_params.get("exploration_rate", 0.2) * 1.1,
            )  # More exploration for complex tasks

        return optimized_params

    def _log_strategy_for_improvement(
        self,
        strategy_name: str,
        strategy_details: dict[str, Any],
    ):
        """Logs strategies that require improvement to a JSONL file."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "strategy_name": strategy_name,
            "details": strategy_details,
            "reason": "Effectiveness below threshold",
        }
        try:
            with open(STRATEGY_IMPROVEMENT_LOG_FILE, "a", encoding="utf-8") as f:
                json.dump(log_entry, f)
                f.write("\n")
            logger.warning(f"Strategy '{strategy_name}' logged for improvement.")
        except Exception as e:
            logger.error(
                f"Failed to log strategy improvement for '{strategy_name}': {e}",
            )

    def get_available_strategies(self) -> dict[str, dict[str, Any]]:
        """Returns the dictionary of available learning strategies."""
        return self.available_strategies
