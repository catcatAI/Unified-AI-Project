"""Primitives package for compositional image generation."""

from .primitive_types import Point, Line, Plane, DrawingInstructions
from .primitive_renderer import PrimitiveRenderer
from .primitive_library import PrimitiveLibrary
from .primitive_encoder import PrimitiveEncoder

__all__ = [
    "Point",
    "Line", 
    "Plane",
    "DrawingInstructions",
    "PrimitiveRenderer",
    "PrimitiveLibrary",
    "PrimitiveEncoder",
]
