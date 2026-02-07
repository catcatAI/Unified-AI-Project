import asyncio
import json
import logging
import time
import uuid
import os
import yaml
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Type, TYPE_CHECKING

from src.core.hsp.connector import HSPConnector
from src.core.hsp.payloads import (
    HSPTaskRequestPayload,
    HSPTaskResultPayload,
    HSPCapabilityAdvertisementPayload,
    HSPMessageEnvelope
)
from src.ai.agents.agent_manager import AgentManager
from ...core.shared.types.common_types import PendingHSPTaskInfo
import networkx as nx

if TYPE_CHECKING:
    from ...core.service_discovery.service_discovery_module import ServiceDiscoveryModule
    from ...core.hsp.connector import HSPConnector
    from ...core.managers.agent_manager import AgentManager
    from ...ai.memory.ham_memory.ham_manager import HAMMemoryManager
    from ...core.learning.learning_manager import LearningManager
    from ...core.personality.personality_manager import PersonalityManager

logger = logging.getLogger(__name__)

class ProjectCoordinator:
    """
    Project Coordinator for Unified AI Project.
    Orchestrates complex projects by breaking it into manageable subtasks.
    """

    def __init__(self, 
                 llm_interface: Any,
                 service_discovery: 'ServiceDiscoveryModule',
                 hsp_connector: 'HSPConnector',
                 agent_manager: 'AgentManager',
                 memory_manager: 'HAMMemoryManager',
                 learning_manager: 'LearningManager',
                 personality_manager: 'PersonalityManager',
                 dialogue_manager_config: Dict[str, Any]):
        self.llm_interface = llm_interface
        self.service_discovery = service_discovery
        self.hsp_connector = hsp_connector
        self.agent_manager = agent_manager
        self.memory_manager = memory_manager
        self.learning_manager = learning_manager
        self.personality_manager = personality_manager
        self.config = dialogue_manager_config

        self.ai_id = self.hsp_connector.ai_id if self.hsp_connector else "project_coordinator"
        self.turn_timeout_seconds = self.config.get("turn_timeout_seconds", 120)
        self.pending_hsp_task_requests: Dict[str, PendingHSPTaskInfo] = {}
        self.task_completion_events: Dict[str, asyncio.Event] = {}
        self.task_results: Dict[str, Any] = {}
        
        self._load_prompts()
        logger.info("ProjectCoordinator initialized.")

    def _load_prompts(self):
        """Loads prompts from the YAML file."""
        prompts_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'configs', 'prompts.yaml')
        try:
            with open(prompts_path, 'r') as f:
                self.prompts = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            self.prompts = {}

    def handle_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        correlation_id = envelope.get('correlation_id')
        if not correlation_id:
            return
            
        status = result_payload.get("status")
        if status == "success":
            self.task_results[correlation_id] = result_payload.get("payload")
        else:
            self.task_results[correlation_id] = {"error": result_payload.get("error_details", "Unknown error")}

        if correlation_id in self.task_completion_events:
            self.task_completion_events[correlation_id].set()

    async def handle_project(self, project_query: str, session_id: Optional[str], user_id: Optional[str]) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")

        if not self.service_discovery or not self.hsp_connector:
            return f"{ai_name}: I can't access my specialist network to handle this project."

        logger.info(f"[{self.ai_id}] Phase 1: Decomposing project query...")
        available_capabilities = await self.service_discovery.get_all_capabilities_async()
        subtasks = await self._decompose_user_intent_into_subtasks(project_query, available_capabilities)

        if not subtasks:
            return f"{ai_name}: I couldn't break down your request into a clear plan."

        logger.info(f"[{ai_name}] Phase 2 / 3, Executing task plan...")
        try:
            task_execution_results = await self._execute_task_graph(subtasks)
        except ValueError as e:
            return f"{ai_name}: I encountered a logical error in my plan: {e}"

        logger.info(f"[{ai_name}] Phase 4: Integrating results...")
        final_response = await self._integrate_subtask_results(project_query, task_execution_results)

        if self.learning_manager:
            await self.learning_manager.learn_from_project_case(
                {
                    "user_query": project_query,
                    "decomposed_subtasks": subtasks,
                    "subtask_results": task_execution_results,
                    "final_response": final_response,
                    "session_id": session_id
                }
            )

        return f"{ai_name}: Here's the result of your project request: \n\n{final_response}"

    async def _execute_task_graph(self, subtasks: List[Dict[str, Any]]) -> Dict[int, Any]:
        """Execute a graph of subtasks in topological order."""
        import networkx as nx
        import re

        task_graph = nx.DiGraph()
        for i, subtask in enumerate(subtasks):
            task_graph.add_node(i, data=subtask)
            parameters = subtask.get("task_parameters", {})
            if isinstance(parameters, dict):
                for param_value in parameters.values():
                    if isinstance(param_value, str):
                        dependencies = re.findall(r" < output_of_task_(\d+) > ", param_value)
                        for dep_index_str in dependencies:
                            dep_index = int(dep_index_str)
                            if dep_index < i:
                                task_graph.add_edge(dep_index, i)
                            else:
                                raise ValueError(f"Task {i} has an invalid dependency on future task {dep_index}.")

        if not nx.is_directed_acyclic_graph(task_graph):
            raise ValueError("Circular dependency detected in task graph.")

        execution_order = list(nx.topological_sort(task_graph))
        task_results = {}

        for task_index in execution_order:
            subtask_data = task_graph.nodes[task_index]['data'].copy()
            
            if isinstance(subtask_data.get("task_parameters"), dict):
                subtask_data["task_parameters"] = self._substitute_dependencies(
                    subtask_data["task_parameters"], task_results
                )

            result = await self._dispatch_single_subtask(subtask_data)
            task_results[task_index] = result

    async def _decompose_user_intent_into_subtasks(self, user_query: str, available_capabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Decompose a complex user intent into a list of subtasks."""
        prompt = self.prompts.get('decompose_user_intent', '').format(
            capabilities=json.dumps(available_capabilities, indent=2),
            user_query=user_query
        )
        
        raw_llm_output = await self.llm_interface.generate_response(prompt=prompt)
        
        if not raw_llm_output or not isinstance(raw_llm_output, str):
            logger.error(f"[ProjectCoordinator] Invalid LLM response: {raw_llm_output}")
            return []

        # Try to parse as JSON
        try:
            result = json.loads(self._clean_json_response(raw_llm_output))
            if isinstance(result, list) and all(isinstance(item, dict) for item in result):
                logger.info(f"[ProjectCoordinator] Successfully parsed LLM response as JSON list: {result}")
                return result
            elif isinstance(result, dict) and "subtasks" in result:
                subtasks = result["subtasks"]
                if isinstance(subtasks, list) and all(isinstance(item, dict) for item in subtasks):
                    logger.info(f"[ProjectCoordinator] Extracted subtasks from dict: {subtasks}")
                    return subtasks
        except json.JSONDecodeError as e:
            logger.error(f"[ProjectCoordinator] Failed to parse LLM response as JSON: {e}")
            logger.error(f"[ProjectCoordinator] Raw LLM output: {raw_llm_output}")

        # Fallback keyword-based decomposition
        logger.warning("[ProjectCoordinator] Falling back to keyword-based decomposition")
        if any(kw in user_query.lower() for kw in ["sum", "calculate", "add"]):
            return [{
                "capability_needed": "data_analysis_v1",
                "task_parameters": {"action": "calculate", "expression": user_query},
                "task_description": "Perform calculation",
                "dependencies": []
            }]
        return []

    def _clean_json_response(self, text: str) -> str:
        """Extract JSON from a potentially messy LLM response."""
        import re
        json_match = re.search(r'\[.*\]|\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        return text

    async def _integrate_subtask_results(self, original_query: str, results: Dict[int, Any]) -> str:
        """Integrate results from multiple subtasks into a final response."""
        prompt = self.prompts.get('integrate_subtask_results', '').format(
            original_query=original_query,
            results=json.dumps(results, indent=2)
        )
        return await self.llm_interface.generate_response(prompt=prompt)