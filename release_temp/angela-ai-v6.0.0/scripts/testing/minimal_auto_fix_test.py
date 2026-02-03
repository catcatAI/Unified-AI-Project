#!/usr/bin/env python3
"""
最小化测试自动修复系统的核心功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports_only():
    """仅测试导入功能，不初始化完整系统"""
    print("测试导入功能...")
    
    # 测试核心类型导入
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        print("✓ FixType, FixStatus, FixScope, FixPriority 导入成功")
        
        # 测试一些枚举值
        assert FixType.SYNTAX_FIX.value == "syntax_fix"
        assert FixStatus.SUCCESS.value == "success"
        assert FixScope.PROJECT.value == "project"
        assert FixPriority.NORMAL.value == "normal"
        print("✓ 枚举值正确")
    except Exception as e:
        print(f"✗ 核心类型导入失败: {e}")
        return False
    
    # 测试结果类导入
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext, FixReport
        print("✓ FixResult, FixContext, FixReport 导入成功")
    except Exception as e:
        print(f"✗ 结果类导入失败: {e}")
        return False
    
    # 测试基础修复器导入
    try:
        from unified_auto_fix_system.modules.base_fixer import BaseFixer
        print("✓ BaseFixer 导入成功")
    except Exception as e:
        print(f"✗ BaseFixer 导入失败: {e}")
        return False
    
    # 测试具体修复器导入（不初始化）
    try:
        from unified_auto_fix_system.modules import syntax_fixer, import_fixer, dependency_fixer
        print("✓ 修复器模块导入成功（未初始化）")
    except Exception as e:
        print(f"✗ 修复器模块导入失败: {e}")
        return False
    
    # 测试接口导入
    try:
        from unified_auto_fix_system.interfaces import cli_interface, api_interface, ai_interface
        print("✓ 接口模块导入成功（未初始化）")
    except Exception as e:
        print(f"✗ 接口模块导入失败: {e}")
        return False
    
    return True

def test_data_classes():
    """测试数据类功能"""
    print("\n测试数据类功能...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        
        # 测试 FixResult
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=5,
            issues_fixed=5
        )
        
        assert result.fix_type == FixType.SYNTAX_FIX
        assert result.status == FixStatus.SUCCESS
        assert result.issues_found == 5
        assert result.issues_fixed == 5
        assert result.is_successful() == True
        assert "成功修复 5 个问题" in result.summary()
        print("✓ FixResult 功能正常")
        
        # 测试 FixContext
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.HIGH
        )
        
        assert context.project_root == project_root
        assert context.scope == FixScope.PROJECT
        assert context.priority == FixPriority.HIGH
        print("✓ FixContext 功能正常")
        
        # 测试 to_dict 方法
        result_dict = result.to_dict()
        context_dict = context.to_dict()
        
        assert result_dict["fix_type"] == "syntax_fix"
        assert result_dict["status"] == "success"
        assert context_dict["scope"] == "project"
        assert context_dict["priority"] == "high"
        print("✓ to_dict 方法正常")
        
    except Exception as e:
        print(f"✗ 数据类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def test_fix_type_descriptions():
    """测试修复类型描述功能"""
    print("\n测试修复类型描述功能...")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, get_fix_type_description
        
        # 测试描述函数
        syntax_desc = get_fix_type_description(FixType.SYNTAX_FIX)
        import_desc = get_fix_type_description(FixType.IMPORT_FIX)
        
        assert "语法错误" in syntax_desc
        assert "导入路径" in import_desc
        print("✓ 修复类型描述功能正常")
        print(f"  - 语法修复描述: {syntax_desc}")
        print(f"  - 导入修复描述: {import_desc}")
        
    except Exception as e:
        print(f"✗ 修复类型描述测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """主测试函数"""
    print("开始最小化测试统一自动修复系统...")
    print("=" * 40)
    
    # 运行各项测试
    tests = [
        test_imports_only,
        test_data_classes,
        test_fix_type_descriptions
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