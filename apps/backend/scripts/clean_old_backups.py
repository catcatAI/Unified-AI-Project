#!/usr/bin/env python3
"""Clean up old backup directories beyond a retention period."""

import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def clean_old_backups(backup_dir: str = "backups", days_to_keep: int = 30) -> None:
    """Remove backup directories older than days_to_keep."""
    backup_path = Path(backup_dir)
    if not backup_path.exists():
        logger.info("Backup directory %s does not exist", backup_dir)
        return

    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    for item in backup_path.iterdir():
        if item.is_dir() and item.name.startswith("auto_fix_"):
            try:
                mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                if mod_time < cutoff_date:
                    logger.info("Removing old backup: %s", item.name)
                    shutil.rmtree(item)
            except Exception as e:
                logger.error("Failed to remove %s: %s", item.name, e)

    logger.info("Old backup cleanup complete")


if __name__ == "__main__":
    clean_old_backups()
