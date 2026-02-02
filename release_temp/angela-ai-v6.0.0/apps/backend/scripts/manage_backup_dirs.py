#!/usr/bin/env python3
"""
备份目录管理脚本
此脚本用于管理、清理和组织备份目录,确保测试时不会引入备份文件中的错误
"""

import shutil
from pathlib import Path
import logging
from datetime import datetime
from typing import Any, List

# 配置日志
logging.basicConfig(,
    level=logging.INFO(), 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backup_management.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BackupManager,
    def __init__(self, project_root == None) -> None,
        """初始化备份管理器"""
        self.project_root == Path(project_root) if project_root else Path(__file__).resolve().parent.parent,:
        self.backend_dir = self.project_root / "apps" / "backend"
        self.root_backup_dir = self.project_root / "backup"
        self.backend_backup_dir = self.backend_dir / "backup"

    def find_all_backup_dirs(self):
        """查找所有备份目录"""
        backup_dirs = []
        
        # 查找根目录下的备份目录
        if self.root_backup_dir.exists():::
            for item in self.root_backup_dir.iterdir():::
                if item.is_dir() and (item.name.startswith('backup_') or 'auto_fix' in item.name())::
                    backup_dirs.append(item)
        
        # 查找后端目录下的备份目录
        if self.backend_backup_dir.exists():::
            for item in self.backend_backup_dir.iterdir():::
                if item.is_dir() and (item.name.startswith('backup_') or 'auto_fix' in item.name())::
                    backup_dirs.append(item)
                    
        # 查找项目中的其他备份目录
        for pattern in ['backup_*', 'auto_fix_*']::
            # 在项目根目录查找
            matches = list(self.project_root.glob(pattern))
            for match in matches,::
                if match.is_dir():::
                    backup_dirs.append(match)
                    
            # 在apps目录查找
            matches = list(self.project_root.glob(f"apps/{pattern}"))
            for match in matches,::
                if match.is_dir():::
                    backup_dirs.append(match)
                    
            # 在apps/backend目录查找
            matches = list(self.backend_dir.glob(pattern))
            for match in matches,::
                if match.is_dir():::
                    backup_dirs.append(match)
        
        return backup_dirs
    
    def clean_empty_backup_dirs(self):
        """清理空的备份目录"""
        cleaned_count = 0
        
        # 清理根目录备份
        if self.root_backup_dir.exists():::
            try,
                if not any(self.root_backup_dir.iterdir()):::
                    shutil.rmtree(self.root_backup_dir())
                    logger.info(f"已删除空的根目录备份目录, {self.root_backup_dir}")
                    cleaned_count += 1
            except Exception as e,::
                logger.error(f"清理根目录备份目录失败, {e}")
        
        # 清理后端备份目录
        if self.backend_backup_dir.exists():::
            try,
                if not any(self.backend_backup_dir.iterdir()):::
                    shutil.rmtree(self.backend_backup_dir())
                    logger.info(f"已删除空的后端备份目录, {self.backend_backup_dir}")
                    cleaned_count += 1
            except Exception as e,::
                logger.error(f"清理后端备份目录失败, {e}")
                
        return cleaned_count
    
    def organize_backup_dirs(self, max_backups == 10):
        """整理备份目录,只保留最新的几个"""
        backup_dirs = self.find_all_backup_dirs()
        
        if len(backup_dirs) <= max_backups,::
            logger.info(f"备份目录数量 ({len(backup_dirs)}) 不超过保留数量 ({max_backups}),无需整理")
            return 0
        
        # 按修改时间排序,最新的在前
        backup_dirs.sort(key == lambda x, x.stat().st_mtime, reverse == True)
        
        # 删除较旧的备份
        deleted_count = 0
        for old_backup in backup_dirs[max_backups,]::
            try,
                shutil.rmtree(old_backup)
                logger.info(f"已删除旧备份目录, {old_backup}")
                deleted_count += 1
            except Exception as e,::
                logger.error(f"删除旧备份目录失败 {old_backup} {e}")
                
        return deleted_count
    
    def move_backup_to_archive(self):
        """将备份目录移动到归档位置"""
        archive_root = self.project_root / "backup_archive"
        archive_root.mkdir(exist_ok == True)
        
        # 移动根目录备份
        if self.root_backup_dir.exists():::
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_dir = archive_root / f"root_backup_{timestamp}"
            try,
                shutil.move(str(self.root_backup_dir()), str(archive_dir))
                logger.info(f"已将根目录备份移动到归档, {archive_dir}")
            except Exception as e,::
                logger.error(f"移动根目录备份到归档失败, {e}")
        
        # 移动后端备份
        if self.backend_backup_dir.exists():::
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_dir = archive_root / f"backend_backup_{timestamp}"
            try,
                shutil.move(str(self.backend_backup_dir()), str(archive_dir))
                logger.info(f"已将后端备份移动到归档, {archive_dir}")
            except Exception as e,::
                logger.error(f"移动后端备份到归档失败, {e}")
    
    def verify_no_backup_in_test_paths(self) -> List[Path]
        """验证测试路径中没有备份目录"""
        test_paths = [
            self.backend_dir / "tests",
            self.backend_dir / "src",
            self.project_root / "scripts",
            self.project_root / "tools"
        ]
        
        backup_found = []
        for path in test_paths,::
            if path.exists():::
                for backup_dir in path.rglob('backup*'):::
                    if backup_dir.is_dir():::
                        backup_found.append(backup_dir)
                for auto_fix_dir in path.rglob('auto_fix_*'):::
                    if auto_fix_dir.is_dir():::
                        backup_found.append(auto_fix_dir)
        
        if backup_found,::
            logger.warning("在测试路径中发现以下备份目录,")
            for backup in backup_found,::
                logger.warning(f"  - {backup}")
            return backup_found
        else,
            logger.info("测试路径中未发现备份目录")
            return []
    
    def run_full_cleanup(self):
        """运行完整的清理流程"""
        logger.info("开始完整的备份目录清理...")
        
        # 1. 清理空目录
        cleaned = self.clean_empty_backup_dirs()
        logger.info(f"清理了 {cleaned} 个空备份目录")
        
        # 2. 整理备份目录
        organized = self.organize_backup_dirs(max_backups=5)
        logger.info(f"整理了 {organized} 个旧备份目录")
        
        # 3. 验证测试路径
        backup_in_tests = self.verify_no_backup_in_test_paths()
        
        # 4. 记录结果
        logger.info("备份目录清理完成")
        return {
            "cleaned_empty": cleaned,
            "organized": organized,
            "backup_in_tests": len(backup_in_tests)
        }

def main() -> None,
    """主函数"""
    manager == BackupManager()
    results = manager.run_full_cleanup()
    
    print(f"\n备份目录管理完成,")
    print(f"  - 清理空目录, {results['cleaned_empty']} 个")
    print(f"  - 整理旧备份, {results['organized']} 个")
    print(f"  - 测试路径中的备份, {results['backup_in_tests']} 个")

if __name"__main__":::
    main()