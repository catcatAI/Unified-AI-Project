"""
Agent Adapter — bridges specialized agents to AgentManager's execute() interface.

Specialized agents expose domain-specific methods (analyze_code, search, etc.)
but AgentManager.execute_agent() expects agent.execute(task). This adapter
wraps any specialized agent and routes task dicts to the correct method.
"""

# =============================================================================
# ANGELA-MATRIX: [L6] [βδ] [A] [L4]
# =============================================================================

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AgentAdapter:
    """
    Wraps a specialized agent and exposes a generic execute(task) interface.

    Task dict format:
        {"method": "analyze_code", "args": {...}}  — calls agent.analyze_code(**args)
        {"method": "search", "args": {"query": "..."}}  — calls agent.search(query="...")
        {"method": "handle_task_request", "args": {...}}
        {} or {"method": "auto"} — auto-detects the primary method
    """

    # Map agent class name patterns → primary method name
    _METHOD_MAP: Dict[str, str] = {
        "CreativeWriting": "generate_creative_content",
        "ImageGeneration": "generate_image",
        "WebSearch": "search",
        "CodeUnderstanding": "analyze_code",
        "DataAnalysis": "analyze_data",
        "VisionProcessing": "analyze_image",
        "AudioProcessing": "process_audio",
        "KnowledgeGraph": "add_knowledge",
        "NLPProcessing": "analyze_sentiment",
        "Planning": "create_plan",
        "FantasyDM": "generate_scenario",
    }

    def __init__(self, agent: Any, agent_id: Optional[str] = None):
        self.agent = agent
        self.agent_id = agent_id or getattr(agent, "agent_id", agent.__class__.__name__)
        self.agent_name = getattr(agent, "agent_name", self.agent_id)
        self._primary_method = self._detect_primary_method()

    def _detect_primary_method(self) -> Optional[str]:
        """Detect the primary method based on agent class name."""
        class_name = self.agent.__class__.__name__
        for pattern, method_name in self._METHOD_MAP.items():
            if pattern in class_name:
                if hasattr(self.agent, method_name):
                    return method_name
        # Fallback: try common method names
        for fallback in ("execute", "process", "handle_task_request", "run"):
            if hasattr(self.agent, fallback):
                return fallback
        return None

    async def execute(self, task: Dict[str, Any]) -> Any:
        """
        Execute a task by routing to the appropriate agent method.

        Args:
            task: Dict with optional "method" and "args" keys.

        Returns:
            Result from the delegated agent method.
        """
        method_name = task.get("method", self._primary_method)
        args = task.get("args", {})

        if not method_name:
            logger.warning(f"[AgentAdapter] No method found for agent {self.agent_id}")
            return {"status": "error", "error": "No method specified and no primary method detected"}

        if not hasattr(self.agent, method_name):
            logger.warning(f"[AgentAdapter] Agent {self.agent_id} has no method '{method_name}'")
            return {"status": "error", "error": f"Method '{method_name}' not found on agent"}

        try:
            method = getattr(self.agent, method_name)
            import inspect
            if inspect.iscoroutinefunction(method):
                result = await method(**args) if args else await method()
            else:
                result = method(**args) if args else method()
            return result
        except TypeError as e:
            # If method signature doesn't match, try passing task directly
            logger.debug(f"[AgentAdapter] Args mismatch for {method_name}, trying positional: {e}")
            try:
                return await method(task) if inspect.iscoroutinefunction(method) else method(task)
            except Exception as e2:
                logger.error(f"[AgentAdapter] Failed to execute {method_name}: {e2}", exc_info=True)
                return {"status": "error", "error": str(e2)}
        except Exception as e:
            logger.error(f"[AgentAdapter] Failed to execute {method_name}: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get adapter and underlying agent status."""
        status = {
            "agent_id": self.agent_id,
            "agent_class": self.agent.__class__.__name__,
            "primary_method": self._primary_method,
            "available_methods": [
                m for m in dir(self.agent)
                if not m.startswith("_") and callable(getattr(self.agent, m))
            ],
        }
        if hasattr(self.agent, "get_status"):
            status["agent_status"] = self.agent.get_status()
        return status


# --- Agent ID → class mapping ---
_AGENT_CLASSES: Dict[str, str] = {
    "creative_writing_agent": ("ai.agents.specialized.creative_writing_agent", "CreativeWritingAgent"),
    "image_generation_agent": ("ai.agents.specialized.image_generation_agent", "ImageGenerationAgent"),
    "web_search_agent": ("ai.agents.specialized.web_search_agent", "WebSearchAgent"),
    "code_understanding_agent": ("ai.agents.specialized.code_understanding_agent", "CodeUnderstandingAgent"),
    "data_analysis_agent": ("ai.agents.specialized.data_analysis_agent", "DataAnalysisAgent"),
    "vision_processing_agent": ("ai.agents.specialized.vision_processing_agent", "VisionProcessingAgent"),
    "audio_processing_agent": ("ai.agents.specialized.audio_processing_agent", "AudioProcessingAgent"),
    "knowledge_graph_agent": ("ai.agents.specialized.knowledge_graph_agent", "KnowledgeGraphAgent"),
    "nlp_processing_agent": ("ai.agents.specialized.nlp_processing_agent", "NLPProcessingAgent"),
    "planning_agent": ("ai.agents.specialized.planning_agent", "PlanningAgent"),
    "fantasy_dm_agent": ("ai.agents.specialized.fantasy_dm_agent", "FantasyDMAgent"),
}


def register_specialized_agents(agent_manager: Any, state_manager: Any = None) -> int:
    """
    Import, instantiate, adapt, and register all specialized agents with AgentManager.

    Returns the number of agents successfully registered.
    """
    import importlib

    registered = 0
    for agent_id, (module_path, class_name) in _AGENT_CLASSES.items():
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            agent_instance = agent_class(agent_id=agent_id)
            adapter = AgentAdapter(agent_instance, agent_id=agent_id)
            agent_manager.agents[agent_id] = adapter
            registered += 1
            logger.info(f"[AgentAdapter] Registered: {agent_id} ({class_name})")
        except Exception as e:
            logger.warning(f"[AgentAdapter] Failed to register {agent_id}: {e}")

    if state_manager:
        agent_manager.set_state_manager(state_manager)

    logger.info(f"[AgentAdapter] Registered {registered}/{len(_AGENT_CLASSES)} specialized agents")
    return registered
