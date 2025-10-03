#!/usr/bin/env python3
"""
清理备份模块脚本
"""

import os
import shutil
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 要删除的备份目录
BACKUP_DIRS = [
    'backup_modules',
]

def remove_backup_directories():
    """
    删除备份目录
    """
    removed_count = 0
    
    for backup_dir in BACKUP_DIRS:
        dir_path = PROJECT_ROOT / backup_dir
        if dir_path.exists() and dir_path.is_dir():
            try:
                shutil.rmtree(dir_path)
                print(f"Removed backup directory: {dir_path}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {dir_path}: {e}")
        else:
            print(f"Backup directory not found: {dir_path}")
    
    return removed_count

def main():
    """
    主函数
    """
    print("Starting backup modules cleanup...")
    
    # 确认操作
    confirm = input("This will permanently delete backup modules. Continue? (y/N): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    removed_count = remove_backup_directories()
    print(f"Cleanup complete. Removed {removed_count} backup directories.")

if __name__ == '__main__':
    main()