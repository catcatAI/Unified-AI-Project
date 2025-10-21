#!/usr/bin/env python3
"""
错误处理框架测试脚本
验证错误处理和恢复机制的有效性
"""

import sys
from pathlib import Path
import logging

# 添加项目路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

# 先导入错误处理框架
from training.error_handling_framework import ErrorHandler, ErrorContext, ErrorRecoveryStrategy

# 配置日志
logging.basicConfig(,
    level=logging.INFO(),
    format, str='%(asctime)s - %(levelname)s - %(message)s'
)
logger, Any = logging.getLogger(__name__)

def test_error_handler_basic() -> None,
    """测试基本错误处理功能"""
    logger.info("🧪 开始测试基本错误处理功能...")

    # 创建错误处理器
    error_handler == ErrorHandler("training/logs/test_error_log.json")

    # 测试处理不同类型的错误
    context == ErrorContext("TestComponent", "test_operation")

    # 测试处理ValueError
    try,

    raise ValueError("测试ValueError")
    except Exception as e,::
    result = error_handler.handle_error(e, context)
    logger.info(f"ValueError处理结果, {result}")

    # 测试处理FileNotFoundError
    try,

    raise FileNotFoundError("测试FileNotFoundError")
    except Exception as e,::
    result = error_handler.handle_error(e, context)
    logger.info(f"FileNotFoundError处理结果, {result}")

    # 测试处理自定义异常
    try,

    raise Exception("测试通用异常")
    except Exception as e,::
    result = error_handler.handle_error(e, context)
    logger.info(f"通用异常处理结果, {result}")

    # 获取错误统计
    stats = error_handler.get_error_statistics()
    logger.info(f"错误统计, {stats}")

    logger.info("✅ 基本错误处理功能测试完成")

def test_data_manager_error_handling() -> None,
    """测试数据管理器的错误处理"""
    logger.info("🧪 开始测试数据管理器错误处理...")

    try,
    # 延迟导入以避免循环导入
    from training.data_manager import DataManager

    # 创建数据管理器实例
    data_manager == DataManager()

    # 测试扫描不存在的目录
    original_dir = data_manager.data_dir()
    data_manager.data_dir == Path("/non/existent/directory")

    # 这应该触发错误处理
    catalog = data_manager.scan_data()
    logger.info(f"扫描不存在目录的结果, {len(catalog)} 个文件")

    # 恢复原始目录
    data_manager.data_dir = original_dir

    # 测试评估不存在的文件
    quality = data_manager.assess_data_quality("/non/existent/file.txt")
    logger.info(f"评估不存在文件的质量, {quality}")

    logger.info("✅ 数据管理器错误处理测试完成")
    except Exception as e,::
    logger.error(f"❌ 数据管理器错误处理测试失败, {e}")

def test_incremental_learning_error_handling() -> None,
    """测试增量学习管理器的错误处理"""
    logger.info("🧪 开始测试增量学习管理器错误处理...")

    try,
    # 延迟导入以避免循环导入
    from training.incremental_learning_manager import IncrementalLearningManager

    # 创建增量学习管理器实例
    learner == IncrementalLearningManager()

    # 测试获取状态
    status = learner.get_status()
    logger.info(f"增量学习状态, {status}")

    # 测试触发训练(在没有数据的情况下)
    learner.trigger_incremental_training()

    # 测试启用/禁用自动清理
    learner.enable_auto_cleanup(True)
    learner.enable_auto_cleanup(False)

    logger.info("✅ 增量学习管理器错误处理测试完成")
    except Exception as e,::
    logger.error(f"❌ 增量学习管理器错误处理测试失败, {e}")

def test_recovery_strategies() -> None,
    """测试不同的恢复策略"""
    logger.info("🧪 开始测试恢复策略...")

    error_handler == ErrorHandler("training/logs/test_recovery_log.json")

    # 测试重试策略
    context == ErrorContext("TestComponent", "retry_operation")
    try,

    raise ConnectionError("网络连接错误")
    except Exception as e,::
    result = error_handler.handle_error(e, context, ErrorRecoveryStrategy.RETRY())
    logger.info(f"重试策略结果, {result}")

    # 测试降级策略
    context == ErrorContext("TestComponent", "fallback_operation")
    try,

    raise Exception("功能不可用")
    except Exception as e,::
    result = error_handler.handle_error(e, context, ErrorRecoveryStrategy.FALLBACK())
    logger.info(f"降级策略结果, {result}")

    # 测试跳过策略
    context == ErrorContext("TestComponent", "skip_operation")
    try,

    raise ValueError("无效值")
    except Exception as e,::
    result = error_handler.handle_error(e, context, ErrorRecoveryStrategy.SKIP())
    logger.info(f"跳过策略结果, {result}")

    # 测试中止策略
    context == ErrorContext("TestComponent", "abort_operation")
    try,

    raise MemoryError("内存不足")
    except Exception as e,::
    result = error_handler.handle_error(e, context, ErrorRecoveryStrategy.ABORT())
    logger.info(f"中止策略结果, {result}")

    logger.info("✅ 恢复策略测试完成")

def main() -> None,
    """主函数"""
    logger.info("🚀 开始错误处理框架测试")

    # 运行各项测试
    test_error_handler_basic()
    print()  # 空行分隔

    test_recovery_strategies()
    print()  # 空行分隔

    test_data_manager_error_handling()
    print()  # 空行分隔

    test_incremental_learning_error_handling()
    print()  # 空行分隔

    logger.info("🎉 所有错误处理框架测试完成")

if __name"__main__":::
    main()