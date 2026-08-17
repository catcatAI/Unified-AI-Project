"""Compact + migrate the GARDEN SNN checkpoint to the live vocabulary size.

Background
----------
The pre-fix train loop left the SNN in a bad state on low-RAM boxes:

1. **Doubling growth + prune cycle**: ``_W`` was allocated by 2x doubling and
   never shrank on eviction, so V=20,573 live keys lived inside a 36,376^2
   block = 5 GB on a 7.5 GB machine → OOM on resume.
2. **Dead keys**: before Fix B, dictionary pruning did NOT sync the SNN
   registry.  The dictionary dropped to 9,573 entries while the SNN kept
   20,573 live keys — 11,000 neurons are unreachable (encode() goes through
   the dictionary) and only waste memory.
3. **Dense storage**: checkpoints saved the full dense matrix (or strided
   view of it) instead of sparse COO.

This script performs a one-time migration that fixes all three:
- loads the checkpoint with ``torch.load(..., mmap=True)`` (pages on demand,
  does not materialize the 5 GB block),
- computes the live key set from ``dictionary.json`` (the authoritative
  concept registry the encoder routes through),
- extracts the matching sub-matrix via vectorized ``index_select`` (peak ~1 GB
  — no 5 GB intermediate),
- re-writes the checkpoint using the engine's sparse-COO save path (~few MB).

Usage: python -m scripts.compact_garden_ckpt [--checkpoint path] [--dict path]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import resource
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps/backend/src"))


def _peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default="data/checkpoints/garden_checkpoint/snn.pt")
    parser.add_argument("--dict", default="data/checkpoints/garden_checkpoint/dictionary.json")
    args = parser.parse_args()

    import torch

    # 1. Load with mmap — the 5 GB storage pages in lazily; nothing materialized yet.
    logging.info("Loading checkpoint (mmap)… peak=%.0fMB", _peak_mb())
    state = torch.load(args.checkpoint, map_location="cpu", weights_only=True, mmap=True)
    W = state["W"]
    keys = list(state["idx_to_key"])
    logging.info("Loaded: W=%s, SNN V=%d, peak=%.0fMB", tuple(W.shape), len(keys), _peak_mb())

    # 2. Live key set = dictionary entries (authoritative concept registry).
    #    dictionary.json is {"version": ..., "entries": [{key, surface_forms, ...}, ...]}
    dict_keys = set()
    if os.path.exists(args.dict):
        with open(args.dict, "r", encoding="utf-8") as f:
            d = json.load(f)
        entries = d.get("entries", d) if isinstance(d, dict) else d
        if isinstance(entries, dict):
            dict_keys = set(entries.keys())
        elif isinstance(entries, list):
            for e in entries:
                if isinstance(e, dict) and e.get("key"):
                    dict_keys.add(e["key"])
    if not dict_keys:
        logging.warning("No dictionary entries found at %s — using full SNN registry", args.dict)
        dict_keys = set(keys)

    keep_indices = [i for i, key in enumerate(keys) if key in dict_keys]
    removed = len(keys) - len(keep_indices)
    logging.info(
        "Live keys: %d, dead keys to drop: %d (%.1f%% of matrix)",
        len(keep_indices),
        removed,
        100.0 * removed / len(keys) if keys else 0,
    )

    # 3. Extract sub-matrix in ONE vectorized pass (peak ~1 GB, no full copy).
    idx_arr = torch.tensor(keep_indices, dtype=torch.long)
    sub = W.index_select(0, idx_arr).index_select(1, idx_arr).contiguous()
    logging.info("Sub-matrix: %s (%.0f MB), peak=%.0fMB", tuple(sub.shape), sub.numel() * 4 / 2**20, _peak_mb())

    # 4. Rebuild registry maps to the kept keys.
    new_key_to_idx = {key: i for i, key in enumerate(keys[i] for i in keep_indices)}
    new_idx_to_key = [keys[i] for i in keep_indices]

    # 5. Save via the engine's sparse-COO path (few MB instead of dense GB).
    from ai.garden.snn_core import TensorSNNCore

    snn = TensorSNNCore(max_vocab=0)
    snn._W = sub
    snn._key_to_idx = new_key_to_idx
    snn._idx_to_key = new_idx_to_key
    snn.leak = float(state.get("leak", 0.2))
    snn.base_threshold = float(state.get("base_threshold", 0.3))
    snn.timesteps = int(state.get("timesteps", 6))
    snn.decay = float(state.get("decay", 0.6))
    snn.total_steps = int(state.get("total_steps", 0))
    snn.total_hebbian_updates = int(state.get("total_hebbian_updates", 0))
    out = args.checkpoint
    snn.save(out)
    logging.info(
        "Migrated checkpoint -> %s (V=%d, %.1f MB on disk), peak=%.0fMB",
        out,
        len(keep_indices),
        os.path.getsize(out) / 2**20,
        _peak_mb(),
    )


if __name__ == "__main__":
    main()
