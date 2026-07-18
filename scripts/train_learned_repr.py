"""Learned Representation: Autoencoder + Classifier on CIFAR-10.

Architecture:
  Encoder: 32x32x3 image → FC → 128-dim latent (the "learned primitives")
  Decoder: 128-dim latent → FC → 32x32x3 image (generation)
  Classifier: 128-dim latent → FC → 10 classes (recognition)

Training:
  - Reconstruction loss (MSE): can the latent represent the image?
  - Classification loss (cross-entropy): can the latent distinguish classes?
  - Total = reconstruction + classification

This is what the user wants: learned primitives, not fixed geometric types.
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
LATENT_DIM = 128
HIDDEN_DIM = 256
N_CLASSES = 10
IMG_DIM = 32 * 32 * 3  # 3072


class LearnedRepresentation:
    """Autoencoder + Classifier: learns primitives that can both render and classify."""

    def __init__(self, latent_dim=128, hidden_dim=256):
        self.latent_dim = latent_dim
        self.hidden_dim = hidden_dim
        rng = np.random.default_rng(42)

        # Encoder: 3072 → hidden → latent
        s1 = np.sqrt(2.0 / IMG_DIM)
        s2 = np.sqrt(2.0 / hidden_dim)
        self.enc_W1 = rng.normal(0, s1, (hidden_dim, IMG_DIM)).astype(np.float32)
        self.enc_b1 = np.zeros(hidden_dim, dtype=np.float32)
        self.enc_W2 = rng.normal(0, s2, (latent_dim, hidden_dim)).astype(np.float32)
        self.enc_b2 = np.zeros(latent_dim, dtype=np.float32)

        # Decoder: latent → hidden → 3072
        s3 = np.sqrt(2.0 / latent_dim)
        s4 = np.sqrt(2.0 / hidden_dim)
        self.dec_W1 = rng.normal(0, s3, (hidden_dim, latent_dim)).astype(np.float32)
        self.dec_b1 = np.zeros(hidden_dim, dtype=np.float32)
        self.dec_W2 = rng.normal(0, s4, (IMG_DIM, hidden_dim)).astype(np.float32)
        self.dec_b2 = np.zeros(IMG_DIM, dtype=np.float32)

        # Classifier: latent → 10
        sc = np.sqrt(2.0 / latent_dim)
        self.clf_W = rng.normal(0, sc, (N_CLASSES, latent_dim)).astype(np.float32)
        self.clf_b = np.zeros(N_CLASSES, dtype=np.float32)

        # Running stats for batch norm
        self.enc_mean = np.zeros(hidden_dim, dtype=np.float32)
        self.enc_var = np.ones(hidden_dim, dtype=np.float32)
        self.dec_mean = np.zeros(hidden_dim, dtype=np.float32)
        self.dec_var = np.ones(hidden_dim, dtype=np.float32)

    def relu(self, x):
        return np.maximum(0, x)

    def softmax(self, x):
        e = np.exp(x - x.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    def encode(self, x):
        """Image → latent space (the learned primitives)."""
        h = self.relu(x @ self.enc_W1.T + self.enc_b1)
        latent = h @ self.enc_W2.T + self.enc_b2
        return latent

    def decode(self, latent):
        """Latent → image (generation)."""
        h = self.relu(latent @ self.dec_W1.T + self.dec_b1)
        out = h @ self.dec_W2.T + self.dec_b2
        return 1.0 / (1.0 + np.exp(-np.clip(out, -10, 10)))  # sigmoid

    def classify(self, latent):
        """Latent → class probabilities (recognition)."""
        logits = latent @ self.clf_W.T + self.clf_b
        return self.softmax(logits)

    def forward(self, x):
        """Full forward pass: image → latent → reconstructed image + class."""
        latent = self.encode(x)
        recon = self.decode(latent)
        probs = self.classify(latent)
        return latent, recon, probs

    def train(self, train_images, train_labels, n_epochs=50, lr=0.001,
              batch_size=64, recon_weight=1.0, cls_weight=0.5, verbose=True):
        """Train the learned representation.

        Loss = recon_weight * MSE(recon, original) + cls_weight * CrossEntropy(pred, label)
        """
        n = len(train_images)
        n_batches = (n + batch_size - 1) // batch_size
        t_start = time.time()

        if verbose:
            print(f"Training: {n} images, {n_epochs} epochs, batch={batch_size}")
            print(f"  Latent dim: {self.latent_dim}, Hidden: {self.hidden_dim}")
            print(f"  Loss weights: recon={recon_weight}, cls={cls_weight}")

        for epoch in range(n_epochs):
            perm = np.random.permutation(n)
            total_loss = 0.0
            total_recon = 0.0
            total_cls = 0.0
            correct = 0

            for i in range(0, n, batch_size):
                batch_idx = perm[i:i+batch_size]
                x = train_images[batch_idx]
                y = train_labels[batch_idx]
                bs = len(x)

                # Forward
                latent, recon, probs = self.forward(x)

                # Losses
                recon_loss = np.mean((recon - x) ** 2)
                # Cross entropy
                y_onehot = np.zeros((bs, N_CLASSES), dtype=np.float32)
                for j, label in enumerate(y):
                    y_onehot[j, label] = 1.0
                cls_loss = -np.mean(np.sum(y_onehot * np.log(probs + 1e-8), axis=1))

                loss = recon_weight * recon_loss + cls_weight * cls_loss

                # Accuracy
                pred = np.argmax(probs, axis=1)
                correct += np.sum(pred == y)

                # Backward (finite differences on small subset of params)
                eps = 0.005
                n_probe = 30
                params = [
                    ('enc_W1', self.enc_W1), ('enc_b1', self.enc_b1),
                    ('enc_W2', self.enc_W2), ('enc_b2', self.enc_b2),
                    ('dec_W1', self.dec_W1), ('dec_b1', self.dec_b1),
                    ('dec_W2', self.dec_W2), ('dec_b2', self.dec_b2),
                    ('clf_W', self.clf_W), ('clf_b', self.clf_b),
                ]

                for name, param in params:
                    flat = param.ravel()
                    probe_idx = np.random.choice(param.size, min(n_probe, param.size), replace=False)
                    for idx in probe_idx:
                        old = flat[idx]
                        flat[idx] = old + eps
                        _, r_plus, p_plus = self.forward(x)
                        l_plus = recon_weight * np.mean((r_plus - x)**2) + cls_weight * (-np.mean(np.sum(y_onehot * np.log(p_plus + 1e-8), axis=1)))
                        flat[idx] = old - eps
                        _, r_minus, p_minus = self.forward(x)
                        l_minus = recon_weight * np.mean((r_minus - x)**2) + cls_weight * (-np.mean(np.sum(y_onehot * np.log(p_minus + 1e-8), axis=1)))
                        flat[idx] = old
                        grad = (l_plus - l_minus) / (2 * eps)
                        flat[idx] -= lr * grad

                total_loss += loss
                total_recon += recon_loss
                total_cls += cls_loss

            acc = correct / n
            avg_loss = total_loss / n_batches
            avg_recon = total_recon / n_batches
            avg_cls = total_cls / n_batches
            elapsed = time.time() - t_start

            if verbose and (epoch + 1) % 10 == 0:
                print(f"  Epoch {epoch+1}/{n_epochs}: loss={avg_loss:.4f} "
                      f"recon={avg_recon:.4f} cls={avg_cls:.4f} "
                      f"train_acc={acc:.1%} ({elapsed:.0f}s)")

    def generate(self, latent=None, class_idx=None):
        """Generate an image from a latent vector or class index."""
        if latent is None:
            if class_idx is not None:
                # Generate from class center
                latent = self._class_centers[class_idx]
            else:
                latent = np.random.randn(self.latent_dim).astype(np.float32)
        return self.decode(latent.reshape(1, -1)).reshape(32, 32, 3)

    def save(self, path):
        data = {
            'latent_dim': self.latent_dim,
            'hidden_dim': self.hidden_dim,
            'enc_W1': self.enc_W1.tolist(), 'enc_b1': self.enc_b1.tolist(),
            'enc_W2': self.enc_W2.tolist(), 'enc_b2': self.enc_b2.tolist(),
            'dec_W1': self.dec_W1.tolist(), 'dec_b1': self.dec_b1.tolist(),
            'dec_W2': self.dec_W2.tolist(), 'dec_b2': self.dec_b2.tolist(),
            'clf_W': self.clf_W.tolist(), 'clf_b': self.clf_b.tolist(),
        }
        if hasattr(self, '_class_centers') and self._class_centers is not None:
            data['class_centers'] = self._class_centers.tolist()
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        with open(path, 'w') as f:
            import json
            json.dump(data, f)
        print(f"Saved to {path}")


def load_cifar():
    images = []
    labels = []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))
        for f in files:
            arr = np.load(f)
            if arr.shape == (3072,):
                pass
            elif arr.shape == (3, 32, 32):
                arr = arr.transpose(1, 2, 0).reshape(-1)
            images.append(arr.astype(np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def main():
    print("Loading CIFAR-10...")
    all_images, all_labels = load_cifar()
    print(f"Loaded {len(all_images)} images")

    # Split: 5000 train, 1000 test
    train_imgs = all_images[:5000]
    train_labels = all_labels[:5000]
    test_imgs = all_images[5000:6000]
    test_labels = all_labels[5000:6000]

    print(f"Train: {len(train_imgs)}, Test: {len(test_imgs)}")

    # Train
    model = LearnedRepresentation(latent_dim=LATENT_DIM, hidden_dim=HIDDEN_DIM)
    model.train(train_imgs, train_labels, n_epochs=50, lr=0.001,
                batch_size=64, recon_weight=1.0, cls_weight=0.5)

    # Compute class centers in latent space
    latent_train = model.encode(train_imgs)
    model._class_centers = np.zeros((N_CLASSES, LATENT_DIM), dtype=np.float32)
    for c in range(N_CLASSES):
        mask = train_labels == c
        model._class_centers[c] = latent_train[mask].mean(axis=0)

    # Test recognition
    print("\n=== Recognition (held-out test set) ===")
    latent_test = model.encode(test_imgs)
    probs = model.classify(latent_test)
    preds = np.argmax(probs, axis=1)
    correct = np.sum(preds == test_labels)
    print(f"Overall: {correct}/{len(test_labels)} = {correct/len(test_labels):.1%}")
    per_class = {c: [0, 0] for c in CLASSES}
    for i in range(len(test_labels)):
        cls = CLASSES[test_labels[i]]
        per_class[cls][1] += 1
        if preds[i] == test_labels[i]:
            per_class[cls][0] += 1
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    # Test generation
    print("\n=== Generation (decode from latent) ===")
    output_dir = "data/multimodal/gvv/learned_test"
    os.makedirs(output_dir, exist_ok=True)

    # Generate from class centers
    for ci, cls in enumerate(CLASSES):
        img = model.generate(class_idx=ci)
        img_uint8 = (img * 255).clip(0, 255).astype(np.uint8)
        pil_img = Image.fromarray(img_uint8)
        pil_img.save(os.path.join(output_dir, f"gen_{cls}.png"))
    print(f"Generated 10 class images → {output_dir}/")

    # Generate from random latent
    for i in range(5):
        img = model.generate()
        img_uint8 = (img * 255).clip(0, 255).astype(np.uint8)
        pil_img = Image.fromarray(img_uint8)
        pil_img.save(os.path.join(output_dir, f"gen_random_{i}.png"))
    print("Generated 5 random images")

    # Show reconstruction quality
    print("\n=== Reconstruction quality (first 5 test images) ===")
    for i in range(5):
        orig = test_imgs[i].reshape(32, 32, 3)
        recon = model.decode(latent_test[i:i+1]).reshape(32, 32, 3)
        mse = np.mean((orig - recon) ** 2)
        orig_pil = Image.fromarray((orig * 255).astype(np.uint8))
        recon_pil = Image.fromarray((recon * 255).astype(np.uint8))
        orig_pil.save(os.path.join(output_dir, f"orig_{i}.png"))
        recon_pil.save(os.path.join(output_dir, f"recon_{i}.png"))
        print(f"  Image {i}: MSE={mse:.4f}")

    # Save model
    model.save("models/learned_representation.json")


if __name__ == "__main__":
    main()
