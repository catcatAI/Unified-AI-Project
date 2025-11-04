import time
from typing import Any, Dict, Iterable, Tuple

class Evaluator:
    """
    A class for evaluating models and tools.
    """

    def __init__(self) -> None:
        pass

    def evaluate(self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]) -> Dict[str, float]:
        """
        Evaluates a model or tool on a dataset.

        Args:
            model_or_tool: The model or tool to be evaluated. It must have an 'evaluate' method.
            dataset: An iterable of (input, expected_output) tuples.

        Returns:
            A dictionary of evaluation metrics.
        """
        accuracy = self._calculate_accuracy(model_or_tool, dataset)
        performance = self._calculate_performance(model_or_tool, dataset)
        robustness = self._calculate_robustness(model_or_tool, dataset)

        return {
            "accuracy": accuracy,
            "performance": performance,
            "robustness": robustness,
        }

    def _calculate_accuracy(self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]) -> float:
        """
        Calculates the accuracy of a model or tool on a dataset.
        """
        correct = 0
        dataset_list = list(dataset)
        if not dataset_list:
            return 0.0

        for input_data, expected_output in dataset_list:
            output = model_or_tool.evaluate(input_data)
            print(f"Input: {input_data}, Output: {output}, Expected: {expected_output}")
            if output == expected_output:
                correct += 1
        
        return correct / len(dataset_list)

    def _calculate_performance(self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]) -> float:
        """
        Calculates the performance (execution time) of a model or tool on a dataset.
        """
        dataset_list = list(dataset)
        if not dataset_list:
            return 0.0

        start_time = time.time()
        for input_data, _ in dataset_list:
            model_or_tool.evaluate(input_data)
        end_time = time.time()
        return end_time - start_time

    def _calculate_robustness(self, model_or_tool: Any, dataset: Iterable[Tuple[Any, Any]]) -> float:
        """
        Calculates the robustness of a model or tool on a dataset.
        """
        no_exception = 0
        dataset_list = list(dataset)
        if not dataset_list:
            return 0.0

        for input_data, _ in dataset_list:
            try:
                model_or_tool.evaluate(input_data)
                no_exception += 1
            except Exception:
                pass
        
        return no_exception / len(dataset_list)