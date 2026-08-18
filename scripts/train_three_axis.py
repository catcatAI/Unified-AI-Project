#!/usr/bin/env python3
"""
=============================================================================
ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
=============================================================================

Three-Axis System training + dialogue verification.

Trains ``ThreeAxisEngine`` on real project datasets (arithmetic / logic /
alpaca) honouring the project memory capacity cap (2 GiB default). Outputs a
JSON checkpoint, then runs a small dialogue verification pass.

Usage:
  python scripts/train_three_axis.py [--max-samples N] [--max-seq LEN]
                                     [--limit-chars N] [--no-alpaca]

Memory safety: the engine's value-pair tables are bounded (<= 65,536 entries)
and position x content matrix is sparse; training reports the measured memory
usage ratio against the capacity cap and fails loudly if the cap is exceeded.
"""

# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================

import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TrainThreeAxis")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "apps/backend/src")
sys.path.insert(0, SRC)

DATA_DIR = os.path.join(ROOT, "apps/backend/data/raw_datasets")
CHECKPOINT_DIR = os.path.join(ROOT, "data/checkpoints/three_axis")
CHECKPOINT = os.path.join(CHECKPOINT_DIR, "three_axis.json")


def _load_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_samples(include_alpaca: bool, max_samples: int) -> list:
    """Load real project datasets into training strings.

    Each sample is serialised as ``<input>=<output>`` so the engine learns the
    position structure linking a problem to its answer.
    """
    samples: list = []

    arith = _load_json(os.path.join(DATA_DIR, "arithmetic_train_dataset.json"))
    for item in arith[:max_samples]:
        samples.append(f"{item['problem']}={item['answer']}")

    logic = _load_json(os.path.join(DATA_DIR, "logic_train.json"))
    for item in logic[:max_samples]:
        out = str(item["answer"]).lower() if isinstance(item["answer"], bool) else str(item["answer"])
        samples.append(f"{item['proposition']}={out}")

    if include_alpaca:
        alpaca = _load_json(os.path.join(DATA_DIR, "alpaca_data.json"))
        for item in alpaca[:max_samples]:
            inp = item.get("input", "").strip()
            out = item.get("output", "").strip()
            if inp and out:
                samples.append(f"{inp}={out}")

    logger.info("Loaded %d training samples", len(samples))
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Three-Axis engine")
    parser.add_argument("--max-samples", type=int, default=30000)
    parser.add_argument("--max-seq", type=int, default=512)
    parser.add_argument("--no-alpaca", action="store_true")
    parser.add_argument("--memory-cap-mb", type=float, default=None)
    args = parser.parse_args()

    from ai.three_axis.three_axis_engine import ThreeAxisEngine

    engine = ThreeAxisEngine(
        memory_cap_mb=args.memory_cap_mb,
        max_seq_len=args.max_seq,
    )
    logger.info(
        "ThreeAxisEngine memory cap: %.1f MiB (%d bytes)",
        engine.memory_cap_bytes / 1024 / 1024,
        engine.memory_cap_bytes,
    )

    samples = load_samples(include_alpaca=not args.no_alpaca, max_samples=args.max_samples)

    t0 = time.time()
    stats = engine.learn_batch(samples)
    elapsed = time.time() - t0
    logger.info(
        "Trained %d samples in %.1fs | chars=%d positions=%d transitions=%d",
        stats["samples"],
        elapsed,
        stats["corpus_chars"],
        stats["positions"],
        stats["transitions"],
    )
    logger.info(
        "Memory: %.1f MiB / %.1f MiB cap (ratio %.3f)",
        stats["memory_bytes"] / 1024 / 1024,
        stats["memory_cap_bytes"] / 1024 / 1024,
        stats["memory_ratio"],
    )
    if stats["memory_ratio"] > 1.0:
        logger.error("Memory cap EXCEEDED (ratio %.3f) — aborting save", stats["memory_ratio"])
        return 1

    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    engine.save(CHECKPOINT)
    logger.info("Saved checkpoint: %s", CHECKPOINT)

    # Dialogue verification on unseen samples.
    logger.info("=== Dialogue verification ===")
    probes = [
        ("178 + 101=?", "178 + 101=279"),
        ("293 - 192=?", "293 - 192=101"),
        ("917 * 814=?", "917 * 814=746438"),
        # Sliding-alignment variants: whitespace / leading-word differences must
        # still align to the same answer via the learned anchor tables.
        ("178+101=?", "178+101=279"),
        ("what is 178 + 101=?", "what is 178 + 101=279"),
        ("178  +  101=?", "178  +  101=279"),
    ]
    for probe, truth in probes:
        out = engine.process(probe)
        ok = "OK" if out == truth else "XX"
        logger.info("  %s  %-16s -> %-16s (conf=%.2f, route=%s)", ok, probe, out, engine.last_confidence, engine._last_route)
    return 0


if __name__ == "__main__":
    sys.exit(main())