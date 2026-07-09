"""
MultimodalService — orchestration layer for multimodal pipelines.

Analogous to ChatService for the chat pipeline. Coordinates:
  - Encoding (VisualEncoder / AudioSpectralEncoder)
  - Decoding (VisualDecoder / AudioWaveformDecoder)
  - Latent space operations (SharedLatentSpace project/compare/attention)
  - Cross-modal RAG retrieval (MultimodalRAGEngine)
  - Training (FullTrainingPipeline)
  - Quality evaluation (quality_metrics: SSIM/PSNR/SNR)
  - Weight persistence (load/save)

P30: First service layer for multimodal pipeline.
     All methods are async with proper error handling and timeouts.
"""

import asyncio
import io
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from core.utils import safe_error
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy imports for heavy modules


class MultimodalService:
    """Unified orchestrator for all multimodal operations.

    Thread-safe: each method creates its own backend instances lazily.
    Timeout-safe: all methods wrapped with asyncio.wait_for(timeout=30).
    """

    ENCODE_TIMEOUT = 30
    DECODE_TIMEOUT = 30
    COMPARE_TIMEOUT = 15
    RETRIEVE_TIMEOUT = 15
    TRAIN_TIMEOUT = 120
    EVALUATE_TIMEOUT = 30
    GENERATE_TIMEOUT = 60
    VISION_DIM = 256
    AUDIO_DIM = 128
    LATENT_DIM = 64

    def __init__(self):
        self._encoders: Dict[str, Any] = {}
        self._decoders: Dict[str, Any] = {}
        self._latent_space = None
        self._bridge = None
        self._rag_engine = None
        self._pipeline = None
        self._vision_pipeline = None
        self._quality_monitor = None
        self._audio_pipeline = None
        self._audio_quality_monitor = None
        self._registered_items: Dict[str, Dict[str, Any]] = {}
        self._items_lock = asyncio.Lock()
        # P36: Continuous multimodal learning + memory
        self._cml = None
        self._memory_store = None
        # P37: Production hardening
        self._error_recovery = None
        self._state_persistence = None
        self._mm_quality_monitor = None
        # P42: Dual encoder router (structural + semantic)
        self._dual_encoder = None
        self._initial_training_started = False
        self._training_lock = threading.Lock()

    # --- Lazy initialization ---

    def _get_visual_encoder(self):
        if "vision" not in self._encoders:
            from ai.multimodal.visual_encoder import VisualEncoder
            self._encoders["vision"] = VisualEncoder(feature_dim=self.VISION_DIM)
        return self._encoders["vision"]

    def _get_audio_encoder(self):
        if "audio" not in self._encoders:
            from ai.multimodal.audio_encoder_spectral import AudioSpectralEncoder
            self._encoders["audio"] = AudioSpectralEncoder(feature_dim=self.AUDIO_DIM)
        return self._encoders["audio"]

    def _get_visual_decoder(self):
        if "vdecoder" not in self._decoders:
            from ai.multimodal.visual_decoder import (
                VisualDecoder,
                load_default_visual_decoder_weights,
            )
            self._decoders["vdecoder"] = VisualDecoder()
            load_default_visual_decoder_weights(self._decoders["vdecoder"])
        return self._decoders["vdecoder"]

    def _get_audio_decoder(self):
        if "adecoder" not in self._decoders:
            from ai.multimodal.audio_decoder import (
                AudioWaveformDecoder,
                load_default_audio_decoder_weights,
            )
            self._decoders["adecoder"] = AudioWaveformDecoder()
            load_default_audio_decoder_weights(self._decoders["adecoder"])
        return self._decoders["adecoder"]

    def _get_latent_space(self):
        if self._latent_space is None:
            from ai.multimodal.shared_latent_space import get_shared_latent_space
            self._latent_space = get_shared_latent_space(latent_dim=self.LATENT_DIM)
        return self._latent_space

    def _get_bridge(self):
        if self._bridge is None:
            from ai.multimodal.multimodal_bridge import MultimodalBridge
            self._bridge = MultimodalBridge()
        return self._bridge

    def _get_rag_engine(self):
        if self._rag_engine is None:
            from ai.multimodal.multimodal_rag_engine import MultimodalRAGEngine
            self._rag_engine = MultimodalRAGEngine()
        return self._rag_engine

    def _get_vision_pipeline(self):
        """Get or create the VisionPipeline (P31)."""
        if self._vision_pipeline is None:
            from ai.vision.vision_pipeline import VisionPipeline
            self._vision_pipeline = VisionPipeline()
        return self._vision_pipeline

    def _get_quality_monitor(self):
        """Get or create the VisionQualityMonitor (P31)."""
        if self._quality_monitor is None:
            from ai.vision.quality_monitor import VisionQualityMonitor
            self._quality_monitor = VisionQualityMonitor()
        return self._quality_monitor

    def _get_audio_pipeline(self):
        """Get or create the AudioPipeline (P32)."""
        if self._audio_pipeline is None:
            from ai.audio.audio_pipeline import AudioPipeline
            self._audio_pipeline = AudioPipeline()
        return self._audio_pipeline

    def _get_audio_quality_monitor(self):
        """Get or create the AudioQualityMonitor (P32)."""
        if self._audio_quality_monitor is None:
            from ai.audio.quality_monitor import AudioQualityMonitor
            self._audio_quality_monitor = AudioQualityMonitor()
        return self._audio_quality_monitor

    # --- P36: Continuous learning ---

    def _get_cml(self):
        """Get or create the ContinuousMultimodalLearning instance."""
        if self._cml is None:
            from ai.multimodal.continuous_multimodal_learning import ContinuousMultimodalLearning
            self._cml = ContinuousMultimodalLearning(
                buffer_max=64,
                auto_train_threshold=32,
                min_interval_sec=60.0,
                pipeline=self._get_pipeline(),
            )
        return self._cml

    def _get_memory_store(self):
        """Get or create the MultimodalMemoryStore instance."""
        if self._memory_store is None:
            from ai.multimodal.multimodal_memory import MultimodalMemoryStore
            self._memory_store = MultimodalMemoryStore(
                store_dir=None,  # Will be set if data/ dir is available
                max_entries=5000,
            )
        return self._memory_store

    # --- P42: Dual encoder router ---

    def _get_dual_encoder(self):
        """Get or create the DualEncoderRouter (P42)."""
        if self._dual_encoder is None:
            from ai.multimodal.dual_encoder_router import DualEncoderRouter
            self._dual_encoder = DualEncoderRouter()
        return self._dual_encoder

    async def encode_semantic(self, data: bytes, modality: str) -> Dict[str, Any]:
        """Encode using dual (structural + semantic) encoders (P42).

        Uses DualEncoderRouter to:
        1. Always encode with structural encoder (numpy, always available)
        2. Attempt semantic encoding (torch/CLIP/Whisper, may be unavailable)
        3. Combine into unified latent

        Returns dict with structural, semantic, latent, modalities_used.
        """
        router = self._get_dual_encoder()
        try:
            if modality == "vision":
                return await asyncio.to_thread(router.encode_vision, data)
            elif modality == "audio":
                return await asyncio.to_thread(router.encode_audio, data)
            else:
                return {"error": f"Unknown modality: {modality}"}
        except Exception as e:
            logger.error("encode_semantic failed: %s", e)
            return {"error": safe_error(e)}

    async def semantic_availability(self) -> Dict[str, bool]:
        """Check availability of semantic encoder backends."""
        router = self._get_dual_encoder()
        return router.availability_report()

    # --- CML-integrated encode ---

    async def cml_encode(self, data: bytes, modality: str,
                         item_id: Optional[str] = None) -> Dict[str, Any]:
        """Encode with automatic CML recording.

        Same as encode() but also records the example in CML buffer
        for autonomous micro-training. Extracts quality scores
        from pipeline results (SSIM for vision, SNR for audio).
        """
        result = await self.encode(data, modality, item_id)
        if result.get("error") is None and "latent" in result:
            cml = self._get_cml()
            # Extract quality score from the pipeline run
            quality_score = 0.0
            if modality == "vision":
                qm = self._get_quality_monitor()
                report = qm.report()
                quality_score = report.get("avg_ssim", 0.0)
            elif modality == "audio":
                qm = self._get_audio_quality_monitor()
                report = qm.report()
                quality_score = report.get("avg_snr", 0.0) / 30.0  # Normalize [0,1]
            cml.record_encode(
                modality=modality,
                feature_vector=result.get("feature_vector", []),
                latent=result["latent"],
                quality_score=quality_score,
            )
            # Check if CML should auto-train
            if cml.should_train():
                train_result = cml.micro_train()
                result["cml_trained"] = train_result.get("status") == "completed"
        return result

    async def cml_quality_feedback(self, modality: str,
                                   metrics: Dict[str, Any]) -> None:
        """Record quality feedback to CML."""
        self._get_cml().record_quality(metrics)

    async def cml_stats(self) -> Dict[str, Any]:
        """Get CML statistics."""
        return self._get_cml().get_stats()

    async def cml_trend(self) -> Dict[str, Any]:
        """Get CML quality trend."""
        return self._get_cml().quality_trend()

    async def cml_micro_train(self, epochs: int = 3) -> Dict[str, Any]:
        """Manually trigger a CML micro-training cycle."""
        return self._get_cml().micro_train(epochs=epochs)

    # --- Memory store operations ---

    async def memory_store(self, item_id: str) -> Optional[str]:
        """Store a registered item into multimodal memory."""
        async with self._items_lock:
            item = self._registered_items.get(item_id)
        if item is None:
            return None
        store = self._get_memory_store()
        return await store.store_from_item(item_id, item)

    async def memory_search(self, query_item_id: str, top_k: int = 5,
                            modality_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search memory by latent similarity to a registered item."""
        async with self._items_lock:
            item = self._registered_items.get(query_item_id)
        if item is None or "latent" not in item:
            return []
        store = self._get_memory_store()
        return await store.search(item["latent"], top_k, modality_filter)

    async def memory_recall(self, hours: float = 24) -> List[Dict[str, Any]]:
        """Recall entries from memory within a time window."""
        store = self._get_memory_store()
        return await store.recall_by_time(hours=hours)

    async def memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        store = self._get_memory_store()
        return await store.stats()

    def _get_pipeline(self):
        if self._pipeline is None:
            from ai.multimodal.training_pipeline import FullTrainingPipeline
            self._pipeline = FullTrainingPipeline(
                latent_space=self._get_latent_space(),
                visual_encoder=self._get_visual_encoder(),
                audio_encoder=self._get_audio_encoder(),
                visual_decoder=self._get_visual_decoder(),
                audio_decoder=self._get_audio_decoder(),
            )
            self._ensure_initial_training()
        return self._pipeline

    def _ensure_initial_training(self):
        """Start background training if no trained weights exist (safe for first deployment)."""
        if self._initial_training_started:
            return
        with self._training_lock:
            if self._initial_training_started:
                return
            try:
                weights_path = self._pipeline.DEFAULT_WEIGHTS_PATH
                if not os.path.exists(weights_path):
                    self._initial_training_started = True
                    t = threading.Thread(target=self._pipeline.run, kwargs={
                        "contrastive_epochs": 10, "recon_epochs": 10, "lr": 0.01,
                    }, daemon=True)
                    t.start()
                    logger.info("[Multimodal] No trained weights found at %s — background training started", weights_path)
                else:
                    self._initial_training_started = True
            except Exception as e:
                logger.warning("[Multimodal] Initial training check failed (non-fatal): %s", e)

    # --- Encoding ---

    async def encode(self, data: bytes, modality: str,
                     item_id: Optional[str] = None) -> Dict[str, Any]:
        """Encode data into a feature vector and latent embedding.

        Args:
            data: Raw bytes (image PNG/JPEG or audio WAV)
            modality: "vision" or "audio"
            item_id: Optional identifier for later operations

        Returns:
            dict with item_id, modality, latent, feature_vector, dim, time_ms
        """
        return await asyncio.wait_for(
            self._encode_impl(data, modality, item_id),
            timeout=self.ENCODE_TIMEOUT,
        )

    async def _encode_impl(self, data: bytes, modality: str,
                           item_id: Optional[str] = None) -> Dict[str, Any]:
        t0 = time.time()
        result: Dict[str, Any] = {"modality": modality}
        if not data:
            logger.warning("encode: empty data provided for modality=%s", modality)
            return {"modality": modality, "error": "Empty data provided"}
        try:
            if modality == "vision":
                # P33: Use VisionPipeline for full pipeline (encode→latent→decode→ssim)
                pipeline = self._get_vision_pipeline()
                pipe_result = await asyncio.to_thread(pipeline.process, data)
                if pipe_result.get("error"):
                    return {"modality": modality, "error": pipe_result["error"]}
                vec = pipe_result.get("feature_vector")
                latent = pipe_result.get("latent")
                ssim_val = pipe_result.get("ssim", 0.0)
                # Record quality
                self._get_quality_monitor().record(pipe_result)
            elif modality == "audio":
                # P33: Use AudioPipeline for full pipeline
                pipeline = self._get_audio_pipeline()
                pipe_result = await asyncio.to_thread(pipeline.process, data)
                if pipe_result.get("error"):
                    return {"modality": modality, "error": pipe_result["error"]}
                vec = pipe_result.get("feature_vector")
                latent = pipe_result.get("latent")
                snr_val = pipe_result.get("snr", 0.0)
                # Record quality
                self._get_audio_quality_monitor().record(pipe_result)
            else:
                return {"modality": modality, "error": f"Unknown modality: {modality}"}

            if vec is None or (hasattr(vec, 'size') and vec.size == 0):
                return {"modality": modality, "error": "Encoding returned empty feature vector"}

            # Ensure latent is projected through shared latent space
            if latent is None:
                ls = self._get_latent_space()
                latent = ls.project(modality, np.array(vec))

            if item_id is None:
                item_id = f"{modality}_{int(t0 * 1000)}_{hash(data) & 0xFFFFFF:06x}"

            async with self._items_lock:
                self._registered_items[item_id] = {
                    "modality": modality,
                    "feature_vector": vec.tolist() if hasattr(vec, 'tolist') else (latent.tolist() if isinstance(vec, np.ndarray) else vec),
                    "latent": latent.tolist() if hasattr(latent, 'tolist') else latent,
                    "timestamp": t0,
                }

            result.update({
                "item_id": item_id,
                "latent": (latent.tolist() if hasattr(latent, 'tolist') else latent),
                "feature_vector": (vec.tolist() if hasattr(vec, 'tolist') else vec),
                "dim": len(vec) if hasattr(vec, '__len__') else 0,
                "time_ms": round((time.time() - t0) * 1000, 1),
            })
            # Feed into continuous multimodal learning
            try:
                cml = self._get_cml()
                quality = 0.0
                if modality == "vision":
                    quality = self._get_quality_monitor().last_score() if hasattr(self._get_quality_monitor(), 'last_score') else 0.0
                elif modality == "audio":
                    quality = self._get_audio_quality_monitor().last_score() if hasattr(self._get_audio_quality_monitor(), 'last_score') else 0.0
                cml.record_encode(modality, vec.tolist() if hasattr(vec, 'tolist') else vec,
                                  latent.tolist() if hasattr(latent, 'tolist') else latent, quality)
                if cml.should_train():
                    cml.micro_train()
            except Exception as cml_e:
                logger.debug("CML feed failed (non-fatal): %s", cml_e)
        except Exception as e:
            logger.error("Encode failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)
        return result

    # --- Decoding ---

    async def decode(self, item_id: str, modality: str,
                     output_format: str = "base64") -> Dict[str, Any]:
        """Decode a previously encoded item's latent back to its modality.

        Args:
            item_id: Previously registered item ID
            modality: "vision" or "audio"
            output_format: "base64" for image/audio, "pil" or "raw" for direct

        Returns:
            dict with item_id, modality, decoded data (base64 or raw), quality metrics
        """
        return await asyncio.wait_for(
            self._decode_impl(item_id, modality, output_format),
            timeout=self.DECODE_TIMEOUT,
        )

    async def _decode_impl(self, item_id: str, modality: str,
                           output_format: str = "base64") -> Dict[str, Any]:
        t0 = time.time()
        result: Dict[str, Any] = {
            "item_id": item_id,
            "modality": modality,
            "error": None,
        }
        try:
            async with self._items_lock:
                item = self._registered_items.get(item_id)
            if item is None:
                return {"error": f"Item not found: {item_id}", "item_id": item_id}
            if item["modality"] != modality:
                return {"error": f"Item {item_id} is {item['modality']}, not {modality}"}

            latent = np.array(item["latent"], dtype=np.float32)

            if modality == "vision":
                decoder = self._get_visual_decoder()
                decoded = decoder.decode(latent)  # numpy uint8 array (128,128,3)
                if decoded is None or decoded.size == 0:
                    return {"error": "Decoding returned empty image"}
                pil_img = Image.fromarray(decoded)
                if output_format == "pil":
                    result["decoded"] = pil_img
                else:
                    import base64
                    buf = io.BytesIO()
                    pil_img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    result["decoded"] = f"data:image/png;base64,{b64}"
                from ai.multimodal.quality_metrics import ssim
                original = item.get("feature_vector")
                if original is not None:
                    result["quality"] = {"ssim": 0.0}  # feature-level no ssim
            elif modality == "audio":
                decoder = self._get_audio_decoder()
                wav = decoder.decode(latent)  # numpy float32 array
                if wav is None or len(wav) == 0:
                    return {"error": "Decoding returned empty audio"}
                if output_format == "raw":
                    result["decoded"] = wav.tolist()
                else:
                    import base64
                    import struct
                    sample_rate = 16000
                    int16 = (np.clip(wav, -1.0, 1.0) * 32767).astype(np.int16)
                    buf = io.BytesIO()
                    import wave
                    with wave.open(buf, "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(sample_rate)
                        wf.writeframes(int16.tobytes())
                    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    result["decoded"] = f"data:audio/wav;base64,{b64}"

            result["format"] = output_format
            result["time_ms"] = round((time.time() - t0) * 1000, 1)
        except Exception as e:
            logger.error("Decode failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)
        return result

    # --- Comparison ---

    async def compare(self, item_a: str, item_b: str) -> Dict[str, Any]:
        """Compare two items via cross-modal similarity in latent space.

        Returns dict with similarity score and cross-modal attention weights.
        """
        return await asyncio.wait_for(
            self._compare_impl(item_a, item_b),
            timeout=self.COMPARE_TIMEOUT,
        )

    async def _compare_impl(self, item_a: str, item_b: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "item_a": item_a,
            "item_b": item_b,
        }
        try:
            async with self._items_lock:
                a = self._registered_items.get(item_a)
                b = self._registered_items.get(item_b)
            if a is None or b is None:
                missing = "item_a" if a is None else "item_b"
                return {**result, "error": f"{missing} not found"}
            ls = self._get_latent_space()
            sim = ls.similarity(a["modality"], b["modality"])
            attn = ls.cross_modal_attention(a["modality"], b["modality"])
            result["similarity"] = sim
            result["modality_a"] = a["modality"]
            result["modality_b"] = b["modality"]
            result["cross_modal_attention"] = attn
        except Exception as e:
            logger.error("Compare failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)
        return result

    # --- Retrieval ---

    async def retrieve(self, query_id: str, top_k: int = 5,
                       modality_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve top-k similar entries for a given query item.

        Uses MultimodalRAGEngine to search across indexed modalities.

        Returns list of {key, score, modality, metadata}.
        """
        return await asyncio.wait_for(
            self._retrieve_impl(query_id, top_k, modality_filter),
            timeout=self.RETRIEVE_TIMEOUT,
        )

    async def _retrieve_impl(self, query_id: str, top_k: int = 5,
                             modality_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            async with self._items_lock:
                item = self._registered_items.get(query_id)
            if item is None:
                logger.warning("Query item %s not found for retrieval", query_id)
                return []
            latent = item.get("latent")
            if latent is None:
                return []
            rag = self._get_rag_engine()
            results = rag.query_by_latent(latent, top_k=top_k)
            if modality_filter:
                results = [r for r in results if r.get("modality") == modality_filter]
            return results
        except Exception as e:
            logger.error("Retrieval failed: %s", e, exc_info=True)
            return []

    # --- Training ---

    async def train(self, mode: str = "full", epochs: int = 5,
                    lr: float = 0.01, use_real: bool = False) -> Dict[str, Any]:
        """Run training pipeline.

        Args:
            mode: "contrastive", "recon", or "full"
            epochs: Number of training epochs
            lr: Learning rate
            use_real: Use RealDataProvider if available (Esc-50 / CIFAR-10)

        Returns dict with status, final_loss, history, and optional task_id.
        """
        return await asyncio.wait_for(
            self._train_impl(mode, epochs, lr, use_real),
            timeout=self.TRAIN_TIMEOUT,
        )

    async def _train_impl(self, mode: str = "full", epochs: int = 5,
                          lr: float = 0.01, use_real: bool = False) -> Dict[str, Any]:
        t0 = time.time()
        result: Dict[str, Any] = {
            "mode": mode,
            "status": "running",
        }
        try:
            pipeline = self._get_pipeline()
            if use_real:
                try:
                    from ai.multimodal.data_loader import RealDataProvider
                    dp = RealDataProvider()
                    if dp.has_data():
                        pipeline.run_on_real(
                            dp,
                            contrastive_epochs=epochs if mode in ("full", "contrastive") else 0,
                            recon_epochs=epochs if mode in ("full", "recon") else 0,
                            lr=lr,
                        )
                        result["data_source"] = "real"
                    else:
                        use_real = False
                except Exception as err:
                    logger.warning("Real training failed, falling back to synthetic: %s", err)
                    use_real = False

            if not use_real:
                pipeline.run(
                    contrastive_epochs=epochs if mode in ("full", "contrastive") else 0,
                    recon_epochs=epochs if mode in ("full", "recon") else 0,
                    lr=lr,
                )
                result["data_source"] = "synthetic"

            result["status"] = "completed"
            result["time_ms"] = round((time.time() - t0) * 1000, 1)
        except Exception as e:
            logger.error("Training failed: %s", e, exc_info=True)
            result["status"] = "error"
            result["error"] = safe_error(e)
        return result

    # --- Evaluation ---

    async def evaluate(self, item_id: Optional[str] = None,
                       modality: str = "vision",
                       n_samples: int = 5) -> Dict[str, Any]:
        """Evaluate generation quality.

        Args:
            item_id: If provided, evaluates on this specific item
            modality: Modality to evaluate ("vision" or "audio"), used when no item_id
            n_samples: Number of synthetic samples if no item_id

        Returns dict with quality metrics.
        """
        return await asyncio.wait_for(
            self._evaluate_impl(item_id, modality, n_samples),
            timeout=self.EVALUATE_TIMEOUT,
        )

    async def _evaluate_impl(self, item_id: Optional[str] = None,
                             modality: str = "vision",
                             n_samples: int = 5) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        try:
            if item_id:
                async with self._items_lock:
                    item = self._registered_items.get(item_id)
                if item is None:
                    return {"error": f"Item not found: {item_id}"}
                # P33: Use quality monitors for real evaluation
                if item["modality"] == "vision":
                    qm = self._get_quality_monitor()
                    report = qm.report()
                    result["metrics"] = {
                        "ssim": report.get("avg_ssim", 0.0),
                        "psnr": report.get("avg_psnr", 0.0),
                        "total_encoded": report.get("total_calls", 0),
                        "source": "vision_pipeline_quality_monitor",
                    }
                elif item["modality"] == "audio":
                    qm = self._get_audio_quality_monitor()
                    report = qm.report()
                    result["metrics"] = {
                        "snr": report.get("avg_snr", 0.0),
                        "total_encoded": report.get("total_calls", 0),
                        "source": "audio_pipeline_quality_monitor",
                    }
            else:
                pipeline = self._get_pipeline()
                eval_result = pipeline.evaluate(n_samples=n_samples)
                result["metrics"] = eval_result
        except Exception as e:
            logger.error("Evaluate failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)
        return result

    # --- Generation ---

    async def generate(self, source_item_id: str,
                       target_modality: str) -> Dict[str, Any]:
        """Cross-modal generation: convert source item to target modality.

        E.g., vision→audio (image describes a scene → generate ambient sound)
        or audio→vision (sound → generate abstract visualization).

        Returns dict with generated data (base64).
        """
        return await asyncio.wait_for(
            self._generate_impl(source_item_id, target_modality),
            timeout=self.GENERATE_TIMEOUT,
        )

    async def _generate_impl(self, source_item_id: str,
                             target_modality: str) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "source_item_id": source_item_id,
            "target_modality": target_modality,
        }
        try:
            async with self._items_lock:
                item = self._registered_items.get(source_item_id)
            if item is None:
                return {**result, "error": f"Source item not found: {source_item_id}"}

            source_modality = item["modality"]
            latent = np.array(item["latent"], dtype=np.float32)

            if source_modality == target_modality:
                return {**result, "error": "Source and target modalities are the same"}

            if source_modality == "vision" and target_modality == "audio":
                audio = self._get_audio_decoder().decode(latent)
                import base64
                import struct
                import wave
                int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(int16.tobytes())
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                result["generated"] = f"data:audio/wav;base64,{b64}"
                result["quality"] = {"snr": 0.0}

            elif source_modality == "audio" and target_modality == "vision":
                img = self._get_visual_decoder().decode(latent)
                buf = io.BytesIO()
                Image.fromarray(img).save(buf, format="PNG")
                import base64
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                result["generated"] = f"data:image/png;base64,{b64}"
                result["quality"] = {"ssim": 0.0}

            else:
                result["error"] = f"Unknown cross-modal path: {source_modality} → {target_modality}"
        except Exception as e:
            logger.error("Generate failed: %s", e, exc_info=True)
            result["error"] = safe_error(e)
        return result

    # --- Registry management ---

    async def list_items(self) -> Dict[str, Any]:
        """List all registered items with metadata."""
        async with self._items_lock:
            items = {
                k: {"modality": v["modality"], "timestamp": v.get("timestamp", 0)}
                for k, v in self._registered_items.items()
            }
        return {"items": items, "count": len(items)}

    async def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get a single registered item by ID. Returns None if not found."""
        async with self._items_lock:
            item = self._registered_items.get(item_id)
        return item

    async def clear_items(self) -> Dict[str, Any]:
        """Clear all registered items and reset latent space."""
        async with self._items_lock:
            self._registered_items.clear()
        self._get_latent_space().reset()
        return {"status": "cleared"}

    # --- Weight persistence ---

    async def save_weights(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Save trained weights to .npz file."""
        try:
            sp = self._get_pipeline().save_weights(path)
            return {"status": "saved" if sp else "failed", "path": sp or ""}
        except Exception as e:
            logger.error("Save weights failed: %s", e)
            return {"status": "failed", "error": safe_error(e)}

    async def load_weights(self, path: str) -> Dict[str, Any]:
        """Load trained weights from .npz file and apply to all components."""
        try:
            ok = self._get_pipeline().load_weights(path)
            return {"status": "loaded" if ok else "failed"}
        except Exception as e:
            logger.error("Load weights failed: %s", e)
            return {"status": "failed", "error": safe_error(e)}

    # --- P37: Error recovery ---

    def _get_error_recovery(self):
        """Get or create the MultimodalErrorRecovery instance."""
        if self._error_recovery is None:
            from services.multimodal_error_recovery import MultimodalErrorRecovery
            self._error_recovery = MultimodalErrorRecovery(self)
        return self._error_recovery

    def _get_state_persistence(self):
        """Get or create the MultimodalStatePersistence instance."""
        if self._state_persistence is None:
            from services.multimodal_state_persistence import MultimodalStatePersistence
            self._state_persistence = MultimodalStatePersistence(self)
        return self._state_persistence

    def _get_multimodal_quality_monitor(self):
        """Get or create the MultimodalQualityMonitor instance (P37).

        NOTE: Different from _get_quality_monitor() (P31, VisionQualityMonitor).
        This is the background quality sampling monitor, not the per-pipeline monitor.
        """
        if self._mm_quality_monitor is None:
            from services.multimodal_quality_monitor import MultimodalQualityMonitor
            self._mm_quality_monitor = MultimodalQualityMonitor(self)
        return self._mm_quality_monitor

    # --- P37: Error recovery operations ---

    async def encode_with_retry(self, data: bytes, modality: str,
                                item_id: Optional[str] = None) -> Dict[str, Any]:
        """Encode with automatic retry on failure."""
        return await self._get_error_recovery().encode_with_retry(data, modality, item_id)

    async def decode_with_fallback(self, item_id: str, modality: str,
                                   output_format: str = "base64") -> Dict[str, Any]:
        """Decode with text fallback on failure."""
        return await self._get_error_recovery().decode_with_fallback(
            item_id, modality, output_format
        )

    async def train_with_checkpoint(self, mode: str = "full", epochs: int = 5,
                                    lr: float = 0.01, use_real: bool = False,
                                    checkpoint_label: Optional[str] = None) -> Dict[str, Any]:
        """Train with pre-training checkpoint for resumability."""
        return await self._get_error_recovery().train_with_checkpoint(
            mode, epochs, lr, use_real, checkpoint_label
        )

    async def get_recovery_state(self) -> Dict[str, Any]:
        """Get error recovery state summary."""
        return self._get_error_recovery().get_recovery_state()

    async def reset_recovery_counters(self) -> None:
        """Reset error recovery counters."""
        self._get_error_recovery().reset_counters()

    # --- P37: State persistence ---

    async def save_checkpoint(self, label: Optional[str] = None) -> Dict[str, Any]:
        """Save a checkpoint of multimodal state."""
        return await self._get_state_persistence().save_checkpoint(label)

    async def load_checkpoint(self, label: str) -> Dict[str, Any]:
        """Load a checkpoint by label."""
        return await self._get_state_persistence().load_checkpoint(label)

    async def list_checkpoints(self) -> Dict[str, Any]:
        """List all available checkpoints."""
        return await self._get_state_persistence().list_checkpoints()

    async def prune_checkpoints(self, keep: int = 10) -> int:
        """Remove old checkpoints keeping only N most recent."""
        return await self._get_state_persistence().prune_checkpoints(keep)

    # --- P37: Quality monitoring ---

    async def start_quality_monitor(self) -> None:
        """Start background quality monitoring."""
        await self._get_multimodal_quality_monitor().start()

    async def stop_quality_monitor(self) -> None:
        """Stop background quality monitoring."""
        await self._get_multimodal_quality_monitor().stop()

    @property
    def is_quality_monitor_running(self) -> bool:
        return self._get_multimodal_quality_monitor().is_running

    async def quality_report(self) -> Dict[str, Any]:
        """Get quality report from the monitor."""
        return self._get_multimodal_quality_monitor().report()

    async def quality_trend(self) -> Dict[str, Any]:
        """Get quality trend analysis."""
        return self._get_multimodal_quality_monitor().quality_trend()

    async def quality_latest_sample(self) -> Dict[str, Any]:
        """Get the most recent quality sample."""
        return self._get_multimodal_quality_monitor().get_latest_sample()

    # --- Health ---

    async def health(self) -> Dict[str, Any]:
        """Check health of all multimodal components."""
        status: Dict[str, Any] = {"status": "healthy"}
        try:
            _ = self._get_visual_encoder()
            status["encoders"] = {"vision": True}
        except Exception as err:
            logger.debug("Vision encoder health check failed: %s", err)
            status["encoders"] = {"vision": False}
        try:
            _ = self._get_audio_encoder()
            status["encoders"]["audio"] = True
        except Exception as err:
            logger.debug("Audio encoder health check failed: %s", err)
            status["encoders"]["audio"] = False
        try:
            _ = self._get_latent_space()
            status["latent_space"] = True
        except Exception as err:
            logger.debug("Latent space health check failed: %s", err)
            status["latent_space"] = False
        try:
            # P33: Check vision pipeline health
            vp = self._get_vision_pipeline()
            if hasattr(vp, 'get_stats'):
                status["vision_pipeline"] = vp.get_stats()
        except Exception:
            logger.debug("vision pipeline health check failed", exc_info=True)
        try:
            async with self._items_lock:
                status["registered_items"] = len(self._registered_items)
        except Exception as err:
            logger.debug("Registered items count failed: %s", err)
            status["registered_items"] = 0
        # P37: Add production hardening health info
        try:
            if self._error_recovery is not None:
                status["recovery_state"] = self._error_recovery.get_recovery_state()
        except Exception:
            logger.debug("error recovery health check failed", exc_info=True)
        try:
            if self._state_persistence is not None:
                cp_list = await self._state_persistence.list_checkpoints()
                status["checkpoints"] = cp_list
        except Exception:
            logger.debug("state persistence health check failed", exc_info=True)
        try:
            if self._mm_quality_monitor is not None:
                status["quality_monitor"] = self._mm_quality_monitor.report()
        except Exception:
            logger.debug("quality monitor health check failed", exc_info=True)
        return status
