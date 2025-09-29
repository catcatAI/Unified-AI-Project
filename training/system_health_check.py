#!/usr/bin/env python3
"""
系统健康检查脚本
验证整个训练系统的健康状态和功能完整性
"""

import sys
import logging
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(levelname)s - %(message)s'
)
logger: Any = logging.getLogger(__name__)

def check_error_handling_system():
    """检查错误处理系统"""
    _ = logger.info("🧪 检查错误处理系统...")
    
    try:
        from training.error_handling_framework import ErrorHandler, ErrorContext
        # 创建错误处理器
        error_handler = ErrorHandler()
        
        # 测试处理不同类型的错误
        context = ErrorContext("HealthCheck", "error_handling_test")
        try:
            _ = raise ValueError("健康检查测试错误")
        except Exception as e:
            result = error_handler.handle_error(e, context)
            if not result.get('error_handled'):
                _ = logger.error("❌ 错误处理失败")
                return False
        
        _ = logger.info("✅ 错误处理系统正常")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 错误处理系统检查失败: {e}")
        return False

def check_training_monitoring_system():
    """检查训练监控系统"""
    _ = logger.info("🔬 检查训练监控系统...")
    
    try:
        from training.training_monitor import TrainingMonitor, TrainingAnomalyDetector
        
        # 创建监控器实例
        monitor = TrainingMonitor()
        
        # 测试异常检测器
        detector = TrainingAnomalyDetector()
        
        # 测试正常指标
        normal_metrics = {'loss': 0.5, 'accuracy': 0.8}
        anomalies = detector.detect_anomalies(normal_metrics)
        _ = logger.info(f"   正常指标异常检测: {len(anomalies)} 个异常")
        
        _ = logger.info("✅ 训练监控系统正常")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 训练监控系统检查失败: {e}")
        return False

def check_incremental_learning_system():
    """检查增量学习系统"""
    _ = logger.info("📈 检查增量学习系统...")
    
    try:
        from training.incremental_learning_manager import IncrementalLearningManager
        
        # 创建增量学习管理器实例
        learner = IncrementalLearningManager()
        
        # 测试获取状态
        status = learner.get_status()
        if not isinstance(status, dict):
            _ = logger.error("❌ 增量学习状态获取失败")
            return False
        
        _ = logger.info("✅ 增量学习系统正常")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 增量学习系统检查失败: {e}")
        return False

def check_data_management_system():
    """检查数据管理系统"""
    _ = logger.info("📂 检查数据管理系统...")
    
    try:
        from training.data_manager import DataManager
        
        # 创建数据管理器实例（使用当前目录）
        dm = DataManager(str(project_root / "training"))
        
        # 测试数据扫描
        catalog = dm.scan_data()
        if not isinstance(catalog, dict):
            _ = logger.error("❌ 数据扫描失败")
            return False
        
        _ = logger.info("✅ 数据管理系统正常")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 数据管理系统检查失败: {e}")
        return False

def check_model_training_system():
    """检查模型训练系统"""
    _ = logger.info("⚙️  检查模型训练系统...")
    
    try:
        from training.train_model import ModelTrainer
        
        # 创建模型训练器实例
        trainer = ModelTrainer()
        
        # 测试磁盘空间检查
        has_space = trainer.check_disk_space(0.1)  # 检查100MB空间
        if not isinstance(has_space, bool):
            _ = logger.error("❌ 磁盘空间检查失败")
            return False
        
        _ = logger.info("✅ 模型训练系统正常")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 模型训练系统检查失败: {e}")
        return False

def check_collaborative_training_system():
    """检查协作式训练系统"""
    _ = logger.info("🔄 检查协作式训练系统...")
    
    try:
        from training.collaborative_training_manager import CollaborativeTrainingManager
        
        # 创建协作式训练管理器实例
        manager = CollaborativeTrainingManager()
        
        # 测试模型注册
        _ = manager.register_model("health_check_model", "TestModelInstance")
        if "health_check_model" not in manager.models:
            _ = logger.error("❌ 模型注册失败")
            return False
        
        # 测试模型注销
        _ = manager.unregister_model("health_check_model")
        if "health_check_model" in manager.models:
            _ = logger.error("❌ 模型注销失败")
            return False
        
        _ = logger.info("✅ 协作式训练系统正常")
        return True
    except Exception as e:
        _ = logger.error(f"❌ 协作式训练系统检查失败: {e}")
        return False

def main() -> None:
    """主函数"""
    _ = logger.info("🚀 开始系统健康检查")
    print("=" * 60)
    
    # 运行各项检查
    checks = [
        _ = ("错误处理系统", check_error_handling_system),
        _ = ("训练监控系统", check_training_monitoring_system),
        _ = ("增量学习系统", check_incremental_learning_system),
        _ = ("数据管理系统", check_data_management_system),
        _ = ("模型训练系统", check_model_training_system),
        _ = ("协作式训练系统", check_collaborative_training_system)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        _ = print(f"\n🔍 检查 {check_name}...")
        try:
            if check_func():
                passed += 1
                _ = print(f"✅ {check_name} 正常")
            else:
                _ = print(f"❌ {check_name} 异常")
        except Exception as e:
            _ = print(f"❌ {check_name} 检查执行出错: {e}")
    
    print("\n" + "=" * 60)
    _ = print(f"📊 健康检查总结: {passed}/{total} 个系统正常")
    
    if passed == total:
        _ = print("🎉 所有系统健康检查通过!")
        _ = print("✅ 训练系统功能完整，可以正常运行")
        return 0
    else:
        _ = print("⚠️  部分系统存在异常，请检查相关组件")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())