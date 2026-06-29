# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
Memory module — HAM memory, vector store, template library, precompute.

P15: VectorMemoryStore (chromadb/numpy dual-backend persistence).
P16: HAMMemoryManager (human associative memory with decay/consolidation).
P22: MathRippleEngine (formula computation with operator precedence).
P24: PrecomputeService + TaskGenerator (background task scheduling).
"""

try:
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager
    from ai.memory.ham_memory.ham_query_engine import HAMQueryEngine
    from ai.memory.ham_memory.ham_core_storage import HAMCoreStorage
    from ai.memory.ham_memory.ham_data_processor import HAMDataProcessor
    from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer
    from ai.memory.ham_memory.ham_background_tasks import HAMBackgroundTasks
    from ai.memory.ham_memory.ham_vector_store_manager import HAMVectorStoreManager
    from ai.memory.ham_memory.ham_errors import HAMMemoryError, HAMInitializationError, HAMStorageError, HAMRetrievalError
except ImportError:
    import logging
    logging.getLogger(__name__).warning("ham_memory subpackage not available — some memory features disabled")
from ai.memory.ham_utils import calculate_cosine_similarity, generate_embedding
from ai.memory.memory_template import MemoryTemplate, ResponseCategory, UserImpression
from ai.memory.template_library import TemplateLibrary, PredefinedTemplate, get_template_library
from ai.memory.memory_learning import MemoryLearningEngine
from ai.memory.vector_store import VectorMemoryStore
from ai.memory.precompute_service import PrecomputeService, PrecomputeTask
from ai.memory.task_generator import TaskGenerator
from ai.memory.math_ripple_engine import MathRippleEngine
from ai.memory.types import MemoryType

__all__ = [
    "HAMMemoryManager",
    "HAMQueryEngine",
    "HAMCoreStorage",
    "HAMDataProcessor",
    "ImportanceScorer",
    "HAMBackgroundTasks",
    "HAMVectorStoreManager",
    "HAMMemoryError",
    "HAMInitializationError",
    "HAMStorageError",
    "HAMRetrievalError",
    "calculate_cosine_similarity",
    "generate_embedding",
    "MemoryTemplate",
    "ResponseCategory",
    "UserImpression",
    "TemplateLibrary",
    "PredefinedTemplate",
    "get_template_library",
    "MemoryLearningEngine",
    "VectorMemoryStore",
    "PrecomputeService",
    "PrecomputeTask",
    "TaskGenerator",
    "MathRippleEngine",
    "MemoryType",
]
