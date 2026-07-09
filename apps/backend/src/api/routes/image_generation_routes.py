"""API routes for compositional image generation (GVV pipeline + ThreeLayerVisual)."""

import base64
import io
import logging
import os
import warnings
from typing import Optional

import numpy as np
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


_gvv_state = None
_three_layer_state = None


def _get_gvv():
    """Lazy-initialize the GVV pipeline with concept space."""
    global _gvv_state
    if _gvv_state is not None:
        return _gvv_state

    try:
        from ai.multimodal.primitives.concept_mapper import ConceptMapper
        from ai.multimodal.primitives.concept_space import ConceptSpaceMapper
        from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
        from ai.multimodal.primitives.instance_optimizer import InstanceOptimizer

        models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models")
        vocab_path = os.path.join(models_dir, "geometric_vocabulary.json")
        mapper_path = os.path.join(models_dir, "concept_mapper.json")
        concept_space_path = os.path.join(models_dir, "concept_space.json")

        if not os.path.exists(vocab_path):
            logger.error("Vocabulary not found at %s", vocab_path)
            return None

        vocabulary = GeometricVocabulary.load(vocab_path)
        if os.path.exists(mapper_path):
            mapper = ConceptMapper.load(vocabulary, mapper_path)
        else:
            mapper = ConceptMapper(vocabulary)

        # Load concept space if available
        if os.path.exists(concept_space_path):
            concept_space = ConceptSpaceMapper.load(concept_space_path)
            mapper.set_concept_space(concept_space)
            logger.info("Loaded concept space mapping")
        else:
            logger.warning("Concept space not found at %s", concept_space_path)

        # Fix: InstanceOptimizer requires (vocabulary, concept_mapper, canvas_size)
        optimizer = InstanceOptimizer(vocabulary, mapper, (128, 128))

        _gvv_state = {
            "vocabulary": vocabulary,
            "concept_mapper": mapper,
            "optimizer": optimizer,
        }
        logger.info("Loaded GVV pipeline (vocab=%d words, %d concepts)",
                     len(vocabulary._visual_words), len(vocabulary._concept_distributions))
        return _gvv_state
    except Exception as e:
        logger.error("Failed to initialize GVV pipeline: %s", e)
        return None


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


def _encode_text_with_clip(text: str) -> np.ndarray:
    """Encode text using CLIP. Returns 512-dim vector."""
    try:
        from ai.multimodal.semantic_visual import SemanticVisualEncoder
        encoder = SemanticVisualEncoder()
        if not encoder.is_available:
            logger.warning("CLIP not available, using zeros")
            return np.zeros(512, dtype=np.float32)
        result = encoder.encode_text([text])
        if result is None:
            return np.zeros(512, dtype=np.float32)
        return result[0].astype(np.float32)
    except Exception as e:
        logger.warning("CLIP encoding failed: %s, using zeros", e)
        return np.zeros(512, dtype=np.float32)


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    """Generate an image from text using the GVV pipeline.

    ⚠️ DEPRECATED: Use POST /image/generate instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.

    Pipeline: text → CLIP → concept space → ConceptMapper → vocabulary init → optimize → render
    """
    warnings.warn("POST /generate-image is deprecated, use POST /image/generate", DeprecationWarning, stacklevel=2)
    gvv = _get_gvv()
    if gvv is None:
        raise HTTPException(status_code=503, detail="GVV pipeline not available")

    try:
        from ai.multimodal.primitives.primitive_renderer import render_primitives_from_vector

        vocabulary = gvv["vocabulary"]
        concept_mapper = gvv["concept_mapper"]
        optimizer = gvv["optimizer"]

        # Step 1: Encode text with CLIP
        clip_vec = _encode_text_with_clip(request.text)

        # Step 2: Map text → concept → initial vector
        mapping = concept_mapper.map_text_to_primitives(clip_vec)
        concept_name = mapping["concept"]

        # Step 3: Optimize for pixel similarity
        # Fix: Use optimize_from_text instead of optimize
        result = optimizer.optimize_from_text(
            clip_vec,
            n_iterations=request.num_iterations,
            lr=request.learning_rate,
        )

        # Step 4: Render final image
        size = (request.canvas_size, request.canvas_size)
        img = render_primitives_from_vector(result["optimized_vector"], size=size)

        # Step 5: Compute metrics
        metrics = {
            "concept": concept_name,
            "similarity": mapping["similarity"],
            "iterations": result["iterations"],
            "final_loss": result["final_loss"],
        }

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        return GenerateImageResponse(
            image_base64=img_base64,
            width=img.size[0],
            height=img.size[1],
            metrics=metrics,
        )
    except Exception as e:
        logger.error("Image generation failed: %s", e)
        raise HTTPException(status_code=500, detail=safe_error(e))


@router.post("/recognize-image", response_model=RecognizeImageResponse)
async def recognize_image(request: RecognizeImageRequest):
    """Recognize an image using concept space mapping.

    ⚠️ DEPRECATED: Use POST /image/recognize instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.

    Pipeline: image → CLIP → concept space → classify
    """
    warnings.warn("POST /recognize-image is deprecated, use POST /image/recognize", DeprecationWarning, stacklevel=2)
    gvv = _get_gvv()
    if gvv is None:
        raise HTTPException(status_code=503, detail="GVV pipeline not available")

    concept_mapper = gvv["concept_mapper"]
    if concept_mapper._concept_space is None:
        raise HTTPException(status_code=503, detail="Concept space not available")

    try:
        from ai.multimodal.semantic_visual import SemanticVisualEncoder

        encoder = SemanticVisualEncoder()

        # Decode image
        img_bytes = base64.b64decode(request.image_base64)

        # Encode with CLIP
        clip_vec = encoder.encode(img_bytes)
        if clip_vec is None:
            raise HTTPException(status_code=400, detail="Failed to encode image with CLIP")

        # Map to concept space
        concept_space = concept_mapper._concept_space
        concept_vec = concept_space.encode(clip_vec.reshape(1, -1))

        # Classify
        pred_idx, confidence = concept_space.predict(clip_vec.reshape(1, -1))

        # Get class scores
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


@router.post("/reconstruct-image", response_model=ReconstructImageResponse)
async def reconstruct_image(request: ReconstructImageRequest):
    """Reconstruct an image using ThreeLayerVisual.

    ⚠️ DEPRECATED: Use POST /image/reconstruct instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.

    Pipeline: image → PCA encode → decode → enhance
    """
    warnings.warn("POST /reconstruct-image is deprecated, use POST /image/reconstruct", DeprecationWarning, stacklevel=2)
    model = _get_three_layer()
    if model is None:
        raise HTTPException(status_code=503, detail="ThreeLayerVisual model not available")

    try:
        from PIL import Image as PILImage

        # Decode image
        img_bytes = base64.b64decode(request.image_base64)
        pil_img = PILImage.open(io.BytesIO(img_bytes)).convert("RGB")
        pil_img = pil_img.resize((32, 32))
        img_arr = np.array(pil_img).astype(np.float32) / 255.0
        img_flat = img_arr.reshape(1, -1)

        # Reconstruct
        import time
        t0 = time.time()
        recon = model.reconstruct(img_flat, enhance=request.enhance)
        recon_time = time.time() - t0

        # Convert back to PIL
        recon_img = (recon[0].reshape(32, 32, 3) * 255).astype(np.uint8)
        pil_recon = PILImage.fromarray(recon_img).resize(pil_img.size)

        # Compute MSE
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


@router.post("/interpolate-classes", response_model=InterpolateResponse)
async def interpolate_classes(request: InterpolateRequest):
    """Interpolate between two class centers using ThreeLayerVisual.

    ⚠️ DEPRECATED: Use POST /image/interpolate instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.

    Pipeline: class A center → class B center → n_steps interpolation
    """
    warnings.warn("POST /interpolate-classes is deprecated, use POST /image/interpolate", DeprecationWarning, stacklevel=2)
    model = _get_three_layer()
    if model is None:
        raise HTTPException(status_code=503, detail="ThreeLayerVisual model not available")

    try:
        # Interpolate
        import time

        from PIL import Image as PILImage
        t0 = time.time()
        interp = model.interpolate(request.class_a, request.class_b, n_steps=request.n_steps,
                                   enhance=request.enhance)
        interp_time = time.time() - t0

        # Convert to base64
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

@router.get("/generate-image/status")
async def generate_image_status():
    """Check if image generation is available.

    ⚠️ DEPRECATED: Use GET /image/status instead.
    This endpoint is kept for backward compatibility and will be removed in a future release.
    """
    warnings.warn("GET /generate-image/status is deprecated, use GET /image/status", DeprecationWarning, stacklevel=2)
    return await image_status()


# =============================================================================
# New standardized image routes (replacing deprecated /generate-image etc.)
# =============================================================================


@router.post("/image/generate", response_model=GenerateImageResponse)
async def image_generate(request: GenerateImageRequest):
    """Generate an image from text using the GVV pipeline.

    Pipeline: text → CLIP → concept space → ConceptMapper → vocabulary init → optimize → render
    """
    return await generate_image(request)


@router.post("/image/recognize", response_model=RecognizeImageResponse)
async def image_recognize(request: RecognizeImageRequest):
    """Recognize an image using concept space mapping.

    Pipeline: image → CLIP → concept space → classify
    """
    return await recognize_image(request)


@router.post("/image/reconstruct", response_model=ReconstructImageResponse)
async def image_reconstruct(request: ReconstructImageRequest):
    """Reconstruct an image using ThreeLayerVisual.

    Pipeline: image → PCA encode → decode → enhance
    """
    return await reconstruct_image(request)


@router.post("/image/interpolate", response_model=InterpolateResponse)
async def image_interpolate(request: InterpolateRequest):
    """Interpolate between two class centers using ThreeLayerVisual.

    Pipeline: class A center → class B center → n_steps interpolation
    """
    return await interpolate_classes(request)


@router.get("/image/status")
async def image_status():
    """Check if image generation is available (standardized endpoint)."""
    gvv = _get_gvv()
    three_layer = _get_three_layer()
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
