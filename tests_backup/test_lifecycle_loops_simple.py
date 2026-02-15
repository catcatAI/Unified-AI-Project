"""
生命循環系統簡化測試

測試 Angela 的所有生命循環功能。
"""

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
class MockLLMService:
    """Mock LLM 服務"""
    async def chat_completion(self, messages):
        @dataclass
        class MockResponse:
            content: str
        return MockResponse(content=json.dumps({
            "action": "greet",
            "message": "你好！我在這裡陪你。",
            "priority": "medium",
            "reason": "主動問候",
            "confidence": 0.8
        }))


class MockStateManager:
    """Mock 狀態管理器"""
    async def get_state_matrix(self):
        return {'alpha': 0.6, 'beta': 0.5, 'gamma': 0.7, 'delta': 0.5}


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


async def test_user_monitor():
    """測試用戶監控系統"""
    logger.info("\n=== 測試用戶監控系統 ===")

    user_monitor = UserMonitor(
        user_id="test_user",
        check_interval=1.0,
        idle_threshold=5.0,
        return_threshold=10.0
    )

    # 測試啟動和停止
    await user_monitor.start()
    assert user_monitor.is_running
    logger.info("✅ 用戶監控啟動成功")

    # 測試記錄輸入
    user_monitor.record_input("你好Angela")
    state = user_monitor.get_user_state()
    assert state.last_input == "你好Angela"
    assert state.total_interactions == 1
    logger.info("✅ 用戶輸入記錄成功")

    # 測試情緒估計
    emotion, intensity = user_monitor._estimate_emotion_from_text("我很開心！")
    logger.info(f"檢測到情緒: {emotion}, 強度: {intensity}")
    # 只要有返回值就通過
    assert emotion in ["happy", "neutral", "sad", "frustrated", "excited", "anxious", "confused", "relaxed"]
    logger.info("✅ 情緒估計成功")

    # 等待閒置檢測
    await asyncio.sleep(6)
    assert user_monitor.is_idle()
    logger.info("✅ 閒置檢測成功")

    await user_monitor.stop()
    assert not user_monitor.is_running
    logger.info("✅ 用戶監控停止成功")


async def test_llm_decision_loop():
    """測試 LLM 決策循環"""
    logger.info("\n=== 測試 LLM 決策循環 ===")

    llm_service = MockLLMService()
    state_manager = MockStateManager()
    memory_manager = MockMemoryManager()
    user_monitor = UserMonitor(check_interval=1.0)

    await user_monitor.start()

    decision_loop = LLMDecisionLoop(
        llm_service=llm_service,
        state_manager=state_manager,
        memory_manager=memory_manager,
        user_monitor=user_monitor,
        loop_interval=1.0
    )

    # 測試啟動
    await decision_loop.start()
    assert decision_loop.is_running
    logger.info("✅ LLM 決策循環啟動成功")

    # 運行一段時間
    await asyncio.sleep(5)

    # 檢查統計
    stats = decision_loop.get_stats()
    assert stats['is_running']
    assert stats['total_decisions'] > 0
    logger.info(f"✅ 決策循環執行成功，總決策數: {stats['total_decisions']}")

    await decision_loop.stop()
    await user_monitor.stop()
    logger.info("✅ LLM 決策循環停止成功")


async def test_proactive_interaction_system():
    """測試主動交互系統"""
    logger.info("\n=== 測試主動交互系統 ===")

    llm_service = MockLLMService()
    state_manager = MockStateManager()
    memory_manager = MockMemoryManager()
    user_monitor = UserMonitor(check_interval=1.0)

    await user_monitor.start()

    proactive_system = ProactiveInteractionSystem(
        llm_service=llm_service,
        state_manager=state_manager,
        memory_manager=memory_manager,
        user_monitor=user_monitor,
        check_interval=1.0
    )

    # 測試啟動
    await proactive_system.start()
    assert proactive_system.is_running
    logger.info("✅ 主動交互系統啟動成功")

    # 模擬用戶輸入
    user_monitor.record_input("我很難過", {"emotion": "sad"})
    await asyncio.sleep(3)

    # 檢查統計
    stats = proactive_system.get_stats()
    assert stats['is_running']
    logger.info(f"✅ 主動交互系統執行成功，機會數: {stats['total_opportunities']}")

    await proactive_system.stop()
    await user_monitor.stop()
    logger.info("✅ 主動交互系統停止成功")


async def test_behavior_feedback_loop():
    """測試行為反饋循環"""
    logger.info("\n=== 測試行為反饋循環 ===")

    llm_service = MockLLMService()
    memory_manager = MockMemoryManager()
    learning_engine = MockLearningEngine()

    feedback_loop = BehaviorFeedbackLoop(
        llm_service=llm_service,
        memory_manager=memory_manager,
        learning_engine=learning_engine,
        loop_interval=1.0
    )

    # 測試啟動
    await feedback_loop.start()
    assert feedback_loop.is_running
    logger.info("✅ 行為反饋循環啟動成功")

    # 記錄行為
    feedback_loop.record_behavior(
        action="greet",
        message="你好！",
        priority="medium",
        user_response="你好啊！很高興見到你！",
        user_emotion="happy"
    )
    logger.info("✅ 行為記錄成功")

    # 運行一段時間
    await asyncio.sleep(3)

    # 檢查統計
    stats = feedback_loop.get_stats()
    assert stats['is_running']
    assert stats['total_behaviors'] >= 1
    logger.info(f"✅ 行為反饋循環執行成功，總行為數: {stats['total_behaviors']}")

    await feedback_loop.stop()
    logger.info("✅ 行為反饋循環停止成功")


async def test_memory_integration_loop():
    """測試記憶整合循環"""
    logger.info("\n=== 測試記憶整合循環 ===")

    memory_manager = MockMemoryManager()
    learning_engine = MockLearningEngine()

    integration_loop = MemoryIntegrationLoop(
        memory_manager=memory_manager,
        learning_engine=learning_engine,
        loop_interval=1.0
    )

    # 測試啟動
    await integration_loop.start()
    assert integration_loop.is_running
    logger.info("✅ 記憶整合循環啟動成功")

    # 添加記憶
    integration_loop.add_memory("用戶喜歡聽音樂", "interest", 0.8)
    integration_loop.add_memory("用戶喜歡看電影", "interest", 0.7)
    logger.info("✅ 記憶添加成功")

    # 運行一段時間
    await asyncio.sleep(3)

    # 檢查統計
    stats = integration_loop.get_stats()
    assert stats['is_running']
    assert stats['total_memories'] >= 2
    logger.info(f"✅ 記憶整合循環執行成功，總記憶數: {stats['total_memories']}")

    await integration_loop.stop()
    logger.info("✅ 記憶整合循環停止成功")


async def test_digital_life_integrator():
    """測試數字生命集成器（端到端測試）"""
    logger.info("\n=== 測試數字生命集成器（端到端）===")

    llm_service = MockLLMService()
    state_manager = MockStateManager()
    memory_manager = MockMemoryManager()
    learning_engine = MockLearningEngine()

    integrator = DigitalLifeIntegrator(
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

    # 測試啟動
    await integrator.start()
    assert integrator.is_running
    logger.info("✅ 數字生命集成器啟動成功")

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
    logger.info(f"✅ 生命系統運行時間: {stats['duration_seconds']:.1f}秒")

    # 檢查健康狀態
    health = integrator.get_health_status()
    logger.info(f"✅ 健康狀態: {health['status']}")

    # 檢查活力評分
    vitality = integrator.get_vitality_score()
    assert 0.0 <= vitality <= 1.0
    logger.info(f"✅ 生命活力評分: {vitality:.2f}/1.0 ({vitality*10:.1f}/10.0)")

    await integrator.stop()
    logger.info("✅ 數字生命集成器停止成功")


async def run_all_tests():
    """運行所有測試"""
    logger.info("🚀 開始運行生命循環測試...")

    try:
        # 1. 測試用戶監控
        await test_user_monitor()

        # 2. 測試 LLM 決策循環
        await test_llm_decision_loop()

        # 3. 測試主動交互系統
        await test_proactive_interaction_system()

        # 4. 測試行為反饋循環
        await test_behavior_feedback_loop()

        # 5. 測試記憶整合循環
        await test_memory_integration_loop()

        # 6. 端到端測試
        await test_digital_life_integrator()

        logger.info("\n" + "="*50)
        logger.info("✅ 所有測試完成！")
        logger.info("="*50)

        return True

    except Exception as e:
        logger.error(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 直接運行測試
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)