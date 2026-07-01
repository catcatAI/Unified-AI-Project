"""
Train VisualDecoder texture weights via FullTrainingPipeline.

Runs Phase 1 (contrastive), Phase 2 (reconstruction), Phase 3a (texture)
and saves all VisualDecoder weights to data/multimodal/weights/p29_trained.npz.

Usage:
    python scripts/train_visual_decoder.py
    python scripts/train_visual_decoder.py --texture-steps 100 --lr 0.005
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.training_pipeline import FullTrainingPipeline
from ai.multimodal.visual_decoder import save_visual_decoder_weights


def main():
    parser = argparse.ArgumentParser(description="Train VisualDecoder texture weights")
    parser.add_argument("--contrastive-epochs", type=int, default=10)
    parser.add_argument("--contrastive-pairs", type=int, default=20)
    parser.add_argument("--recon-epochs", type=int, default=10)
    parser.add_argument("--recon-samples", type=int, default=10)
    parser.add_argument("--texture-steps", type=int, default=100,
                        help="Gradient steps for texture training (default: 100, was 50)")
    parser.add_argument("--texture-lr", type=float, default=0.001)
    parser.add_argument("--lr", type=float, default=0.01)
    args = parser.parse_args()

    print("=" * 60)
    print("VisualDecoder Texture Training Pipeline")
    print("=" * 60)

    pipeline = FullTrainingPipeline()

    # Phase 1 + 2
    print("\n=== Phase 1 + 2: Contrastive + Reconstruction ===")
    results = pipeline.run(
        contrastive_epochs=args.contrastive_epochs,
        contrastive_pairs=args.contrastive_pairs,
        recon_epochs=args.recon_epochs,
        recon_samples=args.recon_samples,
        lr=args.lr,
    )
    print(f"  Contrastive final loss: {results['contrastive']['final_loss']:.6f}")
    for mod, res in results["reconstruction"].items():
        print(f"  {mod} reconstruction final loss: {res['final_loss']:.6f}")

    # Phase 3a: Texture training
    print("\n=== Phase 3a: Texture branch training ===")
    tex_result = pipeline.train_texture(batch_size=4, steps=args.texture_steps, lr=args.texture_lr)
    print(f"  Texture final loss: {tex_result['final_loss']:.6f}")

    # Save VisualDecoder weights
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "p29_trained.npz")
    save_visual_decoder_weights(pipeline._visual_decoder, str(save_path))
    print(f"\n✅ Saved VisualDecoder weights to {save_path}")

    # Verify
    from ai.multimodal.visual_decoder import VisualDecoder, load_default_visual_decoder_weights
    vd = VisualDecoder()
    load_default_visual_decoder_weights(vd)
    w = vd.get_projection()
    print(f"  Load verification: W shape={w[0].shape}, sum={w[0].sum():.2f}")
    print("\nDone!")


if __name__ == "__main__":
    main()
