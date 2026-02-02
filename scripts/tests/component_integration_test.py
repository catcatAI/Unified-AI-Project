#!/usr/bin/env python3
"""
组件集成测试 - 验证自动修复系统组件协同工作
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_component_integration():
    """测试组件集成"""
    print("测试组件集成...")
    
    try:
        # 导入所有必要组件
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        from unified_auto_fix_system.core.fix_result import FixContext, FixResult
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus, FixScope, FixPriority
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        
        print("✓ 所有组件导入成功")
        
        # 创建修复引擎
        engine = UnifiedFixEngine(project_root)
        print(f"✓ 修复引擎创建成功，加载了 {len(engine.modules)} 个模块")
        
        # 创建修复上下文
        context = FixContext(
            project_root=project_root,
            scope=FixScope.PROJECT,
            priority=FixPriority.NORMAL
        )
        print("✓ 修复上下文创建成功")
        
        # 创建修复器实例
        syntax_fixer = EnhancedSyntaxFixer(project_root)
        import_fixer = ImportFixer(project_root)
        print("✓ 修复器实例创建成功")
        
        # 测试修复器功能
        bad_code = "def test_func()\n    return True"
        fixed_code = syntax_fixer._fix_missing_colons(bad_code)
        if "def test_func():" in fixed_code:
            print("✓ 语法修复功能正常")
        else:
            print("✗ 语法修复功能异常")
            return False
        
        # 测试数据结构
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=1,
            issues_fixed=1
        )
        
        if result.is_successful():
            print("✓ 数据结构功能正常")
        else:
            print("✗ 数据结构功能异常")
            return False
        
        print("🎉 组件集成测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 组件集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始组件集成测试...")
    print("=" * 20)
    
    if test_component_integration():
        print("\n✅ 自动修复系统组件集成正常，可以协同工作。")
        return 0
    else:
        print("\n❌ 自动修复系统组件集成存在问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())