#!/usr/bin/env python3
"""
测试自动修复系统的修复规则
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_syntax_fix_rules():
    """测试语法修复规则"""
    print("测试语法修复规则...")
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.core.fix_types import FixScope, FixPriority
        
        # 创建语法修复器实例（使用临时目录避免扫描整个项目）
        temp_dir = project_root / "temp_test"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            fixer = EnhancedSyntaxFixer(temp_dir)
            print("✓ 语法修复器创建成功")
            
            # 检查错误模式
            assert "missing_colon" in fixer.error_patterns
            assert "unmatched_parentheses" in fixer.error_patterns
            assert "invalid_syntax" in fixer.error_patterns
            print("✓ 语法错误模式正确")
            
            # 测试修复方法
            test_content = "def test_function()\n    return True"
            fixed_content = fixer._fix_missing_colons(test_content)
            assert "def test_function():" in fixed_content
            print("✓ 缺少冒号修复功能正常")
            
            test_content2 = "if True:\nprint('hello')"
            fixed_content2 = fixer._fix_indentation(test_content2)
            print("✓ 缩进修复功能正常")
            
        finally:
            # 清理临时目录
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"✗ 语法修复规则测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_fix_rules():
    """测试导入修复规则"""
    print("\n测试导入修复规则...")
    
    try:
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        # 创建导入修复器实例
        temp_dir = project_root / "temp_test"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            fixer = ImportFixer(temp_dir)
            print("✓ 导入修复器创建成功")
            
            # 检查导入模式
            assert "absolute_import_issue" in fixer.import_patterns
            assert "relative_import_issue" in fixer.import_patterns
            print("✓ 导入错误模式正确")
            
            # 测试模块名计算
            test_path = temp_dir / "test_module.py"
            module_name = fixer._calculate_module_name(test_path)
            assert module_name == "test_module"
            print("✓ 模块名计算功能正常")
            
            # 测试相对导入解析
            resolved = fixer._resolve_relative_import("package.module", "submodule", 1)
            print("✓ 相对导入解析功能正常")
            
        finally:
            # 清理临时目录
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"✗ 导入修复规则测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependency_fix_rules():
    """测试依赖修复规则"""
    print("\n测试依赖修复规则...")
    
    try:
        from unified_auto_fix_system.modules.dependency_fixer import DependencyFixer
        
        # 创建依赖修复器实例
        temp_dir = project_root / "temp_test"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            fixer = DependencyFixer(temp_dir)
            print("✓ 依赖修复器创建成功")
            
            # 检查依赖文件映射
            assert "python" in fixer.dependency_files
            assert "nodejs" in fixer.dependency_files
            assert "requirements.txt" in fixer.dependency_files["python"]
            print("✓ 依赖文件映射正确")
            
            # 检查依赖模式
            assert "import_error" in fixer.dependency_patterns
            assert "module_not_found" in fixer.dependency_patterns
            print("✓ 依赖错误模式正确")
            
            # 测试需求行解析
            req_info = fixer._parse_requirement_line("numpy>=1.18.0")
            assert req_info["name"] == "numpy"
            assert req_info["version"] == ">=1.18.0"
            print("✓ 需求行解析功能正常")
            
        finally:
            # 清理临时目录
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        
        return True
    except Exception as e:
        print(f"✗ 依赖修复规则测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fix_type_categories():
    """测试修复类型分类"""
    print("\n测试修复类型分类...")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType, FixCategory
        
        # 检查严重程度分类
        severity_cats = FixCategory.SEVERITY_CATEGORIES
        assert "critical" in severity_cats
        assert "major" in severity_cats
        assert "minor" in severity_cats
        assert FixType.SYNTAX_FIX in severity_cats["critical"]
        assert FixType.IMPORT_FIX in severity_cats["major"]
        print("✓ 严重程度分类正确")
        
        # 检查技术栈分类
        tech_cats = FixCategory.TECH_STACK_CATEGORIES
        assert "python" in tech_cats
        assert "javascript" in tech_cats
        assert FixType.SYNTAX_FIX in tech_cats["python"]
        assert FixType.IMPORT_FIX in tech_cats["python"]
        print("✓ 技术栈分类正确")
        
        # 检查项目部分分类
        proj_cats = FixCategory.PROJECT_CATEGORIES
        assert "backend" in proj_cats
        assert "frontend" in proj_cats
        assert FixType.SYNTAX_FIX in proj_cats["backend"]
        assert FixType.IMPORT_FIX in proj_cats["backend"]
        print("✓ 项目部分分类正确")
        
        return True
    except Exception as e:
        print(f"✗ 修复类型分类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始测试统一自动修复系统的修复规则...")
    print("=" * 50)
    
    # 运行各项测试
    tests = [
        test_syntax_fix_rules,
        test_import_fix_rules,
        test_dependency_fix_rules,
        test_fix_type_categories
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
        print("🎉 所有修复规则测试通过！")
        return 0
    else:
        print("❌ 部分修复规则测试失败，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())