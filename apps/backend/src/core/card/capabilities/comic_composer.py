"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Comic composer — generates comic/manga panels from Card visual_data.
Delegates to AngelaRealPainter / ComfyUI for image generation.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ComicComposer:
    """Generates comic/manga panels from card visual data."""

    def __init__(self, painter: Any = None):
        self.painter = painter

    def compose(self, card: Any, style: str = "manga", panels: int = 4) -> Dict[str, Any]:
        scene = self._scene_breakdown(card, panels)
        rendered = self._render_panels(scene, style)
        return {
            "style": style,
            "panels": rendered,
            "metadata": {"card_id": getattr(card, "card_id", ""), "total_panels": len(rendered)},
        }

    def _scene_breakdown(self, card: Any, panels: int) -> List[Dict[str, Any]]:
        tokens = getattr(card, "tokens", [])
        if not tokens:
            return [{"description": getattr(card, "name", "unknown"), "panel": i} for i in range(panels)]
        scenes = []
        for i in range(min(panels, len(tokens))):
            t = tokens[i]
            scenes.append({"name": t.name, "description": t.description if hasattr(t, "description") else t.name, "panel": i})
        while len(scenes) < panels:
            scenes.append({"name": f"panel_{len(scenes)}", "description": "", "panel": len(scenes)})
        return scenes

    def _render_panels(self, scenes: List[Dict[str, Any]], style: str) -> List[Dict[str, Any]]:
        panels = []
        for scene in scenes:
            panel = {
                "panel": scene["panel"],
                "description": scene.get("description", ""),
                "style": style,
                "image_url": f"comic://generated/{scene['panel']}",
            }
            panels.append(panel)
        return panels


__all__ = ["ComicComposer"]
