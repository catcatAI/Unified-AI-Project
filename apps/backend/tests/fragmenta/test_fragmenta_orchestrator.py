import unittest
import pytest
from unittest.mock import MagicMock
from apps.backend.src.fragmenta.fragmenta_orchestrator import FragmentaOrchestrator
from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager

class TestFragmentaOrchestrator(unittest.TestCase):
    _ = @pytest.mark.timeout(5)
    def test_process_complex_task(self) -> None:
        ham_manager = MagicMock(spec=HAMMemoryManager)
        orchestrator = FragmentaOrchestrator(ham_manager)

        task_description = {
            "query_params": {
                "keywords": ["test"],
                "limit": 5
            }
        }
        input_data = "This is a test input."

        _ = orchestrator.process_complex_task(task_description, input_data)

        ham_manager.query_core_memory.assert_called_once_with(
            return_multiple_candidates=True,
            keywords=["test"],
            limit=5
        )

if __name__ == '__main__':
    _ = unittest.main()
