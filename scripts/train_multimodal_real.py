"""
Full multimodal training pipeline with real CIFAR-10 data.

Runs Phase 1+2 (contrastive + reconstruction on real CIFAR-10/ESC-50 data),
then Phase 3a-3d (texture, wavetable, sequence, primitives).
Saves all weights to data/multimodal/weights/.

Usage:
    python scripts/train_multimodal_real.py
    python scripts/train_multimodal_real.py --texture-steps 500 --samples 1000
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

from ai.multimodal.training_pipeline import FullTrainingPipeline
from ai.multimodal.data_loader import RealDataProvider


def main():
    parser = argparse.ArgumentParser(description="Full multimodal training with real data")
    parser.add_argument("--contrastive-epochs", type=int, default=10)
    parser.add_argument("--pairs", type=int, default=50)
    parser.add_argument("--recon-epochs", type=int, default=10)
    parser.add_argument("--recon-samples", type=int, default=50)
    parser.add_argument("--texture-steps", type=int, default=500,
                        help="Gradient steps for texture training")
    parser.add_argument("--wavetable-steps", type=int, default=200)
    parser.add_argument("--texture-lr", type=float, default=0.001)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--max-samples", type=int, default=5000,
                        help="Max images to encode from CIFAR-10")
    args = parser.parse_args()

    print("=" * 60)
    print("Full Multimodal Training Pipeline (Real Data)")
    print("=" * 60)

    # 1. Load real data
    print("\n[0] Loading real data...")
    dp = RealDataProvider()
    counts = dp.encode_all(max_images=args.max_samples)
    print(f"  Encoded: {counts}")
    print(f"  has_data: {dp.has_data()}")

    # 2. Create pipeline
    print("\n[1] Creating training pipeline...")
    pipeline = FullTrainingPipeline()

    # 3. Phase 1 + 2 on real data
    print("\n=== Phase 1 + 2: Real contrastive + reconstruction ===")
    results = pipeline.run_on_real(
        dp,
        contrastive_epochs=args.contrastive_epochs,
        recon_epochs=args.recon_epochs,
        pairs_per_modality=args.pairs,
        recon_samples_per_modality=args.recon_samples,
        lr=args.lr,
    )
    print(f"  Data source: {results.get('data_source', 'synthetic')}")
    print(f"  Contrastive final loss: {results['contrastive']['final_loss']:.6f}")
    for mod, res in results.get("reconstruction", {}).items():
        print(f"  {mod} reconstruction final loss: {res['final_loss']:.6f}")

    # 4. Phase 3a: Texture training
    print("\n=== Phase 3a: Texture branch training ===")
    tex_result = pipeline.train_texture(batch_size=4, steps=args.texture_steps, lr=args.texture_lr)
    print(f"  Texture final loss: {tex_result['final_loss']:.6f}")

    # 5. Phase 3b: Wavetable training
    print("\n=== Phase 3b: Wavetable branch training ===")
    wt_result = pipeline.train_wavetable(batch_size=4, steps=args.wavetable_steps, lr=args.texture_lr)
    print(f"  Wavetable final loss: {wt_result['final_loss']:.6f}")

    # 6. Save all weights to joint p29_trained.npz (both visual + audio)
    save_dir = os.path.join(os.path.dirname(__file__), "..", "data", "multimodal", "weights")
    os.makedirs(save_dir, exist_ok=True)
    joint_path = os.path.join(save_dir, "p29_trained.npz")

    # Collect visual decoder weights
    vd_weights = {
        "visual_decoder_W": pipeline._visual_decoder._W,
        "visual_decoder_b": pipeline._visual_decoder._b,
        "texture_W_hidden": pipeline._visual_decoder._W_hidden,
        "texture_b_hidden": pipeline._visual_decoder._b_hidden,
        "texture_W_featmap": pipeline._visual_decoder._W_featmap,
        "texture_b_featmap": pipeline._visual_decoder._b_featmap,
        "texture_tex_kernels": pipeline._visual_decoder._tex_kernels,
    }
    # Collect audio decoder weights
    ad = pipeline._audio_decoder
    ad_weights = {
        "audio_decoder_W": ad._W,
        "audio_decoder_b": ad._b,
        "audio_W_hidden": ad._W_hidden,
        "audio_b_hidden": ad._b_hidden,
        "audio_W_wavetable": ad._W_wavetable,
        "audio_b_wavetable": ad._b_wavetable,
        "audio_W_noise": ad._W_noise,
        "audio_b_noise": ad._b_noise,
    }
    # Merge and save
    import numpy as np
    all_weights = {**vd_weights, **ad_weights}
    np.savez(joint_path, **all_weights)
    print(f"\n✅ Saved joint weights ({len(all_weights)} arrays) to {joint_path}")

    # 7. Verify both decoders load from joint file
    from ai.multimodal.visual_decoder import VisualDecoder, load_default_visual_decoder_weights
    vd = VisualDecoder()
    load_default_visual_decoder_weights(vd)
    w = vd.get_projection()
    print(f"  VisualDecoder load verification: W sum={w[0].sum():.2f}")

    from ai.multimodal.audio_decoder import AudioWaveformDecoder, load_default_audio_decoder_weights
    ad_check = AudioWaveformDecoder()
    ok = load_default_audio_decoder_weights(ad_check)
    print(f"  AudioDecoder load verification: {'OK' if ok else 'FAILED'}")

    # Quick decode test
    rng = np.random.default_rng(42)
    z = rng.normal(0, 1, 64).astype(np.float32)
    img = vd.decode(z)
    print(f"  Visual decode: shape={img.shape}, mean={img.mean():.2f}")
    # AudioWaveformDecoder uses decode(), not generate()
    waveform = ad_check.decode(z)
    print(f"  Audio decode: shape={waveform.shape}, mean={waveform.mean():.4f}")

    print("\nDone!")


if __name__ == "__main__":
    main()
