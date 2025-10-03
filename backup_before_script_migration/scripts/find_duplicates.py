#!/usr/bin/env python3
"""
查找项目中的重复文件脚本
"""

import os
import hashlib
from pathlib import Path
from collections import defaultdict

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

def calculate_file_hash(file_path):
    """
    计算文件的MD5哈希值
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None

def find_duplicate_files():
    """
    查找项目中的重复文件
    """
    # 文件哈希映射
    file_hashes = defaultdict(list)
    
    # 遍历项目目录
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 跳过隐藏目录和备份目录
        dirs[:] = [d for d in dirs if not d.startswith('.') and 'backup' not in d.lower() and '__pycache__' not in d]
        
        for file in files:
            # 只检查Python文件和重要配置文件
            if file.endswith(('.py', '.json', '.yaml', '.yml', '.toml', '.md')):
                file_path = os.path.join(root, file)
                file_hash = calculate_file_hash(file_path)
                if file_hash:
                    file_hashes[file_hash].append(file_path)
    
    # 找出重复文件
    duplicates = {hash_val: paths for hash_val, paths in file_hashes.items() if len(paths) > 1}
    
    return duplicates

def print_duplicates(duplicates):
    """
    打印重复文件信息
    """
    if not duplicates:
        print("No duplicate files found.")
        return
    
    print("Duplicate files found:")
    print("=" * 50)
    
    for hash_val, paths in duplicates.items():
        print(f"Hash: {hash_val}")
        for path in paths:
            print(f"  - {path}")
        print()

def main():
    """
    主函数
    """
    print("Searching for duplicate files...")
    duplicates = find_duplicate_files()
    print_duplicates(duplicates)

if __name__ == '__main__':
    main()