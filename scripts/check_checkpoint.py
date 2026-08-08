"""Reconstruct original checkpoint from saved weights + JSON metadata."""
import numpy as np, json, os

npy_path = r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.pt.npy"
json_path = r"D:\Projects\Unified-AI-Project\data\checkpoints\garden_checkpoint\snn.json"

# The .npy was modified in-place. We need the original.
# Check if there's a backup from the training run
backup_dir = r"D:\Projects\Unified-AI-Project\data\checkpoints"
for f in os.listdir(backup_dir):
    if "snn" in f and f != "snn.pt.npy" and f != "snn.json":
        print(f"Found: {f}")

# The original had max=0.9711, mean=0.044281, nnz=85409381
# After row-normalization: max=0.0516, mean=0.000093
# We need to restore the original scale

W = np.load(npy_path)
V = 10000
live = W[:V, :V]
print(f"Current: max={live.max():.4f}, mean={live.mean():.6f}")

# Since we know the original stats, we can't reconstruct exactly.
# But we can use the row-normalized version with a better forward pass.
# The key insight: with row-normalized weights, use sum(active_inputs) as threshold scale.

print("Using row-normalized checkpoint with adaptive forward pass.")
print("The forward pass will normalize signal by number of active inputs.")
