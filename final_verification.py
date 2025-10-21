#!/usr/bin/env python3
"""
最终验证脚本
检查核心文件是否正确修复
"""

import ast
import os
import sys
from pathlib import Path

def check_core_files():
    """检查核心文件的语法"""
    core_files = [
        # 统一自动修复系统核心文件
        "./unified_auto_fix_system/__init__.py",
        "./unified_auto_fix_system/core/fix_result.py",
        "./unified_auto_fix_system/core/fix_result_new.py",
        "./unified_auto_fix_system/core/fix_types.py",
        "./unified_auto_fix_system/core/unified_fix_engine.py",
        "./unified_auto_fix_system/core/enhanced_unified_fix_engine.py",
        
        # 修复脚本
        "./targeted_fix.py",
        "./final_precision_fix.py",
        "./comprehensive_syntax_fix.py",
        "./precise_syntax_fix.py",
        "./smart_fix_system.py",
        
        # 检查脚本
        "./check_syntax_errors.py"
    ]
    
    errors = 0
    error_files = []
    
    print("开始检查核心文件语法...")
    
    for file_path in core_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 尝试解析语法
                ast.parse(content)
                print(f"✓ {file_path}: 语法正确")
            except (SyntaxError, IndentationError) as e:
                errors += 1
                error_files.append((file_path, str(e)))
                print(f"✗ {file_path}: {e}")
            except Exception as e:
                errors += 1
                error_files.append((file_path, str(e)))
                print(f"✗ {file_path}: {e}")
        else:
            print(f"- {file_path}: 文件不存在")
    
    print(f"\n核心文件语法检查完成:")
    print(f"  总文件数: {len(core_files)}")
    print(f"  错误文件数: {errors}")
    
    if errors > 0:
        print("\n有语法错误的文件:")
        for file_path, error in error_files:
            print(f"  {file_path}: {error}")
        return 1
    else:
        print("\n所有核心文件语法正确!")
        return 0

def check_project_status():
    """检查项目整体状态"""
    print("\n检查项目整体状态...")
    
    # 检查是否存在备份文件
    backup_files = list(Path(".").rglob("*.bak"))
    if backup_files:
        print(f"发现 {len(backup_files)} 个备份文件")
    
    # 检查日志文件
    log_files = list(Path(".").rglob("*.log"))
    if log_files:
        print(f"发现 {len(log_files)} 个日志文件")
    
    print("项目状态检查完成")

if __name__ == "__main__":
    print("统一AI项目 - 最终验证脚本")
    print("=" * 40)
    
    # 检查核心文件
    core_result = check_core_files()
    
    # 检查项目状态
    check_project_status()
    
    print("\n" + "=" * 40)
    if core_result == 0:
        print("验证通过! 核心文件语法正确。")
    else:
        print("验证失败! 存在语法错误，请查看详细信息。")
    
    sys.exit(core_result)