#!/usr/bin/env python3
"""
统计项目中Python文件数量的脚本
"""

import os
from pathlib import Path

def count_python_files(directory):
    """统计指定目录下Python文件的数量"""
    count = 0
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.py'):
                count += 1
                files.append(os.path.join(root, filename))
    return count, files

def main():
    """主函数"""
    project_root = Path(__file__).parent.absolute()
    print(f"项目根目录: {project_root}")
    
    # 统计整个项目中的Python文件
    total_count, all_files = count_python_files(project_root)
    print(f"\n项目中共有 {total_count} 个Python文件")
    
    # 显示文件列表
    print("\nPython文件列表:")
    for i, file_path in enumerate(all_files, 1):
        relative_path = os.path.relpath(file_path, project_root)
        print(f"  {i:3d}. {relative_path}")

if __name__ == "__main__":
    main()