"""API routes for compositional image generation."""

import logging
import io
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateImageRequest(BaseModel):
    text: str
    canvas_size: int = 128
    temperature: float = 0.8


class GenerateImageResponse(BaseModel):
    image_base64: str
    width: int
    height: int
    metrics: dict


_generator = None
_evaluator = None


def _get_generator():
    """Lazy-initialize the image generator."""
    global _generator
    if _generator is not None:
        return _generator
    
    try:
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        
        from ai.multimodal.generator.image_generator import ImageGenerator
        from ai.multimodal.generator.sequence_generator import SequenceGenerator
        from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
        
        save_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..",
                                "data", "multimodal", "weights")
        
        gen_path = os.path.join(save_dir, "sequence_generator.json")
        enc_path = os.path.join(save_dir, "primitive_encoder.json")
        
        seq_gen = SequenceGenerator()
        prim_enc = PrimitiveEncoder()
        
        if os.path.exists(gen_path):
            seq_gen = SequenceGenerator.load(gen_path)
            logger.info("Loaded SequenceGenerator from %s", gen_path)
        if os.path.exists(enc_path):
            prim_enc = PrimitiveEncoder.load(enc_path)
            logger.info("Loaded PrimitiveEncoder from %s", enc_path)
        
        _generator = ImageGenerator(
            sequence_generator=seq_gen,
            primitive_encoder=prim_enc,
        )
        return _generator
    except Exception as e:
        logger.error("Failed to initialize ImageGenerator: %s", e)
        return None


@router.post("/generate-image", response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    """Generate an image from a text description.
    
    Uses the compositional image generation pipeline:
    text → CLIP → SequenceGenerator → PrimitiveEncoder → PIL Image
    """
    generator = _get_generator()
    if generator is None:
        raise HTTPException(status_code=503, detail="Image generator not available")
    
    try:
        size = (request.canvas_size, request.canvas_size)
        result = generator.evaluate(request.text, canvas_size=size)
        
        img = result["image"]
        metrics = result["metrics"]
        
        # Convert to base64
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
    generator = _get_generator()
    return {
        "available": generator is not None,
        "has_trained_model": generator._generator.is_trained if generator else False,
    }
