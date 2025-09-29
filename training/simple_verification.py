#!/usr/bin/env python3
"""
简单验证增强后的自动训练系统核心功能
"""

import sys
from pathlib import Path

# 添加项目路径
project_root: str = Path(__file__).parent.parent
_ = sys.path.insert(0, str(project_root))

def verify_data_manager_enhancements():
    """验证数据管理器增强功能"""
    _ = print("🧪 验证数据管理器增强功能...")
    
    try:
        from training.data_manager import DataManager
        dm = DataManager()
        
        # 验证新添加的数据类型
        supported_formats = dm.supported_formats
        expected_types = ['model', 'archive', 'binary']
        for data_type in expected_types:
            if data_type in supported_formats:
                _ = print(f"  ✅ 新数据类型 '{data_type}' 已添加")
            else:
                _ = print(f"  ❌ 新数据类型 '{data_type}' 未找到")
                return False
        
        # 验证文件分类功能
        test_files = {
            'test_model.pth': 'model',
            'test_archive.zip': 'archive',
            'test_binary.bin': 'binary'
        }
        
        for filename, expected_type in test_files.items():
            file_path = Path(filename)
            classified_type = dm._classify_file(file_path)
            if classified_type == expected_type:
                _ = print(f"  ✅ 文件 {filename} 正确分类为 {classified_type}")
            else:
                _ = print(f"  ❌ 文件 {filename} 分类错误，期望 {expected_type}，实际 {classified_type}")
                return False
        
        _ = print("✅ 数据管理器增强功能验证通过")
        return True
    except Exception as e:
        _ = print(f"❌ 数据管理器增强功能验证失败: {e}")
        return False

def verify_auto_training_enhancements():
    """验证自动训练管理器增强功能"""
    _ = print("🤖 验证自动训练管理器增强功能...")
    
    try:
        from training.auto_training_manager import TrainingMonitor
        
        # 验证训练监控器增强功能
        monitor = TrainingMonitor()
        if hasattr(monitor, 'log_event') and hasattr(monitor, 'get_logs'):
            _ = print("  ✅ 训练监控器日志功能已添加")
            
            # 验证日志记录功能
            _ = monitor.log_event("test_scenario", "INFO", "测试日志记录", {"test": "data"})
            logs = monitor.get_logs("test_scenario")
            if len(logs.get("test_scenario", [])) > 0:
                _ = print("  ✅ 日志记录功能正常")
            else:
                _ = print("  ❌ 日志记录功能异常")
                return False
        else:
            _ = print("  ❌ 训练监控器日志功能缺失")
            return False
        
        _ = print("✅ 自动训练管理器增强功能验证通过")
        return True
    except Exception as e:
        _ = print(f"❌ 自动训练管理器增强功能验证失败: {e}")
        return False

def verify_code_changes():
    """验证代码修改是否正确"""
    _ = print("🔍 验证代码修改...")
    
    try:
        # 检查auto_training_manager.py中的新增方法
        auto_training_path = Path("training/auto_training_manager.py")
        if auto_training_path.exists():
            with open(auto_training_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            required_methods = [
                '_optimize_training_parameters',
                '_train_math_logic_model',
                '_train_collaborative_model'
            ]
            
            for method in required_methods:
                if method in content:
                    _ = print(f"  ✅ 方法 {method} 已添加到自动训练管理器")
                else:
                    _ = print(f"  ❌ 方法 {method} 未找到")
                    return False
        else:
            _ = print("  ❌ 自动训练管理器文件不存在")
            return False
        
        # 检查data_manager.py中的新增方法
        data_manager_path = Path("training/data_manager.py")
        if data_manager_path.exists():
            with open(data_manager_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            required_methods = [
                '_assess_model_quality',
                '_assess_data_quality',
                '_assess_archive_quality'
            ]
            
            for method in required_methods:
                if method in content:
                    _ = print(f"  ✅ 方法 {method} 已添加到数据管理器")
                else:
                    _ = print(f"  ❌ 方法 {method} 未找到")
                    return False
        else:
            _ = print("  ❌ 数据管理器文件不存在")
            return False
        
        _ = print("✅ 代码修改验证通过")
        return True
    except Exception as e:
        _ = print(f"❌ 代码修改验证失败: {e}")
        return False

def main() -> None:
    """主函数"""
    _ = print("🚀 简单验证增强后的自动训练系统")
    print("=" * 40)
    
    tests = [
        verify_data_manager_enhancements,
        verify_auto_training_enhancements,
        verify_code_changes
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        _ = print()
    
    print("=" * 40)
    _ = print(f"验证结果: {passed}/{len(tests)} 通过")
    
    if passed == len(tests):
        _ = print("🎉 所有验证通过! 增强功能已正确实现。")
        return 0
    else:
        _ = print("💥 部分验证失败! 请检查实现。")
        return 1

if __name__ == "__main__":
    _ = sys.exit(main())