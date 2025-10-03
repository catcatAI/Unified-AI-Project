#!/usr/bin/env python3
"""
項目清理腳本
清理重複文件、臨時文件和優化項目結構
"""

from pathlib import Path
import logging
from src.shared.utils.cleanup_utils import cleanup_temp_files, cleanup_cache_data, cleanup_log_files

logging.basicConfig(level=logging.INFO)
logger: Any = logging.getLogger(__name__)

def cleanup_project():
    """清理項目"""
    project_root: str = Path(".")
    
    _ = logger.info("開始清理項目...")

    # 使用通用的臨時文件清理
    _ = cleanup_temp_files(project_root)

    # 使用通用的緩存數據清理 (例如，保留1天)
    cleanup_cache_data(retention_days=1, project_root=project_root)

    # 使用通用的日誌文件清理 (例如，保留7天)
    cleanup_log_files(retention_days=7, project_root=project_root)
    
    # 清理重複的測試文件 (這部分保持不變，因為它是特定於項目的)
    duplicate_tests = [
        "tests/hsp/temp_test_gmqtt_mock.py",
        "test_hsp_connector.py"  # 根目錄的重複文件
    ]
    
    for test_file in duplicate_tests:
        file_path = project_root / test_file
        if file_path.exists():
            _ = logger.info(f"刪除重複測試: {file_path}")
            _ = file_path.unlink()
    
    _ = logger.info("項目清理完成")

if __name__ == "__main__":
    _ = cleanup_project()