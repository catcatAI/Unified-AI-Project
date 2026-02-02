#!/usr/bin/env python3
"""
测试自动修复系统的核心功能，避免日志文件占用问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_core_imports():
    """测试核心导入功能"""
    print("测试核心导入功能...")
    
    try:
        # 测试核心类型
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope
        print("✓ 核心类型导入成功")
        
        # 测试结果类
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        print("✓ 结果类导入成功")
        
        # 测试修复引擎
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        print("✓ 修复引擎导入成功")
        
        # 测试修复模块
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        print("✓ 修复模块导入成功")
        
        # 测试接口
        from unified_auto_fix_system.interfaces.cli_interface import CLIFixInterface
        print("✓ 接口导入成功")
        
        return True
    except Exception as e:
        print(f"✗ 核心导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_types_and_enums():
    """测试修复类型和枚举"""
    print("\n测试修复类型和枚举...")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        
        # 测试枚举值
        assert FixType.SYNTAX_FIX.value == "syntax_fix"
        assert FixType.IMPORT_FIX.value == "import_fix"
        assert FixType.DEPENDENCY_FIX.value == "dependency_fix"
        assert FixType.AI_ASSISTED_FIX.value == "ai_assisted_fix"
        print("✓ 修复类型枚举正确")
        
        assert FixStatus.SUCCESS.value == "success"
        assert FixStatus.FAILED.value == "failed"
        assert FixStatus.PARTIAL_SUCCESS.value == "partial_success"
        print("✓ 修复状态枚举正确")
        
        assert FixScope.PROJECT.value == "project"
        assert FixScope.BACKEND.value == "backend"
        print("✓ 修复范围枚举正确")
        
        assert FixPriority.CRITICAL.value == "critical"
        assert FixPriority.NORMAL.value == "normal"
        print("✓ 修复优先级枚举正确")
        
        return True
    except Exception as e:
        print(f"✗ 修复类型和枚举测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_classes():
    """测试数据类功能"""
    print("\n测试数据类功能...")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixResult, FixContext
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        from pathlib import Path
        
        # 测试 FixResult
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=10,
            issues_fixed=10,
            target_path=Path("/test/file.py")
        )
        
        assert result.fix_type == FixType.SYNTAX_FIX
        assert result.status == FixStatus.SUCCESS
        assert result.issues_found == 10
        assert result.issues_fixed == 10
        assert result.is_successful() == True
        assert "成功修复 10 个问题" in result.summary()
        print("✓ FixResult 功能正常")
        
        # 测试 FixContext
        context = FixContext(
            project_root=Path("/test/project"),
            scope=FixScope.BACKEND,
            priority=FixPriority.HIGH
        )
        
        assert context.project_root == Path("/test/project")
        assert context.scope == FixScope.BACKEND
        assert context.priority == FixPriority.HIGH
        print("✓ FixContext 功能正常")
        
        # 测试 to_dict 方法
        result_dict = result.to_dict()
        context_dict = context.to_dict()
        
        assert result_dict["fix_type"] == "syntax_fix"
        assert result_dict["status"] == "success"
        assert result_dict["issues_found"] == 10
        assert context_dict["scope"] == "backend"
        assert context_dict["priority"] == "high"
        print("✓ to_dict 方法正常")
        
        return True
    except Exception as e:
        print(f"✗ 数据类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fixer_functionality():
    """测试修复器功能"""
    print("\n测试修复器功能...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        # 测试语法修复器方法
        fixer = EnhancedSyntaxFixer(Path("."))
        
        # 测试缺少冒号修复
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        assert "def test_func():" in fixed_code
        print("✓ 语法修复器方法正常")
        
        # 测试导入修复器方法
        import_fixer = ImportFixer(Path("."))
        
        # 测试模块名计算
        module_name = import_fixer._calculate_module_name(Path("test/module.py"))
        assert module_name == "test.module"
        print("✓ 导入修复器方法正常")
        
        return True
    except Exception as e:
        print(f"✗ 修复器功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_categories():
    """测试修复分类"""
    print("\n测试修复分类...")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixCategory
        
        # 测试严重程度分类
        severity_cats = FixCategory.SEVERITY_CATEGORIES
        assert "critical" in severity_cats
        assert "major" in severity_cats
        assert FixType.SYNTAX_FIX in severity_cats["critical"]
        print("✓ 严重程度分类正确")
        
        # 测试技术栈分类
        tech_cats = FixCategory.TECH_STACK_CATEGORIES
        assert "python" in tech_cats
        assert FixType.SYNTAX_FIX in tech_cats["python"]
        print("✓ 技术栈分类正确")
        
        # 测试项目部分分类
        proj_cats = FixCategory.PROJECT_CATEGORIES
        assert "backend" in proj_cats
        assert FixType.SYNTAX_FIX in proj_cats["backend"]
        print("✓ 项目部分分类正确")
        
        return True
    except Exception as e:
        print(f"✗ 修复分类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试自动修复系统的核心功能...")
    print("=" * 40)
    
    # 运行各项测试
    tests = [
        test_core_imports,
        test_fix_types_and_enums,
        test_data_classes,
        test_fixer_functionality,
        test_fix_categories
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
        print("🎉 所有核心功能测试通过！")
        return 0
    else:
        print("❌ 部分测试失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())