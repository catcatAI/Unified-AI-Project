"""Train Three-Layer Visual Architecture on CIFAR-10."""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.three_layer_visual import ThreeLayerVisual

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]
OUTPUT_DIR = "data/multimodal/gvv/three_layer_train"


def load_cifar(n_per_class=50):
    images, labels = [], []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[:n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.ndim == 3: arr = arr.reshape(-1)
            images.append(arr.astype(np.float32) / 255.0)
            labels.append(ci)
    return np.array(images), np.array(labels)


def main():
    print("Loading CIFAR-10...")
    images, labels = load_cifar(50)
    print(f"Total: {len(images)} images, {len(CLASSES)} classes")

    # Train
    model = ThreeLayerVisual(model_dir="models/three_layer")
    metrics = model.fit(images, labels, CLASSES, n_epochs=50, verbose=True)

    # Save
    model.save()
    print(f"\nModel saved to models/three_layer/")

    # Test
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Reconstruction
    print("\nTesting reconstruction...")
    recon = model.reconstruct(images[:20], enhance=True)
    for i in range(20):
        orig = (images[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        rec = (recon[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        combo = Image.new('RGB', (64, 32))
        combo.paste(Image.fromarray(orig), (0, 0))
        combo.paste(Image.fromarray(rec), (32, 0))
        combo.save(os.path.join(OUTPUT_DIR, f"recon_{i}.png"))

    # Class generation
    print("Generating class centers...")
    for ci, cls in enumerate(CLASSES):
        gen = model.generate_from_class(ci, enhance=True)
        img = (gen.reshape(32, 32, 3) * 255).astype(np.uint8)
        Image.fromarray(img).save(os.path.join(OUTPUT_DIR, f"gen_{cls}.png"))

    # Interpolation
    print("Generating interpolation...")
    interp = model.interpolate(0, 3, n_steps=10)  # airplane → cat
    for i in range(10):
        img = (interp[i].reshape(32, 32, 3) * 255).astype(np.uint8)
        Image.fromarray(img).save(os.path.join(OUTPUT_DIR, f"interp_{i}.png"))

    print(f"\nImages → {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
