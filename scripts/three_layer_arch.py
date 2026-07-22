"""Three-Layer Architecture: CLIP → PCA → Decoder.

Uses torch autograd for fast decoder training (no finite differences).
Shows concept space captures geometric essence of each class.
"""
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
LATENT_DIM=128
IMG_DIM=3072
OUTPUT_DIR="data/multimodal/gvv/three_layer_test"


def load_cifar(n_per_class=50):
    images=[]
    labels=[]
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

    # Stratified split
    rng = np.random.default_rng(42)
    train_idx=[]
    test_idx=[]
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

    # === Step 1: PCA Encoder ===
    print("\n=== PCA Encoder ===")
    mean = train_imgs.mean(axis=0)
    centered = train_imgs - mean
    t0 = time.time()
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    proj = Vt[:LATENT_DIM]
    explained = (S[:LATENT_DIM] ** 2).sum() / (S ** 2).sum()
    print(f"PCA: {LATENT_DIM} dims, {explained:.1%} variance ({time.time()-t0:.1f}s)")

    train_latent = centered @ proj.T
    test_latent = (test_imgs - mean) @ proj.T

    # === Step 2: Linear Classifier ===
    print("\n=== Linear Classifier ===")
    Y = np.zeros((len(train_latent), 10), dtype=np.float32)
    for i, l in enumerate(train_labels):
        Y[i, l] = 1.0
    W_clf = np.linalg.solve(train_latent.T @ train_latent + 1e-4 * np.eye(LATENT_DIM),
                            train_latent.T @ Y)
    preds = np.argmax(test_latent @ W_clf, axis=1)
    correct = np.sum(preds == test_labels)
    print(f"Recognition: {correct}/{len(test_labels)} = {correct/len(test_labels):.1%}")

    # === Step 3: Nonlinear Decoder (torch) ===
    print("\n=== Nonlinear Decoder (torch autograd) ===")

    class Decoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(LATENT_DIM, 256),
                nn.ReLU(),
                nn.Linear(256, 512),
                nn.ReLU(),
                nn.Linear(512, IMG_DIM),
                nn.Sigmoid(),
            )
        def forward(self, x):
            return self.net(x)

    decoder = Decoder()
    optimizer = torch.optim.Adam(decoder.parameters(), lr=0.001)
    criterion = nn.MSELoss()

    # Convert to torch
    X_train = torch.tensor(train_latent, dtype=torch.float32)
    Y_train = torch.tensor(train_imgs, dtype=torch.float32)
    X_test = torch.tensor(test_latent, dtype=torch.float32)

    # Train
    batch_size=64
    n_epochs=100
    t0 = time.time()

    for epoch in range(n_epochs):
        perm = torch.randperm(len(X_train))
        total_loss=0.0
        n_batches=0

        for i in range(0, len(X_train), batch_size):
            idx = perm[i:i+batch_size]
            x = X_train[idx]
            y = Y_train[idx]

            recon = decoder(x)
            loss = criterion(recon, y)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            n_batches += 1

        if (epoch + 1) % 20 == 0:
            avg = total_loss / n_batches
            elapsed = time.time() - t0
            print(f"  Epoch {epoch+1}: MSE={avg:.4f} ({elapsed:.0f}s)")

    # === Test reconstruction ===
    print("\n=== Reconstruction Quality ===")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    decoder.eval()
    with torch.no_grad():
        test_recon = decoder(X_test).numpy()

    total_mse=0.0
    for i in range(10):
        orig = test_imgs[i].reshape(32, 32, 3)
        recon = test_recon[i].reshape(32, 32, 3)
        mse = np.mean((recon - orig) ** 2)
        total_mse += mse
        Image.fromarray((orig * 255).astype(np.uint8)).save(os.path.join(OUTPUT_DIR, f"orig_{i}.png"))
        Image.fromarray((recon * 255).astype(np.uint8)).save(os.path.join(OUTPUT_DIR, f"recon_{i}.png"))
        print(f"  Image {i}: MSE={mse:.4f}")
    print(f"Average MSE: {total_mse/10:.4f}")

    # === Generate from class centers ===
    print("\n=== Generation from Class Centers ===")
    class_centers = np.zeros((10, LATENT_DIM), dtype=np.float32)
    for c in range(10):
        mask = train_labels == c
        class_centers[c] = train_latent[mask].mean(axis=0)

    with torch.no_grad():
        center_tensors = torch.tensor(class_centers, dtype=torch.float32)
        gen_from_centers = decoder(center_tensors).numpy()

    for ci, cls in enumerate(CLASSES):
        gen = gen_from_centers[ci].reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(OUTPUT_DIR, f"gen_{cls}.png"))
        print(f"  Generated {cls}")

    # === Generate from interpolation ===
    print("\n=== Interpolation: airplane → cat ===")
    n_interp=10
    airplane_center = class_centers[0]
    cat_center = class_centers[3]
    alphas = np.linspace(0, 1, n_interp)
    interp_vecs = np.array([alpha * cat_center + (1 - alpha) * airplane_center for alpha in alphas],
                           dtype=np.float32)

    with torch.no_grad():
        interp_gen = decoder(torch.tensor(interp_vecs)).numpy()

    for i in range(n_interp):
        gen = interp_gen[i].reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(OUTPUT_DIR, f"interp_{i}.png"))
    print(f"  Saved {n_interp} interpolation images")

    # === Random generation ===
    print("\n=== Random Generation ===")
    for i in range(5):
        z = rng.standard_normal(LATENT_DIM).astype(np.float32)
        z = z / np.linalg.norm(z) * np.sqrt(LATENT_DIM)
        with torch.no_grad():
            gen = decoder(torch.tensor(z.reshape(1, -1), dtype=torch.float32)).numpy()[0].reshape(32, 32, 3)
        Image.fromarray((gen * 255).astype(np.uint8)).save(os.path.join(OUTPUT_DIR, f"gen_random_{i}.png"))
    print("Generated 5 random images")

    # === Visualize PCA components as "learned primitives" ===
    print("\n=== PCA Components as Learned Primitives ===")
    for i in range(10):
        comp = proj[i].reshape(32, 32, 3)
        comp = (comp - comp.min()) / (comp.max() - comp.min() + 1e-8)
        Image.fromarray((comp * 255).astype(np.uint8)).save(os.path.join(OUTPUT_DIR, f"pca_comp_{i}.png"))
    print("Saved 10 PCA components")

    print(f"\nAll images → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
