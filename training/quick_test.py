#!/usr/bin/env python3
"""
快速测试增强后的自动训练系统功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

def test_imports() -> None:
    """测试导入功能"""
    try:
        from training.auto_training_manager import AutoTrainingManager
        from training.data_manager import DataManager
        _ = print("✅ 导入测试通过")
        return True
    except Exception as e:
        _ = print(f"❌ 导入测试失败: {e}")
        return False

def test_data_manager_enhancements() -> None:
    """测试数据管理器增强功能"""
    try:
        from training.data_manager import DataManager
        dm = DataManager()
        
        # 测试新添加的数据类型
        supported_formats = dm.supported_formats
        expected_types = ['model', 'archive', 'binary']
        for data_type in expected_types:
            if data_type in supported_formats:
                _ = print(f"✅ 新数据类型 '{data_type}' 已添加")
            else:
                _ = print(f"❌ 新数据类型 '{data_type}' 未找到")
                return False
        
        _ = print("✅ 数据管理器增强功能测试通过")
        return True
    except Exception as e:
        _ = print(f"❌ 数据管理器增强功能测试失败: {e}")
        return False

def test_auto_training_enhancements() -> None:
    """测试自动训练增强功能"""
    try:
        from training.auto_training_manager import AutoTrainingManager
        atm = AutoTrainingManager()
        
        # 测试训练监控器是否有新功能
        monitor = atm.training_monitor
        if hasattr(monitor, 'log_event') and hasattr(monitor, 'get_logs'):
            _ = print("✅ 训练监控器增强功能已添加")
        else:
            _ = print("❌ 训练监控器增强功能缺失")
            return False
        
        _ = print("✅ 自动训练增强功能测试通过")
        return True
    except Exception as e:
        _ = print(f"❌ 自动训练增强功能测试失败: {e}")
        return False

def main() -> None:
    """主函数"""
    _ = print("🚀 快速测试增强后的自动训练系统")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_data_manager_enhancements,
        test_auto_training_enhancements
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        _ = print()
    
    print("=" * 40)
    _ = print(f"测试结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        _ = print("🎉 所有测试通过! 增强功能已正确实现。")
        return 0
    else:
        _ = print("💥 部分测试失败! 请检查实现。")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())