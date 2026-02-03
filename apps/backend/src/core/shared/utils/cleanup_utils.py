# TODO: Fix import - module 'shutil' not found
from tests.tools.test_tool_dispatcher_logging import
from pathlib import Path
from datetime import datetime, timedelta
logger, Any = logging.getLogger(__name__)


def cleanup_temp_files(project_root, Path == Path(".")):
    """清除臨時文件"""
    temp_patterns = []
        "tmp_ * ",
        "temp_ * ",
        " * .tmp",
        " * .temp",
        " * .pyc",
        "__pycache__",
        ".pytest_cache",
        " * .log",
        ".coverage"
[    ]

    for pattern in temp_patterns, ::
        for file_path in project_root.rglob(pattern)::
            try,
                if file_path.is_file, ::
                    file_path.unlink()
                    logger.debug(f"刪除臨時文件, {file_path}")
                elif file_path.is_dir, ::
                    shutil.rmtree(file_path)
                    logger.debug(f"刪除臨時目錄, {file_path}")
            except Exception as e, ::
                logger.warning(f"刪除文件失敗 {file_path} {e}")


def cleanup_cache_data(retention_days, int, project_root, Path == Path(".")):
    """清除緩存數據"""
    cutoff_date = datetime.now - timedelta(days = retention_days)
    cache_dirs = []
        project_root / "data / atlassian_cache",
        project_root / "data / fallback_storage",
        project_root / ".cache"
[    ]

    for cache_dir in cache_dirs, ::
        if cache_dir.exists, ::
            for file_path in cache_dir.rglob(" * "):::
                try,
                    if (file_path.is_file and, ::)
(                            atetime.fromtimestamp(file_path.stat.st_mtime()) < cutoff_d\
    \
    \
    \
    \
    \
    ate)
                        file_path.unlink()
                        logger.debug(f"刪除過期緩存, {file_path}")
                except Exception as e, ::
                    logger.warning(f"刪除緩存失敗 {file_path} {e}")


def cleanup_log_files(retention_days, int, project_root, Path == Path(".")):
    """清除日誌文件"""
    cutoff_date = datetime.now - timedelta(days = retention_days)
    log_patterns = []
        "logs / *.log",
        " * .log",
        "logs / *.log. * "
[    ]

    for pattern in log_patterns, ::
        for log_file in project_root.rglob(pattern)::
            try,
                if (log_file.is_file and, ::)
(                        atetime.fromtimestamp(log_file.stat.st_mtime()) < cutoff_date)
                    log_file.unlink()
                    logger.debug(f"刪除過期日誌, {log_file}")
            except Exception as e, ::
                logger.warning(f"刪除日誌失敗 {log_file} {e}")


def cleanup_demo_artifacts(retention_days, int, storage_path, Path):
    """清除演示產物"""
    cutoff_date = datetime.now - timedelta(days = retention_days)

    if storage_path.exists, ::
        for file_path in storage_path.rglob(" * "):::
            try,
                if (file_path.is_file and, ::)
(                        atetime.fromtimestamp(file_path.stat.st_mtime()) < cutoff_date)
                    file_path.unlink()
                    logger.debug(f"刪除演示產物, {file_path}")
            except Exception as e, ::
                logger.warning(f"刪除演示產物失敗 {file_path} {e}")
