"""
ProjectCoordinator — 複雜任務規劃與多步執行協調器
===============================================
職責：
1. 意圖分解：將複雜查詢拆成可執行子任務圖
2. 執行協調：依賴順序執行（支援 HSP / LLM / WebSearch）
3. 結果整合：多段 LLM 生成 → 拼接 → 輸出
4. 格式學習：成功結果寫入 TemplateLibrary（透過 anchor_learning）

與現有系統整合：
- AngelaLLMService.generate_text() — LLM 文字生成
- WebSearchTool — 網頁搜索
- DocumentBuilder — 多段長文生成 + 格式學習
- HAMMemoryManager — 記憶存儲
- AnchorLearningEngine — 軸狀態學習
"""

import asyncio
import json
import logging
import re
import time
import uuid
import os
import yaml
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, TYPE_CHECKING

from core.hsp.connector import HSPConnector
from core.hsp.types import (
    HSPTaskRequestPayload,
    HSPTaskResultPayload,
    HSPMessageEnvelope,
)
from core.shared.types.common_types import PendingHSPTaskInfo
import networkx as nx

try:
    from core.intent_registry import IntentRegistry
    _intent_registry = IntentRegistry()
except ImportError:
    _intent_registry = None

if TYPE_CHECKING:
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager
    from core.learning.learning_manager import LearningManager
    from core.personality.personality_manager import PersonalityManager

logger = logging.getLogger(__name__)


class ProjectCoordinator:
    """
    複雜任務協調器。
    可以獨立使用（不需要 HSP 完整環境）。
    """

    def __init__(
        self,
        llm_interface: Any = None,
        service_discovery: Any = None,
        hsp_connector: Any = None,
        agent_manager: Any = None,
        memory_manager: "HAMMemoryManager" = None,
        learning_manager: "LearningManager" = None,
        personality_manager: "PersonalityManager" = None,
        dialogue_manager_config: Optional[Dict[str, Any]] = None,
    ):
        self.llm_interface = llm_interface
        self.service_discovery = service_discovery
        self.hsp_connector = hsp_connector
        self.agent_manager = agent_manager
        self.memory_manager = memory_manager
        self.learning_manager = learning_manager
        self.personality_manager = personality_manager
        self.config = dialogue_manager_config or {}

        self.ai_id = getattr(hsp_connector, "ai_id", None) if hsp_connector else "project_coordinator"
        self.turn_timeout_seconds = self.config.get("turn_timeout_seconds", 120)
        self.task_completion_events: Dict[str, asyncio.Event] = {}
        self.task_results: Dict[str, Any] = {}
        self._document_builder: Optional[Any] = None
        self._web_search: Optional[Any] = None
        self._llm_service: Optional[Any] = None
        self._template_library: Optional[Any] = None

        self._load_prompts()
        logger.info("ProjectCoordinator initialized.")

    def _load_prompts(self) -> None:
        prompts_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "configs", "prompts.yaml")
        try:
            with open(prompts_path, "r", encoding="utf-8") as f:
                self.prompts = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load prompts: {e}")
            self.prompts = {}

    async def _ensure_llm_service(self) -> Any:
        if self._llm_service is None:
            from services.angela_llm_service import get_llm_service
            self._llm_service = await get_llm_service()
        return self._llm_service

    def _get_web_search(self) -> Any:
        if self._web_search is None:
            try:
                from core.tools.web_search_tool import WebSearchTool
                self._web_search = WebSearchTool()
            except Exception as e:
                logger.warning(f"WebSearchTool not available: {e}")
        return self._web_search

    def _get_template_library(self) -> Any:
        if self._template_library is None:
            try:
                from ai.memory.template_library import TemplateLibrary
                self._template_library = TemplateLibrary()
            except Exception as e:
                logger.warning(f"TemplateLibrary not available: {e}")
        return self._template_library

    async def _get_document_builder(self) -> Any:
        if self._document_builder is None:
            from ai.dialogue.document_builder import DocumentBuilder
            self._document_builder = DocumentBuilder(
                llm_generate_fn=self._llm_generate_async,
                template_library=self._get_template_library(),
                memory_manager=self.memory_manager,
                max_segments=8,
                tokens_per_segment=512,
            )
        return self._document_builder

    async def _llm_generate_async(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        system_prompt: str = "",
    ) -> str:
        llm = await self._ensure_llm_service()
        return await llm.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
        )

    def _detect_capability_type(self, capability: str) -> str:
        cap_lower = capability.lower()
        if "search" in cap_lower or "web" in cap_lower:
            return "web_search"
        if "creative" in cap_lower or "write" in cap_lower or "角色" in capability:
            return "creative"
        if "document" in cap_lower or "doc" in cap_lower or "整理" in capability:
            return "document"
        if "code" in cap_lower or "programming" in cap_lower:
            return "code"
        return "hsp"

    async def handle_project(
        self, project_query: str, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> str:
        ai_name = "Angela"
        if self.personality_manager:
            try:
                ai_name = self.personality_manager.get_current_personality_trait("display_name", "Angela")
            except Exception:
                pass

        llm = await self._ensure_llm_service()

        logger.info(f"[{self.ai_id}] Phase 1: Decomposing project query...")
        available_capabilities = []
        if self.service_discovery:
            try:
                available_capabilities = await self.service_discovery.get_all_capabilities_async()
            except Exception as e:
                logger.debug(f"Service discovery failed: {e}")

        subtasks = await self._decompose_user_intent_into_subtasks(project_query, available_capabilities, llm)

        if not subtasks:
            logger.warning("[ProjectCoordinator] No subtasks generated, falling back to document builder")
            return await self._handle_as_document_task(project_query, llm)

        logger.info(f"[{self.ai_id}] Phase 2: Executing task graph...")
        try:
            task_execution_results = await self._execute_task_graph(subtasks)
        except ValueError as e:
            logger.error(f"[ProjectCoordinator] Task graph error: {e}")
            return f"{ai_name}：規劃過程中發現邏輯錯誤：{e}。"

        logger.info(f"[{self.ai_id}] Phase 3: Integrating results...")
        final_response = await self._integrate_subtask_results(project_query, task_execution_results, llm)

        if self.learning_manager:
            try:
                await self.learning_manager.learn_from_project_case({
                    "user_query": project_query,
                    "decomposed_subtasks": subtasks,
                    "subtask_results": task_execution_results,
                    "final_response": final_response,
                    "session_id": session_id,
                })
            except Exception as e:
                logger.debug(f"LearningManager not available: {e}")

        return final_response

    async def _handle_as_document_task(self, query: str, llm: Any) -> str:
        """當無法分解時，直接使用 DocumentBuilder 處理"""
        doc_builder = await self._get_document_builder()
        result = await doc_builder.build(
            query=query,
            complexity=0.6,
            learn_from_output=True,
        )
        return result.full_text if result.full_text else "（抱歉，生成過程中遇到問題...）"

    async def _execute_task_graph(self, subtasks: List[Dict[str, Any]]) -> Dict[int, Any]:
        """依賴圖拓撲排序執行"""
        task_graph = nx.DiGraph()
        for i, subtask in enumerate(subtasks):
            task_graph.add_node(i, data=subtask)
            parameters = subtask.get("task_parameters", {})
            if isinstance(parameters, dict):
                for param_value in parameters.values():
                    if isinstance(param_value, str):
                        deps = re.findall(r" < output_of_task_(\d+) > ", param_value)
                        for dep_str in deps:
                            dep_idx = int(dep_str)
                            if dep_idx < i:
                                task_graph.add_edge(dep_idx, i)

        if not nx.is_directed_acyclic_graph(task_graph):
            raise ValueError("Circular dependency detected in task graph.")

        execution_order = list(nx.topological_sort(task_graph))
        task_results: Dict[int, Any] = {}

        for task_index in execution_order:
            subtask_data = task_graph.nodes[task_index]["data"].copy()
            if isinstance(subtask_data.get("task_parameters"), dict):
                subtask_data["task_parameters"] = self._substitute_dependencies(
                    subtask_data["task_parameters"], task_results
                )

            result = await self._dispatch_single_subtask(subtask_data)
            task_results[task_index] = result

        return task_results

    async def _dispatch_single_subtask(self, subtask_data: Dict[str, Any]) -> Any:
        capability = subtask_data.get("capability_needed", "")
        params = subtask_data.get("task_parameters", {})
        cap_type = self._detect_capability_type(capability)

        logger.info(f"[ProjectCoordinator] Dispatching: {capability} (type={cap_type})")

        if cap_type == "web_search":
            return await self._execute_web_search(params)
        elif cap_type in ("creative", "document"):
            return await self._execute_document_task(params, cap_type)
        elif cap_type == "hsp" and self.hsp_connector:
            return await self._execute_via_hsp(capability, params)
        else:
            return await self._execute_llm_direct(params)

    async def _execute_web_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        web = self._get_web_search()
        if not web:
            return {"error": "WebSearchTool not available"}
        query = params.get("query", params.get("search_query", ""))
        num = params.get("num_results", 5)
        results = web.search(query, num_results=num)
        return {"query": query, "results": results, "count": len(results)}

    async def _execute_document_task(self, params: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        query = params.get("query", params.get("prompt", params.get("content", "")))
        if not query:
            return {"error": "No query provided for document task"}
        doc_builder = await self._get_document_builder()
        result = await doc_builder.build(query=query, complexity=0.6, learn_from_output=True)
        return {
            "full_text": result.full_text,
            "segments": len(result.segments),
            "successful": result.successful_segments,
            "format_id": result.format_id,
            "task_id": result.task_id,
        }

    async def _execute_via_hsp(self, capability: str, params: Dict[str, Any]) -> Any:
        correlation_id = str(uuid.uuid4())
        completion_event = asyncio.Event()
        self.task_completion_events[correlation_id] = completion_event

        if self.hsp_connector:
            await self.hsp_connector.send_task_request(
                capability_name=capability,
                payload=params,
                correlation_id=correlation_id,
            )
            try:
                await asyncio.wait_for(completion_event.wait(), timeout=self.turn_timeout_seconds)
                return self.task_results.get(correlation_id, {"error": "No result captured"})
            except asyncio.TimeoutError:
                return {"error": f"Task timeout after {self.turn_timeout_seconds}s"}
        return {"error": "HSP Connector not available"}

    async def _execute_llm_direct(self, params: Dict[str, Any]) -> Dict[str, Any]:
        prompt = params.get("prompt", params.get("query", str(params)))
        llm = await self._ensure_llm_service()
        text = await llm.generate_text(prompt=prompt, max_tokens=512)
        return {"text": text}

    def _substitute_dependencies(self, params: Dict[str, Any], results: Dict[int, Any]) -> Dict[str, Any]:
        new_params = params.copy()
        for key, value in new_params.items():
            if isinstance(value, str):
                match = re.search(r" < output_of_task_(\d+) > ", value)
                if match:
                    task_idx = int(match.group(1))
                    new_params[key] = value.replace(match.group(0), str(results.get(task_idx, "")))
        return new_params

    async def _decompose_user_intent_into_subtasks(
        self, user_query: str, available_capabilities: List[Dict[str, Any]], llm: Any
    ) -> List[Dict[str, Any]]:
        cap_str = json.dumps(available_capabilities[:10], ensure_ascii=False, indent=2)
        prompt_tmpl = self.prompts.get("decompose_user_intent", "")
        if not prompt_tmpl:
            prompt_tmpl = (
                "你是一個任務規劃專家。將用戶的複雜請求分解成子任務。\n"
                "可用能力：{capabilities}\n"
                "用戶請求：{user_query}\n"
                "請輸出 JSON 格式的子任務列表，每個任務包含：\n"
                "  - capability_needed: 需要的 capability 名稱\n"
                "  - task_parameters: 任務參數（可包含 '<output_of_task_N>' 引用前期結果）\n"
                "  - task_description: 任務描述\n"
                "只輸出 JSON，格式：[{{...}}, ...]"
            )

        prompt = prompt_tmpl.format(capabilities=cap_str, user_query=user_query)
        raw = await llm.generate_text(prompt=prompt, max_tokens=768, temperature=0.3)

        if not raw:
            logger.warning("[ProjectCoordinator] Empty LLM response for decomposition")
            return []

        try:
            cleaned = self._clean_json_response(raw)
            result = json.loads(cleaned)
            if isinstance(result, list) and all(isinstance(x, dict) for x in result):
                return result
            if isinstance(result, dict) and "subtasks" in result:
                subtasks = result["subtasks"]
                if isinstance(subtasks, list):
                    return subtasks
        except json.JSONDecodeError as e:
            logger.warning(f"[ProjectCoordinator] JSON parse failed: {e}")
            logger.debug(f"Raw: {raw[:200]}")

        if self._detect_complex_task(user_query):
            return self._fallback_decompose(user_query)
        return []

    def _detect_complex_task(self, query: str) -> bool:
        if _intent_registry:
            return _intent_registry.detect_complex_task(query)
        keywords = ["生成", "建立", "創建", "整理", "彙整", "搜尋", "研究", "規劃", "角色", "文件", "報告"]
        score = sum(1 for kw in keywords if kw in query)
        return score >= 1 or len(query) > 50

    def _fallback_decompose(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        if "角色" in query or "角色卡" in query:
            return [
                {"capability_needed": "creative_writing_v1", "task_parameters": {"task_type": "character_card", "query": query}, "task_description": "生成角色卡"},
                {"capability_needed": "creative_writing_v1", "task_parameters": {"task_type": "character_background", "query": query}, "task_description": "生成背景故事"},
            ]
        elif "搜尋" in query or "找資料" in query:
            return [
                {"capability_needed": "web_search_v1", "task_parameters": {"query": query, "num_results": 5}, "task_description": "搜索相關資料"},
                {"capability_needed": "creative_writing_v1", "task_parameters": {"task_type": "research_summary", "query": query}, "task_description": "整理搜索結果"},
            ]
        else:
            return [
                {"capability_needed": "creative_writing_v1", "task_parameters": {"query": query, "task_type": "general"}, "task_description": "處理任務"},
            ]

    def _clean_json_response(self, text: str) -> str:
        match = re.search(r"\[.*\]|\{.*\}", text, re.DOTALL)
        return match.group(0) if match else text

    async def _integrate_subtask_results(
        self, original_query: str, results: Dict[int, Any], llm: Any
    ) -> str:
        prompt_tmpl = self.prompts.get("integrate_subtask_results", "")
        if not prompt_tmpl:
            prompt_tmpl = (
                "用戶原始請求：{original_query}\n\n"
                "子任務結果：\n{results}\n\n"
                "請將這些結果整合成一個完整、連貫的回應，直接回答用戶的原始請求。"
                "如果結果不完整，說明原因並給出合理的補充。"
            )

        results_str = json.dumps(results, ensure_ascii=False, indent=2)
        prompt = prompt_tmpl.format(original_query=original_query, results=results_str)
        return await llm.generate_text(prompt=prompt, max_tokens=1024, temperature=0.5)

    def handle_task_result(
        self, result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope
    ) -> None:
        correlation_id = envelope.get("correlation_id")
        if not correlation_id:
            return
        status = result_payload.get("status")
        self.task_results[correlation_id] = (
            result_payload.get("payload") if status == "success" else {"error": result_payload.get("error_details", "Unknown")}
        )
        if correlation_id in self.task_completion_events:
            self.task_completion_events[correlation_id].set()