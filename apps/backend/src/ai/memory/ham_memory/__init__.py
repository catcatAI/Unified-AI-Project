# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
HAM Memory subpackage — human associative memory implementation.

P16: Full HAM lifecycle: encoding → storage → consolidation → recall.
P17: Importance-based decay, background consolidation, vector store integration.
"""

from ai.memory.ham_memory.ham_background_tasks import HAMBackgroundTasks
from ai.memory.ham_memory.ham_core_storage import HAMCoreStorage
from ai.memory.ham_memory.ham_data_processor import HAMDataProcessor
from ai.memory.ham_memory.ham_errors import (
    HAMInitializationError,
    HAMMemoryError,
    HAMRetrievalError,
    HAMStorageError,
)
from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer
from ai.memory.ham_memory.ham_manager import HAMMemoryManager
from ai.memory.ham_memory.ham_query_engine import HAMQueryEngine
from ai.memory.ham_memory.ham_vector_store_manager import HAMVectorStoreManager

__all__ = [
    "HAMMemoryManager",
    "HAMCoreStorage",
    "HAMDataProcessor",
    "ImportanceScorer",
    "HAMBackgroundTasks",
    "HAMVectorStoreManager",
    "HAMQueryEngine",
    "HAMMemoryError",
    "HAMInitializationError",
    "HAMStorageError",
    "HAMRetrievalError",
]
