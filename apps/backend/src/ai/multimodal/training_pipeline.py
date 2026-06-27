# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.quality_metrics import snr
from ai.multimodal.reconstruction_cycle import ReconstructionCycle
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.visual_encoder import VisualEncoder

logger = logging.getLogger(__name__)


# Type alias for contrastive pair: (mod_a, feat_a, mod_b, feat_b)
ContrastivePair = Tuple[str, np.ndarray, str, np.ndarray]


# Default weight save path
DEFAULT_WEIGHTS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "data" / "multimodal" / "weights"
DEFAULT_WEIGHTS_PATH = str(DEFAULT_WEIGHTS_DIR / "p29_trained.npz")


class ContrastiveBatchTrainer:
    """Batch contrastive trainer for SharedLatentSpace.

    Generates training pairs from synthetic modality data and trains
    the latent space projection matrices via contrastive loss.
    """

    def __init__(self, latent_space: SharedLatentSpace,
                 visual_encoder: Optional[VisualEncoder] = None,
                 audio_encoder: Optional[AudioSpectralEncoder] = None):
        self._ls = latent_space
        self._visual_encoder = visual_encoder or VisualEncoder()
        self._audio_encoder = audio_encoder or AudioSpectralEncoder()

    def generate_pairs(self, n_pairs: int,
                       img_dim: int = 256, aud_dim: int = 128) -> Tuple[List, List]:
        """Generate synthetic positive/negative training pairs.

        Returns (pos_pairs, neg_pairs) where each element is
        (mod_a, feat_a, mod_b, feat_b).
        """
        pos_pairs: List[ContrastivePair] = []
        neg_pairs: List[ContrastivePair] = []
        rng = np.random.RandomState(42)
        for _ in range(n_pairs):
            seed = rng.randn(img_dim).astype(np.float32)
            feat_img = seed + rng.randn(img_dim).astype(np.float32) * 0.1
            feat_aud = seed[:aud_dim] + rng.randn(aud_dim).astype(np.float32) * 0.1
            pos_pairs.append(("vision", feat_img, "audio", feat_aud))
            feat_img2 = rng.randn(img_dim).astype(np.float32)
            feat_aud2 = rng.randn(aud_dim).astype(np.float32)
            neg_pairs.append(("vision", feat_img2, "audio", feat_aud2))
        return pos_pairs, neg_pairs

    def train_epoch(self, pos_pairs: List, neg_pairs: List,
                    lr: float = 0.01, margin: float = 0.5) -> float:
        """Train one epoch over the given pairs.

        Returns average contrastive loss.
        """
        return self._ls._train_epoch(pos_pairs, neg_pairs, lr, margin)

    def train(self, n_epochs: int = 10, n_pairs_per_epoch: int = 20,
              lr: float = 0.01, margin: float = 0.5) -> Dict:
        """Full training run. Returns dict with final_loss and loss_history."""
        pos_pairs, neg_pairs = self.generate_pairs(n_pairs_per_epoch)
        return self._ls.train(pos_pairs, neg_pairs, epochs=n_epochs,
                              lr=lr, margin=margin)

    def train_on_real_pairs(self, pos_pairs: List[ContrastivePair],
                            neg_pairs: List[ContrastivePair],
                            epochs: int = 5, lr: float = 0.01,
                            margin: float = 0.5) -> Dict:
        """Train on real data pairs from data loaders.

        Args:
            pos_pairs: List of (mod, feat, mod, feat) — same-class pairs
            neg_pairs: List of (mod, feat, mod, feat) — different-class pairs
            epochs: Number of training epochs
            lr: Learning rate

        Returns:
            dict with 'final_loss' and 'history'
        """
        return self._ls.train(pos_pairs, neg_pairs, epochs=epochs,
                              lr=lr, margin=margin)


class ReconstructionTrainer:
    """Trains decoders via feature-level reconstruction on synthetic data."""

    def __init__(self, latent_space: SharedLatentSpace,
                 reconstruction_cycle: ReconstructionCycle):
        self._ls = latent_space
        self._rc = reconstruction_cycle

    def generate_features(self, n_samples: int) -> Dict[str, List[np.ndarray]]:
        """Generate synthetic training features for each registered modality."""
        rng = np.random.RandomState(123)
        result: Dict[str, List[np.ndarray]] = {}
        for mod in self._ls._projections:
            # Use correct dimension per modality
            if mod == "vision":
                feat_dim = 256
            elif mod == "audio":
                feat_dim = 128
            else:
                feat_dim = 64
            samples = [rng.randn(feat_dim).astype(np.float32) for _ in range(n_samples)]
            result[mod] = samples
        return result

    def train(self, n_epochs: int = 10, n_samples: int = 10, lr: float = 0.005) -> Dict:
        """Train reconstruction cycle over all modalities using synthetic features.

        Returns dict per modality with final_loss and history.
        """
        results: Dict[str, Dict] = {}
        for mod in self._ls._projections:
            features = self.generate_features(n_samples)
            mod_features = features.get(mod, [])
            if not mod_features:
                continue
            mod_results = self._rc.train(mod, mod_features, epochs=n_epochs, lr=lr)
            results[mod] = {
                "final_loss": mod_results["final_loss"],
                "history": mod_results["history"][-5:] if mod_results.get("history") else [],
            }
        return results

    def train_on_real_features(self,
                               real_features: Dict[str, List[np.ndarray]],
                               epochs: int = 5, lr: float = 0.005) -> Dict:
        """Train reconstruction on real encoded features.

        Args:
            real_features: {modality: [feature_vectors]}
            epochs: Training epochs
            lr: Learning rate

        Returns:
            dict per modality with 'final_loss' and 'history'
        """
        results: Dict[str, Dict] = {}
        for mod, features in real_features.items():
            if not features:
                continue
            mod_results = self._rc.train(mod, features, epochs=epochs, lr=lr)
            results[mod] = {
                "final_loss": mod_results["final_loss"],
                "history": mod_results["history"][-5:] if mod_results.get("history") else [],
            }
        return results


class FullTrainingPipeline:
    """End-to-end training pipeline: contrastive pre-training + reconstruction fine-tuning.

    P27: Pure numpy — no external data dependencies. Uses synthetic data to train
    the projection matrices and decoder weights.

    P28: Supports real data via RealDataProvider. When real data is available,
    uses ESC-50 audio + CIFAR-10 images instead of random noise.
    """

    def __init__(self, latent_space: Optional[SharedLatentSpace] = None,
                 visual_encoder: Optional[VisualEncoder] = None,
                 audio_encoder: Optional[AudioSpectralEncoder] = None,
                 visual_decoder=None, audio_decoder=None):
        self._ls = latent_space or SharedLatentSpace(latent_dim=64)
        self._visual_encoder = visual_encoder or VisualEncoder()
        self._audio_encoder = audio_encoder or AudioSpectralEncoder()
        from ai.multimodal.audio_decoder import (
            AudioWaveformDecoder,
            load_default_audio_decoder_weights,
        )
        from ai.multimodal.visual_decoder import VisualDecoder, load_default_visual_decoder_weights
        self._visual_decoder = visual_decoder or VisualDecoder()
        load_default_visual_decoder_weights(self._visual_decoder)
        self._audio_decoder = audio_decoder or AudioWaveformDecoder()
        load_default_audio_decoder_weights(self._audio_decoder)
        self._ls.register_modality("vision", 256)
        self._ls.register_modality("audio", 128)
        self._reconstruction = ReconstructionCycle(
            self._ls, self._visual_decoder, self._audio_decoder
        )
        self._contrastive = ContrastiveBatchTrainer(
            self._ls, self._visual_encoder, self._audio_encoder
        )

    def run(self, contrastive_epochs: int = 10, contrastive_pairs: int = 20,
            recon_epochs: int = 10, recon_samples: int = 10,
            lr: float = 0.01) -> Dict:
        """Run full training pipeline.

        Phase 1: Contrastive pre-training of SharedLatentSpace.
        Phase 2: Reconstruction fine-tuning of decoders.
        """
        logger.info("=== Phase 1: Contrastive training ===")
        pos_pairs, neg_pairs = self._contrastive.generate_pairs(contrastive_pairs)
        contrastive_result = self._ls.train(
            pos_pairs, neg_pairs, epochs=contrastive_epochs, lr=lr,
        )
        logger.info("Contrastive final loss: %.6f", contrastive_result["final_loss"])

        logger.info("=== Phase 2: Reconstruction training ===")
        recon_result = ReconstructionTrainer(
            self._ls, self._reconstruction
        ).train(n_epochs=recon_epochs, n_samples=recon_samples, lr=lr * 0.5)
        for mod, res in recon_result.items():
            logger.info("  %s reconstruction final loss: %.6f", mod, res["final_loss"])

        return {
            "contrastive": contrastive_result,
            "reconstruction": recon_result,
        }

    def run_on_real(self,
                    data_provider: 'RealDataProvider',
                    contrastive_epochs: int = 5,
                    recon_epochs: int = 5,
                    pairs_per_modality: int = 30,
                    recon_samples_per_modality: int = 30,
                    lr: float = 0.01) -> Dict:
        """Run full training pipeline on real data from RealDataProvider.

        Phase 1: Contrastive pre-training with real class-labeled pairs.
        Phase 2: Reconstruction fine-tuning with real encoded features.

        Falls back to synthetic data if real data is unavailable.
        """
        from ai.multimodal.data_loader import RealDataProvider as RDP

        if not isinstance(data_provider, RDP) or not data_provider.has_data():
            logger.warning("Real data unavailable, falling back to synthetic")
            return self.run(
                contrastive_epochs=contrastive_epochs,
                contrastive_pairs=pairs_per_modality,
                recon_epochs=recon_epochs,
                recon_samples=recon_samples_per_modality,
                lr=lr,
            )

        logger.info("=== Phase 1: Real contrastive training ===")
        pos_pairs, neg_pairs = data_provider.contrastive_pairs(
            n_per_modality=pairs_per_modality, same_prob=0.5
        )
        logger.info("  Generated %d pos + %d neg pairs from real data",
                    len(pos_pairs), len(neg_pairs))
        contrastive_result = self._ls.train(
            pos_pairs, neg_pairs, epochs=contrastive_epochs, lr=lr,
        )
        logger.info("  Contrastive final loss: %.6f", contrastive_result["final_loss"])

        logger.info("=== Phase 2: Real reconstruction training ===")
        recon_features = data_provider.reconstruction_samples(
            n_per_modality=recon_samples_per_modality
        )
        recon_result = {}
        trainer = ReconstructionTrainer(self._ls, self._reconstruction)
        for mod, features in recon_features.items():
            if not features:
                continue
            mod_result = trainer.train_on_real_features(
                {mod: features}, epochs=recon_epochs, lr=lr * 0.5
            )
            if mod in mod_result:
                recon_result[mod] = mod_result[mod]
                logger.info("  %s reconstruction final loss: %.6f",
                            mod, mod_result[mod]["final_loss"])

        return {
            "contrastive": contrastive_result,
            "reconstruction": recon_result,
            "data_source": "real",
        }

    def save_weights(self, path: Optional[str] = None) -> str:
        """Save trained weights to a .npz file.

        Args:
            path: Output path (default: data/multimodal/weights/p29_trained.npz)

        Returns:
            Path where weights were saved, or empty string on failure.
        """
        save_path = path or DEFAULT_WEIGHTS_PATH
        try:
            vis = self._ls._projections.get("vision", {})
            aud = self._ls._projections.get("audio", {})
            save_data = {
                "vision_W": vis.get("W", np.zeros(1)).copy(),
                "vision_b": vis.get("b", np.zeros(1)).copy(),
                "audio_W": aud.get("W", np.zeros(1)).copy(),
                "audio_b": aud.get("b", np.zeros(1)).copy(),
                "visual_decoder_W": self._visual_decoder._W.copy(),
                "visual_decoder_b": self._visual_decoder._b.copy(),
                "audio_decoder_W": self._audio_decoder._W.copy(),
                "audio_decoder_b": self._audio_decoder._b.copy(),
            }
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            np.savez(save_path, **save_data)
            logger.info("Trained weights saved to %s", save_path)
            return save_path
        except Exception as e:
            logger.warning("Failed to save weights: %s", e)
            return ""

    def load_weights(self, path: str) -> bool:
        """Load trained weights from a .npz file.

        Args:
            path: Path to .npz weights file

        Returns:
            True on success
        """
        try:
            data = np.load(path, allow_pickle=False)
        except Exception as e:
            logger.warning("Failed to load weights from %s: %s", path, e)
            return False

        try:
            if "vision_W" in data:
                self._ls._projections["vision"]["W"][:] = data["vision_W"]
                self._ls._projections["vision"]["b"][:] = data["vision_b"]
            if "audio_W" in data:
                self._ls._projections["audio"]["W"][:] = data["audio_W"]
                self._ls._projections["audio"]["b"][:] = data["audio_b"]
            if "visual_decoder_W" in data:
                self._visual_decoder._W[:] = data["visual_decoder_W"]
                self._visual_decoder._b[:] = data["visual_decoder_b"]
            if "audio_decoder_W" in data:
                self._audio_decoder._W[:] = data["audio_decoder_W"]
                self._audio_decoder._b[:] = data["audio_decoder_b"]
            logger.info("Weights loaded from %s", path)
            return True
        except Exception as e:
            logger.warning("Failed to apply weights: %s", e)
            return False

    def evaluate(self, n_samples: int = 5,
                 real_features: Optional[Dict[str, List[np.ndarray]]] = None) -> Dict:
        """Evaluate current model quality on synthetic or real data.

        Args:
            n_samples: Number of synthetic samples (ignored if real_features given)
            real_features: Optional dict of real encoded features per modality

        Returns dict of quality metrics per modality.
        """
        result: Dict = {}

        if real_features:
            for mod, features in real_features.items():
                if not features:
                    continue
                losses = []
                for f in features[:n_samples]:
                    loss = self._reconstruction.train_step(mod, f, lr=0.0)
                    losses.append(loss)
                result[mod] = {
                    "avg_reconstruction_loss": float(np.mean(losses)),
                }
        else:
            rng = np.random.RandomState(999)
            for mod in ["vision", "audio"]:
                feat_dim = 256 if mod == "vision" else 128
                losses = []
                for _ in range(n_samples):
                    f = rng.randn(feat_dim).astype(np.float32)
                    loss = self._reconstruction.train_step(mod, f, lr=0.0)
                    losses.append(loss)
                result[mod] = {
                    "avg_reconstruction_loss": float(np.mean(losses)),
                }
        return result
