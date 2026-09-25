"""API routes for compositional image generation (GVV pipeline + ThreeLayerVisual)."""

import base64
import io
import logging
import os

import numpy as np
from ai.multimodal.generator.gvv_generator import (
    encode_text_with_clip as _encode_text_with_clip,
    generate_image as _generate_image,
    get_gvv as _get_gvv,
    gvv_initialized as _gvv_initialized,
)
from core.utils import safe_error
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateImageRequest(BaseModel):
    text: str
    canvas_size: int = 128
    num_iterations: int = 30
    learning_rate: float = 0.008


class GenerateImageResponse(BaseModel):
    image_base64: str
    width: int
    height: int
    metrics: dict


class RecognizeImageRequest(BaseModel):
    image_base64: str


class RecognizeImageResponse(BaseModel):
    predicted_class: str
    confidence: float
    class_scores: dict


class ReconstructImageRequest(BaseModel):
    image_base64: str
    enhance: bool = True


class ReconstructImageResponse(BaseModel):
    image_base64: str
    width: int
    height: int
    metrics: dict


class InterpolateRequest(BaseModel):
    class_a: int
    class_b: int
    n_steps: int = 10
    enhance: bool = True


class InterpolateResponse(BaseModel):
    images: list
    width: int
    height: int
    metrics: dict


_three_layer_state = None


def _get_three_layer():
    """Lazy-initialize the ThreeLayerVisual model."""
    global _three_layer_state
    if _three_layer_state is not None:
        return _three_layer_state

    try:
        from ai.multimodal.three_layer_visual import ThreeLayerVisual

        models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models")
        model_dir = os.path.join(models_dir, "three_layer")

        model = ThreeLayerVisual(model_dir=model_dir)
        if model.load():
            _three_layer_state = model
            logger.info("Loaded ThreeLayerVisual model")
        else:
            logger.warning("ThreeLayerVisual model not found at %s", model_dir)
            _three_layer_state = None

        return _three_layer_state
    except Exception as e:
        logger.error("Failed to initialize ThreeLayerVisual: %s", e)
        return None


@router.post("/image/generate", response_model=GenerateImageResponse)
async def image_generate(request: GenerateImageRequest):
    """Generate an image from text using the GVV pipeline.

    Pipeline: text → CLIP → concept space → ConceptMapper → vocabulary init →
    optimize → render. The pipeline itself is owned by
    ai.multimodal.generator.gvv_generator so the chat path can reach the same
    engine (see services/handlers/image_generation_handler.py).
    """
    try:
        result = _generate_image(
            request.text,
            canvas_size=request.canvas_size,
            num_iterations=request.num_iterations,
            learning_rate=request.learning_rate,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Image generation failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=safe_error(e))

    return GenerateImageResponse(
        image_base64=result["image_base64"],
        width=result["width"],
        height=result["height"],
        metrics=result["metrics"],
    )


@router.post("/image/recognize", response_model=RecognizeImageResponse)
async def image_recognize(request: RecognizeImageRequest):
    """Recognize an image using concept space mapping.

    Pipeline: image → CLIP → concept space → classify
    """
    gvv = _get_gvv()
    if gvv is None:
        raise HTTPException(status_code=503, detail="GVV pipeline not available")

    concept_mapper = gvv["concept_mapper"]
    if concept_mapper._concept_space is None:
        raise HTTPException(status_code=503, detail="Concept space not available")

    try:
        from ai.multimodal.semantic_visual import SemanticVisualEncoder

        encoder = SemanticVisualEncoder()

        img_bytes = base64.b64decode(request.image_base64)

        clip_vec = encoder.encode(img_bytes)
        if clip_vec is None:
            raise HTTPException(status_code=400, detail="Failed to encode image with CLIP")

        concept_space = concept_mapper._concept_space
        concept_vec = concept_space.encode(clip_vec.reshape(1, -1))

        pred_idx, confidence = concept_space.predict(clip_vec.reshape(1, -1))

        sims = concept_vec @ concept_space._class_centers.T
        class_scores = {
            concept_space._class_names[i]: float(sims[0, i])
            for i in range(len(concept_space._class_names))
        }

        predicted_class = concept_space._class_names[pred_idx] if pred_idx >= 0 else "unknown"

        return RecognizeImageResponse(
            predicted_class=predicted_class,
            confidence=confidence,
            class_scores=class_scores,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Image recognition failed: %s", e)
        raise HTTPException(status_code=500, detail=safe_error(e))


@router.post("/image/reconstruct", response_model=ReconstructImageResponse)
async def image_reconstruct(request: ReconstructImageRequest):
    """Reconstruct an image using ThreeLayerVisual.

    Pipeline: image → PCA encode → decode → enhance
    """
    model = _get_three_layer()
    if model is None:
        raise HTTPException(status_code=503, detail="ThreeLayerVisual model not available")

    try:
        import time

        from PIL import Image as PILImage

        img_bytes = base64.b64decode(request.image_base64)
        pil_img = PILImage.open(io.BytesIO(img_bytes)).convert("RGB")
        pil_img = pil_img.resize((32, 32))
        img_arr = np.array(pil_img).astype(np.float32) / 255.0
        img_flat = img_arr.reshape(1, -1)

        t0 = time.time()
        recon = model.reconstruct(img_flat, enhance=request.enhance)
        recon_time = time.time() - t0

        recon_img = (recon[0].reshape(32, 32, 3) * 255).astype(np.uint8)
        pil_recon = PILImage.fromarray(recon_img).resize(pil_img.size)

        orig_resized = np.array(pil_img.resize((32, 32))).astype(np.float32) / 255.0
        mse = float(np.mean((recon[0].reshape(32, 32, 3) - orig_resized) ** 2))

        buf = io.BytesIO()
        pil_recon.save(buf, format="PNG")
        img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return ReconstructImageResponse(
            image_base64=img_base64,
            width=pil_recon.size[0],
            height=pil_recon.size[1],
            metrics={
                "mse": mse,
                "reconstruct_time": recon_time,
                "enhanced": request.enhance,
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Image reconstruction failed: %s", e)
        raise HTTPException(status_code=500, detail=safe_error(e))


@router.post("/image/interpolate", response_model=InterpolateResponse)
async def image_interpolate(request: InterpolateRequest):
    """Interpolate between two class centers using ThreeLayerVisual.

    Pipeline: class A center → class B center → n_steps interpolation
    """
    model = _get_three_layer()
    if model is None:
        raise HTTPException(status_code=503, detail="ThreeLayerVisual model not available")

    try:
        import time

        from PIL import Image as PILImage

        t0 = time.time()
        interp = model.interpolate(
            request.class_a, request.class_b, n_steps=request.n_steps, enhance=request.enhance
        )
        interp_time = time.time() - t0

        images = []
        for i in range(len(interp)):
            img_arr = (interp[i].reshape(32, 32, 3) * 255).astype(np.uint8)
            pil_img = PILImage.fromarray(img_arr)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            images.append(base64.b64encode(buf.getvalue()).decode("utf-8"))

        return InterpolateResponse(
            images=images,
            width=32,
            height=32,
            metrics={
                "class_a": request.class_a,
                "class_b": request.class_b,
                "n_steps": request.n_steps,
                "interpolate_time": interp_time,
            },
        )
    except Exception as e:
        logger.error("Interpolation failed: %s", e)
        raise HTTPException(status_code=500, detail=safe_error(e))


@router.get("/image/status")
async def image_status():
    """Check if image generation is available.

    Uses cached state only — does NOT trigger lazy initialization of
    GVV or ThreeLayerVisual. First request may show unavailable if
    models have not been initialized by a prior /generate call.
    """
    gvv = _get_gvv() if _gvv_initialized() else None
    three_layer = _get_three_layer() if _three_layer_state is not None else None
    has_concept_space = False
    if gvv:
        concept_mapper = gvv["concept_mapper"]
        has_concept_space = concept_mapper._concept_space is not None
    return {
        "gvv_available": gvv is not None,
        "three_layer_available": three_layer is not None,
        "pipeline": "gvv",
        "vocab_size": len(gvv["vocabulary"]._visual_words) if gvv else 0,
        "concept_count": len(gvv["vocabulary"]._concept_distributions) if gvv else 0,
        "concept_space": has_concept_space,
    }
