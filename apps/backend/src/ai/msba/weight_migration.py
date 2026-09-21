# -*- coding: utf-8 -*-
# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L3+]
# =============================================================================
"""
WeightMigration — migrate weights from CoreNetwork/TensorSNNCore to MSBA blocks.

Handles:
- Extracting weights from existing engines
- Mapping to MSBA block structure
- Saving migrated weights
"""

import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class WeightMigration:
    """
    Migrates weights from existing SNN engines to MSBA blocks.

    Supports:
    - CoreNetwork -> block-specific weights
    - TensorSNNCore -> block-specific weights
    - Custom engine -> generic extraction
    """

    def __init__(self, output_dir: str = "data/msba/weights"):
        """
        Args:
            output_dir: Directory to save migrated weights.
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def migrate_core_network(
        self,
        engine: Any,
        block_id: str,
        chunk_size: int = 128 * 1024 * 1024,
    ) -> Optional[str]:
        """
        Migrate weights from CoreNetwork to MSBA block.

        Args:
            engine: CoreNetwork instance.
            block_id: Target block identifier.
            chunk_size: Size of each chunk for memmap.

        Returns:
            Path to migrated weights, or None on failure.
        """
        try:
            weights = self._extract_core_network_weights(engine)
            if weights is None:
                return None

            return self._save_as_memmap(weights, block_id, chunk_size)

        except Exception as e:
            logger.error(
                "CoreNetwork migration failed for %s: %s",
                block_id,
                e,
            )
            return None

    def migrate_tensor_snn(
        self,
        engine: Any,
        block_id: str,
        chunk_size: int = 128 * 1024 * 1024,
    ) -> Optional[str]:
        """
        Migrate weights from TensorSNNCore to MSBA block.

        Args:
            engine: TensorSNNCore instance.
            block_id: Target block identifier.
            chunk_size: Size of each chunk for memmap.

        Returns:
            Path to migrated weights, or None on failure.
        """
        try:
            weights = self._extract_tensor_snn_weights(engine)
            if weights is None:
                return None

            return self._save_as_memmap(weights, block_id, chunk_size)

        except Exception as e:
            logger.error(
                "TensorSNNCore migration failed for %s: %s",
                block_id,
                e,
            )
            return None

    def migrate_generic(
        self,
        engine: Any,
        block_id: str,
        weight_keys: Optional[List[str]] = None,
        chunk_size: int = 128 * 1024 * 1024,
    ) -> Optional[str]:
        """
        Generic weight migration from any engine.

        Args:
            engine: Any engine with weight attributes.
            block_id: Target block identifier.
            weight_keys: List of attribute names containing weights.
                         If None, auto-detect.
            chunk_size: Size of each chunk for memmap.

        Returns:
            Path to migrated weights, or None on failure.
        """
        try:
            weights = self._extract_generic_weights(engine, weight_keys)
            if weights is None:
                return None

            return self._save_as_memmap(weights, block_id, chunk_size)

        except Exception as e:
            logger.error(
                "Generic migration failed for %s: %s",
                block_id,
                e,
            )
            return None

    def _extract_core_network_weights(self, engine: Any) -> Optional[np.ndarray]:
        """Extract weights from CoreNetwork."""
        if not hasattr(engine, "W"):
            logger.warning("CoreNetwork has no W attribute")
            return None

        W = engine.W
        if isinstance(W, np.ndarray):
            return W.flatten().astype(np.float32)

        # Try to convert
        try:
            return np.array(W, dtype=np.float32).flatten()
        except Exception:
            logger.warning("Cannot convert CoreNetwork weights")
            return None

    def _extract_tensor_snn_weights(self, engine: Any) -> Optional[np.ndarray]:
        """Extract weights from TensorSNNCore."""
        if not hasattr(engine, "W"):
            logger.warning("TensorSNNCore has no W attribute")
            return None

        W = engine.W
        if isinstance(W, np.ndarray):
            return W.flatten().astype(np.float32)

        try:
            return np.array(W, dtype=np.float32).flatten()
        except Exception:
            logger.warning("Cannot convert TensorSNNCore weights")
            return None

    def _extract_generic_weights(
        self,
        engine: Any,
        weight_keys: Optional[List[str]] = None,
    ) -> Optional[np.ndarray]:
        """Extract weights from any engine."""
        if weight_keys is None:
            # Auto-detect common weight attribute names
            weight_keys = [
                "W",
                "weights",
                "weight_matrix",
                "kernel",
                "params",
                "state_dict",
            ]

        for key in weight_keys:
            if hasattr(engine, key):
                value = getattr(engine, key)
                if isinstance(value, np.ndarray):
                    return value.flatten().astype(np.float32)
                try:
                    return np.array(value, dtype=np.float32).flatten()
                except Exception:
                    continue

        logger.warning("No weights found in engine")
        return None

    def _save_as_memmap(
        self,
        weights: np.ndarray,
        block_id: str,
        chunk_size: int,
    ) -> str:
        """Save weights as memory-mapped file."""
        path = os.path.join(self.output_dir, f"{block_id}.mmap")

        # Save as memmap
        mmap = np.memmap(
            path,
            dtype="float32",
            mode="w+",
            shape=weights.shape,
        )
        mmap[:] = weights[:]
        mmap.flush()

        logger.info(
            "Saved %s weights to %s (%d bytes)",
            block_id,
            path,
            weights.nbytes,
        )
        return path

    def list_migrated(self) -> List[str]:
        """List all migrated weight files."""
        if not os.path.exists(self.output_dir):
            return []

        return [f for f in os.listdir(self.output_dir) if f.endswith(".mmap")]

    def get_migration_info(self) -> Dict[str, Any]:
        """Get information about migrated weights."""
        files = self.list_migrated()
        info = {
            "total_blocks": len(files),
            "blocks": {},
        }

        for f in files:
            path = os.path.join(self.output_dir, f)
            try:
                size = os.path.getsize(path)
                info["blocks"][f[:-5]] = {  # Remove .mmap
                    "path": path,
                    "size_bytes": size,
                    "size_mb": size / (1024 * 1024),
                }
            except OSError:
                continue

        return info
