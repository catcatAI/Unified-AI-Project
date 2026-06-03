from typing import Any, Dict, List, Optional, Callable
import logging
from ai.memory.ham_memory.ham_manager import HAMMemoryManager

logger = logging.getLogger(__name__)


class FragmentaOrchestrator:
    """Orchestrates complex tasks using memory fragments from HAM."""

    def __init__(self, ham_manager: HAMMemoryManager):
        """Initializes the FragmentaOrchestrator with a HAMMemoryManager instance."""
        self.ham_manager = ham_manager
        self.processors: Dict[str, Callable[[Dict[str, Any], Any], Dict[str, Any]]] = {}

    def register_processor(
        self, fragment_type: str, processor: Callable[[Dict[str, Any], Any], Dict[str, Any]]
    ) -> None:
        """
        Registers a fragment processor for a given fragment type.

        Args:
            fragment_type: The type of fragment this processor handles.
            processor: A callable that accepts (fragment_data, context) and returns processed result.
        """
        self.processors[fragment_type] = processor
        logger.info(f"Processor registered for fragment type '{fragment_type}'")

    def process_complex_task(
        self, task_description: Dict[str, Any], input_data: Any
    ) -> Dict[str, Any]:
        """
        Processes a complex task by retrieving multiple candidate memories,
        routing each fragment through its registered processor, and collecting results.
        """
        query_params = task_description.get("query_params", {})
        fragment_type = task_description.get("fragment_type", "default")

        candidate_memories = self.ham_manager.query_core_memory(
            return_multiple_candidates=True, **query_params
        )

        processed_results: List[Dict[str, Any]] = []
        for memory in candidate_memories:
            processor = self.processors.get(fragment_type)
            if processor:
                result = processor(memory, input_data)
                processed_results.append(result)
            else:
                gist = memory.get("rehydrated_gist", "")
                words = gist.split()
                summary = " ".join(words[:10]) + "..." if len(words) > 10 else gist
                processed_results.append({"memory_id": memory.get("id"), "summary": summary})

        return {"status": "success", "processed_results": processed_results}
