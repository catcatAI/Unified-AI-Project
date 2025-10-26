#!/usr/bin/env python3
"""
检查项目中的语法错误并生成报告
"""

import os
import ast
from pathlib import Path

def check_syntax(file_path):
    """检查文件语法是否正确"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"行 {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"其他错误: {e}"

def get_python_files(root_dir):
    """获取项目中的所有Python文件"""
    python_files = []
    exclude_dirs = {'.git', '__pycache__', 'venv', '.venv', 'node_modules', 'backup', 'unified_fix_backups'}
    
    for root, dirs, files in os.walk(root_dir):
        # 排除特定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """主函数"""
    print("开始检查项目中的语法错误...")
    
    # 获取所有Python文件
    python_files = get_python_files('.')
    print(f"找到 {len(python_files)} 个Python文件")
    
    # 检查语法错误
    files_with_errors = []
    for file_path in python_files:
        is_valid, error = check_syntax(file_path)
        if not is_valid:
            files_with_errors.append((file_path, error))
    
    print(f"\n发现 {len(files_with_errors)} 个文件存在语法错误:")
    
    # 按目录分组显示错误
    errors_by_dir = {}
    for file_path, error in files_with_errors:
        dir_path = os.path.dirname(file_path)
        if dir_path not in errors_by_dir:
            errors_by_dir[dir_path] = []
        errors_by_dir[dir_path].append((file_path, error))
    
    # 显示错误详情
    for dir_path, errors in errors_by_dir.items():
        print(f"\n目录: {dir_path}")
        for file_path, error in errors:
            print(f"  ✗ {os.path.basename(file_path)} - {error}")
    
    # 保存错误报告
    with open('syntax_errors_report.txt', 'w', encoding='utf-8') as f:
        f.write("项目语法错误报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"总文件数: {len(python_files)}\n")
        f.write(f"错误文件数: {len(files_with_errors)}\n\n")
        
        for dir_path, errors in errors_by_dir.items():
            f.write(f"目录: {dir_path}\n")
            for file_path, error in errors:
                f.write(f"  {os.path.basename(file_path)} - {error}\n")
            f.write("\n")
    
    print(f"\n错误报告已保存到 syntax_errors_report.txt")

if __name__ == "__main__":
    main()