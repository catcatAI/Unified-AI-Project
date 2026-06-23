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

# Shared infrastructure
from .primitive_types import Point, Line, Plane, Circle, Arc, DrawingInstructions
from .primitive_renderer import PrimitiveRenderer
from .primitive_encoder import PrimitiveEncoder
from .differentiable_renderer import DifferentiableRenderer

# GVV architecture
from .geometric_vocabulary import GeometricVocabulary
from .concept_mapper import ConceptMapper
from .instance_optimizer import InstanceOptimizer
from .vocabulary_expander import VocabularyExpander

__all__ = [
    # Shared
    "Point", "Line", "Plane", "Circle", "Arc",
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
