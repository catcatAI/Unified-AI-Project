"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
PDF exporter — generates a print-ready HTML layout for PDF conversion.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class PDFExporter:
    """
    Generates an HTML layout for PDF conversion from a Card.
    """

    def export_html(self, card: Card) -> str:
        """Generate a print-ready HTML string for the card."""
        lines = [
            "<!DOCTYPE html><html><head><meta charset='utf-8'>",
            f"<title>{card.name or card.card_id}</title>",
            "</head><body>",
            f"<h1>{card.name or card.card_id}</h1>",
            f"<p><strong>ID:</strong> {card.qualified_id or card.card_id}</p>",
            f"<p><strong>World Line:</strong> {card.world_line}</p>",
            f"<p><strong>Core Trait:</strong> {card.core_trait}</p>",
        ]
        if card.tokens:
            lines.append("<h2>Tokens</h2><ul>")
            for t in card.tokens:
                lines.append(f"<li>{t.name} ({t.strength})</li>")
            lines.append("</ul>")
        lines.append(f"<p><em>Generated: {datetime.now().isoformat()}</em></p>")
        lines.append("</body></html>")
        return "\n".join(lines)

    def export_to_file(self, card: Card, path: str) -> bool:
        """Write HTML to a file."""
        try:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(self.export_html(card), encoding="utf-8")
            logger.info(f"Exported PDF HTML for {card.qualified_id} to {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to export PDF HTML: {e}", exc_info=True)
            return False


__all__ = ["PDFExporter"]
