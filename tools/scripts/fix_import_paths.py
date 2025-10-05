#!/usr/bin/env python3
"""
自动修复导入路径问题的脚本
"""

import os
import re
from pathlib import Path

def fix_import_paths_in_file(file_path):
    """
    修复单个文件中的导入路径问题
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找并修复错误的导入路径
        # 将 apps.backend.src.ai.xxx.yyy 导入路径修复为正确的路径
        pattern = r'from apps\.backend\.src\.ai\.([^\.]+)\.([^\.]+) import'
        replacement = r'from apps.backend.src.ai.\1.\2 import'

        # 检查是否需要修复
        if 'from apps.backend.src.ai.' in content:
            # 修复导入路径
            fixed_content = re.sub(
                r'from apps\.backend\.src\.ai\.([^\.]+)\.([^\.]+) import',
                r'from apps.backend.src.ai.\1.\2 import',
                content
            )

            # 如果内容有变化，写回文件
            if fixed_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"修复了文件中的导入路径: {file_path}")
                return True

        return False
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def scan_and_fix_import_paths(root_dir):
    """
    扫描并修复目录中所有Python文件的导入路径
    """
    fixed_count = 0
    error_count = 0

    # 遍历所有Python文件
    for py_file in Path(root_dir).rglob("*.py"):
        try:
            if fix_import_paths_in_file(py_file):
                fixed_count += 1
        except Exception as e:
            print(f"扫描文件 {py_file} 时出错: {e}")
            error_count += 1

    print(f"总共修复了 {fixed_count} 个文件的导入路径")
    if error_count > 0:
        print(f"处理过程中遇到 {error_count} 个错误")

    return fixed_count

def main() -> None:
    """
    主函数
    """
    # 获取项目根目录
    project_root: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print("开始扫描并修复导入路径问题...")
    print(f"项目根目录: {project_root}")

    # 修复测试目录中的导入路径
    test_dir = os.path.join(project_root, "apps", "backend", "tests")
    if os.path.exists(test_dir):
        print(f"扫描测试目录: {test_dir}")
        scan_and_fix_import_paths(test_dir)

    # 修复脚本目录中的导入路径
    scripts_dir = os.path.join(project_root, "scripts")
    if os.path.exists(scripts_dir):
        print(f"扫描脚本目录: {scripts_dir}")
        scan_and_fix_import_paths(scripts_dir)

    # 修复工具目录中的导入路径
    tools_dir = os.path.join(project_root, "tools")
    if os.path.exists(tools_dir):
        print(f"扫描工具目录: {tools_dir}")
        scan_and_fix_import_paths(tools_dir)

    print("导入路径修复完成!")

if __name__ == "__main__":
    main()