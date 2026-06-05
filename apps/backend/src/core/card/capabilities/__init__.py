"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Card Import Pipeline — capabilities subpackage.
"""

try:
    from core.card.capabilities.comic_composer import ComicComposer
except ImportError:
    ComicComposer = None

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
    "ComicComposer",
    "RoleplayEngine",
    "SceneInterpreter",
    "StoryWriter",
]
