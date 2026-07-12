# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from datetime import datetime
from typing import Any, Dict, TypedDict

# Re-export canonical HAMDataPackageInternal from ai.memory.types
from ai.memory.types import HAMDataPackageInternal  # noqa: F401

logger = logging.getLogger(__name__)


class HAMMemory(TypedDict):
    memory_id: str
    content: str
    metadata: Dict[str, Any]
    relevance: float


class HAMRecallResult(TypedDict):
    memory_id: str
    content: str
    score: float
    timestamp: datetime
    metadata: Dict[str, Any]


class HAMMemoryError(Exception):
    """Custom exception for HAM memory operations."""

