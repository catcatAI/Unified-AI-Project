# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
BlockHistoryPersistence — JSON-based block history storage.

Saves/loads block selection history for cross-session learning.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional

from .types import BlockHistory

logger = logging.getLogger(__name__)


class BlockHistoryPersistence:
    """
    Manages block history persistence across sessions.

    Stores confirm/question/supplement/neutral counts per block,
    plus timestamped selection records for trend analysis.
    """

    def __init__(self, base_dir: str = "data/msba/history"):
        """
        Args:
            base_dir: Directory to store history files.
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(
        self,
        block_history: Dict[str, BlockHistory],
        selection_log: Optional[List[dict]] = None,
    ) -> str:
        """
        Save block history to disk.

        Args:
            block_history: Dict mapping block_id -> BlockHistory.
            selection_log: Optional list of selection records.

        Returns:
            Path to saved file.
        """
        data = {
            "timestamp": time.time(),
            "blocks": {},
            "selection_log": selection_log or [],
        }

        for bid, hist in block_history.items():
            data["blocks"][bid] = hist.to_dict()

        path = os.path.join(self.base_dir, "block_history.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(
                "Block history saved: %d blocks, %d selections",
                len(block_history),
                len(selection_log or []),
            )
            return path
        except Exception as e:
            logger.error("Failed to save block history: %s", e)
            return ""

    def load(self) -> Dict[str, BlockHistory]:
        """
        Load block history from disk.

        Returns:
            Dict mapping block_id -> BlockHistory.
        """
        path = os.path.join(self.base_dir, "block_history.json")
        if not os.path.exists(path):
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            block_history = {}
            for bid, hist_data in data.get("blocks", {}).items():
                hist = BlockHistory()
                hist.total = hist_data.get("total", 0)
                hist.confirm_count = hist_data.get("confirm", 0)
                hist.question_count = hist_data.get("question", 0)
                hist.supplement_count = hist_data.get("supplement", 0)
                hist.neutral_count = hist_data.get("neutral", 0)
                block_history[bid] = hist

            logger.info(
                "Block history loaded: %d blocks from %s",
                len(block_history),
                path,
            )
            return block_history

        except Exception as e:
            logger.error("Failed to load block history: %s", e)
            return {}

    def load_selection_log(self) -> List[dict]:
        """Load selection log from disk."""
        path = os.path.join(self.base_dir, "block_history.json")
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("selection_log", [])
        except Exception:
            return []

    def append_selection(
        self,
        input_text: str,
        selected_blocks: List[str],
        verdicts: Dict[str, str],
    ) -> None:
        """
        Append a selection record to the log.

        Args:
            input_text: User input.
            selected_blocks: List of selected block IDs.
            verdicts: Dict mapping block_id -> verdict.
        """
        path = os.path.join(self.base_dir, "block_history.json")

        # Load existing data
        data = {"blocks": {}, "selection_log": []}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        # Append new record
        record = {
            "timestamp": time.time(),
            "input": input_text[:100],  # Truncate for storage
            "blocks": selected_blocks,
            "verdicts": verdicts,
        }

        if "selection_log" not in data:
            data["selection_log"] = []

        data["selection_log"].append(record)

        # Keep only last 1000 records
        if len(data["selection_log"]) > 1000:
            data["selection_log"] = data["selection_log"][-1000:]

        # Save
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Failed to append selection: %s", e)
