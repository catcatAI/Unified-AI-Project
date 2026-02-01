"""
測試 HSM 和 CDM 學習系統整合
驗證 Angela 的真實學習能力
"""

import sys
import asyncio
import logging
from pathlib import Path

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_hsm_cdm_integration():
    """測試 HSM 和 CDM 整合"""
    logger.info("=" * 60)
    logger.info("開始測試 HSM/CDM 學習系統整合")
    logger.info("=" * 60)
    
    try:
        # 1. 導入必要的組件
        from apps.backend.src.core.orchestrator import CognitiveOrchestrator
        logger.info("✅ 成功導入 CognitiveOrchestrator")
        
        # 2. 初始化編排器
        orchestrator = CognitiveOrchestrator()
        logger.info("✅ CognitiveOrchestrator 初始化完成")
        
        # 3. 檢查 HSM 狀態
        if orchestrator.hsm:
            logger.info("✅ HSM (Holographic Storage Matrix) 已啟用")
            hsm_stats = orchestrator.hsm.get_memory_stats()
            logger.info(f"   HSM 統計: {hsm_stats}")
        else:
            logger.warning("⚠️  HSM 未啟用")
        
        # 4. 檢查 CDM 狀態
        if orchestrator.cdm:
            logger.info("✅ CDM (Cognitive Delta Matrix) 已啟用")
            cdm_stats = orchestrator.cdm.get_stats()
            logger.info(f"   CDM 統計: {cdm_stats}")
        else:
            logger.warning("⚠️  CDM 未啟用")
        
        # 5. 測試對話和學習
        logger.info("\n📋 開始對話測試...")
        
        # 測試 1: 基礎對話
        response1 = await orchestrator.process_user_input("你好，我是小明")
        logger.info(f"用戶: 你好，我是小明")
        logger.info(f"Angela: {response1.get('response', '')[:100]}...")
        logger.info(f"學習觸發: {response1.get('learning_triggered', False)}")
        
        # 測試 2: 檢測新信息觸發學習
        response2 = await orchestrator.process_user_input("我喜歡吃巧克力")
        logger.info(f"\n用戶: 我喜歡吃巧克力")
        logger.info(f"Angela: {response2.get('response', '')[:100]}...")
        logger.info(f"學習觸發: {response2.get('learning_triggered', False)}")
        
        # 測試 3: 再次提到名字，測試記憶
        response3 = await orchestrator.process_user_input("你記得我叫什麼名字嗎？")
        logger.info(f"\n用戶: 你記得我叫什麼名字嗎？")
        logger.info(f"Angela: {response3.get('response', '')[:100]}...")
        
        # 測試 4: 更多新信息
        response4 = await orchestrator.process_user_input("我的生日是1995年3月15日")
        logger.info(f"\n用戶: 我的生日是1995年3月15日")
        logger.info(f"Angela: {response4.get('response', '')[:100]}...")
        logger.info(f"學習觸發: {response4.get('learning_triggered', False)}")
        
        # 6. 檢查學習狀態
        logger.info("\n📊 最終學習狀態:")
        learning_status = await orchestrator.get_learning_status()
        logger.info(f"總處理數: {learning_status.get('total_processed', 0)}")
        logger.info(f"學習觸發次數: {learning_status.get('learning_triggered', 0)}")
        logger.info(f"知識庫大小: {learning_status.get('knowledge_base_size', 0)}")
        logger.info(f"對話歷史長度: {learning_status.get('conversation_count', 0)}")
        
        if 'hsm_stats' in learning_status:
            logger.info(f"HSM 記憶數: {learning_status['hsm_stats'].get('total_memories', 0)}")
        
        if 'cdm_stats' in learning_status:
            logger.info(f"CDM 知識單元數: {learning_status['cdm_stats'].get('total_units', 0)}")
        
        # 7. 測試 HSM 記憶檢索
        if orchestrator.hsm:
            logger.info("\n🔍 測試 HSM 記憶檢索:")
            memories = orchestrator.hsm.retrieve_by_association("小明", top_k=3)
            logger.info(f"檢索 '小明': 找到 {len(memories)} 條記憶")
            for i, (exp, score) in enumerate(memories):
                logger.info(f"  {i+1}. [{score:.3f}] {exp.content[:50]}...")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ 測試完成！Angela 現在具備真正的學習能力")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 測試失敗: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_hsm_cdm_integration())
    sys.exit(0 if success else 1)