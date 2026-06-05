# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HAMQueryEngine:
    """Query engine for HAM (Hierarchical Attention Memory) system.

    Provides query methods against memory stores with ranking and filtering.
    """

    def __init__(self, memory_manager: Any = None, config: Optional[Dict[str, Any]] = None):
        self.memory_manager = memory_manager
        self.config = config or {}

    def query(self, query_text: str, top_k: int = 10, threshold: float = 0.0) -> List[Dict[str, Any]]:
        if self.memory_manager and hasattr(self.memory_manager, "query"):
            return self.memory_manager.query(query_text, top_k=top_k, threshold=threshold)
        return []

    def retrieve_similar(self, embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        return []

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        return []

    def get_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        if self.memory_manager and hasattr(self.memory_manager, "get_memory"):
            return self.memory_manager.get_memory(memory_id)
        return None

    def clear_cache(self) -> None:
        logger.debug("HAMQueryEngine cache cleared")


__all__ = ["HAMQueryEngine"]
