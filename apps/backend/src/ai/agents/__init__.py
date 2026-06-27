"""
AI Agents Module
Contains base agent classes and specialized agent implementations.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging

from .agent_collaboration_manager import AgentCollaborationManager
from .agent_manager import AgentManager
from .agent_monitoring_manager import AgentMonitoringManager
from .base.base_agent import BaseAgent
from .dynamic_agent_registry import DynamicAgentRegistry
from .specialized.creative_writing_agent import CreativeWritingAgent
from .specialized.web_search_agent import WebSearchAgent

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
