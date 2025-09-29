import unittest
import pytest
from apps.backend.src.core_ai.lis.tonal_repair_engine import TonalRepairEngine

class TestTonalRepairEngine(unittest.TestCase):
    @pytest.mark.timeout(5)
    def test_repair_output(self) -> None:
        engine = TonalRepairEngine()
        original_text = "This is a test."
        issues = ["This is a test issue."]
        repaired_text = engine.repair_output(original_text, issues)
        self.assertEqual(repaired_text, f"Repaired: {original_text}")

if __name__ == '__main__':
    unittest.main()
