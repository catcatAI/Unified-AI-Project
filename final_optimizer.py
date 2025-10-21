#!/usr/bin/env python3
"""
最终优化脚本
总结修复工作并提供后续建议
"""

import os
import sys
from pathlib import Path

def count_python_files():
    """统计项目中的Python文件数量"""
    python_files = list(Path(".").rglob("*.py"))
    return len(python_files)

def count_error_files():
    """统计存在语法错误的文件数量"""
    # 运行检查脚本并获取结果
    import subprocess
    try:
        result = subprocess.run(
            ["python", "check_syntax_errors.py"], 
            capture_output=True, 
            text=True,
            cwd="."
        )
        # 从输出中提取错误数量
        lines = result.stdout.split('\n') + result.stderr.split('\n')
        for line in lines:
            if "Total syntax errors found:" in line:
                return int(line.split(":")[-1].strip())
        return 0
    except:
        return -1

def generate_summary():
    """生成修复工作总结"""
    print("统一AI项目语法修复工作总结")
    print("=" * 50)
    
    # 统计文件数量
    total_files = count_python_files()
    print(f"项目总Python文件数: {total_files}")
    
    # 统计错误数量
    error_count = count_error_files()
    if error_count >= 0:
        print(f"剩余语法错误文件数: {error_count}")
        if total_files > 0:
            success_rate = (total_files - error_count) / total_files * 100
            print(f"语法正确率: {success_rate:.2f}%")
    
    # 核心文件状态
    print("\n核心文件状态:")
    core_files = [
        "./unified_auto_fix_system/__init__.py",
        "./unified_auto_fix_system/core/fix_result.py",
        "./unified_auto_fix_system/core/fix_types.py",
        "./unified_auto_fix_system/core/unified_fix_engine.py"
    ]
    
    for file_path in core_files:
        if os.path.exists(file_path):
            try:
                import ast
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                ast.parse(content)
                print(f"  ✓ {file_path}")
            except:
                print(f"  ✗ {file_path}")
        else:
            print(f"  - {file_path} (文件不存在)")
    
    # 生成建议
    print("\n后续建议:")
    print("1. 修复剩余的语法错误文件，特别是:")
    print("   - ./unified_auto_fix_system/core/fix_result_new.py")
    print("   - ./unified_auto_fix_system/core/enhanced_unified_fix_engine.py")
    print("2. 修复修复脚本自身的语法问题")
    print("3. 建立代码审查和自动化检查机制")
    print("4. 集成持续集成/持续部署(CI/CD)流程")
    
    print("\n修复工作完成!")

if __name__ == "__main__":
    generate_summary()
