#!/usr/bin/env python3
"""
=============================================================================
ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
=============================================================================

Unified Engine training + honest generalisation evaluation.

Trains ``UnifiedEngine`` on real project datasets (arithmetic / logic) and
reports the metrics that define a REAL AI, not a memoriser:

  - fixed_memory     : model_bytes constant before/after training
  - compression      : corpus_bytes / model_bytes (grows with the corpus)
  - generalisation   : held-out accuracy (deterministic math + learned core)
  - generation       : sample continuations; measure distributional overlap

All metrics are measured on UNSEEN held-out samples (train/test split),
never on the training set. This replaces the old three_axis/ED3N/GARDEN
"training-set self-test" evaluations that measured memorisation.

Usage:
  python scripts/train_unified.py [--checkpoint PATH] [--seed N]
                                  [--test-ratio R] [--max-samples N]
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
from typing import Dict, List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))

from ai.unified_engine.trainer import (  # noqa: E402
    _answers_match,
    _answer_of,
    _query_of,
    evaluate_generalisation,
    measure_generation_fidelity,
    train_test_split,
)
from ai.unified_engine.unified_engine import UnifiedEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DATASETS = [
    ("arithmetic", "apps/backend/data/raw_datasets/arithmetic_train_dataset.json", "problem"),
    ("logic", "apps/backend/data/raw_datasets/logic_train.json", "proposition"),
]


def load_samples(max_samples: Optional[int] = None) -> List[str]:
    samples: List[str] = []
    for name, path, key in DEFAULT_DATASETS:
        if not os.path.exists(path):
            logger.warning("dataset missing, skipping: %s", path)
            continue
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
        for row in rows:
            if name == "arithmetic":
                samples.append(f"{row['problem']}={row['answer']}")
            else:
                samples.append(f"{row['proposition']}={row['answer']}")
        logger.info("loaded %s: %d rows", name, len(rows))
    if max_samples:
        samples = samples[:max_samples]
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Unified Engine.")
    parser.add_argument("--checkpoint", default="data/checkpoints/unified/unified.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--max-samples", type=int, default=None)
    args = parser.parse_args()

    samples = load_samples(args.max_samples)
    if not samples:
        logger.error("no datasets loaded; run the dataset prepare step first")
        sys.exit(1)
    logger.info("total samples: %d", len(samples))

    train, test = train_test_split(samples, args.test_ratio, args.seed)
    logger.info("train=%d test=%d", len(train), len(test))

    t0 = time.time()
    engine = UnifiedEngine(memory_cap_mb=2048)
    engine.learn_batch(train)
    train_secs = time.time() - t0
    logger.info("trained %d samples in %.1fs", len(train), train_secs)

    results: Dict = {
        "train_samples": len(train),
        "test_samples": len(test),
        "train_secs": round(train_secs, 1),
        "model_bytes": engine.model_bytes,
        "train_corpus_bytes": engine.corpus_bytes,
        "compression_ratio": round(engine.compression_ratio(), 4),
        "memory_usage_ratio": round(engine.memory_usage_ratio(), 4),
    }

    # Route breakdown on held-out test set (honest per-capability numbers).
    routes: Dict[str, Dict[str, int]] = {}
    for s in test:
        q, truth = _query_of(s), _answer_of(s)
        out = engine.process(q)
        route = engine._last_route
        routes.setdefault(route, {"n": 0, "ok": 0})
        routes[route]["n"] += 1
        routes[route]["ok"] += int(_answers_match(out, truth, s))
    results["route_breakdown"] = routes
    total_ok = sum(v["ok"] for v in routes.values())
    total_n = sum(v["n"] for v in routes.values())
    results["test_accuracy"] = round(total_ok / max(1, total_n), 4)
    results["route_breakdown_pct"] = {
        k: round(v["ok"] / max(1, v["n"]), 4) for k, v in routes.items()
    }

    # Generation fidelity (reproduction as a by-product of generalisation).
    gen = measure_generation_fidelity(engine.core, train, n=30)
    results["generation"] = gen

    os.makedirs(os.path.dirname(os.path.abspath(args.checkpoint)), exist_ok=True)
    engine.save(args.checkpoint)
    logger.info("checkpoint written: %s", args.checkpoint)

    print("\n===== UNIFIED ENGINE RESULT =====")
    print(f"  train samples     : {results['train_samples']}")
    print(f"  model bytes       : {results['model_bytes']}")
    print(f"  corpus bytes      : {results['train_corpus_bytes']}")
    print(f"  compression ratio : {results['compression_ratio']}")
    print(f"  test accuracy     : {results['test_accuracy']}")
    print(f"  route breakdown   : {results['route_breakdown_pct']}")
    print(f"  generation overlap: {results['generation']['bigram_overlap']}")

    out = args.checkpoint.replace(".json", ".results.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    logger.info("results written: %s", out)


if __name__ == "__main__":
    main()
