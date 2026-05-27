"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
PDF exporter — generates a print-ready HTML layout for PDF conversion.
"""

import logging
from pathlib import Path
from typing import List, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)

PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{title}</title>
<style>
  @page {{ size: A4; margin: 2cm; }}
  body {{ font-family: serif; color: #222; }}
  .card {{ page-break-after: always; }}
  .card:last-child {{ page-break-after: avoid; }}
  h1 {{ font-size: 18pt; border-bottom: 1px solid #333; padding-bottom: 4pt; }}
  h2 {{ font-size: 14pt; margin-top: 1em; }}
  .field {{ margin: 2pt 0; font-size: 11pt; }}
  .label {{ font-weight: bold; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 10pt; }}
  td, th {{ border: 1px solid #999; padding: 4pt; text-align: left; }}
  .token {{ display: inline-block; margin: 2pt; }}
</style>
</head>
<body>
{cards_html}
</body>
</html>"""


class PDFExporter:
    """
    Generates a print-ready HTML layout suitable for PDF conversion
    (print-to-PDF from browser or wkhtmltopdf).
    """

    def render_html(self, cards: List[Card], title: str = "Card Export") -> str:
        cards_html = "\n".join(self._render_card(c) for c in cards)
        return PDF_HTML_TEMPLATE.format(title=title, cards_html=cards_html)

    def render_to_file(self, cards: List[Card], path: str, title: str = "Card Export") -> bool:
        try:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            html = self.render_html(cards, title=title)
            dest.write_text(html, encoding="utf-8")
            logger.info(f"Exported {len(cards)} cards to {path}")
            return True
        except OSError as e:
            logger.error(f"PDF-HTML export failed: {e}")
            return False

    def _render_card(self, card: Card) -> str:
        lines = [f'<div class="card"><h1>{card.name or "—"}</h1>']
        lines.append(f'<div class="field"><span class="label">ID:</span> {card.card_id}</div>')
        lines.append(f'<div class="field"><span class="label">世界線:</span> {card.world_line}</div>')
        lines.append(f'<div class="field"><span class="label">類型:</span> {card.card_type.name if card.card_type else "—"}</div>')
        lines.append(f'<div class="field"><span class="label">核心特質:</span> {card.core_trait or "—"}</div>')

        if card.tokens:
            lines.append('<h2>Token</h2><table><tr><th>特質</th><th>強度</th></tr>')
            for t in card.tokens:
                lines.append(f"<tr><td>{t.name}</td><td>{t.strength}</td></tr>")
            lines.append("</table>")

        if card.history_events:
            lines.append("<h2>事件</h2><table><tr><th>時間</th><th>標題</th><th>描述</th></tr>")
            for e in card.history_events:
                lines.append(f"<tr><td>{e.timestamp.strftime('%Y-%m-%d')}</td><td>{e.title}</td><td>{e.description}</td></tr>")
            lines.append("</table>")

        lines.append("</div>")
        return "\n".join(lines)


__all__ = ["PDFExporter"]
