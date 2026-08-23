"""Learned Representation v2: PCA encoder + learned decoder.

Fast approach:
1. PCA encoder: instant, proven (87% accuracy)
2. Learned decoder: PCA latent → image (learn to render from latent)

This gives us:
- Recognition: image → PCA → classify (87%)
- Generation: PCA latent → decoder → image (learned rendering)
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


class PCAEncoder:
    """PCA projection: image → latent (instant, no training)."""

    def __init__(self, latent_dim=128):
        self.latent_dim = latent_dim
        self.mean=None
        self.projection=None  # (latent_dim, 3072)

    def fit(self, images):
        """Fit PCA on training images."""
        self.mean = images.mean(axis=0)
        centered = images - self.mean
        U, S, Vt = np.linalg.svd(centered, full_matrices=False)
        self.projection = Vt[:self.latent_dim]  # (latent_dim, 3072)
        explained = (S[:self.latent_dim] ** 2).sum() / (S ** 2).sum()
        print(f"PCA: {self.latent_dim} dims explain {explained:.1%} variance")

    def encode(self, images):
        """Project images to latent space."""
        if images.ndim == 1:
            images = images.reshape(1, -1)
        centered = images - self.mean
        latent = centered @ self.projection.T  # (N, latent_dim)
        # L2 normalize
        norms = np.linalg.norm(latent, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return latent / norms


class SimpleDecoder:
    """Linear decoder: latent → image (fast to train)."""

    def __init__(self, latent_dim, img_dim):
        rng = np.random.default_rng(42)
        scale = np.sqrt(2.0 / latent_dim)
        self.W = rng.normal(0, scale, (img_dim, latent_dim)).astype(np.float32)
        self.b = np.zeros(img_dim, dtype=np.float32)

    def decode(self, latent):
        """Latent → image (sigmoid output)."""
        out = latent @ self.W.T + self.b
        return 1.0 / (1.0 + np.exp(-np.clip(out, -10, 10)))

    def train(self, latent, images, n_epochs=30, lr=0.001, batch_size=128, verbose=True):
        """Train decoder with gradient descent."""
        n = len(latent)
        t_start = time.time()

        for epoch in range(n_epochs):
            perm = np.random.permutation(n)
            total_loss=0.0
            n_batches=0

            for i in range(0, n, batch_size):
                idx = perm[i:i+batch_size]
                x = latent[idx]
                y = images[idx]
                bs = len(x)

                # Forward
                recon=self.decode(x)
                loss = np.mean((recon - y) ** 2)

                # Backward: dL/dW = (recon - y)^T @ x / bs
                error = recon - y  # (bs, img_dim)
                grad_W = error.T @ x / bs  # (img_dim, latent_dim)
                grad_b = error.mean(axis=0)  # (img_dim,)

                # Update
                self.W -= lr * grad_W
                self.b -= lr * grad_b

                total_loss += loss
                n_batches += 1

            if verbose and (epoch + 1) % 10 == 0:
                avg = total_loss / n_batches
                elapsed = time.time() - t_start
                print(f"  Epoch {epoch+1}/{n_epochs}: MSE={avg:.4f} ({elapsed:.0f}s)")


class Classifier:
    """Linear classifier: latent → class."""

    def __init__(self, latent_dim, n_classes):
        self.W=None
        self.b=None
        self.n_classes = n_classes

    def fit(self, latent, labels):
        """Solve linear regression."""
        n_classes=self.n_classes
        Y = np.zeros((len(latent), n_classes), dtype=np.float32)
        for i, l in enumerate(labels):
            Y[i, l] = 1.0
        X = latent
        XtX = X.T @ X + 1e-4 * np.eye(X.shape[1])
        self.W = np.linalg.solve(XtX, X.T @ Y)
        self.b = np.zeros(n_classes, dtype=np.float32)

    def predict(self, latent):
        scores = latent @ self.W.T + self.b
        return np.argmax(scores, axis=1), scores


def load_cifar(n_per_class=None):
    images=[]
    labels=[]
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))
        if n_per_class:
            files = files[:n_per_class]
        for f in files:
            arr = np.load(f).astype(np.float32) / 255.0
            images.append(arr)
            labels.append(ci)
    return np.array(images), np.array(labels)


def main():
    print("Loading CIFAR-10...")
    all_images, all_labels = load_cifar()
    print(f"Total: {len(all_images)} images")

    # Split
    train_imgs = all_images[:5000]
    train_labels = all_labels[:5000]
    test_imgs = all_images[5000:6000]
    test_labels = all_labels[5000:6000]

    # 1. PCA encoder
    print("\n=== PCA Encoder ===")
    encoder = PCAEncoder(latent_dim=LATENT_DIM)
    encoder.fit(train_imgs)
    train_latent = encoder.encode(train_imgs)
    test_latent = encoder.encode(test_imgs)
    print(f"Train latent: {train_latent.shape}")
    print(f"Test latent: {test_latent.shape}")

    # 2. Classifier
    print("\n=== Linear Classifier ===")
    classifier = Classifier(LATENT_DIM, 10)
    classifier.fit(train_latent, train_labels)
    preds, _ = classifier.predict(test_latent)
    correct = np.sum(preds == test_labels)
    print(f"Held-out accuracy: {correct}/{len(test_labels)} = {correct/len(test_labels):.1%}")
    per_class={c: [0, 0] for c in CLASSES}
    for i in range(len(test_labels)):
        cls = CLASSES[test_labels[i]]
        per_class[cls][1] += 1
        if preds[i] == test_labels[i]:
            per_class[cls][0] += 1
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    # 3. Decoder
    print("\n=== Learned Decoder ===")
    decoder = SimpleDecoder(LATENT_DIM, IMG_DIM)
    decoder.train(train_latent, train_imgs, n_epochs=50, lr=0.005, batch_size=128)

    # Test reconstruction
    print("\n=== Reconstruction Quality ===")
    output_dir="data/multimodal/gvv/learned_test"
    os.makedirs(output_dir, exist_ok=True)

    total_mse=0.0
    for i in range(10):
        recon = decoder.decode(test_latent[i:i+1]).reshape(32, 32, 3)
        orig = test_imgs[i].reshape(32, 32, 3)
        mse = np.mean((recon - orig) ** 2)
        total_mse += mse

        orig_pil = Image.fromarray((orig * 255).astype(np.uint8))
        recon_pil = Image.fromarray((recon * 255).astype(np.uint8))
        orig_pil.save(os.path.join(output_dir, f"orig_{i}.png"))
        recon_pil.save(os.path.join(output_dir, f"recon_{i}.png"))
        print(f"  Image {i}: MSE={mse:.4f}")
    print(f"Average MSE: {total_mse/10:.4f}")

    # 4. Generate from class centers
    print("\n=== Generation from Class Centers ===")
    class_centers = np.zeros((10, LATENT_DIM), dtype=np.float32)
    for c in range(10):
        mask = train_labels == c
        class_centers[c] = train_latent[mask].mean(axis=0)

    for ci, cls in enumerate(CLASSES):
        gen = decoder.decode(class_centers[ci:ci+1]).reshape(32, 32, 3)
        gen_pil = Image.fromarray((gen * 255).astype(np.uint8))
        gen_pil.save(os.path.join(output_dir, f"gen_{cls}.png"))
        print(f"  Generated {cls}")

    # Random generation
    for i in range(5):
        z = np.random.randn(LATENT_DIM).astype(np.float32)
        z = z / np.linalg.norm(z)
        gen = decoder.decode(z.reshape(1, -1)).reshape(32, 32, 3)
        gen_pil = Image.fromarray((gen * 255).astype(np.uint8))
        gen_pil.save(os.path.join(output_dir, f"gen_random_{i}.png"))
    print("Generated 5 random images")

    print(f"\nAll images saved to {output_dir}/")


if __name__ == "__main__":
    main()
