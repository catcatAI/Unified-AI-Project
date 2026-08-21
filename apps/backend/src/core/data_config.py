# =============================================================================
# ANGELA-MATRIX: [L2] [α] [A] [L2]
# =============================================================================
"""
Centralized dataset location configuration.

All dataset paths resolve through this module so the entire project can be
moved to an external volume (e.g. /media/covo/ZX) via a single env var.

Priority:
  1. $UNIFIED_DATA_ROOT  (e.g. /media/covo/ZX/Unified-AI-Project-data)
  2. $DATA_ROOT           (legacy alias)
  3. <project-root>/data and <project-root>/apps/backend/data (default)

Usage:
  from core.data_config import get_data_root, get_corpus_dir, get_dictionaries_dir

The functions always return a Path that exists (created if needed).
"""

from __future__ import annotations

import os
from pathlib import Path

# Project root: <repo>/apps/backend/src/core -> <repo>
_PROJECT_ROOT = Path(__file__).resolve().parents[4]


def get_data_root() -> Path:
    """Return the canonical data root directory."""
    for var in ("UNIFIED_DATA_ROOT", "DATA_ROOT"):
        val = os.environ.get(var)
        if val:
            p = Path(val).expanduser().resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
    # Default: check if /media/covo/ZX is mounted and has our data, prefer it
    zx = Path("/media/covo/ZX/Unified-AI-Project-data")
    if zx.exists() and any((zx / d).exists() for d in ("dictionaries", "raw_datasets", "checkpoints")):
        return zx
    # Fallback to repo-local data/
    return _PROJECT_ROOT / "data"


def get_dictionaries_dir() -> Path:
    p = get_data_root() / "dictionaries"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_corpus_dir() -> Path:
    # Corpus lives under raw_datasets/corpus for backward compat, but
    # get_data_root() may point to ZX where raw_datasets is the root.
    root = get_data_root()
    # If root is ZX/Unified-AI-Project-data, corpus is root/raw_datasets/corpus
    # If root is repo/data, corpus is repo/apps/backend/data/raw_datasets/corpus (symlinked to ZX)
    cand1 = root / "raw_datasets" / "corpus"
    cand2 = root / "corpus"
    # Prefer cand1 if it exists or if root looks like ZX
    if cand1.exists() or (root / "raw_datasets").exists():
        cand1.mkdir(parents=True, exist_ok=True)
        return cand1
    cand2.mkdir(parents=True, exist_ok=True)
    return cand2


def get_multimodal_dir() -> Path:
    p = get_data_root() / "multimodal"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_checkpoints_dir() -> Path:
    p = get_data_root() / "checkpoints"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_vector_store_dir() -> Path:
    # Respects VECTOR_STORE_PATH env var if set, else data_config
    if "VECTOR_STORE_PATH" in os.environ:
        return Path(os.environ["VECTOR_STORE_PATH"]).expanduser().resolve()
    p = get_data_root() / "vector_store"
    p.mkdir(parents=True, exist_ok=True)
    return p
