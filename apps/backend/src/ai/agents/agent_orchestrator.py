# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L3]
# =============================================================================

"""
Agent Orchestrator — Intelligent task routing and multi-agent collaboration.

Routes user intents to specialized agents based on capability matching,
decomposes complex tasks, and chains agent outputs.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Intent → capability mapping
_INTENT_CAPABILITIES: Dict[str, List[str]] = {
    "file_read": ["file_operations", "read_file"],
    "file_write": ["file_operations", "write_file"],
    "file_delete": ["file_operations", "delete_file"],
    "code_execute": ["code_execution", "run_code"],
    "code_understand": ["code_analysis", "explain_code"],
    "web_search": ["web_search", "search"],
    "knowledge_query": ["knowledge_graph", "query_graph"],
    "creative_write": ["creative_writing", "generate_text"],
    "data_analysis": ["data_analysis", "analyze_data"],
    "plan_create": ["planning", "create_plan"],
    "vision": ["vision_processing", "analyze_image"],
    "audio": ["audio_processing", "transcribe"],
    "nlp": ["nlp_processing", "sentiment_analysis"],
    "image_generate": ["image_generation", "generate_image"],
}

# Intent → agent mapping.
# Handler-backed intents map to the registered ModelBus handler ids (H10: the
# previous class names never matched a registered handler, so every agent
# dispatch returned "handler not found" and silently fell back to the LLM).
# Specialized-agent intents map to the AgentManager-registered ids (the
# `_agent`-suffixed ids created by agent_adapter.register_specialized_agents),
# executed through AgentManager when ModelBus has no such handler.
_INTENT_AGENTS: Dict[str, str] = {
    "file_read": "file_ops",
    "file_write": "file_ops",
    "file_delete": "file_ops",
    "code_execute": "code_exec",
    "web_search": "web_search",
    "vision": "vision",
    "code_understand": "code_understanding_agent",
    "knowledge_query": "knowledge_graph_agent",
    "creative_write": "creative_writing_agent",
    "data_analysis": "data_analysis_agent",
    "plan_create": "planning_agent",
    "audio": "audio_processing_agent",
    "nlp": "nlp_processing_agent",
}


class AgentOrchestrator:
    """
    Intelligent task router that:
    1. Classifies user intent
    2. Selects the best agent(s) for the task
    3. Decomposes complex tasks into sub-tasks
    4. Chains agent outputs when needed
    """

    def __init__(self, agent_manager=None, model_bus=None) -> None:
        self._agent_manager = agent_manager
        self._model_bus = model_bus
        self._agent_cache: Dict[str, Any] = {}

    @property
    def model_bus(self):
        """ModelBus reference (wired after construction by chat_routes)."""
        return self._model_bus

    @model_bus.setter
    def model_bus(self, value) -> None:
        self._model_bus = value

    def classify_intent(self, user_message: str) -> str:
        """Classify user message into an intent category via regex sub-classification."""
        lower = user_message.lower()

        # NOTE: IntentRegistry is intentionally NOT used as a short-circuit
        # gate here. Its density scoring is too coarse for routing (e.g. "搜尋
        # python 歷史" → code at 0.50 because of the "python" keyword, "幫我
        # 寫一首詩" → task at 0.33 because of "幫我"), and treating a hit as
        # "general" silently killed every specialized agent path. Sub-
        # classification below is the single source of truth for routing.

        # Code operations
        if re.search(r"(執行|運行|跑|execute|run|code|代碼|程式)", lower):
            return "code_execute"
        if re.search(r"(理解|解釋|分析|understand|explain|analyze|review.*code)", lower):
            return "code_understand"

        # Knowledge graph queries are more specific than web search — check
        # first so "查詢知識圖譜" routes to knowledge_query, not web_search.
        if re.search(r"(知識圖譜|知識庫|knowledge graph|knowledge base|圖譜|knowledge)", lower):
            return "knowledge_query"

        # Web search
        if re.search(r"(搜索|搜尋|查詢|search|find|lookup|google|web)", lower):
            return "web_search"

        # File operations (checked before creative to catch "寫入" vs creative "寫")
        if re.search(
            r"(讀取|打開|查看|read|open|show|寫入|保存|write|save|刪除|delete|remove)", lower
        ):
            if re.search(r"(刪除|delete|remove|移除)", lower):
                return "file_delete"
            if re.search(r"(寫入|保存|write|save|建立|create|新增|add)", lower):
                return "file_write"
            return "file_read"

        # Creative
        if re.search(r"(寫|創作|生成文本|write|create|story|poem|creative|文章)", lower):
            return "creative_write"

        # Data analysis
        if re.search(r"(分析數據|analyze.*data|統計|statistics|data|數據)", lower):
            return "data_analysis"

        # Planning
        if re.search(r"(規劃|計劃|plan|schedule|安排|organize)", lower):
            return "plan_create"

        # Vision
        if re.search(r"(圖片|影像|image|photo|picture|vision|視覺)", lower):
            return "vision"

        # Audio
        if re.search(r"(音訊|語音|audio|voice|speech|transcribe|音樂)", lower):
            return "audio"

        # NLP
        if re.search(r"(情緒|情感|sentiment|情緒分析|nlp|自然語言)", lower):
            return "nlp"

        # Image generation
        if re.search(r"(畫|繪圖|生成圖|generate.*image|draw|paint|art|藝術)", lower):
            return "image_generate"

        return "general"

    def select_agent(self, intent: str) -> Optional[str]:
        """Select the best agent for a given intent."""
        return _INTENT_AGENTS.get(intent)

    def decompose_task(self, user_message: str) -> List[Dict[str, Any]]:
        """
        Decompose a complex task into sub-tasks.
        Returns a list of {intent, message, priority} dicts.
        """
        subtasks: List[Dict[str, Any]] = []

        # Check for multi-step markers
        multi_step_markers = [
            "然後",
            "接著",
            "之後",
            "and then",
            "after that",
            "同時",
            "also",
            "另外",
            "additionally",
        ]
        lower = user_message.lower()

        has_multiple_steps = any(m in lower for m in multi_step_markers)

        if has_multiple_steps:
            # Split on multi-step markers
            sorted_markers = sorted(multi_step_markers, key=len, reverse=True)
            pattern = "|".join(re.escape(m) for m in sorted_markers)
            parts = re.split(pattern, user_message, flags=re.IGNORECASE)

            for i, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                intent = self.classify_intent(part)
                subtasks.append(
                    {
                        "intent": intent,
                        "message": part,
                        "priority": i + 1,
                        "agent": self.select_agent(intent),
                    }
                )
        else:
            intent = self.classify_intent(user_message)
            subtasks.append(
                {
                    "intent": intent,
                    "message": user_message,
                    "priority": 1,
                    "agent": self.select_agent(intent),
                }
            )

        return subtasks

    async def route_task(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Route a user message to the appropriate agent(s).
        Returns {intent, agent, result, subtasks}.
        """
        subtasks = self.decompose_task(user_message)

        results: List[Dict[str, Any]] = []
        for task in subtasks:
            intent = task["intent"]
            agent_name = task["agent"]
            message = task["message"]

            if intent == "general":
                results.append(
                    {
                        "intent": intent,
                        "agent": None,
                        "result": None,
                        "note": "No specialized agent; use LLM",
                    }
                )
                continue

            if not agent_name:
                results.append(
                    {
                        "intent": intent,
                        "agent": None,
                        "result": None,
                        "note": "No agent mapped for intent",
                    }
                )
                continue

            # Try to execute via ModelBus (handler-backed intents) first, then
            # fall back to AgentManager (specialized agents registered by
            # agent_adapter with `_agent`-suffixed ids). Previously this only
            # consulted ModelBus, so specialized-agent intents (code_understand,
            # knowledge_query, creative_write, ...) always returned None and
            # silently fell back to the LLM — the whole agent path was dead.
            result = None
            if self._model_bus:
                try:
                    result = await self._model_bus.execute_handler(
                        agent_name, message, context or {}
                    )
                except Exception as e:
                    logger.warning(f"ModelBus execution failed for {agent_name}: {e}", exc_info=True)
            # AgentManager fallback only applies to specialized-agent ids (the
            # `_agent`-suffixed ids from register_specialized_agents). ModelBus
            # handler ids (file_ops/code_exec/web_search/vision) must NOT fall
            # back — AgentManager doesn't register them and the attempt only
            # produces a misleading "Agent not found" warning.
            is_specialized_agent = agent_name.endswith("_agent")
            if (result is None or (isinstance(result, dict) and not result.get("success")))\
                    and is_specialized_agent and self._agent_manager is not None:
                try:
                    # Pass the raw message under every common parameter name so
                    # the adapter's _fill_defaults can satisfy the agent method
                    # signature (prompt/code/text/query/...). Without this the
                    # adapter filled required params with empty defaults and
                    # agents returned "No prompt provided" / "No code provided".
                    agent_task = {
                        "message": message,
                        "query": message,
                        "prompt": message,
                        "code": message,
                        "text": message,
                        "content": message,
                    }
                    agent_result = await self._agent_manager.execute_agent(
                        agent_name, agent_task
                    )
                    result = {
                        "type": agent_name,
                        "success": bool(getattr(agent_result, "success", False)),
                        "result": getattr(agent_result, "result_data", None),
                        "error": getattr(agent_result, "error", None),
                    }
                except Exception as e:
                    logger.warning(f"AgentManager execution failed for {agent_name}: {e}", exc_info=True)

            results.append(
                {
                    "intent": intent,
                    "agent": agent_name,
                    "result": result,
                    "message": message,
                }
            )

        return {
            "original_message": user_message,
            "subtasks": subtasks,
            "results": results,
            "primary_intent": subtasks[0]["intent"] if subtasks else "general",
        }
