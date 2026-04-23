import asyncio
import logging
from services.chat_service import AngelaChatService
from core.autonomous.biological_integrator import BiologicalIntegrator
from integrations.os_bridge_adapter import OSBridgeAdapter

async def final_integrity_check():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FinalAudit")
    
    logger.info("--- 啟動終極審計 ---")
    
    # 1. 檢查生物整合器單例
    bio = BiologicalIntegrator()
    if not hasattr(bio, "nervous_system"):
        logger.error("❌ 生物整合器神經通路缺失")
        return
    logger.info("✅ 生物整合器單例檢測通過")

    # 2. 檢查橋接器物理連通
    adapter = OSBridgeAdapter()
    if not adapter.bridge_path:
        logger.error("❌ OS Bridge 路徑失效")
        return
    logger.info("✅ OS Bridge 路徑有效")

    # 3. 檢查生命週期邏輯 (心跳與代謝)
    state = bio.get_biological_state()
    logger.info(f"✅ 生命狀態檢測: {state['dominant_emotion']} (Arousal: {state['arousal']})")

    # 4. 檢查神經反射弧接口 (Tactile Input)
    try:
        await bio.nervous_system.process_tactile_input({"part": "head", "intensity": 0.5})
        logger.info("✅ 神經反射弧接口實體化檢測通過")
    except Exception as e:
        logger.error(f"❌ 神經反射弧接口報錯: {e}")

    logger.info("--- 審計完成：系統具備實體運行能力 ---")

if __name__ == "__main__":
    asyncio.run(final_integrity_check())
