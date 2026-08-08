import sys
sys.path.insert(0, r"D:\Projects\Unified-AI-Project\apps\backend\src")
from ai.garden.snn_core import TensorSNNCore, DEFAULT_THRESHOLD

if __name__ == "__main__":
    print("SNN import OK, threshold=%s" % DEFAULT_THRESHOLD)

    snn = TensorSNNCore(max_vocab=100)
    snn._register_key("a")
    snn._register_key("b")
    snn.add_relation("a", "b", weight=0.3)
    d = snn.hebbian_update(["a"], ["b"], lr=0.05, target_strength=0.35, weight_decay=0.002)
    print("hebbian_update: delta=%.4f" % d)
    out = snn.forward(["a"])
    print("forward(a): %d active" % len(out))
    stats = snn.get_stats()
    print("stats: density=%.4f, mean_w=%.4f" % (stats["matrix_density"], stats["mean_weight"]))
    print("All OK")
