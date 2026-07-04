"""MultimodalBridge — connects multimodal encoders/decoders to ED3N and the service layer.

P20: Provides a unified interface for:
  - Encoding modalities into feature vectors (for ED3N dictionary keys)
  - Decoding latent vectors into modality outputs (for system use)
  - Cross-modal similarity queries
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
from ai.multimodal.audio_decoder import AudioWaveformDecoder
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.text_encoder import TextEncoder
from ai.multimodal.visual_decoder import VisualDecoder
from ai.multimodal.visual_encoder import VisualEncoder
from PIL import Image

logger = logging.getLogger(__name__)


class MultimodalBridge:
    """Unified bridge between multimodal system and ED3N/service layer.

    Synchronous interface suitable for ED3N integration.
    """

    VISION_DIM: int = 256
    AUDIO_DIM: int = 128
    TEXT_DIM: int = 512
    LATENT_DIM: int = 64

    def __init__(self):
        self._visual_encoder = VisualEncoder(feature_dim=self.VISION_DIM)
        self._audio_encoder = AudioSpectralEncoder(feature_dim=self.AUDIO_DIM)
        self._text_encoder = TextEncoder(feature_dim=self.TEXT_DIM)
        from ai.multimodal.audio_decoder import (
            AudioWaveformDecoder,
            load_default_audio_decoder_weights,
        )
        from ai.multimodal.visual_decoder import VisualDecoder, load_default_visual_decoder_weights
        self._visual_decoder = VisualDecoder()
        load_default_visual_decoder_weights(self._visual_decoder)
        self._audio_decoder = AudioWaveformDecoder()
        load_default_audio_decoder_weights(self._audio_decoder)
        self._latent_space = SharedLatentSpace(latent_dim=self.LATENT_DIM)
        self._latent_space.register_modality("vision", self.VISION_DIM)
        self._latent_space.register_modality("audio", self.AUDIO_DIM)
        self._latent_space.register_modality("text", self.TEXT_DIM)

    # --- Encoding (modality → latent) ---

    def encode_image_bytes(self, image_data: bytes) -> Optional[List[float]]:
        """Encode raw image bytes to 256-dim feature vector."""
        vec = self._visual_encoder.encode(image_data)
        if np.all(vec == 0):
            return None
        return vec.tolist()

    def encode_audio_bytes(self, audio_data: bytes) -> Optional[List[float]]:
        """Encode raw audio bytes to 128-dim feature vector."""
        vec = self._audio_encoder.encode(audio_data)
        if np.all(vec == 0):
            return None
        return vec.tolist()

    def encode_image_to_latent(self, image_data: bytes) -> Optional[List[float]]:
        """Encode image all the way to 64-dim latent vector."""
        vec = self._visual_encoder.encode(image_data)
        if np.all(vec == 0):
            return None
        latent = self._latent_space.project("vision", vec)
        return latent.tolist()

    def encode_audio_to_latent(self, audio_data: bytes) -> Optional[List[float]]:
        """Encode audio all the way to 64-dim latent vector."""
        vec = self._audio_encoder.encode(audio_data)
        if np.all(vec == 0):
            return None
        latent = self._latent_space.project("audio", vec)
        return latent.tolist()

    def encode_text_to_latent(self, text: str) -> Optional[List[float]]:
        """Encode text all the way to 64-dim latent vector.

        Uses CLIP text encoder → 512-dim → SharedLatentSpace → 64-dim.
        This completes the tri-modal architecture:
          Text → TextEncoder(512) → SharedLatentSpace → 64-dim
          Image → VisualEncoder(256) → SharedLatentSpace → 64-dim
          Audio → AudioSpectralEncoder(128) → SharedLatentSpace → 64-dim
        """
        vec = self._text_encoder.encode(text)
        if np.all(vec == 0):
            return None
        latent = self._latent_space.project("text", vec)
        return latent.tolist()

    def encode_text_to_features(self, text: str) -> Optional[List[float]]:
        """Encode text to 512-dim CLIP feature vector (before projection)."""
        vec = self._text_encoder.encode(text)
        if np.all(vec == 0):
            return None
        return vec.tolist()

    # --- Decoding (latent → modality) ---

    def decode_latent_to_image(self, latent: List[float]) -> Optional[Image.Image]:
        """Decode a 64-dim latent vector into a PIL Image."""
        arr = np.array(latent, dtype=np.float32)
        if len(arr) != self.LATENT_DIM:
            return None
        return self._visual_decoder.decode_to_pil(arr)

    def decode_latent_to_waveform(self, latent: List[float]) -> Optional[List[float]]:
        """Decode a 64-dim latent vector into PCM waveform samples."""
        arr = np.array(latent, dtype=np.float32)
        if len(arr) != self.LATENT_DIM:
            return None
        wav = self._audio_decoder.decode(arr)
        return wav.tolist()

    # --- Cross-modal ---

    def similarity(self, feat_a: List[float], feat_b: List[float]) -> float:
        """Cosine similarity between two feature vectors in latent space, mapped to [0,1]."""
        a = np.array(feat_a, dtype=np.float32)
        b = np.array(feat_b, dtype=np.float32)
        a_norm = a / max(np.linalg.norm(a), 1e-8)
        b_norm = b / max(np.linalg.norm(b), 1e-8)
        dot = float(np.dot(a_norm, b_norm))
        return max(0.0, min(1.0, (dot + 1.0) / 2.0))

    def cross_similarity(self, image_data: bytes, audio_data: bytes) -> float:
        """Encode both modalities and compute cross-modal similarity."""
        img_vec = self._visual_encoder.encode(image_data)
        aud_vec = self._audio_encoder.encode(audio_data)
        if np.all(img_vec == 0) or np.all(aud_vec == 0):
            return 0.0
        z_img = self._latent_space.project("vision", img_vec)
        z_aud = self._latent_space.project("audio", aud_vec)
        return self.similarity(z_img.tolist(), z_aud.tolist())

    # --- ED3N-compatible entry generation ---

    def to_dictionary_entry(self, image_data: bytes,
                            label: str = "") -> Dict[str, Any]:
        """Convert image bytes to an ED3N-compatible dictionary entry.

        Returns dict with 'key' (latent vector hash), 'value' (label),
        and 'vector' (64-dim latent).
        """
        latent = self.encode_image_to_latent(image_data)
        if latent is None:
            return {"key": "", "value": label, "vector": []}
        key = f"mm_vision_{hash(tuple(latent[:8])) & 0xFFFFFFFF:08x}"
        return {"key": key, "value": label, "vector": latent}

    def latent_to_entry(self, latent: List[float],
                        label: str = "") -> Dict[str, Any]:
        """Convert a latent vector to an ED3N-compatible entry."""
        if not latent:
            return {"key": "", "value": label, "vector": []}
        key = f"mm_latent_{hash(tuple(latent[:8])) & 0xFFFFFFFF:08x}"
        return {"key": key, "value": label, "vector": latent}

    # --- Weight persistence (P29) ---

    def load_weights(self, weights_path: str) -> bool:
        """Load trained weights from a .npz file.

        See SimilarityService.load_weights for the expected format.
        """
        try:
            import numpy as np
            data = np.load(weights_path, allow_pickle=False)
        except Exception as e:
            logger.warning("Bridge load_weights failed: %s", e)
            return False

        try:
            if "vision_W" in data:
                self._latent_space._projections["vision"]["W"][:] = data["vision_W"]
                self._latent_space._projections["vision"]["b"][:] = data["vision_b"]
            if "audio_W" in data:
                self._latent_space._projections["audio"]["W"][:] = data["audio_W"]
                self._latent_space._projections["audio"]["b"][:] = data["audio_b"]
            if "visual_decoder_W" in data:
                self._visual_decoder._W[:] = data["visual_decoder_W"]
                self._visual_decoder._b[:] = data["visual_decoder_b"]
            if "audio_decoder_W" in data:
                self._audio_decoder._W[:] = data["audio_decoder_W"]
                self._audio_decoder._b[:] = data["audio_decoder_b"]
            logger.info("Bridge: trained weights loaded from %s", weights_path)
            return True
        except Exception as e:
            logger.warning("Bridge: failed to apply weights: %s", e)
            return False