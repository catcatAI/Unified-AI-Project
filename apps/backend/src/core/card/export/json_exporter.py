"""
ANGELA-MATRIX: [L3] [β] [B] [L0]
JSON exporter — serializes Card objects to JSON and optionally packages
with portrait images as a ZIP archive.
"""

import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.card.card_types import Card

logger = logging.getLogger(__name__)


class JSONExporter:
    """
    Exports Card objects as JSON, with optional ZIP packaging.
    """

    def export_json(self, card: Card, indent: int = 2) -> str:
        """Execute the export json operation."""
        data = self._card_to_export_dict(card)
        return json.dumps(data, ensure_ascii=False, indent=indent, default=str)

    def export_to_file(self, card: Card, path: str, indent: int = 2) -> bool:
        """Log a diagnostic message."""
        try:
            dest = Path(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            content = self.export_json(card, indent=indent)
            dest.write_text(content, encoding="utf-8")
            logger.info(f"Exported {card.qualified_id} to {path}")
            return True
        except OSError as e:
            logger.error(f"Failed to export {card.qualified_id}: {e}", exc_info=True)
            return False

    def export_zip(
        self, cards: List[Card], zip_path: str,
        image_paths: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Log a diagnostic message."""
        try:
            dest = Path(zip_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
                for card in cards:
                    filename = f"{card.qualified_id or card.card_id}.json"
                    content = self.export_json(card)
                    zf.writestr(filename, content)
                if image_paths:
                    for qid, img_path in image_paths.items():
                        img = Path(img_path)
                        if img.exists():
                            zf.write(str(img), f"images/{qid}{img.suffix}")
            logger.info(f"Exported {len(cards)} cards to {zip_path}")
            return True
        except (OSError, zipfile.BadZipFile) as e:
            logger.error(f"ZIP export failed: {e}", exc_info=True)
            return False

    def _card_to_export_dict(self, card: Card) -> Dict[str, Any]:
        return {
            "card_id": card.card_id,
            "world_line": card.world_line,
            "qualified_id": card.qualified_id,
            "alternate_selves": list(card.alternate_selves),
            "card_type": card.card_type.name if card.card_type else None,
            "name": card.name,
            "core_trait": card.core_trait,
            "meta_data": dict(card.meta_data),
            "tokens": [
                {"category": t.category, "name": t.name, "strength": t.strength}
                for t in card.tokens
            ],
            "social_distance": [
                {"target_id": r.target_id, "grid": r.grid, "nature": r.nature}
                for r in card.social_distance
            ],
            "history_events": [
                {"timestamp": e.timestamp.isoformat(), "title": e.title, "description": e.description}
                for e in card.history_events
            ],
            "conflicts": [
                {
                    "type": c.type.name,
                    "dimension": c.dimension,
                    "description": c.description,
                    "resolution": c.resolution,
                    "user_intent": c.user_intent.name,
                    "suppressed": c.suppressed,
                }
                for c in card.conflicts
            ],
            "exported_at": datetime.now().isoformat(),
        }


__all__ = ["JSONExporter"]
