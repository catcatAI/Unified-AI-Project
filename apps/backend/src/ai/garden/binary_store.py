# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""
GARDEN BinaryStore — Memory-mapped binary weight matrix for GARDEN-1G.

Provides fast load/save of large SNN weight matrices using numpy memmap.
Designed for matrices up to 100K x 100K+ (800MB+ in float32).

The file format is:
  [header 32 bytes]  magic=0x47415244 ("GARD" in LE) + version int32 + V int32 + pad
  [matrix V x V]     float32 values in row-major order

Usage:
    store = BinaryStore("/path/to/garden_relations.bin")
    store.create(V=100000)           # Allocate new 100K x 100K matrix (40GB mmap!)
    data = store[0, :100]            # Read row slice
    store[5, 10] = 0.75             # Write single cell
    store.flush()                    # Ensure written to disk
    store.close()

    store2 = BinaryStore("/path/to/garden_relations.bin", mode='r')
    V = store2.header["V"]
    row_42 = store2[42, :]
"""

from __future__ import annotations

import json
import logging
import os
import struct
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# File format constants
MAGIC = 0x47415244           # "GARD" in little-endian
VERSION = 1
HEADER_SIZE = 28             # bytes (matches HEADER_FORMAT: 4+4+4+16=28)
HEADER_FORMAT = "<I2I16s"     # magic (4B) + version (4B) + V (4B) + pad (16B)

_torch = None


def _lazy_torch():
    global _torch
    if _torch is None:
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError

            def _import():
                import torch
                return torch

            with ThreadPoolExecutor(max_workers=1) as ex:
                _torch = ex.submit(_import).result(timeout=60)
        except (TimeoutError, ImportError):
            logger.warning("torch import timed out; binary_store torch ops disabled")
            _torch = False
    return _torch if _torch else None


class BinaryStore:
    """
    Memory-mapped binary matrix for GARDEN-1G relation weights.

    Supports reading, writing, slicing, and flushing. The underlying file
    uses numpy.memmap so access is lazy and does not copy the full array
    into memory unless explicitly requested.
    """

    def __init__(self, path: str, mode: str = "r+"):
        """
        Open or create a binary store.

        Args:
            path: Path to the .bin file.
            mode: File mode. 'r' for read-only, 'r+' for read-write,
                  'w+' to overwrite/create, 'c' for copy-on-write.
        """
        self.path = os.path.abspath(path)
        self.mode = mode
        self._mmap: Optional[np.memmap] = None
        self._header: Optional[Dict[str, Any]] = None

        if mode == "w+":
            # Will be created via create()
            pass
        elif os.path.exists(path):
            self._open_existing(mode)
        else:
            raise FileNotFoundError(f"BinaryStore: file not found: {path}")

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    @classmethod
    def create(cls, path: str, V: int, fill_value: float = 0.0) -> "BinaryStore":
        """
        Create a new V x V binary matrix file.

        Args:
            path: Path to write the .bin file.
            V: Matrix dimension (square).
            fill_value: Initial value for all cells.

        Returns:
            BinaryStore instance opened in 'r+' mode.
        """
        path = os.path.abspath(path)
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)

        # Write header
        with open(path, "wb") as f:
            pad = b"\x00" * 16
            header = struct.pack(HEADER_FORMAT, MAGIC, VERSION, V, pad)
            f.write(header)
            # Pre-allocate the full matrix (zeros)
            total = V * V
            f.seek(HEADER_SIZE + (total - 1) * 4)
            f.write(b"\x00")

        # Open as memmap
        store = cls(path, mode="r+")
        # Fill with desired value
        if fill_value != 0.0:
            store._mmap[:] = fill_value  # type: ignore
            store.flush()
        logger.info(
            "BinaryStore: created %s with V=%d (%.2f GB)",
            path,
            V,
            (HEADER_SIZE + V * V * 4) / (1024**3),
        )
        return store

    def _open_existing(self, mode: str) -> None:
        """Open an existing binary store file."""
        mode_to_mmap = {"r": "r", "r+": "r+", "c": "c"}
        mmap_mode = mode_to_mmap.get(mode, "r")

        with open(self.path, "rb") as f:
            raw = f.read(HEADER_SIZE)
            magic, version, V, _ = struct.unpack(HEADER_FORMAT, raw)

        if magic != MAGIC:
            raise ValueError(f"BinaryStore: invalid magic 0x{magic:08X} (expected 0x{MAGIC:08X})")
        if version > VERSION:
            raise ValueError(f"BinaryStore: unsupported version {version} (max {VERSION})")

        self._header = {
            "magic": magic,
            "version": version,
            "V": V,
            "path": self.path,
            "mode": mode,
        }
        self._mmap = np.memmap(
            self.path,
            dtype=np.float32,
            mode=mmap_mode,
            offset=HEADER_SIZE,
            shape=(V, V),
        )
        logger.debug("BinaryStore: opened %s (V=%d, mode=%s)", self.path, V, mode)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def header(self) -> Dict[str, Any]:
        if self._header is None:
            raise RuntimeError("BinaryStore: not initialized")
        return self._header

    @property
    def V(self) -> int:
        return self.header["V"]

    @property
    def data(self) -> Optional[np.memmap]:
        return self._mmap

    def __getitem__(self, key) -> Any:
        if self._mmap is None:
            raise RuntimeError("BinaryStore: mmap not initialized")
        return self._mmap[key]

    def __setitem__(self, key, value) -> None:
        if self._mmap is None:
            raise RuntimeError("BinaryStore: mmap not initialized")
        self._mmap[key] = value

    # ------------------------------------------------------------------
    # I/O helpers
    # ------------------------------------------------------------------

    def flush(self) -> None:
        if self._mmap is not None:
            self._mmap.flush()

    def close(self) -> None:
        if self._mmap is not None:
            self.flush()
            self._mmap._mmap.close()  # type: ignore
            self._mmap = None
            logger.debug("BinaryStore: closed %s", self.path)

    def fill(self, value: float) -> None:
        """Fill entire matrix with a scalar value."""
        if self._mmap is None:
            raise RuntimeError("BinaryStore: mmap not initialized")
        self._mmap[:] = value
        self.flush()

    # ------------------------------------------------------------------
    # Import from torch tensor
    # ------------------------------------------------------------------

    def import_from_torch(self, tensor: "torch.Tensor") -> None:
        """
        Copy values from a square PyTorch tensor into the mmap.

        Note: only the submatrix up to min(tensor.shape[0], V) is copied.
        """
        if self._mmap is None:
            raise RuntimeError("BinaryStore: mmap not initialized")
        torch = _lazy_torch()
        if torch is None:
            raise RuntimeError("BinaryStore: torch unavailable (import timed out)")
        n = min(tensor.shape[0], self.V)
        self._mmap[:n, :n] = tensor[:n, :n].cpu().numpy()
        self.flush()
        logger.info("BinaryStore: imported %dx%d tensor", n, n)

    def export_to_torch(self) -> "torch.Tensor":
        """
        Read the full mmap into a PyTorch tensor (CPU).
        Warning: for V=100K this creates a 40GB tensor.
        """
        if self._mmap is None:
            raise RuntimeError("BinaryStore: mmap not initialized")
        torch = _lazy_torch()
        if torch is None:
            raise RuntimeError("BinaryStore: torch unavailable (import timed out)")
        return torch.from_numpy(np.array(self._mmap))

    # ------------------------------------------------------------------
    # Coherency helpers
    # ------------------------------------------------------------------

    def coherency_check(self) -> Dict[str, Any]:
        """Verify file integrity and report shape/stats."""
        if self._mmap is None:
            return {"status": "not_initialized"}
        V = self.V
        mat = self._mmap
        nonzero = (mat > 0).sum()
        total = V * V
        density = float(nonzero) / total if total > 0 else 0.0
        return {
            "status": "ok",
            "V": V,
            "total_cells": total,
            "nonzero": int(nonzero),
            "density": round(density, 6),
            "memory_gb": round(total * 4 / (1024**3), 3),
            "file_size_mb": round(os.path.getsize(self.path) / (1024**2), 1),
            "dtype": "float32",
        }

    def to_dense_numpy(self) -> np.ndarray:
        """Read the entire matrix into a dense numpy array (RAM-heavy!)."""
        if self._mmap is None:
            raise RuntimeError("BinaryStore: mmap not initialized")
        return np.array(self._mmap)

    def estimate_optimal_V(self, target_mb: int = 800) -> int:
        """
        Estimate matrix dimension V given a target file size in MB.
        Formula: V = sqrt(target_bytes / 4)
        """
        target_bytes = target_mb * 1024 * 1024
        V = int(np.sqrt(target_bytes / 4))
        return V
