"""Three-Layer Architecture: Compare PCA dimensions (128/256/512/3072)."""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
IMG_DIM=3072
OUTPUT_BASE="data/multimodal/gvv/pca_compare"


def load_cifar(n_per_class=50):
    images, labels=[], []
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
    import torch
    import torch.nn as nn

    print("Loading CIFAR-10 (50/class)...")
    all_imgs, all_labels = load_cifar(50)
    print(f"Total: {len(all_imgs)}")

    rng = np.random.default_rng(42)
    train_idx, test_idx=[], []
    for c in range(10):
        idxs = np.where(all_labels == c)[0]
        rng.shuffle(idxs)
        train_idx.extend(idxs[:40])
        test_idx.extend(idxs[40:50])
    train_imgs, train_labels = all_imgs[train_idx], all_labels[train_idx]
    test_imgs, test_labels = all_imgs[test_idx], all_labels[test_idx]
    print(f"Train: {len(train_imgs)}, Test: {len(test_imgs)}")

    # PCA
    print("\n=== PCA Encoding ===")
    mean = train_imgs.mean(axis=0)
    centered = train_imgs - mean
    t0 = time.time()
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    pca_time = time.time() - t0
    explained_all = (S ** 2).sum()
    print(f"SVD done: {pca_time:.1f}s")

    dims_to_test=[128, 256, 512, 3072]
    results={}

    for LATENT_DIM in dims_to_test:
        if LATENT_DIM > len(S):
            print(f"\n--- {LATENT_DIM} dims: SKIPPED (only {len(S)} components) ---")
            continue

        print(f"\n{'='*50}")
        print(f"=== PCA {LATENT_DIM} dims ===")
        print(f"{'='*50}")

        proj = Vt[:LATENT_DIM]
        explained = (S[:LATENT_DIM] ** 2).sum() / explained_all
        print(f"Variance: {explained:.2%}")

        train_latent = centered @ proj.T
        test_latent = (test_imgs - mean) @ proj.T

        # Classifier
        Y = np.zeros((len(train_latent), 10), dtype=np.float32)
        for i, l in enumerate(train_labels):
            Y[i, l] = 1.0
        W_clf = np.linalg.solve(train_latent.T @ train_latent + 1e-4 * np.eye(LATENT_DIM),
                                train_latent.T @ Y)
        preds = np.argmax(test_latent @ W_clf, axis=1)
        acc = np.sum(preds == test_labels) / len(test_labels)
        print(f"Recognition: {acc:.1%}")

        # Decoder
        class Decoder(nn.Module):
            def __init__(self, latent_dim):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(latent_dim, 256),
                    nn.ReLU(),
                    nn.Linear(256, 512),
                    nn.ReLU(),
                    nn.Linear(512, IMG_DIM),
                    nn.Sigmoid(),
                )
            def forward(self, x):
                return self.net(x)

        decoder = Decoder(LATENT_DIM)
        optimizer = torch.optim.Adam(decoder.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        X_train = torch.tensor(train_latent, dtype=torch.float32)
        Y_train = torch.tensor(train_imgs, dtype=torch.float32)

        batch_size=64
        n_epochs=100
        t0 = time.time()

        for epoch in range(n_epochs):
            perm = torch.randperm(len(X_train))
            total_loss=0.0
            n_batches=0
            for i in range(0, len(X_train), batch_size):
                idx = perm[i:i+batch_size]
                x, y = X_train[idx], Y_train[idx]
                recon = decoder(x)
                loss = criterion(recon, y)
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                n_batches += 1
            if (epoch + 1) % 25 == 0:
                print(f"  Epoch {epoch+1}: MSE={total_loss/n_batches:.4f}")

        train_time = time.time() - t0

        # Test reconstruction
        decoder.eval()
        with torch.no_grad():
            X_test = torch.tensor(test_latent, dtype=torch.float32)
            test_recon = decoder(X_test).numpy()

        total_mse = np.mean((test_recon - test_imgs) ** 2)
        print(f"Test MSE: {total_mse:.4f} ({train_time:.0f}s)")

        # Save images for comparison
        out_dir = os.path.join(OUTPUT_BASE, f"dims_{LATENT_DIM}")
        os.makedirs(out_dir, exist_ok=True)

        # Save first 10 reconstructions side by side
        for i in range(10):
            orig = (test_imgs[i].reshape(32, 32, 3) * 255).astype(np.uint8)
            recon = (test_recon[i].reshape(32, 32, 3) * 255).astype(np.uint8)
            # Side by side: original | reconstruction
            combo = Image.new('RGB', (64, 32))
            combo.paste(Image.fromarray(orig), (0, 0))
            combo.paste(Image.fromarray(recon), (32, 0))
            combo.save(os.path.join(out_dir, f"pair_{i}.png"))

        # Class center generation
        with torch.no_grad():
            class_centers = np.zeros((10, LATENT_DIM), dtype=np.float32)
            for c in range(10):
                mask = train_labels == c
                class_centers[c] = train_latent[mask].mean(axis=0)
            gen = decoder(torch.tensor(class_centers, dtype=torch.float32)).numpy()
        for ci, cls in enumerate(CLASSES):
            img = (gen[ci].reshape(32, 32, 3) * 255).astype(np.uint8)
            Image.fromarray(img).save(os.path.join(out_dir, f"gen_{cls}.png"))

        results[LATENT_DIM] = {
            'mse': total_mse,
            'acc': acc,
            'variance': explained,
            'train_time': train_time,
        }

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Dims':<8} {'Variance':<12} {'MSE':<10} {'Acc':<8} {'Time':<10}")
    print("-" * 50)
    for d, r in results.items():
        print(f"{d:<8} {r['variance']:<12.2%} {r['mse']:<10.4f} {r['acc']:<8.1%} {r['train_time']:<10.0f}s")
    print(f"\nImages → {OUTPUT_BASE}/")


if __name__ == "__main__":
    main()
