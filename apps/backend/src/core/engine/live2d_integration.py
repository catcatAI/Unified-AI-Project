"""
Angela AI v6.0 - Live2D Integration
Live2D集成系统

Manages Live2D model control, expression parameters, motion control,
and lip-sync for Angela AI's visual representation.

Features:
- Live2D model loading and control
- Facial expression parameter management
- Motion and animation control
- Lip synchronization with speech
- Parameter interpolation

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

# Backward compatibility aliases (2026-06-07)
# Real implementation is Live2DAvatarGenerator in live2d_avatar_generator.py
try:
    from .live2d_avatar_generator import (
        Live2DAvatarGenerator as Live2DIntegration,
        Live2DAvatarGenerator as Live2DExpression,
        Live2DAvatarGenerator as Live2DAction,
    )
except ImportError:
    Live2DIntegration = None
    Live2DExpression = None
    Live2DAction = None
