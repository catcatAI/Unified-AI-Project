"""
Angela AI 7.5.0-dev - Sync Module
同步模块

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

import logging

logger = logging.getLogger(__name__)

from .cloud_sync import (  # noqa: E402
    CloudSyncConfig,
    CloudSyncManager,
    ConflictResolution,
    SyncConflict,
    SyncItem,
    SyncProgress,
    SyncQueue,
    SyncStatus,
)

__version__ = "7.5.0-dev"
__author__ = "Angela AI Development Team"

__all__ = [
    "CloudSyncManager",
    "CloudSyncConfig",
    "SyncItem",
    "SyncConflict",
    "SyncProgress",
    "SyncStatus",
    "ConflictResolution",
    "SyncQueue",
]
