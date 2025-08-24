#!/usr/bin/env python3
"""
專案完善腳本 - 整合訓練數據到現有系統
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List

# 添加專案路徑
sys.path.append(str(Path(__file__).parent.parent / "apps" / "backend" / "src"))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProjectEnhancer:
    """專案完善器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.backend_dir = self.project_root / "apps" / "backend"
        
    def check_training_readiness(self) -> Dict[str, bool]:
        """檢查訓練準備狀態"""
        status = {}
        
        # 檢查核心組件
        core_files = [
            "src/core_ai/memory/ham_memory_manager.py",
            "src/core_ai/memory/vector_store.py", 
            "src/core_ai/reasoning/causal_reasoning_engine.py",
            "src/services/vision_service.py",
            "src/services/audio_service.py"
        ]
        
        for file_path in core_files:
            full_path = self.backend_dir / file_path
            status[file_path] = full_path.exists()
            
        return status
    
    def setup_training_environment(self):
        """設置訓練環境"""
        logger.info("🔧 設置訓練環境...")
        
        # 創建訓練目錄結構
        training_dirs = [
            "training/models",
            "training/logs", 
            "training/checkpoints",
            "training/configs"
        ]
        
        for dir_path in training_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 創建目錄: {full_path}")
    
    def generate_training_config(self):
        """生成訓練配置"""
        config = {
            "data_paths": {
                "flickr30k": str(self.data_dir / "flickr30k_sample"),
                "common_voice": str(self.data_dir / "common_voice_zh"),
                "coco": str(self.data_dir / "coco_captions"),
                "visual_genome": str(self.data_dir / "visual_genome_sample")
            },
            "training": {
                "batch_size": 16,
                "epochs": 10,
                "learning_rate": 0.001,
                "save_interval": 100
            },
            "hardware": {
                "use_gpu": True,
                "mixed_precision": True
            }
        }
        
        config_path = self.project_root / "training/configs/training_config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            
        logger.info(f"📝 生成訓練配置: {config_path}")

def main():
    """主函數"""
    print("🚀 Unified-AI-Project 專案完善器")
    print("=" * 40)
    
    enhancer = ProjectEnhancer()
    
    # 檢查組件狀態
    logger.info("🔍 檢查專案組件...")
    status = enhancer.check_training_readiness()
    
    for component, ready in status.items():
        status_icon = "✅" if ready else "❌"
        logger.info(f"{status_icon} {component}")
    
    # 設置訓練環境
    enhancer.setup_training_environment()
    enhancer.generate_training_config()
    
    logger.info("🎉 專案完善完成！")

if __name__ == "__main__":
    main()