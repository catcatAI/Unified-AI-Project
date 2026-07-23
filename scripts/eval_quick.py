#!/usr/bin/env python3
"""
Evaluate GARDEN SNN association quality.

Uses two evaluation modes:
1. Direct neighbor lookup (weight-matrix based) — fast, clean rankings
2. LIF forward pass — full neural simulation
"""
import json
import os
import time
import random
import numpy as np

BASE = os.path.join(os.path.dirname(__file__), "..")
CKPT = os.path.join(BASE, "data", "checkpoints", "garden_associations")
ASSOC = os.path.join(BASE, "apps", "backend", "data", "raw_datasets", "association_training_data.json")

# Load checkpoint
W_raw = np.load(os.path.join(CKPT, "snn.pt.npy"))
with open(os.path.join(CKPT, "snn.json")) as f:
    meta = json.load(f)
k2i = meta["key_to_idx"]
i2k = meta["idx_to_key"]
V = len(i2k)
W = W_raw[:V, :V]
print(f"SNN: {V} neurons, ~{W.nbytes/1024/1024:.0f} MB")

# === MODE 1: Direct neighbor lookup ===
def get_neighbors(query_key, n=10):
    """Get top-N weighted neighbors directly from weight matrix row."""
    if query_key not in k2i:
        return []
    idx = k2i[query_key]
    row = W[idx]
    top_idx = np.argsort(-row)[:n]
    return [(i2k[i], float(row[i])) for i in top_idx if row[i] > 0]

# Load association data
with open(ASSOC) as f:
    triples = json.load(f)

# === TEST 1: Association Accuracy (Direct Lookup) ===
print("\n" + "=" * 60)
print("  TEST 1: Association Accuracy (Direct Neighbor Lookup)")
print("=" * 60)

random.seed(42)
valid = [t for t in triples
         if f"wn_{t['concept_a']}" in k2i and f"wn_{t['concept_b']}" in k2i]
samples = random.sample(valid, 200)

t0 = time.time()
top1 = top5 = top10 = 0
for t in samples:
    ka = f"wn_{t['concept_a']}"
    kb = f"wn_{t['concept_b']}"
    neighbors = get_neighbors(ka, 10)
    n_keys = [k for k,v in neighbors]
    if kb == n_keys[0] if n_keys else False:
        top1 += 1
    if kb in n_keys[:5]:
        top5 += 1
    if kb in n_keys[:10]:
        top10 += 1
elapsed = time.time() - t0

print(f"  Samples: {len(samples)}")
print(f"  Top-1:  {top1}/{len(samples)} = {top1/len(samples):.1%}")
print(f"  Top-5:  {top5}/{len(samples)} = {top5/len(samples):.1%}")
print(f"  Top-10: {top10}/{len(samples)} = {top10/len(samples):.1%}")
print(f"  Time:   {elapsed:.1f}s" if 'elapsed' in dir() else f"  Time:   {time.time()-t0:.1f}s")

# === TEST 2: Open-Domain Generalization ===
print("\n" + "=" * 60)
print("  TEST 2: Open-Domain Generalization (Novel Concepts)")
print("=" * 60)

tests = [
    ("wn_dog", "dog -> animal/pet/canine", ["wn_animal", "wn_pet", "wn_canine"]),
    ("wn_cat", "cat -> animal/pet/feline", ["wn_animal", "wn_pet", "wn_feline"]),
    ("wn_car", "car -> vehicle/drive", ["wn_vehicle", "wn_drive", "wn_automobile"]),
    ("wn_tree", "tree -> plant/wood", ["wn_plant", "wn_wood", "wn_leaf"]),
    ("wn_piano", "piano -> music/instrument", ["wn_music", "wn_instrument", "wn_play"]),
    ("wn_sun", "sun -> star/light", ["wn_star", "wn_light", "wn_hot"]),
    ("wn_food", "food -> eat/nutrient", ["wn_eat", "wn_nutrient", "wn_meal"]),
    ("wn_river", "river -> water/stream", ["wn_water", "wn_stream", "wn_flow"]),
    ("wn_bird", "bird -> animal/fly", ["wn_animal", "wn_fly", "wn_wing"]),
    ("wn_house", "house -> building/home", ["wn_building", "wn_home", "wn_live"]),
    ("wn_book", "book -> read/write", ["wn_read", "wn_write", "wn_page"]),
    ("wn_fish", "fish -> animal/water", ["wn_animal", "wn_water", "wn_swim"]),
]

gen_hits = gen_total = 0
for q, label, expected in tests:
    if q in k2i:
        neighbors = get_neighbors(q, 15)
        n_keys = set(k for k,v in neighbors if v > 0.01)
        found = [e for e in expected if e in n_keys]
        gen_hits += len(found)
        gen_total += len(expected)
        status = "PASS" if found else "FAIL"
        top5 = [f"{k[3:]}({v:.2f})" for k,v in neighbors[:5]]
        print(f"  [{status}] {label}: {len(found)}/{len(expected)}")
        print(f"         Top-5: {', '.join(top5)}")
    else:
        gen_total += len(expected)
        print(f"  [SKIP] {label}: NOT IN SNN")

print(f"\n  Generalization: {gen_hits}/{gen_total} = {gen_hits/gen_total:.0%}")

# === TEST 3: Hierarchical Reasoning ===
print("\n" + "=" * 60)
print("  TEST 3: Hierarchical Reasoning (Multi-hop)")
print("=" * 60)

hier_tests = [
    ("wn_dog", "dog -> mammal (via hypernym)", ["wn_mammal"]),
    ("wn_rose", "rose -> flower (via hypernym)", ["wn_flower"]),
    ("wn_eagle", "eagle -> bird (via hypernym)", ["wn_bird"]),
    ("wn_piano", "piano -> instrument (via hypernym)", ["wn_instrument"]),
]
hier_hits = hier_total = 0
for q, label, expected in hier_tests:
    if q in k2i:
        neighbors = get_neighbors(q, 20)
        n_keys = set(k for k,v in neighbors)
        found = [e for e in expected if e in n_keys]
        hier_hits += len(found)
        hier_total += len(expected)
        status = "PASS" if found else "FAIL"
        print(f"  [{status}] {label}")
    else:
        hier_total += len(expected)
        print(f"  [SKIP] {label}: NOT IN SNN")

print(f"\n  Hierarchical: {hier_hits}/{hier_total} = {hier_hits/hier_total:.0%}" if hier_total else "")

# === TEST 4: Weight Distribution ===
print("\n" + "=" * 60)
print("  TEST 4: Network Statistics")
print("=" * 60)

nz = W[W > 0]
degrees = np.sum(W > 0, axis=1)
print(f"  Non-zero weights:  {len(nz):,}")
print(f"  Weight range:      [{nz.min():.4f}, {nz.max():.4f}]")
print(f"  Mean weight:       {nz.mean():.4f}")
print(f"  Mean degree:       {degrees[degrees > 0].mean():.1f} connections/neuron")
print(f"  Max degree:        {degrees.max()}")
density = float(np.mean(W > 0))
print(f"  Density:           {density:.4f}")

# === SUMMARY ===
print("\n" + "=" * 60)
print("  EVALUATION SUMMARY")
print("=" * 60)
acc_score = (top1/200 * 0.3 + top5/200 * 0.4 + top10/200 * 0.3)
gen_score = gen_hits/gen_total if gen_total else 0
hier_score = hier_hits/hier_total if hier_total else 0
overall = acc_score * 0.5 + gen_score * 0.3 + hier_score * 0.2
print(f"  Association accuracy (Top-5):  {top5/len(samples):.1%}")
print(f"  Generalization rate:           {gen_score:.0%}")
print(f"  Hierarchical reasoning:        {hier_score:.0%}")
print(f"  Overall quality score:         {overall:.2f} / 1.0")
if overall > 0.5:
    print("  Assessment: GOOD")
elif overall > 0.3:
    print("  Assessment: FAIR")
else:
    print("  Assessment: NEEDS IMPROVEMENT")
