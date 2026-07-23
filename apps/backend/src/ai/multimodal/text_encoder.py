"""Text encoder — CLIP-based text feature extraction for SharedLatentSpace.

Wraps CLIP's text encoder to produce 512-dim feature vectors that can be
projected into SharedLatentSpace alongside vision and audio modalities.

This enables cross-modal reasoning: text ↔ image ↔ audio comparison
in a shared 64-dim latent space.
"""

import logging
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class TextEncoder:
    """Encodes text strings into CLIP text embeddings (512-dim).

    Uses the same CLIP model as SemanticVisualEncoder, ensuring text and
    image embeddings are in the same 512-dim space for cosine similarity.

    Feature pipeline:
      1. CLIP text tokenizer → token IDs
      2. CLIP text transformer → 512-dim semantic vector
      3. L2-normalize

    This encoder is the "text modality encoder" that connects text to
    SharedLatentSpace, completing the tri-modal architecture:
      Text → TextEncoder(512) → SharedLatentSpace → 64-dim
      Image → VisualEncoder(256) → SharedLatentSpace → 64-dim
      Audio → AudioSpectralEncoder(128) → SharedLatentSpace → 64-dim
    """

    FEATURE_DIM: int = 512

    def __init__(self, feature_dim: Optional[int] = None):
        self._feature_dim = feature_dim or self.FEATURE_DIM
        self._clip_available = False
        self._model = None
        self._processor = None

    def _get_clip(self):
        """Lazy-load CLIP model and processor."""
        if self._clip_available and self._model is not None:
            return self._model, self._processor
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor

            model_name = "openai/clip-vit-base-patch32"
            self._model = CLIPModel.from_pretrained(model_name)
            self._processor = CLIPProcessor.from_pretrained(model_name)
            self._model.eval()
            if torch.cuda.is_available():
                self._model = self._model.cuda()
            self._clip_available = True
            logger.info("TextEncoder: CLIP loaded (%s)", model_name)
        except Exception as e:
            logger.warning("TextEncoder: CLIP load failed: %s", e)
            self._clip_available = False
            return None, None
        return self._model, self._processor

    def encode(self, text: str) -> np.ndarray:
        """Encode a single text string into a 512-dim feature vector.

        Args:
            text: Input text string.

        Returns:
            (512,) float32 L2-normalized vector.
            Falls back to zeros if CLIP is unavailable.
        """
        vecs = self.encode_batch([text])
        if vecs is None or len(vecs) == 0:
            return np.zeros(self._feature_dim, dtype=np.float32)
        return vecs[0]

    def encode_batch(self, texts: List[str]) -> Optional[np.ndarray]:
        """Encode a batch of text strings into 512-dim feature vectors.

        Args:
            texts: List of text strings.

        Returns:
            [N, 512] float32 L2-normalized array.
            None if CLIP is unavailable.
        """
        model, processor = self._get_clip()
        if model is None or processor is None:
            return None
        try:
            import torch

            inputs = processor(
                text=texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=77,
            )
            with torch.no_grad():
                text_features = model.get_text_features(**inputs)
            vecs = text_features.cpu().numpy().astype(np.float32)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return vecs / norms
        except Exception as e:
            logger.warning("TextEncoder encode_batch failed: %s", e, exc_info=True)
            return None

    @property
    def feature_dim(self) -> int:
        return self._feature_dim
