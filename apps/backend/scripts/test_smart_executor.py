#!/usr/bin/env python3
"""
测试智能执行器功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_import_detection():
    """测试导入错误检测"""
    from smart_executor import detect_import_errors, detect_path_errors
    
    # 测试ModuleNotFoundError
    stderr = "ModuleNotFoundError: No module named 'core_ai'"
    errors = detect_import_errors(stderr)
    assert 'core_ai' in errors, f"Expected 'core_ai' in errors, got {errors}"
    
    # 测试ImportError
    stderr = "ImportError: cannot import name 'HSPConnector'"
    errors = detect_import_errors(stderr)
    assert 'HSPConnector' in errors, f"Expected 'HSPConnector' in errors, got {errors}"
    
    # 测试路径错误
    stderr = "No module named 'core_ai.dialogue.dialogue_manager'"
    has_path_error = detect_path_errors(stderr)
    assert has_path_error, "Expected path error detection to be True"
    
    print("✅ 所有导入错误检测测试通过")

def test_smart_test_runner():
    """测试智能测试运行器"""
    # 这里我们只测试能否导入模块
    try:
        from smart_test_runner import run_tests
        print("✅ 智能测试运行器导入成功")
    except Exception as e:
        print(f"❌ 智能测试运行器导入失败: {e}")
        return False
    return True

def test_smart_dev_runner():
    """测试智能开发服务器运行器"""
    # 这里我们只测试能否导入模块
    try:
        from smart_dev_runner import run_dev_server
        print("✅ 智能开发服务器运行器导入成功")
    except Exception as e:
        print(f"❌ 智能开发服务器运行器导入失败: {e}")
        return False
    return True

def main():
    """主函数"""
    print("🧪 开始测试智能执行器功能")
    
    # 测试导入错误检测
    test_import_detection()
    
    # 测试智能测试运行器
    if not test_smart_test_runner():
        sys.exit(1)
        
    # 测试智能开发服务器运行器
    if not test_smart_dev_runner():
        sys.exit(1)
    
    print("🎉 所有测试通过！")

if __name__ == "__main__":
    main()