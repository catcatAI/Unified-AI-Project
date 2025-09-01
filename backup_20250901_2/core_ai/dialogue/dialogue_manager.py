"""
对话管理器
负责管理对话流程，包括意图识别、响应生成和会话管理
"""

import logging
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime, timezone

from apps.backend.src.core_ai.personality.personality_manager import PersonalityManager
from apps.backend.src.core_ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.services.multi_llm_service import MultiLLMService
from apps.backend.src.core_ai.emotion_system import EmotionSystem
from apps.backend.src.core_ai.crisis_system import CrisisSystem
from apps.backend.src.core_ai.time_system import TimeSystem
from apps.backend.src.core_ai.formula_engine import FormulaEngine
from apps.backend.src.tools.tool_dispatcher import ToolDispatcher
from apps.backend.src.core_ai.learning.learning_manager import LearningManager
from apps.backend.src.core_ai.service_discovery.service_discovery_module import ServiceDiscoveryModule
from apps.backend.src.services.sandbox_executor import SandboxExecutor
import networkx as nx
from apps.backend.src.shared.types.common_types import (
    OperationalConfig, DialogueTurn, DialogueMemoryEntryMetadata
)

from apps.backend.src.hsp.types import HSPTaskResultPayload, HSPMessageEnvelope
from apps.backend.src.core_ai.dialogue.project_coordinator import ProjectCoordinator
from apps.backend.src.core_ai.agent_manager import AgentManager

if TYPE_CHECKING:
    from apps.backend.src.hsp.connector import HSPConnector

class DialogueManager:
    def __init__(self,
                 ai_id: str,
                 personality_manager: PersonalityManager,
                 memory_manager: HAMMemoryManager,
                 llm_interface: MultiLLMService,
                 emotion_system: EmotionSystem,
                 crisis_system: CrisisSystem,
                 time_system: TimeSystem,
                 formula_engine: FormulaEngine,
                 tool_dispatcher: ToolDispatcher,
                 learning_manager: LearningManager,
                 service_discovery_module: ServiceDiscoveryModule,
                 hsp_connector: Optional[HSPConnector],
                 agent_manager: Optional[AgentManager],
                 config: Optional[OperationalConfig] = None,
                 **kwargs): # Catch other services that might be passed

        self.ai_id = ai_id
        self.personality_manager = personality_manager
        self.memory_manager = memory_manager
        self.llm_interface = llm_interface
        self.emotion_system = emotion_system
        self.crisis_system = crisis_system
        self.time_system = time_system
        self.formula_engine = formula_engine
        self.tool_dispatcher = tool_dispatcher
        self.learning_manager = learning_manager
        self.service_discovery = service_discovery_module # Store service_discovery_module
        self.hsp_connector = hsp_connector # Store hsp_connector
        self.config = config or {}

        # Load command triggers from config with defaults
        self.triggers = self.config.get("command_triggers", {
            "complex_project": "project:",
            "manual_delegation": "!delegate_to",
            "context_analysis": "!analyze:"
        })

        self.active_sessions: Dict[str, List[DialogueTurn]] = {}
        self.pending_hsp_task_requests: Dict[str, Dict[str, Any]] = {} # Initialize pending_hsp_task_requests
        
        # Initialize ProjectCoordinator
        self.project_coordinator = ProjectCoordinator(
            llm_interface=self.llm_interface,
            service_discovery=self.service_discovery,
            hsp_connector=self.hsp_connector,
            agent_manager=agent_manager,
            memory_manager=self.memory_manager,
            learning_manager=self.learning_manager,
            personality_manager=self.personality_manager,
            dialogue_manager_config=self.config
        )

        if self.hsp_connector:
            self.hsp_connector.register_on_task_result_callback(self._handle_incoming_hsp_task_result)

    async def _handle_incoming_hsp_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope) -> None:
        """
        Receives all task results and delegates them to the ProjectCoordinator.
        """
        if self.project_coordinator:
            await self.project_coordinator.handle_task_result(result_payload, sender_ai_id, envelope)
        else:
            logging.warning(f"[{self.ai_id}] Received HSP task result but ProjectCoordinator is not available.")

    async def get_simple_response(self, user_input: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI")

        # --- Intent Classification ---
        # Use triggers from config to activate special handlers
        if self.project_coordinator and user_input.lower().startswith(self.triggers["complex_project"]):
            project_query = user_input[len(self.triggers["complex_project"]):].strip()
            logging.info(f"[{self.ai_id}] Complex project detected. Delegating to ProjectCoordinator...")
            return await self.project_coordinator.handle_project(project_query, session_id, user_id)

        # --- Existing Simple Response Flow ---
        # This is a simplified version of the original extensive logic.
        # A full implementation would include formula matching, single tool dispatch, etc.
        
        try:
            # Attempt to dispatch a tool based on user input
            history = self.active_sessions.get(session_id, []) if session_id else []
            # 确保在调用tool_dispatcher.dispatch时传递history参数
            tool_response = await self.tool_dispatcher.dispatch(user_input, session_id=session_id, user_id=user_id, history=history)

            response_text = ""
            if tool_response['status'] == "success":
                response_text = tool_response['payload']
            elif tool_response['status'] == "no_tool_found" or tool_response['status'] == "no_tool_inferred":
                response_text = f"{ai_name}: You said '{user_input}'. This is a simple response."
            else:
                response_text = f"{ai_name}: I'm sorry, I encountered an error while trying to understand your request."
        except Exception as e:
            logging.error(f"Error dispatching tool: {e}")
            response_text = f"{ai_name}: I'm sorry, I encountered an error while trying to understand your request."

        # Store user and AI turns in session and memory
        if session_id and session_id in self.active_sessions:
            self.active_sessions[session_id].append(DialogueTurn(speaker="user", text=user_input, timestamp=datetime.now(timezone.utc)))
            self.active_sessions[session_id].append(DialogueTurn(speaker="ai", text=response_text, timestamp=datetime.now(timezone.utc)))

        # Always store in memory if memory manager is available, regardless of session
        if self.memory_manager:
            user_metadata: DialogueMemoryEntryMetadata = {"speaker": "user", "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "session_id": session_id} # type: ignore
            user_mem_id = self.memory_manager.store_experience(user_input, "user_dialogue_text", user_metadata)

            ai_metadata: DialogueMemoryEntryMetadata = {"speaker": "ai", "timestamp": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "session_id": session_id, "user_input_ref": user_mem_id} # type: ignore
            self.memory_manager.store_experience(response_text, "ai_dialogue_text", ai_metadata)

        # Analyze for personality adjustment
        if self.learning_manager:
            adjustment = await self.learning_manager.analyze_for_personality_adjustment(user_input)
            if adjustment and self.personality_manager:
                self.personality_manager.apply_personality_adjustment(adjustment)

        return response_text

    async def start_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
        logging.info(f"DialogueManager: New session started for user '{user_id or 'anonymous'}', session_id: {session_id}.")
        self.active_sessions[session_id] = []
        base_prompt = self.personality_manager.get_initial_prompt()
        time_segment = self.time_system.get_time_of_day_segment()
        greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello,"}
        return f"{greetings.get(time_segment, '')} {base_prompt}".strip()

    async def _dispatch_hsp_task_request(self, capability_advertisement, request_parameters, original_user_query, user_id, session_id, request_type="api_initiated_hsp_task"):
        """
        Dispatch an HSP task request and return (user_message, correlation_id)
        """
        try:
            if not self.hsp_connector or not self.hsp_connector.is_connected:
                return ("HSP connector is not available or not connected.", None)
            
            # Generate correlation ID
            correlation_id = str(uuid.uuid4())
            
            # Store pending request
            self.pending_hsp_task_requests[correlation_id] = {
                "capability_id": capability_advertisement.get("capability_id"),
                "target_ai_id": capability_advertisement.get("ai_id"),
                "parameters": request_parameters,
                "user_id": user_id,
                "session_id": session_id,
                "request_type": request_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Send task via HSP connector
            success = await self.hsp_connector.send_task_request(
                target_ai_id=capability_advertisement.get("ai_id"),
                capability_id=capability_advertisement.get("capability_id"),
                parameters=request_parameters,
                correlation_id=correlation_id
            )
            
            if success:
                return (f"Task request sent successfully to {capability_advertisement.get('ai_id')}", correlation_id)
            else:
                # Remove from pending if send failed
                self.pending_hsp_task_requests.pop(correlation_id, None)
                return ("Failed to send task request via HSP", None)
                
        except Exception as e:
            logging.error(f"Error dispatching HSP task: {e}")
            return (f"Error dispatching task: {str(e)}", None)