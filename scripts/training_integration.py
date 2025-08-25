#!/usr/bin/env python3
"""
訓練集成腳本 - 演示如何使用生成的數據訓練各個組件
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加項目路徑
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrainingIntegrator:
    """訓練集成器"""
    
    def __init__(self):
        self.project_root = project_root
        self.data_dir = self.project_root / "data"
        self.training_dir = self.project_root / "training"
        
    def load_training_data(self) -> Dict[str, Any]:
        """加載訓練數據"""
        data = {}
        
        try:
            # 加載視覺數據
            vision_path = self.data_dir / "vision_samples" / "annotations.json"
            if vision_path.exists():
                with open(vision_path, 'r', encoding='utf-8') as f:
                    data['vision'] = json.load(f)
                logger.info(f"✅ 加載視覺數據: {len(data['vision'])}個樣本")
            
            # 加載音頻數據
            audio_path = self.data_dir / "audio_samples" / "transcripts.json"
            if audio_path.exists():
                with open(audio_path, 'r', encoding='utf-8') as f:
                    data['audio'] = json.load(f)
                logger.info(f"✅ 加載音頻數據: {len(data['audio'])}個樣本")
            
            # 加載推理數據
            reasoning_path = self.data_dir / "reasoning_samples" / "causal_relations.json"
            if reasoning_path.exists():
                with open(reasoning_path, 'r', encoding='utf-8') as f:
                    data['reasoning'] = json.load(f)
                logger.info(f"✅ 加載推理數據: {len(data['reasoning'])}個樣本")
            
            # 加載多模態數據
            multimodal_path = self.data_dir / "multimodal_samples" / "multimodal_pairs.json"
            if multimodal_path.exists():
                with open(multimodal_path, 'r', encoding='utf-8') as f:
                    data['multimodal'] = json.load(f)
                logger.info(f"✅ 加載多模態數據: {len(data['multimodal'])}個樣本")
                
        except Exception as e:
            logger.error(f"❌ 數據加載失敗: {e}")
        
        return data
    
    async def test_vision_service_integration(self, vision_data: List[Dict]):
        """測試視覺服務集成"""
        logger.info("🔍 測試視覺服務集成...")
        
        try:
            from src.services.vision_service import VisionService
            
            vision_service = VisionService()
            
            # 模擬圖像數據
            mock_image_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
            
            # 測試圖像分析
            for i, sample in enumerate(vision_data[:3]):
                result = await vision_service.analyze_image(
                    mock_image_data,
                    features=["captioning", "object_detection", "scene_analysis"]
                )
                
                logger.info(f"  樣本 {i+1}: {sample['caption']}")
                logger.info(f"  分析結果: {result.get('processing_id', 'N/A')}")
            
            logger.info("✅ 視覺服務集成測試完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 視覺服務集成失敗: {e}")
            return False
    
    async def test_audio_service_integration(self, audio_data: List[Dict]):
        """測試音頻服務集成"""
        logger.info("🔊 測試音頻服務集成...")
        
        try:
            from src.services.audio_service import AudioService
            
            audio_service = AudioService()
            
            # 模擬音頻數據
            mock_audio_data = b'\x00' * 1000
            
            # 測試語音識別
            for i, sample in enumerate(audio_data[:3]):
                result = await audio_service.speech_to_text(
                    mock_audio_data,
                    language=sample.get('language', 'zh-CN'),
                    enhanced_features=True
                )
                
                logger.info(f"  樣本 {i+1}: {sample['text']}")
                logger.info(f"  識別結果: {result.get('processing_id', 'N/A')}")
            
            logger.info("✅ 音頻服務集成測試完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 音頻服務集成失敗: {e}")
            return False
    
    async def test_reasoning_engine_integration(self, reasoning_data: List[Dict]):
        """測試推理引擎集成"""
        logger.info("🧠 測試推理引擎集成...")
        
        try:
            from src.core_ai.reasoning.causal_reasoning_engine import CausalReasoningEngine
            
            reasoning_engine = CausalReasoningEngine({'causality_threshold': 0.5})
            
            # 測試因果學習
            observations = []
            for sample in reasoning_data[:5]:
                observation = {
                    'id': sample['scenario_id'],
                    'variables': sample['variables'],
                    'data': {sample['cause']: 1, sample['effect']: 1},
                    'relationships': []
                }
                observations.append(observation)
            
            relationships = await reasoning_engine.learn_causal_relationships(observations)
            logger.info(f"  學習到 {len(relationships)} 個因果關係")
            
            # 測試反事實推理
            scenario = {
                'name': 'test_scenario',
                'outcome': 'positive',
                'outcome_variable': 'effect'
            }
            intervention = {'variable': 'cause', 'value': 'modified'}
            
            counterfactual = await reasoning_engine.perform_counterfactual_reasoning(scenario, intervention)
            logger.info(f"  反事實推理: {counterfactual.get('counterfactual_outcome', 'N/A')}")
            
            logger.info("✅ 推理引擎集成測試完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 推理引擎集成失敗: {e}")
            return False
    
    async def test_memory_system_integration(self, all_data: Dict[str, List]):
        """測試記憶系統集成"""
        logger.info("🧠 測試記憶系統集成...")
        
        try:
            from src.core_ai.memory.vector_store import VectorMemoryStore
            
            vector_store = VectorMemoryStore(persist_directory="./test_vector_store")
            
            # 添加各類記憶
            memory_count = 0
            for data_type, samples in all_data.items():
                for i, sample in enumerate(samples[:2]):  # 每種類型取2個樣本
                    memory_id = f"{data_type}_memory_{i:03d}"
                    
                    if data_type == 'vision':
                        content = sample.get('caption', '')
                    elif data_type == 'audio':
                        content = sample.get('text', '')
                    elif data_type == 'reasoning':
                        content = f"Causal relationship: {sample.get('cause')} -> {sample.get('effect')}"
                    else:
                        content = str(sample)
                    
                    if content:
                        result = await vector_store.add_memory(
                            memory_id,
                            content,
                            {'data_type': data_type, 'sample_index': i}
                        )
                        if result.get('status') == 'success':
                            memory_count += 1
            
            logger.info(f"  添加了 {memory_count} 個記憶")
            
            # 測試語義搜索
            search_result = await vector_store.semantic_search("learning and intelligence", n_results=3)
            logger.info(f"  搜索結果: {len(search_result.get('documents', []))} 個匹配")
            
            # 獲取統計信息
            stats = await vector_store.get_memory_statistics()
            logger.info(f"  記憶統計: {stats.get('total_memories', 0)} 個總記憶")
            
            logger.info("✅ 記憶系統集成測試完成")
            return True
            
        except Exception as e:
            logger.error(f"❌ 記憶系統集成失敗: {e}")
            return False
    
    def generate_training_report(self, test_results: Dict[str, bool]):
        """生成訓練報告"""
        report = f"""# 訓練集成測試報告

## 測試時間
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 測試結果

"""
        
        total_tests = len(test_results)
        passed_tests = sum(test_results.values())
        
        for test_name, result in test_results.items():
            status = "✅ 通過" if result else "❌ 失敗"
            report += f"- **{test_name}**: {status}\n"
        
        report += f"""
## 總結

- 總測試數: {total_tests}
- 通過測試: {passed_tests}
- 成功率: {(passed_tests/total_tests*100):.1f}%

## 下一步行動

{"### ✅ 系統就緒" if passed_tests == total_tests else "### ⚠️ 需要修復"}

1. 檢查失敗的測試並修復相關問題
2. 使用真實數據進行完整訓練
3. 優化模型性能和準確率
4. 部署到生產環境

## 數據位置

- 訓練數據: `{self.data_dir}`
- 配置文件: `{self.training_dir}/configs/`
- 模型保存: `{self.training_dir}/models/`
"""
        
        report_path = self.training_dir / "integration_test_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 測試報告已生成: {report_path}")

async def main():
    """主函數"""
    print("🚀 Unified-AI-Project 訓練集成測試")
    print("=" * 50)
    
    integrator = TrainingIntegrator()
    
    # 加載訓練數據
    logger.info("📂 加載訓練數據...")
    training_data = integrator.load_training_data()
    
    if not training_data:
        logger.error("❌ 沒有找到訓練數據，請先運行 generate_mock_data.py")
        return
    
    # 運行集成測試
    test_results = {}
    
    if 'vision' in training_data:
        test_results['視覺服務'] = await integrator.test_vision_service_integration(training_data['vision'])
    
    if 'audio' in training_data:
        test_results['音頻服務'] = await integrator.test_audio_service_integration(training_data['audio'])
    
    if 'reasoning' in training_data:
        test_results['推理引擎'] = await integrator.test_reasoning_engine_integration(training_data['reasoning'])
    
    test_results['記憶系統'] = await integrator.test_memory_system_integration(training_data)
    
    # 生成報告
    integrator.generate_training_report(test_results)
    
    # 顯示結果
    print("\n📊 測試結果總結:")
    passed = sum(test_results.values())
    total = len(test_results)
    
    for name, result in test_results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n🎯 成功率: {passed}/{total} ({(passed/total*100):.1f}%)")
    
    if passed == total:
        print("🎉 所有集成測試通過！系統準備就緒。")
    else:
        print("⚠️ 部分測試失敗，請檢查日志和修復問題。")

if __name__ == "__main__":
    asyncio.run(main())