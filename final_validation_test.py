#!/usr/bin/env python3
"""
最终验证自动修复系统的核心组件
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_system_components():
    """验证系统组件"""
    print("验证自动修复系统组件...")
    
    # 验证核心模块
    core_modules = [
        "unified_auto_fix_system.core.fix_types",
        "unified_auto_fix_system.core.fix_result",
        "unified_auto_fix_system.core.unified_fix_engine"
    ]
    
    for module in core_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            return False
    
    # 验证修复模块
    fix_modules = [
        "unified_auto_fix_system.modules.base_fixer",
        "unified_auto_fix_system.modules.syntax_fixer",
        "unified_auto_fix_system.modules.import_fixer",
        "unified_auto_fix_system.modules.dependency_fixer"
    ]
    
    for module in fix_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            return False
    
    # 验证接口模块
    interface_modules = [
        "unified_auto_fix_system.interfaces.cli_interface",
        "unified_auto_fix_system.interfaces.api_interface",
        "unified_auto_fix_system.interfaces.ai_interface"
    ]
    
    for module in interface_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except Exception as e:
            print(f"✗ {module}: {e}")
            return False
    
    return True

def validate_fix_types():
    """验证修复类型"""
    print("\n验证修复类型...")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        
        # 验证主要修复类型存在
        required_types = [
            FixType.SYNTAX_FIX,
            FixType.IMPORT_FIX,
            FixType.DEPENDENCY_FIX,
            FixType.AI_ASSISTED_FIX
        ]
        
        for fix_type in required_types:
            assert fix_type in FixType.__members__.values()
            print(f"✓ {fix_type.value}")
        
        # 验证状态类型
        required_statuses = [
            FixStatus.SUCCESS,
            FixStatus.FAILED,
            FixStatus.PARTIAL_SUCCESS
        ]
        
        for status in required_statuses:
            assert status in FixStatus.__members__.values()
            print(f"✓ {status.value}")
        
        return True
    except Exception as e:
        print(f"✗ 修复类型验证失败: {e}")
        return False

def validate_data_classes():
    """验证数据类"""
    print("\n验证数据类...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope
        
        # 验证 FixResult
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=5,
            issues_fixed=5
        )
        
        assert result.is_successful()
        assert "成功修复 5 个问题" in result.summary()
        print("✓ FixResult 功能正常")
        
        # 验证 FixContext
        context = FixContext(
            project_root=Path("."),
            scope=FixScope.PROJECT
        )
        
        context_dict = context.to_dict()
        assert context_dict["scope"] == "project"
        print("✓ FixContext 功能正常")
        
        return True
    except Exception as e:
        print(f"✗ 数据类验证失败: {e}")
        return False

def validate_fixer_methods():
    """验证修复器方法"""
    print("\n验证修复器方法...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        # 创建修复器实例
        fixer = EnhancedSyntaxFixer(Path("."))
        
        # 验证方法存在
        assert hasattr(fixer, '_fix_missing_colons')
        assert hasattr(fixer, '_fix_indentation')
        assert hasattr(fixer, '_fix_unmatched_parentheses')
        print("✓ 语法修复器方法存在")
        
        # 验证修复功能
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        assert "def test_func():" in fixed_code
        print("✓ 语法修复功能正常")
        
        return True
    except Exception as e:
        print(f"✗ 修复器方法验证失败: {e}")
        return False

def main():
    """主验证函数"""
    print("开始最终验证自动修复系统...")
    print("=" * 30)
    
    # 运行各项验证
    validations = [
        validate_system_components,
        validate_fix_types,
        validate_data_classes,
        validate_fixer_methods
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        if validation():
            passed += 1
        print()
    
    print("=" * 30)
    print(f"验证完成: {passed}/{total} 项验证通过")
    
    if passed == total:
        print("🎉 系统验证通过！自动修复系统核心组件功能正常。")
        return 0
    else:
        print("❌ 系统验证失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())