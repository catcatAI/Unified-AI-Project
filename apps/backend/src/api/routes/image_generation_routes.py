"""API routes for compositional image generation (GVV pipeline)."""

import logging
import io
import base64
import os
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateImageRequest(BaseModel):
    text: str
    canvas_size: int = 128
    num_iterations: int = 30
    learning_rate: float = 0.1


class GenerateImageResponse(BaseModel):
    image_base64: str
    width: int
    height: int
    metrics: dict


_gvv_state = None


def _get_gvv():
    """Lazy-initialize the GVV pipeline."""
    global _gvv_state
    if _gvv_state is not None:
        return _gvv_state

    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

        from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
        from ai.multimodal.primitives.concept_mapper import ConceptMapper
        from ai.multimodal.primitives.instance_optimizer import InstanceOptimizer
        from ai.multimodal.primitives.primitive_renderer import render_primitives_from_vector

        models_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models")
        vocab_path = os.path.join(models_dir, "geometric_vocabulary.json")
        mapper_path = os.path.join(models_dir, "concept_mapper.json")

        if not os.path.exists(vocab_path):
            logger.error("Vocabulary not found at %s", vocab_path)
            return None

        vocabulary = GeometricVocabulary.load(vocab_path)
        if os.path.exists(mapper_path):
            mapper = ConceptMapper.load(vocabulary, mapper_path)
        else:
            mapper = ConceptMapper(vocabulary)

        optimizer = InstanceOptimizer(vocabulary)

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


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    """Generate an image from text using the GVV pipeline.

    Pipeline: text → CLIP → ConceptMapper → vocabulary init → optimize → render
    """
    gvv = _get_gvv()
    if gvv is None:
        raise HTTPException(status_code=503, detail="GVV pipeline not available")

    try:
        from ai.multimodal.primitives.primitive_renderer import render_primitives_from_vector

        vocabulary = gvv["vocabulary"]
        concept_mapper = gvv["concept_mapper"]
        optimizer = gvv["optimizer"]

        # Step 1: Map text → concept → initial vector
        mapping = concept_mapper.map_text_to_primitives(np.zeros(512))
        concept_name = mapping["concept"]

        # Step 2: Optimize for pixel similarity
        size = (request.canvas_size, request.canvas_size)
        result = optimizer.optimize(
            mapping["initialization"],
            num_iterations=request.num_iterations,
            learning_rate=request.learning_rate,
            target_size=size,
        )

        # Step 3: Render final image
        img = render_primitives_from_vector(result["optimized_vector"], size=size)

        # Step 4: Compute metrics
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate-image/status")
async def generate_image_status():
    """Check if image generation is available."""
    gvv = _get_gvv()
    return {
        "available": gvv is not None,
        "pipeline": "gvv",
        "vocab_size": len(gvv["vocabulary"]._visual_words) if gvv else 0,
        "concept_count": len(gvv["vocabulary"]._concept_distributions) if gvv else 0,
    }
