"""
Angela AI 生命循環系統

這個模塊包含Angela的核心生命循環，讓她真正"活著"：
- LLM決策循環：持續的AI決策機制
- 主動交互系統：主動觸發用戶交互
- 用戶監控系統：檢測用戶狀態和情緒
- 行為反饋循環：行為效果評估和優化
- 記憶整合循環：主動記憶結構化
"""

from .llm_decision_loop import LLMDecisionLoop
from .proactive_interaction_system import ProactiveInteractionSystem
from .user_monitor import UserMonitor, UserState
from .behavior_feedback_loop import BehaviorFeedbackLoop
from .memory_integration_loop import MemoryIntegrationLoop

__all__ = [
    'LLMDecisionLoop',
    'ProactiveInteractionSystem',
    'UserMonitor',
    'UserState',
    'BehaviorFeedbackLoop',
    'MemoryIntegrationLoop',
]