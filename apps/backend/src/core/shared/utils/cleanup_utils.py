# =============================================================================
# ANGELA-MATRIX: L6[执行层] 全层级 [A] L2+
# =============================================================================
#
# 职责: 清理临时文件和缓存
# 维度: 涉及所有维度，维护系统整洁
# 安全: 使用 Key A (后端控制) 进行文件操作
# 成熟度: L2+ 等级理解系统维护的概念
#
# =============================================================================

import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def cleanup_temp_files(project_root: Path = Path(".")):
    """清除臨時文件"""
    temp_patterns = [
        "tmp_*",
        "temp_*",
        "*.tmp",
        "*.temp",
        "*.pyc",
        "__pycache__",
        ".pytest_cache",
        "*.log",
        ".coverage"
    ]
    
    total_deleted = 0
    
    for pattern in temp_patterns:
        for file_path in project_root.rglob(pattern):
            try:
                if file_path.is_file():
                    file_path.unlink()
                    total_deleted += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    total_deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
    
    logger.info(f"Cleaned up {total_deleted} items")
    return total_deleted

def cleanup_old_logs(log_dir: Path, days: int = 7):
    """清除旧的日志文件"""
    cutoff = datetime.now() - timedelta(days=days)
    total_deleted = 0
    
    for log_file in log_dir.glob("*.log"):
        try:
            if log_file.stat().st_mtime < cutoff.timestamp():
                log_file.unlink()
                total_deleted += 1
        except Exception as e:
            logger.warning(f"Failed to delete {log_file}: {e}")
    
    logger.info(f"Cleaned up {total_deleted} old log files")
    return total_deleted