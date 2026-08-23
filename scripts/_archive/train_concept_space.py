"""Train concept space mapping on CIFAR-10 and test recognition."""
import sys
import os
import time
import io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.semantic_visual import SemanticVisualEncoder
from ai.multimodal.primitives.concept_space import ConceptSpaceMapper

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def load_images(n_per_class=50, skip_first=0):
    images=[]
    labels=[]
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


def encode_images(encoder, images, batch_size=16):
    """Encode images with CLIP."""
    all_vecs=[]
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        for img in batch:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            img_bytes = buf.getvalue()
            vec = encoder.encode(img_bytes)
            if vec is not None:
                all_vecs.append(vec)
            else:
                all_vecs.append(np.zeros(512, dtype=np.float32))
        if (i + batch_size) % 100 == 0:
            print(f"  Encoded {min(i+batch_size, len(images))}/{len(images)} images")
    return np.array(all_vecs, dtype=np.float32)


def main():
    # Load encoder
    print("Loading CLIP encoder...")
    encoder = SemanticVisualEncoder()
    from ai.multimodal.semantic_visual import _lazy_init_clip
    model, processor = _lazy_init_clip()
    if model is None:
        print("CLIP failed to load!")
        return

    # Load training images
    print("\nLoading training images (50/class)...")
    train_images, train_labels = load_images(n_per_class=50, skip_first=0)
    print(f"Loaded {len(train_images)} training images")

    # Load test images
    print("Loading test images (10/class)...")
    test_images, test_labels = load_images(n_per_class=10, skip_first=50)
    print(f"Loaded {len(test_images)} test images")

    # Encode with CLIP
    print("\nEncoding training images with CLIP...")
    train_clip = encode_images(encoder, train_images)
    print(f"Training CLIP features: {train_clip.shape}")

    print("Encoding test images with CLIP...")
    test_clip = encode_images(encoder, test_images)
    print(f"Test CLIP features: {test_clip.shape}")

    # Train concept space
    print("\n=== Training Concept Space ===")
    mapper = ConceptSpaceMapper(clip_dim=512, concept_dim=64, hidden_dim=128)
    mapper.train(
        clip_features=train_clip,
        labels=np.array(train_labels),
        class_names=CLASSES,
        n_epochs=200,
        lr=0.001,
        batch_size=32,
        verbose=True,
    )

    # Save
    os.makedirs("models", exist_ok=True)
    mapper.save("models/concept_space.json")

    # Test recognition
    print("\n=== Recognition on Training Set ===")
    correct=0
    per_class={c: [0, 0] for c in CLASSES}
    for i in range(len(train_clip)):
        pred_idx, conf = mapper.predict(train_clip[i:i+1])
        pred = CLASSES[pred_idx]
        actual = CLASSES[train_labels[i]]
        per_class[actual][1] += 1
        if pred == actual:
            correct += 1
            per_class[actual][0] += 1
    acc = correct / len(train_clip)
    print(f"Overall: {correct}/{len(train_clip)} = {acc:.1%}")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    print("\n=== Recognition on Test Set (held-out) ===")
    correct=0
    per_class={c: [0, 0] for c in CLASSES}
    for i in range(len(test_clip)):
        pred_idx, conf = mapper.predict(test_clip[i:i+1])
        pred = CLASSES[pred_idx]
        actual = CLASSES[test_labels[i]]
        per_class[actual][1] += 1
        if pred == actual:
            correct += 1
            per_class[actual][0] += 1
    acc = correct / len(test_clip)
    print(f"Overall: {correct}/{len(test_clip)} = {acc:.1%}")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    # Compare with raw CLIP zero-shot
    print("\n=== Comparison ===")
    print("Concept space vs CLIP zero-shot vs Primitives k-NN vs Random")


if __name__ == "__main__":
    main()
