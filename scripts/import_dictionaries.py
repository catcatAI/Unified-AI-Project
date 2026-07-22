#!/usr/bin/env python3
"""
Import external dictionary JSON files into ED3N's DictionaryLayer.

Usage:
    python scripts/import_dictionaries.py [file ...]

If no file specified, imports all JSON files from data/dictionaries/.
Use --engine to create a full ED3NEngine with imported dictionaries.
Use --test to run sample queries after import.
"""

import json
import logging
import os
import re
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("import_dictionaries")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "apps" / "backend" / "src"))

from ai.ed3n.dictionary_layer import DictionaryLayer
from core.system.config.magic_numbers import limit_value


def import_json(dictionary: DictionaryLayer, path: Path) -> int:
    """Import a single JSON file using bulk import; return entry count."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries_data = data.get("entries", [])
    if not entries_data:
        logger.warning("No entries in %s", path.name)
        return 0

    # Filter out entries that already exist
    bulk=[e for e in entries_data if e.get("key") and e["key"] not in dictionary.entries]
    if not bulk:
        return 0
    return dictionary.bulk_add_entries(bulk)


def show_stats(dictionary: DictionaryLayer) -> None:
    """Print dictionary statistics."""
    stats = dictionary.get_stats()
    logger.info("Dictionary stats:")
    logger.info("  Total entries: %d", stats["entry_count"])
    logger.info("  Relations: %d", stats["relation_count"])
    logger.info("  Avg confidence: %.4f", stats["avg_confidence"])
    logger.info("  Language dist: %s", stats["language_distribution"])


def test_query(dictionary: DictionaryLayer, queries: list[str]) -> None:
    """Run sample queries against the dictionary."""
    print()
    logger.info("=== Sample Queries ===")
    for q in queries:
        keys = dictionary.encode(q)
        decoded = dictionary.decode(keys)
        soft = dictionary.encode_soft(q)
        top_soft = sorted(soft.items(), key=lambda x: -x[1])[:3]
        logger.info("  Query: %s", q)
        logger.info("    Keys: %s", keys)
        logger.info("    Decoded: %s", decoded)
        if top_soft:
            logger.info("    Top soft: %s", dict(top_soft))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Import dictionaries into ED3N")
    parser.add_argument("files", nargs="*", help="JSON files to import")
    parser.add_argument("--engine", action="store_true", help="Create ED3NEngine after import")
    parser.add_argument("--train", action="store_true", help="Train CoreNetwork on dictionary relations (implies --engine)")
    parser.add_argument("--test", action="store_true", help="Run sample queries after import")
    parser.add_argument(
        "--test-queries",
        nargs="*",
        default=["hello", "你好", "谢谢", "computer", "こんにちは"],
        help="Sample queries for --test",
    )
    args = parser.parse_args()
    if args.train:
        args.engine=True

    # Determine which files to import
    dict_dir = ROOT / "data" / "dictionaries"
    if args.files:
        files=[Path(f) for f in args.files]
    else:
        files = sorted(dict_dir.glob("*.json"))

    if not files:
        logger.warning("No JSON files found in %s", dict_dir)
        logger.info("Run 'python scripts/download_datasets.py' first to download dictionaries.")
        return

    dictionary = DictionaryLayer(max_entries=500000)
    dictionary.load_preset_responses()  # load built-in presets first

    total=0
    for f in files:
        if not f.exists():
            logger.warning("File not found: %s", f)
            continue
        t0 = time.perf_counter()
        n = import_json(dictionary, f)
        elapsed = time.perf_counter() - t0
        if n > 0:
            logger.info("Imported %5d entries from %s (%.1fs)", n, f.name, elapsed)
        total += n

    logger.info("Imported %d total entries", total)
    show_stats(dictionary)

    if args.test:
        test_query(dictionary, args.test_queries)

    if args.engine:
        logger.info("Creating ED3NEngine …")
        from ai.ed3n.ed3n_engine import ED3NEngine
        from ai.ed3n.ed3n_trainer import ED3NTrainer
        from ai.ed3n.training_types import TrainingExample

        engine = ED3NEngine(dictionary=dictionary)
        logger.info("ED3NEngine ready with %d dictionary entries", len(dictionary.entries))

        if args.train:
            logger.info("Starting relation-based co-occurrence training …")
            trainer = ED3NTrainer(engine)
            max_examples = limit_value("train.relation.max_examples", 2000)
            examples: list=[]
            processed=0
            t0 = time.perf_counter()
            for key, entry in dictionary.entries.items():
                if not entry.relations:
                    continue
                text = entry.surface_forms.get("en") or next(iter(entry.surface_forms.values()), key)
                for rel_type, targets in entry.relations.items():
                    for tgt_key in targets:
                        if tgt_key not in dictionary.entries:
                            continue
                        tgt_entry = dictionary.entries[tgt_key]
                        tgt_text = tgt_entry.surface_forms.get("en") or next(iter(tgt_entry.surface_forms.values()), tgt_key)
                        examples.append(TrainingExample(
                            input_text=text,
                            expected_output=tgt_text,
                            input_keys=[key],
                            output_keys=[tgt_key],
                            relation_pairs=[(key, rel_type, tgt_key)],
                            confidence=entry.confidence * 0.8,
                        ))
                        processed += 1
                        if processed % 500 == 0:
                            logger.info("  ... built %d training examples", processed)
                        if processed >= max_examples:
                            break
                    if processed >= max_examples:
                        break
                if processed >= max_examples:
                    break
            build_elapsed = time.perf_counter() - t0
            if examples:
                t1 = time.perf_counter()
                metrics = trainer.train_network_phase(examples)
                train_elapsed = time.perf_counter() - t1
                logger.info("Trained on %d relation examples in %.1fs (build=%.1fs, train=%.1fs, loss=%.4f, acc=%.4f)",
                            len(examples), build_elapsed + train_elapsed, build_elapsed, train_elapsed, metrics.loss, metrics.accuracy)
            else:
                logger.warning("No relation examples found for training")

        if args.test:
            print()
            logger.info("=== ED3NEngine Samples ===")
            for q in args.test_queries:
                t0 = time.perf_counter()
                resp = engine.process(q)
                elapsed = time.perf_counter() - t0
                logger.info("  %s -> %s (%.2fs)", q, resp, elapsed)
                if elapsed > 5:
                    logger.warning("Slow response (%.1fs) — timeout may be too short", elapsed)


if __name__ == "__main__":
    main()
