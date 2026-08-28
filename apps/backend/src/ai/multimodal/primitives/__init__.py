"""Primitives package for compositional image generation.

Shared infrastructure (used by both old and GVV architecture):
- primitive_types: Point, Line, Plane, Circle, Arc, DrawingInstructions
- primitive_renderer: PIL-based rendering
- primitive_encoder: encode/decode DrawingInstructions to embeddings
- differentiable_renderer: numpy soft rasterizer (for optimization)

GVV architecture (correct):
- geometric_vocabulary: visual words + concept distributions
- concept_mapper: CLIP text → concept → primitive distribution
- instance_optimizer: pixel-level parameter optimization
- vocabulary_expander: residual analysis → new primitive types
"""

from .concept_mapper import ConceptMapper
from .differentiable_renderer import DifferentiableRenderer

# GVV architecture
from .geometric_vocabulary import GeometricVocabulary
from .instance_optimizer import InstanceOptimizer
from .primitive_encoder import PrimitiveEncoder
from .primitive_renderer import PrimitiveRenderer

# Shared infrastructure
from .primitive_types import Arc, Circle, DrawingInstructions, Line, Plane, Point
from .vocabulary_expander import VocabularyExpander

__all__ = [
    # Shared
    "Point",
    "Line",
    "Plane",
    "Circle",
    "Arc",
    "DrawingInstructions",
    "PrimitiveRenderer",
    "PrimitiveEncoder",
    "DifferentiableRenderer",
    # GVV
    "GeometricVocabulary",
    "ConceptMapper",
    "InstanceOptimizer",
    "VocabularyExpander",
]
