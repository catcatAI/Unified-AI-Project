#!/usr/bin/env python3
"""
組件診斷腳本 - 檢測各個組件的基本功能
"""

import sys
import os
import asyncio
import logging

# 添加src路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComponentDiagnostic:
    """組件診斷類"""
    
    def __init__(self):
        self.test_results = {}
    
    async def diagnose_all_components(self):
        """診斷所有核心組件"""
        logger.info("🔍 開始組件診斷...")
        
        # 診斷各個組件
        await self.diagnose_audio_service()
        await self.diagnose_vision_service()
        await self.diagnose_vector_store()
        await self.diagnose_causal_reasoning()
        
        # 報告結果
        self.report_diagnosis()
    
    async def diagnose_audio_service(self):
        """診斷音頻服務"""
        logger.info("🎵 診斷音頻服務...")
        try:
            from .src.services.audio_service import AudioService
            
            # 創建服務實例
            audio_service = AudioService()
            logger.info("✅ AudioService 初始化成功")
            
            # 測試基本功能
            dummy_audio = b'\x00\x01\x02\x03\x04\x05'
            result = await audio_service.speech_to_text(dummy_audio, language='en-US')
            
            if 'error' not in result:
                logger.info("✅ AudioService speech_to_text 測試通過")
                self.test_results['audio_service'] = 'PASSED'
            else:
                logger.error(f"❌ AudioService speech_to_text 失敗: {result.get('error')}")
                self.test_results['audio_service'] = 'FAILED'
                
        except Exception as e:
            logger.error(f"❌ AudioService 診斷失敗: {e}")
            self.test_results['audio_service'] = f'ERROR: {e}'
    
    async def diagnose_vision_service(self):
        """診斷視覺服務"""
        logger.info("👁️ 診斷視覺服務...")
        try:
            from .src.services.vision_service import VisionService
            
            # 創建服務實例
            vision_service = VisionService()
            logger.info("✅ VisionService 初始化成功")
            
            # 測試基本功能
            dummy_image = b'dummy_image_data'
            result = await vision_service.analyze_image(dummy_image)
            
            if 'error' not in result:
                logger.info("✅ VisionService analyze_image 測試通過")
                self.test_results['vision_service'] = 'PASSED'
            else:
                logger.error(f"❌ VisionService analyze_image 失敗: {result.get('error')}")
                self.test_results['vision_service'] = 'FAILED'
                
        except Exception as e:
            logger.error(f"❌ VisionService 診斷失敗: {e}")
            self.test_results['vision_service'] = f'ERROR: {e}'
    
    async def diagnose_vector_store(self):
        """診斷向量存儲"""
        logger.info("🧠 診斷向量存儲...")
        try:
            from .src.core_ai.memory.vector_store import VectorMemoryStore
            
            # 創建向量存儲實例
            vector_store = VectorMemoryStore(persist_directory="./test_vector_db")
            logger.info("✅ VectorMemoryStore 初始化成功")
            
            # 測試添加記憶
            memory_result = await vector_store.add_memory(
                'test_memory_001',
                'This is a test memory for diagnostics',
                {'test': True}
            )
            
            if memory_result.get('status') == 'success':
                logger.info("✅ VectorMemoryStore add_memory 測試通過")
                
                # 測試統計信息
                stats = await vector_store.get_memory_statistics()
                if 'total_memories' in stats:
                    logger.info("✅ VectorMemoryStore get_memory_statistics 測試通過")
                    self.test_results['vector_store'] = 'PASSED'
                else:
                    logger.error("❌ VectorMemoryStore get_memory_statistics 缺少 total_memories")
                    self.test_results['vector_store'] = 'FAILED'
            else:
                logger.error(f"❌ VectorMemoryStore add_memory 失敗: {memory_result}")
                self.test_results['vector_store'] = 'FAILED'
                
        except Exception as e:
            logger.error(f"❌ VectorMemoryStore 診斷失敗: {e}")
            self.test_results['vector_store'] = f'ERROR: {e}'
    
    async def diagnose_causal_reasoning(self):
        """診斷因果推理引擎"""
        logger.info("🔗 診斷因果推理引擎...")
        try:
            from .src.core_ai.reasoning.causal_reasoning_engine import CausalReasoningEngine
            
            # 創建推理引擎實例
            causal_engine = CausalReasoningEngine(config={'causality_threshold': 0.5})
            logger.info("✅ CausalReasoningEngine 初始化成功")
            
            # 測試因果關係學習
            test_observations = [
                {
                    'id': 'diag_obs_001',
                    'variables': ['x', 'y'],
                    'data': {'x': 1, 'y': 2},
                    'relationships': []
                }
            ]
            
            learned_relationships = await causal_engine.learn_causal_relationships(test_observations)
            
            if isinstance(learned_relationships, list):
                logger.info("✅ CausalReasoningEngine learn_causal_relationships 測試通過")
                self.test_results['causal_reasoning'] = 'PASSED'
            else:
                logger.error("❌ CausalReasoningEngine learn_causal_relationships 返回類型錯誤")
                self.test_results['causal_reasoning'] = 'FAILED'
                
        except Exception as e:
            logger.error(f"❌ CausalReasoningEngine 診斷失敗: {e}")
            self.test_results['causal_reasoning'] = f'ERROR: {e}'
    
    def report_diagnosis(self):
        """報告診斷結果"""
        logger.info("\n" + "="*60)
        logger.info("📊 組件診斷報告")
        logger.info("="*60)
        
        for component, result in self.test_results.items():
            status_icon = "✅" if result == 'PASSED' else "❌"
            logger.info(f"{status_icon} {component}: {result}")
        
        # 統計結果
        passed = len([r for r in self.test_results.values() if r == 'PASSED'])
        total = len(self.test_results)
        
        logger.info(f"\n📈 總結: {passed}/{total} 組件通過診斷")
        
        if passed == total:
            logger.info("🎉 所有組件診斷通過！")
        else:
            logger.warning("⚠️ 某些組件需要修復")

async def main():
    """主函數"""
    diagnostic = ComponentDiagnostic()
    await diagnostic.diagnose_all_components()

if __name__ == "__main__":
    asyncio.run(main())