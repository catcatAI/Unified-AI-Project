#!/usr/bin/env python3
"""
简单检查项目中是否还有明显的语法问题
"""

import os

def simple_check():
    """简单检查"""
    # 检查几个关键目录
    dirs_to_check = [
        "./apps/backend/src/tools/",
        "./apps/backend/src/core/",
        "./apps/backend/src/core_ai/"
    ]
    
    found_issues = []
    
    for base_dir in dirs_to_check:
        if not os.path.exists(base_dir):
            continue
            
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                # 检查明显的语法错误
                                if line.strip().endswith("= "):
                                    found_issues.append((file_path, i, "未初始化变量", line.strip()))
                                elif ".lower" in line and "(" not in line.split(".lower")[1][:10]:
                                    # 简单检查lower方法调用
                                    if not line.strip().startswith("#"):
                                        found_issues.append((file_path, i, "可能缺少括号", line.strip()))
                    except Exception:
                        pass  # 忽略无法读取的文件
    
    return found_issues

if __name__ == "__main__":
    issues = simple_check()
    
    if issues:
        print("发现可能存在问题的代码:")
        for file_path, line_num, issue_type, line in issues[:10]:  # 最多显示10个
            print(f"  {file_path}:{line_num} [{issue_type}] -> {line}")
        if len(issues) > 10:
            print(f"  ... 还有 {len(issues) - 10} 个问题")
    else:
        print("✅ 未发现明显的语法问题。")