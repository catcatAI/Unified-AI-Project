"""
Autonomous Desktop Interaction Submodule (Backward Compat)
Re-exports from core.autonomous shim
"""
from __future__ import annotations

from core.engine.desktop_interaction import (
    DesktopInteraction,
    FileOperation,
    DesktopState,
    FileOperationType,
    FileCategory,
    FileWatcherConfig,
    DesktopBrowserIntegration,
)