"""Reconstruction cycle + cross-modal synthesis — autoencoder train loop and cross-modal generation.

P19: Closes the encoder→latent→decoder→encoder reconstruction loop with
feature-level MSE training, and enables cross-modal latent blending.
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np

from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.visual_decoder import VisualDecoder
from ai.multimodal.audio_decoder import AudioWaveformDecoder

logger = logging.getLogger(__name__)


class ReconstructionCycle:
    """Trains encoder↔decoder projection weights via feature-level autoencoding.

    Pipeline:
      f → W_e @ f + b_e = z → W_d @ z + b_d = f_hat
      loss = 0.5 * ||f - f_hat||²

    Gradients are computed analytically (pure numpy). Only the projection
    matrices W_e (SharedLatentSpace) and W_d (Decoder) are updated.
    """

    def __init__(self, latent_space: SharedLatentSpace,
                 visual_decoder: Optional[VisualDecoder] = None,
                 audio_decoder: Optional[AudioWaveformDecoder] = None):
        self._ls = latent_space
        self._visual_decoder = visual_decoder
        self._audio_decoder = audio_decoder

    def train_step(self, modality: str, features: np.ndarray,
                   lr: float = 0.01) -> float:
        """Single gradient descent step for feature-level reconstruction.

        Args:
            modality: Modality name (registered in latent_space)
            features: Input feature vector from the encoder
            lr: Learning rate

        Returns:
            Loss value before the update
        """
        proj = self._ls._projections.get(modality)
        if proj is None:
            return 0.0

        decoder = self._get_decoder(modality)
        if decoder is None:
            return 0.0

        f = features.astype(np.float32)
        W_e = proj["W"]
        b_e = proj["b"]
        W_d = decoder._W
        b_d = decoder._b

        z = W_e @ f + b_e
        f_hat = W_d @ z + b_d
        loss = 0.5 * float(np.sum((f_hat - f) ** 2))

        grad_f_hat = f_hat - f
        grad_W_d = np.outer(grad_f_hat, z)
        grad_b_d = grad_f_hat.copy()
        grad_z = W_d.T @ grad_f_hat
        grad_W_e = np.outer(grad_z, f)
        grad_b_e = grad_z.copy()

        # Gradient clipping (norm-based)
        max_norm = 10.0
        for g in [grad_W_d, grad_W_e]:
            norm = np.sqrt(np.sum(g ** 2))
            if norm > max_norm:
                g *= max_norm / norm
        for g in [grad_b_d, grad_b_e]:
            norm = np.sqrt(np.sum(g ** 2))
            if norm > max_norm:
                g *= max_norm / norm

        W_d -= lr * grad_W_d
        b_d -= lr * grad_b_d
        W_e -= lr * grad_W_e
        b_e -= lr * grad_b_e

        return loss

    def train(self, modality: str, features_list: List[np.ndarray],
              epochs: int = 20, lr: float = 0.005) -> Dict:
        """Train over multiple samples for multiple epochs.

        Args:
            modality: Modality name
            features_list: List of feature vectors
            epochs: Number of passes over the data
            lr: Learning rate

        Returns:
            Dict with 'final_loss' and 'history'
        """
        history = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for f in features_list:
                epoch_loss += self.train_step(modality, f, lr)
            avg_loss = epoch_loss / max(len(features_list), 1)
            history.append(avg_loss)
        return {"final_loss": history[-1] if history else 0.0, "history": history}

    def reconstruct(self, modality: str, features: np.ndarray) -> np.ndarray:
        """Full forward pass: encode to latent → decode back to features.

        Args:
            modality: Modality name
            features: Input feature vector

        Returns:
            Reconstructed feature vector
        """
        proj = self._ls._projections.get(modality)
        decoder = self._get_decoder(modality)
        if proj is None or decoder is None:
            return np.zeros_like(features)

        z = self._ls.project(modality, features)
        f_hat = decoder._W @ z + decoder._b
        return f_hat

    def reconstruction_error(self, modality: str, features: np.ndarray) -> float:
        """Compute MSE between original and reconstructed features."""
        f_hat = self.reconstruct(modality, features)
        return float(np.mean((features - f_hat) ** 2))

    def _get_decoder(self, modality: str):
        if modality == "vision" and self._visual_decoder:
            return self._visual_decoder
        if modality == "audio" and self._audio_decoder:
            return self._audio_decoder
        return None


class CrossModalSynthesizer:
    """Cross-modal latent blending and generation.

    Takes latents from different modalities, blends them, and decodes
    into any target modality.
    """

    def __init__(self, latent_space: SharedLatentSpace,
                 visual_decoder: Optional[VisualDecoder] = None,
                 audio_decoder: Optional[AudioWaveformDecoder] = None):
        self._ls = latent_space
        self._visual_decoder = visual_decoder
        self._audio_decoder = audio_decoder

    def blend_latents(self, modalities: List[Tuple[str, np.ndarray]],
                      weights: Optional[List[float]] = None) -> np.ndarray:
        """Blend multiple modality latents into a single latent vector.

        Args:
            modalities: List of (modality_name, feature_vector) pairs
            weights: Optional blend weights (default: equal)

        Returns:
            Blended 64-dim latent vector
        """
        n = len(modalities)
        if n == 0:
            return np.zeros(self._ls._latent_dim, dtype=np.float32)
        if weights is None:
            weights = [1.0 / n] * n
        w_sum = sum(weights)
        weights = [w / w_sum for w in weights]

        blended = np.zeros(self._ls._latent_dim, dtype=np.float32)
        for (mod, feat), w in zip(modalities, weights):
            z = self._ls.project(mod, feat)
            blended += w * z
        return blended

    def generate_image(self, latent: np.ndarray) -> np.ndarray:
        """Generate an image from a latent vector (or blended latent)."""
        if self._visual_decoder is None:
            return np.zeros((128, 128, 3), dtype=np.uint8)
        return self._visual_decoder.decode(latent)

    def generate_audio(self, latent: np.ndarray) -> np.ndarray:
        """Generate audio waveform from a latent vector (or blended latent)."""
        if self._audio_decoder is None:
            return np.array([], dtype=np.float32)
        return self._audio_decoder.decode(latent)

    def cross_generate(self, source_modality: str, source_features: np.ndarray,
                       target_modality: str) -> np.ndarray:
        """Encode source modality and decode into target modality.

        E.g., encode an image → decode as audio (vision→audio).
        """
        z = self._ls.project(source_modality, source_features)
        if target_modality == "vision" or target_modality == "image":
            return self.generate_image(z)
        elif target_modality == "audio" or target_modality == "waveform":
            return self.generate_audio(z)
        return np.array([])