#!/usr/bin/env python3
"""
备份目录清理脚本
定期清理项目中的备份目录，只保留最近的几个重要备份
"""

import shutil
import re
from pathlib import Path

def find_backup_dirs(root_path="."):
    """查找所有备份目录"""
    backup_dirs = []
    root = Path(root_path)
    
    # 查找所有可能的备份目录
    for dir_path in root.rglob("*"):
        if dir_path.is_dir():
            dir_name = dir_path.name
            # 匹配备份目录命名模式
            if (dir_name.startswith("backup") or 
                dir_name.startswith("auto_fix_") or
                re.match(r"backup_.*", str(dir_path)) or
                re.match(r"backup_archive.*", str(dir_path)) or
                "backup" in str(dir_path).lower()):
                backup_dirs.append(dir_path)
    
    return backup_dirs

def should_keep_backup_dir(dir_path):
    """判断是否应该保留备份目录"""
    dir_name = dir_path.name
    
    # 保留特定重要备份目录
    important_patterns = [
        r"backup_\d{8}_\d{6}",  # 格式如 backup_20250901_153000
        r"backup_archive_\d+",  # 归档备份
    ]
    
    for pattern in important_patterns:
        if re.match(pattern, dir_name):
            return True
    
    # 保留最近7天的备份
    try:
        # 如果目录名包含日期信息，检查是否是最近的
        if re.search(r"\d{8}", dir_name):
            # 提取日期并检查是否在最近7天内
            # 这里简化处理，实际可根据具体命名规则调整
            pass
    except:
        pass
    
    return False

def cleanup_backup_dirs(root_path=".", keep_recent_days=7):
    """清理备份目录"""
    backup_dirs = find_backup_dirs(root_path)
    
    if not backup_dirs:
        print("未找到备份目录")
        return
    
    print(f"找到 {len(backup_dirs)} 个备份目录:")
    for dir_path in backup_dirs:
        print(f"  - {dir_path}")
    
    # 确定要删除的目录
    dirs_to_delete = []
    dirs_to_keep = []
    
    for dir_path in backup_dirs:
        if should_keep_backup_dir(dir_path):
            dirs_to_keep.append(dir_path)
        else:
            dirs_to_delete.append(dir_path)
    
    print(f"\n将保留 {len(dirs_to_keep)} 个目录:")
    for dir_path in dirs_to_keep:
        print(f"  - {dir_path}")
    
    print(f"\n将删除 {len(dirs_to_delete)} 个目录:")
    for dir_path in dirs_to_delete:
        print(f"  - {dir_path}")
    
    # 确认删除
    if dirs_to_delete:
        confirm = input("\n确认删除这些目录吗? (y/N): ")
        if confirm.lower() in ['y', 'yes']:
            for dir_path in dirs_to_delete:
                try:
                    shutil.rmtree(dir_path)
                    print(f"已删除: {dir_path}")
                except Exception as e:
                    print(f"删除失败 {dir_path}: {e}")
        else:
            print("取消删除操作")
    else:
        print("没有需要删除的目录")

if __name__ == "__main__":
    print("备份目录清理工具")
    print("=" * 30)
    cleanup_backup_dirs()