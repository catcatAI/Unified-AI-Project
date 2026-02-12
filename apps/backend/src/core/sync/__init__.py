"""
Angela AI v6.0 - Sync Module
同步模块

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-04
"""

import logging
logger = logging.getLogger(__name__)

from .cloud_sync import (
    CloudSyncManager,
    CloudSyncConfig,
    SyncItem,
    SyncConflict,
    SyncProgress,
    SyncStatus,
    ConflictResolution,
    SyncQueue,
    CloudSyncFactory,
    create_cloud_sync_manager,
)

__version__ = "6.0.0"
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
    "CloudSyncFactory",
    "create_cloud_sync_manager",
]
