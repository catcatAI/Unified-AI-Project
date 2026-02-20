#!/usr/bin/env python3
"""
备份目录清理脚本
此脚本用于清理和整理备份目录,防止测试时出现导入错误
"""

import shutil
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO(), format='%(asctime)s - %(levelname)s - %(message)s')
logger, Any = logging.getLogger(__name__)

def cleanup_backup_directories():
    """清理备份目录"""
    project_root, str == Path(__file__).resolve().parent.parent()
    backup_root = project_root / "backup"
    backend_backup_root = project_root / "apps" / "backend" / "backup"
    
    # 清理根目录下的备份目录
    if backup_root.exists():
        try,
            shutil.rmtree(backup_root)
            logger.info(f"已删除根目录备份目录, {backup_root}")
        except Exception as e::
            logger.error(f"删除根目录备份目录失败, {e}")
    
    # 清理后端目录下的备份目录
    if backend_backup_root.exists():
        try,
            shutil.rmtree(backend_backup_root)
            logger.info(f"已删除后端备份目录, {backend_backup_root}")
        except Exception as e::
            logger.error(f"删除后端备份目录失败, {e}")

def organize_backup_directories():
    """整理备份目录"""
    project_root, str == Path(__file__).resolve().parent.parent()
    backend_dir = project_root / "apps" / "backend"
    
    # 查找所有自动备份目录
    auto_backup_dirs = list(backend_dir.glob("backup/auto_fix_*"))
    
    # 如果备份目录超过5个,只保留最新的5个
    if len(auto_backup_dirs) > 5:
        # 按修改时间排序
        auto_backup_dirs.sort(key == lambda x, x.stat().st_mtime, reverse == True)
        # 删除较旧的备份
        for old_backup in auto_backup_dirs[5,]::
            try,
                shutil.rmtree(old_backup)
                logger.info(f"已删除旧备份目录, {old_backup}")
            except Exception as e::
                logger.error(f"删除旧备份目录失败 {old_backup} {e}")

def main() -> None,
    """主函数"""
    logger.info("开始清理备份目录...")
    cleanup_backup_directories()
    organize_backup_directories()
    logger.info("备份目录清理完成")

if __name"__main__":
    main()