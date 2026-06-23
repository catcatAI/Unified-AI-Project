"""Train learnable decomposer: CLIP → primitive vectors.

Step 1: Pre-extract primitive vectors from CIFAR-10 using rule-based decomposer
Step 2: Train neural network: CLIP embedding → 263-dim primitive vector (MSE loss)
Step 3: At inference: CLIP → decomposer → DrawingInstructions → render

No rendering during training. Pure matrix operations. Fast CPU training.
"""

import sys, os, json, time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.learnable_decomposer import LearnableDecomposer
from ai.multimodal.primitives.decomposer import decompose_spatial
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    # Load CIFAR-10
    images, labels = [], []
    for cls in idx["classes"]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:5]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print("Loaded %d images" % len(images), flush=True)

    # Step 1: Pre-extract primitive vectors using rule-based decomposer
    print("\n[Step 1] Extracting primitive vectors from images...", flush=True)
    t0 = time.time()
    target_vecs = []
    for img in images:
        instr = decompose_spatial(img)
        vec = instr.to_vector()
        target_vecs.append(vec)
    target_vecs = np.array(target_vecs, dtype=np.float32)
    print("  %d vectors, shape=%s (%.1fs)" % (len(target_vecs), str(target_vecs.shape), time.time() - t0), flush=True)

    # Step 2: Get CLIP embeddings
    print("\n[Step 2] Encoding images with CLIP...", flush=True)
    t0 = time.time()
    from ai.multimodal.semantic_visual import SemanticVisualEncoder
    clip_model = SemanticVisualEncoder()

    clip_embs = []
    for img_arr in images:
        pil = Image.fromarray(img_arr).resize((224, 224), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        emb = clip_model.encode(buf.getvalue())
        clip_embs.append(emb if emb is not None else np.zeros(512))
    clip_embs = np.array(clip_embs, dtype=np.float32)
    print("  %d CLIP embeddings, shape=%s (%.1fs)" % (len(clip_embs), str(clip_embs.shape), time.time() - t0), flush=True)

    # Step 3: Train decomposer (pure MSE, no rendering)
    print("\n[Step 3] Training decomposer: CLIP → primitive vectors...", flush=True)
    decomposer = LearnableDecomposer(clip_dim=512, hidden_dim=256)

    # Train with MSE loss on primitive vectors (NO rendering needed)
    epochs = 200
    lr = 0.01
    losses = []
    t0 = time.time()

    for epoch in range(epochs):
        # Shuffle
        indices = np.random.permutation(len(clip_embs))
        epoch_loss = 0.0

        for idx in indices:
            clip_emb = clip_embs[idx]
            target = target_vecs[idx]

            # Forward: CLIP → primitive vector
            pred, cache = decomposer.forward(clip_emb)

            # MSE loss
            error = pred - target
            loss = float(np.mean(error ** 2))
            epoch_loss += loss

            # Backprop (pure matrix operations)
            d_out = 2.0 * error / decomposer._out_dim

            # Through sigmoid
            d_z2 = d_out * cache["sig"] * (1 - cache["sig"])

            # W2 gradient
            d_W2 = np.outer(cache["h"], d_z2)
            d_b2 = d_z2

            # Through ReLU
            d_h = d_z2 @ decomposer._W2.T
            d_z1 = d_h * (cache["z1"] > 0).astype(np.float32)

            # W1 gradient
            d_W1 = np.outer(cache["x"], d_z1)
            d_b1 = d_z1

            # Gradient clipping
            for g in [d_W1, d_b1, d_W2, d_b2]:
                np.clip(g, -1.0, 1.0, out=g)

            # Update
            decomposer._W1 -= lr * d_W1
            decomposer._b1 -= lr * d_b1
            decomposer._W2 -= lr * d_W2
            decomposer._b2 -= lr * d_b2

        avg_loss = epoch_loss / len(clip_embs)
        losses.append(avg_loss)

        if epoch % 20 == 0:
            print("  Epoch %d/%d - loss: %.6f" % (epoch, epochs, avg_loss), flush=True)

    elapsed = time.time() - t0
    print("  Training done: loss=%.6f (%.1fs)" % (losses[-1], elapsed), flush=True)

    # Step 4: Evaluate with rendering
    print("\n[Step 4] Evaluating with rendering...", flush=True)
    renderer = PrimitiveRenderer((128, 128))
    evaluator = GenerationEvaluator()
    target_images = [Image.fromarray(img).resize((128, 128), Image.LANCZOS) for img in images]

    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples_learned")
    os.makedirs(save_dir, exist_ok=True)

    for i in range(min(15, len(images))):
        pred_vec, _ = decomposer.forward(clip_embs[i])
        from ai.multimodal.primitives.primitive_types import DrawingInstructions
        instructions = DrawingInstructions.from_vector(pred_vec)
        rendered = renderer.render(instructions)
        orig = target_images[i]

        rendered_m = evaluator.evaluate(rendered)
        orig_m = evaluator.evaluate(orig)
        sim = evaluator._clip_image_similarity(rendered, orig)

        # Compare with rule-based decomposer
        rule_instr = decompose_spatial(images[i])
        rule_rendered = renderer.render(rule_instr)
        rule_sim = evaluator._clip_image_similarity(rule_rendered, orig)

        comp = Image.new("RGB", (384, 128))
        comp.paste(orig, (0, 0))
        comp.paste(rule_rendered, (128, 0))
        comp.paste(rendered, (256, 0))
        comp.save(os.path.join(save_dir, "%02d_%s.png" % (i, labels[i])))

        print("  [%d] %s: rule_sim=%.2f learned_sim=%.2f" % (
            i, labels[i], rule_sim, sim), flush=True)

    # Save
    model_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    os.makedirs(model_dir, exist_ok=True)
    decomposer.save(os.path.join(model_dir, "learnable_decomposer.json"))
    print("\nModel saved to %s" % model_dir, flush=True)
    print("Samples saved to %s" % save_dir, flush=True)


if __name__ == "__main__":
    main()
