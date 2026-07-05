"""Cross-modal similarity service — orchestrates encoding/decoding and latent-space comparison."""

import io
import logging
import wave
from typing import Any, Dict, List, Optional

import numpy as np
from ai.multimodal.audio_decoder import AudioWaveformDecoder
from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
from ai.multimodal.quality_metrics import quality_report, snr, ssim
from ai.multimodal.shared_latent_space import SharedLatentSpace, get_shared_latent_space
from ai.multimodal.visual_decoder import VisualDecoder
from ai.multimodal.visual_encoder import VisualEncoder
from PIL import Image

logger = logging.getLogger(__name__)

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
        self._latent_space = get_shared_latent_space(latent_dim=self.LATENT_DIM)
        self._items: Dict[str, str] = {}

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

    def load_weights(self, weights_path: str) -> bool:
        """Load trained weights from a .npz file into SharedLatentSpace and decoders.

        Expected keys: vision_W, vision_b, audio_W, audio_b,
                       visual_decoder_W, visual_decoder_b,
                       audio_decoder_W, audio_decoder_b.

        Returns True on success, False if file not found or invalid.
        """
        try:
            import numpy as np
            data = np.load(weights_path, allow_pickle=False)
        except Exception as e:
            logger.warning("Failed to load weights from %s: %s", weights_path, e)
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
            logger.info("Trained weights loaded from %s", weights_path)
            return True
        except Exception as e:
            logger.warning("Failed to apply weights: %s", e)
            return False

    def save_weights(self, weights_path: str) -> bool:
        """Save current weights to a .npz file.

        Useful for snapshotting before/after training comparisons.
        """
        try:
            from pathlib import Path

            import numpy as np
            vis = self._latent_space._projections.get("vision", {})
            aud = self._latent_space._projections.get("audio", {})
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
            Path(weights_path).parent.mkdir(parents=True, exist_ok=True)
            np.savez(weights_path, **save_data)
            logger.info("Weights saved to %s", weights_path)
            return True
        except Exception as e:
            logger.warning("Failed to save weights: %s", e)
            return False

    def registered_item_count(self) -> int:
        return len(self._items)

    def reset(self) -> None:
        self._latent_space.reset()
        self._items.clear()

    def evaluate_image_generation(self, image_data: bytes, item_id: str) -> Optional[Dict[str, float]]:
        """Encode → decode → evaluate SSIM for a registered image.

        Returns {'ssim': float} or None if item not found.
        """
        modality = self._items.get(item_id)
        if modality != "vision":
            return None
        latent = self._latent_space.get_embedding("vision")
        if latent is None:
            return None
        decoded_pil = self._visual_decoder.decode_to_pil(latent)
        if decoded_pil is None:
            return None
        original_pil = Image.open(io.BytesIO(image_data)).convert("RGB")
        ssim_val = ssim(np.array(original_pil), np.array(decoded_pil))
        return {"ssim": ssim_val}

    def evaluate_audio_generation(self, audio_data: bytes, item_id: str) -> Optional[Dict[str, float]]:
        """Encode → decode → evaluate SNR for a registered audio.

        Returns {'snr': float} or None if item not found.
        """
        modality = self._items.get(item_id)
        if modality != "audio":
            return None
        latent = self._latent_space.get_embedding("audio")
        if latent is None:
            return None
        wav = self._audio_decoder.decode(latent)
        if wav is None or len(wav) == 0:
            return None
        try:
            with wave.open(io.BytesIO(audio_data), "rb") as wf:
                raw = wf.readframes(wf.getnframes())
                arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        except Exception:
            arr = np.frombuffer(audio_data, dtype=np.float32).flatten()
        if len(arr) == 0:
            return None
        min_len = min(len(arr), len(wav))
        snr_val = snr(arr[:min_len], wav[:min_len])
        return {"snr": snr_val}

    def full_quality_report(self, image_data: Optional[bytes] = None,
                            audio_data: Optional[bytes] = None,
                            image_item: str = "",
                            audio_item: str = "") -> Dict[str, Any]:
        """Comprehensive quality report for both image and audio.

        Evaluates SSIM for image and SNR for audio.
        """
        report: Dict[str, Any] = {}
        if image_data and image_item:
            img_report = self.evaluate_image_generation(image_data, image_item)
            if img_report:
                report["image"] = img_report
        if audio_data and audio_item:
            aud_report = self.evaluate_audio_generation(audio_data, audio_item)
            if aud_report:
                report["audio"] = aud_report
        return report
