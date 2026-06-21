# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import time
from typing import Dict, List, Optional, Tuple

import numpy as np

from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.reconstruction_cycle import ReconstructionCycle
from ai.multimodal.visual_encoder import VisualEncoder
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.quality_metrics import snr

logger = logging.getLogger(__name__)


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
        pos_pairs: List = []
        neg_pairs: List = []
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
        """Train reconstruction cycle over all modalities.

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


class FullTrainingPipeline:
    """End-to-end training pipeline: contrastive pre-training + reconstruction fine-tuning.

    Pure numpy — no external data dependencies. Uses synthetic data to train
    the projection matrices and decoder weights.
    """

    def __init__(self, latent_space: Optional[SharedLatentSpace] = None,
                 visual_encoder: Optional[VisualEncoder] = None,
                 audio_encoder: Optional[AudioSpectralEncoder] = None,
                 visual_decoder=None, audio_decoder=None):
        self._ls = latent_space or SharedLatentSpace(latent_dim=64)
        self._visual_encoder = visual_encoder or VisualEncoder()
        self._audio_encoder = audio_encoder or AudioSpectralEncoder()
        from ai.multimodal.visual_decoder import VisualDecoder
        from ai.multimodal.audio_decoder import AudioWaveformDecoder
        self._visual_decoder = visual_decoder or VisualDecoder()
        self._audio_decoder = audio_decoder or AudioWaveformDecoder()
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

    def evaluate(self, n_samples: int = 5) -> Dict:
        """Evaluate current model quality on synthetic data.

        Returns dict of quality metrics per modality.
        """
        result: Dict = {}
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
