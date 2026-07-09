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
from core.utils import safe_error

logger = logging.getLogger(__name__)


class DualEncoderRouter:
    """Routes encoding requests to structural and/or semantic encoders.

    NOTE on latent space compatibility:
    The combined latent from _combine_latents() now projects through
    SharedLatentSpace (P43), so it lives in the SAME 64-dim space as all
    P15-P38 operations: cross-modal attention, similarity search, RAG
    retrieval. Structural features project through "vision"/"audio"
    modalities; semantic features through "vision_semantic"/"audio_semantic".
    The combined latent is a weighted average (0.6 semantic + 0.4 structural).

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
        self._latent_space = None

    # --- SharedLatentSpace integration (P43) ---

    def _get_latent_space(self):
        """Get or create the SharedLatentSpace with structural + semantic modalities.

        Registers:
        - vision (256-dim) + vision_semantic (512-dim)
        - audio (128-dim) + audio_semantic (384-dim)

        The semantic modalities enable `semantic_consistency()` queries,
        cross-modal similarity between structural and semantic projections,
        and contrastive training on semantic pairs.
        """
        if self._latent_space is None:
            from ai.multimodal.shared_latent_space import get_shared_latent_space
            self._latent_space = get_shared_latent_space(latent_dim=64)
        return self._latent_space

    def semantic_consistency_report(self, vision_features: Optional[List[np.ndarray]] = None,
                                    audio_features: Optional[List[np.ndarray]] = None) -> Dict[str, Any]:
        """Evaluate semantic consistency of encoder outputs.

        Projects feature lists through SharedLatentSpace and measures
        how tightly each cluster of semantic features is grouped.

        Args:
            vision_features: List of 512-dim CLIP vectors for same-class items.
            audio_features: List of 384-dim Whisper vectors for same-class items.

        Returns:
            Dict with consistency scores per modality and overall.
        """
        ls = self._get_latent_space()
        report: Dict[str, Any] = {"overall": 0.0}
        scores = []

        if vision_features and len(vision_features) >= 2:
            report["vision_semantic"] = ls.semantic_consistency("vision", vision_features)
            scores.append(report["vision_semantic"])

        if audio_features and len(audio_features) >= 2:
            report["audio_semantic"] = ls.semantic_consistency("audio", audio_features)
            scores.append(report["audio_semantic"])

        if scores:
            report["overall"] = float(np.mean(scores))
        return report

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
            - structural_latent: 64-dim SharedLatentSpace projection of structural (P43)
            - semantic_latent: 64-dim SharedLatentSpace projection of semantic (P43)
            - latent: projected 64-dim combined vector (weighted average)
            - modalities_used: list of encoder types used
            - error: error message if any
        """
        result: Dict[str, Any] = {
            "structural": None,
            "semantic": None,
            "structural_latent": None,
            "semantic_latent": None,
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

            # Produce combined latent through SharedLatentSpace (P43)
            struct_lat, sem_lat, combined = self._combine_latents(
                "vision",
                result.get("structural"),
                result.get("semantic"),
            )
            result["structural_latent"] = struct_lat
            result["semantic_latent"] = sem_lat
            result["latent"] = combined
        except Exception as e:
            logger.error("DualEncoderRouter.encode_vision failed: %s", e)
            result["error"] = safe_error(e)
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
            - structural_latent: 64-dim projection of structural features
            - semantic_latent: 64-dim projection of semantic features
            - latent: projected combined vector (64-dim, SharedLatentSpace)
            - modalities_used: list of encoder types used
            - error: error message if any
        """
        result: Dict[str, Any] = {
            "structural": None,
            "semantic": None,
            "structural_latent": None,
            "semantic_latent": None,
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

            # Produce combined latent through SharedLatentSpace (P43)
            struct_lat, sem_lat, combined = self._combine_latents(
                "audio",
                result.get("structural"),
                result.get("semantic"),
            )
            result["structural_latent"] = struct_lat
            result["semantic_latent"] = sem_lat
            result["latent"] = combined
        except Exception as e:
            logger.error("DualEncoderRouter.encode_audio failed: %s", e)
            result["error"] = safe_error(e)
        return result

    # --- Latent combination ---

    def _combine_latents(self,
                         modality: str,
                         structural: Optional[np.ndarray],
                         semantic: Optional[np.ndarray]) -> Tuple[Optional[np.ndarray],
                                                                   Optional[np.ndarray],
                                                                   Optional[np.ndarray]]:
        """Combine structural and semantic vectors through SharedLatentSpace.

        Unlike P42's random projection, this method:
        1. Projects structural features through SharedLatentSpace ``{modality}``
        2. Projects semantic features through ``{modality}_semantic``
        3. Combines via weighted average (semantic dominant, structural grounding)

        This ensures the output latent lives in the SAME 64-dim space as all
        P15-P38 operations: cross-modal attention, similarity search, RAG.

        Returns
        -------
        tuple (structural_latent, semantic_latent, combined_latent)
            Each is 64-dim or None. Combined is weighted-average + L2 normalized.
        """
        ls = self._get_latent_space()

        structural_latent = None
        if structural is not None and hasattr(structural, 'size') and structural.size > 0:
            structural_latent = ls.project(modality, structural.flatten().astype(np.float32))

        semantic_latent = None
        if semantic is not None and hasattr(semantic, 'size') and semantic.size > 0:
            semantic_name = f"{modality}_semantic"
            semantic_latent = ls.project(semantic_name, semantic.flatten().astype(np.float32))

        # Weighted average: semantic dominant, structural as grounding
        combined = None
        if structural_latent is not None and semantic_latent is not None:
            combined = 0.6 * semantic_latent + 0.4 * structural_latent
        elif structural_latent is not None:
            combined = structural_latent.copy()
        elif semantic_latent is not None:
            combined = semantic_latent.copy()

        # Always L2 normalize the combined latent
        if combined is not None:
            norm = np.linalg.norm(combined)
            if norm > 0:
                combined = combined / norm

        return structural_latent, semantic_latent, combined
