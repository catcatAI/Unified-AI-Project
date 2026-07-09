#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

"""
ED3N CLI — Query, train, and manage the ED3N engine.

Usage:
    python -m ed3n query "你好"
    python -m ed3n train data.json --epochs 5
    python -m ed3n serve          # Start interactive mode
    python -m ed3n stats          # Show engine statistics
    python -m ed3n save path.json
    python -m ed3n load path.json
"""

import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from .ed3n_engine import ED3NEngine
from .ed3n_trainer import ED3NTrainer
from .training_types import TrainingBatch, TrainingExample


def get_engine(path: str = "") -> ED3NEngine:
    e = ED3NEngine()
    if path and os.path.exists(path):
        e.load(path)
        print(f"  Loaded checkpoint: {path}")
    else:
        e.load_presets()
        print(f"  Loaded presets ({len(e.dictionary.entries)} entries)")
    return e


def cmd_query(args) -> None:
    e = get_engine(args.checkpoint)
    result = e.process(args.text, depth=args.depth)
    print(result)


def cmd_train(args) -> None:
    import csv
    e = get_engine(args.checkpoint)

    # Load data
    if args.data.endswith(".csv"):
        examples = []
        with open(args.data, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                examples.append({"input": row.get("input", row.get("problem", "")),
                                 "output": row.get("output", row.get("answer", ""))})
    elif args.data.endswith(".json"):
        with open(args.data, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            examples = [{"input": item.get("input", item.get("problem", "")),
                         "output": item.get("output", item.get("answer", ""))}
                        for item in raw]
        else:
            examples = raw.get("examples", [])
    else:
        print(f"Unsupported format: {args.data}")
        sys.exit(1)

    # Filter empty
    examples = [ex for ex in examples if ex["input"] and ex["output"]]
    if not examples:
        print("No valid examples found")
        return
    print(f"  Training on {len(examples)} examples ({args.epochs} epochs)...")

    # Build TrainingExamples
    texamples = []
    for ex in examples:
        ik = e.dictionary.encode(ex["input"])
        ok = e.dictionary.encode(ex["output"])
        if not ik or not ok:
            continue
        texamples.append(TrainingExample(
            input_text=ex["input"], expected_output=ex["output"],
            input_keys=ik, output_keys=ok,
            relation_pairs=[], confidence=0.8, metadata={},
        ))

    if not texamples:
        print("No examples with valid dictionary keys")
        return

    trainer = JointTrainer(e, dict_lr=args.lr, network_lr=args.lr)
    t0 = time.time()
    for epoch in range(args.epochs):
        batch = TrainingBatch(examples=texamples, batch_id=f"cli_{epoch}")
        metrics = trainer.train_step(batch)
        print(f"  Epoch {epoch+1}/{args.epochs}: loss={metrics.loss:.4f} acc={metrics.accuracy:.4f}")

    print(f"  Training completed in {time.time()-t0:.1f}s")

    # Save
    if args.output:
        e.save(args.output)
        trainer.save(args.output.replace(".json", "_trainer.json"))
        print(f"  Saved to {args.output}")


def cmd_serve(args):
    e = get_engine(args.checkpoint)
    # Wire continuous learning for interactive sessions
    try:
        from .continuous_learning import ContinuousLearningPipeline
        from .ed3n_trainer import JointTrainer

        trainer = JointTrainer(e, dict_lr=0.05, network_lr=0.05)
        clp = ContinuousLearningPipeline(engine=e, trainer=trainer,
                                         growth_interval=15, train_interval=50,
                                         min_examples_for_train=30, auto_grow=True)
        e._continuous_learning = clp
        print("  Continuous learning enabled")
    except Exception as exc:
        print(f"  Continuous learning unavailable: {exc}")

    print("\nED3N Interactive Mode (type 'quit' to exit)\n")
    while True:
        try:
            text = input(">>> ").strip()
            if not text or text.lower() in ("quit", "exit", "q"):
                break
            result = e.process(text)
            print(result)
        except (KeyboardInterrupt, EOFError):
            break
    print()


def cmd_stats(args):
    e = get_engine(args.checkpoint)
    ds = e.dictionary.get_stats()
    print(f"\n  ED3N Engine Stats")
    print(f"  {'='*40}")
    print(f"  Dictionary entries:  {ds.get('entry_count', 0)}")
    print(f"  Relations:           {ds.get('relation_count', 0)}")
    print(f"  Avg confidence:      {ds.get('avg_confidence', 0):.4f}")
    print(f"  Growth history:      {ds.get('growth_history_count', 0)}")
    print(f"  Reflex patterns:     {len(e.reflex.patterns)}")
    print(f"  SNN mode:            {e.snn_mode}")
    print(f"  Multimodal:          {'enabled' if e.image_encoder or e.audio_encoder else 'disabled'}")
    print()


def cmd_save(args) -> None:
    e = get_engine(args.checkpoint)
    e.save(args.path)
    print(f"  Saved to {args.path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ED3N Command Line Interface")
    parser.add_argument("--checkpoint", "-c", default="", help="Path to engine checkpoint")
    sub = parser.add_subparsers(dest="command")

    p_query = sub.add_parser("query", help="Query the engine with text")
    p_query.add_argument("text", help="Input text")
    p_query.add_argument("--depth", default="auto", choices=["auto", "reflex", "shallow", "deep", "snn"])

    p_train = sub.add_parser("train", help="Train on data file")
    p_train.add_argument("data", help="Path to JSON/CSV training data")
    p_train.add_argument("--epochs", type=int, default=3)
    p_train.add_argument("--lr", type=float, default=0.05)
    p_train.add_argument("--output", "-o", default="", help="Output checkpoint path")

    sub.add_parser("serve", help="Interactive query mode")
    sub.add_parser("stats", help="Show engine statistics")

    p_save = sub.add_parser("save", help="Save checkpoint")
    p_save.add_argument("path", help="Output path")

    args = parser.parse_args()
    if args.command == "query":
        cmd_query(args)
    elif args.command == "train":
        cmd_train(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "save":
        cmd_save(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
