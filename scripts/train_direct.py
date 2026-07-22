"""Direct primitive optimization: optimize 263-dim vector per image.

Skip the decomposer entirely. For each image:
1. Initialize random primitives
2. Render with differentiable renderer
3. Compute pixel loss vs target
4. Update primitives directly (gradient descent on 263 params)

This proves primitives CAN represent images. Then we train decomposer to predict these optimized vectors.
"""

import sys
import os
import json
import time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.differentiable_renderer import DifferentiableRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, TOTAL_DIM
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def optimize_primitives(target_arr, renderer, n_iters=200, lr=0.005):
    """Optimize primitive vector to match target image.
    
    Args:
        target_arr: (128, 128, 3) target as float [0, 1]
        renderer: DifferentiableRenderer
        n_iters: optimization iterations
        lr: learning rate
        
    Returns:
        optimized (263,) vector
    """
    # Initialize with some structure
    vec = np.random.uniform(0.2, 0.8, TOTAL_DIM).astype(np.float32)
    
    # Set background to image mean
    vec[0:3] = target_arr.mean(axis=(0, 1))
    
    best_vec = vec.copy()
    best_loss = float('inf')
    
    for it in range(n_iters):
        # Forward
        rendered = renderer.render(vec)
        
        # Loss
        error = rendered - target_arr
        loss = float(np.mean(error ** 2))
        
        if loss < best_loss:
            best_loss = loss
            best_vec = vec.copy()
        
        # Compute gradient via finite differences (subset)
        d_vec = np.zeros(TOTAL_DIM, dtype=np.float32)
        eps=0.015
        probe_dims = np.random.choice(TOTAL_DIM, size=40, replace=False)
        
        for dim in probe_dims:
            v_plus = vec.copy()
            v_plus[dim] = min(1.0, v_plus[dim] + eps)
            r_plus = renderer.render(v_plus)
            l_plus = np.mean((r_plus - target_arr) ** 2)
            
            v_minus = vec.copy()
            v_minus[dim] = max(0.0, v_minus[dim] - eps)
            r_minus = renderer.render(v_minus)
            l_minus = np.mean((r_minus - target_arr) ** 2)
            
            d_vec[dim] = (l_plus - l_minus) / (2 * eps)
        
        # Update
        vec -= lr * d_vec
        vec = np.clip(vec, 0, 1)
    
    return best_vec, best_loss


def main():
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    images, labels=[], []
    for cls in idx["classes"][:3]:
        cls_dir = os.path.join(data_dir, cls)
        for f in sorted(os.listdir(cls_dir))[:5]:
            if f.endswith(".npy"):
                images.append(np.load(os.path.join(cls_dir, f)))
                labels.append(cls)

    print("Loaded %d images" % len(images), flush=True)

    # Differentiable renderer
    diff_renderer = DifferentiableRenderer((128, 128))
    pil_renderer = PrimitiveRenderer((128, 128))
    evaluator = GenerationEvaluator()

    # Target images
    target_arrs=[np.array(Image.fromarray(img).resize((128, 128), Image.LANCZOS),
                            dtype=np.float32) / 255.0 for img in images]

    # Optimize each image
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "samples_direct")
    os.makedirs(save_dir, exist_ok=True)

    optimized_vecs=[]

    print("\nOptimizing primitives per image...", flush=True)
    for i in range(len(images)):
        t0 = time.time()
        opt_vec, opt_loss = optimize_primitives(target_arrs[i], diff_renderer, n_iters=150, lr=0.005)
        optimized_vecs.append(opt_vec)
        
        # Render with PIL (for visual quality)
        instructions = DrawingInstructions.from_vector(opt_vec)
        rendered_pil = pil_renderer.render(instructions)
        orig = Image.fromarray(images[i]).resize((128, 128), Image.LANCZOS)
        diff_rendered = Image.fromarray((diff_renderer.render(opt_vec) * 255).astype(np.uint8))
        
        sim_pil = evaluator._clip_image_similarity(rendered_pil, orig)
        sim_diff = evaluator._clip_image_similarity(diff_rendered, orig)
        
        comp = Image.new("RGB", (384, 128))
        comp.paste(orig, (0, 0))
        comp.paste(diff_rendered, (128, 0))
        comp.paste(rendered_pil, (256, 0))
        comp.save(os.path.join(save_dir, "%02d_%s.png" % (i, labels[i])))
        
        elapsed = time.time() - t0
        print("  [%d] %s: loss=%.4f diff_sim=%.2f pil_sim=%.2f (%.1fs)" % (
            i, labels[i], opt_loss, sim_diff, sim_pil, elapsed), flush=True)

    # Save optimized vectors for decomposer training
    opt_data={
        "vectors": [v.tolist() for v in optimized_vecs],
        "labels": labels[:len(images)]
    }
    with open(os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "optimized_vectors.json"), "w") as f:
        json.dump(opt_data, f)
    print("\nSaved optimized vectors", flush=True)
    print("Samples in %s" % save_dir, flush=True)


if __name__ == "__main__":
    main()
