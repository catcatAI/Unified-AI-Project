"""
Train decomposer on directly-optimized primitive vectors.

Pipeline:
1. Load CIFAR-10 images
2. Encode with CLIP
3. Train decomposer: CLIP(512) → optimized_vector(263) via MSE
4. Evaluate: CLIP text → decomposer → primitives → render → compare with real
"""
import sys
import os
import time
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'backend', 'src'))

import numpy as np
from PIL import Image

from ai.multimodal.primitives.learnable_decomposer import LearnableDecomposer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer

CIFAR_DIR="D:/Projects/Unified-AI-Project/data/multimodal/cifar10"
CLASSES=["airplane", "automobile", "bird", "cat", "deer",
           "dog", "frog", "horse", "ship", "truck"]
MODEL_DIR="D:/Projects/Unified-AI-Project/models"
SAVE_DIR="D:/Projects/Unified-AI-Project/data/multimodal/samples_optimized_decomposer"


def load_cifar_images_and_labels():
    """Load all CIFAR images indexed by the optimized vectors."""
    optimized_labels = np.load(os.path.join(CIFAR_DIR, "optimized_labels.npy"))

    # Load one image per label to match the order
    all_files={}
    for ci, cls in enumerate(CLASSES):
        cls_dir = os.path.join(CIFAR_DIR, cls)
        files = sorted([f for f in os.listdir(cls_dir) if f.endswith(".npy")])
        all_files[ci] = [os.path.join(cls_dir, f) for f in files]

    images=[]
    labels=[]
    for label in optimized_labels:
        f = all_files[int(label)].pop(0)
        arr = np.load(f)
        if arr.shape == (3072,):
            arr = arr.reshape(3, 32, 32).transpose(1, 2, 0)
        elif arr.shape == (3, 32, 32):
            arr = arr.transpose(1, 2, 0)
        pil = Image.fromarray(arr).resize((128, 128), Image.LANCZOS)
        images.append(np.array(pil, dtype=np.float32) / 255.0)
        labels.append(CLASSES[int(label)])

    return images, labels


def get_clip_embeddings(images):
    """Encode images with CLIP."""
    import io
    from ai.multimodal.semantic_visual import SemanticVisualEncoder

    sv = SemanticVisualEncoder()

    embeddings=[]
    for img_arr in images:
        pil = Image.fromarray((img_arr * 255).astype(np.uint8))
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        emb = sv.encode(img_bytes)
        if emb is None:
            emb = np.zeros(512, dtype=np.float32)
        embeddings.append(emb)
    return embeddings


def train_decomposer(clip_embs, optimized_vecs, epochs=200, lr=0.002):
    """Train decomposer: CLIP(512) → optimized_vector(263) via MSE."""
    decomposer = LearnableDecomposer(clip_dim=512, hidden_dim=256)

    # Initialize clip stats
    for emb in clip_embs:
        decomposer.update_clip_stats(emb)

    # Manual MSE training (pure numpy, no rendering)
    n = len(clip_embs)
    clip_embs_arr = np.array(clip_embs, dtype=np.float32)
    opt_vecs_arr = np.array(optimized_vecs, dtype=np.float32)

    losses=[]
    best_loss = float('inf')
    best_W1 = decomposer._W1.copy()
    best_b1 = decomposer._b1.copy()
    best_W2 = decomposer._W2.copy()
    best_b2 = decomposer._b2.copy()

    for epoch in range(epochs):
        indices = np.random.permutation(n)
        epoch_loss=0.0

        for i in range(0, n, 8):
            batch_idx = indices[i:i + 8]
            batch_clip = clip_embs_arr[batch_idx]
            batch_target = opt_vecs_arr[batch_idx]

            # Forward
            batch_pred=[]
            batch_caches=[]
            for j in range(len(batch_idx)):
                pred, cache = decomposer.forward(batch_clip[j])
                batch_pred.append(pred)
                batch_caches.append(cache)

            batch_pred_arr = np.array(batch_pred)
            batch_loss = np.mean((batch_pred_arr - batch_target) ** 2)

            # Backward (manual MSE gradient)
            for j in range(len(batch_idx)):
                pred = batch_pred[j]
                target = batch_target[j]
                cache = batch_caches[j]

                # MSE gradient: d(loss)/d(pred) = 2*(pred - target)/n
                d_pred=2.0 * (pred - target) / len(batch_idx)

                # Through sigmoid: d(sig)/dz = sig * (1 - sig)
                d_z2 = d_pred * cache["sig"] * (1 - cache["sig"])

                # W2 gradient
                d_W2 = np.outer(cache["h"], d_z2)
                d_b2 = d_z2

                # Through ReLU
                d_h = d_z2 @ decomposer._W2.T
                d_z1 = d_h * (cache["z1"] > 0).astype(np.float32)

                # W1 gradient
                d_W1 = np.outer(cache["x"], d_z1)
                d_b1 = d_z1

                # Clip gradients
                for g in [d_W1, d_b1, d_W2, d_b2]:
                    np.clip(g, -1.0, 1.0, out=g)

                # Update
                decomposer._W1 -= lr * d_W1
                decomposer._b1 -= lr * d_b1
                decomposer._W2 -= lr * d_W2
                decomposer._b2 -= lr * d_b2

            epoch_loss += float(batch_loss)

        avg_loss = epoch_loss / max(n // 8, 1)
        losses.append(avg_loss)

        if avg_loss < best_loss:
            best_loss = avg_loss
            best_W1 = decomposer._W1.copy()
            best_b1 = decomposer._b1.copy()
            best_W2 = decomposer._W2.copy()
            best_b2 = decomposer._b2.copy()

        if (epoch + 1) % 20 == 0:
            print(f"  Epoch {epoch+1}/{epochs} - loss={avg_loss:.6f} (best={best_loss:.6f})")

    # Restore best weights
    decomposer._W1 = best_W1
    decomposer._b1 = best_b1
    decomposer._W2 = best_W2
    decomposer._b2 = best_b2

    return decomposer, losses


def evaluate_end_to_end(decomposer, images, labels):
    """Evaluate: CLIP image → decomposer → primitives → render → CLIP similarity."""
    from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator
    import torch

    evaluator = GenerationEvaluator()
    renderer = PrimitiveRenderer(canvas_size=(128, 128))

    os.makedirs(SAVE_DIR, exist_ok=True)

    sims=[]
    for i in range(min(20, len(images))):
        # Get CLIP embedding
        pil_orig = Image.fromarray((images[i] * 255).astype(np.uint8))

        # Encode with CLIP
        import io
        from ai.multimodal.semantic_visual import SemanticVisualEncoder
        sv = SemanticVisualEncoder()
        buf = io.BytesIO()
        pil_orig.save(buf, format="PNG")
        clip_emb = sv.encode(buf.getvalue())
        if clip_emb is None:
            clip_emb = np.zeros(512, dtype=np.float32)

        # Predict primitives
        pred_vec, _ = decomposer.forward(clip_emb)

        # Render
        instructions = decomposer.decode_to_instructions(pred_vec, canvas_size=(128, 128))
        rendered = renderer.render(instructions)

        # CLIP similarity
        sim = evaluator._clip_image_similarity(rendered, pil_orig)
        sims.append(sim)

        # Save comparison
        comp = Image.new("RGB", (256, 128))
        comp.paste(pil_orig, (0, 0))
        comp.paste(rendered, (128, 0))
        comp.save(os.path.join(SAVE_DIR, f"{i:02d}_{labels[i]}_sim{sim:.3f}.png"))

        if (i + 1) % 5 == 0:
            print(f"  Evaluated {i+1}/20 - avg_sim={np.mean(sims):.4f}")

    return np.mean(sims)


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # 1. Load data
    print("Loading CIFAR-10 images...")
    images, labels = load_cifar_images_and_labels()
    optimized_vecs = np.load(os.path.join(CIFAR_DIR, "optimized_vectors.npy"))
    print(f"Loaded {len(images)} images, {len(optimized_vecs)} optimized vectors")

    # 2. Get CLIP embeddings
    print("Encoding with CLIP...")
    t0 = time.time()
    clip_embs = get_clip_embeddings(images)
    print(f"CLIP encoding done ({time.time()-t0:.1f}s)")

    # 3. Train decomposer
    print("Training decomposer (CLIP→optimized_vector MSE)...")
    t0 = time.time()
    decomposer, losses = train_decomposer(
        clip_embs, optimized_vecs,
        epochs=200, lr=0.002
    )
    print(f"Training done ({time.time()-t0:.1f}s), final_loss={losses[-1]:.6f}")

    # Save model
    model_path = os.path.join(MODEL_DIR, "decomposer_optimized.json")
    decomposer.save(model_path)
    print(f"Saved model to {model_path}")

    # 4. Evaluate end-to-end
    print("Evaluating end-to-end...")
    avg_sim = evaluate_end_to_end(decomposer, images, labels)
    print(f"Average CLIP similarity: {avg_sim:.4f}")

    # Save training history
    with open(os.path.join(MODEL_DIR, "decomposer_training_history.json"), "w") as f:
        json.dump({"losses": losses, "final_loss": losses[-1], "avg_sim": float(avg_sim)}, f)


if __name__ == "__main__":
    main()
