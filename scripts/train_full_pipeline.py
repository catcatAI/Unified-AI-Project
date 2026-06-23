"""Full training pipeline: fix encoder, then train generator with real CLIP.

Step 1: Train PrimitiveEncoder on CIFAR-10 decomposed primitives
Step 2: Train SequenceGenerator with real CLIP embeddings
Step 3: Evaluate generated images

Usage:
    python scripts/train_full_pipeline.py
    python scripts/train_full_pipeline.py --samples 500 --epochs 100
"""

import sys
import os
import time
import json
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.primitives.primitive_types import (
    DrawingInstructions, Point, Line, Plane
)
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


# ─── Better Primitive Decomposition ─────────────────────────────────────

def decompose_image(img_arr: np.ndarray) -> DrawingInstructions:
    """Decompose a numpy image into DrawingInstructions with better color extraction.
    
    Improvements over previous version:
    - Dominant color from k-means-like clustering (3 bins)
    - Bright regions mapped to colored points
    - Edge detection for lines with actual edge colors
    - Background plane from dominant color
    """
    arr = img_arr.astype(np.float32)
    h, w = arr.shape[:2]
    
    # 1. Dominant color: quantize each channel to 4 levels, find most common
    quantized = (arr / 64).astype(int)  # 4 bins per channel
    quantized = np.clip(quantized, 0, 3)
    pixels = quantized.reshape(-1, 3)
    
    # Find most common color bin
    color_counts = {}
    for p in pixels:
        key = (int(p[0]), int(p[1]), int(p[2]))
        color_counts[key] = color_counts.get(key, 0) + 1
    
    sorted_colors = sorted(color_counts.items(), key=lambda x: -x[1])
    dominant_bin = sorted_colors[0][0]
    
    # Map bin back to center value
    dominant_color = tuple(int(c * 64 + 32) for c in dominant_bin)
    dominant_color = tuple(max(0, min(255, c)) for c in dominant_color)
    
    # 2. Find accent colors (top 3 non-dominant colors)
    accent_colors = []
    for bin_key, count in sorted_colors[1:6]:
        if count > h * w * 0.01:  # At least 1% of pixels
            accent = tuple(int(c * 64 + 32) for c in bin_key)
            accent = tuple(max(0, min(255, c)) for c in accent)
            accent_colors.append(accent)
    
    # 3. Find bright regions → colored points
    gray = arr.mean(axis=2)
    bright_threshold = gray.mean() + gray.std()
    bright_mask = gray > bright_threshold
    
    points = []
    bright_coords = np.argwhere(bright_mask)
    if len(bright_coords) > 0:
        # Grid sample for even distribution
        step = max(1, len(bright_coords) // 8)
        sampled = bright_coords[::step][:8]
        
        for y, x in sampled:
            px = float(x) / w
            py = float(y) / h
            # Get actual color at this pixel
            r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
            # Make it an accent color if available
            color = accent_colors[0] if accent_colors else (r, g, b)
            points.append(Point(px, py, color, 0.06))
    
    # 4. Edge detection → lines with edge colors
    from PIL import Image as PILImage
    pil_gray = PILImage.fromarray(gray.astype(np.uint8))
    edges = pil_gray.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edges).astype(np.float32)
    
    edge_threshold = edge_arr.mean() + edge_arr.std() * 0.5
    edge_mask = edge_arr > edge_threshold
    
    lines = []
    edge_coords = np.argwhere(edge_mask)
    if len(edge_coords) > 0:
        step = max(1, len(edge_coords) // 6)
        sampled = edge_coords[::step][:6]
        
        for i in range(0, len(sampled) - 1, 2):
            y1, x1 = sampled[i]
            y2, x2 = sampled[i + 1]
            
            sx, sy = float(x1) / w, float(y1) / h
            ex, ey = float(x2) / w, float(y2) / h
            
            # Edge color from midpoint
            my = (y1 + y2) // 2
            mx = (x1 + x2) // 2
            r = int(arr[min(my, h-1), min(mx, w-1), 0])
            g = int(arr[min(my, h-1), min(mx, w-1), 1])
            b = int(arr[min(my, h-1), min(mx, w-1), 2])
            
            # Use a distinct color if available
            color = accent_colors[1] if len(accent_colors) > 1 else (r, g, b)
            lines.append(Line(
                Point(sx, sy, (0, 0, 0), 0),
                Point(ex, ey, (0, 0, 0), 0),
                0.03,
                color
            ))
    
    # 5. Background plane from dominant color
    planes = [Plane(
        [Point(0.0, 0.0, (0,0,0), 0), Point(1.0, 0.0, (0,0,0), 0),
         Point(1.0, 1.0, (0,0,0), 0), Point(0.0, 1.0, (0,0,0), 0)],
        dominant_color, (0, 0, 0), 0.0
    )]
    
    return DrawingInstructions(
        points=points, lines=lines, planes=planes,
        background_color=dominant_color
    )


# ─── CLIP Encoding ──────────────────────────────────────────────────────

def get_clip_encoder():
    """Get real CLIP encoder if available, else None."""
    try:
        from ai.multimodal.semantic_visual import SemanticVisualEncoder
        encoder = SemanticVisualEncoder()
        # Quick test
        test_img = Image.new("RGB", (64, 64), (128, 128, 128))
        import io
        buf = io.BytesIO()
        test_img.save(buf, format="PNG")
        result = encoder.encode(buf.getvalue())
        if result is not None and result.shape == (512,):
            print("  CLIP encoder loaded successfully")
            return encoder
    except Exception as e:
        print(f"  CLIP not available: {e}")
    return None


def encode_images_with_clip(images, clip_encoder):
    """Encode images with real CLIP."""
    embeddings = []
    for img_arr in images:
        pil = Image.fromarray(img_arr).resize((224, 224), Image.LANCZOS)
        import io
        buf = io.BytesIO()
        pil.save(buf, format="PNG")
        emb = clip_encoder.encode(buf.getvalue())
        if emb is not None:
            embeddings.append(emb)
        else:
            embeddings.append(np.zeros(512, dtype=np.float32))
    return np.array(embeddings, dtype=np.float32)


def encode_images_random(images):
    """Encode images with random projection (fast fallback)."""
    rng = np.random.default_rng(123)
    proj = rng.normal(0, 1, (32 * 32 * 3, 512)).astype(np.float32)
    proj /= np.linalg.norm(proj, axis=1, keepdims=True)
    
    embeddings = []
    for img_arr in images:
        flat = img_arr.flatten().astype(np.float32) / 255.0
        emb = flat @ proj
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        embeddings.append(emb)
    return np.array(embeddings, dtype=np.float32)


# ─── Training ───────────────────────────────────────────────────────────

def load_cifar10(data_dir, n_samples=200, seed=42):
    """Load CIFAR-10 images."""
    index_path = os.path.join(data_dir, "index.json")
    with open(index_path, 'r') as f:
        idx = json.load(f)
    
    all_classes = idx["classes"]
    images = []
    labels = []
    rng = np.random.default_rng(seed)
    
    for cls in all_classes:
        cls_dir = os.path.join(data_dir, cls)
        if not os.path.isdir(cls_dir):
            continue
        npy_files = [f for f in os.listdir(cls_dir) if f.endswith('.npy')]
        if len(npy_files) > 30:
            npy_files = list(rng.choice(npy_files, 30, replace=False))
        for f in npy_files:
            arr = np.load(os.path.join(cls_dir, f))
            images.append(arr)
            labels.append(cls)
    
    if n_samples < len(images):
        indices = rng.choice(len(images), n_samples, replace=False)
        images = [images[i] for i in indices]
        labels = [labels[i] for i in indices]
    
    return images, labels


def train_encoder(instructions_list, epochs=200, lr=0.005):
    """Step 1: Train PrimitiveEncoder to faithfully encode/decode primitives."""
    print("\n[Step 1] Training PrimitiveEncoder (autoencoder)...")
    encoder = PrimitiveEncoder()
    
    result = encoder.train(instructions_list, epochs=epochs, lr=lr)
    print(f"  Loss: {result['best_loss']:.6f} ({result['epochs_trained']} epochs)")
    
    # Verify decode quality
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    sample = instructions_list[:3]
    for i, instr in enumerate(sample):
        emb = encoder.encode(instr)
        decoded = encoder.decode(emb)
        orig_img = np.array(renderer.render(instr)).astype(float)
        dec_img = np.array(renderer.render(decoded)).astype(float)
        mse = np.mean((orig_img - dec_img) ** 2)
        brightness = np.mean(dec_img) / 255.0
        print(f"  Sample {i}: MSE={mse:.1f}, brightness={brightness:.2f}")
    
    return encoder


def train_generator(clip_embeddings, primitive_embeddings, epochs=100, lr=0.005):
    """Step 2: Train SequenceGenerator to map CLIP → primitive embeddings."""
    from ai.multimodal.generator.sequence_generator import SequenceGenerator
    
    print(f"\n[Step 2] Training SequenceGenerator ({len(clip_embeddings)} pairs)...")
    gen = SequenceGenerator(hidden_dim=64, max_steps=5)
    
    # Wrap as single-step sequences
    sequences = [[emb] for emb in primitive_embeddings]
    
    result = gen.train(clip_embeddings, sequences, epochs=epochs, lr=lr)
    print(f"  Loss: {result['history'][0]:.6f} → {result['final_loss']:.6f}")
    
    return gen


def evaluate_pipeline(gen, encoder, images, labels, n=5):
    """Step 3: Generate and evaluate images."""
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    evaluator = GenerationEvaluator()
    
    print(f"\n[Step 3] Generating {n} sample images...")
    
    for i in range(min(n, len(images))):
        # Use a deterministic embedding (from training data index)
        rng = np.random.default_rng(i * 7 + 1)
        clip_emb = rng.normal(0, 1, 512).astype(np.float32)
        clip_emb /= np.linalg.norm(clip_emb) + 1e-8
        
        # Generate
        primitives = gen.generate_deterministic(clip_emb)
        if primitives:
            instructions = encoder.decode(primitives[0])
            img = renderer.render(instructions)
            metrics = evaluator.evaluate(img)
            
            # Compare with original
            orig_img = Image.fromarray(images[i]).resize((128, 128), Image.LANCZOS)
            orig_metrics = evaluator.evaluate(orig_img)
            
            print(f"  [{i}] {labels[i]}: "
                  f"brightness={metrics['mean_brightness']:.2f} (orig={orig_metrics['mean_brightness']:.2f}), "
                  f"colors={metrics['color_coverage']:.2f} (orig={orig_metrics['color_coverage']:.2f})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--encoder-epochs", type=int, default=200)
    parser.add_argument("--generator-epochs", type=int, default=100)
    parser.add_argument("--lr", type=float, default=0.005)
    args = parser.parse_args()
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    
    print("=" * 60)
    print("Full Compositional Image Generation Training Pipeline")
    print("=" * 60)
    
    # Load data
    print("\n[0] Loading CIFAR-10...")
    images, labels = load_cifar10(data_dir, n_samples=args.samples)
    print(f"  {len(images)} images, {len(set(labels))} classes")
    
    # Decompose images into primitives
    print("\n[*] Decomposing images into primitives...")
    t0 = time.time()
    instructions_list = [decompose_image(img) for img in images]
    print(f"  {len(instructions_list)} instructions ({time.time()-t0:.1f}s)")
    
    # Verify decomposition quality
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    evaluator = GenerationEvaluator()
    for i in range(min(3, len(images))):
        orig = Image.fromarray(images[i]).resize((128, 128), Image.LANCZOS)
        decomp = renderer.render(instructions_list[i])
        orig_m = evaluator.evaluate(orig)
        dec_m = evaluator.evaluate(decomp)
        print(f"  Decomposition [{i}] {labels[i]}: "
              f"brightness {orig_m['mean_brightness']:.2f}→{dec_m['mean_brightness']:.2f}, "
              f"colors {orig_m['color_coverage']:.2f}→{dec_m['color_coverage']:.2f}")
    
    # Step 1: Train encoder
    encoder = train_encoder(instructions_list, epochs=args.encoder_epochs, lr=args.lr)
    
    # Get CLIP embeddings
    print("\n[*] Encoding images...")
    clip_encoder = get_clip_encoder()
    if clip_encoder:
        clip_embeddings = encode_images_with_clip(images, clip_encoder)
        print(f"  Real CLIP: {clip_embeddings.shape}")
    else:
        clip_embeddings = encode_images_random(images)
        print(f"  Random projection: {clip_embeddings.shape}")
    
    # Encode instructions to primitive embeddings
    print("\n[*] Encoding instructions to primitive embeddings...")
    primitive_embeddings = np.array([encoder.encode(instr) for instr in instructions_list])
    print(f"  Shape: {primitive_embeddings.shape}")
    
    # Step 2: Train generator
    gen = train_generator(clip_embeddings, primitive_embeddings,
                          epochs=args.generator_epochs, lr=args.lr)
    
    # Step 3: Evaluate
    evaluate_pipeline(gen, encoder, images, labels, n=5)
    
    # Save
    os.makedirs(save_dir, exist_ok=True)
    gen.save(os.path.join(save_dir, "sequence_generator.json"))
    encoder.save(os.path.join(save_dir, "primitive_encoder.json"))
    print(f"\nModels saved to {save_dir}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
