#!/usr/bin/env python3
"""
检查项目中是否还有可能存在问题的文件
"""

import os
import glob

def check_common_syntax_issues():
    """检查常见的语法错误模式"""
    # 查找所有Python文件
    python_files = glob.glob("./apps/backend/**/*.py", recursive=True)
    
    # 添加根目录下的部分Python文件
    root_py_files = glob.glob("./*.py")
    python_files.extend(root_py_files)
    
    issues = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for line_num, line in enumerate(lines, 1):
                    # 检查常见的语法错误模式
                    stripped_line = line.strip()
                    
                    # 检查未初始化的字典或列表
                    if "= " in stripped_line and stripped_line.endswith("="):
                        issues.append((file_path, line_num, "未初始化的变量", line.strip()))
                    
                    # 检查缺少括号的方法调用
                    if any(method in stripped_line for method in [".lower", ".upper", ".strip", ".split", ".keys", ".values", ".items", ".get"]) and "(" not in stripped_line and ")" not in stripped_line:
                        # 确保这不是字符串中的内容
                        if not stripped_line.startswith("#") and not stripped_line.startswith('"') and not stripped_line.startswith("'"):
                            issues.append((file_path, line_num, "可能缺少括号的方法调用", line.strip()))
                            
                    # 检查未实例化的类
                    if " = " in stripped_line and stripped_line.endswith("()"):
                        # 检查是否是类名(首字母大写)
                        parts = stripped_line.split(" = ")
                        if len(parts) == 2 and parts[1][0].isupper() and parts[1][-2:] == "()":
                            issues.append((file_path, line_num, "可能未正确实例化的类", line.strip()))
                            
        except Exception as e:
            pass  # 忽略无法读取的文件
    
    return issues

if __name__ == "__main__":
    issues = check_common_syntax_issues()
    
    if issues:
        print("发现可能存在问题的代码:")
        for file_path, line_num, issue_type, line in issues[:20]:  # 最多显示20个
            print(f"  {file_path}:{line_num} [{issue_type}] -> {line}")
        if len(issues) > 20:
            print(f"  ... 还有 {len(issues) - 20} 个问题")
    else:
        print("✅ 未发现明显的语法问题。")