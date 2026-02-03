#!/usr/bin/env python3
"""
简单测试自动修复系统的核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """测试基本导入功能"""
    print("测试基本导入功能...")
    
    try:
        # 测试核心模块导入
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        print("✓ 核心模块导入成功")
        
        # 测试修复模块导入
        from unified_auto_fix_system.modules.base_fixer import BaseFixer
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        print("✓ 修复模块导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_result():
    """测试修复结果功能"""
    print("\n测试修复结果功能...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        
        # 创建修复结果
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=3,
            issues_fixed=3
        )
        
        # 测试方法
        assert result.is_successful() == True
        assert "成功修复 3 个问题" in result.summary()
        
        print("✓ 修复结果功能正常")
        print(f"  - 摘要: {result.summary()}")
        print(f"  - 是否成功: {result.is_successful()}")
        
        return True
    except Exception as e:
        print(f"✗ 修复结果测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_context():
    """测试修复上下文功能"""
    print("\n测试修复上下文功能...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建修复上下文
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL
        )
        
        # 转换为字典
        context_dict = context.to_dict()
        assert context_dict["project_root"] == str(project_root)
        assert context_dict["scope"] == "project"
        assert context_dict["priority"] == "normal"
        
        print("✓ 修复上下文功能正常")
        print(f"  - 项目根目录: {context_dict['project_root']}")
        print(f"  - 范围: {context_dict['scope']}")
        print(f"  - 优先级: {context_dict['priority']}")
        
        return True
    except Exception as e:
        print(f"✗ 修复上下文测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始简单测试统一自动修复系统...")
    print("=" * 40)
    
    # 运行各项测试
    tests = [
        test_basic_imports,
        test_fix_result,
        test_fix_context
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"测试完成: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！统一自动修复系统核心功能正常。")
        return 0
    else:
        print("❌ 部分测试失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())