"""
ANGELA-MATRIX: [L5] [β] [B] [L0]
Comic composer — generates comic/manga panels from Card visual_data.
Delegates to AngelaRealPainter / ComfyUI for image generation.
"""

import logging
from typing import Any, Dict, List, Optional

from core.card.card_types import Card, Visual

logger = logging.getLogger(__name__)

DEFAULT_STYLE = "anime"
DEFAULT_SIZE = (512, 512)


class ComicComposer:
    """
    Composes manga/comic panels from card visual_data.
    Delegates image generation to AngelaRealPainter.
    """

    def __init__(self, painter: Optional[Any] = None):
        self._painter = painter

    @property
    def painter(self):
        if self._painter is None:
            raise RuntimeError("AngelaRealPainter not set")
        return self._painter

    @painter.setter
    def painter(self, value: Any) -> None:
        self._painter = value

    async def compose_portrait(self, card: Card) -> Optional[Any]:
        """Execute the compose portrait operation."""
        prompt = self._build_prompt(card)
        style = self._pick_style(card)
        return await self.painter.paint_portrait(
            description=prompt, style=style, size=DEFAULT_SIZE
        )

    def _build_prompt(self, card: Card) -> str:
        """Build prompt."""
        parts: List[str] = []
        if card.visual_data and card.visual_data.prompt:
            parts.append(card.visual_data.prompt)
        if card.name:
            parts.append(f"character: {card.name}")
        if card.core_trait:
            parts.append(f"personality: {card.core_trait}")
        if card.tokens:
            traits = ", ".join(t.name for t in card.tokens[:3])
            parts.append(f"traits: {traits}")
        return ", ".join(parts) if parts else card.name

    def _pick_style(self, card: Card) -> str:
        """Pick style."""
        if card.visual_data and card.visual_data.style:
            return card.visual_data.style
        return DEFAULT_STYLE


__all__ = ["ComicComposer"]
