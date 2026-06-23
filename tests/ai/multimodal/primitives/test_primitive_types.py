"""Tests for primitive type definitions."""

import numpy as np
import pytest

from ai.multimodal.primitives.primitive_types import (
    Point, Line, Plane, DrawingInstructions
)


class TestPoint:
    def test_create_point(self):
        p = Point(0.5, 0.5, (255, 0, 0), 0.1)
        assert p.x == 0.5
        assert p.y == 0.5
        assert p.color == (255, 0, 0)
        assert p.size == 0.1
    
    def test_point_clamps_values(self):
        p = Point(1.5, -0.5, (300, -10, 128), 1.5)
        assert p.x == 1.0
        assert p.y == 0.0
        assert p.color == (255, 0, 128)
        assert p.size == 1.0


class TestLine:
    def test_create_line(self):
        start = Point(0.0, 0.0, (0, 0, 0), 0.0)
        end = Point(1.0, 1.0, (0, 0, 0), 0.0)
        line = Line(start, end, 0.05, (0, 255, 0))
        assert line.start == start
        assert line.end == end
        assert line.width == 0.05
        assert line.color == (0, 255, 0)


class TestPlane:
    def test_create_plane(self):
        points = [
            Point(0.0, 0.0, (0, 0, 0), 0.0),
            Point(1.0, 0.0, (0, 0, 0), 0.0),
            Point(1.0, 1.0, (0, 0, 0), 0.0),
            Point(0.0, 1.0, (0, 0, 0), 0.0),
        ]
        plane = Plane(points, (0, 0, 255), (0, 0, 0), 0.02)
        assert len(plane.points) == 4
        assert plane.fill_color == (0, 0, 255)
        assert plane.outline_color == (0, 0, 0)
        assert plane.outline_width == 0.02


class TestDrawingInstructions:
    def test_empty_instructions(self):
        instr = DrawingInstructions()
        assert len(instr.points) == 0
        assert len(instr.lines) == 0
        assert len(instr.planes) == 0
        assert instr.background_color == (255, 255, 255)
    
    def test_to_vector_shape(self):
        from ai.multimodal.primitives.primitive_types import TOTAL_DIM
        instr = DrawingInstructions()
        vec = instr.to_vector()
        assert vec.shape == (TOTAL_DIM,)
        assert vec.dtype == np.float32
    
    def test_to_vector_with_content(self):
        from ai.multimodal.primitives.primitive_types import TOTAL_DIM
        instr = DrawingInstructions(
            points=[Point(0.5, 0.5, (255, 0, 0), 0.1)],
            lines=[Line(Point(0.0, 0.0, (0, 0, 0), 0.0), 
                       Point(1.0, 1.0, (0, 0, 0), 0.0), 
                       0.05, (0, 255, 0))],
            background_color=(0, 0, 0)
        )
        vec = instr.to_vector()
        assert vec.shape == (TOTAL_DIM,)
        # Background color should be (0, 0, 0) -> 0.0
        assert vec[0] == 0.0
        assert vec[1] == 0.0
        assert vec[2] == 0.0
    
    def test_from_vector_roundtrip(self):
        original = DrawingInstructions(
            points=[Point(0.5, 0.5, (255, 0, 0), 0.1)],
            background_color=(128, 128, 128)
        )
        vec = original.to_vector()
        restored = DrawingInstructions.from_vector(vec)
        assert restored.background_color == (128, 128, 128)
        assert len(restored.points) == 1
        assert abs(restored.points[0].x - 0.5) < 0.01
        assert abs(restored.points[0].y - 0.5) < 0.01
