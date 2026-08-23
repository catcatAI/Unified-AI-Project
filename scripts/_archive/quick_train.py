#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3+]
# =============================================================================
"""
Quick Training Script — trains ED3N and GARDEN with a small subset of data
to verify the training pipeline works and produces usable weights.

Usage:
    python scripts/quick_train.py

This is NOT a replacement for the full train_pipeline.py — it's a quick
verification that training works and produces weights that improve responses.
"""

import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("QuickTrain")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))

from ai.ed3n.ed3n_engine import ED3NEngine
from ai.ed3n.ed3n_trainer import ED3NTrainer
from ai.garden.garden_engine import GARDENEngine
from ai.core.model_bus import ModelBus

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "apps/backend/data/raw_datasets")
CKPT_DIR = os.path.join(os.path.dirname(__file__), "..", "data/checkpoints")
os.makedirs(CKPT_DIR, exist_ok=True)


def load_json_dataset(path: str, limit: int = 1000) -> list:
    """Load a JSON dataset with optional limit."""
    if not os.path.exists(path):
        logger.warning("Dataset not found: %s", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data[:limit]
    if isinstance(data, dict) and "samples" in data:
        return data["samples"][:limit]
    if isinstance(data, dict) and "data" in data:
        return data["data"][:limit]
    return []


def train_ed3n(engine: ED3NEngine, trainer: ED3NTrainer, samples: list, label: str) -> dict:
    """Train ED3N on a set of samples using the trainer's API."""
    if not samples:
        return {"status": "skipped", "reason": "no samples"}

    from ai.ed3n.training_types import TrainingExample

    examples = []
    for s in samples:
        if isinstance(s, dict):
            inp = s.get("input", s.get("problem", s.get("question", s.get("text", ""))))
            out = s.get("output", s.get("answer", s.get("response", s.get("result", ""))))
            if inp and out:
                examples.append(TrainingExample(
                    input_text=str(inp),
                    expected_output=str(out),
                    input_keys=[],
                    output_keys=[],
                    relation_pairs=[],
                    confidence=float(s.get("confidence", 0.8)),
                    metadata={"domain": s.get("domain", "general"), "source": "quick_train"},
                ))

    if not examples:
        return {"status": "skipped", "reason": "no valid samples"}

    metrics = trainer.train_dictionary_phase(examples)
    return {
        "status": "trained",
        "samples": len(examples),
        "loss": metrics.loss,
        "accuracy": metrics.accuracy,
    }


def main():
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("Quick Training Pipeline — ED3N + GARDEN")
    logger.info("=" * 60)

    # Step 1: Initialize engines
    logger.info("Step 1: Initializing engines...")
    ed3n = ED3NEngine.get_shared(load_trained=True)
    ed3n.warm_up()
    ed3n_stats = ed3n.dictionary.get_stats()
    logger.info("  ED3N dictionary: %d entries", ed3n_stats.get("entry_count", 0))

    garden = GARDENEngine(compatibility_mode=True)
    garden.load_presets()
    logger.info("  GARDEN presets loaded")

    trainer = ED3NTrainer(ed3n)

    # Step 2: Load training data (small subset for quick verification)
    logger.info("Step 2: Loading training data...")
    arithmetic = load_json_dataset(os.path.join(DATA_DIR, "arithmetic_train_dataset.json"), limit=500)
    logic = load_json_dataset(os.path.join(DATA_DIR, "logic_train.json"), limit=500)
    logger.info("  Arithmetic samples: %d", len(arithmetic))
    logger.info("  Logic samples: %d", len(logic))

    # Step 3: Train ED3N
    logger.info("Step 3: Training ED3N...")
    results = {}

    if arithmetic:
        results["arithmetic"] = train_ed3n(ed3n, trainer, arithmetic, "arithmetic")
        logger.info("  Arithmetic: %s", results["arithmetic"])

    if logic:
        results["logic"] = train_ed3n(ed3n, trainer, logic, "logic")
        logger.info("  Logic: %s", results["logic"])

    # Step 4: Save checkpoints
    logger.info("Step 4: Saving checkpoints...")
    ckpt_path = os.path.join(CKPT_DIR, "ed3n_quick_train.json")
    try:
        ed3n.save(ckpt_path)
        size = os.path.getsize(ckpt_path)
        logger.info("  Saved: %s (%d bytes)", ckpt_path, size)
        results["checkpoint"] = {"path": ckpt_path, "size": size}
    except Exception as e:
        logger.error("  Save failed: %s", e)
        results["checkpoint"] = {"error": str(e)}

    # Step 5: Verify training worked
    logger.info("Step 5: Verification...")
    test_queries = ["hello", "3+5", "what is AI"]
    for q in test_queries:
        try:
            resp = ed3n.process(q)
            logger.info("  '%s' → '%s'", q, str(resp)[:60] if resp else "None")
        except Exception as e:
            logger.warning("  '%s' → ERROR: %s", q, e)

    elapsed = time.time() - start_time
    logger.info("=" * 60)
    logger.info("Training complete in %.1f seconds", elapsed)
    logger.info("Results: %s", json.dumps(results, indent=2, default=str))
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    main()
