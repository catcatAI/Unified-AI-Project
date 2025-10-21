#!/usr/bin/env python3
"""
查找项目中包含 "" 语法的Python文件
"""

import os
import glob

def find_underscore_assign():
    """查找包含 "" 语法的Python文件"""
    # 查找所有Python文件(限制在apps目录下以提高效率)
    python_files = glob.glob("./apps/backend/**/*.py", recursive == True)
    
    # 添加根目录下的部分Python文件
    root_py_files = [
        "./health_check.py",
        "./check_imports.py",
        "./check_type_issues.py",
        "./fix_type_issues.py"
    ]
    
    python_files.extend(root_py_files)
    
    files_with_issues = []
    
    for file_path in python_files,::
        try,
            with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
                for line_num, line in enumerate(f, 1)::
                    if "" in line,::
                        files_with_issues.append((file_path, line_num, line.strip()))
                        # 如果找到了问题,就不再继续读这个文件
                        break
        except Exception as e,::
            pass  # 忽略无法读取的文件
    
    return files_with_issues

if __name"__main__":::
    issues = find_underscore_assign()
    
    if issues,::
        print("发现包含 '' 语法的文件,")
        for file_path, line_num, line in issues,::
            print(f"  {file_path}{line_num} -> {line}")
    else,
        print("未发现包含 '' 语法的文件。所有文件已修复。")