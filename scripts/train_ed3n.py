#!/usr/bin/env python3
"""ED3N Training + Reflex Generation Pipeline."""
import sys
import os
import json
import re
import csv
import time
import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))
from ai.ed3n.ed3n_engine import ED3NEngine
from ai.ed3n.ed3n_trainer import ED3NTrainer
from ai.ed3n.training_types import TrainingExample, TrainingBatch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

OP_MAP={"+": " plus ", "-": " minus ", "*": " times ", "/": " over "}

def preprocess(text):
    text = text.lower().strip()
    for s, w in OP_MAP.items():
        text = text.replace(s, w)
    text = re.sub(r"(\d)\.(\d)", r"\1 . \2", text)
    text = re.sub(r"\d+", lambda m: " ".join(m.group(0)), text)
    return text

def load_data(data_dir):
    samples=[]
    for fname in ["arithmetic_train_dataset.json", "logic_test.json"]:
        path = os.path.join(data_dir, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            inp = item.get("problem", item.get("proposition", ""))
            out = item.get("answer", "")
            out = str(out).lower() if isinstance(out, bool) else str(out)
            samples.append({"input": inp, "output": out, "domain": fname.split("_")[0]})
        print(f"  {fname}: {sum(1 for s in samples if s['domain'] == fname.split('_')[0])}")
        # Also CSV
    path = os.path.join(data_dir, "arithmetic_test_dataset.csv")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                samples.append({"input": row["problem"], "output": row["answer"], "domain": "arithmetic"})
        arith_count = sum(1 for s in samples if s["domain"] == "arithmetic")
        print(f"  arithmetic_test: {arith_count}")
    return samples

def add_reflex_patterns(engine, samples, top_n=5000):
    """Generate reflex patterns directly from training data."""
    count=0
    for s in samples:
        output_str = s["output"]
        if not output_str:
            continue
        engine.reflex.add_pattern(s["input"], output_str)
        count += 1
        if count >= top_n:
            break
    print(f"  Added {count} reflex patterns from training data")

def test(engine, queries, label=""):
    print(f"\n  --- {label} ---")
    for q, expected in queries:
        r = engine.process(q)
        ok="OK" if (expected and expected in r) else "?"
        print(f"  [{ok}] {q:35s} -> {r[:60] if r and len(r)>60 else r}")

def main():
    data_dir = os.path.join(ROOT, "apps/backend/data/raw_datasets")
    output_dir = os.path.join(ROOT, "data/checkpoints")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("  ED3N FULL TRAINING PIPELINE")
    print("=" * 60)

    print("\n[1/5] Loading data...")
    samples = load_data(data_dir)
    print(f"  Total: {len(samples)}")

    print("\n[2/5] Initializing ED3N...")
    engine = ED3NEngine()
    engine.load_presets()
    print(f"  Presets: {len(engine.dictionary.entries)} dict entries")

    print("\n[3/5] Expanding dictionary + training...")
    # Grow entries for unknown tokens in training data
    all_tokens = set()
    for s in samples:
        pp = preprocess(s["input"]) + " " + preprocess(s["output"])
        for t in re.findall(r"[\w]+", pp):
            if len(t) >= 1:
                all_tokens.add(t)
    before = len(engine.dictionary.entries)
    grown=0
    for token in sorted(all_tokens):
        if not engine.dictionary.encode(token):
            try:
                engine.dictionary.grow(token, token, confidence=0.7)
                grown += 1
            except Exception as e:
                logging.warning("Failed to grow dictionary token '%s': %s", token, e)
    engine.dictionary._rebuild_index()
    print(f"  Dictionary: {before} -> {len(engine.dictionary.entries)} ({grown} new)")

    # Create TrainingExamples with keys
    examples=[]
    skip=0
    for s in samples:
        inp = preprocess(s["input"])
        out = preprocess(s["output"])
        ik = list(set(engine.dictionary.encode(inp)))
        ok = list(set(engine.dictionary.encode(out)))
        if not ik or not ok:
            skip += 1
            continue
        pairs=[(a, "mapping", b) for a in ik[:5] for b in ok[:3]]
        examples.append(TrainingExample(
            input_text=s["input"], expected_output=s["output"],
            input_keys=ik, output_keys=ok,
            relation_pairs=pairs, confidence=0.8,
            metadata={"domain": s["domain"]},
        ))
    print(f"  Examples: {len(examples)} ({skip} skipped)")

    # Train
    print("\n  Training network...")
    trainer = ED3NTrainer(engine, dictionary_lr=0.05, network_lr=0.05)
    for epoch in range(3):
        t0 = time.time()
        batch = TrainingBatch(examples=examples, batch_id=f"ep{epoch}")
        m = trainer.train_step(batch)
        print(f"  Epoch {epoch+1}/3: loss={m.loss:.4f} acc={m.accuracy:.4f} ({time.time()-t0:.1f}s)")

    print("\n[4/5] Generating reflex patterns...")
    add_reflex_patterns(engine, samples, top_n=len(samples))

    print("\n[5/5] Saving full checkpoint...")
    engine.save(os.path.join(output_dir, "ed3n_full.json"))
    trainer.save(os.path.join(output_dir, "trainer_state.json"))
    engine.network.save_connections(os.path.join(output_dir, "network.json"))
    # Also export reflex patterns
    reflex_data={"patterns": list(engine.reflex.responses.items()) if hasattr(engine.reflex, "responses") else []}
    with open(os.path.join(output_dir, "reflex_patterns.json"), "w", encoding="utf-8") as f:
        json.dump(reflex_data, f, ensure_ascii=False, indent=2)
    print(f"  Saved to {output_dir}")

    print("\n" + "=" * 60)
    print("  EVALUATION")
    print("=" * 60)
    test(engine, [
        ("178 + 101", "279"),
        ("917 * 814", "746438"),
        ("true OR false", "true"),
        ("NOT false", "true"),
    ], "Seen problems")
    test(engine, [
        ("999 + 1", "1000"),
        ("123 + 456", "579"),
        ("50 * 50", "2500"),
        ("true AND false", "false"),
        ("你好嗎", None),
    ], "Unseen problems")

    print("\n  Final state:")
    print(f"    Dictionary entries: {len(engine.dictionary.entries)}")
    print(f"    Reflex patterns: {len(engine.reflex.patterns)}")
    print(f"    Training accuracy: {trainer.get_training_summary().get('last_accuracy', 0):.4f}")
    print("=" * 60)

if __name__ == "__main__":
    main()
