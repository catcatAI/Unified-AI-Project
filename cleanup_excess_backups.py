import os
import shutil
from pathlib import Path
from datetime import datetime

def cleanup_excess_backups():
    """清理多余的备份目录，只保留最近的3个"""
    project_root = Path(r"D:\Projects\Unified-AI-Project")
    backup_dir = project_root / "apps" / "backend" / "backup"
    
    if not backup_dir.exists():
        print("备份目录不存在")
        return
    
    # 获取所有auto_fix目录
    auto_fix_dirs = []
    for item in backup_dir.iterdir():
        if item.is_dir() and item.name.startswith('auto_fix_'):
            # 提取时间戳
            try:
                timestamp_str = item.name.split('_')[2] + '_' + item.name.split('_')[3]
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                auto_fix_dirs.append((timestamp, item))
            except Exception as e:
                print(f"无法解析目录名 {item.name}: {e}")
    
    # 按时间排序
    auto_fix_dirs.sort(key=lambda x: x[0], reverse=True)
    
    # 保留最近的3个，删除其余的
    if len(auto_fix_dirs) > 3:
        dirs_to_delete = auto_fix_dirs[3:]  # 保留前3个，其余删除
        print(f"找到 {len(auto_fix_dirs)} 个备份目录，将删除 {len(dirs_to_delete)} 个")
        
        for timestamp, dir_path in dirs_to_delete:
            print(f"删除备份目录: {dir_path.name} (时间: {timestamp})")
            try:
                shutil.rmtree(dir_path)
                print(f"  已删除: {dir_path}")
            except Exception as e:
                print(f"  删除失败: {e}")
    else:
        print(f"只有 {len(auto_fix_dirs)} 个备份目录，无需清理")

if __name__ == "__main__":
    cleanup_excess_backups()
