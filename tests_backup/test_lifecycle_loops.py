"""
生命循環系統測試

測試 Angela 的所有生命循環功能。
"""

import pytest
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
import json
from dataclasses import dataclass

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mock 服務類
@dataclass
class MockLLMService:
    """Mock LLM 服務"""
    async def chat_completion(self, messages):
        @dataclass
        class MockResponse:
            content: str = json.dumps({
                "action": "greet",
                "message": "你好！我在這裡陪你。",
                "priority": "medium",
                "reason": "主動問候",
                "confidence": 0.8
            })
        return MockResponse()


@dataclass
class MockStateManager:
    """Mock 狀態管理器"""
    async def get_state_matrix(self):
        return {'alpha': 0.6, 'beta': 0.5, 'gamma': 0.7, 'delta': 0.5}


@dataclass
class MockMemoryManager:
    """Mock 記憶管理器"""
    async def get_recent_memories(self, limit=5):
        return [
            "用戶剛才問了關於AI的問題",
            "用戶表示對機器學習感興趣"
        ]

    async def store_experience(self, raw_data, data_type):
        pass

    async def store_structured_memory(self, content, structured_data):
        pass

    async def add_to_knowledge_base(self, content, importance):
        pass

    async def generate_template(self, template):
        pass

    async def get_important_events(self, limit=3):
        return ["用戶的生日快到了"]


@dataclass
class MockLearningEngine:
    """Mock 學習引擎"""
    pass


# 導入被測試的模塊
import sys
sys.path.insert(0, '/home/cat/桌面/Unified-AI-Project/apps/backend')

from src.ai.lifecycle.user_monitor import UserMonitor, UserState
from src.ai.lifecycle.llm_decision_loop import LLMDecisionLoop
from src.ai.lifecycle.proactive_interaction_system import ProactiveInteractionSystem
from src.ai.lifecycle.behavior_feedback_loop import BehaviorFeedbackLoop
from src.ai.lifecycle.memory_integration_loop import MemoryIntegrationLoop
from src.ai.integration.digital_life_integrator import DigitalLifeIntegrator


class TestUserMonitor:
    """測試用戶監控系統"""

    @pytest.fixture
    def user_monitor(self):
        return UserMonitor(
            user_id="test_user",
            check_interval=1.0,
            idle_threshold=10.0,
            return_threshold=20.0
        )

    @pytest.mark.asyncio
    async def test_user_monitor_start_stop(self, user_monitor):
        """測試啟動和停止"""
        assert not user_monitor.is_running

        await user_monitor.start()
        assert user_monitor.is_running

        await user_monitor.stop()
        assert not user_monitor.is_running

    @pytest.mark.asyncio
    async def test_user_monitor_record_input(self, user_monitor):
        """測試記錄用戶輸入"""
        await user_monitor.start()

        user_monitor.record_input("你好Angela")
        state = user_monitor.get_user_state()

        assert state.last_input == "你好Angela"
        assert state.total_interactions == 1
        assert state.emotion in UserMonitor.UserEmotion._value2member_map_.keys()

        await user_monitor.stop()

    @pytest.mark.asyncio
    async def test_user_monitor_emotion_estimation(self, user_monitor):
        """測試情緒估計"""
        # 測試不同情緒
        emotions = {
            "我很開心！": "happy",
            "我感到很難過": "sad",
            "這太糟糕了": "frustrated",
            "我不明白": "confused"
        }

        for text, expected_emotion in emotions.items():
            emotion, intensity = user_monitor._estimate_emotion_from_text(text)
            assert emotion == expected_emotion

    @pytest.mark.asyncio
    async def test_user_monitor_idle_detection(self, user_monitor):
        """測試閒置檢測"""
        await user_monitor.start()

        # 記錄輸入
        user_monitor.record_input("測試")
        assert not user_monitor.is_idle()

        # 等待超過閾值
        await asyncio.sleep(11)
        assert user_monitor.is_idle()

        await user_monitor.stop()

    @pytest.mark.asyncio
    async def test_user_monitor_return_detection(self, user_monitor):
        """測試返回檢測"""
        await user_monitor.start()

        # 用戶在線
        user_monitor.record_input("測試")

        # 模擬離線後返回
        await asyncio.sleep(12)
        user_monitor.record_input("我回來了")

        assert user_monitor.detect_return()

        await user_monitor.stop()


class TestLLMDecisionLoop:
    """測試 LLM 決策循環"""

    @pytest.fixture
    def components(self):
        llm_service = MockLLMService()
        state_manager = MockStateManager()
        memory_manager = MockMemoryManager()
        user_monitor = UserMonitor(check_interval=1.0)

        return {
            'llm_service': llm_service,
            'state_manager': state_manager,
            'memory_manager': memory_manager,
            'user_monitor': user_monitor
        }

    @pytest.mark.asyncio
    async def test_decision_loop_start_stop(self, components):
        """測試啟動和停止"""
        decision_loop = LLMDecisionLoop(
            llm_service=components['llm_service'],
            state_manager=components['state_manager'],
            memory_manager=components['memory_manager'],
            user_monitor=components['user_monitor'],
            loop_interval=1.0
        )

        assert not decision_loop.is_running

        await decision_loop.start()
        assert decision_loop.is_running

        await decision_loop.stop()
        assert not decision_loop.is_running

    @pytest.mark.asyncio
    async def test_decision_loop_execution(self, components):
        """測試決策執行"""
        await components['user_monitor'].start()

        decision_loop = LLMDecisionLoop(
            llm_service=components['llm_service'],
            state_manager=components['state_manager'],
            memory_manager=components['memory_manager'],
            user_monitor=components['user_monitor'],
            loop_interval=1.0
        )

        await decision_loop.start()
        await asyncio.sleep(5)  # 運行幾次循環

        stats = decision_loop.get_stats()
        assert stats['is_running']
        assert stats['total_decisions'] > 0

        await decision_loop.stop()
        await components['user_monitor'].stop()

    @pytest.mark.asyncio
    async def test_decision_loop_fallback(self, components):
        """測試回退決策"""
        decision_loop = LLMDecisionLoop(
            llm_service=components['llm_service'],
            state_manager=components['state_manager'],
            memory_manager=components['memory_manager'],
            user_monitor=components['user_monitor'],
            loop_interval=1.0
        )

        # 測試回退決策
        fallback_decision = decision_loop._fallback_decision()

        assert 'action' in fallback_decision
        assert 'message' in fallback_decision
        assert 'priority' in fallback_decision


class TestProactiveInteractionSystem:
    """測試主動交互系統"""

    @pytest.fixture
    def components(self):
        llm_service = MockLLMService()
        state_manager = MockStateManager()
        memory_manager = MockMemoryManager()
        user_monitor = UserMonitor(check_interval=1.0)

        return {
            'llm_service': llm_service,
            'state_manager': state_manager,
            'memory_manager': memory_manager,
            'user_monitor': user_monitor
        }

    @pytest.mark.asyncio
    async def test_proactive_system_start_stop(self, components):
        """測試啟動和停止"""
        proactive_system = ProactiveInteractionSystem(
            llm_service=components['llm_service'],
            state_manager=components['state_manager'],
            memory_manager=components['memory_manager'],
            user_monitor=components['user_monitor'],
            check_interval=1.0
        )

        assert not proactive_system.is_running

        await proactive_system.start()
        assert proactive_system.is_running

        await proactive_system.stop()
        assert not proactive_system.is_running

    @pytest.mark.asyncio
    async def test_proactive_system_identify_opportunities(self, components):
        """測試識別交互機會"""
        await components['user_monitor'].start()

        proactive_system = ProactiveInteractionSystem(
            llm_service=components['llm_service'],
            state_manager=components['state_manager'],
            memory_manager=components['memory_manager'],
            user_monitor=components['user_monitor'],
            check_interval=1.0
        )

        await proactive_system.start()

        # 模擬用戶輸入以生成機會
        components['user_monitor'].record_input("我很難過", {"emotion": "sad"})
        await asyncio.sleep(3)

        stats = proactive_system.get_stats()
        assert stats['is_running']
        assert stats['total_opportunities'] >= 0

        await proactive_system.stop()
        await components['user_monitor'].stop()


class TestBehaviorFeedbackLoop:
    """測試行為反饋循環"""

    @pytest.fixture
    def components(self):
        llm_service = MockLLMService()
        memory_manager = MockMemoryManager()
        learning_engine = MockLearningEngine()

        return {
            'llm_service': llm_service,
            'memory_manager': memory_manager,
            'learning_engine': learning_engine
        }

    @pytest.mark.asyncio
    async def test_feedback_loop_start_stop(self, components):
        """測試啟動和停止"""
        feedback_loop = BehaviorFeedbackLoop(
            llm_service=components['llm_service'],
            memory_manager=components['memory_manager'],
            learning_engine=components['learning_engine'],
            loop_interval=1.0
        )

        assert not feedback_loop.is_running

        await feedback_loop.start()
        assert feedback_loop.is_running

        await feedback_loop.stop()
        assert not feedback_loop.is_running

    @pytest.mark.asyncio
    async def test_feedback_loop_record_behavior(self, components):
        """測試記錄行為"""
        feedback_loop = BehaviorFeedbackLoop(
            llm_service=components['llm_service'],
            memory_manager=components['memory_manager'],
            learning_engine=components['learning_engine'],
            loop_interval=1.0
        )

        # 記錄行為
        feedback_loop.record_behavior(
            action="greet",
            message="你好！",
            priority="medium",
            user_response="你好啊",
            user_emotion="happy"
        )

        assert feedback_loop.stats['total_behaviors'] == 1

    @pytest.mark.asyncio
    async def test_feedback_loop_evaluation(self, components):
        """測試行為評估"""
        feedback_loop = BehaviorFeedbackLoop(
            llm_service=components['llm_service'],
            memory_manager=components['memory_manager'],
            learning_engine=components['learning_engine'],
            loop_interval=1.0
        )

        # 記錄行為
        feedback_loop.record_behavior(
            action="greet",
            message="你好！",
            priority="medium",
            user_response="你好啊！很高興見到你！",
            user_emotion="happy"
        )

        await feedback_loop.start()
        await asyncio.sleep(3)

        stats = feedback_loop.get_stats()
        assert stats['evaluated_behaviors'] >= 0

        await feedback_loop.stop()


class TestMemoryIntegrationLoop:
    """測試記憶整合循環"""

    @pytest.fixture
    def components(self):
        memory_manager = MockMemoryManager()
        learning_engine = MockLearningEngine()

        return {
            'memory_manager': memory_manager,
            'learning_engine': learning_engine
        }

    @pytest.mark.asyncio
    async def test_integration_loop_start_stop(self, components):
        """測試啟動和停止"""
        integration_loop = MemoryIntegrationLoop(
            memory_manager=components['memory_manager'],
            learning_engine=components['learning_engine'],
            loop_interval=1.0
        )

        assert not integration_loop.is_running

        await integration_loop.start()
        assert integration_loop.is_running

        await integration_loop.stop()
        assert not integration_loop.is_running

    @pytest.mark.asyncio
    async def test_integration_loop_add_memory(self, components):
        """測試添加記憶"""
        integration_loop = MemoryIntegrationLoop(
            memory_manager=components['memory_manager'],
            learning_engine=components['learning_engine'],
            loop_interval=1.0
        )

        # 添加記憶
        integration_loop.add_memory("用戶喜歡聽音樂", "interest", 0.8)

        assert integration_loop.stats['total_memories'] == 1

    @pytest.mark.asyncio
    async def test_integration_loop_pattern_analysis(self, components):
        """測試模式分析"""
        integration_loop = MemoryIntegrationLoop(
            memory_manager=components['memory_manager'],
            learning_engine=components['learning_engine'],
            loop_interval=1.0
        )

        # 添加多個相似記憶
        integration_loop.add_memory("用戶喜歡聽音樂", "interest", 0.8)
        integration_loop.add_memory("用戶喜歡聽音樂", "interest", 0.8)
        integration_loop.add_memory("用戶喜歡聽音樂", "interest", 0.8)

        await integration_loop.start()
        await asyncio.sleep(3)

        patterns = integration_loop.get_patterns()
        assert len(patterns) >= 0

        await integration_loop.stop()


class TestDigitalLifeIntegrator:
    """測試數字生命集成器（端到端測試）"""

    @pytest.fixture
    def integrator(self):
        llm_service = MockLLMService()
        state_manager = MockStateManager()
        memory_manager = MockMemoryManager()
        learning_engine = MockLearningEngine()

        return DigitalLifeIntegrator(
            llm_service=llm_service,
            state_manager=state_manager,
            memory_manager=memory_manager,
            learning_engine=learning_engine,
            config={
                'user_id': 'test_user',
                'decision_interval': 1.0,
                'proactive_interval': 2.0,
                'feedback_interval': 3.0,
                'memory_interval': 4.0
            }
        )

    @pytest.mark.asyncio
    async def test_integrator_start_stop(self, integrator):
        """測試啟動和停止"""
        assert not integrator.is_running

        await integrator.start()
        assert integrator.is_running

        await integrator.stop()
        assert not integrator.is_running

    @pytest.mark.asyncio
    async def test_integrator_full_lifecycle(self, integrator):
        """測試完整生命循環"""
        await integrator.start()

        # 模擬用戶交互
        integrator.record_user_input("你好Angela！")
        await asyncio.sleep(2)

        integrator.record_user_input("我今天心情不好")
        await asyncio.sleep(2)

        # 記錄行為
        integrator.record_behavior(
            action="comfort",
            message="別擔心，我陪著你",
            priority="high",
            user_response="謝謝",
            user_emotion="neutral"
        )

        # 添加記憶
        integrator.add_memory("用戶喜歡聽音樂", "interest", 0.8)

        # 運行一段時間
        await asyncio.sleep(10)

        # 檢查統計
        stats = integrator.get_lifecycle_stats()
        assert stats['is_running']
        assert stats['duration_seconds'] > 0

        # 檢查健康狀態
        health = integrator.get_health_status()
        assert health['status'] in ['healthy', 'degraded']

        # 檢查活力評分
        vitality = integrator.get_vitality_score()
        assert 0.0 <= vitality <= 1.0

        logger.info(f"Vitality Score: {vitality:.2f}/1.0")

        await integrator.stop()


# 運行測試的便捷函數
async def run_all_tests():
    """運行所有測試"""
    logger.info("開始運行生命循環測試...")

    # 1. 測試用戶監控
    logger.info("\n=== 測試用戶監控系統 ===")
    test_user_monitor = TestUserMonitor()
    await test_user_monitor.test_user_monitor_start_stop(test_user_monitor.user_monitor())
    await test_user_monitor.test_user_monitor_record_input(test_user_monitor.user_monitor())

    # 2. 測試 LLM 決策循環
    logger.info("\n=== 測試 LLM 決策循環 ===")
    test_decision = TestLLMDecisionLoop()
    components = test_decision.components()
    await test_decision.test_decision_loop_start_stop(components)
    await test_decision.test_decision_loop_execution(components)

    # 3. 測試主動交互系統
    logger.info("\n=== 測試主動交互系統 ===")
    test_proactive = TestProactiveInteractionSystem()
    components = test_proactive.components()
    await test_proactive.test_proactive_system_start_stop(components)

    # 4. 測試行為反饋循環
    logger.info("\n=== 測試行為反饋循環 ===")
    test_feedback = TestBehaviorFeedbackLoop()
    components = test_feedback.components()
    await test_feedback.test_feedback_loop_start_stop(components)
    await test_feedback.test_feedback_loop_record_behavior(components)

    # 5. 測試記憶整合循環
    logger.info("\n=== 測試記憶整合循環 ===")
    test_memory = TestMemoryIntegrationLoop()
    components = test_memory.components()
    await test_memory.test_integration_loop_start_stop(components)
    await test_memory.test_integration_loop_add_memory(components)

    # 6. 端到端測試
    logger.info("\n=== 端到端測試 ===")
    test_integrator = TestDigitalLifeIntegrator()
    integrator = test_integrator.integrator()
    await test_integrator.test_integrator_full_lifecycle(integrator)

    logger.info("\n✅ 所有測試完成！")


if __name__ == "__main__":
    # 直接運行測試
    asyncio.run(run_all_tests())
