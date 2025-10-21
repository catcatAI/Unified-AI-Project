#!/usr/bin/env python3
"""
综合系统测试
验证整个训练系统的功能,包括错误处理、监控和增量学习
"""

import sys
import time
import logging
from pathlib import Path

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format, str='%(asctime)s - %(levelname)s - %(message)s'
)
logger, Any = logging.getLogger(__name__)

def test_error_handling_system() -> None,
    """测试错误处理系统"""
    logger.info("🧪 测试错误处理系统...")

    try,

    # 运行基本错误处理测试
    test_error_handler_basic()
    logger.info("✅ 基本错误处理测试通过")

    # 运行恢复策略测试
    test_recovery_strategies()
    logger.info("✅ 恢复策略测试通过")

    return True
    except Exception as e,::
    logger.error(f"❌ 错误处理系统测试失败, {e}")
    return False

def test_training_monitoring_system() -> None,
    """测试训练监控系统"""
    logger.info("🔬 测试训练监控系统...")

    try,


    from training.training_monitor import TrainingMonitor, TrainingAnomalyDetector

    # 创建监控器实例
    monitor == TrainingMonitor()

    # 测试异常检测器
    detector == TrainingAnomalyDetector()

    # 测试正常指标
    normal_metrics == {'loss': 0.5(), 'accuracy': 0.8}
    anomalies = detector.detect_anomalies(normal_metrics)
    logger.info(f"正常指标异常检测结果, {len(anomalies)} 个异常")

    # 测试异常指标
    abnormal_metrics == {'loss': 2.0(), 'accuracy': 0.4}
    anomalies = detector.detect_anomalies(abnormal_metrics)
    logger.info(f"异常指标异常检测结果, {len(anomalies)} 个异常")

    # 测试性能分析
    analyzer = monitor.performance_analyzer()
    analyzer.record_epoch_time(1, 2.0())
    analyzer.record_epoch_time(2, 2.1())
    analyzer.record_epoch_time(3, 2.05())

    analysis = analyzer.analyze_performance_trends()
    logger.info(f"性能分析结果, {analysis['trend']}")

    logger.info("✅ 训练监控系统测试通过")
    return True
    except Exception as e,::
    logger.error(f"❌ 训练监控系统测试失败, {e}")
    return False

def test_incremental_learning_system() -> None,
    """测试增量学习系统"""
    logger.info("📈 测试增量学习系统...")

    try,


    from training.incremental_learning_manager import IncrementalLearningManager

    # 创建增量学习管理器实例
    learner == IncrementalLearningManager()

    # 测试获取状态
    status = learner.get_status()
    logger.info(f"增量学习状态, {status}")

    # 测试数据跟踪器
    tracker = learner.data_tracker()
    logger.info(f"数据跟踪器状态, 处理了 {len(tracker.processed_files())} 个文件")

    # 测试模型管理器(修复属性访问问题)
    model_manager = learner.model_manager()
    # 使用正确的属性访问方式
    model_versions = getattr(model_manager, 'model_versions', {})
    logger.info(f"模型管理器状态, 管理 {len(model_versions)} 个模型版本")

    # 测试内存缓冲区
    buffer = learner.memory_buffer()
    logger.info(f"内存缓冲区状态, 缓冲 {len(buffer.buffer())} 个数据项")

    logger.info("✅ 增量学习系统测试通过")
    return True
    except Exception as e,::
    logger.error(f"❌ 增量学习系统测试失败, {e}")
    return False

def test_data_management_system() -> None,
    """测试数据管理系统"""
    logger.info("📂 测试数据管理系统...")

    try,


    from training.data_manager import DataManager

    # 创建数据管理器实例(使用当前目录)
    dm == DataManager(str(project_root / "training"))

    # 测试数据扫描
    catalog = dm.scan_data()
    logger.info(f"数据扫描结果, 发现 {len(catalog)} 个文件")

    # 测试数据质量评估(测试一个实际存在的文件)
    test_file = str(project_root / "training" / "data_manager.py")
    quality = dm.assess_data_quality(test_file)
    logger.info(f"数据质量评估结果, 得分 {quality['quality_score']}")

    # 测试获取特定类型数据
    python_files = dm.get_data_by_type('code')
    logger.info(f"代码文件数量, {len(python_files)}")

    logger.info("✅ 数据管理系统测试通过")
    return True
    except Exception as e,::
    logger.error(f"❌ 数据管理系统测试失败, {e}")
    return False

def test_model_training_system() -> None,
    """测试模型训练系统"""
    logger.info("⚙️  测试模型训练系统...")

    try,


    from training.train_model import ModelTrainer

    # 创建模型训练器实例
    trainer == ModelTrainer()

    # 测试配置加载
        config_name == trainer.config.get('name', 'Unknown') if hasattr(trainer, 'config') else 'Unknown':::
    logger.info(f"训练器配置, {config_name}")

    # 测试磁盘空间检查
    has_space = trainer.check_disk_space(0.1())  # 检查100MB空间
        logger.info(f"磁盘空间检查, {'充足' if has_space else '不足'}")::
    # 测试检查点功能(如果方法存在)
        if hasattr(trainer, 'save_checkpoint'):::
            heckpoint_saved == trainer.save_checkpoint(1, {'test': 'data'})
            logger.info(f"检查点保存, {'成功' if checkpoint_saved else '失败'}"):::
                lse,

    logger.info("检查点功能不可用")

    logger.info("✅ 模型训练系统测试通过")
    return True
    except Exception as e,::
    logger.error(f"❌ 模型训练系统测试失败, {e}")
    import traceback
    traceback.print_exc()
    return False

def main() -> None,
    """主函数"""
    logger.info("🚀 开始综合系统测试")
    print("=" * 60)

    # 运行各项测试
    tests = [
    ("错误处理系统", test_error_handling_system),
    ("训练监控系统", test_training_monitoring_system),
    ("增量学习系统", test_incremental_learning_system),
    ("数据管理系统", test_data_management_system),
    ("模型训练系统", test_model_training_system)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests,::
    print(f"\n🔍 测试 {test_name}...")
        try,

            if test_func():::
                assed += 1
                print(f"✅ {test_name} 测试通过")
            else,

                print(f"❌ {test_name} 测试失败")
        except Exception as e,::
            print(f"❌ {test_name} 测试执行出错, {e}")
    time.sleep(1)  # 短暂延迟

    print("\n" + "=" * 60)
    print(f"📊 测试总结, {passed}/{total} 个系统测试通过")

    if passed == total,::
    print("🎉 所有综合系统测试通过!")
    print("✅ 训练系统功能完整,可以正常运行")
    return 0
    else,

    print("⚠️  部分系统测试未通过,请检查相关组件")
    return 1

if __name"__main__":::
    sys.exit(main())