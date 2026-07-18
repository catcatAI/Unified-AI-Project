"""Fast concept space training using linear probing + center loss."""
import sys, os, time, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
import glob
from PIL import Image
from ai.multimodal.semantic_visual import SemanticVisualEncoder

CIFAR_DIR = "D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck"]


def load_images(n_per_class=50, skip_first=0):
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


def encode_images(encoder, images):
    all_vecs = []
    for i, img in enumerate(images):
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        vec = encoder.encode(buf.getvalue())
        if vec is not None:
            all_vecs.append(vec)
        else:
            all_vecs.append(np.zeros(512, dtype=np.float32))
        if (i + 1) % 100 == 0:
            print(f"  Encoded {i+1}/{len(images)}")
    return np.array(all_vecs, dtype=np.float32)


def main():
    print("Loading CLIP...")
    encoder = SemanticVisualEncoder()
    from ai.multimodal.semantic_visual import _lazy_init_clip
    model, _ = _lazy_init_clip()
    if model is None:
        print("CLIP failed!")
        return

    # Load data
    print("\nLoading training (50/class) + test (10/class)...")
    train_imgs, train_labels = load_images(50, 0)
    test_imgs, test_labels = load_images(10, 50)
    print(f"Train: {len(train_imgs)}, Test: {len(test_imgs)}")

    # Encode
    print("\nEncoding training...")
    train_clip = encode_images(encoder, train_imgs)
    print("Encoding test...")
    test_clip = encode_images(encoder, test_imgs)

    # === Method 1: Pure CLIP cosine similarity (baseline) ===
    print("\n=== CLIP Cosine Similarity (no training) ===")
    text_prompts = [f"a photo of a {cls}" for cls in CLASSES]
    text_vecs = encoder.encode_text(text_prompts)

    correct = 0
    for i in range(len(test_clip)):
        sims = text_vecs @ test_clip[i]
        pred = int(np.argmax(sims))
        if pred == test_labels[i]:
            correct += 1
    print(f"CLIP zero-shot: {correct}/{len(test_clip)} = {correct/len(test_clip):.1%}")

    # === Method 2: Linear classifier on CLIP features ===
    print("\n=== Linear Classifier on CLIP Features ===")
    n_classes = len(CLASSES)
    n_features = 512

    # One-hot encode labels
    Y = np.zeros((len(train_clip), n_classes), dtype=np.float32)
    for i, l in enumerate(train_labels):
        Y[i, l] = 1.0

    # Solve linear regression: W = (X^T X)^{-1} X^T Y
    X = train_clip  # (N, 512)
    XtX = X.T @ X + 1e-4 * np.eye(n_features)  # regularized
    W = np.linalg.solve(XtX, X.T @ Y)  # (512, 10)

    # Test
    correct = 0
    per_class = {c: [0, 0] for c in CLASSES}
    for i in range(len(test_clip)):
        scores = test_clip[i] @ W  # (10,)
        pred = int(np.argmax(scores))
        actual = test_labels[i]
        per_class[CLASSES[actual]][1] += 1
        if pred == actual:
            correct += 1
            per_class[CLASSES[actual]][0] += 1
    acc = correct / len(test_clip)
    print(f"Overall: {correct}/{len(test_clip)} = {acc:.1%}")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    # === Method 3: Concept space (low-dim projection) ===
    print("\n=== Concept Space (PCA → 64-dim → classify) ===")
    # PCA projection
    X_mean = X.mean(axis=0)
    X_centered = X - X_mean
    U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)
    # Top 64 components
    proj = Vt[:64]  # (64, 512)

    # Project training data
    train_proj = X_centered @ proj.T  # (N, 64)
    # Normalize
    train_norms = np.linalg.norm(train_proj, axis=1, keepdims=True)
    train_norms[train_norms == 0] = 1.0
    train_proj_norm = train_proj / train_norms

    # Class centers in projected space
    centers = np.zeros((n_classes, 64), dtype=np.float32)
    for c in range(n_classes):
        mask = np.array(train_labels) == c
        centers[c] = train_proj_norm[mask].mean(axis=0)
        centers[c] /= np.linalg.norm(centers[c]) + 1e-8

    # Test
    correct = 0
    per_class = {c: [0, 0] for c in CLASSES}
    for i in range(len(test_clip)):
        proj_vec = (test_clip[i] - X_mean) @ proj.T
        norm = np.linalg.norm(proj_vec)
        if norm > 0:
            proj_vec /= norm
        sims = centers @ proj_vec
        pred = int(np.argmax(sims))
        actual = test_labels[i]
        per_class[CLASSES[actual]][1] += 1
        if pred == actual:
            correct += 1
            per_class[CLASSES[actual]][0] += 1
    acc = correct / len(test_clip)
    print(f"Overall: {correct}/{len(test_clip)} = {acc:.1%}")
    for cls in CLASSES:
        c, t = per_class[cls]
        print(f"  {cls:12s}: {c}/{t} = {c/t:.1%}" if t > 0 else f"  {cls}: 0")

    # Save the concept space projection
    from ai.multimodal.primitives.concept_space import ConceptSpaceMapper
    mapper = ConceptSpaceMapper(clip_dim=512, concept_dim=64, hidden_dim=64)
    # Use PCA weights as a linear projection (no training needed)
    mapper._W1 = proj.astype(np.float32)  # (64, 512)
    mapper._b1 = (-X_mean @ proj.T).astype(np.float32)  # (64,)
    mapper._W2 = np.eye(64, dtype=np.float32)
    mapper._b2 = np.zeros(64, dtype=np.float32)
    mapper._W3 = np.eye(64, dtype=np.float32)
    mapper._b3 = np.zeros(64, dtype=np.float32)
    mapper._class_centers = centers
    mapper._class_names = CLASSES
    mapper._is_trained = True
    mapper.save("models/concept_space.json")
    print("\nSaved concept space (PCA-based)")


if __name__ == "__main__":
    main()
