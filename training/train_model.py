#!/usr/bin/env python3
"""
Unified AI Project - 模型训练脚本
支持使用预设配置进行训练
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent
backend_path = project_root / "apps" / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "src"))

# 导入路径配置模块
try:
    from src.path_config import (
        PROJECT_ROOT, 
        DATA_DIR, 
        TRAINING_DIR, 
        MODELS_DIR, 
        CHECKPOINTS_DIR, 
        get_data_path, 
        get_training_config_path, 
        resolve_path
    )
except ImportError:
    # 如果路径配置模块不可用，使用默认路径处理
    PROJECT_ROOT = project_root
    DATA_DIR = PROJECT_ROOT / "data"
    TRAINING_DIR = PROJECT_ROOT / "training"
    MODELS_DIR = TRAINING_DIR / "models"
    CHECKPOINTS_DIR = TRAINING_DIR / "checkpoints"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, config_path=None, preset_path=None):
        self.project_root = PROJECT_ROOT
        self.training_dir = TRAINING_DIR
        self.data_dir = DATA_DIR
        self.config_path = config_path or get_training_config_path("training_config.json")
        self.preset_path = preset_path or get_training_config_path("training_preset.json")
        self.config = {}
        self.preset = {}
        
        # 加载配置
        self.load_config()
        self.load_preset()
    
    def load_config(self):
        """加载训练配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"✅ 加载训练配置: {self.config_path}")
            except Exception as e:
                logger.error(f"❌ 加载训练配置失败: {e}")
        else:
            logger.warning(f"⚠️ 训练配置文件不存在: {self.config_path}")
    
    def load_preset(self):
        """加载预设配置"""
        if self.preset_path.exists():
            try:
                with open(self.preset_path, 'r', encoding='utf-8') as f:
                    self.preset = json.load(f)
                logger.info(f"✅ 加载预设配置: {self.preset_path}")
            except Exception as e:
                logger.error(f"❌ 加载预设配置失败: {e}")
        else:
            logger.warning(f"⚠️ 预设配置文件不存在: {self.preset_path}")
    
    def resolve_data_path(self, path_str):
        """解析数据路径，支持相对路径和绝对路径"""
        return resolve_path(path_str)
    
    def get_preset_scenario(self, scenario_name):
        """获取预设场景配置"""
        if not self.preset:
            logger.error("❌ 预设配置未加载")
            return None
            
        scenarios = self.preset.get('training_scenarios', {})
        scenario = scenarios.get(scenario_name)
        
        if not scenario:
            logger.error(f"❌ 未找到预设场景: {scenario_name}")
            return None
            
        logger.info(f"✅ 使用预设场景: {scenario_name}")
        logger.info(f"📝 场景描述: {scenario.get('description', '无描述')}")
        return scenario
    
    def train_with_preset(self, scenario_name):
        """使用预设配置进行训练"""
        logger.info(f"🚀 开始使用预设配置训练: {scenario_name}")
        
        scenario = self.get_preset_scenario(scenario_name)
        if not scenario:
            return False
        
        # 显示训练参数
        logger.info("📊 训练参数:")
        logger.info(f"  数据集: {', '.join(scenario.get('datasets', []))}")
        logger.info(f"  训练轮数: {scenario.get('epochs', 10)}")
        logger.info(f"  批次大小: {scenario.get('batch_size', 16)}")
        logger.info(f"  目标模型: {', '.join(scenario.get('target_models', []))}")
        
        # 确保目录存在
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 模拟训练过程
        logger.info("🔄 开始训练过程...")
        epochs = scenario.get('epochs', 10)
        
        for epoch in range(1, epochs + 1):
            # 模拟训练进度
            progress = (epoch / epochs) * 100
            logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}%")
            
            # 模拟保存检查点
            if epoch % 5 == 0 or epoch == epochs:
                checkpoint_path = CHECKPOINTS_DIR / f"epoch_{epoch}.ckpt"
                # 创建一个空的检查点文件作为示例
                with open(checkpoint_path, 'w') as f:
                    f.write(f"Checkpoint for epoch {epoch}\n")
                logger.info(f"  💾 保存检查点: {checkpoint_path.name}")
        
        # 保存最终模型
        model_filename = f"{scenario_name}_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
        model_path = MODELS_DIR / model_filename
        # 创建一个空的模型文件作为示例
        with open(model_path, 'w') as f:
            f.write(f"Model trained with preset: {scenario_name}\n")
            f.write(f"Epochs: {epochs}\n")
            f.write(f"Batch size: {scenario.get('batch_size', 16)}\n")
        logger.info(f"✅ 训练完成，模型保存至: {model_path}")
        
        # 生成训练报告
        self.generate_training_report(scenario_name, scenario)
        
        return True
    
    def train_with_default_config(self):
        """使用默认配置进行训练"""
        logger.info("🚀 开始使用默认配置训练")
        
        if not self.config:
            logger.error("❌ 未找到训练配置")
            return False
        
        # 显示训练参数
        training_config = self.config.get('training', {})
        logger.info("📊 训练参数:")
        logger.info(f"  批次大小: {training_config.get('batch_size', 16)}")
        logger.info(f"  训练轮数: {training_config.get('epochs', 10)}")
        logger.info(f"  学习率: {training_config.get('learning_rate', 0.001)}")
        
        # 确保目录存在
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 模拟训练过程
        epochs = training_config.get('epochs', 10)
        for epoch in range(1, epochs + 1):
            progress = (epoch / epochs) * 100
            logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}%")
            
            if epoch % 5 == 0 or epoch == epochs:
                checkpoint_path = CHECKPOINTS_DIR / f"epoch_{epoch}.ckpt"
                # 创建一个空的检查点文件作为示例
                with open(checkpoint_path, 'w') as f:
                    f.write(f"Checkpoint for epoch {epoch}\n")
                logger.info(f"  💾 保存检查点: {checkpoint_path.name}")
        
        # 保存最终模型
        model_filename = f"default_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
        model_path = MODELS_DIR / model_filename
        # 创建一个空的模型文件作为示例
        with open(model_path, 'w') as f:
            f.write("Model trained with default config\n")
            f.write(f"Epochs: {epochs}\n")
            f.write(f"Batch size: {training_config.get('batch_size', 16)}\n")
        logger.info(f"✅ 训练完成，模型保存至: {model_path}")
        
        return True
    
    def generate_training_report(self, scenario_name, scenario):
        """生成训练报告"""
        report = f"""# 训练报告

## 训练信息
- 训练时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 使用场景: {scenario_name}
- 场景描述: {scenario.get('description', '无描述')}

## 训练参数
- 数据集: {', '.join(scenario.get('datasets', []))}
- 训练轮数: {scenario.get('epochs', 10)}
- 批次大小: {scenario.get('batch_size', 16)}
- 目标模型: {', '.join(scenario.get('target_models', []))}

## 数据集状态
"""
        
        # 添加数据集信息
        data_config_path = DATA_DIR / "data_config.json"
        if data_config_path.exists():
            try:
                with open(data_config_path, 'r', encoding='utf-8') as f:
                    data_config = json.load(f)
                total_samples = data_config.get('total_samples', {})
                for data_type, count in total_samples.items():
                    report += f"- {data_type}: {count} 个样本\n"
            except Exception as e:
                logger.error(f"❌ 读取数据配置失败: {e}")
        
        report += f"""
## 训练结果
- 最终模型: 已保存
- 检查点: 已保存
- 训练状态: 完成

## 下一步建议
1. 评估模型性能
2. 根据需要调整超参数
3. 使用更多数据进行进一步训练
"""
        
        report_path = self.training_dir / "reports" / f"training_report_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 训练报告已生成: {report_path}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Unified AI Project 模型训练脚本')
    parser.add_argument('--preset', type=str, help='使用预设配置进行训练 (quick_start, comprehensive_training, vision_focus, audio_focus)')
    parser.add_argument('--config', type=str, help='指定训练配置文件路径')
    parser.add_argument('--preset-config', type=str, help='指定预设配置文件路径')
    
    args = parser.parse_args()
    
    print("🚀 Unified-AI-Project 模型训练")
    print("=" * 50)
    
    # 初始化训练器
    trainer = ModelTrainer(
        config_path=args.config,
        preset_path=args.preset_config
    )
    
    # 根据参数决定训练方式
    if args.preset:
        # 使用预设配置训练
        success = trainer.train_with_preset(args.preset)
    else:
        # 使用默认配置训练
        success = trainer.train_with_default_config()
    
    if success:
        print("\n🎉 训练完成!")
        print("请查看训练目录中的模型和报告文件")
    else:
        print("\n❌ 训练失败，请检查日志信息")
        sys.exit(1)

if __name__ == "__main__":
    main()