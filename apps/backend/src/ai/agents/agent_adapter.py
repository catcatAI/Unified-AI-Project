"""

Agent Adapter — bridges specialized agents to AgentManager's execute() interface.

Specialized agents expose domain-specific methods (analyze_code, search, etc.)
but AgentManager.execute_agent() expects agent.execute(task). This adapter
wraps any specialized agent and routes task dicts to the correct method.
"""

import inspect
import logging
from typing import Any, Dict, Optional

from core.utils import safe_error

# =============================================================================
# ANGELA-MATRIX: [L6] [βδ] [A] [L4]
# =============================================================================


logger = logging.getLogger(__name__)


class AgentAdapter:
    """
    Wraps a specialized agent and exposes a generic execute(task) interface.

    Task dict format:
        {"method": "analyze_code", "args": {...}}  — calls agent.analyze_code(**args)
        {"args": {"query": "..."}}  — auto-detects method, maps args
        {} — uses primary method with empty args
    """

    # Map agent class name patterns → (primary method, fallback method)
    _METHOD_MAP: Dict[str, tuple] = {
        "CreativeWriting": ("generate_story", "generate_poem"),
        "ImageGeneration": ("generate_image", None),
        "WebSearch": ("search", None),
        "CodeUnderstanding": ("analyze_code", "explain_code"),
        "DataAnalysis": ("analyze_dataset", "generate_report"),
        "VisionProcessing": ("analyze_image", "detect_objects"),
        "AudioProcessing": ("transcribe_audio", "analyze_audio"),
        "KnowledgeGraph": ("query_graph", "add_entity"),
        "NLPProcessing": ("analyze_sentiment", "summarize_text"),
        "Planning": ("create_plan", None),
        "FantasyDM": ("generate_scenario", "create_character"),
    }

    def __init__(self, agent: Any, agent_id: Optional[str] = None):
        self.agent = agent
        self.agent_id = agent_id or getattr(agent, "agent_id", agent.__class__.__name__)
        self.agent_name = getattr(agent, "agent_name", self.agent_id)
        self._primary_method, self._fallback_method = self._detect_methods()

    def _detect_methods(self) -> tuple:
        """Detect primary and fallback methods based on agent class name."""
        class_name = self.agent.__class__.__name__
        for pattern, (primary, fallback) in self._METHOD_MAP.items():
            if pattern in class_name:
                has_primary = hasattr(self.agent, primary) if primary else False
                has_fallback = hasattr(self.agent, fallback) if fallback else False
                if has_primary:
                    return primary, fallback
                if has_fallback:
                    return fallback, None
        # Fallback: try common method names
        for name in ("execute", "process", "run"):
            if hasattr(self.agent, name):
                return name, None
        return None, None

    def _fill_defaults(self, method, args: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect method signature and fill defaults for missing required params."""
        try:
            sig = inspect.signature(method)
        except (ValueError, TypeError):
            return args

        filled = dict(args)
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param_name not in filled:
                if param.default is not inspect.Parameter.empty:
                    continue  # Has default, skip
                # Fill required params with sensible defaults
                if "sender_ai_id" in param_name:
                    filled[param_name] = "adapter"
                elif "envelope" in param_name:
                    filled[param_name] = None
                elif "language" in param_name:
                    filled[param_name] = "python"
                elif "text" in param_name:
                    filled[param_name] = ""
                elif "query" in param_name:
                    filled[param_name] = ""
                elif "data" in param_name:
                    filled[param_name] = []
                elif "prompt" in param_name:
                    filled[param_name] = ""
                elif "theme" in param_name:
                    filled[param_name] = "general"
                elif "goal" in param_name:
                    filled[param_name] = "unknown"
                elif "entity" in param_name:
                    filled[param_name] = ""
                elif "audio_path" in param_name or "image_path" in param_name:
                    filled[param_name] = ""
                elif "content" in param_name:
                    filled[param_name] = ""
                else:
                    filled[param_name] = None
        return filled

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
            return {
                "status": "error",
                "error": "No method specified and no primary method detected",
            }

        if not hasattr(self.agent, method_name):
            # Try fallback
            if self._fallback_method and hasattr(self.agent, self._fallback_method):
                method_name = self._fallback_method
            else:
                logger.warning(
                    f"[AgentAdapter] Agent {self.agent_id} has no method '{method_name}'"
                )
                return {"status": "error", "error": f"Method '{method_name}' not found on agent"}

        method = getattr(self.agent, method_name)
        filled_args = self._fill_defaults(method, args)

        try:
            if inspect.iscoroutinefunction(method):
                result = await method(**filled_args) if filled_args else await method()
            else:
                result = method(**filled_args) if filled_args else method()
            return result
        except TypeError as e:
            logger.debug(f"[AgentAdapter] Args mismatch for {method_name}: {e}")
            return {"status": "error", "error": f"Method signature mismatch: {e}"}
        except Exception as e:
            logger.error(f"[AgentAdapter] Failed to execute {method_name}: {e}", exc_info=True)
            return {"status": "error", "error": safe_error(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get adapter and underlying agent status."""
        status = {
            "agent_id": self.agent_id,
            "agent_class": self.agent.__class__.__name__,
            "primary_method": self._primary_method,
            "available_methods": [
                m
                for m in dir(self.agent)
                if not m.startswith("_") and callable(getattr(self.agent, m))
            ],
        }
        if hasattr(self.agent, "get_status"):
            status["agent_status"] = self.agent.get_status()
        return status


# --- Agent ID → class mapping ---
_AGENT_CLASSES: Dict[str, str] = {
    "creative_writing_agent": (
        "ai.agents.specialized.creative_writing_agent",
        "CreativeWritingAgent",
    ),
    "web_search_agent": ("ai.agents.specialized.web_search_agent", "WebSearchAgent"),
    "code_understanding_agent": (
        "ai.agents.specialized.code_understanding_agent",
        "CodeUnderstandingAgent",
    ),
    "data_analysis_agent": ("ai.agents.specialized.data_analysis_agent", "DataAnalysisAgent"),
    "vision_processing_agent": (
        "ai.agents.specialized.vision_processing_agent",
        "VisionProcessingAgent",
    ),
    "audio_processing_agent": (
        "ai.agents.specialized.audio_processing_agent",
        "AudioProcessingAgent",
    ),
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
