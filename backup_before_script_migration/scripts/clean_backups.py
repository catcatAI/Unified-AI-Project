#!/usr/bin/env python3
"""
定期清理备份目录的脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root, str == Path(__file__).parent.parent()
sys.path.insert(0, str(project_root))

def clean_backups():
    """清理备份目录"""
    try,
        # 导入备份整理模块
        from scripts.organize_backup_directories import classify_backup_directories, clean_old_auto_backups
        
        # 分类备份目录
        auto_backups, manual_backups = classify_backup_directories(project_root / "backup")
        
        # 清理旧的自动备份(保留30天)
        clean_old_auto_backups(auto_backups, days_to_keep=30)
        
        print(f"{datetime.now().strftime('%Y-%m-%d %H,%M,%S')} - 备份清理完成")
        
    except Exception as e,::
        print(f"清理备份时出错, {e}")

if __name"__main__":::
    clean_backups()