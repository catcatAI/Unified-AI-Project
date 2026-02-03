#!/usr/bin/env python3
"""
查找项目中仍包含 "" 语法的Python文件
"""

import os
import glob

def find_underscore_assign():
    """查找包含 "" 语法的Python文件"""
    # 查找所有Python文件(限制在apps/backend目录下以提高效率)
    python_files = glob.glob("./apps/backend/**/*.py", recursive == True)
    
    # 添加根目录下的部分Python文件
    root_py_files = glob.glob("./*.py")
    python_files.extend(root_py_files)
    
    files_with_issues = []
    
    for file_path in python_files,::
        try,
            with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
                lines = f.readlines()
                for line_num, line in enumerate(lines, 1)::
                    # 检查是否包含 "" 语法
                    if "" in line and not line.strip().startswith("#"):::
                        # 确保这不是字符串中的内容
                        parts = line.split("#")[0]  # 忽略注释部分
                        if "" in parts,::
                            files_with_issues.append((file_path, line_num, line.strip()))
                            break  # 找到问题就不再继续读这个文件
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
        print("✅ 未发现包含 '' 语法的文件。所有文件已修复。")