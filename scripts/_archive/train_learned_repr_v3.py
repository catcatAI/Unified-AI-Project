"""Learned Representation v3: Fast with smaller dataset."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
LATENT_DIM=64


def load_cifar(n_per_class=50):
    images=[]
    labels=[]
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.shape == (32, 32, 3):
                arr = arr.reshape(-1).astype(np.float32) / 255.0
            elif arr.shape == (3, 32, 32):
                arr = arr.transpose(1, 2, 0).reshape(-1).astype(np.float32) / 255.0
            elif arr.shape == (3072,):
                arr = arr.astype(np.float32) / 255.0
            else:
                continue
            images.append(arr)
            labels.append(ci)
    return np.array(images), np.array(labels)


def main():
    print("Loading CIFAR-10 (50/class)...")
    all_imgs, all_labels = load_cifar(50)
    print(f"Total: {len(all_imgs)} images")

    # Split 80/20
    n_train=400
    train_imgs = all_imgs[:n_train]
    train_labels = all_labels[:n_train]
    test_imgs = all_imgs[n_train:]
    test_labels = all_labels[n_train:]
    print(f"Train: {n_train}, Test: {len(test_imgs)}")

    # PCA encoder (fast: use incremental PCA via random projection)
    print("\n=== Random Projection Encoder ===")
    rng = np.random.default_rng(42)
    # Random projection matrix
    proj = rng.normal(0, 1/np.sqrt(3072), (LATENT_DIM, 3072)).astype(np.float32)
    # Orthogonalize
    Q, _ = np.linalg.qr(proj.T)
    proj = Q.T[:LATENT_DIM].astype(np.float32)

    mean = train_imgs.mean(axis=0)
    train_latent = (train_imgs - mean) @ proj.T
    test_latent = (test_imgs - mean) @ proj.T

    # L2 normalize
    train_norms = np.linalg.norm(train_latent, axis=1, keepdims=True)
    train_norms[train_norms == 0] = 1.0
    train_latent = train_latent / train_norms
    test_norms = np.linalg.norm(test_latent, axis=1, keepdims=True)
    test_norms[test_norms == 0] = 1.0
    test_latent = test_latent / test_norms

    # Linear classifier
    print("Training classifier...")
    n_classes=10
    Y = np.zeros((n_train, n_classes), dtype=np.float32)
    for i, l in enumerate(train_labels):
        Y[i, l] = 1.0
    XtX = train_latent.T @ train_latent + 1e-4 * np.eye(LATENT_DIM)
    W_clf = np.linalg.solve(XtX, train_latent.T @ Y)

    preds = np.argmax(test_latent @ W_clf, axis=1)
    correct = np.sum(preds == test_labels)
    print(f"Recognition: {correct}/{len(test_labels)} = {correct/len(test_labels):.1%}")

    # Linear decoder (fast gradient descent)
    print("\n=== Linear Decoder ===")
    W_dec = rng.normal(0, 0.01, (3072, LATENT_DIM)).astype(np.float32)
    b_dec = np.zeros(3072, dtype=np.float32)

    lr=0.001
    batch_size=64
    n_epochs=30
    t_start = time.time()

    for epoch in range(n_epochs):
        perm = np.random.permutation(n_train)
        total_loss=0.0
        n_batches=0
        for i in range(0, n_train, batch_size):
            idx = perm[i:i+batch_size]
            x = train_latent[idx]
            y = train_imgs[idx]

            recon=1.0 / (1.0 + np.exp(-np.clip(x @ W_dec.T + b_dec, -10, 10)))
            loss = np.mean((recon - y) ** 2)

            error = recon - y
            grad_W = error.T @ x / len(x)
            grad_b = error.mean(axis=0)
            W_dec -= lr * grad_W
            b_dec -= lr * grad_b

            total_loss += loss
            n_batches += 1

        if (epoch + 1) % 10 == 0:
            print(f"  Epoch {epoch+1}: MSE={total_loss/n_batches:.4f} ({time.time()-t_start:.0f}s)")

    # Test reconstruction
    print("\n=== Reconstruction ===")
    output_dir="data/multimodal/gvv/learned_test"
    os.makedirs(output_dir, exist_ok=True)

    total_mse=0.0
    for i in range(10):
        recon=1.0 / (1.0 + np.exp(-np.clip(test_latent[i] @ W_dec.T + b_dec, -10, 10)))
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
        gen=1.0 / (1.0 + np.exp(-np.clip(center @ W_dec.T + b_dec, -10, 10)))
        gen = gen.reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(output_dir, f"gen_{cls}.png"))
        print(f"  Generated {cls}")

    # Random generation
    for i in range(5):
        z = rng.standard_normal(LATENT_DIM).astype(np.float32)
        z = z / np.linalg.norm(z)
        gen=1.0 / (1.0 + np.exp(-np.clip(z @ W_dec.T + b_dec, -10, 10)))
        gen = gen.reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(output_dir, f"gen_random_{i}.png"))
    print("Generated 5 random images")
    print(f"\nAll images → {output_dir}/")


if __name__ == "__main__":
    main()
