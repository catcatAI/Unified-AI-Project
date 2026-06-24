"""Compare decoder sizes on PCA 128 dims."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
IMG_DIM = 3072
LATENT_DIM = 128
OUTPUT_BASE = "data/multimodal/gvv/decoder_compare"


def load_cifar(n_per_class=50):
    images, labels = [], []
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

    rng = np.random.default_rng(42)
    train_idx, test_idx = [], []
    for c in range(10):
        idxs = np.where(all_labels == c)[0]
        rng.shuffle(idxs)
        train_idx.extend(idxs[:40])
        test_idx.extend(idxs[40:50])
    train_imgs, train_labels = all_imgs[train_idx], all_labels[train_idx]
    test_imgs, test_labels = all_imgs[test_idx], all_labels[test_idx]

    # PCA
    print("PCA encoding...")
    mean = train_imgs.mean(axis=0)
    centered = train_imgs - mean
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    proj = Vt[:LATENT_DIM]
    train_latent = centered @ proj.T
    test_latent = (test_imgs - mean) @ proj.T

    X_train = torch.tensor(train_latent, dtype=torch.float32)
    Y_train = torch.tensor(train_imgs, dtype=torch.float32)
    X_test = torch.tensor(test_latent, dtype=torch.float32)

    # Decoder configs
    configs = {
        "small_2layer": [256, 512],
        "large_3layer": [512, 1024, 1024],
        "xlarge_4layer": [512, 1024, 1024, 1024],
    }

    results = {}

    for name, hidden_dims in configs.items():
        print(f"\n{'='*50}")
        print(f"=== {name}: {hidden_dims} ===")
        print(f"{'='*50}")

        layers = []
        in_dim = LATENT_DIM
        for h in hidden_dims:
            layers.extend([nn.Linear(in_dim, h), nn.ReLU()])
            in_dim = h
        layers.extend([nn.Linear(in_dim, IMG_DIM), nn.Sigmoid()])

        decoder = nn.Sequential(*layers)
        n_params = sum(p.numel() for p in decoder.parameters())
        print(f"Parameters: {n_params:,}")

        optimizer = torch.optim.Adam(decoder.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        batch_size = 64
        n_epochs = 50
        t0 = time.time()

        for epoch in range(n_epochs):
            perm = torch.randperm(len(X_train))
            total_loss = 0.0
            n_batches = 0
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

        # Test
        decoder.eval()
        with torch.no_grad():
            test_recon = decoder(X_test).numpy()

        total_mse = np.mean((test_recon - test_imgs) ** 2)
        print(f"Test MSE: {total_mse:.4f} ({train_time:.0f}s)")

        # Save images
        out_dir = os.path.join(OUTPUT_BASE, name)
        os.makedirs(out_dir, exist_ok=True)
        for i in range(10):
            orig = (test_imgs[i].reshape(32, 32, 3) * 255).astype(np.uint8)
            recon = (test_recon[i].reshape(32, 32, 3) * 255).astype(np.uint8)
            combo = Image.new('RGB', (64, 32))
            combo.paste(Image.fromarray(orig), (0, 0))
            combo.paste(Image.fromarray(recon), (32, 0))
            combo.save(os.path.join(out_dir, f"pair_{i}.png"))

        # Class centers
        with torch.no_grad():
            class_centers = np.zeros((10, LATENT_DIM), dtype=np.float32)
            for c in range(10):
                mask = train_labels == c
                class_centers[c] = train_latent[mask].mean(axis=0)
            gen = decoder(torch.tensor(class_centers, dtype=torch.float32)).numpy()
        for ci, cls in enumerate(CLASSES):
            img = (gen[ci].reshape(32, 32, 3) * 255).astype(np.uint8)
            Image.fromarray(img).save(os.path.join(out_dir, f"gen_{cls}.png"))

        results[name] = {'mse': total_mse, 'params': n_params, 'time': train_time}

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Config':<20} {'Params':<12} {'MSE':<10} {'Time':<10}")
    print("-" * 55)
    for name, r in sorted(results.items(), key=lambda x: x[1]['mse']):
        print(f"{name:<20} {r['params']:<12,} {r['mse']:<10.4f} {r['time']:<10.0f}s")
    print(f"\nImages → {OUTPUT_BASE}/")


if __name__ == "__main__":
    main()
