#!/usr/bin/env python3
"""
Train multimodal encoders/decoders via contrastive pre-training + reconstruction.

Usage:
    python scripts/train_multimodal.py              # Run full pipeline
    python scripts/train_multimodal.py --contrastive-only
    python scripts/train_multimodal.py --recon-only
    python scripts/train_multimodal.py --evaluate-only

Zero external data dependencies — uses synthetic data.
"""

import argparse
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_multimodal")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "apps" / "backend" / "src"))

from ai.multimodal.training_pipeline import FullTrainingPipeline


def main():
    parser = argparse.ArgumentParser(description="Multimodal training pipeline")
    parser.add_argument("--contrastive-epochs", type=int, default=10)
    parser.add_argument("--contrastive-pairs", type=int, default=20)
    parser.add_argument("--recon-epochs", type=int, default=10)
    parser.add_argument("--recon-samples", type=int, default=10)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--contrastive-only", action="store_true")
    parser.add_argument("--recon-only", action="store_true")
    parser.add_argument("--evaluate-only", action="store_true")
    parser.add_argument("--save", type=str, default="", help="Path to save trained weights")
    parser.add_argument("--load", type=str, default="", help="Path to load trained weights")
    args = parser.parse_args()

    print("=" * 60)
    print("  MULTIMODAL TRAINING PIPELINE (P27)")
    print("=" * 60)

    pipeline = FullTrainingPipeline()

    if args.load:
        print(f"\nLoading weights from {args.load}...")
        import numpy as np
        data = np.load(args.load, allow_pickle=True).item()
        if "vision_W" in data:
            pipeline._ls._projections["vision"]["W"][:] = data["vision_W"]
            pipeline._ls._projections["vision"]["b"][:] = data["vision_b"]
        if "audio_W" in data:
            pipeline._ls._projections["audio"]["W"][:] = data["audio_W"]
            pipeline._ls._projections["audio"]["b"][:] = data["audio_b"]
        if "visual_decoder_W" in data:
            pipeline._visual_decoder._W[:] = data["visual_decoder_W"]
            pipeline._visual_decoder._b[:] = data["visual_decoder_b"]
        if "audio_decoder_W" in data:
            pipeline._audio_decoder._W[:] = data["audio_decoder_W"]
            pipeline._audio_decoder._b[:] = data["audio_decoder_b"]
        print("  Loaded successfully")

    if args.evaluate_only:
        print("\n=== Evaluation only ===")
        results = pipeline.evaluate(n_samples=5)
        for mod, res in results.items():
            print(f"  {mod}: avg_reconstruction_loss={res['avg_reconstruction_loss']:.6f}")
        return

    t_start = time.perf_counter()

    if args.recon_only:
        from ai.multimodal.training_pipeline import ReconstructionTrainer
        print("\n=== Phase: Reconstruction only ===")
        trainer = ReconstructionTrainer(pipeline._ls, pipeline._reconstruction)
        result = trainer.train(n_epochs=args.recon_epochs, n_samples=args.recon_samples, lr=args.lr * 0.5)
        elapsed = time.perf_counter() - t_start
        for mod, res in result.items():
            print(f"  {mod}: final_loss={res['final_loss']:.6f} ({elapsed:.1f}s)")
    elif args.contrastive_only:
        print("\n=== Phase: Contrastive only ===")
        result = pipeline._contrastive.train(
            n_epochs=args.contrastive_epochs,
            n_pairs_per_epoch=args.contrastive_pairs,
            lr=args.lr,
        )
        elapsed = time.perf_counter() - t_start
        print(f"  Contrastive final loss: {result['final_loss']:.6f} ({elapsed:.1f}s)")
    else:
        result = pipeline.run(
            contrastive_epochs=args.contrastive_epochs,
            contrastive_pairs=args.contrastive_pairs,
            recon_epochs=args.recon_epochs,
            recon_samples=args.recon_samples,
            lr=args.lr,
        )
        elapsed = time.perf_counter() - t_start
        print(f"\nTraining completed in {elapsed:.1f}s")
        print(f"  Contrastive final loss:    {result['contrastive']['final_loss']:.6f}")
        for mod, res in result.get("reconstruction", {}).items():
            print(f"  {mod} reconstruction loss:  {res['final_loss']:.6f}")

    if args.save:
        import numpy as np
        save_data = {
            "vision_W": pipeline._ls._projections.get("vision", {}).get("W", np.zeros(1)).copy(),
            "vision_b": pipeline._ls._projections.get("vision", {}).get("b", np.zeros(1)).copy(),
            "audio_W": pipeline._ls._projections.get("audio", {}).get("W", np.zeros(1)).copy(),
            "audio_b": pipeline._ls._projections.get("audio", {}).get("b", np.zeros(1)).copy(),
            "visual_decoder_W": pipeline._visual_decoder._W.copy(),
            "visual_decoder_b": pipeline._visual_decoder._b.copy(),
            "audio_decoder_W": pipeline._audio_decoder._W.copy(),
            "audio_decoder_b": pipeline._audio_decoder._b.copy(),
        }
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        np.savez(args.save, **save_data)
        print(f"Weights saved to {args.save}")

    # Final evaluation
    print("\n=== Final evaluation ===")
    results = pipeline.evaluate(n_samples=5)
    for mod, res in results.items():
        print(f"  {mod}: avg_reconstruction_loss={res['avg_reconstruction_loss']:.6f}")


if __name__ == "__main__":
    main()
