# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
MSBACheckpointer — persistence for MSBA state with auto-save.

Saves/loads:
  - BlockSNN weights (sparse COO format)
  - Cross-attention matrix (.npy)
  - Block history (JSON)
  - Online training state (replay buffer, LR, co-occurrence)
  - A/B testing state
  - Metrics snapshot

Features:
  - Auto-save on configurable interval
  - Session resume from latest checkpoint
  - Versioned checkpoints (keep last N)
"""

import json
import logging
import os
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

import numpy as np

if TYPE_CHECKING:
    from .semantic_block import SemanticBlock

logger = logging.getLogger(__name__)


class MSBACheckpointer:
    """Unified checkpoint management for MSBA."""

    def __init__(
        self,
        base_dir: str = "data/checkpoints/msba",
        auto_save_interval: float = 300.0,
        max_versions: int = 5,
    ):
        """
        Args:
            base_dir: Base directory for checkpoints.
            auto_save_interval: Seconds between auto-saves (0=disabled).
            max_versions: Maximum checkpoint versions to keep.
        """
        self.base_dir = base_dir
        self.auto_save_interval = auto_save_interval
        self.max_versions = max_versions
        self._last_save_time = 0.0
        self._version = 0

        os.makedirs(base_dir, exist_ok=True)

    def save(
        self,
        blocks: Dict[str, "SemanticBlock"],
        cross_attention: np.ndarray,
        history: Dict[str, Any],
        training_state: Optional[Dict[str, Any]] = None,
        ab_state: Optional[Dict[str, Any]] = None,
        metrics_snapshot: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Save all MSBA state to disk.

        Returns:
            Checkpoint directory path.
        """
        self._version += 1
        ckpt_dir = os.path.join(self.base_dir, f"v{self._version:04d}")
        os.makedirs(ckpt_dir, exist_ok=True)

        # BlockSNN weights
        for bid, block in blocks.items():
            coordinator = getattr(block, "coordinator", None)
            if coordinator is None or coordinator.engine is None:
                continue
            engine = coordinator.engine
            path = os.path.join(ckpt_dir, f"{bid}_snn.npz")
            try:
                if hasattr(engine, "W"):
                    np.savez_compressed(path, W=engine.W)
                elif hasattr(engine, "save_checkpoint"):
                    engine.save_checkpoint(path)
            except Exception as e:
                logger.debug("Failed to save %s: %s", bid, e)

        # Cross-attention matrix
        ca_path = os.path.join(ckpt_dir, "cross_attention.npy")
        try:
            np.save(ca_path, cross_attention)
        except Exception as e:
            logger.debug("Failed to save cross_attention: %s", e)

        # Block history
        hist_path = os.path.join(ckpt_dir, "history.json")
        try:
            with open(hist_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug("Failed to save history: %s", e)

        # Training state
        if training_state:
            train_path = os.path.join(ckpt_dir, "training.json")
            try:
                with open(train_path, "w", encoding="utf-8") as f:
                    json.dump(training_state, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.debug("Failed to save training state: %s", e)

        # A/B testing state
        if ab_state:
            ab_path = os.path.join(ckpt_dir, "ab_testing.json")
            try:
                with open(ab_path, "w", encoding="utf-8") as f:
                    json.dump(ab_state, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.debug("Failed to save A/B state: %s", e)

        # Metrics snapshot
        if metrics_snapshot:
            metrics_path = os.path.join(ckpt_dir, "metrics.json")
            try:
                with open(metrics_path, "w", encoding="utf-8") as f:
                    json.dump(metrics_snapshot, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.debug("Failed to save metrics: %s", e)

        # Write version metadata
        meta_path = os.path.join(ckpt_dir, "meta.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "version": self._version,
                        "timestamp": time.time(),
                        "blocks": list(blocks.keys()),
                    },
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            logger.debug("Failed to save meta: %s", e)

        # Cleanup old versions
        self._cleanup_old_versions()

        # Update latest symlink
        self._update_latest_symlink(ckpt_dir)

        logger.info("MSBA checkpoint saved to %s", ckpt_dir)
        return ckpt_dir

    def load(
        self,
        blocks: Dict[str, "SemanticBlock"],
        version: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Load MSBA state from disk.

        Args:
            blocks: Dict of block_id -> SemanticBlock.
            version: Specific version to load (None=latest).

        Returns:
            Dict with cross_attention, history, training_state, etc.
        """
        # Find checkpoint directory
        if version is not None:
            ckpt_dir: Optional[str] = os.path.join(self.base_dir, f"v{version:04d}")
        else:
            ckpt_dir = self._find_latest_checkpoint()

        if ckpt_dir is None or not os.path.exists(ckpt_dir):
            logger.info("No checkpoint found, using defaults")
            return {}

        result: Dict[str, Any] = {}

        # BlockSNN weights
        for bid, block in blocks.items():
            coordinator = getattr(block, "coordinator", None)
            if coordinator is None or coordinator.engine is None:
                continue
            engine = coordinator.engine
            path = os.path.join(ckpt_dir, f"{bid}_snn.npz")
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
        ca_path = os.path.join(ckpt_dir, "cross_attention.npy")
        if os.path.exists(ca_path):
            try:
                result["cross_attention"] = np.load(ca_path)
                logger.info("Loaded cross_attention matrix")
            except Exception as e:
                logger.debug("Failed to load cross_attention: %s", e)

        # Block history
        hist_path = os.path.join(ckpt_dir, "history.json")
        if os.path.exists(hist_path):
            try:
                with open(hist_path, "r", encoding="utf-8") as f:
                    result["history"] = json.load(f)
                logger.info("Loaded block history")
            except Exception as e:
                logger.debug("Failed to load history: %s", e)

        # Training state
        train_path = os.path.join(ckpt_dir, "training.json")
        if os.path.exists(train_path):
            try:
                with open(train_path, "r", encoding="utf-8") as f:
                    result["training_state"] = json.load(f)
                logger.info("Loaded training state")
            except Exception as e:
                logger.debug("Failed to load training state: %s", e)

        # A/B testing state
        ab_path = os.path.join(ckpt_dir, "ab_testing.json")
        if os.path.exists(ab_path):
            try:
                with open(ab_path, "r", encoding="utf-8") as f:
                    result["ab_state"] = json.load(f)
                logger.info("Loaded A/B testing state")
            except Exception as e:
                logger.debug("Failed to load A/B state: %s", e)

        # Metrics snapshot
        metrics_path = os.path.join(ckpt_dir, "metrics.json")
        if os.path.exists(metrics_path):
            try:
                with open(metrics_path, "r", encoding="utf-8") as f:
                    result["metrics_snapshot"] = json.load(f)
                logger.info("Loaded metrics snapshot")
            except Exception as e:
                logger.debug("Failed to load metrics: %s", e)

        # Read version metadata
        meta_path = os.path.join(ckpt_dir, "meta.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    result["meta"] = json.load(f)
            except Exception as e:
                logger.debug("Failed to load meta: %s", e)

        return result

    def check_auto_save(self) -> bool:
        """Check if auto-save should trigger. Returns True if save needed."""
        if self.auto_save_interval <= 0:
            return False
        return time.monotonic() - self._last_save_time >= self.auto_save_interval

    def mark_saved(self) -> None:
        """Mark that auto-save was performed."""
        self._last_save_time = time.monotonic()

    def get_version_list(self) -> list:
        """List all checkpoint versions."""
        versions: list = []
        if not os.path.exists(self.base_dir):
            return versions

        for entry in os.listdir(self.base_dir):
            if entry.startswith("v") and entry[1:].isdigit():
                v = int(entry[1:])
                meta_path = os.path.join(self.base_dir, entry, "meta.json")
                meta = {}
                if os.path.exists(meta_path):
                    try:
                        with open(meta_path, "r") as f:
                            meta = json.load(f)
                    except Exception:
                        pass
                versions.append(
                    {
                        "version": v,
                        "timestamp": meta.get("timestamp", 0),
                        "blocks": meta.get("blocks", []),
                    }
                )

        return sorted(versions, key=lambda x: x["version"])

    def _find_latest_checkpoint(self) -> Optional[str]:
        """Find the latest checkpoint directory."""
        if not os.path.exists(self.base_dir):
            return None

        latest_version = 0
        for entry in os.listdir(self.base_dir):
            if entry.startswith("v") and entry[1:].isdigit():
                v = int(entry[1:])
                if v > latest_version:
                    latest_version = v

        if latest_version == 0:
            return None

        return os.path.join(self.base_dir, f"v{latest_version:04d}")

    def _cleanup_old_versions(self) -> None:
        """Remove old checkpoint versions beyond max_versions."""
        if self.max_versions <= 0:
            return

        versions = self.get_version_list()
        if len(versions) <= self.max_versions:
            return

        to_remove = versions[: len(versions) - self.max_versions]
        for v_info in to_remove:
            v_dir = os.path.join(self.base_dir, f"v{v_info['version']:04d}")
            try:
                import shutil

                shutil.rmtree(v_dir)
                logger.debug("Removed old checkpoint v%s", v_info["version"])
            except Exception as e:
                logger.debug("Failed to remove old checkpoint: %s", e)

    def _update_latest_symlink(self, ckpt_dir: str) -> None:
        """Update 'latest' symlink to point to newest checkpoint."""
        latest_path = os.path.join(self.base_dir, "latest")
        try:
            if os.path.islink(latest_path) or os.path.exists(latest_path):
                os.remove(latest_path)
            os.symlink(os.path.basename(ckpt_dir), latest_path)
        except Exception as e:
            logger.debug("Failed to update latest symlink: %s", e)
