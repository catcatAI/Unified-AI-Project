"""
ANGELA-MATRIX: [L4] [β] [B] [L0]
Card Import Pipeline — integration subpackage.
"""

from core.card.integration.memory_adapter import MemoryAdapter
from core.card.integration.personality_adapter import PersonalityAdapter

__all__ = [
    "MemoryAdapter",
    "PersonalityAdapter",
]
