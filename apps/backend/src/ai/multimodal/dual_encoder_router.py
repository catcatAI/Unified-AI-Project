"""
Dual Encoder Router — selects between semantic and structural encoders (P42).

The core insight: the project needs BOTH:
1. Structural encoders (VisualEncoder/AudioSpectralEncoder) — pure numpy,
   always available, pixel/spectrogram-level features
2. Semantic encoders (SemanticVisualEncoder/SemanticAudioEncoder) — torch-based,
   high-level meaning features, may be unavailable

The DualEncoderRouter:
- Automatically routes to the best available encoder
- Returns BOTH semantic and structural vectors when possible
- Falls back gracefully when torch/CLIP/Whisper is unavailable
- Provides a unified encode_vision() / encode_audio() API
"""

import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class DualEncoderRouter:
    """Routes encoding requests to structural and/or semantic encoders.

    NOTE on latent space compatibility:
    The combined latent from _combine_latents() uses random projection
    (seed=42) into 64-dim, NOT the existing SharedLatentSpace. This means
    the combined latent lives in a DIFFERENT latent space than all P15-P38
    operations (cross-modal attention, similarity search, RAG retrieval).
    P44 will add an explicit alignment layer between the dual-encoder
    latent and SharedLatentSpace.

    Provides a unified API that:
    - Always returns structural features (numpy-based, always available)
    - Optionally returns semantic features (torch-based, may be unavailable)
    - Reports availability of each encoder backend
    """

    def __init__(self):
        self._visual_encoder = None
        self._audio_encoder = None
        self._semantic_visual = None
        self._semantic_audio = None

    # --- Lazy init ---

    def _get_visual_encoder(self):
        if self._visual_encoder is None:
            from ai.multimodal.visual_encoder import VisualEncoder
            self._visual_encoder = VisualEncoder(feature_dim=256)
        return self._visual_encoder

    def _get_audio_encoder(self):
        if self._audio_encoder is None:
            from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
            self._audio_encoder = AudioSpectralEncoder(feature_dim=128)
        return self._audio_encoder

    def _get_semantic_visual(self):
        if self._semantic_visual is None:
            from ai.multimodal.semantic_visual import SemanticVisualEncoder
            self._semantic_visual = SemanticVisualEncoder()
        return self._semantic_visual

    def _get_semantic_audio(self):
        if self._semantic_audio is None:
            from ai.multimodal.semantic_audio import SemanticAudioEncoder
            self._semantic_audio = SemanticAudioEncoder()
        return self._semantic_audio

    # --- Availability ---

    @property
    def semantic_vision_available(self) -> bool:
        """Whether CLIP-based semantic vision encoder is available."""
        return self._get_semantic_visual().is_available

    @property
    def semantic_audio_available(self) -> bool:
        """Whether Whisper-based semantic audio encoder is available."""
        return self._get_semantic_audio().is_available

    @property
    def structural_vision_available(self) -> bool:
        """Structural vision encoder is always available (pure numpy)."""
        return True

    @property
    def structural_audio_available(self) -> bool:
        """Structural audio encoder is always available (pure numpy)."""
        return True

    def availability_report(self) -> Dict[str, bool]:
        """Report availability of all encoder backends."""
        return {
            "structural_vision": True,
            "structural_audio": True,
            "semantic_vision": self.semantic_vision_available,
            "semantic_audio": self.semantic_audio_available,
        }

    # --- Encoding ---

    def encode_vision(self, image_data: bytes,
                      include_semantic: bool = True,
                      include_structural: bool = True) -> Dict[str, Any]:
        """Encode image using both structural and semantic encoders.

        Args:
            image_data: Raw image bytes (PNG/JPEG)
            include_semantic: Whether to attempt CLIP semantic encoding
            include_structural: Whether to include structural encoding

        Returns:
            Dict with keys:
            - structural: 256-dim numpy array (or None)
            - semantic: 512-dim numpy array (or None)
            - latent: projected 64-dim combined vector (or structural-only)
            - modalities_used: list of encoder types used
            - error: error message if any
        """
        result: Dict[str, Any] = {
            "structural": None,
            "semantic": None,
            "latent": None,
            "modalities_used": [],
            "error": None,
        }
        try:
            # Structural encoding (always available)
            if include_structural:
                ve = self._get_visual_encoder()
                structural = ve.encode(image_data)
                result["structural"] = structural
                result["modalities_used"].append("structural_vision")

            # Semantic encoding (may be unavailable)
            if include_semantic:
                sve = self._get_semantic_visual()
                if sve.is_available:
                    semantic = sve.encode(image_data)
                    result["semantic"] = semantic
                    if semantic is not None:
                        result["modalities_used"].append("semantic_vision")

            # Produce combined latent
            result["latent"] = self._combine_latents(
                result.get("structural"),
                result.get("semantic")
            )
        except Exception as e:
            logger.error("DualEncoderRouter.encode_vision failed: %s", e)
            result["error"] = str(e)
        return result

    def encode_audio(self, audio_data: bytes,
                     include_semantic: bool = True,
                     include_structural: bool = True) -> Dict[str, Any]:
        """Encode audio using both structural and semantic encoders.

        Args:
            audio_data: Raw audio bytes (WAV)
            include_semantic: Whether to attempt Whisper semantic encoding
            include_structural: Whether to include structural encoding

        Returns:
            Dict with keys:
            - structural: 128-dim numpy array (or None)
            - semantic: 384-dim numpy array (or None)
            - latent: projected combined vector
            - modalities_used: list of encoder types used
            - error: error message if any
        """
        result: Dict[str, Any] = {
            "structural": None,
            "semantic": None,
            "latent": None,
            "modalities_used": [],
            "error": None,
        }
        try:
            if include_structural:
                ae = self._get_audio_encoder()
                structural = ae.encode(audio_data)
                result["structural"] = structural
                result["modalities_used"].append("structural_audio")

            if include_semantic:
                sae = self._get_semantic_audio()
                if sae.is_available:
                    semantic = sae.encode(audio_data)
                    result["semantic"] = semantic
                    if semantic is not None:
                        result["modalities_used"].append("semantic_audio")

            result["latent"] = self._combine_latents(
                result.get("structural"),
                result.get("semantic")
            )
        except Exception as e:
            logger.error("DualEncoderRouter.encode_audio failed: %s", e)
            result["error"] = str(e)
        return result

    # --- Latent combination ---

    def _combine_latents(self,
                         structural: Optional[np.ndarray],
                         semantic: Optional[np.ndarray]) -> Optional[np.ndarray]:
        """Combine structural and semantic vectors into a unified latent.

        Strategy:
        - If both available: concatenate and project to 64-dim via random projection
        - If only structural: project structural to 64-dim
        - If only semantic: project semantic to 64-dim
        - If neither: return None
        """
        vectors = []
        if structural is not None and hasattr(structural, 'size') and structural.size > 0:
            vectors.append(structural.flatten())
        if semantic is not None and hasattr(semantic, 'size') and semantic.size > 0:
            vectors.append(semantic.flatten())

        if not vectors:
            return None

        combined = np.concatenate(vectors).astype(np.float32)
        target_dim = 64

        if len(combined) == target_dim:
            return combined
        if len(combined) < target_dim:
            padded = np.zeros(target_dim, dtype=np.float32)
            padded[:len(combined)] = combined
            return padded

        # Project down: random projection
        rng = np.random.default_rng(42)
        proj = rng.normal(0, 1.0 / np.sqrt(len(combined)),
                          (target_dim, len(combined))).astype(np.float32)
        latent = proj @ combined
        # L2 normalize
        norm = np.linalg.norm(latent)
        if norm > 0:
            latent = latent / norm
        return latent
