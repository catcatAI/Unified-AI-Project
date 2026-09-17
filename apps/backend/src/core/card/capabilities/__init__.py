"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Card Import Pipeline — capabilities subpackage.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.card.capabilities.roleplay_engine import RoleplayEngine
    from core.card.capabilities.scene_interpreter import SceneInterpreter
    from core.card.capabilities.story_writer import StoryWriter
else:
    try:
        from core.card.capabilities.roleplay_engine import RoleplayEngine
    except ImportError:
        RoleplayEngine = None
    try:
        from core.card.capabilities.scene_interpreter import SceneInterpreter
    except ImportError:
        SceneInterpreter = None
    try:
        from core.card.capabilities.story_writer import StoryWriter
    except ImportError:
        StoryWriter = None

__all__ = [
    "RoleplayEngine",
    "SceneInterpreter",
    "StoryWriter",
]
