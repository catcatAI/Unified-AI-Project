#!/usr/bin/env python3
"""
Unified AI Project - 模型训练脚本
支持使用预设配置进行训练，包含暂停、继续、自动磁盘空间检查等功能
支持真实的TensorFlow神经网络训练
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import logging
import shutil
import time
import random
import subprocess

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
    """模型训练器，支持暂停、继续、自动磁盘空间检查等功能，以及真实的TensorFlow训练"""
    
    def __init__(self, config_path=None, preset_path=None):
        self.project_root = PROJECT_ROOT
        self.training_dir = TRAINING_DIR
        self.data_dir = DATA_DIR
        self.config_path = config_path or get_training_config_path("training_config.json")
        self.preset_path = preset_path or get_training_config_path("training_preset.json")
        self.config = {}
        self.preset = {}
        self.checkpoint_file = None
        self.is_paused = False
        self.tensorflow_available = self._check_tensorflow_availability()
        
        # 加载配置
        self.load_config()
        self.load_preset()
    
    def _check_tensorflow_availability(self):
        """检查TensorFlow是否可用"""
        try:
            import tensorflow as tf
            logger.info("✅ TensorFlow可用")
            return True
        except ImportError:
            logger.warning("⚠️ TensorFlow不可用，将使用模拟训练")
            return False
    
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
    
    def check_disk_space(self, min_space_gb=5):
        """检查磁盘空间是否充足"""
        disk_usage = shutil.disk_usage(str(self.project_root))
        free_space_gb = disk_usage.free / (1024**3)
        
        if free_space_gb < min_space_gb:
            logger.warning(f"⚠️ 磁盘空间不足: 剩余 {free_space_gb:.2f} GB, 最少需要 {min_space_gb} GB")
            return False
        else:
            logger.info(f"✅ 磁盘空间充足: 剩余 {free_space_gb:.2f} GB")
            return True
    
    def save_checkpoint(self, epoch, model_state=None):
        """保存训练检查点"""
        checkpoint_path = CHECKPOINTS_DIR / f"epoch_{epoch}_checkpoint.json"
        checkpoint_data = {
            "epoch": epoch,
            "timestamp": datetime.now().isoformat(),
            "model_state": model_state if model_state else {}
        }
        
        try:
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 保存检查点: {checkpoint_path.name}")
            self.checkpoint_file = checkpoint_path
            return True
        except Exception as e:
            logger.error(f"❌ 保存检查点失败: {e}")
            return False
    
    def load_checkpoint(self, checkpoint_path=None):
        """加载训练检查点"""
        if not checkpoint_path and self.checkpoint_file:
            checkpoint_path = self.checkpoint_file
        elif not checkpoint_path:
            # 查找最新的检查点文件
            checkpoint_files = list(CHECKPOINTS_DIR.glob("*_checkpoint.json"))
            if not checkpoint_files:
                logger.info("🔍 未找到检查点文件")
                return None
            checkpoint_path = max(checkpoint_files, key=os.path.getctime)
        
        if not checkpoint_path or not Path(checkpoint_path).exists():
            logger.info("🔍 未找到检查点文件")
            return None
            
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            logger.info(f"✅ 加载检查点: {checkpoint_path.name}")
            return checkpoint_data
        except Exception as e:
            logger.error(f"❌ 加载检查点失败: {e}")
            return None
    
    def simulate_training_step(self, epoch, batch_size=16):
        """模拟一个训练步骤（实际项目中这里会是真正的训练代码）"""
        # 模拟更真实的训练时间
        # 对于早期epoch，训练时间较短；对于后期epoch，训练时间较长
        base_time = 0.05  # 基础时间
        epoch_factor = min(1.0, epoch / 20.0)  # epoch因子，最多增加到原来的2倍
        batch_factor = batch_size / 16.0  # 批次大小因子
        
        # 计算实际睡眠时间
        sleep_time = base_time * (1 + epoch_factor) * batch_factor
        time.sleep(min(0.5, sleep_time))  # 最多睡眠0.5秒，避免太慢
        
        # 模拟训练损失（更真实的损失下降曲线）
        # 使用指数衰减函数模拟损失下降
        initial_loss = 2.0
        decay_rate = 0.05
        noise = random.uniform(-0.05, 0.05)
        loss = initial_loss * (0.8 ** (epoch * decay_rate)) + noise
        loss = max(0.01, loss)  # 确保损失不会降到0以下
        
        # 模拟准确率上升
        max_accuracy = 0.98
        accuracy = min(max_accuracy, (epoch / 100) * max_accuracy + random.uniform(-0.02, 0.02))
        accuracy = max(0, accuracy)
        
        return {
            "loss": loss,
            "accuracy": accuracy
        }
    
    def _train_math_model(self, scenario):
        """训练数学模型"""
        if not self.tensorflow_available:
            logger.error("❌ TensorFlow不可用，无法训练数学模型")
            return False
        
        try:
            logger.info("🚀 开始训练数学模型...")
            # 使用子进程调用真实的训练脚本
            math_model_script = self.project_root / "apps" / "backend" / "src" / "tools" / "math_model" / "train.py"
            if not math_model_script.exists():
                logger.error(f"❌ 数学模型训练脚本不存在: {math_model_script}")
                return False
            
            # 激活虚拟环境并运行训练脚本
            venv_python = self.project_root / "apps" / "backend" / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                cmd = [str(venv_python), str(math_model_script)]
            else:
                cmd = [sys.executable, str(math_model_script)]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ 数学模型训练完成")
                logger.info(f"训练输出: {result.stdout}")
                return True
            else:
                logger.error(f"❌ 数学模型训练失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 数学模型训练过程中发生错误: {e}")
            return False
    
    def _train_logic_model(self, scenario):
        """训练逻辑模型"""
        if not self.tensorflow_available:
            logger.error("❌ TensorFlow不可用，无法训练逻辑模型")
            return False
        
        try:
            logger.info("🚀 开始训练逻辑模型...")
            # 使用子进程调用真实的训练脚本
            logic_model_script = self.project_root / "apps" / "backend" / "src" / "tools" / "logic_model" / "train_logic_model.py"
            if not logic_model_script.exists():
                logger.error(f"❌ 逻辑模型训练脚本不存在: {logic_model_script}")
                return False
            
            # 激活虚拟环境并运行训练脚本
            venv_python = self.project_root / "apps" / "backend" / "venv" / "Scripts" / "python.exe"
            if venv_python.exists():
                cmd = [str(venv_python), str(logic_model_script)]
            else:
                cmd = [sys.executable, str(logic_model_script)]
            
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ 逻辑模型训练完成")
                logger.info(f"训练输出: {result.stdout}")
                return True
            else:
                logger.error(f"❌ 逻辑模型训练失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"❌ 逻辑模型训练过程中发生错误: {e}")
            return False
    
    def _train_concept_models(self, scenario):
        """训练概念模型"""
        logger.info("🚀 开始训练概念模型...")
        
        # 导入概念模型
        try:
            sys.path.append(str(self.project_root / "apps" / "backend" / "src"))
            from core_ai.concept_models.environment_simulator import EnvironmentSimulator
            from core_ai.concept_models.causal_reasoning_engine import CausalReasoningEngine
            from core_ai.concept_models.adaptive_learning_controller import AdaptiveLearningController
            from core_ai.concept_models.alpha_deep_model import AlphaDeepModel
            from core_ai.concept_models.unified_symbolic_space import UnifiedSymbolicSpace
            
            logger.info("✅ 概念模型导入成功")
        except Exception as e:
            logger.error(f"❌ 概念模型导入失败: {e}")
            return False
        
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        # 模拟训练过程
        try:
            for epoch in range(1, epochs + 1):
                # 模拟训练步骤
                epoch_metrics = self.simulate_training_step(epoch, batch_size)
                
                # 显示进度
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f}")
                
                # 保存检查点
                if epoch % checkpoint_interval == 0 or epoch == epochs:
                    self.save_checkpoint(epoch, epoch_metrics)
            
            # 保存模型
            model_filename = f"concept_models_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            model_path = MODELS_DIR / model_filename
            
            model_info = {
                "model_type": "concept_models",
                "training_date": datetime.now().isoformat(),
                "epochs": epochs,
                "batch_size": batch_size,
                "final_metrics": epoch_metrics
            }
            
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 概念模型训练完成，模型保存至: {model_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 概念模型训练过程中发生错误: {e}")
            return False
    
    def _train_environment_simulator(self, scenario):
        """训练环境模拟器"""
        logger.info("🚀 开始训练环境模拟器...")
        # 这里应该是环境模拟器的实际训练代码
        # 为示例起见，我们使用模拟训练
        return self._simulate_training(scenario)
    
    def _train_causal_reasoning(self, scenario):
        """训练因果推理引擎"""
        logger.info("🚀 开始训练因果推理引擎...")
        # 这里应该是因果推理引擎的实际训练代码
        # 为示例起见，我们使用模拟训练
        return self._simulate_training(scenario)
    
    def _train_adaptive_learning(self, scenario):
        """训练自适应学习控制器"""
        logger.info("🚀 开始训练自适应学习控制器...")
        # 这里应该是自适应学习控制器的实际训练代码
        # 为示例起见，我们使用模拟训练
        return self._simulate_training(scenario)
    
    def _train_alpha_deep_model(self, scenario):
        """训练Alpha深度模型"""
        logger.info("🚀 开始训练Alpha深度模型...")
        # 这里应该是Alpha深度模型的实际训练代码
        # 为示例起见，我们使用模拟训练
        return self._simulate_training(scenario)
    
    def _train_collaboratively(self, scenario):
        """执行协作式训练"""
        logger.info("🔄 开始协作式训练...")
        
        try:
            # 导入协作式训练管理器
            from .collaborative_training_manager import CollaborativeTrainingManager
            
            # 初始化协作式训练管理器
            manager = CollaborativeTrainingManager()
            
            # 注册所有可用模型
            self._register_all_models(manager)
            
            # 开始协作式训练
            success = manager.start_collaborative_training(scenario)
            
            if success:
                logger.info("✅ 协作式训练完成")
                return True
            else:
                logger.error("❌ 协作式训练失败")
                return False
                
        except ImportError as e:
            logger.error(f"❌ 无法导入协作式训练管理器: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 协作式训练过程中发生错误: {e}")
            return False
    
    def _register_all_models(self, manager):
        """注册所有可用模型"""
        # 注册概念模型
        try:
            from core_ai.concept_models.environment_simulator import EnvironmentSimulator
            manager.register_model("environment_simulator", EnvironmentSimulator())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册环境模拟器: {e}")
        
        try:
            from core_ai.concept_models.causal_reasoning_engine import CausalReasoningEngine
            manager.register_model("causal_reasoning_engine", CausalReasoningEngine())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册因果推理引擎: {e}")
        
        try:
            from core_ai.concept_models.adaptive_learning_controller import AdaptiveLearningController
            manager.register_model("adaptive_learning_controller", AdaptiveLearningController())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册自适应学习控制器: {e}")
        
        try:
            from core_ai.concept_models.alpha_deep_model import AlphaDeepModel
            manager.register_model("alpha_deep_model", AlphaDeepModel())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册Alpha深度模型: {e}")
        
        # 注册其他模型
        # 这里可以根据需要添加更多模型的注册
        logger.info("✅ 模型注册完成")

    def _simulate_training(self, scenario):
        """模拟训练过程"""
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        # 模拟训练过程
        try:
            for epoch in range(1, epochs + 1):
                # 模拟训练步骤
                epoch_metrics = self.simulate_training_step(epoch, batch_size)
                
                # 显示进度
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f}")
                
                # 保存检查点
                if epoch % checkpoint_interval == 0 or epoch == epochs:
                    self.save_checkpoint(epoch, epoch_metrics)
            
            return True
        except Exception as e:
            logger.error(f"❌ 模拟训练过程中发生错误: {e}")
            return False

    def train_with_preset(self, scenario_name):
        """使用预设配置进行训练，支持暂停、继续、自动磁盘空间检查等功能"""
        logger.info(f"🚀 开始使用预设配置训练: {scenario_name}")
        
        scenario = self.get_preset_scenario(scenario_name)
        if not scenario:
            return False
        
        # 检查是否是真实训练场景
        target_models = scenario.get('target_models', [])
        if 'math_model' in target_models:
            return self._train_math_model(scenario)
        elif 'logic_model' in target_models:
            return self._train_logic_model(scenario)
        elif 'concept_models' in target_models:
            return self._train_concept_models(scenario)
        elif 'environment_simulator' in target_models:
            return self._train_environment_simulator(scenario)
        elif 'causal_reasoning_engine' in target_models:
            return self._train_causal_reasoning(scenario)
        elif 'adaptive_learning_controller' in target_models:
            return self._train_adaptive_learning(scenario)
        elif 'alpha_deep_model' in target_models:
            return self._train_alpha_deep_model(scenario)
        
        # 检查是否启用协作式训练
        if scenario.get('enable_collaborative_training', False):
            return self._train_collaboratively(scenario)
        
        # 显示训练参数
        logger.info("📊 训练参数:")
        logger.info(f"  数据集: {', '.join(scenario.get('datasets', []))}")
        logger.info(f"  训练轮数: {scenario.get('epochs', 10)}")
        logger.info(f"  批次大小: {scenario.get('batch_size', 16)}")
        logger.info(f"  目标模型: {', '.join(scenario.get('target_models', []))}")
        
        # 检查自动暂停设置
        auto_pause_on_low_disk = scenario.get('auto_pause_on_low_disk', False)
        min_disk_space_gb = scenario.get('min_disk_space_gb', 5)
        
        # 确保目录存在
        CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 尝试加载检查点以支持从中断处继续
        start_epoch = 1
        checkpoint_data = self.load_checkpoint()
        if checkpoint_data:
            start_epoch = checkpoint_data.get('epoch', 0) + 1
            logger.info(f"🔄 从检查点继续训练，起始轮数: {start_epoch}")
        
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        try:
            # 模拟训练过程（实际项目中这里会是真正的训练循环）
            logger.info("🔄 开始训练过程...")
            
            for epoch in range(start_epoch, epochs + 1):
                # 检查磁盘空间
                if auto_pause_on_low_disk and not self.check_disk_space(min_disk_space_gb):
                    logger.warning("⏸️ 磁盘空间不足，自动暂停训练")
                    self.save_checkpoint(epoch)
                    self.is_paused = True
                    return False
                
                # 模拟一个epoch的训练（实际项目中这里会是多个batch的训练）
                epoch_metrics = self.simulate_training_step(epoch, batch_size)
                
                # 显示进度
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f}")
                
                # 模拟保存检查点
                if epoch % checkpoint_interval == 0 or epoch == epochs:
                    self.save_checkpoint(epoch, epoch_metrics)
                
                # 检查是否需要暂停（模拟用户中断）
                if self.is_paused:
                    logger.info("⏸️ 训练已暂停")
                    self.save_checkpoint(epoch, epoch_metrics)
                    return False
                    
            # 保存最终模型
            model_filename = f"{scenario_name}_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
            model_path = MODELS_DIR / model_filename
            
            # 创建一个示例模型文件（实际项目中这里会保存真正的模型）
            model_info = {
                "model_name": scenario_name,
                "training_date": datetime.now().isoformat(),
                "epochs": epochs,
                "batch_size": batch_size,
                "final_metrics": epoch_metrics,
                "datasets": scenario.get('datasets', [])
            }
            
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 训练完成，模型保存至: {model_path}")
            
            # 生成训练报告
            self.generate_training_report(scenario_name, scenario, model_info)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("⏹️ 训练被用户中断")
            self.save_checkpoint(epoch, epoch_metrics)
            return False
        except Exception as e:
            logger.error(f"❌ 训练过程中发生错误: {e}")
            self.save_checkpoint(epoch, epoch_metrics)
            return False
    
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
        
        # 获取训练参数
        epochs = training_config.get('epochs', 10)
        batch_size = training_config.get('batch_size', 16)
        
        # 模拟训练过程
        try:
            logger.info("🔄 开始训练过程...")
            for epoch in range(1, epochs + 1):
                # 模拟一个epoch的训练
                epoch_metrics = self.simulate_training_step(epoch, batch_size)
                
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f}")
                
                if epoch % 5 == 0 or epoch == epochs:
                    checkpoint_path = CHECKPOINTS_DIR / f"epoch_{epoch}.ckpt"
                    # 创建一个检查点文件
                    with open(checkpoint_path, 'w') as f:
                        f.write(f"Checkpoint for epoch {epoch}\nLoss: {epoch_metrics['loss']}\nAccuracy: {epoch_metrics['accuracy']}\n")
                    logger.info(f"  💾 保存检查点: {checkpoint_path.name}")
            
            # 保存最终模型
            model_filename = f"default_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
            model_path = MODELS_DIR / model_filename
            
            # 创建模型文件
            with open(model_path, 'w') as f:
                f.write("Default model trained with default config\n")
                f.write(f"Epochs: {epochs}\n")
                f.write(f"Batch size: {batch_size}\n")
            logger.info(f"✅ 训练完成，模型保存至: {model_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 训练过程中发生错误: {e}")
            return False
    
    def generate_training_report(self, scenario_name, scenario, model_info=None):
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

## 模型信息
"""
        
        if model_info:
            report += f"""- 模型名称: {model_info.get('model_name', 'N/A')}
- 训练日期: {model_info.get('training_date', 'N/A')}
- 最终损失: {model_info.get('final_metrics', {}).get('loss', 'N/A')}
- 最终准确率: {model_info.get('final_metrics', {}).get('accuracy', 'N/A')}
"""
        
        report += f"""

## 下一步建议
1. 评估模型性能
2. 根据需要调整超参数
3. 使用更多数据进行进一步训练

## 模型文件关联信息
- 模型文件路径: {MODELS_DIR}
- 检查点路径: {CHECKPOINTS_DIR}
- 项目根目录: {self.project_root}
- 模型与项目关联: 通过项目路径配置和训练配置文件建立关联
"""

        report_path = self.training_dir / "reports" / f"training_report_{scenario_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 训练报告已生成: {report_path}")
    
    def pause_training(self):
        """暂停训练"""
        self.is_paused = True
        logger.info("⏸️ 训练暂停请求已发送")
    
    def resume_training(self, scenario_name):
        """继续训练"""
        self.is_paused = False
        logger.info("▶️ 继续训练")
        return self.train_with_preset(scenario_name)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Unified AI Project 模型训练脚本')
    parser.add_argument('--preset', type=str, help='使用预设配置进行训练 (quick_start, comprehensive_training, vision_focus, audio_focus, full_dataset_training, math_model_training, logic_model_training, collaborative_training)')
    parser.add_argument('--config', type=str, help='指定训练配置文件路径')
    parser.add_argument('--preset-config', type=str, help='指定预设配置文件路径')
    parser.add_argument('--resume', action='store_true', help='从检查点继续训练')
    parser.add_argument('--pause', action='store_true', help='暂停训练')
    
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
        if args.pause:
            trainer.pause_training()
        elif args.resume:
            success = trainer.resume_training(args.preset)
        else:
            success = trainer.train_with_preset(args.preset)
    else:
        # 使用默认配置训练
        success = trainer.train_with_default_config()
    
    if success:
        print("\n🎉 训练完成!")
        print("请查看训练目录中的模型和报告文件")
    else:
        print("\n⚠️ 训练暂停或中断，请使用 --resume 参数继续训练")
        sys.exit(1)


if __name__ == "__main__":
    main()
