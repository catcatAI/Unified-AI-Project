#!/usr/bin/env python3
"""
简单系统检查 - 验证自动修复系统核心功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def check_system_components():
    """检查系统组件"""
    print("检查自动修复系统组件...")
    
    # 检查核心模块
    core_modules = [
        ("unified_auto_fix_system.core.fix_types", "修复类型模块"),
        ("unified_auto_fix_system.core.fix_result", "修复结果模块"),
        ("unified_auto_fix_system.core.unified_fix_engine", "统一修复引擎模块")
    ]
    
    for module_name, description in core_modules:
        try:
            __import__(module_name)
            print(f"✓ {description} [OK]")
        except Exception as e:
            print(f"✗ {description} [ERROR]: {e}")
            return False
    
    # 检查修复模块
    fix_modules = [
        ("unified_auto_fix_system.modules.base_fixer", "基础修复器模块"),
        ("unified_auto_fix_system.modules.syntax_fixer", "语法修复器模块"),
        ("unified_auto_fix_system.modules.import_fixer", "导入修复器模块"),
        ("unified_auto_fix_system.modules.dependency_fixer", "依赖修复器模块")
    ]
    
    for module_name, description in fix_modules:
        try:
            __import__(module_name)
            print(f"✓ {description} [OK]")
        except Exception as e:
            print(f"✗ {description} [ERROR]: {e}")
            return False
    
    # 检查接口模块
    interface_modules = [
        ("unified_auto_fix_system.interfaces.cli_interface", "CLI接口模块"),
        ("unified_auto_fix_system.interfaces.api_interface", "API接口模块"),
        ("unified_auto_fix_system.interfaces.ai_interface", "AI接口模块")
    ]
    
    for module_name, description in interface_modules:
        try:
            __import__(module_name)
            print(f"✓ {description} [OK]")
        except Exception as e:
            print(f"✗ {description} [ERROR]: {e}")
            return False
    
    return True

def check_fix_types():
    """检查修复类型"""
    print("\n检查修复类型...")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        
        # 检查主要修复类型
        main_types = [
            (FixType.SYNTAX_FIX, "语法修复"),
            (FixType.IMPORT_FIX, "导入修复"),
            (FixType.DEPENDENCY_FIX, "依赖修复"),
            (FixType.AI_ASSISTED_FIX, "AI辅助修复")
        ]
        
        for fix_type, description in main_types:
            print(f"✓ {description} [{fix_type.value}]")
        
        # 检查主要状态
        main_statuses = [
            (FixStatus.SUCCESS, "成功"),
            (FixStatus.FAILED, "失败"),
            (FixStatus.PARTIAL_SUCCESS, "部分成功")
        ]
        
        for status, description in main_statuses:
            print(f"✓ {description} [{status.value}]")
        
        return True
    except Exception as e:
        print(f"✗ 修复类型检查失败: {e}")
        return False

def check_data_classes():
    """检查数据类"""
    print("\n检查数据类...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope
        
        # 测试 FixResult
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=5,
            issues_fixed=5
        )
        
        assert result.is_successful()
        assert "成功修复 5 个问题" in result.summary()
        print("✓ FixResult 功能正常")
        
        # 测试 FixContext
        context = FixContext(
            project_root=Path("."),
            scope=FixScope.PROJECT
        )
        
        context_dict = context.to_dict()
        assert context_dict["scope"] == "project"
        print("✓ FixContext 功能正常")
        
        return True
    except Exception as e:
        print(f"✗ 数据类检查失败: {e}")
        return False

def check_fixer_functionality():
    """检查修复器功能"""
    print("\n检查修复器功能...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        
        # 创建修复器实例
        fixer = EnhancedSyntaxFixer(Path("."))
        
        # 检查方法存在
        methods_to_check = [
            '_fix_missing_colons',
            '_fix_indentation',
            '_fix_unmatched_parentheses'
        ]
        
        for method_name in methods_to_check:
            assert hasattr(fixer, method_name)
            print(f"✓ 方法 {method_name} 存在")
        
        # 测试修复功能
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        assert "def test_func():" in fixed_code
        print("✓ 语法修复功能正常")
        
        return True
    except Exception as e:
        print(f"✗ 修复器功能检查失败: {e}")
        return False

def main():
    """主函数"""
    print("开始简单系统检查...")
    print("=" * 25)
    
    # 运行各项检查
    checks = [
        ("系统组件", check_system_components),
        ("修复类型", check_fix_types),
        ("数据类", check_data_classes),
        ("修复器功能", check_fixer_functionality)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n[{check_name}]")
        if check_func():
            passed += 1
        else:
            print(f"  检查失败!")
    
    print("\n" + "=" * 25)
    print(f"检查完成: {passed}/{total} 项通过")
    
    if passed == total:
        print("🎉 系统检查通过！自动修复系统核心功能正常。")
        return 0
    else:
        print("❌ 系统检查失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())