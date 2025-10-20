#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查项目中的未使用文件
"""

import os
import glob

def find_unused_files():
    """查找可能未使用的文件"""
    print("🔍 开始查找未使用的文件...")
    
    # 定义可能未使用的文件模式
    unused_patterns = [
        '**/test_*.py',
        '**/*_test.py',
        '**/tests/*.py',
        '**/temp_*.py',
        '**/tmp_*.py',
        '**/old_*.py',
        '**/*_old.py',
        '**/backup_*.py',
        '**/*_backup.py'
    ]
    
    unused_files = []
    for pattern in unused_patterns:
        files = glob.glob(pattern, recursive=True)
        unused_files.extend(files)
    
    if unused_files:
        print(f"发现 {len(unused_files)} 个可能未使用的文件:")
        for file in unused_files:
            size = os.path.getsize(file)
            print(f"  {file} ({size} bytes)")
    else:
        print("✅ 未发现明显未使用的文件")
    
    return unused_files

def find_empty_files():
    """查找空文件"""
    print("\n🔍 开始查找空文件...")
    
    empty_files = []
    for root, dirs, files in os.walk('.'):
        # 跳过一些目录
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.pytest_cache', '.vscode']]
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    if os.path.getsize(filepath) == 0:
                        empty_files.append(filepath)
                except:
                    continue
    
    if empty_files:
        print(f"发现 {len(empty_files)} 个空文件:")
        for file in empty_files:
            print(f"  {file}")
    else:
        print("✅ 未发现空文件")
    
    return empty_files

def main():
    """主函数"""
    print("🔧 Unified AI Project 未使用文件检查工具")
    print("=" * 50)
    
    # 执行检查
    unused_files = find_unused_files()
    empty_files = find_empty_files()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 检查总结:")
    print(f"  未使用文件: {len(unused_files)}")
    print(f"  空文件: {len(empty_files)}")
    
    total_issues = len(unused_files) + len(empty_files)
    if total_issues > 0:
        print(f"\n⚠️ 总共发现 {total_issues} 个需要注意的文件")
    else:
        print("\n✅ 未发现问题")
    
    return total_issues

if __name__ == "__main__":
    main()