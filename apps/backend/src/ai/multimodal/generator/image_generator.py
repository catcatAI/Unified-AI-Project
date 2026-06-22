"""End-to-end image generation pipeline.

Takes text → CLIP → SequenceGenerator → PrimitiveEncoder → PrimitiveRenderer → Image.
"""

import logging
from typing import List, Optional

import numpy as np
from PIL import Image

from ..primitives.primitive_encoder import PrimitiveEncoder
from ..primitives.primitive_renderer import PrimitiveRenderer
from .sequence_generator import SequenceGenerator

logger = logging.getLogger(__name__)


class ImageGenerator:
    """End-to-end text → image generation using compositional primitives.
    
    Pipeline:
        text → CLIP encode → SequenceGenerator → PrimitiveEncoder.decode()
        → DrawingInstructions → PrimitiveRenderer → PIL Image
    """
    
    def __init__(self, semantic_encoder=None,
                 sequence_generator: Optional[SequenceGenerator] = None,
                 primitive_encoder: Optional[PrimitiveEncoder] = None,
                 renderer: Optional[PrimitiveRenderer] = None):
        """Initialize image generator.
        
        Args:
            semantic_encoder: SemanticVisualEncoder for text→CLIP encoding
            sequence_generator: Trained SequenceGenerator
            primitive_encoder: Trained PrimitiveEncoder
            renderer: PrimitiveRenderer for drawing
        """
        self._encoder = semantic_encoder
        self._generator = sequence_generator or SequenceGenerator()
        self._prim_encoder = primitive_encoder or PrimitiveEncoder()
        self._renderer = renderer or PrimitiveRenderer()
    
    def generate_from_text(self, text: str, temperature: float = 0.8,
                           canvas_size: tuple = (128, 128)) -> Image.Image:
        """Generate image from text description.
        
        Args:
            text: Text description (e.g., "a red circle")
            temperature: Sampling temperature
            canvas_size: Output image size
            
        Returns:
            Generated PIL Image
        """
        # Step 1: Encode text with CLIP
        clip_emb = self._encode_text(text)
        
        # Step 2: Generate primitive sequence
        return self.generate_from_embedding(clip_emb, temperature, canvas_size)
    
    def generate_from_embedding(self, clip_embedding: np.ndarray,
                                temperature: float = 0.8,
                                canvas_size: tuple = (128, 128)) -> Image.Image:
        """Generate image from CLIP embedding.
        
        Args:
            clip_embedding: (512,) CLIP embedding
            temperature: Sampling temperature
            canvas_size: Output image size
            
        Returns:
            Generated PIL Image
        """
        # Generate primitive sequence
        primitives = self._generator.generate(clip_embedding, temperature)
        
        if not primitives:
            # Fallback: return blank image
            return Image.new("RGB", canvas_size, (200, 200, 200))
        
        # Use the first primitive embedding to decode
        # (for simple single-primitive generation)
        prim_emb = primitives[0]
        
        # Decode to DrawingInstructions
        instructions = self._prim_encoder.decode(prim_emb, canvas_size)
        
        # Render to image
        renderer = PrimitiveRenderer(canvas_size)
        return renderer.render(instructions)
    
    def generate_multi_primitives(self, text: str, temperature: float = 0.8,
                                   canvas_size: tuple = (128, 128)) -> Image.Image:
        """Generate image using multiple primitives from sequence.
        
        Each primitive in the sequence is rendered as a separate layer
        on the canvas.
        
        Args:
            text: Text description
            temperature: Sampling temperature
            canvas_size: Output image size
            
        Returns:
            Generated PIL Image
        """
        clip_emb = self._encode_text(text)
        
        primitives = self._generator.generate(clip_emb, temperature)
        
        if not primitives:
            return Image.new("RGB", canvas_size, (200, 200, 200))
        
        # Start with background
        from ..primitives.primitive_types import DrawingInstructions
        canvas = Image.new("RGB", canvas_size, (255, 255, 255))
        
        renderer = PrimitiveRenderer(canvas_size)
        
        for prim_emb in primitives:
            instructions = self._prim_encoder.decode(prim_emb, canvas_size)
            layer = renderer.render(instructions)
            # Composite onto canvas
            canvas = Image.alpha_composite(
                canvas.convert("RGBA"), layer.convert("RGBA")
            ).convert("RGB")
        
        return canvas
    
    def generate_variations(self, text: str, n_variations: int = 4,
                            canvas_size: tuple = (128, 128)) -> List[Image.Image]:
        """Generate multiple variations of the same text.
        
        Args:
            text: Text description
            n_variations: Number of variations to generate
            canvas_size: Output image size
            
        Returns:
            List of generated PIL Images
        """
        clip_emb = self._encode_text(text)
        
        variations = []
        for _ in range(n_variations):
            primitives = self._generator.generate(clip_emb, temperature=1.0)
            if primitives:
                prim_emb = primitives[0]
                instructions = self._prim_encoder.decode(prim_emb, canvas_size)
                img = self._renderer.render(instructions)
                variations.append(img)
            else:
                variations.append(Image.new("RGB", canvas_size, (200, 200, 200)))
        
        return variations
    
    def _encode_text(self, text: str) -> np.ndarray:
        """Encode text with CLIP.
        
        Returns:
            (512,) CLIP embedding
        """
        if self._encoder is not None:
            embs = self._encoder.encode_text([text])
            if embs is not None and len(embs) > 0:
                return embs[0]
        
        # Fallback: random embedding (for testing without CLIP)
        rng = np.random.default_rng(hash(text) % (2**31))
        vec = rng.normal(0, 1, 512).astype(np.float32)
        return vec / (np.linalg.norm(vec) + 1e-8)
