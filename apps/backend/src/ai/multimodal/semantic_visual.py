"""
Semantic Visual Encoder — CLIP-based semantic feature extraction (P42).

Uses HuggingFace transformers' CLIPModel with optional torch backend.
Falls back gracefully to None when torch/transformers/CLIP is unavailable.

Feature pipeline:
  1. CLIP ViT image encoder → 512-dim semantic vector
  2. Falls back to None when no torch available

This runs IN PARALLEL with VisualEncoder (256-dim structural CNN features).
The DualEncoderRouter combines both outputs.
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy-load torch and CLIP with guarded imports
_CLIP_AVAILABLE = False
_CLIP_MODEL = None
_CLIP_PROCESSOR = None


def _lazy_init_clip():
    """Try to load CLIP model and processor. Returns (model, processor) or (None, None)."""
    global _CLIP_AVAILABLE, _CLIP_MODEL, _CLIP_PROCESSOR
    if _CLIP_AVAILABLE:
        return _CLIP_MODEL, _CLIP_PROCESSOR
    try:
        import torch
        import transformers
        from transformers import CLIPModel, CLIPProcessor

        model_name = "openai/clip-vit-base-patch32"
        _CLIP_MODEL = CLIPModel.from_pretrained(model_name)
        _CLIP_PROCESSOR = CLIPProcessor.from_pretrained(model_name)
        _CLIP_MODEL.eval()
        if torch.cuda.is_available():
            _CLIP_MODEL = _CLIP_MODEL.cuda()
        _CLIP_AVAILABLE = True
        logger.info("SemanticVisualEncoder: CLIP loaded (%s)", model_name)
    except Exception as e:
        logger.warning("SemanticVisualEncoder: CLIP load failed: %s", e)
        _CLIP_AVAILABLE = False
        _CLIP_MODEL = None
        _CLIP_PROCESSOR = None
    return _CLIP_MODEL, _CLIP_PROCESSOR


class SemanticVisualEncoder:
    """Encodes images into 512-dim CLIP semantic vectors.

    Parallel to VisualEncoder (256-dim structural CNN features).
    Semantic vectors capture high-level meaning (objects, scenes, concepts)
    rather than pixel-level statistics.

    Features:
    - torch-guarded lazy initialization
    - 512-dim CLIP ViT embedding
  - Graceful fallback: is_available = False when no torch/CLIP
  - Singleton model instance (shared across all encoder instances)
    """

    FEATURE_DIM: int = 512
    INPUT_SIZE: int = 224  # CLIP ViT input size

    def __init__(self):
        self._model, self._processor = None, None

    @property
    def is_available(self) -> bool:
        """Whether the CLIP backend is available."""
        model, _ = self._get_backend()
        return model is not None

    def _get_backend(self) -> Tuple[Optional[object], Optional[object]]:
        """Get or lazy-init CLIP backend."""
        if self._model is None:
            self._model, self._processor = _lazy_init_clip()
        return self._model, self._processor

    def encode(self, image_data: bytes) -> Optional[np.ndarray]:
        """Encode image bytes into a 512-dim CLIP semantic vector.

        Args:
            image_data: Raw image bytes (PNG, JPEG, etc.)

        Returns:
            512-dim float32 numpy array, or None if CLIP is unavailable or encoding fails.
        """
        model, processor = self._get_backend()
        if model is None or processor is None:
            logger.debug("SemanticVisualEncoder: CLIP unavailable, returning None")
            return None
        try:
            import torch

            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            inputs = processor(images=img, return_tensors="pt")
            with torch.no_grad():
                outputs = model.get_image_features(**inputs)
                # get_image_features() may return BaseModelOutputWithPooling named tuple
                if hasattr(outputs, 'pooler_output'):
                    emb = outputs.pooler_output
                elif hasattr(outputs, 'image_embeds'):
                    emb = outputs.image_embeds
                else:
                    emb = outputs
            vec = emb.cpu().numpy().flatten().astype(np.float32)
            # L2 normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as e:
            logger.debug("SemanticVisualEncoder encode failed: %s", e)
            return None

    def encode_from_pil(self, img: Image.Image) -> Optional[np.ndarray]:
        """Encode a PIL Image into a 512-dim CLIP semantic vector."""
        model, processor = self._get_backend()
        if model is None or processor is None:
            return None
        try:
            import torch

            inputs = processor(images=img, return_tensors="pt")
            with torch.no_grad():
                outputs = model.get_image_features(**inputs)
                if hasattr(outputs, 'pooler_output'):
                    emb = outputs.pooler_output
                elif hasattr(outputs, 'image_embeds'):
                    emb = outputs.image_embeds
                else:
                    emb = outputs
            vec = emb.cpu().numpy().flatten().astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec
        except Exception as e:
            logger.debug("SemanticVisualEncoder encode_from_pil failed: %s", e)
            return None

    def encode_text(self, texts: List[str]) -> Optional[np.ndarray]:
        """Encode text strings into CLIP text embeddings.

        Returns text vectors in the SAME 512-dim space as image vectors,
        enabling cosine similarity comparison between images and text.

        Args:
            texts: List of text strings to encode.

        Returns:
            [N, 512] float32 array, L2-normalized per row.
            None if CLIP is unavailable.
        """
        model, processor = self._get_backend()
        if model is None or processor is None:
            return None
        try:
            import torch

            inputs = processor(text=texts, return_tensors="pt",
                               padding=True, truncation=True, max_length=77)
            with torch.no_grad():
                outputs = model.get_text_features(**inputs)
            if hasattr(outputs, 'pooler_output'):
                text_features = outputs.pooler_output
            elif hasattr(outputs, 'text_embeds'):
                text_features = outputs.text_embeds
            else:
                text_features = outputs
            vecs = text_features.cpu().numpy().astype(np.float32)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            return vecs / norms
        except Exception as e:
            logger.debug("SemanticVisualEncoder encode_text failed: %s", e)
            return None

    def classify_image(self, image_data: bytes, labels: List[str],
                       confidence_threshold: float = 0.15) -> List[Dict[str, Any]]:
        """Zero-shot classify an image against text labels using CLIP.

        Compares the image embedding against text embeddings for each label.
        Returns ranked results with softmax probabilities.

        Args:
            image_data: Raw image bytes (PNG, JPEG, etc.)
            labels: Text labels to classify against
                    (e.g. ["a photo of a chicken", "a photo of a cat"]).
            confidence_threshold: Minimum probability to include in results.

        Returns:
            List of {label, confidence, raw_score, rank}, sorted by
            descending confidence. Empty if CLIP unavailable or encoding fails.
        """
        img_vec = self.encode(image_data)
        if img_vec is None:
            return []
        text_vecs = self.encode_text(labels)
        if text_vecs is None:
            return []
        scores = text_vecs @ img_vec
        temp = 0.01
        scores_scaled = scores / temp
        exp_scores = np.exp(scores_scaled - scores_scaled.max())
        probs = exp_scores / exp_scores.sum()

        results = []
        for i, (label, prob) in enumerate(zip(labels, probs)):
            if prob >= confidence_threshold:
                results.append({
                    "label": label,
                    "confidence": round(float(prob), 4),
                    "raw_score": round(float(scores[i]), 4),
                    "rank": 0,
                })
        results.sort(key=lambda x: x["confidence"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1
        return results
