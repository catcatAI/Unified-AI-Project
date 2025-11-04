#!/usr/bin/env python3
"""
简单集成测试 - 验证核心功能 without 触发项目分析
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_functionality():
    """测试基本功能"""
    print("测试基本功能...")
    
    try:
        # 测试核心类型导入
        from unified_auto_fix_system.core.fix_types import FixType, FixStatus
        print("✓ 核心类型导入成功")
        
        # 测试数据类
        from unified_auto_fix_system.core.fix_result import FixResult
        result = FixResult(
            fix_type=FixType.SYNTAX_FIX,
            status=FixStatus.SUCCESS,
            issues_found=5,
            issues_fixed=5
        )
        assert result.is_successful()
        assert "成功修复 5 个问题" in result.summary()
        print("✓ 数据类功能正常")
        
        # 测试语法修复器（不触发项目分析）
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        fixer = EnhancedSyntaxFixer(project_root)
        
        # 直接测试修复方法
        bad_code = "def test_func()\n    return True"
        fixed_code = fixer._fix_missing_colons(bad_code)
        assert "def test_func():" in fixed_code
        print("✓ 语法修复功能正常")
        
        print("🎉 基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始简单集成测试...")
    print("=" * 20)
    
    if test_basic_functionality():
        print("\n✅ 自动修复系统基本功能正常。")
        return 0
    else:
        print("\n❌ 自动修复系统基本功能存在问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())