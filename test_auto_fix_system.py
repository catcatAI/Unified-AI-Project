#!/usr/bin/env python3
"""
测试自动修复系统的核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入功能"""
    print("测试导入功能...")
    
    try:
        from unified_auto_fix_system import __version__, __author__
        print(f"✓ 成功导入 unified_auto_fix_system.__version__: {__version__}")
        print(f"✓ 成功导入 unified_auto_fix_system.__author__: {__author__}")
    except Exception as e:
        print(f"✗ 导入 unified_auto_fix_system 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope
        print("✓ 成功导入 FixType, FixStatus, FixScope")
    except Exception as e:
        print(f"✗ 导入 fix_types 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext, FixReport
        print("✓ 成功导入 FixResult, FixContext, FixReport")
    except Exception as e:
        print(f"✗ 导入 fix_result 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        print("✓ 成功导入 UnifiedFixEngine")
    except Exception as e:
        print(f"✗ 导入 unified_fix_engine 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.modules.base_fixer import BaseFixer
        print("✓ 成功导入 BaseFixer")
    except Exception as e:
        print(f"✗ 导入 base_fixer 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        print("✓ 成功导入 EnhancedSyntaxFixer")
    except Exception as e:
        print(f"✗ 导入 syntax_fixer 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        print("✓ 成功导入 ImportFixer")
    except Exception as e:
        print(f"✗ 导入 import_fixer 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        print("✓ 成功导入 DependencyFixer")
    except Exception as e:
        print(f"✗ 导入 dependency_fixer 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.modules.ai_assisted_fixer import AIAssistedFixer
        print("✓ 成功导入 AIAssistedFixer")
    except Exception as e:
        print(f"✗ 导入 ai_assisted_fixer 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.interfaces.cli_interface import CLIFixInterface
        print("✓ 成功导入 CLIFixInterface")
    except Exception as e:
        print(f"✗ 导入 cli_interface 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.interfaces.api_interface import APIFixInterface
        print("✓ 成功导入 APIFixInterface")
    except Exception as e:
        print(f"✗ 导入 api_interface 失败: {e}")
        return False
    
    try:
        from unified_auto_fix_system.interfaces.ai_interface import AIFixInterface
        print("✓ 成功导入 AIFixInterface")
    except Exception as e:
        print(f"✗ 导入 ai_interface 失败: {e}")
        return False
    
    return True

def test_fix_engine_initialization():
    """测试修复引擎初始化"""
    print("\n测试修复引擎初始化...")
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_types import FixScope
        
        # 创建修复引擎实例
        engine = UnifiedFixEngine(project_root)
        print("✓ 成功创建 UnifiedFixEngine 实例")
        
        # 检查模块加载
        print(f"✓ 加载了 {len(engine.modules)} 个修复模块:")
        for fix_type, module in engine.modules.items():
            print(f"  - {fix_type.value}: {module}")
        
        # 检查配置加载
        print(f"✓ 配置加载成功: {engine.config}")
        
        return True
    except Exception as e:
        print(f"✗ 修复引擎初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_context_creation():
    """测试修复上下文创建"""
    print("\n测试修复上下文创建...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建修复上下文
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL
        )
        
        print("✓ 成功创建 FixContext 实例")
        print(f"  - 项目根目录: {context.project_root}")
        print(f"  - 修复范围: {context.scope.value}")
        print(f"  - 修复优先级: {context.priority.value}")
        
        return True
    except Exception as e:
        print(f"✗ 修复上下文创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_result_creation():
    """测试修复结果创建"""
    print("\n测试修复结果创建...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        
        # 创建修复结果
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=5,
            issues_fixed=5
        )
        
        print("✓ 成功创建 FixResult 实例")
        print(f"  - 修复类型: {result.fix_type.value}")
        print(f"  - 修复状态: {result.status.value}")
        print(f"  - 发现问题: {result.issues_found}")
        print(f"  - 修复问题: {result.issues_fixed}")
        print(f"  - 摘要: {result.summary()}")
        
        return True
    except Exception as e:
        print(f"✗ 修复结果创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试统一自动修复系统...")
    print("=" * 50)
    
    # 运行各项测试
    tests = [
        test_imports,
        test_fix_context_creation,
        test_fix_result_creation,
        test_fix_engine_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！统一自动修复系统工作正常。")
        return 0
    else:
        print("❌ 部分测试失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())