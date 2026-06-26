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
    parser.add_argument("--real", action="store_true",
                        help="Use real data (ESC-50 audio + CIFAR-10 images)")
    parser.add_argument("--encode", action="store_true",
                        help="Encode real datasets before training")
    parser.add_argument("--real-pairs", type=int, default=30,
                        help="Number of contrastive pairs per modality (default: 30)")
    parser.add_argument("--real-samples", type=int, default=30,
                        help="Number of reconstruction samples per modality (default: 30)")
    parser.add_argument("--auto-save", action="store_true",
                        help="Save trained weights automatically after training")
    parser.add_argument("--auto-load", type=str, default="", nargs="?", const="auto",
                        help="Load trained weights before training (path or 'auto' for default)")
    parser.add_argument("--eval-before", action="store_true",
                        help="Evaluate quality before training (for before/after comparison)")
    parser.add_argument("--max-images", type=int, default=0,
                        help="Max images to encode per dataset (0 = all)")
    args = parser.parse_args()

    print("=" * 60)
    print("  MULTIMODAL TRAINING PIPELINE (P27)")
    print("=" * 60)

    pipeline = FullTrainingPipeline()

    # Auto-load weights before training (P29: end-to-end pipeline)
    load_path = args.load
    if args.auto_load and args.auto_load != "":
        load_path = args.auto_load if args.auto_load != "auto" else None
    if load_path:
        from ai.multimodal.training_pipeline import DEFAULT_WEIGHTS_PATH
        wpath = load_path if load_path != "auto" else DEFAULT_WEIGHTS_PATH
        print(f"\nLoading weights from {wpath}...")
        if pipeline.load_weights(wpath):
            print("  Loaded successfully")
        else:
            print("  No weights found or load failed (will train from scratch)")

    # Real data mode: load and optionally encode real datasets
    data_provider = None
    if args.real or args.encode:
        try:
            from ai.multimodal.data_loader import RealDataProvider
            data_provider = RealDataProvider()
            if args.encode:
                print("\nEncoding real datasets...")
                counts = data_provider.encode_all(max_images=args.max_images)
                for name, cnt in counts.items():
                    print(f"  {name}: {cnt} samples encoded")
            elif data_provider.has_data() or data_provider.cifar10.available or data_provider.esc50.available:
                # Check if already encoded
                if len(data_provider.cifar10._encoded) > 0 or len(data_provider.esc50._encoded) > 0:
                    print(f"  Using pre-encoded data (CIFAR10: {len(data_provider.cifar10._encoded)}, ESC50: {len(data_provider.esc50._encoded)})")
                else:
                    print("\nEncoding real datasets (first use)...")
                    counts = data_provider.encode_all(max_images=args.max_images)
                    for name, cnt in counts.items():
                        print(f"  {name}: {cnt} samples encoded")
        except ImportError as e:
            print(f"  Warning: data_loader not available: {e}")
        except Exception as e:
            print(f"  Warning: real data load failed: {e}")

    # Optional: evaluate BEFORE training (for before/after comparison)
    if args.eval_before:
        print("\n=== Evaluation BEFORE training ===")
        if data_provider and data_provider.has_data():
            recon_features = data_provider.reconstruction_samples(n_per_modality=5)
            before_results = pipeline.evaluate(n_samples=5, real_features=recon_features)
        else:
            before_results = pipeline.evaluate(n_samples=5)
        for mod, res in before_results.items():
            print(f"  {mod} (before): avg_loss={res['avg_reconstruction_loss']:.6f}")

    if args.evaluate_only:
        return

    t_start = time.perf_counter()

    if args.real and data_provider and data_provider.has_data():
        # Real data mode
        print("\n=== Running on REAL data ===")
        if args.recon_only:
            print("Phase: Real reconstruction only")
            recon_features = data_provider.reconstruction_samples(
                n_per_modality=args.real_samples
            )
            from ai.multimodal.training_pipeline import ReconstructionTrainer
            trainer = ReconstructionTrainer(pipeline._ls, pipeline._reconstruction)
            result = trainer.train_on_real_features(recon_features, epochs=args.recon_epochs, lr=args.lr * 0.5)
            elapsed = time.perf_counter() - t_start
            for mod, res in result.items():
                print(f"  {mod}: final_loss={res['final_loss']:.6f} ({elapsed:.1f}s)")
        elif args.contrastive_only:
            print("Phase: Real contrastive only")
            pos_pairs, neg_pairs = data_provider.contrastive_pairs(
                n_per_modality=args.real_pairs
            )
            print(f"  {len(pos_pairs)} pos + {len(neg_pairs)} neg pairs")
            result = pipeline._contrastive.train_on_real_pairs(
                pos_pairs, neg_pairs, epochs=args.contrastive_epochs, lr=args.lr
            )
            elapsed = time.perf_counter() - t_start
            print(f"  Contrastive final loss: {result['final_loss']:.6f} ({elapsed:.1f}s)")
        else:
            result = pipeline.run_on_real(
                data_provider,
                contrastive_epochs=args.contrastive_epochs,
                recon_epochs=args.recon_epochs,
                pairs_per_modality=args.real_pairs,
                recon_samples_per_modality=args.real_samples,
                lr=args.lr,
            )
            elapsed = time.perf_counter() - t_start
            print(f"\nReal training completed in {elapsed:.1f}s")
            print(f"  Data source: {result.get('data_source', 'real')}")
            print(f"  Contrastive final loss:    {result['contrastive']['final_loss']:.6f}")
            for mod, res in result.get("reconstruction", {}).items():
                print(f"  {mod} reconstruction loss:  {res['final_loss']:.6f}")
    else:
        # Synthetic data mode (existing behavior)
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
            print(f"\nSynthetic training completed in {elapsed:.1f}s")
            print(f"  Contrastive final loss:    {result['contrastive']['final_loss']:.6f}")
            for mod, res in result.get("reconstruction", {}).items():
                print(f"  {mod} reconstruction loss:  {res['final_loss']:.6f}")

    # Save weights (explicit --save or automatic --auto-save)
    if args.save:
        pipeline.save_weights(args.save)
        print(f"Weights saved to {args.save}")
    if args.auto_save:
        saved_path = pipeline.save_weights()
        if saved_path:
            print(f"Auto-saved weights to {saved_path}")

    # Final evaluation
    print("\n=== Final evaluation ===")
    if data_provider and data_provider.has_data():
        recon_features = data_provider.reconstruction_samples(n_per_modality=5)
        results = pipeline.evaluate(n_samples=5, real_features=recon_features)
    else:
        results = pipeline.evaluate(n_samples=5)
    for mod, res in results.items():
        print(f"  {mod}: avg_reconstruction_loss={res['avg_reconstruction_loss']:.6f}")


if __name__ == "__main__":
    main()
