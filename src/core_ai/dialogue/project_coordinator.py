from __future__ import annotations
import asyncio
import json
import re
import uuid
import networkx as nx
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
import yaml
import os

from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPMessageEnvelope, HSPCapabilityAdvertisementPayload
from src.shared.types.common_types import PendingHSPTaskInfo
from datetime import datetime, timezone

if TYPE_CHECKING:
    from src.services.llm_interface import LLMInterface
    from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
    from src.hsp.connector import HSPConnector
    from src.core_ai.agent_manager import AgentManager
    from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
    from src.core_ai.learning.learning_manager import LearningManager
    from src.core_ai.personality.personality_manager import PersonalityManager

class ProjectCoordinator:
    def __init__(self,
                 llm_interface: LLMInterface,
                 service_discovery: ServiceDiscoveryModule,
                 hsp_connector: HSPConnector,
                 agent_manager: AgentManager,
                 memory_manager: HAMMemoryManager,
                 learning_manager: LearningManager,
                 personality_manager: PersonalityManager,
                 dialogue_manager_config: Dict[str, Any]):

        self.llm_interface = llm_interface
        self.service_discovery = service_discovery
        self.hsp_connector = hsp_connector
        self.agent_manager = agent_manager
        self.memory_manager = memory_manager
        self.learning_manager = learning_manager
        self.personality_manager = personality_manager
        self.config = dialogue_manager_config

        self.turn_timeout_seconds = self.config.get("turn_timeout_seconds", 120)
        self.pending_hsp_task_requests: Dict[str, PendingHSPTaskInfo] = {}
        self.task_completion_events: Dict[str, asyncio.Event] = {}
        self.task_results: Dict[str, Any] = {}
        self.ai_id = self.hsp_connector.ai_id if self.hsp_connector else "project_coordinator"
        self._load_prompts()
        print("ProjectCoordinator initialized.")

    def _load_prompts(self):
        """Loads prompts from the YAML file."""
        prompts_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'configs', 'prompts.yaml')
        with open(prompts_path, 'r') as f:
            self.prompts = yaml.safe_load(f)

    def handle_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope):
        correlation_id = envelope.get('correlation_id')
        if not correlation_id: return

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

        print(f"[{ai_name}] Phase 0/1: Decomposing project query...")
        available_capabilities = self.service_discovery.get_all_capabilities()
        subtasks = await self._decompose_user_intent_into_subtasks(project_query, available_capabilities)

        if not subtasks:
            return f"{ai_name}: I couldn't break down your request into a clear plan."

        print(f"[{ai_name}] Phase 2/3: Executing task plan...")
        try:
            task_execution_results = await self._execute_task_graph(subtasks)
        except ValueError as e:
            return f"{ai_name}: I encountered a logical error in my plan: {e}"

        print(f"[{ai_name}] Phase 4: Integrating results...")
        final_response = await self._integrate_subtask_results(project_query, task_execution_results)

        if self.learning_manager:
            await self.learning_manager.learn_from_project_case({
                "user_query": project_query, "decomposed_subtasks": subtasks,
                "subtask_results": task_execution_results, "final_response": final_response,
                "user_id": user_id, "session_id": session_id
            })

        return f"{ai_name}: Here's the result of your project request:\n\n{final_response}"

    async def _execute_task_graph(self, subtasks: List[Dict[str, Any]]) -> Dict[int, Any]:
        task_graph = nx.DiGraph()
        for i, subtask in enumerate(subtasks):
            task_graph.add_node(i, data=subtask)
            if isinstance(subtask.get("task_parameters"), dict):
                for param_value in subtask["task_parameters"].values():
                    if isinstance(param_value, str):
                        dependencies = re.findall(r"<output_of_task_(\d+)>", param_value)
                        for dep_index_str in dependencies:
                            dep_index = int(dep_index_str)
                            if dep_index < i: task_graph.add_edge(dep_index, i)
                            else: raise ValueError(f"Task {i} has an invalid dependency on a future task {dep_index}.")

        if not nx.is_directed_acyclic_graph(task_graph):
            raise ValueError("Circular dependency detected.")

        execution_order = list(nx.topological_sort(task_graph))
        task_results = {}
        for task_index in execution_order:
            subtask_data = task_graph.nodes[task_index]['data'].copy()

            if isinstance(subtask_data.get("task_parameters"), dict):
                subtask_data["task_parameters"] = self._substitute_dependencies(subtask_data["task_parameters"], task_results)

            result = await self._dispatch_single_subtask(subtask_data)
            task_results[task_index] = result
        return task_results

    def _substitute_dependencies(self, params: Dict[str, Any], results: Dict[int, Any]) -> Dict[str, Any]:
        substituted_params = params.copy()
        for key, value in substituted_params.items():
            if isinstance(value, str):
                def replace_func(match):
                    dep_idx = int(match.group(1))
                    try:
                        return json.dumps(results.get(dep_idx, ""))
                    except TypeError:
                        return str(results.get(dep_idx, ""))
                substituted_params[key] = re.sub(r"<output_of_task_(\d+)>", replace_func, value)
        return substituted_params

    async def _dispatch_single_subtask(self, subtask: Dict[str, Any]) -> Any:
        capability_name = subtask.get("capability_needed")
        params = subtask.get("task_parameters", {})
        found_caps = self.service_discovery.find_capabilities(capability_name_filter=capability_name)

        if not found_caps and self.agent_manager:
            agent_to_launch = f"{capability_name.split('_v')[0]}_agent"
            if self.agent_manager.launch_agent(agent_to_launch):
                await self.agent_manager.wait_for_agent_ready(agent_to_launch)
                found_caps = self.service_discovery.find_capabilities(capability_name_filter=capability_name)

        if not found_caps:
            return {"error": f"Could not find or launch an agent with capability '{capability_name}'."}

        selected_cap = found_caps[0]
        _user_msg, correlation_id = await self._send_hsp_request(selected_cap, params, subtask.get("task_description", ""))

        if not correlation_id:
            return {"error": f"Failed to dispatch task for capability '{capability_name}'."}

        return await self._wait_for_task_result(correlation_id, capability_name)

    async def _send_hsp_request(self, capability: Dict[str, Any], parameters: Dict[str, Any], description: str) -> Tuple[Optional[str], Optional[str]]:
        target_ai_id = capability.get("ai_id")
        capability_id = capability.get("capability_id")
        if not target_ai_id or not capability_id or not self.hsp_connector:
            return None, None

        request_id = f"taskreq_{uuid.uuid4().hex}"
        callback_topic = f"hsp/results/{self.ai_id}/{request_id}"

        hsp_task_payload = HSPTaskRequestPayload(
            request_id=request_id, requester_ai_id=self.ai_id, target_ai_id=target_ai_id,
            capability_id_filter=capability_id, parameters=parameters, callback_address=callback_topic
        )
        mqtt_request_topic = f"hsp/requests/{target_ai_id}"

        correlation_id = self.hsp_connector.send_task_request(payload=hsp_task_payload, target_ai_id_or_topic=mqtt_request_topic)
        if correlation_id:
            self.pending_hsp_task_requests[correlation_id] = PendingHSPTaskInfo(
                user_id="project_subtask", session_id="project_subtask", original_query_text=description,
                request_timestamp=datetime.now(timezone.utc).isoformat(),
                capability_id=capability_id, target_ai_id=target_ai_id,
                expected_callback_topic=callback_topic, request_type="project_subtask"
            )
        return "Request sent.", correlation_id

    async def _wait_for_task_result(self, correlation_id: str, capability_name: str) -> Any:
        completion_event = asyncio.Event()
        self.task_completion_events[correlation_id] = completion_event
        try:
            await asyncio.wait_for(completion_event.wait(), timeout=self.turn_timeout_seconds)
            return self.task_results.pop(correlation_id, {"error": "Result not found after event."})
        except asyncio.TimeoutError:
            return {"error": f"Task for '{capability_name}' timed out."}
        finally:
            self.task_completion_events.pop(correlation_id, None)

    async def _decompose_user_intent_into_subtasks(self, user_query: str, available_capabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        prompt = self.prompts['decompose_user_intent'].format(
            capabilities=json.dumps(available_capabilities, indent=2),
            user_query=user_query
        )
        raw_llm_output = await self.llm_interface.generate_response(prompt=prompt)
        try:
            return json.loads(raw_llm_output)
        except json.JSONDecodeError:
            return []

    async def _integrate_subtask_results(self, original_query: str, results: Dict[int, Any]) -> str:
        prompt = self.prompts['integrate_subtask_results'].format(
            original_query=original_query,
            results=json.dumps(results, indent=2)
        )
        return await self.llm_interface.generate_response(prompt=prompt)
