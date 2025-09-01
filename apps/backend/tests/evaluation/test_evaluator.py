import unittest
import pytest
from apps.backend.src.evaluation.evaluator import Evaluator

class TestEvaluator(unittest.TestCase):
    """
    A class for testing the Evaluator class.
    """

    @pytest.mark.timeout(5)
    def test_evaluate(self):
        """
        Tests the evaluate method.
        """
        evaluator = Evaluator()

        class DummyModel:
            def evaluate(self, input):
                return input

        model = DummyModel()
        dataset = [(1, 1), (2, 2), (3, 3), (4, 5)]
        evaluation = evaluator.evaluate(model, dataset)

        self.assertEqual(evaluation["accuracy"], 0.75)
        self.assertGreaterEqual(evaluation["performance"], 0)
        self.assertEqual(evaluation["robustness"], 1.0)

if __name__ == "__main__":
    unittest.main()
