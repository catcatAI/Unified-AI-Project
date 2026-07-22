"""Quick demo: train SequenceGenerator on random data and generate images."""

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.generator.sequence_generator import SequenceGenerator
from ai.multimodal.generator.training_data import TrainingDataGenerator
from ai.multimodal.generator.image_generator import ImageGenerator
from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer


def main():
    print("=" * 60)
    print("Compositional Image Generation - Phase 2 Demo")
    print("=" * 60)
    
    # Step 1: Generate random training data
    print("\n[1/4] Generating random training data...")
    data_gen = TrainingDataGenerator()
    data = data_gen.generate_random_primitives(n_samples=100, seed=42)
    print(f"  Samples: {len(data['clip_embeddings'])}")
    print(f"  Clip dim: {data['clip_embeddings'][0].shape}")
    print(f"  Sequence lengths: {[len(s) for s in data['primitive_sequences'][:5]]}...")
    
    # Step 2: Train SequenceGenerator
    print("\n[2/4] Training SequenceGenerator...")
    gen = SequenceGenerator(hidden_dim=64, max_steps=10)
    t0 = time.time()
    result = gen.train(
        data["clip_embeddings"],
        data["primitive_sequences"],
        epochs=50,
        lr=0.005,
    )
    t1 = time.time()
    print(f"  Training time: {t1 - t0:.1f}s")
    print(f"  Final loss: {result['final_loss']:.6f}")
    print(f"  Loss reduction: {result['history'][0]:.4f} → {result['final_loss']:.6f}")
    
    # Step 3: Generate images
    print("\n[3/4] Generating images...")
    encoder = PrimitiveEncoder()
    renderer = PrimitiveRenderer(canvas_size=(128, 128))
    img_gen = ImageGenerator(
        sequence_generator=gen,
        primitive_encoder=encoder,
        renderer=renderer,
    )
    
    texts=["a red circle", "a blue square", "a green blob"]
    for text in texts:
        img = img_gen.generate_from_text(text, canvas_size=(128, 128))
        arr = np.array(img)
        print(f"  '{text}' → {img.size}, mean={arr.mean():.1f}, non-white pixels={np.sum(arr < 250) // 3}")
    
    # Step 4: Save model
    print("\n[4/4] Saving model...")
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    os.makedirs(save_dir, exist_ok=True)
    gen.save(os.path.join(save_dir, "sequence_generator.json"))
    encoder.save(os.path.join(save_dir, "primitive_encoder.json"))
    print(f"  Saved to {save_dir}")
    
    print("\n" + "=" * 60)
    print("Phase 2 demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
