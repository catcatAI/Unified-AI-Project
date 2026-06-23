"""Train learnable decomposer with REINFORCE on rendering loss.

Instead of predicting rule-based primitives, this trains the decomposer
to produce primitives that RENDER into images similar to the target.

Approach:
1. Decomposer outputs primitive params (263-dim)
2. Render each output
3. Compare rendered image with target (pixel loss)
4. Update decomposer using REINFORCE (score = negative loss)

No differentiable renderer needed. Works with PIL.
"""

import sys, os, json, time, math
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.learnable_decomposer import LearnableDecomposer
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def render_loss(decomposer, clip_emb, target_arr, renderer, sigma=0.1, n_samples=5):
    """REINFORCE: sample multiple decompositions, score each, return gradient estimate.
    
    Args:
        decomposer: LearnableDecomposer
        clip_emb: (512,) CLIP embedding
        target_arr: (H, W, 3) target image as float [0, 1]
        renderer: PrimitiveRenderer
        sigma: noise std for exploration
        n_samples: number of samples per update
        
    Returns:
        avg_loss: average pixel loss of samples
        grad_estimate: approximate gradient of decomposer output w.r.t. loss
    """
    # Get mean prediction
    mean_vec, cache = decomposer.forward(clip_emb)
    
    losses = []
    weighted_deltas = []
    
    for _ in range(n_samples):
        # Sample: add noise to mean prediction
        noise = np.random.randn(TOTAL_DIM).astype(np.float32) * sigma
        sample_vec = np.clip(mean_vec + noise, 0.0, 1.0)
        
        # Render
        instructions = DrawingInstructions.from_vector(sample_vec)
        rendered = renderer.render(instructions)
        rendered_arr = np.array(rendered, dtype=np.float32) / 255.0
        
        # Loss
        loss = float(np.mean((rendered_arr - target_arr) ** 2))
        losses.append(loss)
        
        # REINFORCE gradient: d(log p)/d(mu) * reward
        # For Gaussian: d(log p)/d(mu) = (x - mu) / sigma^2
        # reward = -loss (higher is better)
        reward = -loss
        d_log_p = noise / (sigma ** 2)
        weighted_deltas.append(d_log_p * reward)
    
    avg_loss = np.mean(losses)
    
    # Average gradient estimate
    grad_estimate = np.mean(weighted_deltas, axis=0)
    
    return avg_loss, grad_estimate, mean_vec, cache


def train_reinforce(clip_embeddings, target_images, renderer,
                    epochs=50, lr=0.001, sigma=0.15, n_samples=5,
                    batch_size=4):
    """Train decomposer with REINFORCE."""
    
    decomposer = LearnableDecomposer(clip_dim=512, hidden_dim=256)
    
    # Convert targets
    target_arrs = [np.array(img, dtype=np.float32) / 255.0 for img in target_images]
    
    # Update CLIP stats
    for clip_emb in clip_embeddings:
        decomposer.update_clip_stats(clip_emb)
    
    n = len(clip_embeddings)
    losses = []
    
    for epoch in range(epochs):
        indices = np.random.permutation(n)
        epoch_loss = 0.0
        n_batches = 0
        
        for start in range(0, n, batch_size):
            batch_idx = indices[start:start + batch_size]
            batch_loss = 0.0
            
            # Accumulate gradients over batch
            batch_grad_W1 = np.zeros_like(decomposer._W1)
            batch_grad_b1 = np.zeros_like(decomposer._b1)
            batch_grad_W2 = np.zeros_like(decomposer._W2)
            batch_grad_b2 = np.zeros_like(decomposer._b2)
            
            for idx in batch_idx:
                avg_loss, grad_estimate, mean_vec, cache = render_loss(
                    decomposer, clip_embeddings[idx], target_arrs[idx],
                    renderer, sigma=sigma, n_samples=n_samples)
                batch_loss += avg_loss
                
                # Backprop grad_estimate through decomposer
                # grad_estimate is d(loss)/d(mean_vec)
                # Need d(loss)/d(W1,b1,W2,b2) through the network
                
                # Through sigmoid: d(sig)/dz = sig*(1-sig)
                d_z2 = grad_estimate * cache["sig"] * (1 - cache["sig"])
                
                # W2 gradient
                batch_grad_W2 += np.outer(cache["h"], d_z2)
                batch_grad_b2 += d_z2
                
                # Through ReLU
                d_h = d_z2 @ decomposer._W2.T
                d_z1 = d_h * (cache["z1"] > 0).astype(np.float32)
                
                # W1 gradient
                batch_grad_W1 += np.outer(cache["x"], d_z1)
                batch_grad_b1 += d_z1
            
            # Average and clip gradients
            bs = len(batch_idx)
            for g in [batch_grad_W1, batch_grad_b1, batch_grad_W2, batch_grad_b2]:
                g /= bs
                np.clip(g, -0.1, 0.1, out=g)
            
            # Update
            decomposer._W1 -= lr * batch_grad_W1
            decomposer._b1 -= lr * batch_grad_b1
            decomposer._W2 -= lr * batch_grad_W2
            decomposer._b2 -= lr * batch_grad_b2
            
            epoch_loss += batch_loss / bs
            n_batches += 1
        
        avg_epoch_loss = epoch_loss / n_batches
        losses.append(avg_epoch_loss)
        
        if epoch % 5 == 0:
            print("  Epoch %d/%d - loss: %.6f" % (epoch, epochs, avg_epoch_loss), flush=True)
    
    return decomposer, losses


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

    # CLIP embeddings
    print("CLIP encoding...", flush=True)
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
    print("CLIP done: %d embeddings" % len(clip_embs), flush=True)

    # Target images
    target_images = [Image.fromarray(img).resize((128, 128), Image.LANCZOS) for img in images]
    renderer = PrimitiveRenderer((128, 128))

    # Train with REINFORCE
    print("\nTraining with REINFORCE...", flush=True)
    t0 = time.time()
    decomposer, losses = train_reinforce(
        clip_embs, target_images, renderer,
        epochs=30, lr=0.0005, sigma=0.2, n_samples=3, batch_size=4
    )
    print("Done: %.1fs, final_loss=%.6f" % (time.time() - t0, losses[-1]), flush=True)

    # Evaluate
    evaluator = GenerationEvaluator()
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples_reinforce")
    os.makedirs(save_dir, exist_ok=True)

    print("\nGenerated:", flush=True)
    for i in range(min(15, len(images))):
        pred_vec, _ = decomposer.forward(clip_embs[i])
        instructions = DrawingInstructions.from_vector(pred_vec)
        rendered = renderer.render(instructions)
        orig = target_images[i]

        sim = evaluator._clip_image_similarity(rendered, orig)
        orig_m = evaluator.evaluate(orig)
        ren_m = evaluator.evaluate(rendered)

        comp = Image.new("RGB", (256, 128))
        comp.paste(orig, (0, 0))
        comp.paste(rendered, (128, 0))
        comp.save(os.path.join(save_dir, "%02d_%s.png" % (i, labels[i])))

        print("  [%d] %s: sim=%.2f bright=%.2f->%.2f colors=%.2f->%.2f" % (
            i, labels[i], sim, orig_m["mean_brightness"], ren_m["mean_brightness"],
            orig_m["color_coverage"], ren_m["color_coverage"]), flush=True)

    decomposer.save(os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights", "learnable_decomposer_reinforce.json"))
    print("Saved", flush=True)


if __name__ == "__main__":
    main()
