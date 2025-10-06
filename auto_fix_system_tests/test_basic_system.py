#!/usr/bin/env python3
"""
简化错误识别测试
"""

import sys
import os
import traceback
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_imports():
    """测试基本导入"""
    print("=== 基本导入测试 ===")
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import UnifiedFixEngine
        print("✓ 核心引擎导入成功")
    except Exception as e:
        print(f"✗ 核心引擎导入失败: {e}")
        traceback.print_exc()
        return False
    
    try:
        from unified_auto_fix_system.modules.base_fixer import BaseFixer
        print("✓ 基础修复器导入成功")
    except Exception as e:
        print(f"✗ 逻辑图谱修复器导入失败: {e}")
        traceback.print_exc()
        return False
    
    try:
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        print("✓ 语法修复器导入成功")
    except Exception as e:
        print(f"✗ 智能迭代修复器导入失败: {e}")
        traceback.print_exc()
        return False
    
    try:
        from unified_auto_fix_system.modules.import_fixer import ImportFixer
        print("✓ 导入修复器导入成功")
    except Exception as e:
        print(f"✗ AI辅助修复器导入失败: {e}")
        traceback.print_exc()
        return False
    
    return True

def test_simple_functionality():
    """测试简单功能"""
    print("\n=== 简单功能测试 ===")
    
    try:
        from unified_auto_fix_system.core.unified_fix_engine import FixContext
        from unified_auto_fix_system.modules.syntax_fixer import EnhancedSyntaxFixer
        from pathlib import Path
        
        # 创建测试文件
        test_file = Path("test_simple.py")
        with open(test_file, 'w') as f:
            f.write("def test(): pass\n")
        
        context = FixContext(
            project_root=Path("."),
            target_path=test_file,
            backup_enabled=True,
            dry_run=True
        )
        
        syntax_fixer = EnhancedSyntaxFixer(Path("."))
        issues = syntax_fixer.analyze(context)
        print(f"✓ 语法修复器分析完成，发现 {len(issues)} 个问题")
        
        # 清理
        test_file.unlink()
        return True
        
    except Exception as e:
        print(f"✗ 简单功能测试失败: {e}")
        traceback.print_exc()
        return False

def main():
    """主函数"""
    success = True
    success &= test_basic_imports()
    success &= test_simple_functionality()
    
    if success:
        print("\n🎉 基础测试通过！")
    else:
        print("\n❌ 基础测试失败，需要修复问题。")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)