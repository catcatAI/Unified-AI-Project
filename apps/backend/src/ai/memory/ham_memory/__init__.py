# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
HAM Memory subpackage — human associative memory implementation.

P16: Full HAM lifecycle: encoding → storage → consolidation → recall.
P17: Importance-based decay, background consolidation, vector store integration.

WHAT IS HERE (2026-10-20)
-------------------------
``HAMMemoryManager`` (the live store: bucketed, capped, age/importance
pruned) and ``ImportanceScorer`` (wired into the chat service).

The parallel implementation — ``ham_query_engine`` / ``ham_data_processor`` /
``ham_core_storage`` / ``ham_background_tasks`` / ``ham_vector_store_manager``
/ ``ham_types`` / ``ham_errors`` — was removed: it had no consumer outside its
own package and its ``__init__`` exports, so the "encrypted core memory",
"background retention" and "vector-indexed recall" it advertised never ran.
The retention rules it contained now live in ``HAMMemoryManager.prune()``,
over the data the system actually stores.
"""

from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer
from ai.memory.ham_memory.ham_manager import HAMMemoryManager

__all__ = [
    "HAMMemoryManager",
    "ImportanceScorer",
]
