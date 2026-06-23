"""Test CLIP zero-shot classification on held-out CIFAR-10."""
import sys, os, time, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.semantic_visual import SemanticVisualEncoder

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def load_test_images(n_per_class=10, skip_first=50):
    images = []
    labels = []
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted(glob.glob(os.path.join(cls_dir, "*.npy")))[skip_first:skip_first+n_per_class]
        for f in files:
            arr = np.load(f)
            if arr.shape == (3072,):
                arr = arr.reshape(3, 32, 32).transpose(1, 2, 0)
            elif arr.shape == (3, 32, 32):
                arr = arr.transpose(1, 2, 0)
            pil_img = Image.fromarray(arr).resize((224, 224), Image.LANCZOS)
            images.append(pil_img)
            labels.append(ci)
    return images, labels


def main():
    print("Loading CLIP...")
    encoder = SemanticVisualEncoder()

    # Force load
    from ai.multimodal.semantic_visual import _lazy_init_clip
    model, processor = _lazy_init_clip()
    if model is None:
        print("CLIP failed to load!")
        return

    print("Loading held-out test images...")
    images, labels = load_test_images(n_per_class=10, skip_first=50)
    print(f"Loaded {len(images)} images")

    # Create text prompts
    text_prompts = [f"a photo of a {cls}" for cls in CLASSES]

    print("Encoding text prompts...")
    text_vecs = encoder.encode_text(text_prompts)
    if text_vecs is None:
        print("Text encoding failed!")
        return
    print(f"Text vectors shape: {text_vecs.shape}")

    print("\nClassifying images...")
    correct = 0
    per_class = {c: [0, 0] for c in CLASSES}
    t_start = time.time()

    for i, (img, label) in enumerate(zip(images, labels)):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

        img_vec = encoder.encode(img_bytes)
        if img_vec is None:
            print(f"  Image {i} encoding failed!")
            continue

        sims = text_vecs @ img_vec
        pred_idx = int(np.argmax(sims))
        pred = CLASSES[pred_idx]
        actual = CLASSES[label]

        per_class[actual][1] += 1
        if pred == actual:
            correct += 1
            per_class[actual][0] += 1

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(images)}] running_acc={correct/(i+1):.1%}")

    acc = correct / len(images)
    elapsed = time.time() - t_start
    print(f"\n=== CLIP Zero-Shot Results ===")
    print(f"Overall: {correct}/{len(images)} = {acc:.1%} ({elapsed:.0f}s, {elapsed/len(images):.1f}s/img)")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")


if __name__ == "__main__":
    main()
