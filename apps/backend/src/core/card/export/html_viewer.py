"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
HTML viewer — generates an interactive HTML page for card browsing.
"""

import logging
from datetime import datetime
from pathlib import Path

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class HTMLViewer:
    """
    Generates an interactive HTML page for browsing Card data.
    """

    def render(self, card: Card) -> str:
        """Render a card as an interactive HTML page."""
        lines = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'>",
            "<style>body{font-family:sans-serif;max-width:800px;margin:auto;padding:2em}"
            "h1{color:#333}.token{display:inline-block;background:#eef;padding:2px 8px;margin:2px;border-radius:4px}"
            "table{width:100%;border-collapse:collapse}td,th{border:1px solid #ddd;padding:8px;text-align:left}"
            "</style>",
            f"<title>{card.name or card.card_id}</title>",
            "</head><body>",
            f"<h1>{card.name or card.card_id}</h1>",
            "<table>",
            f"<tr><th>ID</th><td>{card.qualified_id or card.card_id}</td></tr>",
            f"<tr><th>World Line</th><td>{card.world_line}</td></tr>",
            f"<tr><th>Core Trait</th><td>{card.core_trait}</td></tr>",
            f"<tr><th>Type</th><td>{card.card_type.name if card.card_type else ''}</td></tr>",
            "</table>",
        ]
        if card.tokens:
            lines.append("<h2>Tokens</h2><p>")
            for t in card.tokens:
                lines.append(f"<span class='token'>{t.name} ({t.strength})</span> ")
            lines.append("</p>")
        if card.source_files:
            lines.append("<h2>Sources</h2><ul>")
            for sf in card.source_files:
                lines.append(f"<li>{sf.path} ({sf.last_write_time.date()})</li>")
            lines.append("</ul>")
        lines.append(f"<p><em>Generated: {datetime.now().isoformat()}</em></p>")
        lines.append("</body></html>")
        return "\n".join(lines)

    def render_to_file(self, card: Card, path: str) -> bool:
        """Write rendered HTML to a file."""
        try:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(self.render(card), encoding="utf-8")
            logger.info(f"Rendered HTML viewer for {card.qualified_id} to {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to render HTML viewer: {e}", exc_info=True)
            return False


__all__ = ["HTMLViewer"]
