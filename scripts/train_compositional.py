"""Train SequenceGenerator on CIFAR-10 real data.

Two modes:
1. Fast mode (default): Uses random projections as CLIP proxy, ~30s
2. CLIP mode (--clip): Uses real CLIP encoding, ~30min on CPU

Usage:
    python scripts/train_compositional.py
    python scripts/train_compositional.py --clip --samples 200
"""

import sys
import os
import time
import argparse
import json
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.generator.sequence_generator import SequenceGenerator
from ai.multimodal.generator.image_generator import ImageGenerator
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
from ai.multimodal.primitives.primitive_types import DrawingInstructions, Point, Plane
from ai.multimodal.evaluation.generation_evaluator import GenerationEvaluator


def load_cifar10_images(data_dir: str, n_samples: int=500,
                        classes: list=None, seed: int=42):
    """Load CIFAR-10 images as numpy arrays."""
    index_path = os.path.join(data_dir, "index.json")
    with open(index_path, 'r') as f:
        idx = json.load(f)
    
    all_classes = idx["classes"]
    if classes:
        all_classes=[c for c in all_classes if c in classes]
    
    images=[]
    labels=[]
    rng = np.random.default_rng(seed)
    
    for cls in all_classes:
        cls_dir = os.path.join(data_dir, cls)
        if not os.path.isdir(cls_dir):
            continue
        npy_files=[f for f in os.listdir(cls_dir) if f.endswith('.npy')]
        if len(npy_files) > 50:
            npy_files = list(rng.choice(npy_files, 50, replace=False))
        
        for f in npy_files:
            arr = np.load(os.path.join(cls_dir, f))
            images.append(arr)
            labels.append(cls)
    
    # Sample subset
    if n_samples < len(images):
        indices = rng.choice(len(images), n_samples, replace=False)
        images=[images[i] for i in indices]
        labels=[labels[i] for i in indices]
    
    return images, labels


def images_to_embeddings(images: list, use_clip: bool=False):
    """Convert images to CLIP-like embeddings.
    
    Fast mode: random projection (deterministic from image hash).
    CLIP mode: real CLIP encoding.
    """
    if use_clip:
        try:
            from ai.multimodal.semantic_visual import SemanticVisualEncoder
            encoder = SemanticVisualEncoder()
            embeddings=[]
            for img_arr in images:
                pil = Image.fromarray(img_arr).resize((224, 224), Image.LANCZOS)
                import io
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                emb = encoder.encode(buf.getvalue())
                if emb is not None:
                    embeddings.append(emb)
                else:
                    embeddings.append(np.zeros(512, dtype=np.float32))
            return np.array(embeddings, dtype=np.float32)
        except Exception as e:
            print(f"CLIP encoding failed: {e}, falling back to random projection")
    
    # Fast random projection (deterministic)
    rng = np.random.default_rng(123)
    proj = rng.normal(0, 1, (32 * 32 * 3, 512)).astype(np.float32)
    proj /= np.linalg.norm(proj, axis=1, keepdims=True)
    
    embeddings=[]
    for img_arr in images:
        flat = img_arr.flatten().astype(np.float32) / 255.0
        emb = flat @ proj
        emb = emb / (np.linalg.norm(emb) + 1e-8)
        embeddings.append(emb)
    
    return np.array(embeddings, dtype=np.float32)


def images_to_primitives(images: list, labels: list):
    """Convert images to primitive drawing instructions.
    
    Creates simple geometric primitives that approximate each image:
    - Background plane from dominant color
    - Points for bright spots
    - Lines for edges
    """
    sequences=[]
    
    for img_arr, label in zip(images, labels):
        arr = img_arr.astype(np.float32)
        
        # Dominant color from center region
        h, w = arr.shape[:2]
        center = arr[h//4:3*h//4, w//4:3*w//4]
        dominant = tuple(int(c) for c in center.mean(axis=(0, 1)))
        
        # Build drawing instructions
        bg_color = dominant
        
        # Find bright regions as points
        gray = arr.mean(axis=2)
        bright_mask = gray > gray.mean() + gray.std()
        bright_coords = np.argwhere(bright_mask)
        
        points=[]
        if len(bright_coords) > 0:
            # Sample up to 5 bright spots
            if len(bright_coords) > 5:
                indices = np.random.default_rng(42).choice(len(bright_coords), 5, replace=False)
                bright_coords = bright_coords[indices]
            
            for y, x in bright_coords:
                px = float(x) / w
                py = float(y) / h
                r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
                points.append(Point(px, py, (r, g, b), 0.05))
        
        # Find edges as lines
        dx = np.abs(np.diff(gray, axis=1))
        dy = np.abs(np.diff(gray, axis=0))
        edge_threshold=30
        
        lines=[]
        edge_y, edge_x = np.where(dx > edge_threshold)
        if len(edge_x) > 0:
            # Sample up to 3 edge segments
            if len(edge_x) > 10:
                indices = np.random.default_rng(42).choice(len(edge_x), 10, replace=False)
                edge_x, edge_y = edge_x[indices], edge_y[indices]
            
            for i in range(0, len(edge_x) - 1, 2):
                from ai.multimodal.primitives.primitive_types import Line
                sx, sy = float(edge_x[i]) / w, float(edge_y[i]) / h
                ex, ey = float(edge_x[i+1]) / w, float(edge_y[i+1]) / h
                r, g, b = int(arr[edge_y[i], min(edge_x[i], w-1), 0]), \
                           int(arr[edge_y[i], min(edge_x[i], w-1), 1]), \
                           int(arr[edge_y[i], min(edge_x[i], w-1), 2])
                lines.append(Line(
                    Point(sx, sy, (0, 0, 0), 0),
                    Point(ex, ey, (0, 0, 0), 0),
                    0.02,
                    (r, g, b)
                ))
                if len(lines) >= 3:
                    break
        
        # Background plane
        planes=[Plane(
            [Point(0.0, 0.0, (0,0,0), 0), Point(1.0, 0.0, (0,0,0), 0),
             Point(1.0, 1.0, (0,0,0), 0), Point(0.0, 1.0, (0,0,0), 0)],
            bg_color, (0, 0, 0), 0.0
        )]
        
        instructions = DrawingInstructions(
            points=points, lines=lines, planes=planes,
            background_color=bg_color
        )
        sequences.append(instructions)
    
    return sequences


def train(images, labels, clip_embeddings, instructions_list,
          epochs=50, lr=0.005, hidden_dim=64):
    """Train SequenceGenerator on real data."""
    encoder = PrimitiveEncoder()
    
    # Encode instructions to primitive embeddings
    print(f"Encoding {len(instructions_list)} instructions to embeddings...")
    primitive_seqs=[]
    for instr in instructions_list:
        emb = encoder.encode(instr)
        primitive_seqs.append([emb])  # Wrap as single-step sequence
    
    # Split into train/val
    n = len(clip_embeddings)
    n_train = int(n * 0.8)
    indices = np.random.permutation(n)
    
    train_embs=[clip_embeddings[i] for i in indices[:n_train]]
    train_seqs=[primitive_seqs[i] for i in indices[:n_train]]
    val_embs=[clip_embeddings[i] for i in indices[n_train:]]
    val_seqs=[primitive_seqs[i] for i in indices[n_train:]]
    
    print(f"Train: {len(train_embs)}, Val: {len(val_embs)}")
    
    # Train
    gen = SequenceGenerator(hidden_dim=hidden_dim, max_steps=10)
    t0 = time.time()
    result = gen.train(train_embs, train_seqs, epochs=epochs, lr=lr)
    t1 = time.time()
    
    print(f"Training: {t1 - t0:.1f}s")
    print(f"Final loss: {result['final_loss']:.6f}")
    print(f"Loss reduction: {result['history'][0]:.4f} → {result['final_loss']:.6f}")
    
    # Evaluate on validation set
    if val_embs:
        val_losses=[]
        for emb, seq in zip(val_embs, val_seqs):
            loss = gen.train_step(emb, seq, lr=0.0)  # No update, just compute loss
            val_losses.append(loss)
        print(f"Val loss: {np.mean(val_losses):.6f}")
    
    return gen, encoder


def generate_samples(gen, encoder, labels, n=5):
    """Generate sample images."""
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    evaluator = GenerationEvaluator()
    
    print(f"\nGenerating {n} sample images...")
    
    for i in range(min(n, len(labels))):
        # Create a random CLIP-like embedding
        rng = np.random.default_rng(i * 42)
        clip_emb = rng.normal(0, 1, 512).astype(np.float32)
        clip_emb /= np.linalg.norm(clip_emb) + 1e-8
        
        # Generate
        primitives = gen.generate_deterministic(clip_emb)
        if primitives:
            instructions = encoder.decode(primitives[0])
            img = renderer.render(instructions)
            
            # Evaluate
            metrics = evaluator.evaluate(img)
            arr = np.array(img)
            print(f"  [{i}] {labels[i] if i < len(labels) else 'unknown'}: "
                  f"brightness={metrics['mean_brightness']:.2f}, "
                  f"colors={metrics['color_coverage']:.2f}, "
                  f"edges={metrics['edge_density']:.2f}")
    
    return gen


def save_models(gen, encoder, save_dir):
    """Save trained models."""
    os.makedirs(save_dir, exist_ok=True)
    gen.save(os.path.join(save_dir, "sequence_generator.json"))
    encoder.save(os.path.join(save_dir, "primitive_encoder.json"))
    print(f"\nModels saved to {save_dir}")


def main():
    parser = argparse.ArgumentParser(description="Train compositional image generator on CIFAR-10")
    parser.add_argument("--samples", type=int, default=200, help="Number of CIFAR-10 samples")
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--lr", type=float, default=0.005, help="Learning rate")
    parser.add_argument("--clip", action="store_true", help="Use real CLIP encoding (slow)")
    parser.add_argument("--hidden", type=int, default=64, help="RNN hidden dim")
    args = parser.parse_args()
    
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "cifar10")
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    
    print("=" * 60)
    print("Compositional Image Generator - CIFAR-10 Training")
    print("=" * 60)
    print(f"Mode: {'CLIP' if args.clip else 'Random projection'}")
    print(f"Samples: {args.samples}, Epochs: {args.epochs}, LR: {args.lr}")
    
    # Load data
    print("\n[1/5] Loading CIFAR-10 images...")
    images, labels = load_cifar10_images(data_dir, n_samples=args.samples)
    print(f"  Loaded {len(images)} images, {len(set(labels))} classes")
    
    # Convert to embeddings
    print(f"\n[2/5] Converting to embeddings ({args.clip and 'CLIP' or 'random projection'})...")
    t0 = time.time()
    clip_embeddings = images_to_embeddings(images, use_clip=args.clip)
    t1 = time.time()
    print(f"  Shape: {clip_embeddings.shape}, time: {t1 - t0:.1f}s")
    
    # Convert to primitives
    print("\n[3/5] Creating primitive decompositions...")
    instructions_list = images_to_primitives(images, labels)
    print(f"  Created {len(instructions_list)} drawing instructions")
    
    # Train
    print(f"\n[4/5] Training SequenceGenerator (hidden_dim={args.hidden})...")
    gen, encoder = train(images, labels, clip_embeddings, instructions_list,
                         epochs=args.epochs, lr=args.lr, hidden_dim=args.hidden)
    
    # Generate samples
    print("\n[5/5] Generating sample images...")
    generate_samples(gen, encoder, labels, n=5)
    
    # Save
    save_models(gen, encoder, save_dir)
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
