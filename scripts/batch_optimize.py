"""
Batch direct optimization of CIFAR-10 images using differentiable renderer.
Uses lightweight finite differences (10 probes, 15 iterations).
For training the decomposer on optimized vectors.
"""
import sys
import os
import time
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer",
           "dog", "frog", "horse", "ship", "truck"]
NUM_IMAGES = 50
N_ITERS = 15
LR = 0.008
N_PROBES = 10


def load_random_images(n):
    all_files = []
    all_labels = []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))
        for f in files:
            all_files.append(f)
            all_labels.append(ci)

    indices = np.random.choice(len(all_files), n, replace=False)
    images = []
    labels = []
    for idx in indices:
        arr = np.load(all_files[idx])
        if arr.shape == (3072,):
            arr = arr.reshape(3, 32, 32).transpose(1, 2, 0)
        elif arr.shape == (3, 32, 32):
            arr = arr.transpose(1, 2, 0)
        # Resize to 128x128
        from PIL import Image
        pil_img = Image.fromarray(arr).resize((128, 128), Image.LANCZOS)
        arr = np.array(pil_img, dtype=np.float32) / 255.0
        images.append(arr)
        labels.append(all_labels[idx])
    return images, labels


def optimize_one(target, renderer):
    vec = np.random.uniform(0.2, 0.8, TOTAL_DIM).astype(np.float32)
    vec[0:3] = target.mean(axis=(0, 1))

    best_vec = vec.copy()
    best_loss = float('inf')
    eps = 0.015

    for it in range(N_ITERS):
        rendered = renderer.render(vec)
        loss = float(np.mean((rendered - target) ** 2))

        if loss < best_loss:
            best_loss = loss
            best_vec = vec.copy()

        d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
        probe_dims = np.random.choice(TOTAL_DIM, size=N_PROBES, replace=False)

        for dim in probe_dims:
            v_plus = vec.copy()
            v_plus[dim] = min(1.0, v_plus[dim] + eps)
            r_plus = renderer.render(v_plus)
            l_plus = np.mean((r_plus - target) ** 2)

            v_minus = vec.copy()
            v_minus[dim] = max(0.0, v_minus[dim] - eps)
            r_minus = renderer.render(v_minus)
            l_minus = np.mean((r_minus - target) ** 2)

            d_vec[dim] = (l_plus - l_minus) / (2 * eps)

        vec -= LR * d_vec
        vec = np.clip(vec, 0, 1)

    return best_vec, best_loss


def main():
    print(f"Loading {NUM_IMAGES} random CIFAR-10 images...")
    images, labels = load_random_images(NUM_IMAGES)
    print(f"Loaded {len(images)} images, shape={images[0].shape}")

    diff_renderer = DifferentiableRenderer((128, 128))
    pil_renderer = PrimitiveRenderer((128, 128))

    optimized_vecs = []
    losses = []
    t_start = time.time()

    for i in range(NUM_IMAGES):
        t0 = time.time()
        opt_vec, opt_loss = optimize_one(images[i], diff_renderer)
        optimized_vecs.append(opt_vec)
        losses.append(opt_loss)
        elapsed = time.time() - t0

        # Compute PIL similarity for reporting
        instructions = DrawingInstructions.from_vector(opt_vec, canvas_size=(128, 128))
        rendered_pil = pil_renderer.render(instructions)
        orig_pil = __import__('PIL').Image.fromarray((images[i] * 255).astype(np.uint8))

        # Cosine similarity
        r_arr = np.array(rendered_pil, dtype=np.float32).flatten()
        o_arr = np.array(orig_pil, dtype=np.float32).flatten()
        cos_sim = float(np.dot(r_arr, o_arr) / (np.linalg.norm(r_arr) * np.linalg.norm(o_arr) + 1e-8))

        if (i + 1) % 5 == 0:
            total_elapsed = time.time() - t_start
            print(f"  [{i+1}/{NUM_IMAGES}] loss={opt_loss:.4f} cos_sim={cos_sim:.4f} ({elapsed:.1f}s/img, total={total_elapsed:.0f}s)")

    # Save
    save_dir = os.path.join(CIFAR_DIR)
    np.save(os.path.join(save_dir, "optimized_vectors.npy"), np.array(optimized_vecs))
    np.save(os.path.join(save_dir, "optimized_labels.npy"), np.array(labels))

    print(f"\nDone! {len(optimized_vecs)} vectors saved")
    print(f"Average loss: {np.mean(losses):.4f}")
    print(f"Total time: {time.time() - t_start:.0f}s")


if __name__ == "__main__":
    main()
