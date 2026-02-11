"""
对话管理器
负责管理对话流程, 包括意图识别、响应生成和会话管理
"""

import logging
import uuid
import json
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from ai.personality.personality_manager import PersonalityManager
from ai.memory.ham_memory.ham_manager import HAMMemoryManager
from core.services.multi_llm_service import MultiLLMService, ChatMessage
from ai.emotion.emotion_system import EmotionSystem
from ai.crisis.crisis_system import CrisisSystem
from ai.time.time_system import TimeSystem
from ai.formula_engine import FormulaEngine
from ai.learning.learning_manager import LearningManager
from ai.discovery.service_discovery_module import ServiceDiscoveryModule
from core.shared.types.common_types import OperationalConfig, DialogueTurn, DialogueMemoryEntryMetadata
from core.hsp.payloads import HSPTaskResultPayload, HSPMessageEnvelope
from ai.dialogue.project_coordinator import ProjectCoordinator
from managers.agent_manager import AgentManager
from core.hsp.connector import HSPConnector

# ToolDispatcher import might be needed if not provided by components
try:
    from src.ai.tools.tool_dispatcher import ToolDispatcher
except ImportError:
    ToolDispatcher = Any

logger = logging.getLogger(__name__)

class DialogueManager:
    """
    对话管理器 - 管理对话流程, 包括意图识别、响应生成和会话管理
    """

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
                 hsp_connector: Optional[HSPConnector] = None,
                 agent_manager: Optional[AgentManager] = None,
                 config: Optional[OperationalConfig] = None, 
                 **kwargs) -> None:

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
        self.service_discovery = service_discovery_module
        self.hsp_connector = hsp_connector
        self.agent_manager = agent_manager
        self.config = config or {}

        # Load command triggers from config with defaults
        self.triggers = self.config.get("command_triggers", {
            "complex_project": "project:",
            "manual_delegation": "!delegate_to",
            "context_analysis": "!analyze:"
        })

        self.active_sessions: Dict[str, List[DialogueTurn]] = {}
        self.pending_hsp_task_requests: Dict[str, Dict[str, Any]] = {}

        # Initialize ProjectCoordinator
        self.project_coordinator = ProjectCoordinator(
            llm_interface=self.llm_interface,
            service_discovery=self.service_discovery,
            hsp_connector=self.hsp_connector,
            agent_manager=self.agent_manager,
            memory_manager=self.memory_manager,
            learning_manager=self.learning_manager,
            personality_manager=self.personality_manager,
            dialogue_manager_config=self.config
        )

        if self.hsp_connector:
            self.hsp_connector.register_on_task_result_callback(self._handle_incoming_hsp_task_result)

    async def _handle_incoming_hsp_task_result(self, 
                                            result_payload: HSPTaskResultPayload, 
                                            sender_ai_id: str, 
                                            envelope: HSPMessageEnvelope) -> None:
        """
        Receives all task results and delegates them to the ProjectCoordinator.
        """
        if self.project_coordinator:
            await self.project_coordinator.handle_task_result(result_payload, sender_ai_id, envelope)
        else:
            logger.warning(f"[{self.ai_id}] Received HSP task result but ProjectCoordinator is not available.")

    async def get_simple_response(self, user_input: str, 
                                session_id: Optional[str] = None, 
                                user_id: Optional[str] = None) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI") or "AI"

        # Intent Classification
        if self.project_coordinator and user_input.lower().startswith(self.triggers["complex_project"]):
            project_query = user_input[len(self.triggers["complex_project"]):].strip()
            logger.info(f"[{self.ai_id}] Complex project detected. Delegating to ProjectCoordinator...")
            return await self.project_coordinator.handle_project(project_query, session_id, user_id)

        # Simple Response Flow
        try:
            history = self.active_sessions.get(session_id, []) if session_id else []
            tool_response = await self.tool_dispatcher.dispatch(user_input, 
                                                              session_id=session_id, 
                                                              user_id=user_id, 
                                                              history=history)

            if tool_response['status'] == "success":
                response_text = tool_response.get('payload', "")
            elif tool_response['status'] in ["no_tool_found", "no_tool_inferred"]:
                response_text = await self.generate_intelligent_response(user_input, session_id, user_id, ai_name)
            else:
                response_text = f"{ai_name}: I'm sorry, I encountered an error while trying to understand your request."
        except Exception as e:
            logger.error(f"Error dispatching tool: {e}")
            response_text = f"{ai_name}: I apologize, but something went wrong while processing your request."

        # Store in session
        if session_id:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = []
            
            timestamp = datetime.now(timezone.utc).isoformat()
            self.active_sessions[session_id].append(DialogueTurn(speaker="user", text=user_input, timestamp=timestamp))
            self.active_sessions[session_id].append(DialogueTurn(speaker="ai", text=response_text, timestamp=timestamp))

        # Store in memory
        if self.memory_manager:
            timestamp = datetime.now(timezone.utc).isoformat()
            user_metadata: DialogueMemoryEntryMetadata = {
                "speaker": "user", 
                "timestamp": timestamp, 
                "user_id": user_id, 
                "session_id": session_id
            }
            user_mem_id = self.memory_manager.store_experience(user_input, "user_dialogue_text", user_metadata)

            ai_metadata: DialogueMemoryEntryMetadata = {
                "speaker": "ai", 
                "timestamp": timestamp, 
                "user_id": user_id, 
                "session_id": session_id, 
                "user_input_ref": user_mem_id
            }
            self.memory_manager.store_experience(response_text, "ai_dialogue_text", ai_metadata)

        # Analyze for personality adjustment
        if self.learning_manager:
            adjustment = await self.learning_manager.analyze_for_personality_adjustment(user_input)
            if adjustment and self.personality_manager:
                self.personality_manager.apply_personality_adjustment(adjustment)

        return response_text

    async def generate_intelligent_response(self, user_input: str, 
                                         session_id: Optional[str], 
                                         user_id: Optional[str], 
                                         ai_name: str) -> str:
        """生成真实的智能响应, 使用LLM进行推理"""
        try:
            # Context gathering
            user_context = ""
            if self.memory_manager and user_id:
                user_memories = await self.memory_manager.retrieve_experiences(
                    query=user_input, 
                    experience_type="user_dialogue_text", 
                    user_id=user_id, 
                    limit=5
                )
                if user_memories:
                    user_context = "Previous context: " + " ".join([mem.get("content", "") for mem in user_memories[-2:]])

            emotion_context = ""
            if self.emotion_system:
                current_emotion = await self.emotion_system.get_current_emotion_state()
                if current_emotion:
                    emotion_context = f"Current emotional state: {current_emotion}"
            
            # Prompt building
            system_prompt = f"You are {ai_name}, an AI assistant with genuine reasoning capabilities.\n{emotion_context}"
            user_prompt = f"User said: \"{user_input}\"\n{user_context}\nPlease provide a thoughtful response."
            
            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_prompt)
            ]
            
            llm_response = await self.llm_interface.chat_completion(messages)
            
            if llm_response and llm_response.content:
                if len(llm_response.content.strip()) > 10:
                    logger.info("Generated intelligent response using real LLM inference.")
                    return f"{llm_response.content}"
                
            return await self.generate_contextual_response(user_input, ai_name, user_context)
        except Exception as e:
            logger.error(f"Error in intelligent response generation: {e}")
            return await self.generate_contextual_response(user_input, ai_name, "")

    async def generate_contextual_response(self, user_input: str, ai_name: str, context: str) -> str:
        """基于上下文的响应生成, 作为降级方案"""
        if len(user_input.strip()) < 5:
            return f"I hear you. Could you tell me more about that?"
        elif "?" in user_input:
            return f"That's an interesting question. Let me think about it carefully..."
        elif any(word in user_input.lower() for word in ["hello", "hi", "hey"]):
            return f"Hello! I'm here to help. What would you like to discuss?"
        else:
            return f"I understand you're sharing something important. Let me consider this thoughtfully."

    async def start_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
        
        logger.info(f"DialogueManager: New session started for user '{user_id or 'anonymous'}', session_id: {session_id}.")
        self.active_sessions[session_id] = []
        
        base_prompt = self.personality_manager.get_initial_prompt() or ""
        time_segment = self.time_system.get_time_of_day_segment()
        greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello,"}
        return f"{greetings.get(time_segment, '')} {base_prompt}".strip()

    async def _dispatch_hsp_task_request(self, 
                                        capability_advertisement: Dict[str, Any],
                                        request_parameters: Dict[str, Any], 
                                        original_user_query: str, 
                                        user_id: str, 
                                        session_id: str,
                                        request_type: str = "api_initiated_hsp_task") -> Tuple[str, Optional[str]]:
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
                "capability_id": capability_advertisement.get("capability_id") or "",
                "target_ai_id": capability_advertisement.get("ai_id") or "",
                "parameters": request_parameters,
                "user_id": user_id or "",
                "session_id": session_id or "",
                "request_type": request_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Send task via HSP connector
            success = await self.hsp_connector.send_task_request(
                target_ai_id=capability_advertisement.get("ai_id") or "",
                capability_id=capability_advertisement.get("capability_id") or "",
                parameters=request_parameters,
                correlation_id=correlation_id
            )

            if success:
                logger.info(f"Task request {correlation_id} sent successfully to {capability_advertisement.get('ai_id')}")
                return (f"Task request sent successfully to {capability_advertisement.get('ai_id')}", correlation_id)
            else:
                self.pending_hsp_task_requests.pop(correlation_id, None)
                return ("Failed to send task request via HSP", None)

        except Exception as e:
            logger.error(f"Error dispatching HSP task: {e}")
            return (f"Error dispatching task: {str(e)}", None)