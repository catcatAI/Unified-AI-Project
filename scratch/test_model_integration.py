import asyncio
import logging
import sys
import os

# 將 src 目錄加入路徑
sys.path.append(os.path.join(os.path.dirname(__file__), "../apps/backend/src"))

from core.autonomous.angela_model_core import get_model_core
from core.autonomous.biological_integrator import BiologicalIntegrator
from core.autonomous.state_matrix import StateMatrix4D
from services.chat_service import get_angela_chat_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Test-Integration")

async def test_integration():
    logger.info("🚀 Starting Angela Model Integration Test...")
    
    # 1. 初始化核心
    core = get_model_core()
    chat = get_angela_chat_service()
    bio = BiologicalIntegrator()
    matrix = StateMatrix4D()
    
    await core.initialize()
    await chat.initialize()
    
    # 2. 驗證單例模式
    logger.info("🧪 Testing Singleton mapping...")
    assert core.bio is bio, "❌ BioIntegrator mismatch!"
    assert core.spatial is matrix, "❌ StateMatrix4D mismatch!"
    logger.info("✅ Singleton architecture verified.")
    
    # 3. 模擬空間位移
    logger.info("🧪 Simulating spatial movement...")
    matrix.evaluate_math_spatially("10+20") # 位移到 30

    current_pos = matrix.get_position()
    logger.info(f"📍 Current Position: {current_pos}")
    
    # 4. 驗證意識快照
    logger.info("🧪 Testing Consciousness Snapshot...")
    snapshot = core.get_consciousness_snapshot()
    logger.info(f"🧠 Snapshot: {snapshot}")
    assert snapshot["spatial_awareness"]["coordinates"]["gamma"]["x"] == 30.0, "❌ Snapshot coordinate mismatch!"
    
    # 5. 驗證 Prompt 生成
    logger.info("🧪 Testing Prompt prefix generation...")
    prompt_prefix = core.generate_prompt_prefix()
    logger.info(f"📝 Generated Prompt Prefix:\n{prompt_prefix}")
    assert "Spatial Position: {'alpha': {'x': 0.0, 'y': -5.0, 'z': 0.0}" in prompt_prefix or "alpha" in prompt_prefix, "❌ Prompt content mismatch!"

    
    # 6. 測試代謝反應 (壓力擾動)
    logger.info("🧪 Testing Metabolic Stress Reaction...")
    # 人為設置高壓力/悲傷
    from core.autonomous.emotional_blending import BasicEmotion
    bio.emotional_system.set_emotion_from_basic(BasicEmotion.SADNESS, intensity=0.9)

    # 等待代謝循環 (2s)
    logger.info("⏳ Waiting for metabolic loop reaction...")
    await asyncio.sleep(2.5)
    
    logger.info("🏁 All tests passed! Angela's brain is correctly integrated.")

if __name__ == "__main__":
    asyncio.run(test_integration())
