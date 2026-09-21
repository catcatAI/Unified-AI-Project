# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MSBACheckpointer — persistence for MSBA state.

Saves/loads:
  - BlockSNN weights (sparse COO format)
  - Cross-attention matrix (.npy)
  - Block history (JSON)
"""

import json
import logging
import os
from typing import Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MSBACheckpointer:
    """Unified checkpoint management for MSBA."""

    def __init__(self, base_dir: str = "data/checkpoints/msba"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(
        self,
        blocks: Dict[str, object],
        cross_attention: np.ndarray,
        history: Dict[str, object],
    ) -> None:
        """
        Save all MSBA state to disk.

        Args:
            blocks: Dict of block_id -> SemanticBlock.
            cross_attention: 9x9 numpy array.
            history: Block selection history dict.
        """
        # BlockSNN weights
        for bid, block in blocks.items():
            coordinator = getattr(block, "coordinator", None)
            if coordinator is None or coordinator.engine is None:
                continue
            engine = coordinator.engine
            path = os.path.join(self.base_dir, f"{bid}_snn.npz")
            try:
                if hasattr(engine, "W"):
                    np.savez_compressed(path, W=engine.W)
                elif hasattr(engine, "save_checkpoint"):
                    engine.save_checkpoint(path)
            except Exception as e:
                logger.debug("Failed to save %s: %s", bid, e)

        # Cross-attention matrix
        ca_path = os.path.join(self.base_dir, "cross_attention.npy")
        try:
            np.save(ca_path, cross_attention)
        except Exception as e:
            logger.debug("Failed to save cross_attention: %s", e)

        # Block history
        hist_path = os.path.join(self.base_dir, "history.json")
        try:
            with open(hist_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Failed to save history: %s", e)

        logger.info("MSBA checkpoint saved to %s", self.base_dir)

    def load(self, blocks: Dict[str, object]) -> Optional[np.ndarray]:
        """
        Load MSBA state from disk.

        Returns:
            Cross-attention matrix if loaded, None otherwise.
        """
        # BlockSNN weights
        for bid, block in blocks.items():
            coordinator = getattr(block, "coordinator", None)
            if coordinator is None or coordinator.engine is None:
                continue
            engine = coordinator.engine
            path = os.path.join(self.base_dir, f"{bid}_snn.npz")
            if not os.path.exists(path):
                continue
            try:
                if hasattr(engine, "W"):
                    data = np.load(path)
                    engine.W = data["W"]
                elif hasattr(engine, "load_checkpoint"):
                    engine.load_checkpoint(path)
                logger.info("Loaded SNN weights for %s", bid)
            except Exception as e:
                logger.debug("Failed to load %s: %s", bid, e)

        # Cross-attention matrix
        ca_path = os.path.join(self.base_dir, "cross_attention.npy")
        cross_attention = None
        if os.path.exists(ca_path):
            try:
                cross_attention = np.load(ca_path)
                logger.info("Loaded cross_attention matrix")
            except Exception as e:
                logger.debug("Failed to load cross_attention: %s", e)

        # Block history
        hist_path = os.path.join(self.base_dir, "history.json")
        history = {}
        if os.path.exists(hist_path):
            try:
                with open(hist_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
                logger.info("Loaded block history")
            except Exception as e:
                logger.debug("Failed to load history: %s", e)

        return cross_attention
