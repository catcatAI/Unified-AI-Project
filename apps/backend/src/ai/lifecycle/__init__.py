"""
Angela AI 生命循環系統

這個模塊包含Angela的核心生命循環，讓她真正"活著"：
- LLM決策循環：持續的AI決策機制
- 主動交互系統：主動觸發用戶交互
- 用戶監控系統：檢測用戶狀態和情緒
- 統一記憶協調：跨記憶後端的協調
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

from .llm_decision_loop import LLMDecisionLoop
from .proactive_interaction_system import ProactiveInteractionSystem
from .unified_memory_coordinator import UnifiedMemoryCoordinator
from .user_monitor import UserMonitor, UserState

__all__ = [
    "LLMDecisionLoop",
    "ProactiveInteractionSystem",
    "UserMonitor",
    "UserState",
    "UnifiedMemoryCoordinator",
]
