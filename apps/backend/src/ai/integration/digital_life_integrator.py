"""
數字生命集成器

協調所有生命循環，讓 Angela 真正"活著"。

這是 Angela 的生命系統核心控制器，負責：
- 初始化所有生命循環
- 協調循環之間的交互
- 監控生命系統狀態
- 提供統一的生命系統 API
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import json

from ..lifecycle.llm_decision_loop import LLMDecisionLoop
from ..lifecycle.proactive_interaction_system import ProactiveInteractionSystem
from ..lifecycle.user_monitor import UserMonitor
from ..lifecycle.behavior_feedback_loop import BehaviorFeedbackLoop
from ..lifecycle.memory_integration_loop import MemoryIntegrationLoop

logger = logging.getLogger(__name__)


class DigitalLifeIntegrator:
    """
    數字生命集成器

    整合所有生命循環：
    1. LLM決策循環 - "大腦"核心決策
    2. 主動交互系統 - 主動社交能力
    3. 用戶監控系統 - 感知用戶狀態
    4. 行為反饋循環 - 從經驗中學習
    5. 記憶整合循環 - 主動整理記憶

    這些循環協同工作，讓 Angela 具備：
    - 持續的思考和決策能力
    - 主動性和社交能力
    - 感知和響應能力
    - 學習和改進能力
    - 記憶和知識管理能力
    """

    def __init__(
        self,
        llm_service: Any,
        state_manager: Any,
        memory_manager: Any,
        learning_engine: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
        broadcast_callback: Optional[callable] = None,
    ):
        self.llm_service = llm_service
        self.state_manager = state_manager
        self.memory_manager = memory_manager
        self.learning_engine = learning_engine
        self.config = config or {}
        self.broadcast_callback = broadcast_callback

        self.is_running = False
        self.start_time: Optional[datetime] = None

        # 初始化所有生命循環
        self._init_lifecycle_loops()

        logger.info("DigitalLifeIntegrator initialized")

    def _init_lifecycle_loops(self):
        """初始化所有生命循環"""
        logger.info("Initializing lifecycle loops...")

        # 1. 用戶監控系統 - 最基礎的系統
        self.user_monitor = UserMonitor(
            user_id=self.config.get("user_id", "default_user"),
            check_interval=self.config.get("user_monitor_interval", 5.0),
            idle_threshold=self.config.get("idle_threshold", 300.0),
            return_threshold=self.config.get("return_threshold", 1800.0),
        )

        # 2. LLM 決策循環 - "大腦"
        self.llm_decision_loop = LLMDecisionLoop(
            llm_service=self.llm_service,
            state_manager=self.state_manager,
            memory_manager=self.memory_manager,
            user_monitor=self.user_monitor,
            loop_interval=self.config.get("decision_interval", 3.0),
            min_loop_interval=2.0,
            max_loop_interval=5.0,
            broadcast_callback=self.broadcast_callback,
        )

        # 3. 主動交互系統 - 主動社交能力
        self.proactive_interaction = ProactiveInteractionSystem(
            llm_service=self.llm_service,
            state_manager=self.state_manager,
            memory_manager=self.memory_manager,
            user_monitor=self.user_monitor,
            check_interval=self.config.get("proactive_interval", 15.0),
            min_check_interval=10.0,
            max_check_interval=30.0,
            broadcast_callback=self.broadcast_callback,
        )

        # 4. 行為反饋循環 - 學習能力
        self.behavior_feedback = BehaviorFeedbackLoop(
            llm_service=self.llm_service,
            memory_manager=self.memory_manager,
            learning_engine=self.learning_engine or self.learning_engine,
            loop_interval=self.config.get("feedback_interval", 45.0),
            min_loop_interval=30.0,
            max_loop_interval=60.0,
        )

        # 5. 記憶整合循環 - 記憶管理
        self.memory_integration = MemoryIntegrationLoop(
            memory_manager=self.memory_manager,
            learning_engine=self.learning_engine or self.learning_engine,
            loop_interval=self.config.get("memory_interval", 180.0),
            min_loop_interval=120.0,
            max_loop_interval=300.0,
        )

        logger.info("✅ All lifecycle loops initialized")

    async def start(self):
        """啟動所有生命循環"""
        if self.is_running:
            logger.warning("DigitalLifeIntegrator is already running")
            return

        logger.info("🚀 Starting Digital Life Integrator...")
        self.is_running = True
        self.start_time = datetime.now()

        try:
            # 1. 啟動用戶監控（最基礎）
            logger.info("Starting user monitor...")
            await self.user_monitor.start()

            # 2. 啟動 LLM 決策循環
            logger.info("Starting LLM decision loop...")
            await self.llm_decision_loop.start()

            # 3. 啟動主動交互系統
            logger.info("Starting proactive interaction system...")
            await self.proactive_interaction.start()

            # 4. 啟動行為反饋循環
            logger.info("Starting behavior feedback loop...")
            await self.behavior_feedback.start()

            # 5. 啟動記憶整合循環
            logger.info("Starting memory integration loop...")
            await self.memory_integration.start()

            # 6. 設置循環之間的協調
            self._setup_loop_coordination()

            logger.info("✅ Digital Life Integrator started successfully!")
            logger.info(f"   Angela is now ALIVE at {self.start_time.isoformat()}")

        except Exception as e:
            logger.error(f"❌ Error starting Digital Life Integrator: {e}")
            await self.stop()
            raise

    async def stop(self):
        """停止所有生命循環"""
        if not self.is_running:
            return

        logger.info("🛑 Stopping Digital Life Integrator...")
        self.is_running = False

        try:
            # 按相反順序停止
            await self.memory_integration.stop()
            await self.behavior_feedback.stop()
            await self.proactive_interaction.stop()
            await self.llm_decision_loop.stop()
            await self.user_monitor.stop()

            duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            logger.info(f"✅ Digital Life Integrator stopped. Duration: {duration:.1f}s")

        except Exception as e:
            logger.error(f"❌ Error stopping Digital Life Integrator: {e}")

    def _setup_loop_coordination(self):
        """設置循環之間的協調"""

        # 當用戶輸入時，記錄到行為反饋系統
        def on_user_input(input_text, metadata=None):
            self.user_monitor.record_input(input_text, metadata)

        # 協調邏輯：LLM 決策時更新行為反饋
        if hasattr(self.llm_decision_loop, "decision_history"):

            def on_llm_decision(decision):
                """當 LLM 做出決策時，記錄到行為反饋系統"""
                self.behavior_feedback.record_behavior(
                    action=decision.action,
                    message=decision.message,
                    priority=decision.priority,
                    confidence=decision.confidence,
                )

        # 協調邏輯：主動交互執行後評估效果
        if hasattr(self.proactive_interaction, "interaction_queue"):

            def on_proactive_action_executed(plan):
                """當主動交互執行後，評估效果並記錄到記憶"""
                if plan.executed and plan.execution_result:
                    # 記錄成功的主動交互
                    self.memory_manager.add_memory(
                        content=f"主動執行 {plan.opportunity}: {plan.message}",
                        importance=0.7,
                        tags=["proactive", plan.opportunity, plan.action],
                    )

        # 協調邏輯：狀態變化時觸發適應
        if hasattr(self.state_manager, "state"):

            def on_state_change(old_state, new_state):
                """當狀態發生變化時，觸發適應性調整"""
                # 如果情緒發生顯著變化，記錄到記憶
                if old_state.get("emotion") != new_state.get("emotion"):
                    self.memory_manager.add_memory(
                        content=f"情緒從 {old_state.get('emotion')} 變為 {new_state.get('emotion')}",
                        importance=0.5,
                        tags=["emotion", "state_change"],
                    )

    def record_user_input(self, input_text: str, metadata: Optional[Dict[str, Any]] = None):
        """記錄用戶輸入"""
        self.user_monitor.record_input(input_text, metadata)

    def record_behavior(
        self,
        action: str,
        message: str,
        priority: str,
        user_response: Optional[str] = None,
        user_emotion: Optional[str] = None,
    ):
        """記錄行為到反饋系統"""
        self.behavior_feedback.record_behavior(
            action=action,
            message=message,
            priority=priority,
            user_response=user_response,
            user_emotion=user_emotion,
        )

    def add_memory(self, content: str, memory_type: str = "general", importance: float = 0.5):
        """添加記憶到整合系統"""
        self.memory_integration.add_memory(content, memory_type, importance)

    def get_user_state(self):
        """獲取用戶狀態"""
        return self.user_monitor.get_user_state()

    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """獲取生命系統統計信息"""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        return {
            "is_running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "duration_seconds": duration,
            "loops": {
                "user_monitor": self.user_monitor.get_stats(),
                "llm_decision": self.llm_decision_loop.get_stats(),
                "proactive_interaction": self.proactive_interaction.get_stats(),
                "behavior_feedback": self.behavior_feedback.get_stats(),
                "memory_integration": self.memory_integration.get_stats(),
            },
            "user_state": self.user_monitor.get_user_state().to_dict(),
            "behavior_patterns": self.behavior_feedback.get_patterns(),
            "knowledge_patterns": self.memory_integration.get_patterns(),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """獲取健康狀態"""
        loops_status = {
            "user_monitor": self.user_monitor.is_running,
            "llm_decision": self.llm_decision_loop.is_running,
            "proactive_interaction": self.proactive_interaction.is_running,
            "behavior_feedback": self.behavior_feedback.is_running,
            "memory_integration": self.memory_integration.is_running,
        }

        all_running = all(loops_status.values())

        return {
            "status": "healthy" if all_running else "degraded",
            "all_loops_running": all_running,
            "loops_status": loops_status,
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
        }

    def get_vitality_score(self) -> float:
        """計算生命活力評分"""
        if not self.is_running:
            return 0.0

        # 基於多個因素計算活力評分
        scores = []

        # 1. 用戶監控運行狀態
        scores.append(1.0 if self.user_monitor.is_running else 0.0)

        # 2. LLM 決策活躍度
        decision_stats = self.llm_decision_loop.get_stats()
        if decision_stats["total_decisions"] > 0:
            scores.append(min(1.0, decision_stats["total_decisions"] / 10.0))
        else:
            scores.append(0.0)

        # 3. 主動交互活躍度
        proactive_stats = self.proactive_interaction.get_stats()
        if proactive_stats["executed_actions"] > 0:
            scores.append(min(1.0, proactive_stats["executed_actions"] / 5.0))
        else:
            scores.append(0.5)

        # 4. 行為學習進度
        feedback_stats = self.behavior_feedback.get_stats()
        if feedback_stats["total_behaviors"] > 0:
            scores.append(min(1.0, feedback_stats["evaluated_behaviors"] / 10.0))
        else:
            scores.append(0.0)

        # 5. 記憶整合進度
        memory_stats = self.memory_integration.get_stats()
        if memory_stats["total_memories"] > 0:
            scores.append(min(1.0, memory_stats["integrated_memories"] / 5.0))
        else:
            scores.append(0.0)

        # 計算平均分
        vitality = sum(scores) / len(scores)

        return vitality


if __name__ == "__main__":
    # 測試數字生命集成器
    async def test_digital_life_integrator():
        from dataclasses import dataclass

        logging.basicConfig(level=logging.INFO)

        # Mock 服務
        class MockLLMService:
            async def chat_completion(self, messages):
                @dataclass
                class MockResponse:
                    content: str

                return MockResponse(
                    content=json.dumps(
                        {
                            "action": "greet",
                            "message": "你好！我在這裡陪你。",
                            "priority": "medium",
                            "reason": "主動問候",
                            "confidence": 0.8,
                        }
                    )
                )

        class MockStateManager:
            async def get_state_matrix(self):
                return {"alpha": 0.6, "beta": 0.5, "gamma": 0.7, "delta": 0.5}

        class MockMemoryManager:
            async def get_recent_memories(self, limit=5):
                return ["用戶剛才問了關於AI的問題"]

            async def store_experience(self, raw_data, data_type):
                pass

            async def store_structured_memory(self, content, structured_data):
                pass

            async def add_to_knowledge_base(self, content, importance):
                pass

            async def generate_template(self, template):
                pass

        class MockLearningEngine:
            pass

        # 創建組件
        llm_service = MockLLMService()
        state_manager = MockStateManager()
        memory_manager = MockMemoryManager()
        learning_engine = MockLearningEngine()

        # 創建數字生命集成器
        integrator = DigitalLifeIntegrator(
            llm_service=llm_service,
            state_manager=state_manager,
            memory_manager=memory_manager,
            learning_engine=learning_engine,
            config={
                "user_id": "test_user",
                "decision_interval": 2.0,
                "proactive_interval": 5.0,
                "feedback_interval": 10.0,
                "memory_interval": 8.0,
            },
        )

        # 啟動
        logger.info("=== 啟動數字生命系統 ===")
        await integrator.start()

        # 模擬用戶交互
        logger.info("\n=== 模擬用戶交互 ===")
        integrator.record_user_input("你好Angela！", {"type": "greeting"})
        await asyncio.sleep(3)

        integrator.record_user_input("我今天心情不好", {"type": "emotion"})
        await asyncio.sleep(3)

        # 記錄行為
        integrator.record_behavior(
            action="comfort",
            message="別擔心，我陪著你",
            priority="high",
            user_response="謝謝",
            user_emotion="neutral",
        )

        # 添加記憶
        integrator.add_memory("用戶喜歡聽音樂", "interest", 0.8)

        # 運行一段時間
        await asyncio.sleep(20)

        # 打印狀態
        logger.info(f"\n=== 生命系統統計 ===")
        logger.info(json.dumps(integrator.get_lifecycle_stats(), indent=2, ensure_ascii=False))

        logger.info(f"\n=== 健康狀態 ===")
        logger.info(json.dumps(integrator.get_health_status(), indent=2, ensure_ascii=False))

        logger.info(f"\n=== 生命活力評分 ===")
        vitality = integrator.get_vitality_score()
        logger.info(f"Vitality Score: {vitality:.2f}/1.0 ({vitality*10:.1f}/10.0)")

        # 停止
        await integrator.stop()

    asyncio.run(test_digital_life_integrator())
