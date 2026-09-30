# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L3]
# =============================================================================
"""
GVV text→image generation — the single owner of the pipeline.

WHY this module exists: the whole pipeline (GeometricVocabulary →
ConceptMapper → ConceptSpaceMapper → InstanceOptimizer → PrimitiveRenderer)
lived inline in ``api/routes/image_generation_routes.py``. That left the chat
path with no way to reach it: an image-generation request classified as
``vision`` was dispatched to the *vision analysis* handler, so the user got
「請提供圖片路徑」 while a working generator sat behind an HTTP route nobody
from chat could call. The route and the chat handler both call this module.
"""

import base64
import io
import logging
import os
from typing import Any, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_GVV_STATE: Optional[Dict[str, Any]] = None

# The model files live in the repository-level models/ directory. The previous
# code counted parent directories (os.path.join(__file__, "..", *4, "models")),
# which resolved to apps/models — a directory that does not exist — so
# POST /api/v1/image/generate answered 503 "GVV pipeline not available" on every
# real call while its mocked tests passed. Walk up until the anchor file is found
# instead of trusting the depth.
_VOCAB_FILENAME = "geometric_vocabulary.json"


def _find_models_dir() -> Optional[str]:
    here = os.path.abspath(os.path.dirname(__file__))
    for _ in range(8):
        candidate = os.path.join(here, "models")
        if os.path.exists(os.path.join(candidate, _VOCAB_FILENAME)):
            return candidate
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent
    return None


def get_gvv() -> Optional[Dict[str, Any]]:
    """Lazy-initialize (process-wide) the GVV pipeline with concept space."""
    global _GVV_STATE
    if _GVV_STATE is not None:
        return _GVV_STATE

    try:
        from ai.multimodal.primitives.concept_mapper import ConceptMapper
        from ai.multimodal.primitives.concept_space import ConceptSpaceMapper
        from ai.multimodal.primitives.geometric_vocabulary import GeometricVocabulary
        from ai.multimodal.primitives.instance_optimizer import InstanceOptimizer

        models_dir = _find_models_dir()
        if models_dir is None:
            logger.error("models/%s not found (searched upward from %s)", _VOCAB_FILENAME, __file__)
            return None

        vocab_path = os.path.join(models_dir, "geometric_vocabulary.json")
        mapper_path = os.path.join(models_dir, "concept_mapper.json")
        concept_space_path = os.path.join(models_dir, "concept_space.json")

        vocabulary = GeometricVocabulary.load(vocab_path)
        mapper = (
            ConceptMapper.load(vocabulary, mapper_path)
            if os.path.exists(mapper_path)
            else ConceptMapper(vocabulary)
        )

        if os.path.exists(concept_space_path):
            mapper.set_concept_space(ConceptSpaceMapper.load(concept_space_path))
            logger.info("Loaded concept space mapping")
        else:
            logger.warning("Concept space not found at %s", concept_space_path)

        _GVV_STATE = {
            "vocabulary": vocabulary,
            "concept_mapper": mapper,
            "optimizer": InstanceOptimizer(vocabulary, mapper, (128, 128)),
        }
        logger.info(
            "Loaded GVV pipeline (vocab=%d words, %d concepts)",
            len(vocabulary._visual_words),
            len(vocabulary._concept_distributions),
        )
        return _GVV_STATE
    except Exception as exc:
        logger.error("Failed to initialize GVV pipeline: %s", exc, exc_info=True)
        _GVV_STATE = None
        return None


def gvv_initialized() -> bool:
    """True once the pipeline has been built (no lazy init side effect)."""
    return _GVV_STATE is not None


def encode_text_with_clip(text: str) -> np.ndarray:
    """Encode text into a 512-dim CLIP vector (zeros when CLIP is absent)."""
    try:
        from ai.multimodal.semantic_visual import SemanticVisualEncoder

        encoder = SemanticVisualEncoder()
        if not encoder.is_available:
            logger.warning("CLIP not available, using zeros")
            return np.zeros(512, dtype=np.float32)
        result = encoder.encode_text([text])
        if result is None:
            return np.zeros(512, dtype=np.float32)
        return np.asarray(result[0], dtype=np.float32)
    except Exception as exc:
        logger.warning("CLIP encoding failed: %s, using zeros", exc)
        return np.zeros(512, dtype=np.float32)


def generate_image(
    text: str,
    canvas_size: int = 128,
    num_iterations: int = 30,
    learning_rate: float = 0.008,
) -> Dict[str, Any]:
    """Generate an image from text.

    Pipeline: text → CLIP → concept space → ConceptMapper → vocabulary init →
    optimize → DrawingInstructions → PrimitiveRenderer.

    Returns ``{"image_base64", "width", "height", "metrics"}`` or raises
    ``RuntimeError`` when the pipeline is unavailable. Callers translate the
    failure; this function never returns a fake success.
    """
    gvv = get_gvv()
    if gvv is None:
        raise RuntimeError("GVV pipeline not available")

    from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
    from ai.multimodal.primitives.primitive_types import DrawingInstructions

    concept_mapper = gvv["concept_mapper"]
    optimizer = gvv["optimizer"]

    clip_vec = encode_text_with_clip(text)
    mapping = concept_mapper.map_text_to_primitives(clip_vec)
    result = optimizer.optimize_from_text(
        clip_vec,
        n_iterations=num_iterations,
        lr=learning_rate,
    )

    size = (canvas_size, canvas_size)
    instructions = DrawingInstructions.from_vector(result["vector"], size)
    image = PrimitiveRenderer(size).render(instructions)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return {
        "image_base64": base64.b64encode(buf.getvalue()).decode("utf-8"),
        "width": image.size[0],
        "height": image.size[1],
        "metrics": {
            # The optimizer returns {"vector","rendered","loss","concept","elapsed"} —
            # the previous code read result["iterations"] / result["final_loss"],
            # which do not exist, so a KeyError turned every successful generation
            # into HTTP 500 once the model path was reachable.
            "concept": result.get("concept") or mapping["concept"],
            "similarity": mapping["similarity"],
            "loss": result.get("loss"),
            "elapsed": result.get("elapsed"),
        },
    }


def render_png_bytes(image: Any) -> Tuple[bytes, str]:
    """Encode a PIL image to PNG bytes (shared by callers that persist output)."""
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue(), base64.b64encode(buf.getvalue()).decode("utf-8")
