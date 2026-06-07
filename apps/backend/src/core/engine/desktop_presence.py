"""
Angela AI v6.0 - Desktop Presence System
桌面存在系统

Manages Angela's desktop presence including global mouse tracking,
body collision detection, layer management (click-through), and wallpaper mode.

Features:
- Global mouse position tracking
- Body collision detection with desktop elements
- Layer management with click-through support
- Wallpaper mode for ambient presence
- Screen boundary awareness

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

# Backward compatibility alias (2026-06-07)
# Real implementation is DesktopInteraction in desktop_interaction.py
try:
    from .desktop_interaction import DesktopInteraction as DesktopPresence
except ImportError:
    DesktopPresence = None

# MouseTracker alias if needed
try:
    from .desktop_interaction import DesktopInteraction as MouseTracker
except ImportError:
    MouseTracker = None
