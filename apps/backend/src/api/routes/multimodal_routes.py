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


# --- Health ---

@router.get("/multimodal/health")
async def multimodal_health():
    """Health check for all multimodal components.
    Returns status of encoders, decoders, latent space, and registered items.
    """
    svc = _get_service()
    if svc is None:
        return {"success": False, "status": "unavailable", "error": "MultimodalService not loaded"}
    health = await svc.health()
    return {"success": True, **health}
