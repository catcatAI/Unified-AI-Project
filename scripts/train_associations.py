#!/usr/bin/env python3
"""
Train GARDEN SNN on real WordNet association data.

Pre-filters to top-K most connected concepts to stay within RAM budget.
Wires associations directly via TensorSNNCore.add_relation().
"""
import json
import logging
import os
import sys
import time
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TrainAssociations")
for n in ("garden_engine", "VectorDictionary", "TensorSNNCore"):
    logging.getLogger(n).setLevel(logging.WARNING)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src")))

from ai.garden.garden_engine import GARDENEngine
from ai.garden.snn_core import TensorSNNCore

CKPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "checkpoints"))
ASSOC_DATA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "data", "raw_datasets", "association_training_data.json"))

# Target: ~10K new WordNet neurons + 5K existing = 15K total
# 15K x 15K x 4 bytes = ~900MB (fits in 1.7GB available)
MAX_WN_CONCEPTS = 10000
MAX_VOCAB = 15000  # existing presets + new WordNet

REL_WEIGHTS = {
    "hypernym": 0.3, "hyponym": 0.3, "synonym": 0.4, "antonym": 0.15,
    "property": 0.2, "purpose": 0.2, "whole": 0.2, "location": 0.2,
    "causes": 0.25, "capability": 0.2,
}


def main():
    print("=" * 60)
    print("  GARDEN SNN Association Training (capped vocabulary)")
    print("=" * 60)

    # Load association data
    print(f"\nLoading {ASSOC_DATA}...")
    with open(ASSOC_DATA, "r", encoding="utf-8") as f:
        triples = json.load(f)
    print(f"  Loaded {len(triples)} triples")

    # Count concept frequency to find the most connected concepts
    freq = Counter()
    for t in triples:
        ca = t.get("concept_a", "").strip().lower()
        cb = t.get("concept_b", "").strip().lower()
        if ca and cb and ca != cb:
            freq[ca] += 1
            freq[cb] += 1

    # Select top-K most frequent concepts
    top_concepts = set(c for c, _ in freq.most_common(MAX_WN_CONCEPTS))
    print(f"  Selected top {len(top_concepts)} most-connected concepts "
          f"(max frequency: {freq.most_common(1)[0][1]}, "
          f"min frequency: {freq.most_common(MAX_WN_CONCEPTS)[-1][1]})")

    # Filter triples to only those where both concepts are in top-K
    filtered = []
    for t in triples:
        ca = t.get("concept_a", "").strip().lower()
        cb = t.get("concept_b", "").strip().lower()
        if ca in top_concepts and cb in top_concepts and ca != cb:
            filtered.append(t)
    print(f"  Filtered to {len(filtered)} triples (both concepts in top-{MAX_WN_CONCEPTS})")

    # Initialize GARDEN with capped vocabulary (fresh — don't load old checkpoint
    # which may be numpy-format while current session uses torch)
    print(f"\nInitializing GARDEN engine (max_vocab={MAX_VOCAB})...")
    engine = GARDENEngine(compatibility_mode=True)
    engine.load_presets()
    print(f"  Loaded presets: {len(engine.dictionary.entries)} dict entries")

    # Reinitialize SNN with capped vocab
    snn = engine.snn
    snn.max_vocab = MAX_VOCAB
    print(f"  SNN vocab: {snn.vocab_size} neurons (max_vocab={MAX_VOCAB})")

    # Wire associations directly into SNN
    print(f"\nWiring {len(filtered)} associations into SNN weight matrix...")
    t0 = time.time()
    wired = 0
    skipped = 0
    keys_created = set()

    for i, triple in enumerate(filtered):
        ca = triple["concept_a"].strip().lower()
        cb = triple["concept_b"].strip().lower()
        rel = triple.get("relation", "synonym")
        strength = float(triple.get("strength", 0.7))

        key_a = f"wn_{ca}"
        key_b = f"wn_{cb}"
        weight = REL_WEIGHTS.get(rel, 0.5) * strength

        snn.add_relation(key_a, key_b, weight=weight, bidirectional=True)
        keys_created.add(key_a)
        keys_created.add(key_b)
        wired += 1

        if (i + 1) % 20000 == 0:
            elapsed = time.time() - t0
            print(f"  Processed {i + 1}/{len(filtered)} ({wired} wired, "
                  f"{snn.vocab_size} neurons, {elapsed:.1f}s)...")

    elapsed = time.time() - t0
    print(f"\n  Done in {elapsed:.1f}s")
    print(f"  Associations wired: {wired}")
    print(f"  Unique WN concepts: {len(keys_created)}")
    print(f"  SNN total vocab: {snn.vocab_size} neurons")
    matrix_mb = snn.vocab_size ** 2 * 4 / 1024 / 1024
    print(f"  SNN matrix size: ~{matrix_mb:.0f} MB")

    # Save checkpoint
    assoc_ckpt = os.path.join(CKPT_DIR, "garden_associations")
    print(f"\nSaving checkpoint to {assoc_ckpt}...")
    engine.save(assoc_ckpt)
    print("  Saved!")

    # Verify: test propagation
    print("\n--- Verification: SNN propagation tests ---")
    test_cases = [
        (["wn_dog"], "dog -> related concepts"),
        (["wn_car"], "car -> related concepts"),
        (["wn_happy"], "happy -> related concepts"),
        (["wn_water"], "water -> related concepts"),
        (["wn_food"], "food -> related concepts"),
    ]
    for input_keys, label in test_cases:
        existing = [k for k in input_keys if k in snn._key_to_idx]
        if existing:
            result = snn.forward(existing)
            top = sorted(result.items(), key=lambda x: -x[1])[:5]
            top_labels = [f"{k[3:]}({v:.2f})" for k, v in top if v > 0.01]
            print(f"  {label}: {', '.join(top_labels)}")
        else:
            print(f"  {label}: NOT IN SNN")

    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
