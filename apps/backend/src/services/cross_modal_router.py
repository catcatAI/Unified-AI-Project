"""
CrossModalRouter — routes multimodal requests to the correct pipeline.

Analogous to ModelBus for the chat pipeline. Supports:
  - Unimodal routing (vision-only, audio-only)
  - Cross-modal routing (vision↔audio comparison, generation)
  - Fallback chain: cross-modal → parallel unimodal → text-only
  - Confidence scoring per route
  - LRU caching for repeated identical requests
  - Rate limiting to prevent O(n²) computation

P33: Cross-modal integration layer after P30-P32 single-modality pipelines.
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from core.utils import safe_error

logger = logging.getLogger(__name__)


class CrossModalRouter:
    """Routes multimodal requests to correct pipeline with confidence scoring.

    Attributes:
        cache_size: Max entries in LRU result cache (default 20)
        rate_limit: Max cross-modal requests per minute (default 60)
    """

    VISION_DIM: int = 256
    AUDIO_DIM: int = 128
    LATENT_DIM: int = 64
    ROUTE_TIMEOUT: float = 30.0

    def __init__(self, cache_size: int = 20, rate_limit: int = 60):
        self._multimodal_svc = None
        self._vision_pipeline = None
        self._audio_pipeline = None
        self._latent_space = None
        # Cache: {request_hash: result}
        self._cache: OrderedDict = OrderedDict()
        self._cache_size = cache_size
        # Rate limiting
        self._rate_limit = rate_limit
        self._request_timestamps: List[float] = []

    # --- Lazy initialization ---

    def _get_multimodal_svc(self):
        if self._multimodal_svc is None:
            from services.multimodal_service import MultimodalService

            self._multimodal_svc = MultimodalService()
        return self._multimodal_svc

    def _get_vision_pipeline(self):
        if self._vision_pipeline is None:
            from ai.vision.vision_pipeline import VisionPipeline

            self._vision_pipeline = VisionPipeline()
        return self._vision_pipeline

    def _get_audio_pipeline(self):
        if self._audio_pipeline is None:
            from ai.audio.audio_pipeline import AudioPipeline

            self._audio_pipeline = AudioPipeline()
        return self._audio_pipeline

    def _get_latent_space(self):
        if self._latent_space is None:
            from ai.multimodal.shared_latent_space import get_shared_latent_space

            self._latent_space = get_shared_latent_space(latent_dim=self.LATENT_DIM)
        return self._latent_space

    # --- Rate limiting ---

    def _check_rate_limit(self) -> bool:
        """Check if request is within rate limit. Returns True if allowed."""
        now = time.time()
        # Prune timestamps older than 60s
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 60.0]
        if len(self._request_timestamps) >= self._rate_limit:
            return False
        self._request_timestamps.append(now)
        return True

    # --- Cache ---

    def _make_cache_key(self, modality: str, data: bytes, mode: str) -> str:
        """Generate a deterministic cache key."""
        return hashlib.md5(f"{modality}:{mode}:".encode() + data).hexdigest()

    def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return dict(self._cache[key])
        return None

    def _cache_put(self, key: str, result: Dict[str, Any]) -> None:
        self._cache[key] = {
            k: v
            for k, v in result.items()
            if k not in ("decoded_image", "decoded_array", "decoded_waveform")
        }
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    # --- Core routing ---

    async def route(
        self, modality: str, data: bytes, mode: str = "auto", item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route a multimodal request to the correct pipeline.

        Args:
            modality: "vision", "audio", or "cross"
            data: Raw bytes (image PNG/JPEG or audio WAV)
            mode: "auto" (detect), "encode", "decode", "compare", "generate"
            item_id: Optional identifier

        Returns:
            dict with:
              - result: the pipeline result
              - pipeline: which pipeline was used ("vision", "audio", "cross", "unavailable")
              - confidence: confidence score [0, 1]
              - time_ms: processing time
              - error: error message if any
        """
        t0 = time.time()

        # Check rate limit
        if not self._check_rate_limit():
            return {
                "result": None,
                "pipeline": "rate_limited",
                "confidence": 0.0,
                "time_ms": round((time.time() - t0) * 1000, 1),
                "error": "Rate limit exceeded",
            }

        # Check cache
        cache_key = self._make_cache_key(modality, data, mode)
        cached = self._cache_get(cache_key)
        if cached is not None:
            cached["pipeline"] = "cache"
            cached["time_ms"] = round((time.time() - t0) * 1000, 1)
            return cached

        # Route to correct pipeline
        try:
            if modality == "vision":
                result = await self._route_vision(data, mode, item_id)
                result["pipeline"] = "vision"
            elif modality == "audio":
                result = await self._route_audio(data, mode, item_id)
                result["pipeline"] = "audio"
            elif modality == "cross":
                result = await self._route_cross(data, mode, item_id)
                result["pipeline"] = "cross"
            else:
                return {
                    "result": None,
                    "pipeline": "unknown",
                    "confidence": 0.0,
                    "time_ms": round((time.time() - t0) * 1000, 1),
                    "error": f"Unknown modality: {modality}",
                }

            result["time_ms"] = round((time.time() - t0) * 1000, 1)
            result["modality"] = modality
            result["mode"] = mode

            # Cache successful results
            if result.get("error") is None:
                self._cache_put(cache_key, result)

            return result

        except Exception as e:
            logger.error("CrossModalRouter.route failed: %s", e, exc_info=True)
            return {
                "result": None,
                "pipeline": "error",
                "confidence": 0.0,
                "time_ms": round((time.time() - t0) * 1000, 1),
                "error": safe_error(e),
            }

    # --- Unimodal routing ---

    async def _route_vision(
        self, data: bytes, mode: str = "auto", item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route to vision pipeline."""
        svc = self._get_multimodal_svc()

        if mode in ("auto", "encode", "pipeline"):
            # Use vision pipeline for full processing
            import asyncio

            pipeline = self._get_vision_pipeline()
            result_data = await asyncio.to_thread(pipeline.process, data)
            result = {
                "result": result_data,
                "confidence": min(float(result_data.get("ssim", 0.5) + 0.3), 1.0),
            }
            if result_data.get("error"):
                result["error"] = result_data["error"]
                result["confidence"] = 0.0
            return result

        elif mode == "analyze":
            # Use MultimodalService encode for item registration
            return await svc.encode(data, "vision", item_id)

        else:
            return {"result": None, "error": f"Unknown mode: {mode}", "confidence": 0.0}

    async def _route_audio(
        self, data: bytes, mode: str = "auto", item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route to audio pipeline."""
        svc = self._get_multimodal_svc()

        if mode in ("auto", "encode", "pipeline"):
            import asyncio

            pipeline = self._get_audio_pipeline()
            result_data = await asyncio.to_thread(pipeline.process, data)
            snr_val = result_data.get("snr", 0.0)
            # SNR-based confidence: clamp [-20, 40] dB to [0, 1]
            confidence = max(0.0, min(1.0, (snr_val + 20.0) / 60.0))
            result = {
                "result": result_data,
                "confidence": confidence,
            }
            if result_data.get("error"):
                result["error"] = result_data["error"]
                result["confidence"] = 0.0
            return result

        elif mode == "analyze":
            return await svc.encode(data, "audio", item_id)

        else:
            return {"result": None, "error": f"Unknown mode: {mode}", "confidence": 0.0}

    async def _route_cross(
        self, data: bytes, mode: str = "auto", item_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Route to cross-modal pipeline."""
        svc = self._get_multimodal_svc()
        ls = self._get_latent_space()

        if mode in ("auto", "compare"):
            # Compare across modalities — requires two items registered
            # Fallback: use latent space intrinsic similarity
            sim = ls.similarity("vision", "audio")
            attn = ls.cross_modal_attention("vision", "audio")
            result = {
                "result": {
                    "similarity": sim,
                    "cross_modal_attention": attn,
                },
                "confidence": min(sim + 0.1, 1.0) if sim else 0.3,
            }
            return result

        elif mode == "generate":
            # Cross-modal generation via the registered items
            # Requires item_id to exist in multimodal service
            if item_id:
                return await svc.generate(
                    item_id, "audio" if item_id.startswith("vision") else "vision"
                )
            return {"result": None, "error": "item_id required for generation", "confidence": 0.0}

        else:
            return {"result": None, "error": f"Unknown cross-modal mode: {mode}", "confidence": 0.0}

    # --- Registry management ---

    async def list_pipelines(self) -> Dict[str, Any]:
        """List all available pipelines with status."""
        status = {"vision": False, "audio": False, "cross": False}
        try:
            self._get_vision_pipeline()
            status["vision"] = True
        except Exception:
            logger.warning("Vision pipeline not available", exc_info=True)
        try:
            self._get_audio_pipeline()
            status["audio"] = True
        except Exception:
            logger.warning("Audio pipeline not available", exc_info=True)
        try:
            self._get_latent_space()
            status["cross"] = True
        except Exception:
            logger.warning("Latent space not available", exc_info=True)
        return {
            "pipelines": status,
            "cache_size": len(self._cache),
            "rate_limit": self._rate_limit,
        }

    def clear_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()

    def get_route_stats(self) -> Dict[str, Any]:
        """Return routing statistics."""
        return {
            "cache_size": len(self._cache),
            "vision_pipeline_ready": self._vision_pipeline is not None,
            "audio_pipeline_ready": self._audio_pipeline is not None,
            "multimodal_service_ready": self._multimodal_svc is not None,
        }
