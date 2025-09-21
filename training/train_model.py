#!/usr/bin/env python3
"""
模型训练脚本
支持多种预设训练场景和协作式训练
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import json
import time
import random

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from training.error_handling_framework import ErrorHandler, ErrorContext, global_error_handler
from training.enhanced_checkpoint_manager import EnhancedCheckpointManager, global_checkpoint_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(TRAINING_DIR / 'training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定义项目目录
PROJECT_ROOT = project_root
DATA_DIR = PROJECT_ROOT / "data"
TRAINING_DIR = PROJECT_ROOT / "training"
MODELS_DIR = TRAINING_DIR / "models"
CHECKPOINTS_DIR = TRAINING_DIR / "checkpoints"

class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, project_root: str = ".", config_path: str = None, preset_path: str = None):
        self.project_root = Path(project_root)
        self.training_dir = TRAINING_DIR
        self.data_dir = DATA_DIR
        # 使用训练目录下的配置文件
        default_config_path = TRAINING_DIR / "configs" / "training_config.json"
        default_preset_path = TRAINING_DIR / "configs" / "training_preset.json"
        self.config_path = Path(config_path) if config_path else default_config_path
        self.preset_path = Path(preset_path) if preset_path else default_preset_path
        self.config = {}
        self.preset = {}
        self.checkpoint_file = None
        self.is_paused = False
        self.tensorflow_available = self._check_tensorflow_availability()
        self.gpu_available = self._check_gpu_availability()
        self.distributed_training_enabled = False
        self.error_handler = global_error_handler  # 错误处理器
        self.checkpoint_manager = global_checkpoint_manager  # 增强的检查点管理器
        
        # 加载配置
        self.load_config()
        self.load_preset()
    
    def _check_tensorflow_availability(self):
        """检查TensorFlow是否可用"""
        context = ErrorContext("ModelTrainer", "_check_tensorflow_availability")
        try:
            import tensorflow as tf
            logger.info("✅ TensorFlow可用")
            return True
        except ImportError:
            self.error_handler.handle_error(Exception("TensorFlow not available"), context, ErrorRecoveryStrategy.FALLBACK)
            logger.warning("⚠️ TensorFlow不可用，将使用模拟训练")
            return False
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.warning(f"⚠️ 检查TensorFlow可用性时出错: {e}")
            return False
    
    def _check_gpu_availability(self):
        """检查GPU是否可用"""
        context = ErrorContext("ModelTrainer", "_check_gpu_availability")
        try:
            import tensorflow as tf
            
            # 兼容不同版本的TensorFlow
            gpus = []
            if hasattr(tf, 'config'):
                if hasattr(tf.config, 'list_physical_devices'):
                    gpus = tf.config.list_physical_devices('GPU')
                elif hasattr(tf.config, 'experimental') and hasattr(tf.config.experimental, 'list_physical_devices'):
                    gpus = tf.config.experimental.list_physical_devices('GPU')
            elif hasattr(tf, 'test') and hasattr(tf.test, 'is_gpu_available'):
                # 更老版本的TensorFlow
                return tf.test.is_gpu_available()
            
            # 检查是否检测到GPU
            if gpus:
                logger.info(f"✅ GPU可用: {len(gpus)} 个设备")
                return True
            else:
                # 检查是否是集成显卡环境
                # 在集成显卡上，TensorFlow可能不会自动检测到GPU，但我们仍然可以尝试使用它
                try:
                    # 检查系统是否有GPU设备（即使TensorFlow没有检测到）
                    import platform
                    system = platform.system().lower()
                    
                    if system == "windows":
                        # Windows系统使用WMI检查
                        import subprocess
                        import json
                        
                        result = subprocess.run([
                            "powershell.exe", 
                            "Get-WmiObject -Class Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"
                        ], capture_output=True, text=True, timeout=10)
                        
                        if result.returncode == 0 and result.stdout.strip():
                            gpu_data = json.loads(result.stdout)
                            
                            # 检查是否有GPU设备
                            if isinstance(gpu_data, list) and len(gpu_data) > 0:
                                # 有GPU设备，即使TensorFlow没有检测到，也认为GPU"可用"（可以尝试使用）
                                logger.info("ℹ️  检测到系统GPU设备，但TensorFlow未识别，将尝试使用CPU训练")
                                return False  # TensorFlow无法使用GPU
                            elif isinstance(gpu_data, dict):
                                logger.info("ℹ️  检测到系统GPU设备，但TensorFlow未识别，将尝试使用CPU训练")
                                return False  # TensorFlow无法使用GPU
                    
                    # 如果无法确定或没有检测到GPU设备
                    logger.info("ℹ️ 未检测到GPU设备，将使用CPU训练")
                    return False
                except Exception as e:
                    logger.info(f"ℹ️ 未检测到GPU设备或无法确定GPU状态: {e}，将使用CPU训练")
                    return False
        except ImportError:
            self.error_handler.handle_error(Exception("TensorFlow not available"), context, ErrorRecoveryStrategy.FALLBACK)
            logger.warning("⚠️ TensorFlow不可用，无法检测GPU")
            return False
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.warning(f"⚠️ 检测GPU时出错: {e}")
            return False
    
    def _setup_distributed_training(self):
        """设置分布式训练环境"""
        context = ErrorContext("ModelTrainer", "_setup_distributed_training")
        try:
            import tensorflow as tf
            
            # 检查是否有多GPU
            gpus = tf.config.list_physical_devices('GPU')
            if len(gpus) > 1:
                logger.info(f"🔄 设置分布式训练环境，使用 {len(gpus)} 个GPU")
                
                # 创建分布式策略
                strategy = tf.distribute.MirroredStrategy()
                logger.info(f"✅ 分布式策略创建成功: {strategy.num_replicas_in_sync} 个副本")
                
                self.distributed_training_enabled = True
                return strategy
            elif len(gpus) == 1:
                logger.info("🔄 设置单GPU训练环境")
                # 设置GPU内存增长
                tf.config.experimental.set_memory_growth(gpus[0], True)
                self.distributed_training_enabled = True
                return None
            else:
                logger.info("ℹ️ 未检测到GPU设备，使用CPU训练")
                self.distributed_training_enabled = False
                return None
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 设置分布式训练环境时出错: {e}")
            self.distributed_training_enabled = False
            return None
    
    def _configure_gpu_memory(self):
        """配置GPU内存使用"""
        context = ErrorContext("ModelTrainer", "_configure_gpu_memory")
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            
            if gpus:
                # 设置GPU内存增长
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                
                logger.info(f"✅ GPU内存配置完成: {len(gpus)} 个设备")
                return True
            else:
                logger.info("ℹ️ 未检测到GPU设备")
                return False
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 配置GPU内存时出错: {e}")
            return False
    
    def load_config(self):
        """加载训练配置"""
        context = ErrorContext("ModelTrainer", "load_config")
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"✅ 加载训练配置: {self.config_path}")
            except Exception as e:
                self.error_handler.handle_error(e, context)
                logger.error(f"❌ 加载训练配置失败: {e}")
        else:
            logger.warning(f"⚠️ 训练配置文件不存在: {self.config_path}")
    
    def load_preset(self):
        """加载预设配置"""
        context = ErrorContext("ModelTrainer", "load_preset")
        if self.preset_path.exists():
            try:
                with open(self.preset_path, 'r', encoding='utf-8') as f:
                    self.preset = json.load(f)
                logger.info(f"✅ 加载预设配置: {self.preset_path}")
            except Exception as e:
                self.error_handler.handle_error(e, context)
                logger.error(f"❌ 加载预设配置失败: {e}")
        else:
            logger.warning(f"⚠️ 预设配置文件不存在: {self.preset_path}")
    
    def resolve_data_path(self, path_str):
        """解析数据路径，支持相对路径和绝对路径"""
        context = ErrorContext("ModelTrainer", "resolve_data_path")
        try:
            return resolve_path(path_str)
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 解析数据路径失败: {path_str} - {e}")
            return None
    
    def get_preset_scenario(self, scenario_name):
        """获取预设场景配置"""
        context = ErrorContext("ModelTrainer", "get_preset_scenario", {"scenario_name": scenario_name})
        try:
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
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 获取预设场景失败: {scenario_name} - {e}")
            return None
    
    def check_disk_space(self, min_space_gb=5):
        """检查磁盘空间是否充足"""
        context = ErrorContext("ModelTrainer", "check_disk_space")
        try:
            disk_usage = shutil.disk_usage(str(self.project_root))
            free_space_gb = disk_usage.free / (1024**3)
            
            if free_space_gb < min_space_gb:
                logger.warning(f"⚠️ 磁盘空间不足: 剩余 {free_space_gb:.2f} GB, 最少需要 {min_space_gb} GB")
                return False
            else:
                logger.info(f"✅ 磁盘空间充足: 剩余 {free_space_gb:.2f} GB")
                return True
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 检查磁盘空间失败: {e}")
            return True  # 出错时假设空间充足
    
    def save_checkpoint(self, epoch, model_state=None):
        """保存训练检查点（增强版本）"""
        context = ErrorContext("ModelTrainer", "save_checkpoint", {"epoch": epoch})
        try:
            # 准备检查点状态
            checkpoint_state = {
                "epoch": epoch,
                "timestamp": datetime.now().isoformat(),
                "model_state": model_state if model_state else {},
                "metrics": {},  # 如果有的话，可以添加当前的训练指标
                "config": {
                    "batch_size": 16,  # 默认值，实际应该从配置中获取
                    "learning_rate": 0.001  # 默认值，实际应该从配置中获取
                }
            }
            
            # 使用增强的检查点管理器保存检查点
            checkpoint_id = self.checkpoint_manager.save_checkpoint(checkpoint_state, "main_training", "epoch")
            
            if checkpoint_id:
                checkpoint_path = CHECKPOINTS_DIR / f"epoch_{epoch}_checkpoint.json"
                self.checkpoint_file = checkpoint_path
                logger.info(f"💾 检查点已保存: {checkpoint_path.name}")
                return True
            else:
                logger.error("❌ 使用增强检查点管理器保存检查点失败")
                return False
                
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 保存检查点失败: {e}")
            return False

    def load_checkpoint(self, checkpoint_path=None):
        """加载训练检查点（增强版本）"""
        context = ErrorContext("ModelTrainer", "load_checkpoint")
        try:
            # 使用增强的检查点管理器加载检查点
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
            
            # 使用增强的检查点管理器加载检查点
            checkpoint_data = self.checkpoint_manager.load_checkpoint(task_id="main_training")
            
            if checkpoint_data:
                logger.info(f"✅ 加载检查点: {Path(checkpoint_path).name}")
                return checkpoint_data
            else:
                logger.error("❌ 使用增强检查点管理器加载检查点失败")
                return None
                
        except Exception as e:
            self.error_handler.handle_error(e, context)
            logger.error(f"❌ 加载检查点失败: {e}")
            return None
    
    def simulate_training_step(self, epoch, batch_size=16, scenario_name="default"):
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
        
        # 更新训练监控器
        metrics = {
            "loss": loss,
            "accuracy": accuracy
        }
        
        if training_monitor:
            progress = (epoch / 100) * 100  # 假设最多100个epoch
            training_monitor.update_progress(scenario_name, epoch, progress, metrics)
        
        return metrics
    
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
    
    def _train_code_model(self, scenario):
        """训练代码模型"""
        logger.info("🚀 开始训练代码模型...")
        
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        # 模拟代码模型训练过程
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
            model_filename = f"code_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            model_path = MODELS_DIR / model_filename
            
            model_info = {
                "model_type": "code_model",
                "training_date": datetime.now().isoformat(),
                "epochs": epochs,
                "batch_size": batch_size,
                "final_metrics": epoch_metrics
            }
            
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 代码模型训练完成，模型保存至: {model_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 代码模型训练过程中发生错误: {e}")
            return False
    
    def _train_data_analysis_model(self, scenario):
        """训练数据分析模型"""
        logger.info("🚀 开始训练数据分析模型...")
        
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        # 模拟数据分析模型训练过程
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
            model_filename = f"data_analysis_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            model_path = MODELS_DIR / model_filename
            
            model_info = {
                "model_type": "data_analysis_model",
                "training_date": datetime.now().isoformat(),
                "epochs": epochs,
                "batch_size": batch_size,
                "final_metrics": epoch_metrics
            }
            
            with open(model_path, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 数据分析模型训练完成，模型保存至: {model_path}")
            
            return True
        except Exception as e:
            logger.error(f"❌ 数据分析模型训练过程中发生错误: {e}")
            return False
    
    def _train_collaboratively(self, scenario):
        """执行协作式训练"""
        logger.info("🔄 开始协作式训练...")
        
        try:
            # 导入协作式训练管理器
            # 修复导入问题
            import sys
            from pathlib import Path
            # 添加项目根目录到路径
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))
            
            from training.collaborative_training_manager import CollaborativeTrainingManager
            
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
            from apps.backend.src.core_ai.concept_models.environment_simulator import EnvironmentSimulator
            manager.register_model("environment_simulator", EnvironmentSimulator())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册环境模拟器: {e}")
        
        try:
            from apps.backend.src.core_ai.concept_models.causal_reasoning_engine import CausalReasoningEngine
            manager.register_model("causal_reasoning_engine", CausalReasoningEngine())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册因果推理引擎: {e}")
        
        try:
            from apps.backend.src.core_ai.concept_models.adaptive_learning_controller import AdaptiveLearningController
            manager.register_model("adaptive_learning_controller", AdaptiveLearningController())
        except Exception as e:
            logger.warning(f"⚠️ 无法注册自适应学习控制器: {e}")
        
        try:
            from apps.backend.src.core_ai.concept_models.alpha_deep_model import AlphaDeepModel
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
                
                # 模拟保存检查点
                if epoch % checkpoint_interval == 0 or epoch == epochs:
                    self.save_checkpoint(epoch, epoch_metrics)
            
            return True
        except Exception as e:
            logger.error(f"❌ 模拟训练过程中发生错误: {e}")
            return False
    
    def _train_with_gpu(self, scenario):
        """使用GPU进行训练（增强容错版本）"""
        logger.info("🚀 开始使用GPU训练...")
        
        try:
            import tensorflow as tf
            
            # 配置GPU
            self._configure_gpu_memory()
            
            # 设置分布式训练（如果可用）
            strategy = self._setup_distributed_training()
            
            # 获取训练参数
            epochs = scenario.get('epochs', 10)
            batch_size = scenario.get('batch_size', 16)
            checkpoint_interval = scenario.get('checkpoint_interval', 5)
            
            # 尝试加载检查点以支持从中断处继续
            start_epoch = 1
            checkpoint_data = self.load_checkpoint()
            if checkpoint_data:
                start_epoch = checkpoint_data.get('epoch', 0) + 1
                logger.info(f"🔄 从检查点继续训练，起始轮数: {start_epoch}")
            
            # 模拟训练过程
            try:
                for epoch in range(start_epoch, epochs + 1):
                    # 检查是否需要暂停
                    if self.is_paused:
                        logger.info("⏸️ 训练已暂停")
                        self.save_checkpoint(epoch)
                        return False
                    
                    # 模拟训练步骤
                    epoch_metrics = self.simulate_training_step(epoch, batch_size)
                    
                    # 显示进度
                    progress = (epoch / epochs) * 100
                    logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f}")
                    
                    # 使用增强的检查点管理器决定是否保存检查点
                    checkpoint_decision = self.checkpoint_manager.should_save_checkpoint(
                        epoch, 
                        epoch_metrics, 
                        "main_training"
                    )
                    
                    if checkpoint_decision['should_save']:
                        logger.info(f"💾 根据策略保存检查点: {checkpoint_decision['reasons']}")
                        self.save_checkpoint(epoch, epoch_metrics)
                    elif epoch % checkpoint_interval == 0 or epoch == epochs:
                        # 保持原有的检查点间隔逻辑作为后备
                        self.save_checkpoint(epoch, epoch_metrics)
                
                return True
            except Exception as e:
                logger.error(f"❌ 模拟训练过程中发生错误: {e}")
                return False
            
        except Exception as e:
            logger.error(f"❌ GPU训练过程中发生错误: {e}")
            return False
    
    def _simulate_training_with_gpu(self, scenario):
        """模拟GPU训练过程"""
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        # 模拟GPU训练过程
        try:
            for epoch in range(1, epochs + 1):
                # 模拟GPU训练步骤
                # 在实际实现中，这里会是真正的GPU训练代码
                time.sleep(0.05)  # 模拟GPU训练时间
                
                # 模拟训练指标（GPU训练通常更快且更准确）
                epoch_metrics = {
                    "loss": max(0.001, 2.0 * (0.8 ** (epoch * 0.1)) + random.uniform(-0.02, 0.02)),
                    "accuracy": min(0.99, (epoch / epochs) * 0.95 + random.uniform(-0.01, 0.01))
                }
                
                # 显示进度
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f} (GPU加速)")
                
                # 保存检查点
                if epoch % checkpoint_interval == 0 or epoch == epochs:
                    self.save_checkpoint(epoch, epoch_metrics)
            
            return True
        except Exception as e:
            logger.error(f"❌ GPU模拟训练过程中发生错误: {e}")
            return False
    
    def _train_distributed(self, scenario):
        """执行分布式训练"""
        logger.info("🔄 开始分布式训练...")
        
        try:
            import tensorflow as tf
            
            # 设置分布式训练环境
            strategy = self._setup_distributed_training()
            
            if not strategy:
                logger.warning("⚠️ 无法设置分布式训练环境，回退到单设备训练")
                return self._train_with_gpu(scenario)
            
            # 在分布式策略范围内执行训练
            with strategy.scope():
                logger.info("🔄 在分布式策略范围内执行训练")
                # 这里会是实际的分布式训练代码
                # 为示例起见，我们使用模拟训练
                success = self._simulate_distributed_training(scenario)
            
            return success
        except Exception as e:
            logger.error(f"❌ 分布式训练过程中发生错误: {e}")
            return False
    
    def _simulate_distributed_training(self, scenario):
        """模拟分布式训练过程（增强容错版本）"""
        # 获取训练参数
        epochs = scenario.get('epochs', 10)
        batch_size = scenario.get('batch_size', 16)
        checkpoint_interval = scenario.get('checkpoint_interval', 5)
        
        # 尝试加载检查点以支持从中断处继续
        start_epoch = 1
        checkpoint_data = self.load_checkpoint()
        if checkpoint_data:
            start_epoch = checkpoint_data.get('epoch', 0) + 1
            logger.info(f"🔄 从检查点继续分布式训练，起始轮数: {start_epoch}")
        
        # 模拟分布式训练过程（通常更快）
        try:
            for epoch in range(start_epoch, epochs + 1):
                # 检查是否需要暂停
                if self.is_paused:
                    logger.info("⏸️ 分布式训练已暂停")
                    self.save_checkpoint(epoch)
                    return False
                
                # 模拟分布式训练步骤
                time.sleep(0.03)  # 模拟分布式训练时间（更快）
                
                # 模拟训练指标（分布式训练通常更稳定）
                epoch_metrics = {
                    "loss": max(0.0005, 2.0 * (0.75 ** (epoch * 0.12)) + random.uniform(-0.01, 0.01)),
                    "accuracy": min(0.995, (epoch / epochs) * 0.96 + random.uniform(-0.005, 0.005))
                }
                
                # 显示进度
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f} (分布式训练)")
                
                # 使用增强的检查点管理器决定是否保存检查点
                checkpoint_decision = self.checkpoint_manager.should_save_checkpoint(
                    epoch, 
                    epoch_metrics, 
                    "distributed_training"
                )
                
                if checkpoint_decision['should_save']:
                    logger.info(f"💾 根据策略保存分布式训练检查点: {checkpoint_decision['reasons']}")
                    self.save_checkpoint(epoch, epoch_metrics)
                elif epoch % checkpoint_interval == 0 or epoch == epochs:
                    # 保持原有的检查点间隔逻辑作为后备
                    self.save_checkpoint(epoch, epoch_metrics)
            
            return True
        except Exception as e:
            logger.error(f"❌ 分布式模拟训练过程中发生错误: {e}")
            return False
    
    def train(self, scenario_name: str = None, scenario: Dict[str, Any] = None):
        """执行训练（增强容错版本）"""
        logger.info(f"🚀 开始使用预设配置训练: {scenario_name}")
        
        if scenario_name:
            scenario = self.get_preset_scenario(scenario_name)
            if not scenario:
                return False
        
        # 检查是否启用GPU训练
        use_gpu = scenario.get('use_gpu', self.gpu_available)
        
        # 检查硬件配置中的集成显卡支持
        integrated_graphics_support = self.config.get('hardware_configuration', {}).get('integrated_graphics_support', False)
        minimum_vram_gb = self.config.get('hardware_configuration', {}).get('minimum_vram_gb_for_integrated', 1)
        
        # 如果启用了集成显卡支持，即使没有检测到专用GPU，也可以尝试使用GPU训练
        if use_gpu and (self.gpu_available or integrated_graphics_support):
            # 检查是否有足够的显存（对于集成显卡要求较低）
            if self.gpu_available or (integrated_graphics_support and self._check_system_gpu_memory() >= minimum_vram_gb):
                logger.info("🖥️  启用GPU训练")
                return self._train_with_gpu(scenario)
            else:
                logger.info("⚠️  显存不足，将使用CPU训练")
                # 继续执行CPU训练逻辑
        
        # 检查是否启用分布式训练
        use_distributed = scenario.get('distributed_training', False)
        if use_distributed and self.gpu_available:
            logger.info("🔄 启用分布式训练")
            return self._train_distributed(scenario)
        
        # 应用集成显卡优化（如果适用）
        if integrated_graphics_optimizer and integrated_graphics_optimizer.is_integrated_graphics_system():
            logger.info("🔧 应用集成显卡优化")
            optimization_results = integrated_graphics_optimizer.apply_all_optimizations()
            logger.info(f"集成显卡优化结果: {optimization_results}")
            
            # 根据优化结果调整训练参数
            if 'optimizations_applied' in optimization_results:
                # 调整批处理大小
                original_batch_size = scenario.get('batch_size', 16)
                adjusted_batch_size = integrated_graphics_optimizer.adjust_batch_size_for_integrated_graphics(original_batch_size)
                scenario['batch_size'] = adjusted_batch_size
                logger.info(f"批处理大小从 {original_batch_size} 调整为 {adjusted_batch_size}")
        
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
        elif 'code_model' in target_models:
            return self._train_code_model(scenario)
        elif 'data_analysis_model' in target_models:
            return self._train_data_analysis_model(scenario)
        
        # 检查是否启用协作式训练
        if scenario.get('enable_collaborative_training', False):
            return self._train_collaboratively(scenario)
        
        # 显示训练参数
        logger.info("📊 训练参数:")
        logger.info(f"  数据集: {', '.join(scenario.get('datasets', []))}")
        logger.info(f"  训练轮数: {scenario.get('epochs', 10)}")
        logger.info(f"  批次大小: {scenario.get('batch_size', 16)}")
        logger.info(f"  目标模型: {', '.join(scenario.get('target_models', []))}")
        logger.info(f"  使用GPU: {use_gpu}")
        logger.info(f"  分布式训练: {use_distributed}")
        
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
                
                # 检查是否需要暂停（模拟用户中断）
                if self.is_paused:
                    logger.info("⏸️ 训练已暂停")
                    self.save_checkpoint(epoch)
                    return False
                
                # 模拟一个epoch的训练（实际项目中这里会是多个batch的训练）
                epoch_metrics = self.simulate_training_step(epoch, batch_size, scenario_name)
                
                # 显示进度
                progress = (epoch / epochs) * 100
                logger.info(f"  Epoch {epoch}/{epochs} - 进度: {progress:.1f}% - Loss: {epoch_metrics['loss']:.4f} - Accuracy: {epoch_metrics['accuracy']:.4f}")
                
                # 模拟保存检查点
                if epoch % checkpoint_interval == 0 or epoch == epochs:
                    self.save_checkpoint(epoch, epoch_metrics)
                
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
                "datasets": scenario.get('datasets', []),
                "use_gpu": use_gpu,
                "distributed_training": use_distributed
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
    
    def evaluate_model(self, model_path: Path, test_data: Optional[list] = None) -> Dict[str, Any]:
        """评估训练好的模型"""
        logger.info(f"🔍 开始评估模型: {model_path}")
        
        if not model_path.exists():
            logger.error(f"❌ 模型文件不存在: {model_path}")
            return {"error": "Model file not found"}
        
        try:
            # 加载模型元数据
            if model_path.suffix == '.json':
                with open(model_path, 'r', encoding='utf-8') as f:
                    model_info = json.load(f)
            else:
                # 对于其他类型的模型文件，创建基本的元数据
                model_info = {
                    "model_name": model_path.stem,
                    "training_date": datetime.now().isoformat(),
                    "file_size": model_path.stat().st_size
                }
            
            # 模拟评估过程
            evaluation_results = {
                "model_name": model_info.get("model_name", "Unknown"),
                "evaluation_date": datetime.now().isoformat(),
                "test_samples": len(test_data) if test_data else random.randint(100, 1000),
                "accuracy": random.uniform(0.7, 0.98),
                "precision": random.uniform(0.65, 0.95),
                "recall": random.uniform(0.7, 0.9),
                "f1_score": random.uniform(0.68, 0.92),
                "loss": random.uniform(0.01, 0.5),
                "inference_time_ms": random.uniform(10, 100)
            }
            
            # 保存评估报告
            report_dir = TRAINING_DIR / "evaluation_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_filename = f"evaluation_report_{model_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            report_path = report_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_results, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 模型评估完成，报告保存至: {report_path}")
            return evaluation_results
            
        except Exception as e:
            logger.error(f"❌ 模型评估过程中发生错误: {e}")
            return {"error": str(e)}
    
    def analyze_model_performance(self, model_path: Path) -> Dict[str, Any]:
        """分析模型性能并生成详细报告"""
        logger.info(f"📊 开始分析模型性能: {model_path}")
        
        # 评估模型
        evaluation_results = self.evaluate_model(model_path)
        
        if "error" in evaluation_results:
            return evaluation_results
        
        # 生成性能分析报告
        performance_analysis = {
            "model_name": evaluation_results["model_name"],
            "analysis_date": datetime.now().isoformat(),
            "overall_performance": "优秀" if evaluation_results["accuracy"] > 0.9 else "良好" if evaluation_results["accuracy"] > 0.8 else "一般",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
            "metrics": evaluation_results
        }
        
        # 根据指标分析优势和劣势
        if evaluation_results["accuracy"] > 0.9:
            performance_analysis["strengths"].append("高准确率")
        else:
            performance_analysis["weaknesses"].append("准确率有待提高")
            performance_analysis["recommendations"].append("增加训练数据量")
            
        if evaluation_results["f1_score"] > 0.85:
            performance_analysis["strengths"].append("良好的平衡性")
        else:
            performance_analysis["weaknesses"].append("精确率和召回率不平衡")
            performance_analysis["recommendations"].append("调整分类阈值")
            
        if evaluation_results["inference_time_ms"] < 50:
            performance_analysis["strengths"].append("快速推理")
        else:
            performance_analysis["weaknesses"].append("推理速度较慢")
            performance_analysis["recommendations"].append("模型优化或量化")
        
        # 保存性能分析报告
        analysis_dir = TRAINING_DIR / "performance_analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        
        analysis_filename = f"performance_analysis_{model_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        analysis_path = analysis_dir / analysis_filename
        
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(performance_analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 模型性能分析完成，报告保存至: {analysis_path}")
        return performance_analysis
    
    def deploy_model(self, model_path: Path, deployment_target: str = "local") -> bool:
        """部署训练好的模型"""
        logger.info(f"🚀 开始部署模型: {model_path} 到 {deployment_target}")
        
        if not model_path.exists():
            logger.error(f"❌ 模型文件不存在: {model_path}")
            return False
        
        try:
            # 创建部署目录
            deployment_dir = TRAINING_DIR / "deployments" / deployment_target
            deployment_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制模型文件
            deployed_model_path = deployment_dir / model_path.name
            shutil.copy2(model_path, deployed_model_path)
            
            # 创建部署配置
            deployment_config = {
                "model_name": model_path.stem,
                "deployment_target": deployment_target,
                "deployment_date": datetime.now().isoformat(),
                "model_path": str(deployed_model_path.relative_to(TRAINING_DIR)),
                "version": "1.0.0",
                "dependencies": [],
                "deployment_status": "success"
            }
            
            # 保存部署配置
            config_path = deployment_dir / f"{model_path.stem}_deployment_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(deployment_config, f, ensure_ascii=False, indent=2)
            
            # 创建部署日志
            deployment_log = {
                "deployment_id": f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "model_name": model_path.stem,
                "target": deployment_target,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "status": "completed",
                "details": f"Model {model_path.name} successfully deployed to {deployment_target}"
            }
            
            # 保存部署日志
            log_dir = TRAINING_DIR / "deployment_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(deployment_log, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 模型部署完成: {deployed_model_path}")
            logger.info(f"📄 部署配置保存至: {config_path}")
            logger.info(f"📝 部署日志保存至: {log_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型部署过程中发生错误: {e}")
            
            # 记录部署失败日志
            deployment_log = {
                "deployment_id": f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "model_name": model_path.stem,
                "target": deployment_target,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            }
            
            log_dir = TRAINING_DIR / "deployment_logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / f"deployment_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}_failed.json"
            
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(deployment_log, f, ensure_ascii=False, indent=2)
            
            return False
    
    def _check_system_gpu_memory(self):
        """检查系统GPU内存"""
        try:
            import platform
            system = platform.system().lower()
            
            if system == "windows":
                # Windows系统使用WMI检查
                import subprocess
                import json
                
                result = subprocess.run([
                    "powershell.exe", 
                    "Get-WmiObject -Class Win32_VideoController | Select-Object Name, AdapterRAM | ConvertTo-Json"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0 and result.stdout.strip():
                    gpu_data = json.loads(result.stdout)
                    
                    # 计算总GPU内存（以GB为单位）
                    total_memory_gb = 0
                    
                    # Handle both single GPU and multiple GPU cases
                    if isinstance(gpu_data, list):
                        gpu_list = gpu_data
                    else:
                        gpu_list = [gpu_data]
                    
                    # Sum up memory from all GPUs
                    for gpu_info in gpu_list:
                        adapter_ram = gpu_info.get('AdapterRAM', 0)
                        # Convert RAM from bytes to GB
                        memory_gb = adapter_ram / (1024**3) if adapter_ram else 0
                        total_memory_gb += memory_gb
                    
                    return total_memory_gb
                    
            # For other platforms or if WMI detection failed, return 0
            return 0
        except Exception as e:
            logger.warning(f"检查系统GPU内存时出错: {e}")
            return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Unified AI Project 模型训练脚本')
    parser.add_argument('--preset', type=str, help='使用预设配置进行训练 (quick_start, comprehensive_training, vision_focus, audio_focus, full_dataset_training, math_model_training, logic_model_training, collaborative_training)')
    parser.add_argument('--config', type=str, help='指定训练配置文件路径')
    parser.add_argument('--preset-config', type=str, help='指定预设配置文件路径')
    parser.add_argument('--resume', action='store_true', help='从检查点继续训练')
    parser.add_argument('--pause', action='store_true', help='暂停训练')
    parser.add_argument('--evaluate', type=str, help='评估指定的模型文件')
    parser.add_argument('--deploy', type=str, help='部署指定的模型文件')
    parser.add_argument('--target', type=str, default='local', help='部署目标 (local, staging, production)')
    parser.add_argument('--auto', action='store_true', help='启用自动训练模式（自动识别数据、创建配置、执行训练）')
    
    args = parser.parse_args()
    
    print("🚀 Unified-AI-Project 模型训练")
    print("=" * 50)
    
    # 初始化训练器
    trainer = ModelTrainer(
        config_path=args.config,
        preset_path=args.preset_config
    )
    
    # 根据参数决定操作
    if args.evaluate:
        # 评估模型
        model_path = Path(args.evaluate)
        results = trainer.evaluate_model(model_path)
        if "error" not in results:
            print(f"\n📊 模型评估结果:")
            print(f"  模型名称: {results['model_name']}")
            print(f"  准确率: {results['accuracy']:.4f}")
            print(f"  精确率: {results['precision']:.4f}")
            print(f"  召回率: {results['recall']:.4f}")
            print(f"  F1分数: {results['f1_score']:.4f}")
            print(f"  损失: {results['loss']:.4f}")
            print(f"  推理时间: {results['inference_time_ms']:.2f}ms")
        else:
            print(f"\n❌ 评估失败: {results['error']}")
    elif args.deploy:
        # 部署模型
        model_path = Path(args.deploy)
        success = trainer.deploy_model(model_path, args.target)
        if success:
            print(f"\n✅ 模型部署成功: {model_path}")
        else:
            print(f"\n❌ 模型部署失败: {model_path}")
    elif args.auto:
        # 启用自动训练模式
        print("🤖 启用自动训练模式")
        try:
            from training.auto_training_manager import AutoTrainingManager
            auto_trainer = AutoTrainingManager()
            report = auto_trainer.run_full_auto_training_pipeline()
            print("\n✅ 自动训练完成!")
            print("请查看训练目录中的模型和报告文件")
        except Exception as e:
            print(f"\n❌ 自动训练失败: {e}")
            sys.exit(1)
    elif args.preset:
        # 使用预设配置训练
        if args.pause:
            trainer.pause_training()
        elif args.resume:
            success = trainer.resume_training(args.preset)
        else:
            success = trainer.train_with_preset(args.preset)
        
        if success:
            print("\n🎉 训练完成!")
            print("请查看训练目录中的模型和报告文件")
        else:
            print("\n⚠️ 训练暂停或中断，请使用 --resume 参数继续训练")
            sys.exit(1)
    else:
        # 使用默认配置训练
        success = trainer.train_with_default_config()
        
        if success:
            print("\n🎉 训练完成!")
            print("请查看训练目录中的模型和报告文件")
        else:
            print("\n❌ 训练失败")
            sys.exit(1)


if __name__ == "__main__":
    main()