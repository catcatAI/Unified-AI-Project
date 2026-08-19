#!/usr/bin/env python3
"""
=============================================================================
ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
=============================================================================

Three-Axis System training + dialogue verification.

Trains ``ThreeAxisEngine`` on real project datasets (arithmetic / logic /
alpaca) honouring the project memory capacity cap (2 GiB default). Outputs a
JSON checkpoint, then runs a small dialogue verification pass.

Datasets are auto-provisioned: ``--prepare`` runs the auto-decision preparer
first (hardware tier + memory cap decide which datasets and how many samples),
and the per-dataset sample caps are read from the resulting manifest.

Usage:
  python scripts/train_three_axis.py [--prepare] [--max-samples N]
                                     [--max-seq LEN] [--no-alpaca]

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
from typing import Dict, Optional

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


def load_samples(
    include_alpaca: bool, max_samples: int, per_dataset: Optional[Dict[str, int]] = None
) -> list:
    """Load real project datasets into training strings.

    Each sample is serialised as ``<input>=<output>`` so the engine learns the
    position structure linking a problem to its answer. ``per_dataset`` caps
    each dataset independently (from the auto-decision manifest); otherwise a
    single ``max_samples`` slice applies to all.
    """
    samples: list = []
    per_dataset = per_dataset or {}

    def _cap(key: str) -> int:
        return per_dataset.get(key, max_samples)

    arith = _load_json(os.path.join(DATA_DIR, "arithmetic_train_dataset.json"))
    for item in arith[: _cap("arithmetic")]:
        samples.append(f"{item['problem']}={item['answer']}")

    logic = _load_json(os.path.join(DATA_DIR, "logic_train.json"))
    for item in logic[: _cap("logic")]:
        out = (
            str(item["answer"]).lower() if isinstance(item["answer"], bool) else str(item["answer"])
        )
        samples.append(f"{item['proposition']}={out}")

    if include_alpaca:
        alpaca = _load_json(os.path.join(DATA_DIR, "alpaca_data.json"))
        for item in alpaca[: _cap("alpaca")]:
            # Alpaca stores the prompt in ``instruction`` (+ optional ``input``
            # context); ``input`` alone is empty for ~60% of entries, so reading
            # only it silently dropped most of the dataset.
            inp = item.get("instruction", "").strip()
            extra = item.get("input", "").strip()
            if extra:
                inp = f"{inp} {extra}".strip()
            out = item.get("output", "").strip()
            if inp and out:
                samples.append(f"{inp}={out}")

    logger.info("Loaded %d training samples", len(samples))
    return samples


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Three-Axis engine")
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="auto-provision datasets first (hardware tier + memory cap decide)",
    )
    parser.add_argument("--max-samples", type=int, default=30000)
    parser.add_argument("--max-seq", type=int, default=512)
    parser.add_argument("--no-alpaca", action="store_true")
    parser.add_argument("--memory-cap-mb", type=float, default=None)
    args = parser.parse_args()

    if args.prepare:
        prep = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "prepare_three_axis_datasets.py"
        )
        rc = os.system(f"{sys.executable} {prep}")
        if rc != 0:
            logger.error("Dataset auto-provisioning failed (rc=%s); aborting", rc)
            return 1

    max_samples = args.max_samples
    per_dataset: Optional[Dict[str, int]] = None
    manifest_path = os.path.join(CHECKPOINT_DIR, "dataset_manifest.json")
    if args.max_samples == 30000 and os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                manifest = json.load(fh)
            caps = manifest.get("caps", {})
            per_dataset = {
                k: v
                for k, v in caps.items()
                if k in ("arithmetic", "logic", "alpaca") and isinstance(v, int)
            }
            if per_dataset:
                max_samples = max(per_dataset.values())
                logger.info(
                    "Using manifest per-dataset caps: %s (tier %s)",
                    per_dataset,
                    manifest.get("tier"),
                )
        except Exception as exc:  # noqa: BLE001 - corrupt manifest falls back to default
            logger.warning("Ignoring corrupt manifest (%s)", exc)

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

    samples = load_samples(
        include_alpaca=not args.no_alpaca,
        max_samples=max_samples,
        per_dataset=per_dataset,
    )

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
        logger.info(
            "  %s  %-16s -> %-16s (conf=%.2f, route=%s)",
            ok,
            probe,
            out,
            engine.last_confidence,
            engine._last_route,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
