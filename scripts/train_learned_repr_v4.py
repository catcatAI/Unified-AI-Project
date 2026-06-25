"""Learned Representation v4: PCA encoder + linear decoder."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
LATENT_DIM = 64


def load_cifar(n_per_class=50):
    images = []
    labels = []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.ndim == 3:
                arr = arr.reshape(-1)
            images.append(arr.astype(np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def main():
    print("Loading CIFAR-10 (50/class)...")
    all_imgs, all_labels = load_cifar(50)
    print(f"Total: {len(all_imgs)}")

    # Stratified split
    rng = np.random.default_rng(42)
    train_idx = []
    test_idx = []
    for c in range(10):
        idxs = np.where(all_labels == c)[0]
        rng.shuffle(idxs)
        train_idx.extend(idxs[:40])
        test_idx.extend(idxs[40:50])
    train_imgs = all_imgs[train_idx]
    train_labels = all_labels[train_idx]
    test_imgs = all_imgs[test_idx]
    test_labels = all_labels[test_idx]
    print(f"Train: {len(train_imgs)}, Test: {len(test_imgs)}")

    # PCA encoder
    print("\n=== PCA Encoder ===")
    mean = train_imgs.mean(axis=0)
    centered = train_imgs - mean
    t0 = time.time()
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    proj = Vt[:LATENT_DIM]  # (64, 3072)
    explained = (S[:LATENT_DIM] ** 2).sum() / (S ** 2).sum()
    print(f"PCA: {LATENT_DIM} dims, {explained:.1%} variance ({time.time()-t0:.1f}s)")

    train_latent = centered @ proj.T  # (400, 64)
    test_latent = (test_imgs - mean) @ proj.T

    # L2 normalize
    tn = np.linalg.norm(train_latent, axis=1, keepdims=True)
    tn[tn == 0] = 1.0
    train_latent_n = train_latent / tn
    tt = np.linalg.norm(test_latent, axis=1, keepdims=True)
    tt[tt == 0] = 1.0
    test_latent_n = test_latent / tt

    # Classifier
    print("\n=== Classifier ===")
    Y = np.zeros((len(train_latent_n), 10), dtype=np.float32)
    for i, l in enumerate(train_labels):
        Y[i, l] = 1.0
    W_clf = np.linalg.solve(train_latent_n.T @ train_latent_n + 1e-4 * np.eye(LATENT_DIM),
                            train_latent_n.T @ Y)
    preds = np.argmax(test_latent_n @ W_clf, axis=1)
    correct = np.sum(preds == test_labels)
    print(f"Recognition: {correct}/{len(test_labels)} = {correct/len(test_labels):.1%}")

    # Linear decoder (analytical solution, no gradient descent needed)
    print("\n=== Linear Decoder (analytical) ===")
    # Solve: W_dec @ latent ≈ image → W_dec = image @ latent^+ (pseudoinverse)
    # W_dec = (image^T @ latent) @ (latent^T @ latent + reg)^{-1}
    reg = 1.0
    LtL = train_latent.T @ train_latent + reg * np.eye(LATENT_DIM)
    LtX = train_latent.T @ train_imgs  # (64, 3072)
    W_dec = np.linalg.solve(LtL, LtX).T  # (3072, 64)
    b_dec = train_imgs.mean(axis=0) - (train_latent.mean(axis=0) @ W_dec.T)

    # Test reconstruction
    print("\n=== Reconstruction ===")
    output_dir = "data/multimodal/gvv/learned_test"
    os.makedirs(output_dir, exist_ok=True)

    total_mse = 0.0
    for i in range(10):
        raw = test_latent[i] @ W_dec.T + b_dec
        recon = 1.0 / (1.0 + np.exp(-np.clip(raw, -10, 10)))
        recon = recon.reshape(32, 32, 3)
        orig = test_imgs[i].reshape(32, 32, 3)
        mse = np.mean((recon - orig) ** 2)
        total_mse += mse
        Image.fromarray((orig * 255).astype(np.uint8)).save(os.path.join(output_dir, f"orig_{i}.png"))
        Image.fromarray((recon * 255).astype(np.uint8)).save(os.path.join(output_dir, f"recon_{i}.png"))
        print(f"  Image {i}: MSE={mse:.4f}")
    print(f"Average MSE: {total_mse/10:.4f}")

    # Generate from class centers
    print("\n=== Generation from Class Centers ===")
    for ci, cls in enumerate(CLASSES):
        mask = train_labels == ci
        center = train_latent[mask].mean(axis=0)
        raw = center @ W_dec.T + b_dec
        gen = 1.0 / (1.0 + np.exp(-np.clip(raw, -10, 10)))
        gen = gen.reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(output_dir, f"gen_{cls}.png"))
        print(f"  Generated {cls}")

    # Random generation
    for i in range(5):
        z = rng.standard_normal(LATENT_DIM).astype(np.float32)
        z = z / np.linalg.norm(z)
        raw = z @ W_dec.T + b_dec
        gen = 1.0 / (1.0 + np.exp(-np.clip(raw, -10, 10)))
        gen = gen.reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(output_dir, f"gen_random_{i}.png"))
    print("Generated 5 random images")
    print(f"\nAll → {output_dir}/")


if __name__ == "__main__":
    main()
