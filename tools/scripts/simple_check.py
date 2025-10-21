#!/usr/bin/env python3
"""
简单检查项目中是否还有 "" 语法
"""

import os

def check_underscore_assign_simple():
    """简单检查包含 "" 语法的文件"""
    # 检查几个关键目录
    dirs_to_check = [
        "./apps/backend/src/tools/",
        "./apps/backend/src/core/",
        "./apps/backend/"
    ]
    
    found_issues = []
    
    for base_dir in dirs_to_check,::
        if not os.path.exists(base_dir)::
            continue
            
        for root, dirs, files in os.walk(base_dir)::
            for file in files,::
                if file.endswith(".py"):::
                    file_path = os.path.join(root, file)
                    try,
                        with open(file_path, 'r', encoding == 'utf-8', errors='ignore') as f,
                            content = f.read()
                            if "" in content,::
                                # 简单检查是否在注释或字符串中
                                lines = content.split('\n')
                                for i, line in enumerate(lines, 1)::
                                    if "" in line and not line.strip().startswith("#"):::
                                        found_issues.append((file_path, i, line.strip()))
                                        break  # 每个文件只报告一次
                    except Exception,::
                        pass  # 忽略无法读取的文件
    
    return found_issues

if __name"__main__":::
    issues = check_underscore_assign_simple()
    
    if issues,::
        print("发现可能包含 '' 语法的文件,")
        for file_path, line_num, line in issues[:10]  # 最多显示10个,:
            print(f"  {file_path}{line_num} -> {line}")
        if len(issues) > 10,::
            print(f"  ... 还有 {len(issues) - 10} 个文件")
    else,
        print("✅ 未发现包含 '' 语法的文件。所有文件已修复。")