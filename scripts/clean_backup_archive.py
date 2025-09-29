#!/usr/bin/env python3
"""
定期清理备份目录脚本
自动清理旧的备份归档目录，防止磁盘空间被过度占用
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level: str=logging.INFO,
    format: str='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        _ = logging.FileHandler('backup_cleanup.log'),
        _ = logging.StreamHandler()
    ]
)
logger: Any = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 备份目录路径
BACKUP_DIRS = [
    PROJECT_ROOT / 'backup',
    PROJECT_ROOT / 'apps' / 'backend' / 'backup'
]

# 保留最近N天的备份
RETENTION_DAYS = 7

def clean_old_backups():
    """清理旧的备份目录"""
    _ = logger.info("开始清理旧备份目录...")
    
    # 计算截止日期
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    _ = logger.info(f"保留 {RETENTION_DAYS} 天内的备份，截止日期: {cutoff_date.strftime('%Y-%m-%d')}")
    
    cleaned_count = 0
    
    # 遍历所有备份目录
    for backup_dir in BACKUP_DIRS:
        if not backup_dir.exists():
            continue
            
        _ = logger.info(f"检查目录: {backup_dir}")
        
        # 遍历目录中的所有子目录
        for item in backup_dir.iterdir():
            if not item.is_dir():
                continue
                
            # 检查是否为备份目录（以auto_fix_或backup_开头）
            if not (item.name.startswith('auto_fix_') or item.name.startswith('backup_')):
                continue
                
            # 获取目录的修改时间
            try:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
            except Exception as e:
                _ = logger.warning(f"无法获取目录修改时间 {item}: {e}")
                continue
                
            # 如果目录早于截止日期，则删除
            if mtime < cutoff_date:
                try:
                    _ = logger.info(f"删除旧备份目录: {item} (修改时间: {mtime.strftime('%Y-%m-%d')})")
                    _ = shutil.rmtree(item)
                    cleaned_count += 1
                except Exception as e:
                    _ = logger.error(f"删除目录失败 {item}: {e}")
    
    _ = logger.info(f"清理完成，共删除 {cleaned_count} 个旧备份目录")

def clean_excessive_backups(max_backups=10):
    """清理过多的备份目录，只保留最近的几个"""
    _ = logger.info(f"开始清理过多备份目录，只保留最近 {max_backups} 个...")
    
    cleaned_count = 0
    
    # 遍历所有备份目录
    for backup_dir in BACKUP_DIRS:
        if not backup_dir.exists():
            continue
            
        _ = logger.info(f"检查目录: {backup_dir}")
        
        # 获取所有备份目录并按修改时间排序
        backup_dirs = []
        for item in backup_dir.iterdir():
            if not item.is_dir():
                continue
                
            # 检查是否为备份目录
            if not (item.name.startswith('auto_fix_') or item.name.startswith('backup_')):
                continue
                
            try:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                _ = backup_dirs.append((item, mtime))
            except Exception as e:
                _ = logger.warning(f"无法获取目录修改时间 {item}: {e}")
                continue
        
        # 按修改时间排序（最新的在前）
        backup_dirs.sort(key=lambda x: x[1], reverse=True)
        
        # 删除超出数量的备份目录
        if len(backup_dirs) > max_backups:
            for item, mtime in backup_dirs[max_backups:]:
                try:
                    _ = logger.info(f"删除多余备份目录: {item} (修改时间: {mtime.strftime('%Y-%m-%d')})")
                    _ = shutil.rmtree(item)
                    cleaned_count += 1
                except Exception as e:
                    _ = logger.error(f"删除目录失败 {item}: {e}")
    
    _ = logger.info(f"清理完成，共删除 {cleaned_count} 个多余备份目录")

if __name__ == '__main__':
    try:
        # 清理旧备份
        _ = clean_old_backups()
        
        # 清理过多备份
        _ = clean_excessive_backups()
        
        _ = logger.info("备份清理任务完成")
    except Exception as e:
        _ = logger.error(f"备份清理任务失败: {e}")
        raise