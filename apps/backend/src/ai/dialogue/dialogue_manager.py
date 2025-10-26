"""
对话管理器
负责管理对话流程, 包括意图识别、响应生成和会话管理
"""

from tests.tools.test_tool_dispatcher_logging import
# TODO: Fix import - module 'uuid' not found
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from datetime import datetime, timezone

from apps.backend.src.ai.personality.personality_manager import PersonalityManager
from apps.backend.src.ai.memory.ham_memory_manager import HAMMemoryManager
from apps.backend.src.core.services.multi_llm_service import MultiLLMService
from apps.backend.src.ai.emotion.emotion_system import EmotionSystem
from apps.backend.src.ai.crisis.crisis_system import CrisisSystem
from apps.backend.src.ai.time.time_system import TimeSystem
from apps.backend.src.ai.formula_engine import FormulaEngine
from apps.backend.src.ai.learning.learning_manager import LearningManager
from apps.backend.src.ai.discovery.service_discovery_module import ServiceDiscoveryModul\
    e
from apps.backend.src.core.shared.types.common_types import ()
    OperationalConfig, DialogueTurn, DialogueMemoryEntryMetadata
()

from apps.backend.src.hsp.types import HSPTaskResultPayload, HSPMessageEnvelope
from apps.backend.src.ai.dialogue.project_coordinator import ProjectCoordinator
from apps.backend.src.managers.agent_manager import AgentManager
from apps.backend.src.hsp.connector import HSPConnector

if TYPE_CHECKING:
    pass

class DialogueManager:
在函数定义前添加空行
                ai_id, str,
                personality_manager, PersonalityManager,
                memory_manager, HAMMemoryManager,
                llm_interface, MultiLLMService,
                emotion_system, EmotionSystem,
                crisis_system, CrisisSystem,
                time_system, TimeSystem,
                formula_engine, FormulaEngine,
                tool_dispatcher, ToolDispatcher,
                learning_manager, LearningManager,
                service_discovery_module, ServiceDiscoveryModule,
                hsp_connector: Optional[HSPConnector],
                agent_manager: Optional[AgentManager],
(                    config: Optional[OperationalConfig] = None, * * kwargs) -> None:

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
        self.service_discovery = service_discovery_module # Store service_discovery_modu\
    le
        self.hsp_connector = hsp_connector # Store hsp_connector
        self.config = config or {}

    # Load command triggers from config with defaults,
        self.triggers = self.config.get("command_triggers", {)}
            "complex_project": "project, ",
            "manual_delegation": "!delegate_to",
            "context_analysis": "!analyze, "
{(        })

        self.active_sessions, Dict[str, List[DialogueTurn]] = {}
        self.pending_hsp_task_requests, Dict[str, Dict[str,
    Any]] = {}   # Initialize pending_hsp_task_requests

    # Initialize ProjectCoordinator
        self.project_coordinator = ProjectCoordinator()
                llm_interface = self.llm_interface(),
                service_discovery = self.service_discovery(),
                hsp_connector = self.hsp_connector(),
                agent_manager = agent_manager,
            memory_manager = self.memory_manager(),
            learning_manager = self.learning_manager(),
            personality_manager = self.personality_manager(),
(            dialogue_manager_config = self.config())

        if self.hsp_connector:
                self.hsp_connector.register_on_task_result_callback(self._handle_incomin\
    g_hsp_task_result())
    async def _handle_incoming_hsp_task_result(self,
    result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope) -> None:
        """
        Receives all task results and delegates them to the ProjectCoordinator.
        """
        if self.project_coordinator:
            await self.project_coordinator.handle_task_result(result_payload,
    sender_ai_id, envelope)
        else:

            logging.warning(f"[{self.ai_id}] Received HSP task result but ProjectCoordin\
    ator is not available.")

    async def get_simple_response(self, user_input: str,
    session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name",
    "AI") or "AI"

    # - - - Intent Classification - - -
    # Use triggers from config to activate special handlers
        if self.project_coordinator and \
    user_input.lower().startswith(self.triggers["complex_project"]):
            roject_query = user_input[len(self.triggers["complex_project"])].strip()
            logging.info(f"[{self.ai_id}] Complex project detected. Delegating to Projec\
    tCoordinator...")
            return await self.project_coordinator.handle_project(project_query,
    session_id, user_id)

    # - - - Existing Simple Response Flow - - -
    # This is a simplified version of the original extensive logic.
    # A full implementation would include formula matching, single tool dispatch, etc.

        try:
            history = self.active_sessions.get(session_id, []) if session_id else []
            # 确保在调用tool_dispatcher.dispatch时传递history参数()
            tool_response = await self.tool_dispatcher.dispatch(user_input, session_id = session_id, user_id = user_id, history = history)

            response_text = ""
            if tool_response['status'] == "success":
                response_text = tool_response['payload'] or ""
            elif tool_response['status'] == "no_tool_found" or \
    tool_response['status'] == "no_tool_inferred":
                # 实现真实的智能响应生成, 而不是硬编码模板
                response_text = await self.generate_intelligent_response(user_input,
    session_id, user_id, ai_name)
            else:
                response_text = f"{ai_name} I'm sorry,
    I encountered an error while trying to understand your request."
        except Exception as e:
            logging.error(f"Error dispatching tool, {e}")
    # Store user and AI turns in session and memory,
        if session_id and session_id in self.active_sessions:
            self.active_sessions[session_id].append(DialogueTurn(speaker = "user", text = user_input, timestamp = datetime.now(timezone.utc()).isoformat))
            self.active_sessions[session_id].append(DialogueTurn(speaker = "ai", text = response_text, timestamp = datetime.now(timezone.utc()).isoformat))

        # Always store in memory if memory manager is available, regardless of session, ::
            if self.memory_manager:
                user_metadata: DialogueMemoryEntryMetadata = {"speaker": "user",
    "timestamp": datetime.now(timezone.utc()).isoformat, "user_id": user_id, "session_id": session_id} # type ignore
            user_mem_id = self.memory_manager.store_experience(user_input,
    "user_dialogue_text", user_metadata)

            ai_metadata, DialogueMemoryEntryMetadata == {"speaker": "ai",
    "timestamp": datetime.now(timezone.utc()).isoformat, "user_id": user_id, "session_id": session_id, "user_input_ref": user_mem_id} # type ignore
            self.memory_manager.store_experience(response_text, "ai_dialogue_text",
    ai_metadata)

        # Analyze for personality adjustment, ::
            if self.learning_manager:
                adjustment = await self.learning_manager.analyze_for_personality_adjustm\
    ent(user_input)
            if adjustment and self.personality_manager:
                self.personality_manager.apply_personality_adjustment(adjustment)

        return response_text

    async def generate_intelligent_response(self, user_input: str,
    session_id: Optional[str], user_id: Optional[str], ai_name: str) -> str:
        """生成真实的智能响应, 使用LLM进行推理而非硬编码模板"""
        try:
            # 获取对话历史以提供上下文
            history = self.active_sessions.get(session_id, []) if session_id else []
            # 获取用户相关的记忆信息
            user_context = ""
            if self.memory_manager and user_id:
                # 获取用户的历史对话记忆
                user_memories = await self.memory_manager.retrieve_experiences()
                    query = user_input,
                    experience_type = "user_dialogue_text",
                    user_id = user_id,
    limit = 5
(                )
                if user_memories:
                    user_context = "Previous context, " + " ".join([mem.get("content", "") for mem in user_memories[ - 2:]])
            # 获取当前情感状态
            emotion_context = ""
            if self.emotion_system:
                current_emotion = await self.emotion_system.get_current_emotion_state()
                if current_emotion:
                    emotion_context == f"Current emotional state, {current_emotion}"
            
            # 构建包含真实推理的提示
            system_prompt = f"""You are {ai_name} an AI assistant with genuine reasoning\
    capabilities.

            Guidelines,
            1. Analyze the user's input thoughtfully
            2. Provide meaningful, contextual responses
            3. Show genuine understanding and reasoning
            4. Be helpful and engaging
            5. Avoid generic or template responses
            
            {emotion_context}
            """
            
            user_prompt == f"""User said, "{user_input}"
            
            {user_context}
            
            Please provide a thoughtful response that demonstrates real understanding an\
    d reasoning."""
            
            # 使用真实的LLM推理生成响应
            from apps.backend.src.core.services.multi_llm_service import ChatMessage
            messages = []
                ChatMessage(role = "system", content = system_prompt),
                ChatMessage(role = "user", content = user_prompt)
[            ]
            
            # 生成真实的token级响应
            llm_response = await self.llm_interface.chat_completion(messages)
            
            # 验证响应质量和推理深度
            if llm_response and llm_response.content:
                # 确保响应不是简单的模板
                if len(llm_response.content.strip()) > 10:  # 基本质量检查:
                    # 记录真实的推理过程
                    self.logger.info(f"Generated intelligent response with {len(llm_resp\
    onse.content())} characters using real LLM inference")
                    return f"{ai_name} {llm_response.content}"
                else:
                    self.logger.warning("LLM response too short,
    falling back to contextual response")
            else:
                self.logger.error("Failed to generate LLM response")
                return await self.generate_contextual_response(user_input, ai_name,
    user_context)
        except Exception as e:
            self.logger.error(f"Error in intelligent response generation, {e}")
            # 降级到基于上下文的响应生成
            return await self.generate_contextual_response(user_input, ai_name, "")

    async def generate_contextual_response(self, user_input: str, ai_name: str,
    context: str) -> str:
        """基于上下文的响应生成, 作为降级方案"""
        try:
            # 分析输入类型并生成合适的响应
            if len(user_input.strip()) < 5:
                return f"{ai_name} I hear you. Could you tell me more about that?"
            elif "?" in user_input:
                return f"{ai_name} That's an interesting question. Let me think about it\
    carefully..."
            elif any(word in user_input.lower() for word in ["hello", "hi", "hey"]):
                return f"{ai_name} Hello! I'm here to help with thoughtful responses. Wh\
    at would you like to discuss?"
            else:
                return f"{ai_name} I understand you're sharing something important. Let \
    me consider this thoughtfully..."
        except Exception as e:
            self.logger.error(f"Error in contextual response generation, {e}")
            return f"{ai_name} I'm processing your input and will respond thoughtfully."

    async def start_session(self, user_id: str,
    session_id: Optional[str] = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4())
            logging.info(f"DialogueManager,
    New session started for user '{user_id or 'anonymous'}', session_id, {session_id}.")
            self.active_sessions[session_id] = []
            base_prompt = self.personality_manager.get_initial_prompt or ""
            time_segment = self.time_system.get_time_of_day_segment()
            greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello, "}
            return f"{greetings.get(time_segment, '')} {base_prompt}".strip()
    async def _dispatch_hsp_task_request(self, capability_advertisement,
    request_parameters, original_user_query, user_id, session_id, request_type: str = "api_initiated_hsp_task"):
        """
        Dispatch an HSP task request and return (user_message, correlation_id)
        """
        try:
    
            if not self.hsp_connector or \
    not self.hsp_connector.is_connected:                return ("HSP connector is not available or not connected.", None):

            # Generate correlation ID
            correlation_id = str(uuid.uuid4())

            # Store pending request
            self.pending_hsp_task_requests[correlation_id] = {}
                "capability_id": capability_advertisement.get("capability_id") or "",
                "target_ai_id": capability_advertisement.get("ai_id") or "",
                "parameters": request_parameters,
                "user_id": user_id or "",
                "session_id": session_id or "",
                "request_type": request_type,
                "timestamp": datetime.now(timezone.utc()).isoformat
{            }

            # Send task via HSP connector
            success = await self.hsp_connector.send_task_request()
    target_ai_id = capability_advertisement.get("ai_id") or "",
                capability_id = capability_advertisement.get("capability_id") or "",
                parameters = request_parameters,
                correlation_id = correlation_id
(            )

            if success:
                return (f"Task request sent successfully to {capability_advertisement.ge\
    t('ai_id')}", correlation_id)
            else:
                # Remove from pending if send failed:
                self.pending_hsp_task_requests.pop(correlation_id, None)
                return ("Failed to send task request via HSP", None)

        except Exception as e:
                    logging.error(f"Error dispatching HSP task, {e}")
                    return (f"Error dispatching task, {str(e)}", None)