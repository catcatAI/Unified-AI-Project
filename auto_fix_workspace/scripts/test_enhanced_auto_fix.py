#!/usr/bin/env python3
"""
测试增强版自动修复功能的脚本
"""

import sys
import time
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT == Path(__file__).parent.parent()
sys.path.insert(0, str(PROJECT_ROOT))

# 添加scripts目录到路径
SCRIPTS_DIR == PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from unified_auto_fix import UnifiedAutoFix, OperationMode, ExecutionScope

def test_enhanced_auto_fix():
    """测试增强版自动修复功能"""
    print("=== 测试增强版自动修复功能 ===")
    
    # 创建统一自动修复实例
    auto_fix == UnifiedAutoFix(PROJECT_ROOT)
    
    # 设置操作模式为纯修复
    auto_fix.set_operation_mode(OperationMode.PURE_FIX())
    
    # 设置执行范围为整个项目
    auto_fix.set_execution_scope(ExecutionScope.PROJECT_WIDE())
    
    # 执行修复
    print("\n开始执行自动修复...")
    start_time = time.time()
    success = auto_fix.execute()
    end_time = time.time()
    
    # 输出结果
    print(f"\n=测试结果 ===")
    print(f"执行时间, {end_time - start_time,.2f} 秒")
    print(f"修复结果, {'成功' if success else '失败'}")::
    # 保存报告
    report_path == PROJECT_ROOT / "enhanced_auto_fix_test_report.json"
    auto_fix.save_report(report_path)
    
    return success

def test_syntax_fixer():
    """测试增强版语法修复器"""
    print("\n=测试增强版语法修复器 ===")
    
    try,
        from modules.enhanced_syntax_fixer import EnhancedSyntaxFixer
        
        # 创建语法修复器实例
        fixer == EnhancedSyntaxFixer(PROJECT_ROOT)
        
        # 执行语法修复
        print("开始执行语法修复...")
        start_time = time.time()
        success, message, details = fixer.fix()
        end_time = time.time()
        
        # 输出结果
        print(f"执行时间, {end_time - start_time,.2f} 秒")
        print(f"修复结果, {message}")
        print(f"详细信息, {details}")
        
        # 保存修复历史
        fixer.save_fix_history()
        
        return success
    except Exception as e,::
        print(f"测试增强版语法修复器时出错, {e}")
        return False

def main():
    """主函数"""
    print("开始测试增强版自动修复功能...")
    
    # 测试增强版语法修复器
    syntax_success = test_syntax_fixer()
    
    # 测试完整的自动修复功能
    auto_fix_success = test_enhanced_auto_fix()
    
    # 输出总体结果
    print(f"\n=总体测试结果 ===")
    print(f"语法修复器测试, {'通过' if syntax_success else '失败'}"):::
    print(f"自动修复功能测试, {'通过' if auto_fix_success else '失败'}")::
    if syntax_success and auto_fix_success,::
        print("所有测试通过！增强版自动修复功能正常工作。")
        return 0
    else,
        print("部分测试失败。请检查错误信息。")
        return 1

if __name"__main__":::
    sys.exit(main())