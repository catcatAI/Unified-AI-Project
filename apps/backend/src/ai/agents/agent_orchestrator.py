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

# Intent → agent class name mapping
_INTENT_AGENTS: Dict[str, str] = {
    "file_read": "FileOperationHandler",
    "file_write": "FileOperationHandler",
    "file_delete": "FileOperationHandler",
    "code_execute": "CodeExecutionHandler",
    "code_understand": "CodeUnderstandingAgent",
    "web_search": "WebSearchAgent",
    "knowledge_query": "KnowledgeGraphAgent",
    "creative_write": "CreativeWritingAgent",
    "data_analysis": "DataAnalysisAgent",
    "plan_create": "PlanningAgent",
    "vision": "VisionProcessingAgent",
    "audio": "AudioProcessingAgent",
    "nlp": "NLPProcessingAgent",
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

    def classify_intent(self, user_message: str) -> str:
        """Classify user message into an intent category.

        Gate: IntentRegistry density+anti+format check must pass first.
        Only then do sub-classification regex patterns run.
        """
        lower = user_message.lower()

        # IntentRegistry gate — density+anti+format scoring is canonical
        try:
            from core.intent_registry import IntentRegistry

            ir = IntentRegistry()
            ir_name, ir_conf = ir.detect(user_message)
            # Only gate if IntentRegistry is confident enough (>= 0.3).
            # Low-confidence hits (e.g. "分析這張圖片" → document at 0.12) fall through to regex.
            if ir_name and ir_conf >= 0.3:
                return "general"
        except Exception as e:
            logger.warning("IntentRegistry detection failed in classify_intent(): %s", e, exc_info=True)

        # Sub-classification only runs after the gate passes
        # (IntentRegistry didn't match → treat as general creative/conversational)

        # Code operations
        if re.search(r"(執行|運行|跑|execute|run|code|代碼|程式)", lower):
            return "code_execute"
        if re.search(r"(理解|解釋|分析|understand|explain|analyze|review.*code)", lower):
            return "code_understand"

        # Web search
        if re.search(r"(搜索|搜尋|查詢|search|find|lookup|google|web)", lower):
            return "web_search"

        # Knowledge
        if re.search(r"(知識|knowledge|graph|圖譜|關係)", lower):
            return "knowledge_query"

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

            # Try to execute via ModelBus if available
            result = None
            if self._model_bus:
                try:
                    result = await self._model_bus.execute_handler(
                        agent_name, message, context or {}
                    )
                except Exception as e:
                    logger.warning(f"ModelBus execution failed for {agent_name}: {e}", exc_info=True)

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
