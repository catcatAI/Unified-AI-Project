"""
Angela AI v6.0 - Explicit/Implicit Learning System
显性/隐性学习系统

Distinguishes between explicit (conscious, declarative) and
implicit (unconscious, procedural) learning with different
consolidation patterns.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class LearningEvent:
    """学习事件 / Learning event for explicit/implicit tracking"""

    event_id: str
    content: Any
    learning_type: str  # "explicit" or "implicit"
    context: str
    timestamp: datetime = field(default_factory=datetime.now)
    consolidation_level: float = 0.0


class ExplicitImplicitLearning:
    """
    显性/隐性学习系统 / Explicit and Implicit Learning System

    Distinguishes between:
    - Explicit learning: Conscious, declarative, factual
    - Implicit learning: Unconscious, procedural, skill-based

    Different consolidation patterns:
    - Explicit: Fast encoding, vulnerable to interference
    - Implicit: Slow encoding, resistant to interference

    Example:
        >>> learning = ExplicitImplicitLearning()
        >>>
        >>> # Explicit learning (facts, conscious)
        >>> learning.learn_explicit(
        ...     event_id="fact_001",
        ...     content="Paris is the capital of France",
        ...     context="study_session"
        ... )
        >>>
        >>> # Implicit learning (skills, unconscious)
        >>> learning.learn_implicit(
        ...     event_id="skill_001",
        ...     content="riding_bike_procedural_memory",
        ...     context="practice_session"
        ... )
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # Learning storage
        self.explicit_memories: Dict[str, LearningEvent] = {}
        self.implicit_memories: Dict[str, LearningEvent] = {}

        # Consolidation parameters
        self.explicit_consolidation_rate: float = self.config.get("explicit_rate", 0.3)
        self.implicit_consolidation_rate: float = self.config.get("implicit_rate", 0.1)
        self.explicit_interference: float = self.config.get("explicit_interference", 0.4)

    def learn_explicit(
        self, event_id: str, content: Any, context: str, timestamp: Optional[datetime] = None
    ) -> LearningEvent:
        """
        显性学习 / Explicit (conscious) learning

        Fast encoding but vulnerable to interference.
        """
        event = LearningEvent(
            event_id=event_id,
            content=content,
            learning_type="explicit",
            context=context,
            timestamp=timestamp or datetime.now(),
            consolidation_level=0.2,  # Starts low, consolidates quickly
        )

        self.explicit_memories[event_id] = event

        # Apply interference to other explicit memories
        self._apply_interference(event_id)

        return event

    def learn_implicit(
        self, event_id: str, content: Any, context: str, timestamp: Optional[datetime] = None
    ) -> LearningEvent:
        """
        隐性学习 / Implicit (unconscious) learning

        Slow encoding but resistant to interference.
        """
        event = LearningEvent(
            event_id=event_id,
            content=content,
            learning_type="implicit",
            context=context,
            timestamp=timestamp or datetime.now(),
            consolidation_level=0.1,  # Starts lower, consolidates slowly
        )

        self.implicit_memories[event_id] = event

        return event

    def _apply_interference(self, new_event_id: str) -> None:
        """应用干扰 / Apply interference to existing explicit memories"""
        self.explicit_memories[new_event_id]

        for event_id, event in self.explicit_memories.items():
            if event_id != new_event_id:
                # Reduce consolidation level due to interference
                event.consolidation_level = max(
                    0.0, event.consolidation_level - self.explicit_interference * 0.1
                )

    def consolidate(self, hours_elapsed: float = 1.0) -> None:
        """
        巩固学习记忆 / Consolidate learning memories

        Different rates for explicit vs implicit.
        """
        # Consolidate explicit memories (faster)
        for event in self.explicit_memories.values():
            consolidation_increase = self.explicit_consolidation_rate * hours_elapsed / 24.0
            event.consolidation_level = min(1.0, event.consolidation_level + consolidation_increase)

        # Consolidate implicit memories (slower but more stable)
        for event in self.implicit_memories.values():
            consolidation_increase = self.implicit_consolidation_rate * hours_elapsed / 24.0
            event.consolidation_level = min(1.0, event.consolidation_level + consolidation_increase)

    def get_explicit_memory(self, event_id: str) -> Optional[LearningEvent]:
        """获取显性记忆 / Get explicit memory"""
        return self.explicit_memories.get(event_id)

    def get_implicit_memory(self, event_id: str) -> Optional[LearningEvent]:
        """获取隐性记忆 / Get implicit memory"""
        return self.implicit_memories.get(event_id)

    def get_consolidation_stats(self) -> Dict[str, Any]:
        """获取巩固统计 / Get consolidation statistics"""
        explicit_consolidated = sum(
            1 for e in self.explicit_memories.values() if e.consolidation_level > 0.7
        )
        implicit_consolidated = sum(
            1 for e in self.implicit_memories.values() if e.consolidation_level > 0.7
        )

        return {
            "explicit_count": len(self.explicit_memories),
            "explicit_consolidated": explicit_consolidated,
            "implicit_count": len(self.implicit_memories),
            "implicit_consolidated": implicit_consolidated,
            "avg_explicit_consolidation": (
                sum(e.consolidation_level for e in self.explicit_memories.values())
                / len(self.explicit_memories)
                if self.explicit_memories
                else 0.0
            ),
            "avg_implicit_consolidation": (
                sum(e.consolidation_level for e in self.implicit_memories.values())
                / len(self.implicit_memories)
                if self.implicit_memories
                else 0.0
            ),
        }
