"""
Multimodal API routes — REST endpoints for the multimodal pipeline.

P30: First layer of multimodal pipeline infrastructure.
Provides 9 REST endpoints + 1 health endpoint, analogous to chat_routes.

Endpoints:
  POST /multimodal/encode      → Encode image/audio to feature vector + latent
  POST /multimodal/decode      → Decode latent to image/audio (base64)
  POST /multimodal/compare     → Cross-modal similarity comparison
  POST /multimodal/retrieve    → RAG retrieval by latent query
  POST /multimodal/train       → Trigger training pipeline
  POST /multimodal/evaluate    → Evaluate generation quality
  POST /multimodal/generate    → Cross-modal generation (vision↔audio)
  POST /multimodal/visualize   → Latent space visualization data
  GET  /multimodal/health      → Health check for all components

ANGELA-MATRIX: L6[执行层] αβγδ [B] L4
"""

import base64
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

logger = logging.getLogger(__name__)

router = APIRouter(tags=["multimodal"])

_SERVICE = None


def _get_service():
    global _SERVICE
    if _SERVICE is None:
        try:
            from services.multimodal_service import MultimodalService
            _SERVICE = MultimodalService()
        except Exception as e:
            logger.warning("MultimodalService not available: %s", e)
    return _SERVICE


def set_service(service) -> None:
    global _SERVICE
    _SERVICE = service


# --- Encode ---

@router.post("/multimodal/encode")
async def encode_endpoint(
    file: UploadFile = File(...),
    modality: str = Form("vision"),
    item_id: Optional[str] = Form(None),
):
    """Encode an uploaded image or audio file into feature vectors.

    Accepts multipart upload. Returns feature_vector, latent, item_id, dim, time_ms.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.encode(data, modality, item_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


# --- Decode ---

@router.post("/multimodal/decode")
async def decode_endpoint(
    item_id: str = Form(...),
    modality: str = Form("vision"),
    output_format: str = Form("base64"),
):
    """Decode a previously encoded item's latent back to image/audio.

    Returns base64-encoded data or raw format.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.decode(item_id, modality, output_format)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


# --- Compare ---

@router.post("/multimodal/compare")
async def compare_endpoint(
    item_a: str = Form(...),
    item_b: str = Form(...),
):
    """Compare two encoded items via cross-modal similarity.

    Returns similarity score [0,1], modalities, and attention weights.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.compare(item_a, item_b)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


# --- Retrieve ---

@router.post("/multimodal/retrieve")
async def retrieve_endpoint(
    query_id: str = Form(...),
    top_k: int = Form(5),
    modality_filter: Optional[str] = Form(None),
):
    """Retrieve top-k similar items for a query item via latent search.

    Returns list of {key, score, modality, metadata}.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    results = await svc.retrieve(query_id, top_k, modality_filter)
    return {"success": True, "results": results, "count": len(results)}


# --- Train ---

@router.post("/multimodal/train")
async def train_endpoint(
    mode: str = Form("full"),
    epochs: int = Form(5),
    lr: float = Form(0.01),
    use_real: bool = Form(False),
):
    """Trigger training pipeline.

    Modes: 'full' (contrastive + reconstruction), 'contrastive', 'recon'.
    Returns status and final loss metrics.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.train(mode, epochs, lr, use_real)
    return {"success": result.get("status") == "completed", **result}


# --- Evaluate ---

@router.post("/multimodal/evaluate")
async def evaluate_endpoint(
    item_id: Optional[str] = Form(None),
    modality: str = Form("vision"),
    n_samples: int = Form(5),
):
    """Evaluate generation quality for an item or synthetic samples.

    If item_id is provided, evaluates on that item; otherwise uses synthetic.
    Returns quality metrics (SSIM/PSNR/SNR).
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.evaluate(item_id, modality, n_samples)
    return {"success": True, **result}


# --- Generate (cross-modal) ---

@router.post("/multimodal/generate")
async def generate_endpoint(
    source_item_id: str = Form(...),
    target_modality: str = Form("audio"),
):
    """Cross-modal generation: transform source item into target modality.

    E.g., vision→audio (image → ambient sound) or audio→vision (sound → image).
    Returns base64-encoded generated data.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.generate(source_item_id, target_modality)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


# Module-level CrossModalRouter singleton (preserves cache + rate limiting)
_ROUTER = None


def _get_router():
    global _ROUTER
    if _ROUTER is None:
        from services.cross_modal_router import CrossModalRouter
        _ROUTER = CrossModalRouter()
    return _ROUTER


# --- Cross-modal inference ---

@router.post("/multimodal/cross-infer")
async def cross_infer_endpoint(
    source_modality: str = Form("vision"),
    mode: str = Form("auto"),
    file: Optional[UploadFile] = File(None),
    item_id: Optional[str] = Form(None),
):
    """Cross-modal inference via CrossModalRouter.

    Routes the request to the correct pipeline (vision/audio/cross)
    with confidence scoring and fallback chain.

    Args:
        source_modality: "vision", "audio", or "cross"
        mode: "auto", "encode", "pipeline", "analyze", "compare", "generate"
        file: Optional uploaded file
        item_id: Optional item identifier

    Returns routed result with pipeline name and confidence.
    """
    router_svc = _get_router()
    data = b""
    if file:
        data = await file.read()
    if not data and not item_id:
        # If no data and no item_id, still can do cross-modal comparison
        if source_modality == "cross" and mode in ("auto", "compare"):
            result = await router_svc.route("cross", b"", mode)
            return {"success": True, **result}
        raise HTTPException(status_code=400, detail="No file data or item_id provided")
    result = await router_svc.route(source_modality, data, mode, item_id)
    if result.get("error"):
        return {"success": False, **result}
    return {"success": True, **result}


# --- Quality dashboard ---

@router.get("/multimodal/quality/dashboard")
async def quality_dashboard_endpoint():
    """Get integrated quality dashboard for all multimodal pipelines.

    Returns vision_summary, audio_summary, and overall health assessment.
    """
    from services.cross_modal_quality import CrossModalQualityDashboard
    dashboard = CrossModalQualityDashboard()
    dash_report = dashboard.dashboard_simple()
    return {"success": True, **dash_report}


# --- Visualize ---

@router.post("/multimodal/visualize")
async def visualize_endpoint(
    item_ids: Optional[str] = Form(None),
    n_latents: int = Form(20),
):
    """Generate 2D projection coordinates of latent space for visualization.

    Accepts a list of item IDs (JSON array) or n_latents random samples.
    Returns 2D coordinates with labels for frontend rendering.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    items = await svc.list_items()
    registered = items.get("items", {})
    points = []
    import numpy as np

    if item_ids:
        try:
            ids = json.loads(item_ids)
        except json.JSONDecodeError:
            ids = []
        for iid in ids:
            item = await svc.get_item(iid)
            if item and "latent" in item:
                latent = np.array(item["latent"], dtype=np.float32)
                points.append({
                    "item_id": iid,
                    "modality": item["modality"],
                    "x": float(latent[0]),
                    "y": float(latent[1]) if len(latent) > 1 else 0.0,
                })
    else:
        sample_keys = list(registered.keys())[:n_latents]
        for iid in sample_keys:
            item = await svc.get_item(iid)
            if item and "latent" in item:
                latent = np.array(item["latent"], dtype=np.float32)
                points.append({
                    "item_id": iid,
                    "modality": item["modality"],
                    "x": float(latent[0]),
                    "y": float(latent[1]) if len(latent) > 1 else 0.0,
                })
    return {"success": True, "points": points, "count": len(points)}


# --- List items ---

@router.get("/multimodal/items")
async def list_items_endpoint():
    """List all registered multimodal items with metadata.

    Returns dict of {item_id: {modality, timestamp}} and count.
    Used by frontend for rendering item dropdowns and lists.
    """
    svc = _get_service()
    if svc is None:
        return {"success": False, "items": {}, "count": 0}
    items = await svc.list_items()
    return {"success": True, **items}


# --- CML (Continuous Multimodal Learning) ---

@router.get("/multimodal/cml/stats")
async def cml_stats_endpoint():
    """Get CML statistics (total encodes, training runs, buffer size)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    stats = await svc.cml_stats()
    return {"success": True, **stats}


@router.get("/multimodal/cml/trend")
async def cml_trend_endpoint():
    """Get CML quality trend assessment."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    trend = await svc.cml_trend()
    return {"success": True, **trend}


@router.post("/multimodal/cml/train")
async def cml_train_endpoint(epochs: int = Form(3)):
    """Manually trigger CML micro-training cycle."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.cml_micro_train(epochs)
    return {"success": result.get("status") == "completed", **result}


# --- Memory store ---

@router.post("/multimodal/memory/store")
async def memory_store_endpoint(item_id: str = Form(...)):
    """Store a registered item into multimodal memory."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    entry_id = await svc.memory_store(item_id)
    if entry_id is None:
        raise HTTPException(status_code=400, detail=f"Item not found: {item_id}")
    return {"success": True, "entry_id": entry_id}


@router.post("/multimodal/memory/search")
async def memory_search_endpoint(
    query_item_id: str = Form(...),
    top_k: int = Form(5),
    modality_filter: Optional[str] = Form(None),
):
    """Search memory by latent similarity to a registered item."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "results": [], "count": 0}
    results = await svc.memory_search(query_item_id, top_k, modality_filter)
    return {"success": True, "results": results, "count": len(results)}


@router.post("/multimodal/memory/recall")
async def memory_recall_endpoint(hours: float = Form(24)):
    """Recall entries from memory within a time window."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "entries": [], "count": 0}
    entries = await svc.memory_recall(hours=hours)
    return {"success": True, "entries": entries, "count": len(entries)}


@router.get("/multimodal/memory/stats")
async def memory_stats_endpoint():
    """Get multimodal memory statistics."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    stats = await svc.memory_stats()
    return {"success": True, **stats}


# --- P39: Vision caption ---

@router.post("/multimodal/caption")
async def caption_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    language: str = Form("zh"),
    preferred_backend: Optional[str] = Form(None),
):
    """Generate a semantic caption for an uploaded image using LLM Vision API (P39).

    Uses Gemini Pro Vision or GPT-4 Vision to describe the image content.
    Returns semantic description (not just pixel stats).
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.caption(data, prompt, language, preferred_backend)
    if result.get("error"):
        return {"success": False, **result}
    return {"success": True, **result}


@router.post("/multimodal/caption-pipeline")
async def caption_pipeline_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    language: str = Form("zh"),
):
    """Run full vision pipeline with semantic caption (P39).

    Combines pixel-level features (VisualEncoder -> latent -> decode -> SSIM)
    with LLM Vision semantic description. One endpoint for the complete pipeline.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.caption_pipeline(data, prompt, language)
    return {"success": True, **result}


@router.get("/multimodal/caption/status")
async def caption_status_endpoint():
    """Check VisionCaptionService availability and configured backends."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "available": False, "backends": []}
    status = await svc.caption_status()
    return {"success": True, **status}


# --- P40: Audio caption ---

@router.post("/multimodal/audio-caption")
async def audio_caption_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    language: str = Form("zh"),
    preferred_backend: Optional[str] = Form(None),
    mode: str = Form("auto"),
):
    """Generate a semantic caption for uploaded audio using LLM Audio API (P40).

    Uses Gemini Audio (multimodal) or OpenAI Whisper to describe/transcribe
    audio content. Returns semantic description, speech transcription, and metadata.

    Modes:
      - "auto": Auto-detect and describe the audio
      - "transcribe": Speech-to-text transcription
      - "describe": Full semantic description of audio content
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.audio_caption(data, prompt, language, preferred_backend, mode)
    if result.get("error"):
        return {"success": False, **result}
    return {"success": True, **result}


@router.post("/multimodal/audio-caption-pipeline")
async def audio_caption_pipeline_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    language: str = Form("zh"),
    mode: str = Form("auto"),
):
    """Run full audio pipeline with semantic caption (P40).

    Combines spectral features (AudioSpectralEncoder -> latent -> decode -> SNR)
    with LLM Audio semantic description/transcription.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.audio_caption_pipeline(data, prompt, language, mode)
    return {"success": True, **result}


@router.get("/multimodal/audio-caption/status")
async def audio_caption_status_endpoint():
    """Check AudioCaptionService availability and configured backends (P40)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "available": False, "backends": []}
    status = await svc.audio_caption_status()
    return {"success": True, **status}
async def caption_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    language: str = Form("zh"),
    preferred_backend: Optional[str] = Form(None),
):
    """Generate a semantic caption for an uploaded image using LLM Vision API (P39).

    Uses Gemini Pro Vision or GPT-4 Vision to describe the image content.
    Returns semantic description (not just pixel stats).
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.caption(data, prompt, language, preferred_backend)
    if result.get("error"):
        return {"success": False, **result}
    return {"success": True, **result}


@router.post("/multimodal/caption-pipeline")
async def caption_pipeline_endpoint(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    language: str = Form("zh"),
):
    """Run full vision pipeline with semantic caption (P39).

    Combines pixel-level features (VisualEncoder -> latent -> decode -> SSIM)
    with LLM Vision semantic description. One endpoint for the complete pipeline.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.caption_pipeline(data, prompt, language)
    return {"success": True, **result}


@router.get("/multimodal/caption/status")
async def caption_status_endpoint():
    """Check VisionCaptionService availability and configured backends."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "available": False, "backends": []}
    status = await svc.caption_status()
    return {"success": True, **status}


# --- Clear items ---

@router.post("/multimodal/clear")
async def clear_items_endpoint():
    """Clear all registered items and reset latent space.

    Returns status confirmation.
    """
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.clear_items()
    return {"success": True, **result}


# --- Health (P37 enhanced) ---

@router.get("/multimodal/health")
async def multimodal_health():
    """Enhanced health check for all multimodal components (P37).

    Returns status of encoders, decoders, latent space, registered items,
    recovery state, checkpoints, and quality monitor.
    """
    svc = _get_service()
    if svc is None:
        return {"success": False, "status": "unavailable", "error": "MultimodalService not loaded"}
    health = await svc.health()
    return {"success": True, **health}


# --- P37: Error recovery ---

@router.get("/multimodal/recovery/state")
async def recovery_state_endpoint():
    """Get error recovery state (retry counts, crisis levels, last success timestamps)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    state = await svc.get_recovery_state()
    return {"success": True, **state}


@router.post("/multimodal/recovery/reset")
async def recovery_reset_endpoint():
    """Reset all error recovery counters."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    await svc.reset_recovery_counters()
    return {"success": True, "status": "reset"}


@router.post("/multimodal/encode-with-retry")
async def encode_with_retry_endpoint(
    file: UploadFile = File(...),
    modality: str = Form("vision"),
    item_id: Optional[str] = Form(None),
):
    """Encode with automatic retry on failure (P37)."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file data")
    result = await svc.encode_with_retry(data, modality, item_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, **result}


@router.post("/multimodal/decode-with-fallback")
async def decode_with_fallback_endpoint(
    item_id: str = Form(...),
    modality: str = Form("vision"),
    output_format: str = Form("base64"),
):
    """Decode with text fallback on failure (P37)."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.decode_with_fallback(item_id, modality, output_format)
    return {"success": True, **result}


@router.post("/multimodal/train-with-checkpoint")
async def train_with_checkpoint_endpoint(
    mode: str = Form("full"),
    epochs: int = Form(5),
    lr: float = Form(0.01),
    use_real: bool = Form(False),
    checkpoint_label: Optional[str] = Form(None),
):
    """Train with automatic pre-training checkpoint (P37)."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.train_with_checkpoint(mode, epochs, lr, use_real, checkpoint_label)
    return {"success": result.get("status") == "completed", **result}


# --- P37: State persistence ---

@router.post("/multimodal/checkpoint/save")
async def checkpoint_save_endpoint(label: Optional[str] = Form(None)):
    """Save a checkpoint of multimodal state."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.save_checkpoint(label)
    return {"success": result.get("status") == "saved", **result}


@router.post("/multimodal/checkpoint/load")
async def checkpoint_load_endpoint(label: str = Form(...)):
    """Load a checkpoint by label."""
    svc = _get_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="MultimodalService not available")
    result = await svc.load_checkpoint(label)
    return {"success": result.get("status") == "loaded", **result}


@router.get("/multimodal/checkpoints")
async def checkpoints_list_endpoint():
    """List all available checkpoints."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "checkpoints": [], "count": 0}
    result = await svc.list_checkpoints()
    return {"success": True, **result}


# --- P37: Quality monitoring ---

@router.get("/multimodal/quality/report")
async def quality_report_endpoint():
    """Get quality report from the background monitor (P37)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    report = await svc.quality_report()
    return {"success": True, **report}


@router.get("/multimodal/quality/trend")
async def quality_trend_endpoint():
    """Get quality trend analysis (P37)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    trend = await svc.quality_trend()
    return {"success": True, **trend}


@router.get("/multimodal/quality/latest")
async def quality_latest_endpoint():
    """Get the most recent quality sample (P37)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    sample = await svc.quality_latest_sample()
    return {"success": True, **sample}


@router.post("/multimodal/quality/start")
async def quality_start_endpoint():
    """Start background quality monitoring (P37)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    await svc.start_quality_monitor()
    return {"success": True, "status": "started"}


@router.post("/multimodal/quality/stop")
async def quality_stop_endpoint():
    """Stop background quality monitoring (P37)."""
    svc = _get_service()
    if svc is None:
        return {"success": False, "error": "MultimodalService not available"}
    await svc.stop_quality_monitor()
    return {"success": True, "status": "stopped"}
