#!/usr/bin/env python3
"""
测试后端导入
"""

import sys
import os
from pathlib import Path

# 添加后端路径
backend_path = Path(__file__).parent / "apps" / "backend"
sys.path.insert(0, str(backend_path))

def test_imports():
    """测试关键模块导入"""
    results = {}
    
    # 测试基础模块
    modules = [
        ("src.api.routes", "API路由"),
        ("src.core.managers.system_manager", "系统管理器"),
        ("src.core.config.system_config", "系统配置"),
        ("src.core.config.level5_config", "Level 5配置"),
    ]
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            results[module_name] = {"status": "success", "desc": description}
            print(f"✓ {description}: 导入成功")
        except ImportError as e:
            results[module_name] = {"status": "failed", "desc": description, "error": str(e)}
            print(f"✗ {description}: 导入失败 - {e}")
        except Exception as e:
            results[module_name] = {"status": "error", "desc": description, "error": str(e)}
            print(f"✗ {description}: 其他错误 - {e}")
    
    return results

def test_main_function():
    """测试主函数功能"""
    try:
        # 测试create_app函数
        from main import create_app
        app = create_app()
        print("✓ FastAPI应用创建成功")
        return True
    except Exception as e:
        print(f"✗ FastAPI应用创建失败: {e}")
        return False

def main():
    print("=" * 60)
    print("测试后端系统运行状态")
    print("=" * 60)
    
    # 测试导入
    print("\n1. 测试模块导入:")
    import_results = test_imports()
    
    # 测试主函数
    print("\n2. 测试主函数:")
    main_success = test_main_function()
    
    # 统计结果
    total = len(import_results)
    success = sum(1 for r in import_results.values() if r["status"] == "success")
    
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"模块导入: {success}/{total} 成功")
    print(f"主函数: {'成功' if main_success else '失败'}")
    
    if success == total and main_success:
        print("\n✅ 后端系统可以正常运行")
        return 0
    else:
        print("\n❌ 后端系统存在问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())