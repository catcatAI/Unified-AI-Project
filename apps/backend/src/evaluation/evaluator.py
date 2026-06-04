import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Evaluator:
    """
    A class for evaluating models and tools.
    """

    def __init__(self) -> None:
        self.metrics: Dict[str, Callable[..., float]] = {
            "accuracy": self._calculate_accuracy,
            "performance": self._calculate_performance,
            "robustness": self._calculate_robustness,
        }
        logger.debug(f"{type(self).__name__}.__init__ completed")

    def register_metric(self, name: str, metric_func: Callable[..., float]) -> None:
        self.metrics[name] = metric_func

    def get_score(self, results: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Return structured evaluation with weighted composite score."""
        weights = weights or {k: 1.0 / max(1, len(results)) for k in results}
        composite = sum(v * weights.get(k, 0.0) for k, v in results.items())
        total_w = sum(weights.get(k, 0.0) for k in results)
        composite = composite / total_w if total_w > 0 else 0.0
        return {
            "metrics": results,
            "weights": weights,
            "composite_score": round(composite, 4),
            "passed": all(v >= 0.5 for v in results.values()),
        }

    def evaluate(
        self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]],
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Evaluates a model or tool on a dataset.

        Args:
            model_or_tool: The model or tool to be evaluated. It must have an 'evaluate' method.
            dataset: An iterable of (input, expected_output) tuples.
            metric_names: Optional subset of metrics to compute (default: all).

        Returns:
            A dictionary of evaluation metrics.
        """
        names = metric_names or list(self.metrics.keys())
        results = {}
        for name in names:
            func = self.metrics.get(name)
            if func is None:
                logger.warning(f"Metric '{name}' not registered, skipping")
                continue
            try:
                results[name] = func(model_or_tool, dataset)
            except Exception as e:
                logger.error(f"Metric '{name}' failed: {e}", exc_info=True)
                results[name] = 0.0
        return results

    def _calculate_accuracy(self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]) -> float:
        correct = 0
        dataset_list = list(dataset)
        if not dataset_list:
            return 0.0

        for input_data, expected_output in dataset_list:
            output = model_or_tool.evaluate(input_data)
            if output == expected_output:
                correct += 1

        return correct / len(dataset_list)

    def _calculate_performance(
        self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]
    ) -> float:
        dataset_list = list(dataset)
        if not dataset_list:
            return 0.0

        start_time = time.time()
        for input_data, _ in dataset_list:
            model_or_tool.evaluate(input_data)
        end_time = time.time()
        return end_time - start_time

    def _calculate_robustness(
        self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]
    ) -> float:
        no_exception = 0
        dataset_list = list(dataset)
        if not dataset_list:
            return 0.0

        for input_data, _ in dataset_list:
            try:
                model_or_tool.evaluate(input_data)
                no_exception += 1
            except Exception as e:
                logger.error(f"Error in {__name__}: {e}", exc_info=True)

        return no_exception / len(dataset_list)
