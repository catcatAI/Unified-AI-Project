#!/usr/bin/env python3
"""
检查项目中所有Python文件的语法错误
"""

import os
import sys
import subprocess
from pathlib import Path

def check_syntax_errors(root_dir="."):
    """检查指定目录下所有Python文件的语法错误"""
    error_files = []
    
    # 遍历所有Python文件
    for py_file in Path(root_dir).rglob("*.py"):
        try:
            # 使用Python编译器检查语法
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 如果返回码不为0，说明有语法错误
            if result.returncode != 0:
                error_files.append((py_file, result.stderr))
                print(f"语法错误: {py_file}")
                print(f"错误详情: {result.stderr}")
                print("-" * 50)
                
        except subprocess.TimeoutExpired:
            error_files.append((py_file, "检查超时"))
            print(f"检查超时: {py_file}")
        except Exception as e:
            error_files.append((py_file, str(e)))
            print(f"检查异常: {py_file}, 错误: {e}")
    
    return error_files

if __name__ == "__main__":
    print("开始检查项目中的Python文件语法错误...")
    errors = check_syntax_errors(".")
    
    if errors:
        print(f"\n发现 {len(errors)} 个文件存在语法错误:")
        for file_path, error_msg in errors:
            print(f"  - {file_path}")
    else:
        print("\n恭喜！所有Python文件都没有语法错误。")