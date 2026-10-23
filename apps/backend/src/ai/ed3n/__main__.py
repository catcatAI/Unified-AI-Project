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
from typing import Any, List, cast

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))

from .ed3n_engine import ED3NEngine
from .ed3n_trainer import ED3NTrainer, JointTrainer
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


def _pair(item: dict) -> dict:
    """Normalize one dataset row to ``{"input", "output"}``.

    Alpaca-style rows put the task in ``instruction`` and only the optional
    context in ``input``; reading ``input`` alone therefore dropped ~every
    alpaca row (its ``input`` is usually empty) and the trainer reported
    "No valid examples". The instruction is the input; the context is
    appended when present.
    """
    instruction = str(item.get("instruction") or item.get("question") or item.get("prompt") or "")
    context = str(item.get("input") or "")
    problem = str(item.get("problem") or "")
    text_in = problem or (f"{instruction}\n{context}".strip() if context else instruction)
    return {
        "input": text_in.strip(),
        "output": str(
            item.get("output") or item.get("response") or item.get("answer") or ""
        ).strip(),
    }


def _load_train_examples(path: str) -> List[dict]:
    """依副檔名載入 CSV/JSON 訓練樣本；不支援格式印訊息 exit(1)。"""
    import csv

    if path.endswith(".csv"):
        with open(path, encoding="utf-8") as f:
            return [_pair(row) for row in csv.DictReader(f)]
    if path.endswith(".jsonl"):
        with open(path, encoding="utf-8") as f:
            return [_pair(json.loads(line)) for line in f if line.strip()]
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, list):
            return [_pair(item) for item in raw]
        return [_pair(item) for item in raw.get("examples", [])]
    print(f"Unsupported format: {path}")
    sys.exit(1)


def _build_texamples(engine: Any, examples: List[dict]) -> List[TrainingExample]:
    """encode 兩端得 keys；任一為空跳過該例。"""
    texamples: List[TrainingExample] = []
    for ex in examples:
        ik = engine.dictionary.encode(ex["input"])
        ok = engine.dictionary.encode(ex["output"])
        if not ik or not ok:
            continue
        texamples.append(
            TrainingExample(
                input_text=ex["input"],
                expected_output=ex["output"],
                input_keys=ik,
                output_keys=ok,
                relation_pairs=[],
                confidence=0.8,
                metadata={},
            )
        )
    return texamples


def cmd_train(args) -> None:
    e = get_engine(args.checkpoint)

    # Load data
    examples = [ex for ex in _load_train_examples(args.data) if ex["input"] and ex["output"]]
    if not examples:
        print("No valid examples found")
        return
    print(f"  Training on {len(examples)} examples ({args.epochs} epochs)...")

    # Build TrainingExamples
    texamples = _build_texamples(e, examples)

    if not texamples:
        print("No examples with valid dictionary keys")
        return

    # Train both paths. The association path alone was trained before, while
    # ``generate()`` reads the sequence decoder — so the CLI could report
    # acc=1.000 and still emit nonsense (the decoder had never seen an edge).
    from .training_types import seq_batch_from_examples

    trainer = JointTrainer(e, dict_lr=args.lr, network_lr=args.lr)
    t0 = time.time()
    for epoch in range(args.epochs):
        batch = TrainingBatch(examples=texamples, batch_id=f"cli_{epoch}")
        seq_batch = seq_batch_from_examples(texamples, batch_id=f"cli_seq_{epoch}")
        metrics = trainer.train_step(batch, seq_batch=seq_batch)
        print(
            f"  Epoch {epoch+1}/{args.epochs}: loss={metrics.loss:.4f} acc={metrics.accuracy:.4f}"
        )

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
        clp = ContinuousLearningPipeline(
            engine=e,
            trainer=trainer,
            growth_interval=15,
            train_interval=50,
            min_examples_for_train=30,
            auto_grow=True,
        )
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
    print("\n  ED3N Engine Stats")
    print(f"  {'='*40}")
    print(f"  Dictionary entries:  {ds.get('entry_count', 0)}")
    print(f"  Relations:           {ds.get('relation_count', 0)}")
    print(f"  Avg confidence:      {ds.get('avg_confidence', 0):.4f}")
    print(f"  Growth history:      {ds.get('growth_history_count', 0)}")
    print(f"  Reflex patterns:     {len(e.reflex.patterns)}")
    print(f"  SNN mode:            {e.snn_mode}")
    print(
        f"  Multimodal:          {'enabled' if e.image_encoder or e.audio_encoder else 'disabled'}"
    )
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
    p_query.add_argument(
        "--depth", default="auto", choices=["auto", "reflex", "shallow", "deep", "snn"]
    )

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
