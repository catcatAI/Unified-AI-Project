#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [γ] [B] [L0]
# =============================================================================
"""
GARDEN CLI — interactive query, stats, and engine management.

Usage (from project root):
    python -m apps.backend.src.ai.garden query "你好"
    python -m apps.backend.src.ai.garden query "今天天气怎样" --depth deep
    python -m apps.backend.src.ai.garden stats
    python -m apps.backend.src.ai.garden serve
    python -m apps.backend.src.ai.garden save ./garden_checkpoint/
    python -m apps.backend.src.ai.garden load ./garden_checkpoint/
"""

import argparse
import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", ".."),
)

from apps.backend.src.ai.garden.garden_engine import GARDENEngine


def _make_engine(checkpoint: str = "") -> GARDENEngine:
    engine = GARDENEngine()
    if checkpoint and os.path.isdir(checkpoint):
        engine.load(checkpoint)
        print(f"  Loaded checkpoint: {checkpoint}")
    else:
        engine.load_presets()
        print(f"  Loaded presets ({len(engine.dictionary.entries)} concepts)")
    return engine


def cmd_query(args) -> None:
    engine = _make_engine(args.checkpoint)
    t0 = time.time()
    response = engine.process(args.text)
    elapsed_ms = (time.time() - t0) * 1000
    print(response)
    if args.verbose:
        keys = engine.dictionary.encode(args.text)
        print(f"\n  [input_keys={keys}  latency={elapsed_ms:.1f}ms]")


def cmd_stats(args) -> None:
    engine = _make_engine(args.checkpoint)
    s = engine.stats()
    print("\n  GARDEN-1G Engine Stats")
    print("  " + "=" * 44)
    print(f"  Tier:                {s['tier']}")
    print(f"  Query count:         {s['query_count']}")
    print(f"  Reflex patterns:     {s['reflex_patterns']}")
    d = s["dictionary"]
    print(f"  Dictionary entries:  {d['entry_count']}")
    print(f"  Encoder type:        {d['encoder_type']}")
    print(f"  Embedding dim:       {d.get('embedding_dim', '(not built)')}")
    snn = s["snn"]
    print(f"  SNN vocab size:      {snn['vocab_size']}")
    print(f"  SNN matrix shape:    {snn['weight_matrix_shape']}")
    mem_kb = snn["matrix_memory_bytes"] / 1024
    print(f"  SNN matrix memory:   {mem_kb:.1f} KB")
    print(f"  SNN density:         {snn['matrix_density']:.4f}")
    print()


def cmd_serve(args) -> None:
    engine = _make_engine(args.checkpoint)
    print("\nGARDEN-1G Interactive Mode  (type 'quit' to exit)\n")
    while True:
        try:
            text = input(">>> ").strip()
            if not text or text.lower() in ("quit", "exit", "q"):
                break
            t0 = time.time()
            response = engine.process(text)
            ms = (time.time() - t0) * 1000
            print(f"{response}  [{ms:.1f}ms]")
        except (KeyboardInterrupt, EOFError):
            break
    print()


def cmd_save(args) -> None:
    engine = _make_engine(args.checkpoint)
    engine.save(args.directory)
    print(f"  Saved to {args.directory}")


def cmd_load(args) -> None:
    """Load engine state from a saved directory."""
    if not os.path.isdir(args.directory):
        print(f"  Error: directory not found: {args.directory}")
        return
    engine = GARDENEngine()
    engine.load(args.directory)
    print(f"  Loaded from {args.directory}")
    s = engine.stats()
    print(f"  Dictionary: {s['dictionary']['entry_count']} entries")
    print(f"  SNN vocab:  {s['snn']['vocab_size']}")


def cmd_learn(args) -> None:
    """Learn from a single interaction."""
    engine = _make_engine(args.checkpoint)
    result = engine.learn_from_interaction(
        user_text=args.user_text,
        response_text=args.response_text,
        confidence=args.confidence,
    )
    print(f"  Learned from interaction #{result['interaction']}")
    if result["new_concepts"]:
        print(f"  New concepts: {', '.join(result['new_concepts'])}")
    print(f"  Hebbian delta: {result['hebbian_delta']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="GARDEN-1G Command Line Interface")
    parser.add_argument("--checkpoint", "-c", default="", help="Path to saved engine directory")
    sub = parser.add_subparsers(dest="command")

    p_query = sub.add_parser("query", help="Query the engine with text")
    p_query.add_argument("text", help="Input text")
    p_query.add_argument("--verbose", "-v", action="store_true", help="Show keys and latency")

    sub.add_parser("stats", help="Show engine statistics")
    sub.add_parser("serve", help="Interactive query mode")

    p_save = sub.add_parser("save", help="Save engine state")
    p_save.add_argument("directory", help="Directory to save into")

    sub.add_parser("load", help="Alias for --checkpoint; loads engine state from directory")

    # Add 'learn' subcommand for interactive learning
    p_learn = sub.add_parser("learn", help="Learn from an interaction")
    p_learn.add_argument("user_text", help="User input text")
    p_learn.add_argument("response_text", help="Response text")
    p_learn.add_argument("--confidence", "-c", type=float, default=0.7, help="Learning confidence")

    p_load = sub.add_parser("load", help="Load engine state from directory")
    p_load.add_argument("directory", help="Directory to load from")

    args = parser.parse_args()
    if args.command == "query":
        cmd_query(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "serve":
        cmd_serve(args)
    elif args.command == "save":
        cmd_save(args)
    elif args.command == "load":
        cmd_load(args)
    elif args.command == "learn":
        cmd_learn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
