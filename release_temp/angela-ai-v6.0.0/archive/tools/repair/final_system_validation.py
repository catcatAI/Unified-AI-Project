#!/usr/bin/env python3
"""
最终系统验证 - 确认自动修复系统完全正常
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def validate_system_integrity():
    """验证系统完整性"""
    print("验证系统完整性...")
    
    # 1. 验证所有核心模块可以导入
    core_modules = [
        "unified_auto_fix_system",
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
    
    # 2. 验证所有修复模块可以导入
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
    
    # 3. 验证所有接口模块可以导入
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

def validate_fix_engine():
    """验证修复引擎"""
    print("\n验证修复引擎...")
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        
        # 创建引擎实例
        engine = UnifiedFixEngine(project_root)
        print("✓ 修复引擎创建成功")
        
        # 检查模块加载
        module_count = len(engine.modules)
        print(f"✓ 加载了 {module_count} 个修复模块")
        
        # 检查配置
        if "enabled_modules" in engine.config:
            print("✓ 配置加载成功")
        else:
            print("✗ 配置加载失败")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 修复引擎验证失败: {e}")
        return False

def validate_fixers():
    """验证修复器"""
    print("\n验证修复器...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        # 创建语法修复器
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        print("✓ 语法修复器创建成功")
        
        # 测试语法修复功能
        bad_code = "def test_func()\n    return True"
        fixed_code = syntax_fixer._fix_missing_colons(bad_code)
        if "def test_func():" in fixed_code:
            print("✓ 语法修复功能正常")
        else:
            print("✗ 语法修复功能异常")
            return False
        
        # 创建导入修复器
        import_fixer = ImportFixer(project_root)
        print("✓ 导入修复器创建成功")
        
        # 测试模块名计算
        from pathlib import Path
        module_name = import_fixer._calculate_module_name(Path("test/module.py"))
        if module_name == "test.module":
            print("✓ 模块名计算正常")
        else:
            print(f"✗ 模块名计算异常: {module_name}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 修复器验证失败: {e}")
        return False

def validate_data_structures():
    """验证数据结构"""
    print("\n验证数据结构...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope
        
        # 测试 FixResult
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=3,
            issues_fixed=3
        )
        
        if result.is_successful() and "成功修复 3 个问题" in result.summary():
            print("✓ FixResult 功能正常")
        else:
            print("✗ FixResult 功能异常")
            return False
        
        # 测试 FixContext
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT
        )
        
        context_dict = context.to_dict()
        if context_dict["scope"] == "project":
            print("✓ FixContext 功能正常")
        else:
            print("✗ FixContext 功能异常")
            return False
        
        return True
    except Exception as e:
        print(f"✗ 数据结构验证失败: {e}")
        return False

def main():
    """主函数"""
    print("开始最终系统验证...")
    print("=" * 25)
    
    # 运行各项验证
    validations = [
        ("系统完整性", validate_system_integrity),
        ("修复引擎", validate_fix_engine),
        ("修复器", validate_fixers),
        ("数据结构", validate_data_structures)
    ]
    
    passed = 0
    total = len(validations)
    
    for validation_name, validation_func in validations:
        print(f"\n[{validation_name}]")
        if validation_func():
            passed += 1
        else:
            print(f"  验证失败!")
    
    print("\n" + "=" * 25)
    print(f"验证完成: {passed}/{total} 项通过")
    
    if passed == total:
        print("🎉 最终验证通过！自动修复系统完全正常。")
        return 0
    else:
        print("❌ 最终验证失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())