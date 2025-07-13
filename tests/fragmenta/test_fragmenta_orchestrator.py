import unittest
from unittest.mock import MagicMock
from src.fragmenta.fragmenta_orchestrator import FragmentaOrchestrator
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager

class TestFragmentaOrchestrator(unittest.TestCase):
    def test_process_complex_task(self):
        ham_manager = MagicMock(spec=HAMMemoryManager)
        orchestrator = FragmentaOrchestrator(ham_manager)

        task_description = {
            "query_params": {
                "keywords": ["test"],
                "limit": 5
            }
        }
        input_data = "This is a test input."

        orchestrator.process_complex_task(task_description, input_data)

        ham_manager.query_core_memory.assert_called_once_with(
            return_multiple_candidates=True,
            keywords=["test"],
            limit=5
        )

if __name__ == '__main__':
    unittest.main()
