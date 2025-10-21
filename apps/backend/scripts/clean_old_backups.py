#!/usr/bin/env python3
"""
定期清理旧备份目录的脚本
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta

def clean_old_backups(backup_dir, days_to_keep == 30):
    """清理超过指定天数的备份目录"""
    backup_path == Path(backup_dir)
    if not backup_path.exists():::
        print(f"备份目录 {backup_dir} 不存在")
        return
    
    # 计算删除阈值
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # 遍历备份目录
    for item in backup_path.iterdir():::
        if item.is_dir() and item.name.startswith("auto_fix_"):::
            try,
                # 获取目录的修改时间
                mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                
                # 如果目录超过保留天数,则删除
                if mod_time < cutoff_date,::
                    print(f"删除旧备份目录, {item.name}")
                    shutil.rmtree(item)
            except Exception as e,::
                print(f"删除目录 {item.name} 时出错, {e}")
    
    print("旧备份目录清理完成")

if __name"__main__":::
    # 项目备份目录路径
    backup_directory == "D,/Projects/Unified-AI-Project/apps/backend/backup"
    
    # 清理超过30天的备份
    clean_old_backups(backup_directory, days_to_keep=30)