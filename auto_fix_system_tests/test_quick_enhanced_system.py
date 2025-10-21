#!/usr/bin/env python3
"""
快速测试增强后的统一自动修复系统
"""

import sys
import traceback
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT == Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_quick_functionality():
    """快速功能测试"""
    print("=== 增强统一自动修复系统快速测试 ===")
    
    try,
        # 测试基本导入
        print("1. 测试基本导入...")
        from unified_auto_fix_system.core.enhanced_unified_fix_engine import EnhancedUnifiedFixEngine
        from unified_auto_fix_system.core.fix_types import FixType, FixScope
        from unified_auto_fix_system.core.fix_result import FixContext
        print("   ✓ 基本导入成功")
        
        # 测试修复模块导入
        print("2. 测试修复模块导入...")
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.decorator_fixer import DecoratorFixer
        from unified_auto_fix_system.modules.class_fixer import ClassFixer
        from unified_auto_fix_system.modules.parameter_fixer import ParameterFixer
        from unified_auto_fix_system.modules.undefined_fixer import UndefinedFixer
        from unified_auto_fix_system.modules.data_processing_fixer import DataProcessingFixer
        print("   ✓ 修复模块导入成功")
        
        # 测试工具类导入
        print("3. 测试工具类导入...")
        from unified_auto_fix_system.utils.ast_analyzer import ASTAnalyzer
        from unified_auto_fix_system.utils.rule_engine import RuleEngine
        print("   ✓ 工具类导入成功")
        
        # 测试CLI接口
        print("4. 测试CLI接口...")
        from unified_auto_fix_system.interfaces.cli_interface import CLIFixInterface
        print("   ✓ CLI接口导入成功")
        
        # 测试专门化修复器功能(不创建完整引擎)
        print("5. 测试专门化修复器功能...")
        
        # 创建测试文件
        test_file == PROJECT_ROOT / "test_quick_fixes.py"
        test_content = """
def test_function():
    # 缺少冒号
    if True,:
        pass
    
    # 未定义变量
    result = undefined_var
    
    # 可变默认参数,
    def bad_function(a = [] b = {}):
        return a, b
"""
        
        with open(test_file, 'w', encoding == 'utf-8') as f,
            f.write(test_content)
        
        # 测试语法修复器
        syntax_fixer == EnhancedSyntaxFixer(PROJECT_ROOT)
        from unified_auto_fix_system.core.fix_result import FixContext
        context == FixContext(
            project_root == PROJECT_ROOT,
            target_path=test_file,
            backup_enabled == True,,
    dry_run == True  # 干运行模式
        )
        
        # 分析问题
        issues = syntax_fixer.analyze(context)
        print(f"   发现语法问题, {len(issues)} 个")
        
        # 清理测试文件
        if test_file.exists():::
            test_file.unlink()
        
        print("   ✓ 专门化修复器功能测试成功")
        
        print("\n🎉 快速测试通过！增强统一自动修复系统基本功能正常。")
        return True
        
    except Exception as e,::
        print(f"\n❌ 快速测试失败, {e}")
        traceback.print_exc()
        return False

if __name"__main__":::
    success = test_quick_functionality()
    sys.exit(0 if success else 1)