class Evaluator:
    """
    A class for evaluating models and tools.
    """

    def __init__(self):
        pass

    def evaluate(self, model_or_tool, dataset):
        """
        Evaluates a model or tool on a dataset.

        Args:
            model_or_tool: The model or tool to be evaluated.
            dataset: The dataset to be used for evaluation.

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

    def _calculate_accuracy(self, model_or_tool, dataset):
        """
        Calculates the accuracy of a model or tool on a dataset.

        Args:
            model_or_tool: The model or tool to be evaluated.
            dataset: The dataset to be used for evaluation.

        Returns:
            The accuracy of the model or tool.
        """
        correct = 0
        for input, expected_output in dataset:
            output = model_or_tool.evaluate(input)
            if output == expected_output:
                correct += 1
        return correct / len(dataset)

    def _calculate_performance(self, model_or_tool, dataset):
        """
        Calculates the performance of a model or tool on a dataset.

        Args:
            model_or_tool: The model or tool to be evaluated.
            dataset: The dataset to be used for evaluation.

        Returns:
            The performance of the model or tool.
        """
        import time
        start_time = time.time()
        for input, _ in dataset:
            model_or_tool.evaluate(input)
        end_time = time.time()
        return end_time - start_time

    def _calculate_robustness(self, model_or_tool, dataset):
        """
        Calculates the robustness of a model or tool on a dataset.

        Args:
            model_or_tool: The model or tool to be evaluated.
            dataset: The dataset to be used for evaluation.

        Returns:
            The robustness of the model or tool.
        """
        no_exception = 0
        for input, _ in dataset:
            try:
                model_or_tool.evaluate(input)
                no_exception += 1
            except:
                pass
        return no_exception / len(dataset)
