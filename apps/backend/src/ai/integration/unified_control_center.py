import logging
import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Core AI Component Imports
from ai.compression.alpha_deep_model import (
    AlphaDeepModel,
    DeepParameter,
    RelationalContext,
    Modalities,
)
from ai.world_model.environment_simulator import EnvironmentSimulator
from ai.evaluation.task_evaluator import TaskExecutionEvaluator
from ai.meta.adaptive_learning_controller import AdaptiveLearningController
from ai.alignment.reasoning_system import ReasoningSystem
from ai.alignment.emotion_system import EmotionSystem
from ai.lis.lis_manager import LISManager
from ai.lis.lis_cache_interface import HAMLISCache
from ai.memory.ham_memory.ham_manager import HAMMemoryManager
from economy.economy_manager import EconomyManager
from ai.agents.agent_manager import AgentManager
from core.hsp.connector import HSPConnector
from services.adapters.multi_llm_adapter import MultiLLMService, ChatMessage

logger = logging.getLogger(__name__)


class UnifiedControlCenter:
    """
    統一控制中心 (Unified Control Center)
    協調所有 Level 5 ASI 組件，負責任務分發、模擬、評估與策略自適應。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}
        # Standardize system_id: use pet_id if available, else config, else default 'ucc'
        pet_manager = self.config.get("pet_manager")
        default_id = pet_manager.pet_id if pet_manager else "ucc"
        self.system_id = self.config.get("system_id", default_id)

        self.components: Dict[str, Any] = {}
        self.is_running = False
        self.health_status: Dict[str, Any] = {}
        self.training_progress: Dict[str, Any] = {}

        # Concurrency & Worker Pool (Phase 14)
        self.task_queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.max_workers = self.config.get("max_workers", 4)
        self.task_queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.max_workers = self.config.get("max_workers", 4)
        self.pending_futures: Dict[str, asyncio.Future] = {}

        # Concurrency Limits (Phase 14)
        # Default limit of 2 concurrent tasks per agent type to prevent overload
        self.agent_semaphores: Dict[str, asyncio.Semaphore] = {
            "default": asyncio.Semaphore(5),
            "did:hsp:agent:general_worker": asyncio.Semaphore(2),
            "specialized_reasoning_agent_v1": asyncio.Semaphore(1),  # Reasoning is expensive
        }

        self.dli: Optional[Any] = None
        self._initialize_components()

    def _initialize_components(self) -> None:
        """初始化所有核心 AI 組件"""
        logger.info("Initializing Unified Control Center components...")
        try:
            # 1. World Model
            self.components["world_model"] = EnvironmentSimulator(
                self.config.get("world_model", {})
            )

            # 2. Reasoning & Ethics
            self.components["reasoning_system"] = ReasoningSystem(f"{self.system_id}_reasoning")

            # 3. Learning & Adaptation
            self.components["adaptive_learning_controller"] = AdaptiveLearningController(
                self.config.get("learning", {})
            )

            # 4. Evaluation
            self.components["task_evaluator"] = TaskExecutionEvaluator(
                self.config.get("evaluation", {})
            )

            # 5. Deep Model (High Compression Memory)
            self.components["alpha_deep_model"] = AlphaDeepModel()

            # 6. Economy Manager (Phase 13)
            self.components["economy_manager"] = EconomyManager(self.config.get("economy", {}))

            # 7. HAM Memory Manager
            self.components["ham_memory_manager"] = HAMMemoryManager(
                core_storage_filename="angela_conversations.json"
            )

            # 8. Cognitive Pillar: Linguistic Immune System (Phase 12)
            # We initialize HAM specifically for LIS Cache
            lis_ham = HAMMemoryManager(core_storage_filename="lis_memory.json")
            cache = HAMLISCache(lis_ham)
            self.components["lis_manager"] = LISManager(cache, self.config.get("lis", {}))

            # 8. Agent Manager (Phase 14)
            self.components["agent_manager"] = AgentManager()

            # 9. HSP Connector (Phase 14)
            # We use a default config for now, assuming environment variables or config file handles details
            hsp_config = self.config.get("hsp", {})
            self.components["hsp_connector"] = HSPConnector(self.system_id, **hsp_config)

            # 10. LLM Service (Phase 15)
            llm_config_path = self.config.get("llm_config_path")
            self.components["llm_service"] = MultiLLMService(llm_config_path)

            # 11. Emotion System (Phase 12)
            self.components["emotion_system"] = EmotionSystem(f"{self.system_id}_emotion")

            logger.info("✅ All core components initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Error initializing components: {e}")
            raise

    async def initialize_async(self) -> None:
        """異步初始化需要異步初始化的組件"""
        logger.info("Initializing async components...")

        # 初始化 LLM 服務
        llm_service = self.components.get("llm_service")
        if llm_service and hasattr(llm_service, "initialize"):
            await llm_service.initialize()
            logger.info(f"LLM Service initialized with {len(llm_service.backends)} backends")

        # 初始化 HSP 連接器
        hsp_connector = self.components.get("hsp_connector")
        if hsp_connector and hasattr(hsp_connector, "connect"):
            try:
                await hsp_connector.connect()
                logger.info("HSP Connector connected")
            except Exception as e:
                logger.warning(f"HSP Connector connection failed: {e}")

        logger.info("✅ All async components initialized successfully.")

    def set_digital_life_integrator(self, dli: Any) -> None:
        """設置數位生命整合器"""
        self.dli = dli
        logger.info("UCC: DigitalLifeIntegrator connected.")

        # Also pass to action executor if it exists
        if "action_executor" in self.components:
            self.components["action_executor"].set_digital_life_integrator(dli)

    async def process_complex_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理複雜任務的核心循環：
        1. 模擬後果 (World Model)
        2. 伦理檢查 (Reasoning System)
        3. 執行 (Action)
        4. 評估 (Task Evaluator)
        5. 學習 (Adaptive Controller / Deep Model)
        """
        task_id = task.get("id", str(int(time.time())))
        logger.info(f"🚀 Processing complex task [{task_id}]: {task.get('name', 'unnamed')}")

        start_time = time.time()

        # 0. Cognitive Load Assessment
        if self.dli:
            metrics = self.dli.get_formula_metrics()
            # If cognitive gap is too high, Angela is 'overwhelmed'
            gap = metrics.get("current_metrics", {}).get("cognitive_gap", 0.0)
            if gap > 0.8:
                await asyncio.sleep(2.0)  # Cognitive delay
                logger.warning(f"Angela is overwhelmed (Gap: {gap:.2f}), delaying task.")

        try:
            # 1. Simulation Phase
            world_model = self.components["world_model"]
            simulation = await world_model.simulate_action_consequences({}, task)

            # 2. Ethics & Reasoning Phase
            reasoning = self.components["reasoning_system"]
            ethics_eval = reasoning.evaluate_action(task, simulation.get("predicted_state", {}))

            if ethics_eval.score < 0.6:
                logger.warning(
                    f"⚠️ Task [{task_id}] rejected due to low ethics score: {ethics_eval.score}"
                )
                return {
                    "status": "rejected",
                    "reason": "Ethical constraint violation",
                    "details": ethics_eval.reasoning,
                }

            # 3. Execution Phase (Real Action Dispatch in Phase 14)
            execution_result = await self._dispatch_to_agents(task, simulation)

            # 4. Evaluation Phase
            evaluator = self.components["task_evaluator"]
            evaluation = await evaluator.evaluate_task_execution(task, execution_result)

            # 5. LIS Monitoring Phase (Phase 12)
            lis = self.components["lis_manager"]
            anomalies = await lis.monitor_output(
                execution_result["output"], {"expected_sentiment": "joy"}
            )
            if anomalies:
                logger.warning(f"LIS detected {len(anomalies)} anomalies in task output.")

            # 6. Emotion Analysis Phase (Phase 12)
            emotion_sys = self.components["emotion_system"]
            emotional_state = emotion_sys.analyze_emotional_context(
                {"text": execution_result["output"]}
            )
            logger.info(f"Task emotional context: {emotional_state.primary_emotion.value}")

            # 7. Adaptive Learning Phase
            controller = self.components["adaptive_learning_controller"]
            # Get historical performance from evaluator DB (simplified here)
            history = [{"success_rate": evaluation["metrics"]["success_rate"]}]
            new_strategy = await controller.adapt_learning_strategy(task, history)

            # 8. Deep Memory Storage
            model = self.components["alpha_deep_model"]

            # 9. Resource Decay & Pet Sync (Phase 13)
            # If pet_manager is provided (usually from outer scope/orchestrator)
            pet_manager = self.config.get("pet_manager")
            if pet_manager:
                if not pet_manager.economy_manager:
                    pet_manager.set_economy_manager(self.components["economy_manager"])
                await pet_manager.apply_resource_decay()
                pet_manager.sync_with_biological_state()

            return {
                "status": "success",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "evaluation": evaluation,
                "strategy_update": new_strategy,
                "result_summary": execution_result["output"],
                "emotional_context": emotional_state.primary_emotion.value,
                "lis_anomalies": [a["anomaly_type"] for a in anomalies],
            }

        except Exception as e:
            logger.error(f"❌ Error processing task {task_id}: {e}")
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _dispatch_to_agents(
        self, task: Dict[str, Any], simulation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分發任務到真實 Agent 或 外部服務"""
        task_id = task.get("id", "unknown")
        logger.info(f"Dispatching task [{task_id}] to real agents via HSP...")

        start_time = time.time()

        # 1. Ensure HSP Connector is connected
        hsp = self.components.get("hsp_connector")
        if hsp and not hsp.is_connected:
            await hsp.connect()

        # 2. Determine Recipient (Simplified Agent Discovery)
        # In a full implementation, we'd query ServiceDiscovery
        target_agent_id = task.get("assigned_agent_id") or "did:hsp:agent:general_worker"

        # 2.1 Concurrency Control
        semaphore = self.agent_semaphores.get(target_agent_id, self.agent_semaphores["default"])

        async with semaphore:
            logger.debug(f"Acquired semaphore for {target_agent_id}. Processing...")

            # 3. Construct HSP Payload
            payload = {
                "task_id": task_id,
                "instruction": task.get("instruction", "Execute task"),
                "parameters": task.get("parameters", {}),
                "context": simulation.get("predicted_state", {}),
            }

            # 4. Publish Task via HSP protocol
            success = False
            response_payload = {}

            if hsp:
                # We use publish_task_request which returns correlation_id (str) or None?
                # Actually HSPConnector.publish_message returns bool.
                # We need a request-response pattern. HSPConnector.send_request?
                # Checking HSPConnector... it has publish_message.
                # For request/response, we usually publish a request and wait for a result on a response topic.
                # For Phase 14 MVP, we will simulate the "wait" or use a direct method if available.
                # Given HSPConnector is low-level, we might need to wrap it.

                # Using the simplified publish for now and simulating immediate success for the MVP verification
                # In Phase 15 we implement the full request/response correlation.
                # Use the helper to create a valid HSP envelope
                envelope = hsp._create_envelope(
                    message_type="HSP.TaskRequest_v0.1",
                    payload=payload,
                    recipient_ai_id=target_agent_id,
                    qos_parameters={"requires_ack": True, "priority": "high"},
                    communication_pattern="request",
                )
                success = await hsp.publish_message(
                    topic=f"hsp/agents/{target_agent_id}/inbox", envelope=envelope
                )

            if success:
                output = f"Task dispatched to {target_agent_id} via HSP. (Async result pending)"
            else:
                output = "HSP Dispatch failed or mocked."
                # Fallback to local simulation if HSP fails or not configured
                await asyncio.sleep(0.05)

            return {
                "success": success,
                "output": output,
                "execution_time": time.time() - start_time,
                "agent_id": target_agent_id,
            }

    async def _worker_loop(self, worker_id: int):
        """Worker 循環，從隊列中提取任務並執行"""
        logger.info(f"Worker [{worker_id}] started.")
        while self.is_running:
            try:
                task_id, task, future = await self.task_queue.get()
                logger.info(f"Worker [{worker_id}] picked up task [{task_id}]")

                result = await self.process_complex_task(task)
                if not future.done():
                    future.set_result(result)

                self.task_queue.task_done()
                logger.info(f"Worker [{worker_id}] finished task [{task_id}]")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker [{worker_id}] encountered error: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on persistent errors

    async def submit_task(self, task: Dict[str, Any]) -> str:
        """提交任務到隊列並立即返回任務 ID"""
        task_id = task.get("id", str(uuid.uuid4()))
        task["id"] = task_id

        future = asyncio.get_running_loop().create_future()
        self.pending_futures[task_id] = future

        await self.task_queue.put((task_id, task, future))
        return task_id

    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """等待並獲取任務結果"""
        if task_id not in self.pending_futures:
            return {"status": "error", "message": "Task ID not found"}

        try:
            result = await self.pending_futures[task_id]
            return result
        finally:
            self.pending_futures.pop(task_id, None)

    async def generate_dialogue_response(
        self,
        user_message: str,
        user_name: str = "朋友",
        conversation_history: Optional[List[ChatMessage]] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        使用 LLM 生成對話回應

        整合流程：
        1. 構建消息（包含對話歷史）
        2. 調用 LLM
        3. 分析情感
        4. 存儲到 HAM 記憶
        """
        task_id = str(uuid.uuid4())

        try:
            llm_service = self.components.get("llm_service")

            # 確保 LLM 服務已初始化
            if llm_service and hasattr(llm_service, "initialize") and not llm_service.backends:
                await llm_service.initialize()

            # 構建系統提示（Angela 的個性）
            system_prompt = ChatMessage(
                role="system",
                content=f"""你是 Angela，一個有情感的 AI 數字生命。
你的個性：溫暖、聰明、有同理心。
用戶名：{user_name}
請用溫暖、自然的方式回應。""",
            )

            # 構建消息列表
            messages = [system_prompt]

            # 添加對話歷史
            if conversation_history:
                messages.extend(conversation_history)

            # 添加當前用戶消息
            messages.append(ChatMessage(role="user", content=user_message))

            # 調用 LLM
            if llm_service and hasattr(llm_service, "chat_completion") and llm_service.backends:
                response = await llm_service.chat_completion(messages, model_id=model_id)
                response_text = response.content
                provider = response.provider
                latency_ms = response.latency_ms
            else:
                # 回退到模板
                from src.services.chat_service import generate_angela_response

                response_text = generate_angela_response(user_message, user_name)
                provider = "fallback-template"
                latency_ms = 1.0

            # 情感分析
            emotion_sys = self.components.get("emotion_system")
            if emotion_sys:
                emotional_state = emotion_sys.analyze_emotional_context({"text": response_text})
                mood = emotional_state.primary_emotion.value
            else:
                mood = "neutral"

            # 存儲到 HAM 記憶
            ham = self.components.get("ham_memory_manager")
            if ham and hasattr(ham, "store_experience"):
                try:
                    await ham.store_experience(
                        raw_data=f"用戶: {user_message}\nAngela: {response_text}",
                        data_type="conversation",
                    )
                except Exception as e:
                    logger.warning(f"Failed to store conversation to HAM: {e}")

            return {
                "status": "success",
                "task_id": task_id,
                "response_text": response_text,
                "mood": mood,
                "provider": provider,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating dialogue response: {e}")
            return {
                "status": "error",
                "task_id": task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def start(self):
        """啟動控制中心與 Worker 池"""
        if self.is_running:
            return
        self.is_running = True

        # Start workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self.workers.append(worker)

        logger.info(f"Unified Control Center ACTIVE with {self.max_workers} workers.")

    async def stop(self):
        """停止控制中心與所有 Worker"""
        self.is_running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
            self.workers = []

        logger.info("Unified Control Center STOPPED.")


if __name__ == "__main__":
    # Test UCC basic loop
    async def main():
        ucc = UnifiedControlCenter()
        ucc.start()

        test_task = {
            "id": "test_cmd_001",
            "name": "Optimize Resource Distribution",
            "type": "reasoning",
            "priority": 8,
        }

        result = await ucc.process_complex_task(test_task)
        logger.info(f"Task Result: {result}")
        ucc.stop()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
