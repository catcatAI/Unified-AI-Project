"""Verify SNN fix: different inputs should produce different outputs."""
import sys, time, numpy as np
sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")

from ai.garden.snn_core import TensorSNNCore, DEFAULT_THRESHOLD

def main():
    print("=== SNN Fix Verification ===")
    print(f"Default threshold: {DEFAULT_THRESHOLD}")

    # Create a fresh SNN and simulate training
    snn = TensorSNNCore(max_vocab=500, connection_budget=5000)
    snn.base_threshold = DEFAULT_THRESHOLD

    # Register some keys
    keys = ["m1", "m2", "m3", "op1", "op5", "true", "false", "or", "not", "hello"]
    for k in keys:
        snn._register_key(k)

    # Add some relations (simulating dictionary presets)
    snn.add_relation("m1", "op1", weight=0.3)
    snn.add_relation("m2", "op1", weight=0.3)
    snn.add_relation("op1", "m3", weight=0.3)
    snn.add_relation("m3", "op5", weight=0.3)
    snn.add_relation("true", "or", weight=0.3)
    snn.add_relation("false", "or", weight=0.3)
    snn.add_relation("or", "not", weight=0.3)

    # Simulate Hebbian training with new defaults (target=0.35, decay=0.001)
    print("\n--- Training with new parameters ---")
    for epoch in range(5):
        d1 = snn.hebbian_update(["m1", "m2", "op1", "m3", "op5"], ["m1", "m2", "op1", "m3", "op5"],
                                lr=0.05, target_strength=0.35, weight_decay=0.001)
        d2 = snn.hebbian_update(["true", "false", "or"], ["true", "false", "or"],
                                lr=0.05, target_strength=0.35, weight_decay=0.001)
        d3 = snn.hebbian_update(["hello"], ["hello"],
                                lr=0.05, target_strength=0.35, weight_decay=0.001)

    stats = snn.get_stats()
    print(f"After training: density={stats['matrix_density']*100:.1f}%, "
          f"mean_weight={stats['mean_weight']:.4f}, "
          f"hebbian={stats['total_hebbian_updates']}")

    # Test forward with different inputs
    print("\n--- Forward pass tests ---")
    test_cases = [
        (["m1", "m2", "op1"], "math: 1+2"),
        (["true", "false", "or"], "logic: true OR false"),
        (["hello"], "greeting: hello"),
    ]

    for input_keys, label in test_cases:
        t0 = time.time()
        result = snn.forward(input_keys)
        elapsed = time.time() - t0
        top5 = sorted(result.items(), key=lambda x: -x[1])[:5]
        print(f"[{label:25s}] active={len(result):4d} top5={top5} ({elapsed:.3f}s)")

    # Key check: different inputs should activate DIFFERENT neurons
    r1 = snn.forward(["m1", "m2", "op1"])
    r2 = snn.forward(["true", "false", "or"])
    r3 = snn.forward(["hello"])

    overlap_12 = len(set(r1.keys()) & set(r2.keys()))
    overlap_13 = len(set(r1.keys()) & set(r3.keys()))
    overlap_23 = len(set(r2.keys()) & set(r3.keys()))

    print(f"\n--- Differentiation check ---")
    print(f"math vs logic overlap:  {overlap_12}/{min(len(r1), len(r2))} "
          f"({overlap_12/max(1,min(len(r1),len(r2)))*100:.0f}%)")
    print(f"math vs greeting overlap: {overlap_13}/{min(len(r1), len(r3))} "
          f"({overlap_13/max(1,min(len(r1),len(r3)))*100:.0f}%)")
    print(f"logic vs greeting overlap: {overlap_23}/{min(len(r2), len(r3))} "
          f"({overlap_23/max(1,min(len(r2),len(r3)))*100:.0f}%)")

    # Test with loaded (saturated) checkpoint
    print("\n--- Loading existing saturated checkpoint ---")
    snn2 = TensorSNNCore(max_vocab=10000, connection_budget=50000)
    snn2.load(r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.pt")
    stats2 = snn2.get_stats()
    print(f"Before reset: density={stats2['matrix_density']*100:.1f}%, "
          f"mean_weight={stats2['mean_weight']:.4f}")

    r_old_math = snn2.forward(["m1", "m2", "op1"])
    r_old_logic = snn2.forward(["true", "false", "or"])
    overlap_old = len(set(r_old_math.keys()) & set(r_old_logic.keys()))
    total_active = max(len(r_old_math), 1)
    print(f"Before reset: math vs logic overlap={overlap_old}/{total_active} "
          f"({overlap_old/total_active*100:.0f}%) — SAME output = saturated")

    # Reset and test
    snn2.reset_for_retrain()
    stats3 = snn2.get_stats()
    print(f"\nAfter reset: density={stats3['matrix_density']*100:.1f}%, "
          f"mean_weight={stats3['mean_weight']:.4f}")

    r_new_math = snn2.forward(["m1", "m2", "op1"])
    r_new_logic = snn2.forward(["true", "false", "or"])
    overlap_new = len(set(r_new_math.keys()) & set(r_new_logic.keys()))
    total_new = max(min(len(r_new_math), len(r_new_logic)), 1)
    print(f"After reset: math vs logic overlap={overlap_new}/{total_new} "
          f"({overlap_new/total_new*100:.0f}%)" if total_new > 0 else "After reset: no active neurons")


if __name__ == "__main__":
    main()
