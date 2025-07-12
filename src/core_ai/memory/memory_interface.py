import abc
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from src.shared.types.common_types import DialogueMemoryEntryMetadata, HAMRecallResult

class AbstractMemoryManager(abc.ABC):
    """
    Abstract Base Class for Memory Managers.
    Defines the core interface for storing, recalling, and querying experiences.
    """

    @abc.abstractmethod
    def store_experience(self, raw_data: Any, data_type: str, metadata: Optional[DialogueMemoryEntryMetadata] = None) -> Optional[str]:
        """
        Stores a new experience into the memory.

        Args:
            raw_data: The raw data of the experience (e.g., text string, dict).
            data_type (str): Type of the data (e.g., "dialogue_text", "sensor_reading").
            metadata (Optional[DialogueMemoryEntryMetadata]): Additional metadata for the experience.

        Returns:
            Optional[str]: The generated memory ID if successful, otherwise None.
        """
        pass

    @abc.abstractmethod
    def recall_gist(self, memory_id: str) -> Optional[HAMRecallResult]:
        """
        Recalls an abstracted gist of an experience by its memory ID.

        Args:
            memory_id (str): The ID of the memory to recall.

        Returns:
            Optional[HAMRecallResult]: A HAMRecallResult object if successful,
                                       None if recall fails at any stage.
        """
        pass

    @abc.abstractmethod
    def query_core_memory(
                          self,
                          keywords: Optional[List[str]] = None,
                          date_range: Optional[Tuple[datetime, datetime]] = None,
                          data_type_filter: Optional[str] = None,
                          metadata_filters: Optional[Dict[str, Any]] = None,
                          user_id_for_facts: Optional[str] = None,
                          limit: int = 5,
                          sort_by_confidence: bool = False
                          ) -> List[HAMRecallResult]:
        """
        Queries the stored memories based on various filters.

        Args:
            keywords (Optional[List[str]]): Keywords to search for.
            date_range (Optional[Tuple[datetime, datetime]]): Date range to filter memories.
            data_type_filter (Optional[str]): Filter by data type.
            metadata_filters (Optional[Dict[str, Any]]): Filter by exact metadata matches.
            user_id_for_facts (Optional[str]): User ID to filter facts.
            limit (int): Maximum number of results to return.
            sort_by_confidence (bool): Whether to sort results by confidence score.

        Returns:
            List[HAMRecallResult]: A list of HAMRecallResult objects.
        """
        pass