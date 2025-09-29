#!/usr/bin/env python3
"""
清理多余的备份目录脚本
此脚本会删除apps/backend/backup目录下除了最近5个备份目录之外的所有目录
"""

import shutil
from pathlib import Path
import re
from datetime import datetime

def get_backup_dirs_sorted(backup_path):
    """获取按时间排序的备份目录列表"""
    backup_dirs = []
    
    if not backup_path.exists():
        return backup_dirs
        
    for item in backup_path.iterdir():
        if item.is_dir() and item.name.startswith('auto_fix_'):
            # 提取时间戳
            match = re.match(r'auto_fix_(\d{8}_\d{6})', item.name)
            if match:
                try:
                    timestamp_str = match.group(1)
                    timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    _ = backup_dirs.append((item, timestamp))
                except ValueError:
                    _ = print(f"无法解析时间戳: {item.name}")
    
    # 按时间戳排序，最新的在前
    backup_dirs.sort(key=lambda x: x[1], reverse=True)
    return backup_dirs

def cleanup_old_backups(backup_path, keep_count=5):
    """清理旧的备份目录"""
    backup_dirs = get_backup_dirs_sorted(backup_path)
    
    if len(backup_dirs) <= keep_count:
        _ = print(f"备份目录数量 ({len(backup_dirs)}) 不超过保留数量 ({keep_count})，无需清理")
        return
    
    # 删除多余的备份目录
    to_remove = backup_dirs[keep_count:]
    removed_count = 0
    
    _ = print(f"找到 {len(backup_dirs)} 个备份目录，将保留最近的 {keep_count} 个")
    _ = print(f"需要删除 {len(to_remove)} 个旧备份目录:")
    
    for dir_path, timestamp in to_remove:
        try:
            _ = print(f"  删除: {dir_path.name} ({timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
            _ = shutil.rmtree(dir_path)
            removed_count += 1
        except Exception as e:
            _ = print(f"  删除失败 {dir_path.name}: {e}")
    
    _ = print(f"成功删除 {removed_count} 个备份目录")

def cleanup_root_backup_dirs(root_path, keep_count=3):
    """清理根目录下的备份目录"""
    backup_patterns = [
        r'backup_\d{8}_\d{6}',
        r'backup_archive_\d{8}_\d{6}'
    ]
    
    backup_dirs = []
    for item in root_path.iterdir():
        if item.is_dir():
            for pattern in backup_patterns:
                if re.match(pattern, item.name):
                    # 提取时间戳
                    match = re.search(r'\d{8}_\d{6}', item.name)
                    if match:
                        try:
                            timestamp_str = match.group(0)
                            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                            _ = backup_dirs.append((item, timestamp))
                        except ValueError:
                            _ = print(f"无法解析时间戳: {item.name}")
    
    # 按时间戳排序，最新的在前
    backup_dirs.sort(key=lambda x: x[1], reverse=True)
    
    if len(backup_dirs) <= keep_count:
        _ = print(f"根目录备份目录数量 ({len(backup_dirs)}) 不超过保留数量 ({keep_count})，无需清理")
        return
    
    # 删除多余的备份目录
    to_remove = backup_dirs[keep_count:]
    removed_count = 0
    
    _ = print(f"根目录找到 {len(backup_dirs)} 个备份目录，将保留最近的 {keep_count} 个")
    _ = print(f"需要删除 {len(to_remove)} 个旧备份目录:")
    
    for dir_path, timestamp in to_remove:
        try:
            _ = print(f"  删除: {dir_path.name} ({timestamp.strftime('%Y-%m-%d %H:%M:%S')})")
            _ = shutil.rmtree(dir_path)
            removed_count += 1
        except Exception as e:
            _ = print(f"  删除失败 {dir_path.name}: {e}")
    
    _ = print(f"根目录成功删除 {removed_count} 个备份目录")

def main() -> None:
    """主函数"""
    project_root: str = Path(__file__).parent.parent
    backend_backup_path = project_root / 'apps' / 'backend' / 'backup'
    root_backup_path = project_root
    
    _ = print("开始清理备份目录...")
    
    # 清理apps/backend/backup目录
    if backend_backup_path.exists():
        _ = print(f"\n清理 {backend_backup_path} 目录:")
        cleanup_old_backups(backend_backup_path, keep_count=5)
    else:
        _ = print(f"\n目录不存在: {backend_backup_path}")
    
    # 清理根目录下的备份目录
    _ = print(f"\n清理根目录 {root_backup_path} 下的备份目录:")
    cleanup_root_backup_dirs(root_backup_path, keep_count=3)
    
    _ = print("\n备份目录清理完成!")

if __name__ == '__main__':
    _ = main()