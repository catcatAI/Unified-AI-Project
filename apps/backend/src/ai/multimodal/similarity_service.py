"""Cross-modal similarity service — orchestrates encoding/decoding and latent-space comparison."""

import logging
from typing import Dict, List, Optional

import numpy as np
from PIL import Image

from ai.multimodal.visual_encoder import VisualEncoder
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.shared_latent_space import SharedLatentSpace
from ai.multimodal.visual_decoder import VisualDecoder
from ai.multimodal.audio_decoder import AudioWaveformDecoder

logger = logging.getLogger(__name__)


class MultimodalSimilarityService:
    """Orchestrates encoding/decoding of different modalities and cross-modal comparison.

    P20: Added decode_to_image() and decode_to_audio() — true bidirectional multimodality.

    Usage:
        service = MultimodalSimilarityService()
        await service.encode_vision(image_bytes, "my_image")
        await service.encode_audio(audio_bytes, "my_audio")
        sim = service.compare("my_image", "my_audio")
        img = service.decode_to_image("my_image")
        wav = service.decode_to_audio("my_audio")
    """

    VISION_DIM: int = 256
    AUDIO_DIM: int = 128
    LATENT_DIM: int = 64

    def __init__(self):
        self._visual_encoder = VisualEncoder(feature_dim=self.VISION_DIM)
        self._audio_encoder = AudioSpectralEncoder(feature_dim=self.AUDIO_DIM)
        self._visual_decoder = VisualDecoder()
        self._audio_decoder = AudioWaveformDecoder()
        self._latent_space = SharedLatentSpace(latent_dim=self.LATENT_DIM)
        self._items: Dict[str, str] = {}

        self._latent_space.register_modality("vision", self.VISION_DIM)
        self._latent_space.register_modality("audio", self.AUDIO_DIM)

    async def encode_vision(self, image_data: bytes, item_id: str) -> Optional[List[float]]:
        """Encode image and register in latent space."""
        vec = self._visual_encoder.encode(image_data)
        if np.all(vec == 0):
            return None
        self._latent_space.project("vision", vec)
        self._items[item_id] = "vision"
        return vec.tolist()

    async def encode_audio(self, audio_data: bytes, item_id: str) -> Optional[List[float]]:
        """Encode audio and register in latent space."""
        vec = self._audio_encoder.encode(audio_data)
        if np.all(vec == 0):
            return None
        self._latent_space.project("audio", vec)
        self._items[item_id] = "audio"
        return vec.tolist()

    def decode_to_image(self, item_id: str) -> Optional[Image.Image]:
        """Decode a previously encoded item's latent back to a PIL Image.

        Returns None if item not found or not a vision modality.
        """
        modality = self._items.get(item_id)
        if modality != "vision":
            return None
        latent = self._latent_space.get_embedding("vision")
        if latent is None:
            return None
        return self._visual_decoder.decode_to_pil(latent)

    def decode_to_audio(self, item_id: str) -> Optional[List[float]]:
        """Decode a previously encoded item's latent back to waveform samples.

        Returns List[float] PCM samples or None.
        """
        modality = self._items.get(item_id)
        if modality != "audio":
            return None
        latent = self._latent_space.get_embedding("audio")
        if latent is None:
            return None
        wav = self._audio_decoder.decode(latent)
        return wav.tolist()

    def compare(self, item_a: str, item_b: str) -> float:
        """Compare two items via cross-modal similarity in latent space."""
        mod_a = self._items.get(item_a)
        mod_b = self._items.get(item_b)
        if mod_a is None or mod_b is None:
            return 0.0
        return self._latent_space.similarity(mod_a, mod_b)

    def get_embedding(self, item_id: str) -> Optional[List[float]]:
        """Get the latent embedding for a previously encoded item."""
        modality = self._items.get(item_id)
        if modality is None:
            return None
        emb = self._latent_space.get_embedding(modality)
        if emb is None:
            return None
        return emb.tolist()

    def registered_item_count(self) -> int:
        return len(self._items)

    def reset(self) -> None:
        self._latent_space.reset()
        self._items.clear()
