# Placeholder for Dialogue Manager
# This module will orchestrate the conversation flow, integrate with other AI components,
# and generate responses.

import asyncio
import json
from datetime import datetime, timezone # Added timezone
from typing import Optional, Dict, Any, List, Tuple
import uuid # For test session IDs in __main__
import os # Added for os.path.exists and os.remove in __main__
import re # Added for regex in _is_kg_query
# Removed redundant json import: import json # Added for parsing LLM response for I/O details
import ast # Added for syntax validation of generated code

from src.core_ai.personality.personality_manager import PersonalityManager
from src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from src.services.llm_interface import LLMInterface, LLMInterfaceConfig
from src.core_ai.emotion_system import EmotionSystem
from src.core_ai.crisis_system import CrisisSystem
from src.core_ai.time_system import TimeSystem
from src.core_ai.formula_engine import FormulaEngine
from src.tools.tool_dispatcher import ToolDispatcher
from src.core_ai.learning.self_critique_module import SelfCritiqueModule
from src.core_ai.learning.fact_extractor_module import FactExtractorModule
from src.core_ai.learning.learning_manager import LearningManager
from src.core_ai.learning.content_analyzer_module import ContentAnalyzerModule
from src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from src.services.sandbox_executor import SandboxExecutor
from src.services.resource_awareness_service import ResourceAwarenessService # Added import
import networkx as nx
from src.shared.types.common_types import ( # Added src.
    FormulaConfigEntry, CritiqueResult, OperationalConfig, DialogueTurn,
    PendingHSPTaskInfo, ParsedToolIODetails, DialogueMemoryEntryMetadata # Added missing DialogueMemoryEntryMetadata
)
from src.hsp.connector import HSPConnector # Added src.
from src.hsp.types import HSPTaskRequestPayload, HSPTaskResultPayload, HSPCapabilityAdvertisementPayload, HSPFactPayload, HSPMessageEnvelope # Added src. and HSPMessageEnvelope
from src.fragmenta_bus.module_bus.controller import ModuleBusController, ModuleExecutionError, ModuleAssemblyError # Added import

class DialogueManager:
    def __init__(self, personality_manager: Optional[PersonalityManager] = None,
                 memory_manager: Optional[HAMMemoryManager] = None,
                 llm_interface: Optional[LLMInterface] = None,
                 emotion_system: Optional[EmotionSystem] = None,
                 crisis_system: Optional[CrisisSystem] = None,
                 time_system: Optional[TimeSystem] = None,
                 formula_engine: Optional[FormulaEngine] = None,
                 tool_dispatcher: Optional[ToolDispatcher] = None,
                 self_critique_module: Optional[SelfCritiqueModule] = None,
                 learning_manager: Optional[LearningManager] = None,
                 content_analyzer: Optional[ContentAnalyzerModule] = None,
                 sandbox_executor: Optional[SandboxExecutor] = None,
                 ai_id: Optional[str] = None,
                 service_discovery_module: Optional[ServiceDiscoveryModule] = None,
                 hsp_connector: Optional[HSPConnector] = None,
                 config: Optional[OperationalConfig] = None,
                 module_bus_controller: Optional[ModuleBusController] = None): # Added module_bus_controller

        self.config: OperationalConfig = config if config else {} # type: ignore
        self.ai_id: str = ai_id if ai_id else f"dm_instance_{uuid.uuid4().hex[:6]}"

        op_configs_from_main: Dict[str, Any] = {}
        if isinstance(self.config, dict):
            operational_configs_value = self.config.get("operational_configs")
            if isinstance(operational_configs_value, dict):
                op_configs_from_main = operational_configs_value

        self.service_discovery_module = service_discovery_module
        self.hsp_connector = hsp_connector
        self.pending_hsp_task_requests: Dict[str, PendingHSPTaskInfo] = {}

        self.personality_manager = personality_manager if personality_manager else PersonalityManager()

        # Initialize ResourceAwarenessService first if HAM is to be default-instantiated
        self.resource_awareness_service = ResourceAwarenessService() # Uses default config path

        self.memory_manager = memory_manager if memory_manager else HAMMemoryManager(
            core_storage_filename="dialogue_context_memory.json",
            resource_awareness_service=self.resource_awareness_service # Pass it here
        )

        # LLMInterface expects a config that might contain OperationalConfig, not OperationalConfig directly.
        # If self.config is OperationalConfig, we might need to wrap it or LLMInterface needs adjustment.
        # Assuming LLMInterface can handle OperationalConfig or a dict representation of it.
        llm_config_arg: Any = self.config
        self.llm_interface = llm_interface if llm_interface else LLMInterface(config=llm_config_arg)

        # Initialize ModuleBusController
        self.module_bus_controller = module_bus_controller
        if self.module_bus_controller: # Register the dialogue response blueprint if module_bus is provided
            # Load the blueprint from file
            project_root = os.path.dirname(os.path.abspath(__file__)) # src/core_ai/dialogue
            project_root = os.path.abspath(os.path.join(project_root, '..', '..', '..')) # Unified-AI-Project/
            blueprint_path = os.path.join(project_root, 'configs', 'fragmenta_bus', 'module_blueprints', 'dialogue_response_module.json')
            try:
                with open(blueprint_path, 'r') as f:
                    dialogue_response_blueprint = json.load(f)
                self.module_bus_controller.register_blueprint(dialogue_response_blueprint)
                print(f"DialogueManager: Registered dialogue.response.v1 blueprint.")
            except FileNotFoundError:
                print(f"DialogueManager: WARNING - Dialogue response blueprint not found at {blueprint_path}. ModuleBus response generation will be unavailable.")
                self.module_bus_controller = None # Disable if blueprint not found
            except Exception as e:
                print(f"DialogueManager: WARNING - Error loading/registering dialogue response blueprint: {e}. ModuleBus response generation will be unavailable.")
                self.module_bus_controller = None # Disable if error


        self.formula_engine = formula_engine if formula_engine else FormulaEngine()
        self.tool_dispatcher = tool_dispatcher if tool_dispatcher else ToolDispatcher(llm_interface=self.llm_interface)

        self.fact_extractor_module = FactExtractorModule(
            llm_interface=self.llm_interface
        )
        self.self_critique_module = self_critique_module if self_critique_module else SelfCritiqueModule(
            self.llm_interface,
            operational_config=op_configs_from_main # This expects Dict[str,Any]
        )
        # LearningManager also expects operational_config as Dict[str,Any]
        self.learning_manager = learning_manager if learning_manager else LearningManager(
            ai_id=self.ai_id, # Pass ai_id to LearningManager
            ham_memory_manager=self.memory_manager, # Corrected order
            fact_extractor=self.fact_extractor_module,
            content_analyzer=content_analyzer, # Pass CA here
            hsp_connector=self.hsp_connector, # Pass HSP connector
            trust_manager=getattr(service_discovery_module, 'trust_manager', None), # Pass TrustManager if available
            operational_config=op_configs_from_main
        )
        self.content_analyzer = content_analyzer if content_analyzer else ContentAnalyzerModule()
        self.sandbox_executor = sandbox_executor if sandbox_executor else SandboxExecutor()

        current_pers_profile = self.personality_manager.current_personality
        self.emotion_system = emotion_system if emotion_system else EmotionSystem(personality_profile=current_pers_profile)
        self.crisis_system = crisis_system if crisis_system else CrisisSystem(config=dict(self.config))
        self.time_system = time_system if time_system else TimeSystem(config=dict(self.config))

        self.active_sessions: Dict[str, List[DialogueTurn]] = {}
        self.session_knowledge_graphs: Dict[str, nx.DiGraph] = {}

        max_hist_val: Any = 6
        learning_thresholds_config_val: Any = None
        timeouts_config_val: Any = None

        if isinstance(self.config, dict):
            max_hist_val = self.config.get("max_dialogue_history", 6)
            op_configs = self.config.get("operational_configs")
            if isinstance(op_configs, dict):
                 learning_thresholds_config_val = op_configs.get("learning_thresholds")
                 timeouts_config_val = op_configs.get("timeouts")

        try:
            self.max_history_per_session: int = int(max_hist_val)
        except (ValueError, TypeError):
            self.max_history_per_session: int = 6

        self.turn_timeout_seconds: int = int(timeouts_config_val.get("dialogue_manager_turn", 120)) if isinstance(timeouts_config_val, dict) else 120
        self.min_critique_score_to_store: float = float(learning_thresholds_config_val.get("min_critique_score_to_store", 0.0)) if isinstance(learning_thresholds_config_val, dict) else 0.0

        if not self.personality_manager.current_personality:
            self.personality_manager.load_personality(self.personality_manager.default_profile_name)

        print(f"DialogueManager: Initialized. Turn timeout: {self.turn_timeout_seconds}s. Min critique score to store: {self.min_critique_score_to_store}")

        if self.hsp_connector:
            self.hsp_connector.register_on_task_result_callback(self._handle_incoming_hsp_task_result)

    def _handle_incoming_hsp_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, full_envelope: HSPMessageEnvelope) -> None:
        correlation_id = full_envelope.get("correlation_id")
        print(f"DialogueManager (AI ID: {self.ai_id}): Received HSP TaskResult from '{sender_ai_id}' for correlation ID '{correlation_id}'.")

        if not correlation_id or correlation_id not in self.pending_hsp_task_requests:
            print(f"DialogueManager: Received unsolicited or unknown TaskResult (correlation_id: {correlation_id}). Discarding.")
            return

        pending_request_info: PendingHSPTaskInfo = self.pending_hsp_task_requests.pop(correlation_id)
        original_user_id = pending_request_info.get("user_id")
        original_session_id = pending_request_info.get("session_id")
        original_query_text = pending_request_info.get("original_query_text")
        request_type = pending_request_info.get("request_type", "generic_task")

        status = result_payload.get("status")
        service_payload = result_payload.get("payload", {})
        ai_name = self.personality_manager.get_current_personality_trait("display_name", self.ai_id)
        result_message_to_user: str = ""

        if status == "success":
            print(f"DialogueManager: Task/Query SUCCESS for correlation ID '{correlation_id}'. Result payload: {service_payload}")
            if request_type == "proactive_fact_query" and self.learning_manager:
                facts_found = service_payload.get("facts_found", [])
                if isinstance(facts_found, list) and len(facts_found) > 0:
                    print(f"DialogueManager: Received {len(facts_found)} facts from proactive HSP query.")
                    for fact_idx, fact_data in enumerate(facts_found):
                        if isinstance(fact_data, dict):
                            # Assuming fact_data is HSPFactPayload compatible
                            self.learning_manager.process_and_store_hsp_fact(fact_data, sender_ai_id, full_envelope) # type: ignore
                    result_message_to_user = f"{ai_name}: I've found some additional information related to '{original_query_text.replace('Proactive fact query for: ', '')}' from my network."
                    print(f"--- Proactive HSP Facts Received (User: {original_user_id}) ---\n{result_message_to_user}\n---")
                else:
                    print(f"DialogueManager: Proactive HSP fact query for '{original_query_text}' returned no usable facts.")
            elif request_type == "generic_task":
                result_message_to_user = f"{ai_name}: Regarding your request about '{original_query_text}', the specialist AI ({sender_ai_id}) responded with: {json.dumps(service_payload)}"
                print(f"--- HSP Task Result for User (Session: {original_session_id}, User: {original_user_id}) ---\n{result_message_to_user}\n---")

            if result_message_to_user and self.memory_manager: # Store if there's a message
                metadata_dict: Dict[str, Any] = {
                    "speaker": "ai", "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": original_user_id, "session_id": original_session_id,
                    "source": "hsp_task_result_success", "hsp_correlation_id": correlation_id,
                    "hsp_result_sender_ai_id": sender_ai_id, "original_user_query_text": original_query_text,
                    "hsp_task_service_payload": service_payload
                }
                self.memory_manager.store_experience(result_message_to_user, "ai_dialogue_text_hsp_result_success", metadata_dict) # type: ignore

            if self.content_analyzer and isinstance(service_payload, dict):
                description_text = service_payload.get("description") or service_payload.get("summary")
                if isinstance(description_text, str):
                    synthetic_fact = HSPFactPayload(
                        id=f"hsp_res_fact_{result_payload.get('result_id', uuid.uuid4().hex[:6])}",
                        statement_type="natural_language", statement_nl=description_text,
                        source_ai_id=sender_ai_id,
                        timestamp_created=result_payload.get("timestamp_completed", datetime.now(timezone.utc).isoformat()),
                        confidence_score=0.85, tags=["hsp_task_result_derived"]
                    )
                    self.content_analyzer.process_hsp_fact_content(synthetic_fact, sender_ai_id) # type: ignore

            if hasattr(self, 'trust_manager') and self.trust_manager:
                self.trust_manager.update_trust_score(sender_ai_id, adjustment=0.05)
        else:
            error_details = result_payload.get("error_details", {})
            error_msg_from_peer = error_details.get('error_message', 'an unknown issue')
            result_message_to_user = f"{ai_name}: Regarding your request about '{original_query_text}', the specialist AI ({sender_ai_id}) could not complete it. Status: {status}, Details: {error_msg_from_peer}"
            print(f"--- HSP Task Error for User (Session: {original_session_id}, User: {original_user_id}) ---\n{result_message_to_user}\n---")
            if self.memory_manager:
                metadata_dict: Dict[str, Any] = {
                    "speaker": "ai", "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_id": original_user_id, "session_id": original_session_id,
                    "source": "hsp_task_result_error", "hsp_correlation_id": correlation_id,
                    "hsp_result_sender_ai_id": sender_ai_id, "error_details": error_details,
                    "original_user_query_text": original_query_text
                }
                self.memory_manager.store_experience(result_message_to_user, "ai_dialogue_text_hsp_error", metadata_dict) # type: ignore
            if hasattr(self, 'trust_manager') and self.trust_manager:
                self.trust_manager.update_trust_score(sender_ai_id, adjustment=-0.1 if status == "failure" else -0.05)

    async def _dispatch_hsp_task_request(
        self, capability_advertisement: HSPCapabilityAdvertisementPayload,
        request_parameters: Dict[str, Any], original_user_query: str,
        user_id: Optional[str], session_id: Optional[str],
        request_type: str = "generic_task"
    ) -> Tuple[Optional[str], Optional[str]]:
        if not self.hsp_connector or not self.service_discovery_module:
            return "I can't connect to my specialist network right now.", None

        target_ai_id = capability_advertisement.get("ai_id")
        capability_id = capability_advertisement.get("capability_id")
        if not target_ai_id or not capability_id: # Should not happen if cap_adv is valid
            return "I found a specialist, but some details are missing to contact them.", None

        request_id = f"taskreq_{uuid.uuid4().hex}"
        callback_topic = f"hsp/results/{self.ai_id}/{request_id}"

        hsp_task_payload = HSPTaskRequestPayload(
            request_id=request_id, requester_ai_id=self.ai_id, target_ai_id=target_ai_id,
            capability_id_filter=capability_id, parameters=request_parameters, callback_address=callback_topic
        )
        mqtt_request_topic = f"hsp/requests/{target_ai_id}"
        print(f"DialogueManager: Sending HSP TaskRequest '{request_id}' to '{target_ai_id}' (MQTT topic: {mqtt_request_topic}) for capability '{capability_id}'.")

        correlation_id = self.hsp_connector.send_task_request(payload=hsp_task_payload, target_ai_id_or_topic=mqtt_request_topic)

        if correlation_id:
            pending_info: PendingHSPTaskInfo = {
                "user_id": user_id, "session_id": session_id, "original_query_text": original_user_query,
                "request_timestamp": datetime.now(timezone.utc).isoformat(),
                "capability_id": capability_id, "target_ai_id": target_ai_id,
                "expected_callback_topic": callback_topic, "request_type": request_type
            }
            self.pending_hsp_task_requests[correlation_id] = pending_info
            user_message = f"I've sent your request for '{capability_advertisement.get('name', capability_id)}' to a specialist AI ({target_ai_id}). I'll process their response once I get it."
            return user_message, correlation_id
        else:
            return "I tried to consult a specialist, but I couldn't send the request.", None

    def _find_entity_node_id_in_kg(self, graph: nx.DiGraph, entity_label_query: str) -> Optional[str]:
        if not graph: return None
        for node_id, data in graph.nodes(data=True):
            node_label = data.get("label")
            if isinstance(node_label, str) and node_label.lower() == entity_label_query.lower():
                return node_id
        return None

    def _query_session_kg(self, session_id: str, entity_label: str, relationship_query: str) -> Optional[str]:
        graph = self.session_knowledge_graphs.get(session_id)
        if not graph: return None
        source_node_id = self._find_entity_node_id_in_kg(graph, entity_label)
        if not source_node_id: return None
        for target_node_id in graph.successors(source_node_id):
            edge_data = graph.get_edge_data(source_node_id, target_node_id)
            if edge_data and edge_data.get("type") == relationship_query:
                return graph.nodes.get(target_node_id, {}).get("label", target_node_id)
        return None

    def _is_kg_query(self, user_input: str) -> Optional[Tuple[str, str]]:
        user_input_lower = user_input.lower()
        title_patterns = [r"who is (?:the |a )?(ceo|president|founder|manager|director|cto|coo|cfo|cio|cmo|vp|chairman|chairwoman|chairperson) of (.+)\??"]
        for pattern_str in title_patterns:
            match = re.match(pattern_str, user_input_lower)
            if match: return match.group(2).strip().rstrip('?').replace("'s", "").strip(), f"has_{match.group(1).strip()}"
        location_patterns = [r"where is (.+) located\??", r"where is (.+) based\??"]
        for pattern_str in location_patterns:
            match = re.match(pattern_str, user_input_lower)
            if match: return match.group(1).strip().rstrip('?').replace("'s", "").strip(), "located_in"
        acquire_patterns = [r"what (?:company|organization|entity|firm|startup) did (.+) acquire\??", r"what did (.+) acquire\??"]
        for pattern_str in acquire_patterns:
            match = re.match(pattern_str, user_input_lower)
            if match: return match.group(1).strip().rstrip('?').replace("'s", "").strip(), "acquire"
        return None

    async def _analyze_and_store_text_context(self, text_content: str, context_id: str):
        if not self.content_analyzer: return
        print(f"DialogueManager: Analyzing content for context_id '{context_id}'...")
        try:
            _, nx_graph = self.content_analyzer.analyze_content(text_content)
            self.session_knowledge_graphs[context_id] = nx_graph
            print(f"DialogueManager: KG for context '{context_id}' updated: {nx_graph.number_of_nodes()} nodes, {nx_graph.number_of_edges()} edges.")
        except Exception as e: print(f"DialogueManager: Error during content analysis for '{context_id}': {e}")

    async def get_response_with_tool_support(self, user_input: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        print(f"DialogueManager: Received input='{user_input}', session_id='{session_id}', user_id='{user_id}'")
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")

        # Store user input
        user_mem_id: Optional[str] = None
        if self.memory_manager:
            user_metadata: DialogueMemoryEntryMetadata = {"speaker": "user", "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "session_id": session_id} # type: ignore
            user_mem_id = self.memory_manager.store_experience(user_input, "user_dialogue_text", user_metadata)

        # Check for formula match that indicates a tool call
        matched_formula = self.formula_engine.match_input(user_input)
        if matched_formula:
            formula_result = self.formula_engine.execute_formula(matched_formula)
            action_name = formula_result.get("action_name")
            if action_name == "dispatch_tool":
                action_params = formula_result.get("action_params", {})
                tool_name = action_params.get("tool_name")
                tool_query = action_params.get("tool_query")
                if tool_name and tool_query:
                    return {
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "tool_query": tool_query,
                        "action_params": action_params
                    }

        # If no tool call, fallback to simple response generation
        response_text = await self.get_simple_response(user_input, session_id, user_id)
        return {"type": "text", "content": response_text}

    async def get_response_from_tool_result(self, tool_name: str, tool_result: Dict[str, Any], session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")

        # Log the tool result
        if self.memory_manager:
            tool_metadata = {
                "speaker": "system",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "session_id": session_id,
                "tool_name": tool_name,
                "tool_result": tool_result
            }
            self.memory_manager.store_experience(f"Tool {tool_name} executed.", "system_tool_result", tool_metadata)

        # Generate a response based on the tool result
        prompt = f"The user asked to use the '{tool_name}' tool. The tool returned the following result: {json.dumps(tool_result)}. Please formulate a natural language response to the user based on this result."

        response_text = self.llm_interface.generate_response(prompt=prompt)

        # Store AI response
        if self.memory_manager:
            ai_metadata: DialogueMemoryEntryMetadata = {"speaker": "ai", "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "session_id": session_id} # type: ignore
            self.memory_manager.store_experience(response_text, "ai_dialogue_text", ai_metadata)

        return f"{ai_name}: {response_text}"

    async def get_simple_response(self, user_input: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        print(f"DialogueManager: Received input='{user_input}', session_id='{session_id}', user_id='{user_id}'")
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")
        response_text: str = ""
        user_mem_id: Optional[str] = None
        if self.memory_manager:
            user_metadata: DialogueMemoryEntryMetadata = {"speaker": "user", "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "session_id": session_id} # type: ignore
            user_mem_id = self.memory_manager.store_experience(user_input, "user_dialogue_text", user_metadata)

        if user_mem_id and self.learning_manager and not (self.crisis_system.assess_input_for_crisis({"text": user_input}) > 0):
            # process_and_store_learnables is currently synchronous
            self.learning_manager.process_and_store_learnables(text=user_input, user_id=user_id, session_id=session_id, source_interaction_ref=user_mem_id)

        crisis_level = self.crisis_system.assess_input_for_crisis({"text": user_input})
        analysis_command = "!analyze: "
        if user_input.startswith(analysis_command):
            if session_id:
                await self._analyze_and_store_text_context(user_input[len(analysis_command):], session_id)
                response_text = f"{ai_name}: Context analysis triggered. Knowledge graph updated."
            else: response_text = f"{ai_name}: Cannot analyze context without a session_id."
            # Fall through to store this response

        # --- Attempt to answer from Knowledge Graph (if no response yet) ---
        if not response_text and session_id and session_id in self.session_knowledge_graphs and not crisis_level > 0 :
            kg_query_parts = self._is_kg_query(user_input)
            if kg_query_parts:
                entity_label, rel_query_keyword = kg_query_parts
                # Retrieve the source node data to get its original label for a more natural response
                source_node_id = self._find_entity_node_id_in_kg(self.session_knowledge_graphs[session_id], entity_label)
                source_node_data = self.session_knowledge_graphs[session_id].nodes.get(source_node_id, {}) if source_node_id else {}
                display_entity_label = source_node_data.get('label', entity_label.capitalize())

                answer_from_kg = self._query_session_kg(session_id, entity_label, rel_query_keyword)
                if answer_from_kg:
                    if rel_query_keyword.startswith("has_"): response_text = f"{ai_name}: From context, the {rel_query_keyword.split('has_')[1].replace('_', ' ')} of {display_entity_label} is {answer_from_aq}."
                    elif rel_query_keyword == "located_in": response_text = f"{ai_name}: From context, {display_entity_label} is located in {answer_from_kg}."
                    elif rel_query_keyword == "acquire": response_text = f"{ai_name}: From context, {display_entity_label} acquired {answer_from_kg}."
                    else: response_text = f"{ai_name}: From context regarding {display_entity_label}: {answer_from_kg}."
                    print(f"DialogueManager: Answered from KG: '{response_text}'")

        # --- HSP Task Dispatch Trigger (if no response yet) ---
        hsp_task_trigger = "hsp_task: "
        if not response_text and user_input.lower().startswith(hsp_task_trigger) and self.service_discovery_module and self.hsp_connector:
            command_part = user_input[len(hsp_task_trigger):]
            parts = command_part.split(" with params ", 1)
            if len(parts) == 2:
                capability_name_query, params_json_str = parts[0].strip(), parts[1].strip()
                try:
                    request_params = json.loads(params_json_str)
                    found_caps = self.service_discovery_module.find_capabilities(capability_name_filter=capability_name_query, sort_by_trust=True) or \
                                 self.service_discovery_module.find_capabilities(tags_filter=[capability_name_query], sort_by_trust=True)
                    if found_caps:
                        selected_cap = found_caps[0]
                        user_facing_msg, _ = await self._dispatch_hsp_task_request(selected_cap, request_params, user_input, user_id, session_id)
                        response_text = f"{ai_name}: {user_facing_msg}" if user_facing_msg else f"{ai_name}: Issue dispatching HSP task."
                    else: response_text = f"{ai_name}: Couldn't find specialist for '{capability_name_query}'."
                except json.JSONDecodeError: response_text = f"{ai_name}: HSP task parameters invalid JSON."
                except Exception as e: response_text = f"{ai_name}: Error dispatching HSP task: {e}"
            else: response_text = f"{ai_name}: HSP task command malformed."
            # Fall through to store this response

        if crisis_level > 0 and not response_text: # Crisis response if no other response yet
            response_text = self.config.get("crisis_response_text", f"{ai_name}: Sensitive situation. Please seek appropriate support.") # type: ignore
            self.emotion_system.update_emotion_based_on_input({"text": user_input})

        if not response_text: # If still no response, proceed to formula/LLM/HSP fallback
            self.emotion_system.update_emotion_based_on_input({"text": user_input})
            matched_formula = self.formula_engine.match_input(user_input)
            attempt_hsp_fallback = False
            hsp_capability_query = user_input # Default for direct HSP fallback
            hsp_params = {"query": user_input}

            if matched_formula:
                # Construct context for formula engine
                context_for_formula: Dict[str, Any] = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "ai_name": ai_name,
                    # TODO: Add more context like current emotion, time, etc. later if needed by templates
                }
                # Remove None keys from context to avoid issues with .format if templates aren't robust
                context_for_formula = {k: v for k, v in context_for_formula.items() if v is not None}

                formula_result = self.formula_engine.execute_formula(matched_formula, context=context_for_formula)
                action_name = formula_result.get("action_name")
                action_params = formula_result.get("action_params", {}) # Ensure action_params is a dict

                if action_name == "dispatch_tool":
                    tool_name = action_params.get("tool_name") # Get tool_name from action_params
                    tool_query_template = action_params.get("tool_query") # Get tool_query from action_params
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
                    # Ensure action_params is used for formatting tool_query if it's a template string
                    # And also for passing to tool_dispatcher
                    current_context_for_tool_query = action_params.copy() # Start with formula params
                    current_context_for_tool_query.update(context_for_formula) # Add DM context

                    tool_query = str(tool_query_template)
                    if isinstance(tool_query_template, str):
                        try:
                            tool_query = tool_query_template.format(**current_context_for_tool_query)
                        except KeyError as e:
                            print(f"DM: KeyError formatting tool_query '{tool_query_template}' for tool '{tool_name}'. Missing key: {e}. Using raw template.")
                            # tool_query remains the raw template string
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======

>>>>>>> Stashed changes
=======

>>>>>>> Stashed changes
                    if tool_name and tool_query:
                        # Pass all action_params to the dispatcher, it can pick what it needs
                        tool_res = self.tool_dispatcher.dispatch(query=tool_query, explicit_tool_name=tool_name, **action_params)
                        if tool_res["status"] == "success": response_text = f"{ai_name}: {tool_res['payload']}"
                        elif tool_res["status"] in ["unhandled_by_local_tool", "failure_tool_error"]:
                            attempt_hsp_fallback, hsp_capability_query, hsp_params = True, tool_name, {k:v for k,v in action_params.items() if k not in ["tool_name", "tool_query"]}
                        else: response_text = f"{ai_name}: Issue with '{tool_name}' tool: {tool_res.get('error_message', 'unknown')}"
                    else: response_text = f"{ai_name}: Formula '{matched_formula.get('name')}' tool dispatch error (missing tool_name or tool_query)."
                elif action_name == "initiate_tool_draft":
                    response_text = await self.handle_draft_tool_request(action_params.get("tool_name",""), action_params.get("description_for_llm",""), session_id)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
                else: # Non-dispatch_tool, non-initiate_tool_draft formula actions
=======
=======
>>>>>>> Stashed changes
                elif action_name == "generate_response_via_module_bus": # New action for ModuleBus
                    module_id = action_params.get("module_id")
                    module_input = action_params.get("module_input", {})
                    if self.module_bus_controller and module_id:
                        try:
                            # Execute the module via ModuleBus
                            module_output = await self.module_bus_controller.execute_module(module_id, module_input)
                            response_text = f"{ai_name}: ModuleBus response: {module_output.get('response_text', 'No response text from module.')}"
                            if module_output.get('additional_info'):
                                response_text += f" (Info: {module_output['additional_info']})"
                        except ModuleExecutionError as mee:
                            response_text = f"{ai_name}: Error executing ModuleBus module '{module_id}': {mee}"
                        except ModuleAssemblyError as mae:
                            response_text = f"{ai_name}: Error assembling ModuleBus module '{module_id}': {mae}"
                        except Exception as e:
                            response_text = f"{ai_name}: Unexpected error with ModuleBus module '{module_id}': {e}"
                    else:
                        response_text = f"{ai_name}: ModuleBus controller not available or module_id missing for response generation."
                else: # Non-dispatch_tool, non-initiate_tool_draft, non-module_bus formula actions
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                    formatted_response_from_engine = formula_result.get("formatted_response")
                    if formatted_response_from_engine and isinstance(formatted_response_from_engine, str):
                        response_text = f"{ai_name}: {formatted_response_from_engine}" # Prepend AI name if template doesn't include it
                    elif action_name: # Fallback if no formatted_response
                        response_text = f"{ai_name}: Action '{action_name}' triggered."
                    else: # Fallback if no action_name either (should not happen for valid formulas)
                        response_text = f"{ai_name}: Recognized pattern: '{matched_formula.get('name')}'."
            else: # No formula matched
                attempt_hsp_fallback = True

            if attempt_hsp_fallback and not response_text and self.service_discovery_module and self.hsp_connector:
                found_caps = self.service_discovery_module.find_capabilities(capability_name_filter=hsp_capability_query, sort_by_trust=True) or \
                             self.service_discovery_module.find_capabilities(tags_filter=[hsp_capability_query], sort_by_trust=True)
                if found_caps:
                    selected_cap = found_caps[0]
                    user_facing_msg, _ = await self._dispatch_hsp_task_request(selected_cap, hsp_params, user_input, user_id, session_id)
                    if user_facing_msg: response_text = f"{ai_name}: {user_facing_msg}"
                # If no HSP cap found, response_text remains empty, falls to LLM

            if not response_text: # LLM Fallback
                print("DialogueManager: No formula or HSP. Using LLM.")
                # Build context string... (simplified for brevity)
                session_history_str = "\n".join([f"{t['speaker']}: {t['text']}" for t in self.active_sessions.get(session_id, [])])
                prompt_context_for_llm = f"Conversation history:\n{session_history_str}\n\nUser query: {user_input}"

                initial_llm_response_text = self.llm_interface.generate_response(prompt=prompt_context_for_llm)
                response_text = f"{ai_name}: {initial_llm_response_text}"

                # Proactive HSP fact query
                enable_proactive_query, proactive_query_cap_name = False, "Mock Fact Query Service"
                if isinstance(self.config, dict) and isinstance(self.config.get("operational_configs"), dict):
                    op_conf = self.config.get("operational_configs",{})
                    enable_proactive_query = op_conf.get("enable_proactive_hsp_fact_query", False)
                    proactive_query_cap_name = op_conf.get("proactive_hsp_fact_query_capability_name", proactive_query_cap_name)

                if enable_proactive_query and (len(initial_llm_response_text) < 50 or any(kw in initial_llm_response_text.lower() for kw in ["not sure", "don't know"])) \
                   and self.service_discovery_module and self.hsp_connector:
                    found_fact_services = self.service_discovery_module.find_capabilities(capability_name_filter=proactive_query_cap_name, sort_by_trust=True)
                    if found_fact_services:
                        _, proactive_corr_id = await self._dispatch_hsp_task_request(
                            found_fact_services[0], {"query_text": user_input, "max_results": 2},
                            f"Proactive fact query for: {user_input}", user_id, session_id, "proactive_fact_query")
                        if proactive_corr_id: print(f"DialogueManager: Proactive HSP fact query dispatched (CorrID: {proactive_corr_id}).")

        # Final response processing (emotion, critique)
        emotion_expression = self.emotion_system.get_current_emotion_expression()
        response_text = f"{response_text}{emotion_expression.get('text_ending', '')}" if emotion_expression.get('text_ending') else response_text

        if self.self_critique_module:
            critique_result = self.self_critique_module.critique_interaction(user_input, response_text, self.active_sessions.get(session_id, []))

        # Store AI response
        if self.memory_manager:
            ai_metadata: DialogueMemoryEntryMetadata = {"speaker": "ai", "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "session_id": session_id} # type: ignore
            if user_mem_id: ai_metadata["user_input_ref"] = user_mem_id
            if critique_result and critique_result["score"] >= self.min_critique_score_to_store:
                ai_metadata["critique"] = critique_result
            self.memory_manager.store_experience(response_text, "ai_dialogue_text", ai_metadata)

        if session_id: # Update active_sessions
            self.active_sessions.setdefault(session_id, []).append(DialogueTurn(speaker="user", text=user_input))
            self.active_sessions[session_id].append(DialogueTurn(speaker="ai", text=response_text))
            self.active_sessions[session_id] = self.active_sessions[session_id][-self.max_history_per_session:]

        return response_text

    async def start_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        print(f"DialogueManager: New session started for user '{user_id or 'anonymous'}', session_id: {session_id}.")
        if session_id: self.active_sessions[session_id] = []
        base_prompt = self.personality_manager.get_initial_prompt()
        time_segment = self.time_system.get_time_of_day_segment()
        greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello,"}
        return f"{greetings.get(time_segment, '')} {base_prompt}".strip()

    async def handle_draft_tool_request(self, tool_name: str, purpose_and_io_desc: str, session_id: Optional[str] = None) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")
        io_parsing_prompt = self._construct_io_parsing_prompt(purpose_and_io_desc)
        raw_io_details_str = self.llm_interface.generate_response(prompt=io_parsing_prompt, params={"temperature": 0.1})

        parsed_io_details: Optional[ParsedToolIODetails] = None
        try:
            json_match = re.search(r"```json\s*([\s\S]*?)\s*```|[\s\S]*", raw_io_details_str, re.DOTALL)
            # Guard against json_match being None before calling .group or .strip
            json_str_candidate = ""
            if json_match:
                group1 = json_match.group(1)
                group2 = json_match.group(2)
                json_str_candidate = (group1 if group1 is not None else group2 if group2 is not None else "").strip()

            if not json_str_candidate: raise ValueError("Empty JSON string from LLM for I/O parsing.")
            parsed_io_details = json.loads(json_str_candidate)
            # Basic validation of ParsedToolIODetails structure
            if not all(k in parsed_io_details for k in ["suggested_method_name", "parameters", "return_type"]): # type: ignore
                 raise ValueError("Parsed I/O details missing required fields.")
            print(f"DialogueManager: Parsed I/O details: {parsed_io_details}")
        except (json.JSONDecodeError, ValueError) as e:
            return f"{ai_name}: Error structuring tool details for '{tool_name}': {e}. Raw: '{raw_io_details_str}'"

        if not parsed_io_details:
            # This case should ideally be caught by the exception block if json_str_candidate is empty.
            # However, as a safeguard or if validation above fails in a way that doesn't raise ValueError but leaves parsed_io_details as None.
            return f"{ai_name}: Couldn't structure I/O for '{tool_name}' (details remained None after parsing attempt)."

        code_gen_prompt = self._construct_code_generation_prompt(
            tool_name, parsed_io_details.get("class_docstring_hint", purpose_and_io_desc), # type: ignore
            parsed_io_details["suggested_method_name"], # type: ignore
            parsed_io_details.get("method_docstring_hint", f"Executes {tool_name}."), # type: ignore
            parsed_io_details["parameters"], return_type=parsed_io_details["return_type"] # type: ignore
        )
        generated_code_text = self.llm_interface.generate_response(prompt=code_gen_prompt, params={"temperature": 0.3})

        validation_message, is_syntactically_valid = "", False
        try:
            ast.parse(generated_code_text.strip()); validation_message = "\nInfo: Syntactically valid."; is_syntactically_valid = True
        except SyntaxError as e: validation_message = f"\nWarning: Syntax error (line {e.lineno}): {e.msg}"
        except Exception as e: validation_message = f"\nWarning: Syntax validation error: {str(e)[:100]}"

        sandbox_output_message = ""
        if is_syntactically_valid and self.sandbox_executor:
            params_info = parsed_io_details.get("parameters", [])
            placeholder_params: Dict[str, Any] = {
                p["name"] : p.get("default") if "default" in p else (
                    "test_string" if "str" in str(p.get("type","")).lower() else
                    0 if "int" in str(p.get("type","")).lower() else
                    0.0 if "float" in str(p.get("type","")).lower() else
                    False if "bool" in str(p.get("type","")).lower() else
                    [] if "list" in str(p.get("type","")).lower() else
                    {} if "dict" in str(p.get("type","")).lower() else None)
                for p in params_info if isinstance(p, dict) and "name" in p and p["name"] not in ["self", "cls"]
            }
            res, err = self.sandbox_executor.run(generated_code_text.strip(), tool_name, parsed_io_details["suggested_method_name"], placeholder_params) # type: ignore
            sandbox_output_message = f"\n---Sandbox Test Run---\nResult: {str(res)[:500]}\nError: {str(err)[:500]}" if err else f"\n---Sandbox Test Run---\nResult: {str(res)[:1000]}"

        return f"{ai_name}: Draft for `{tool_name}`:\n```python\n{generated_code_text.strip()}\n```\n{validation_message}{sandbox_output_message}\nReview carefully."

    def _construct_io_parsing_prompt(self, purpose_and_io_desc: str) -> str:
        # (Prompt content remains the same)
        prompt = f"""
You are an expert Python code analyst. Your task is to parse a natural language description of a tool's desired functionality and extract structured information about its primary execution method, parameters, and return value. Output this information as a valid JSON object.

Guidelines for extraction:
1.  `suggested_method_name`: Suggest a concise, Pythonic method name (e.g., "execute", "run", or a verb phrase like "process_data", "calculate_sum") based on the tool's purpose. Use snake_case.
2.  `class_docstring_hint`: Provide a brief summary suitable for a class docstring, based on the overall tool purpose.
3.  `method_docstring_hint`: Provide a brief summary suitable for the primary method's docstring.
4.  `parameters`: This should be a list of JSON objects. Each object represents a parameter and should have:
    *   `"name"`: The parameter name (snake_case).
    *   `"type"`: The inferred Python type hint as a string (e.g., "str", "int", "float", "bool", "List[str]", "Dict[str, Any]", "Optional[int]"). Use `typing` module types where appropriate (e.g., `Optional`, `List`, `Dict`, `Any`). If a parameter is described as optional and no default is given, its type should be `Optional[...]`.
    *   `"default"`: (Optional field) If a default value is mentioned, include it. Represent numbers as numbers, booleans as booleans, and strings as strings in the JSON. For `None` default with `Optional` type, you can omit the default field or set it to `null`.
    *   `"description"`: A brief description of the parameter.
5.  `return_type`: The inferred Python type hint for the return value as a string. If no specific return is mentioned or it's complex, use "Any" or "str" as a sensible default.
6.  `return_description`: A brief description of what the method returns.

If the description is too vague to extract some details, use your best judgment to provide sensible placeholders or omit optional fields (like "default"). Strive for valid Python type hint syntax for "type" fields.

Here are a few examples of input descriptions and their desired JSON output:

---
Input Description 1:
"reverses a given input string named 'text_to_reverse' and returns the reversed string."

Desired JSON Output 1:
```json
{{
  "suggested_method_name": "reverse_string",
  "class_docstring_hint": "A tool to reverse strings.",
  "method_docstring_hint": "Reverses the provided input string.",
  "parameters": [
    {{"name": "text_to_reverse", "type": "str", "description": "The string to be reversed."}}
  ],
  "return_type": "str",
  "return_description": "The reversed string."
}}
```
---
Input Description 2:
"calculates the sum of a list of numbers. The list is called 'numbers_list'. It should also take an optional boolean flag 'as_float' which defaults to false, to return a float. The result is the sum."

Desired JSON Output 2:
```json
{{
  "suggested_method_name": "calculate_sum",
  "class_docstring_hint": "A tool to calculate the sum of a list of numbers.",
  "method_docstring_hint": "Calculates the sum of a list of numbers, optionally returning the sum as a float.",
  "parameters": [
    {{"name": "numbers_list", "type": "List[Union[int, float]]", "description": "A list of numbers to sum."}},
    {{"name": "as_float", "type": "bool", "default": false, "description": "If true, returns the sum as a float, otherwise as int/float based on input."}}
  ],
  "return_type": "Union[int, float]",
  "return_description": "The sum of the numbers in the list."
}}
```
---
Input Description 3:
"a tool that takes a user's name and their age. The name is a string, age is an integer. It just prints them."

Desired JSON Output 3:
```json
{{
  "suggested_method_name": "display_user_info",
  "class_docstring_hint": "A tool to display user information.",
  "method_docstring_hint": "Takes a user's name and age and prepares them for display.",
  "parameters": [
    {{"name": "name", "type": "str", "description": "The user's name."}},
    {{"name": "age", "type": "int", "description": "The user's age."}}
  ],
  "return_type": "str",
  "return_description": "A string confirming the action or the formatted info."
}}
```
---

Now, parse the following tool description:

Input Description:
"{purpose_and_io_desc}"

Desired JSON Output:
"""
        return prompt.replace("{{", "{").replace("}}", "}")

    def _construct_code_generation_prompt(self, tool_name: str, class_docstring: str,
                                        method_name: str, method_docstring: str,
                                        parameters: List[Dict[str, Any]], return_type: str) -> str:
        # (Prompt content remains the same)
        # example_tool_structure = """
        # Example of a simple Python tool class structure:
        #
        # ```python
        # from typing import Optional, List, Dict, Any # Common imports
        #
        # class ExampleTool:
        #     """Provides a brief description of what the tool does."""
        #
        #     def __init__(self, config: Optional[Dict[str, Any]] = None):
        #         """Initializes the tool, optionally with configuration."""
        #         self.config = config or {}
        #         print(f"{self.__class__.__name__} initialized.")
        #
        #     def execute(self, parameter_one: str, parameter_two: int = 0) -> Dict[str, Any]:
        #         """
        #         Describes what this main method does.
        #
        #         Args:
        #             parameter_one (str): Description of first parameter.
        #             parameter_two (int, optional): Description of second parameter. Defaults to 0.
        #
        #         Returns:
        #             Dict[str, Any]: Description of the output, often a dictionary.
        #         """
        #         print(f"Executing {self.__class__.__name__} with {parameter_one=}, {parameter_two=}")
        #         # TODO: Implement actual tool logic here
        #         # Replace 'pass' with your logic or raise NotImplementedError
        #         raise NotImplementedError("Tool logic not implemented yet.")
        #         # Example return:
        #         # return {"status": "success", "result": f"Processed {parameter_one} and {parameter_two}"}
        # ```
        # """
        print(f"Executing {self.__class__.__name__} with {parameter_one=}, {parameter_two=}")
        # TODO: Implement actual tool logic here
        # Replace 'pass' with your logic or raise NotImplementedError
        raise NotImplementedError("Tool logic not implemented yet.")
        # Example return:
        # return {"status": "success", "result": f"Processed {parameter_one} and {parameter_two}"}
```
"""

```
        print(f"Executing {self.__class__.__name__} with {parameter_one=}, {parameter_two=}")
        # TODO: Implement actual tool logic here
        # Replace 'pass' with your logic or raise NotImplementedError
        raise NotImplementedError("Tool logic not implemented yet.")
        # Example return:
        # return {"status": "success", "result": f"Processed {parameter_one} and {parameter_two}"}
```
"""
        param_str_list = []
        for p_info in parameters: # p_info is now ToolParameterDetail compatible
            p_name = p_info.get("name", "param")
            p_type = p_info.get("type", "Any")
            param_str = f"{p_name}: {p_type}"
            if "default" in p_info:
                default_val = p_info["default"]
                param_str += f" = {repr(default_val)}" # Use repr for safer default value string
            param_str_list.append(param_str)

        method_signature_params = ", ".join(param_str_list)
        if not method_signature_params.startswith("self") and not method_name == "__init__":
             method_signature_params = "self" + (f", {method_signature_params}" if method_signature_params else "")

        prompt = f"""
You are an expert Python programmer assisting in drafting tool skeletons for an AI framework.
Your task is to generate a Python class for a new tool based on the provided specifications.

Tool Specifications:
- Tool Class Name: {tool_name}
- Class Docstring: {class_docstring}

- Method Name: {method_name}
- Method Docstring: {method_docstring}
- Method Parameters (for signature): {method_signature_params}
- Method Return Type: {return_type}

Instructions for the generated code:
1. The tool should be a single Python class named '{tool_name}'.
2. The class docstring should be: """{class_docstring}"""
3. The primary execution method should be named '{method_name}'.
4. The method signature should be: `def {method_name}({method_signature_params}) -> {return_type}:`
5. The method docstring should be: """{method_docstring}"""
   (Ensure Args and Returns sections are appropriate if parameter details were rich enough).
6. The body of this primary method should be `raise NotImplementedError("Tool logic not implemented yet.")`.
7. Include an `__init__` method: `def __init__(self, config: Optional[Dict[str, Any]] = None):`. Its docstring should be "Initializes the tool, optionally with configuration.". It should store the config and print an initialization message.
8. Include necessary imports from `typing` (e.g., `Optional`, `List`, `Dict`, `Any`) if used in type hints.

{example_tool_structure}

Based on these structured specifications, please generate *only* the complete Python code for the class.
Start with any necessary imports, then the class definition. Do not include any explanatory text before or after the Python code block.
"""
        return prompt


if __name__ == '__main__':
    import asyncio
    import json
    from core_ai.personality.personality_manager import PersonalityManager
    from tools.tool_dispatcher import ToolDispatcher
    from services.llm_interface import LLMInterface, LLMInterfaceConfig
    from core_ai.learning.self_critique_module import SelfCritiqueModule
    from core_ai.learning.fact_extractor_module import FactExtractorModule
    from core_ai.learning.learning_manager import LearningManager
    from shared.types.common_types import OperationalConfig

    async def main_dm_test():
        test_op_configs_dict: OperationalConfig = { # type: ignore
            "timeouts": {
                "llm_general_request": 10, "llm_critique_request": 8, "llm_fact_extraction_request": 8,
                "dialogue_manager_turn": 30,
                "llm_ollama_request": 60,
                "llm_ollama_list_models_request": 10
            },
            "learning_thresholds": {"min_fact_confidence_to_store": 0.7, "min_critique_score_to_store": 0.25}
        }

        full_config_for_dm: OperationalConfig = { # type: ignore
             "operational_configs": test_op_configs_dict,
             "max_dialogue_history": 10, # Example top-level config for DM
             # Add other DM specific top-level configs if any
        }


        ollama_llm_config_for_dm_test: LLMInterfaceConfig = { # type: ignore
            "default_provider": "ollama",
            "default_model": "nous-hermes2:latest",
            "providers": {
                "ollama": {"base_url": "http://localhost:11434"}
            },
            "default_generation_params": {"temperature": 0.7},
            "operational_configs": test_op_configs_dict
        }
        actual_llm_interface_for_dm = LLMInterface(config=ollama_llm_config_for_dm_test)
        pm = PersonalityManager()
        test_ham_file = f"dialogue_manager_test_ham_{uuid.uuid4().hex}.json"
        memory_manager_inst = HAMMemoryManager(core_storage_filename=test_ham_file)

        # For testing, we might not have SDM or HSPConnector fully set up.
        # Pass None for them if they are not essential for the specific tests below.
        dm = DialogueManager(
            personality_manager=pm,
            memory_manager=memory_manager_inst,
            llm_interface=actual_llm_interface_for_dm,
            config=full_config_for_dm, # Pass the OperationalConfig typed config
            # service_discovery_module=None, # Example if not testing HSP tasks
            # hsp_connector=None             # Example if not testing HSP tasks
        )

        print(f"\n--- Test: Basic Interaction & Formula (Ollama LLM where applicable) ---")
        # ... (rest of the __main__ test block as before) ...
        # (Ensure any part of __main__ that uses self.config directly is updated if self.config structure changed)
        # For example, crisis_system and time_system take `config=dict(self.config)`.
        # LLMInterface also takes `config=self.config`.
        # If self.config is now `OperationalConfig`, these might need adjustment or
        # OperationalConfig needs to be dict-like or provide a .get() method.
        # `OperationalConfig` is a TypedDict, so it is dict-like.

        test_session_id_1 = "session_basic_001"
        test_user_id_1 = "user_basic_001"
        print(await dm.start_session(user_id=test_user_id_1, session_id=test_session_id_1))

        user_msg = "Hello Miko" # Should trigger formula
        ai_reply = await dm.get_simple_response(user_msg, session_id=test_session_id_1, user_id=test_user_id_1)
        print(f"User: {user_msg}\nAI: {ai_reply}")
        assert "Hello! I am Miko (Base). How can I help you today?" in ai_reply

        print("\n--- Test: Learning and Using Learned Facts ---")
        # ... (rest of learning test)

        print("\n--- Test: Tool Dispatch via Formula ---")
        # ... (rest of tool dispatch test)

        print("\n--- Test: Content Analysis and KG Prompt Augmentation ---")
        # ... (rest of KG analysis test)

        print("\n--- Test: New CONCEPT Node and 'is_a' relationship via !analyze ---")
        # ... (rest of concept node test)

        print("\nDialogueManager tests finished (using Ollama where LLM is involved).")

        if os.path.exists(memory_manager_inst.core_storage_filepath):
            try: os.remove(memory_manager_inst.core_storage_filepath); print(f"Cleaned up {memory_manager_inst.core_storage_filepath}")
            except Exception as e: print(f"Error cleaning up test HAM file: {e}")

    asyncio.run(main_dm_test())