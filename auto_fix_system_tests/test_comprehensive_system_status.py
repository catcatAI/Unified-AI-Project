#!/usr/bin/env python3
"""
全面测试修复系统状态
检查所有模块和功能的完整性
"""

import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_system_imports():
    """测试系统导入"""
    print("=== 测试修复系统导入 ===")
    
    # 核心引擎
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine, FixContext
        from unified_auto_fix_system.core.fix_types import FixType, FixScope
        print("✓ 核心引擎导入成功")
    except Exception as e:
        print(f"✗ 核心引擎导入失败: {e}")
        return False
    
    # 修复模块
    modules = [
        ("syntax_fixer", "EnhancedSyntaxFixer"),
        ("decorator_fixer", "DecoratorFixer"),
        ("class_fixer", "ClassFixer"),
        ("parameter_fixer", "ParameterFixer"),
        ("undefined_fixer", "UndefinedFixer"),
        ("data_processing_fixer", "DataProcessingFixer"),
        ("logic_graph_fixer", "LogicGraphFixer"),
        ("intelligent_iterative_fixer", "IntelligentIterativeFixer"),
        ("ai_assisted_fixer", "AIAssistedFixer")
    ]
    
    for module_name, class_name in modules:
        try:
            module = __import__(f"unified_auto_fix_system.modules.{module_name}", fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name} 导入成功")
        except Exception as e:
            print(f"✗ {module_name} 导入失败: {e}")
            return False
    
    # 工具类
    tools = [
        ("ast_analyzer", "ASTAnalyzer"),
        ("dependency_tracker", "DependencyTracker"),
        ("io_analyzer", "IOAnalyzer"),
        ("rule_engine", "RuleEngine")
    ]
    
    for module_name, class_name in tools:
        try:
            module = __import__(f"unified_auto_fix_system.utils.{module_name}", fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name} 导入成功")
        except Exception as e:
            print(f"✗ {module_name} 导入失败: {e}")
            return False
    
    print("✓ 所有模块导入成功")
    return True

def test_fix_types():
    """测试修复类型"""
    print("\n=== 测试修复类型 ===")
    
    try:
        from unified_auto_fix_system.core.fix_types import FixType
        
        fix_types = [
            FixType.SYNTAX_FIX,
            FixType.IMPORT_FIX,
            FixType.DEPENDENCY_FIX,
            FixType.DECORATOR_FIX,
            FixType.CLASS_FIX,
            FixType.PARAMETER_FIX,
            FixType.UNDEFINED_FIX,
            FixType.DATA_PROCESSING_FIX,
            FixType.LOGIC_GRAPH_FIX,
            FixType.INTELLIGENT_ITERATIVE_FIX,
            FixType.AI_ASSISTED_FIX
        ]
        
        for fix_type in fix_types:
            print(f"✓ {fix_type.value} 可用")
        
        return True
    except Exception as e:
        print(f"✗ 修复类型测试失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    try:
        from unified_auto_fix_system.core.fix_result import FixContext
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from pathlib import Path
        
        # 创建测试上下文
        context = FixContext(
            project_root=Path("."),
            backup_enabled=True,
            dry_run=True
        )
        
        # 测试语法修复器
        syntax_fixer = EnhancedSyntaxFixer(Path("."))
        issues = syntax_fixer.analyze(context)
        print(f"✓ 语法修复器分析完成，发现 {len(issues)} 个问题")
        
        # 测试逻辑图谱修复器
        from unified_auto_fix_system.modules.logic_graph_fixer import LogicGraphFixer
        logic_fixer = LogicGraphFixer(Path("."))
        logic_issues = logic_fixer.analyze(context)
        print(f"✓ 逻辑图谱修复器分析完成，发现 {len(logic_issues)} 个问题")
        
        return True
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("=== 全面测试修复系统状态 ===")
    print(f"测试时间: {datetime.now()}")
    
    success = True
    
    # 运行所有测试
    success &= test_system_imports()
    success &= test_fix_types()
    success &= test_basic_functionality()
    
    if success:
        print("\n🎉 所有测试通过！修复系统状态良好。")
    else:
        print("\n❌ 测试失败，需要修复问题。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)