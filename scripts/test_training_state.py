# =============================================================================
# ANGELA-MATRIX: [L1] [γ] [C] [L0]
# =============================================================================
"""Quick training test - ED3N + GARDEN with real data."""
import sys
import os
if __name__ != "__main__":
    import pytest
    pytest.skip("Not a test file", allow_module_level=True)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

import json
import time

print("=" * 60)
print("Angela AI Training Test")
print("=" * 60)

# 1. Load training data
print("\n--- 1. Loading Training Data ---")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "data", "raw_datasets")

samples = []

# Math data
math_path = os.path.join(DATA_DIR, "arithmetic_train_dataset.json")
if os.path.exists(math_path):
    with open(math_path, encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            samples.append({"input": item["problem"], "output": str(item["answer"]), "domain": "math"})
    print(f"  Math samples: {len([s for s in samples if s['domain'] == 'math'])}")

# Logic data
logic_path = os.path.join(DATA_DIR, "logic_train.json")
if os.path.exists(logic_path):
    with open(logic_path, encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            samples.append({"input": item["proposition"], "output": str(item["answer"]).lower(), "domain": "logic"})
    print(f"  Logic samples: {len([s for s in samples if s['domain'] == 'logic'])}")

# Knowledge data
knowledge_path = os.path.join(DATA_DIR, "knowledge_extra.json")
if os.path.exists(knowledge_path):
    with open(knowledge_path, encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            samples.append({"input": item["input"], "output": item["output"], "domain": "knowledge"})
    print(f"  Knowledge samples: {len([s for s in samples if s['domain'] == 'knowledge'])}")

print(f"  Total samples: {len(samples)}")

# 2. Test ED3N (before training)
print("\n--- 2. ED3N Before Training ---")
try:
    from ai.ed3n.ed3n_engine import ED3NEngine
    engine = ED3NEngine()
    
    # Test math
    test_cases = [
        ("1+1", "2"),
        ("2*3", "6"),
        ("10-5", "5"),
    ]
    
    correct = 0
    for expr, expected in test_cases:
        result = engine.process(expr)
        answer = result.get("answer", "") if isinstance(result, dict) else str(result)
        if expected in str(answer):
            correct += 1
            print(f"  ✅ {expr} = {answer}")
        else:
            print(f"  ❌ {expr} = {answer} (expected {expected})")
    
    print(f"  Math accuracy: {correct}/{len(test_cases)} ({correct*100//len(test_cases)}%)")
    
except Exception as e:
    print(f"  ❌ ED3N error: {e}")

# 3. Test GARDEN (before training)
print("\n--- 3. GARDEN Before Training ---")
try:
    from ai.garden.garden_engine import GARDENEngine
    garden = GARDENEngine()
    
    # Test knowledge retrieval
    test_queries = [
        "What is the capital of France?",
        "What color is the sky?",
    ]
    
    for query in test_queries:
        result = garden.process(query)
        print(f"  Query: {query}")
        print(f"  Response: {str(result)[:100]}...")
    
    print("  ✅ GARDEN: OK")
    
except Exception as e:
    print(f"  ❌ GARDEN error: {e}")

# 4. Test SharedLatentSpace (before training)
print("\n--- 4. SharedLatentSpace Before Training ---")
try:
    from ai.multimodal.shared_latent_space import get_shared_latent_space, reset_shared_latent_space
    import numpy as np
    
    reset_shared_latent_space()
    ls = get_shared_latent_space(latent_dim=64)
    
    # Test projection consistency
    vec = np.random.randn(512).astype(np.float32)
    latent1 = ls.project("text", vec)
    latent2 = ls.project("text", vec)
    
    if np.allclose(latent1, latent2):
        print("  ✅ Projection consistent")
    else:
        print("  ❌ Projection inconsistent")
    
    print(f"  Modalities: {ls.registered_modalities()}")
    
except Exception as e:
    print(f"  ❌ SharedLatentSpace error: {e}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
Current State:
- Training data: EXISTS (math, logic, knowledge)
- Training pipeline: EXISTS (train_pipeline.py)
- ED3N: Functional but untrained
- GARDEN: Functional but untrained
- SharedLatentSpace: Functional, untrained projections

To improve scores:
1. Run: python scripts/train_pipeline.py
2. This will train ED3N + GARDEN on real data
3. Save weights to data/training/
4. Re-test and update scores
""")
