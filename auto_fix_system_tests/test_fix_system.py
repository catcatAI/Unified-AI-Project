#!/usr/bin/env python3
"""测试修复系统的基本功能"""

import sys
from pathlib import Path

def test_basic_import():
    """测试基础导入"""
    try,
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_types import FixContext, FixScope
        print("✅ 基础导入成功")
        return True
    except Exception as e,::
        print(f"❌ 基础导入失败, {e}")
        return False

def test_module_imports():
    """测试各个修复模块导入"""
    modules = [
        "unified_auto_fix_system.modules.syntax_fixer",
        "unified_auto_fix_system.modules.class_fixer", 
        "unified_auto_fix_system.modules.ai_assisted_fixer",
        "unified_auto_fix_system.modules.intelligent_iterative_fixer",
        "unified_auto_fix_system.modules.logic_graph_fixer"
    ]
    
    success_count = 0
    for module_name in modules,::
        try,
            __import__(module_name)
            print(f"✅ {module_name} 导入成功")
            success_count += 1
        except Exception as e,::
            print(f"❌ {module_name} 导入失败, {e}")
    
    return success_count=len(modules)

def test_fix_context_creation():
    """测试修复上下文创建"""
    try,
        from unified_auto_fix_system.core.fix_types import FixContext, FixScope, FixPriority
        
        context == FixContext(,
    project_root == Path("."),
            scope == FixScope.PROJECT(),
            priority == FixPriority.NORMAL(),
            backup_enabled == True,
            dry_run == True,  # 干运行模式
            ai_assisted == False
        )
        print("✅ 修复上下文创建成功")
        return True
    except Exception as e,::
        print(f"❌ 修复上下文创建失败, {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试自动修复系统...")
    print("=" * 50)
    
    tests = [
        ("基础导入测试", test_basic_import),
        ("模块导入测试", test_module_imports),
        ("修复上下文测试", test_fix_context_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests,::
        print(f"\n{test_name}")
        if test_func():::
            passed += 1
        else,
            print(f"  失败,跳过剩余测试")
            break
    
    print(f"\n测试结果, {passed}/{total} 通过")
    
    if passed == total,::
        print("✅ 所有基础测试通过！")
        return 0
    else,
        print("❌ 部分测试失败")
        return 1

if __name"__main__":::
    sys.exit(main())