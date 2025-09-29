"""
对话管理器
负责管理对话流程，包括意图识别、响应生成和会话管理
"""

import logging
from datetime import datetime, timezone
# 修复导入路径 - 使用正确的模块路径
from apps.backend.src.hsp.types import HSPTaskResultPayload, HSPMessageEnvelope
# 导入缺失的类型
from apps.backend.src.ai.personality.personality_manager import PersonalityManager
from apps.backend.src.core.services.multi_llm_service import MultiLLMService
from apps.backend.src.ai.emotion.emotion_system import EmotionSystem
from apps.backend.src.ai.crisis.crisis_system import CrisisSystem
from apps.backend.src.ai.time.time_system import TimeSystem
from apps.backend.src.ai.formula_engine import FormulaEngine
from apps.backend.src.tools.tool_dispatcher import ToolDispatcher
from apps.backend.src.ai.learning.learning_manager import LearningManager
from apps.backend.src.ai.discovery.service_discovery_module import ServiceDiscoveryModule
from apps.backend.src.hsp.connector import HSPConnector
from apps.backend.src.managers.agent_manager import AgentManager
from apps.backend.src.ai.dialogue.project_coordinator import ProjectCoordinator
from apps.backend.src.core.shared.types.common_types import DialogueTurn as CommonDialogueTurn, OperationalConfig
import uuid

# 定义一个类型别名来解决类型不兼容问题
DialogueManagerConfig = Dict[str, Any]

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
                 hsp_connector: Optional[HSPConnector],  # 确保类型注解正确
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
        self.config = config or 

        # Load command triggers from config with defaults
        self.triggers = self.config.get("command_triggers", {
            "complex_project": "project:",
            "manual_delegation": "!delegate_to",
            "context_analysis": "!analyze:"
        })

        self.active_sessions: Dict[str, List[CommonDialogueTurn]] = 
        self.pending_hsp_task_requests: Dict[str, Dict[str, Any]] =  # Initialize pending_hsp_task_requests
        
        # Initialize ProjectCoordinator
        # 修复类型不兼容问题：确保传递的参数类型与ProjectCoordinator期望的类型一致
        config_dict: Dict[str, Any] = 
        if self.config is not None:
            # 将TypedDict转换为普通字典
            config_dict = {k: v for k, v in self.config.items if v is not None}
        
        self.project_coordinator = ProjectCoordinator(
            llm_interface=self.llm_interface,
            service_discovery=self.service_discovery,
            hsp_connector=hsp_connector,  # 明确传递hsp_connector参数
            agent_manager=agent_manager,
            memory_manager=self.memory_manager,
            learning_manager=self.learning_manager,
            personality_manager=self.personality_manager,
            dialogue_manager_config=config_dict  # 确保传递dict类型
        )

        if self.hsp_connector:
            # 修复回调函数类型不匹配问题
            self.hsp_connector.register_on_task_result_callback(self._handle_incoming_hsp_task_result_sync)

    # 添加一个同步包装函数来处理异步回调
    def _handle_incoming_hsp_task_result_sync(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope) -> None:
        """
        同步包装函数，用于处理HSP任务结果回调
        """
        # 在实际应用中，这应该在事件循环中调度异步函数
        # 但在当前上下文中，我们简化处理
        try:
            import asyncio
            # 尝试获取当前事件循环
            try:
                loop = asyncio.get_running_loop
                # 在事件循环中调度异步函数
                asyncio.create_task(self._handle_incoming_hsp_task_result(result_payload, sender_ai_id, envelope))
            except RuntimeError:
                # 没有运行中的事件循环，直接运行异步函数
                asyncio.run(self._handle_incoming_hsp_task_result(result_payload, sender_ai_id, envelope))
        except Exception as e:
            logging.error(f"Error handling HSP task result: {e}")

    async def _handle_incoming_hsp_task_result(self, result_payload: HSPTaskResultPayload, sender_ai_id: str, envelope: HSPMessageEnvelope) -> None:
        """
        Receives all task results and delegates them to the ProjectCoordinator.
        """
        if self.project_coordinator:
            # 修复await问题：确保正确处理异步调用
            try:
                # 由于handle_task_result返回None，我们不需要await它
                self.project_coordinator.handle_task_result(result_payload, sender_ai_id, envelope)
            except Exception as e:
                logging.warning(f"[{self.ai_id}] Error handling HSP task result in ProjectCoordinator: {e}")
        else:
            logging.warning(f"[{self.ai_id}] Received HSP task result but ProjectCoordinator is not available.")

    async def get_simple_response(self, user_input: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        ai_name = self.personality_manager.get_current_personality_trait("display_name", "AI") or "AI"

        # --- Intent Classification ---
        # Use triggers from config to activate special handlers
        if self.project_coordinator and user_input.lower.startswith(self.triggers["complex_project"]):
            project_query = user_input[len(self.triggers["complex_project"]):].strip
            logging.info(f"[{self.ai_id}] Complex project detected. Delegating to ProjectCoordinator...")
            # 修复await问题：确保正确处理异步调用
            result = await self.project_coordinator.handle_project(project_query, session_id, user_id)
            return result if result is not None else f"{ai_name}: I couldn't process your project request."

        # --- Existing Simple Response Flow ---
        # This is a simplified version of the original extensive logic.
        # A full implementation would include formula matching, single tool dispatch, etc.
        
        try:
            # Attempt to dispatch a tool based on user input
            history = self.active_sessions.get(session_id, ) if session_id else 
            # 确保在调用tool_dispatcher.dispatch时传递history参数
            tool_response = await self.tool_dispatcher.dispatch(user_input, session_id=session_id, user_id=user_id, history=history)

            response_text = ""
            if tool_response['status'] == "success":
                response_text = tool_response['payload'] if tool_response['payload'] is not None else ""
            elif tool_response['status'] == "no_tool_found" or tool_response['status'] == "no_tool_inferred":
                response_text = f"{ai_name}: You said '{user_input}'. This is a simple response."
            else:
                response_text = f"{ai_name}: I'm sorry, I encountered an error while trying to understand your request."
        except Exception as e:
            logging.error(f"Error dispatching tool: {e}")
            response_text = f"{ai_name}: I'm sorry, I encountered an error while trying to understand your request."

        # Store user and AI turns in session and memory
        if session_id and session_id in self.active_sessions:
            user_turn: CommonDialogueTurn = {
                "speaker": "user", 
                "text": user_input, 
                "timestamp": datetime.now(timezone.utc).isoformat,
                "metadata": None
            }
            self.active_sessions[session_id].append(user_turn)
            
            ai_turn: CommonDialogueTurn = {
                "speaker": "ai", 
                "text": response_text, 
                "timestamp": datetime.now(timezone.utc).isoformat,
                "metadata": None
            }
            self.active_sessions[session_id].append(ai_turn)

        # Always store in memory if memory manager is available, regardless of session
        if self.memory_manager:
            # 使用None作为metadata参数来避免类型冲突
            user_mem_id = await self.memory_manager.store_experience(user_input, "user_dialogue_text", None)

            # 使用None作为metadata参数来避免类型冲突
            _ = await self.memory_manager.store_experience(response_text, "ai_dialogue_text", None)

        # Analyze for personality adjustment
        if self.learning_manager:
            adjustment = await self.learning_manager.analyze_for_personality_adjustment(user_input)
            if adjustment and self.personality_manager:
                self.personality_manager.apply_personality_adjustment(adjustment)

        return response_text if response_text is not None else ""

    async def start_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        if not session_id:
            session_id = str(uuid.uuid4)
        logging.info(f"DialogueManager: New session started for user '{user_id or 'anonymous'}', session_id: {session_id}.")
        self.active_sessions[session_id] = 
        base_prompt = self.personality_manager.get_initial_prompt
        time_segment = self.time_system.get_time_of_day_segment
        greetings = {"morning": "Good morning!", "afternoon": "Good afternoon!", "evening": "Good evening!", "night": "Hello,"}
        return f"{greetings.get(time_segment, '')} {base_prompt}".strip

    async def _dispatch_hsp_task_request(self, capability_advertisement, request_parameters, original_user_query, user_id, session_id, request_type="api_initiated_hsp_task"):
        """
        _ = Dispatch an HSP task request and return (user_message, correlation_id)
        """
        try:
            if not self.hsp_connector or not self.hsp_connector.is_connected:
                return ("HSP connector is not available or not connected.", None)
            
            # Generate correlation ID
            correlation_id = str(uuid.uuid4)
            
            # Store pending request
            self.pending_hsp_task_requests[correlation_id] = {
                "capability_id": capability_advertisement.get("capability_id") if capability_advertisement.get("capability_id") is not None else "",
                "target_ai_id": capability_advertisement.get("ai_id") if capability_advertisement.get("ai_id") is not None else "",
                "parameters": request_parameters,
                "user_id": user_id if user_id is not None else "",
                "session_id": session_id if session_id is not None else "",
                "request_type": request_type,
                "timestamp": datetime.now(timezone.utc).isoformat
            }
            
            # Send task via HSP connector
            # 修复类型问题：确保参数类型正确
            success = await self.hsp_connector.send_task_request(
                payload=request_parameters,  # 确保使用正确的参数名
                target_ai_id_or_topic=capability_advertisement.get("ai_id") if capability_advertisement.get("ai_id") is not None else "",
                qos=1
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