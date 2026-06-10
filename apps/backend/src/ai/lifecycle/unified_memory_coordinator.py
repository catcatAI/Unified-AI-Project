"""
Unified Memory Coordinator — C1: connect HAM + LU + CDM into a single query/storage flow.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class UnifiedMemoryCoordinator:
    """
    Thin adapter that coordinates query/storage across HAM, LU, and CDM.
    All storage is delegated to existing interfaces — zero data duplication.
    """

    def __init__(self, memory_manager=None, logic_unit=None, cdm_model=None):
        self.memory_manager = memory_manager  # HAMMemoryManager
        self.logic_unit = logic_unit          # LogicUnit
        self.cdm_model = cdm_model            # CDMCognitiveDividendModel
        logger.info(
            f"UnifiedMemoryCoordinator: HAM={memory_manager is not None}"
            f", LU={logic_unit is not None}, CDM={cdm_model is not None}"
        )

    async def unified_query(self, keywords: Optional[List[str]] = None,
                            context: Optional[Dict[str, Any]] = None,
                            limit: int = 10) -> Dict[str, Any]:
        """Query across HAM + LU + CDM and merge results."""
        result: Dict[str, Any] = {"memories": [], "rule_action": None, "cognitive_stats": {}}

        if self.memory_manager and keywords:
            result["memories"] = await self.memory_manager.query_core_memory(
                keywords=keywords, limit=limit
            )

        if self.logic_unit and context:
            result["rule_action"] = self.logic_unit.evaluate(context)

        if self.cdm_model:
            result["cognitive_stats"] = self.cdm_model.get_conversion_statistics()

        return result

    async def store_experience(self, raw_data: Any, data_type: str,
                               metadata: Optional[Dict[str, Any]] = None,
                               activity_type=None, duration: float = 0.0,
                               intensity: float = 0.5,
                               context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Store in HAM and (optionally) record CDM investment."""
        mem_id = None
        if self.memory_manager:
            mem_id = await self.memory_manager.store_experience(raw_data, data_type, metadata)
        if self.cdm_model and activity_type is not None:
            self.cdm_model.record_investment(activity_type, duration, intensity, context)
        return mem_id

    def evaluate_rules(self, context: Dict[str, Any]) -> Optional[str]:
        """Evaluate LU rules against current context."""
        if self.logic_unit:
            return self.logic_unit.evaluate(context)
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate status from all connected subsystems."""
        stats: Dict[str, Any] = {
            "ham": {"connected": self.memory_manager is not None},
            "lu": {"connected": self.logic_unit is not None},
            "cdm": {"connected": self.cdm_model is not None},
        }
        if self.logic_unit:
            stats["lu"]["rule_count"] = len(self.logic_unit.list_rules())
        if self.cdm_model:
            stats["cdm"]["stats"] = self.cdm_model.get_conversion_statistics()
        return stats
