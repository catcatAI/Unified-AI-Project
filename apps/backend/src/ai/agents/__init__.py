"""
AI Agents Module
Contains base agent classes and specialized agent implementations.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

# =============================================================================
# DEPRECATED: This subpackage has no production consumers.
# Retained for reference — not wired into the running system.
# See MASTER_CONSOLIDATED_PLAN.md § Phase 4 Priority 2.
# =============================================================================

from .base.base_agent import BaseAgent
from .specialized.creative_writing_agent import CreativeWritingAgent
from .specialized.web_search_agent import WebSearchAgent
from .agent_manager import AgentManager
from .agent_collaboration_manager import AgentCollaborationManager
from .agent_monitoring_manager import AgentMonitoringManager
from .dynamic_agent_registry import DynamicAgentRegistry
import logging

logger = logging.getLogger(__name__)

__all__ = [
    "BaseAgent",
    "CreativeWritingAgent",
    "WebSearchAgent",
    "AgentManager",
    "AgentCollaborationManager",
    "AgentMonitoringManager",
    "DynamicAgentRegistry",
]
