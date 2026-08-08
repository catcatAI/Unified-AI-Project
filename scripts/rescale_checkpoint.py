"""Rescale row-normalized checkpoint so max incoming signal is ~0.5."""
import numpy as np, json

npy_path = r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.pt.npy"
json_path = r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.json"

W = np.load(npy_path)
V = 10000

with open(json_path) as f:
    meta = json.load(f)
key_to_idx = meta["key_to_idx"]

# Test with known inputs
test_keys = ["m2", "m3", "op1", "m5", "op5"]
active_idx = [key_to_idx[k] for k in test_keys if k in key_to_idx]
live = W[:V, :V]

# Current max incoming
incoming = live[active_idx].sum(axis=0) / len(active_idx)
print(f"Before: max_incoming={incoming.max():.6f}")

# We need max_incoming ~ 0.5 for threshold 0.3 to work
# Scale factor = 0.5 / current_max
scale = 0.5 / max(incoming.max(), 1e-10)
print(f"Scale factor: {scale:.1f}")

# Apply scale while preserving row normalization
live_scaled = live * scale
# Re-normalize rows to sum to at most 1.0
row_sums = np.abs(live_scaled).sum(axis=1, keepdims=True)
row_sums = np.maximum(row_sums, 1.0)
live_scaled = live_scaled / row_sums

W[:V, :V] = live_scaled

# Verify
incoming2 = live_scaled[active_idx].sum(axis=0) / len(active_idx)
print(f"After: max_incoming={incoming2.max():.6f}")
print(f"After: weights max={live_scaled.max():.6f}, mean={live_scaled.mean():.6f}")
row_check = np.abs(live_scaled).sum(axis=1)
print(f"After row sums: min={row_check.min():.4f} max={row_check.max():.4f} mean={row_check.mean():.4f}")
print(f"Neurons above 0.3: {(incoming2 > 0.3).sum()}")
print(f"Neurons above 0.1: {(incoming2 > 0.1).sum()}")

np.save(npy_path, W)
print("Saved")
