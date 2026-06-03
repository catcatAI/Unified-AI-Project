"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
HTML viewer — generates an interactive HTML page for card browsing.
"""

import logging
from pathlib import Path
from typing import List, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  body {{ font-family: sans-serif; max-width: 800px; margin: 2em auto; padding: 0 1em; }}
  .card {{ border: 1px solid #ccc; border-radius: 8px; padding: 1.5em; margin: 1em 0; }}
  .card h2 {{ margin-top: 0; color: #333; }}
  .field {{ margin: 0.3em 0; }}
  .label {{ font-weight: bold; color: #666; }}
  .tokens {{ display: flex; gap: 0.5em; flex-wrap: wrap; }}
  .token {{ background: #e3f2fd; padding: 0.2em 0.6em; border-radius: 12px; font-size: 0.9em; }}
  .conflict {{ background: #fff3e0; padding: 0.5em; border-radius: 4px; margin: 0.3em 0; }}
</style>
</head>
<body>
<h1>{heading}</h1>
{cards_html}
</body>
</html>"""

CARD_TEMPLATE = """<div class="card">
  <h2>{name}</h2>
  <div class="field"><span class="label">ID:</span> {card_id}</div>
  <div class="field"><span class="label">世界線:</span> {world_line}</div>
  <div class="field"><span class="label">類型:</span> {card_type}</div>
  <div class="field"><span class="label">核心特質:</span> {core_trait}</div>
  <div class="field"><span class="label">同位體:</span> {alternate_selves}</div>
  {tokens_html}
  {events_html}
  {conflicts_html}
</div>"""


class HTMLViewer:
    """
    Generates an interactive HTML page for browsing cards.
    """

    def render(self, cards: List[Card], title: str = "Card Viewer") -> str:
        """Render the content for output."""
        cards_html = "\n".join(self._render_card(c) for c in cards)
        return HTML_TEMPLATE.format(
            title=title,
            heading=title,
            cards_html=cards_html,
        )

    def render_to_file(self, cards: List[Card], path: str, title: str = "Card Viewer") -> bool:
        """Log a diagnostic message."""
        try:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            html = self.render(cards, title=title)
            dest.write_text(html, encoding="utf-8")
            logger.info(f"Exported {len(cards)} cards to {path}")
            return True
        except OSError as e:
            logger.error(f"HTML export failed: {e}", exc_info=True)
            return False

    def _render_card(self, card: Card) -> str:
        """Render card."""
        tokens_html = ""
        if card.tokens:
            token_spans = "".join(
                f'<span class="token">{t.name} ({t.strength})</span>'
                for t in card.tokens
            )
            tokens_html = f'<div class="field"><span class="label">Tokens:</span><div class="tokens">{token_spans}</div></div>'

        events_html = ""
        if card.history_events:
            items = "".join(
                f"<li>{e.timestamp.strftime('%Y-%m-%d')} — {e.title}: {e.description}</li>"
                for e in card.history_events
            )
            events_html = f'<div class="field"><span class="label">事件:</span><ul>{items}</ul></div>'

        conflicts_html = ""
        if card.conflicts:
            def _render_conflict(c) -> str:
                """Render conflict."""
                parts = [f'<div class="conflict">{c.type.name}: {c.description}']
                if c.resolution:
                    parts.append(f" → {c.resolution}")
                if c.suppressed:
                    parts.append(" ✅保留")
                parts.append("</div>")
                return "".join(parts)
            blocks = "".join(_render_conflict(c) for c in card.conflicts)
            conflicts_html = f'<div class="field"><span class="label">衝突:</span>{blocks}</div>'

        return CARD_TEMPLATE.format(
            name=card.name or "—",
            card_id=card.card_id or "—",
            world_line=card.world_line or "—",
            card_type=card.card_type.name if card.card_type else "—",
            core_trait=card.core_trait or "—",
            alternate_selves=", ".join(card.alternate_selves) if card.alternate_selves else "—",
            tokens_html=tokens_html,
            events_html=events_html,
            conflicts_html=conflicts_html,
        )


__all__ = ["HTMLViewer"]
