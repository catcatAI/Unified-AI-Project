"""Tests for primitive renderer."""

import numpy as np
import pytest
from ai.multimodal.primitives.primitive_renderer import PrimitiveRenderer
from ai.multimodal.primitives.primitive_types import DrawingInstructions, Line, Plane, Point
from PIL import Image


@pytest.fixture
def renderer():
    return PrimitiveRenderer(canvas_size=(128, 128))


class TestPrimitiveRenderer:
    def test_render_empty_instructions(self, renderer):
        instr = DrawingInstructions()
        img = renderer.render(instr)
        assert isinstance(img, Image.Image)
        assert img.size == (128, 128)
        assert img.mode == "RGB"
    
    def test_render_with_points(self, renderer):
        instr = DrawingInstructions(
            points=[
                Point(0.25, 0.25, (255, 0, 0), 0.1),
                Point(0.75, 0.75, (0, 255, 0), 0.1),
            ]
        )
        img = renderer.render(instr)
        assert isinstance(img, Image.Image)
        # Check that image is not all white (has some color)
        arr = np.array(img)
        assert not np.all(arr == 255)
    
    def test_render_with_lines(self, renderer):
        instr = DrawingInstructions(
            lines=[
                Line(
                    Point(0.1, 0.1, (0, 0, 0), 0.0),
                    Point(0.9, 0.9, (0, 0, 0), 0.0),
                    0.05,
                    (0, 0, 255)
                )
            ]
        )
        img = renderer.render(instr)
        assert isinstance(img, Image.Image)
        arr = np.array(img)
        assert not np.all(arr == 255)
    
    def test_render_with_planes(self, renderer):
        instr = DrawingInstructions(
            planes=[
                Plane(
                    [
                        Point(0.2, 0.2, (0, 0, 0), 0.0),
                        Point(0.8, 0.2, (0, 0, 0), 0.0),
                        Point(0.8, 0.8, (0, 0, 0), 0.0),
                        Point(0.2, 0.8, (0, 0, 0), 0.0),
                    ],
                    (255, 0, 0),
                    (0, 0, 0),
                    0.02
                )
            ]
        )
        img = renderer.render(instr)
        assert isinstance(img, Image.Image)
        arr = np.array(img)
        assert not np.all(arr == 255)
    
    def test_render_all_primitives(self, renderer):
        instr = DrawingInstructions(
            background_color=(200, 200, 200),
            points=[Point(0.5, 0.5, (255, 255, 0), 0.1)],
            lines=[Line(
                Point(0.1, 0.5, (0, 0, 0), 0.0),
                Point(0.9, 0.5, (0, 0, 0), 0.0),
                0.03,
                (0, 0, 0)
            )],
            planes=[Plane(
                [
                    Point(0.3, 0.3, (0, 0, 0), 0.0),
                    Point(0.7, 0.3, (0, 0, 0), 0.0),
                    Point(0.7, 0.7, (0, 0, 0), 0.0),
                    Point(0.3, 0.7, (0, 0, 0), 0.0),
                ],
                (0, 0, 255),
                (0, 0, 0),
                0.01
            )]
        )
        img = renderer.render(instr)
        assert isinstance(img, Image.Image)
        arr = np.array(img)
        # Should have background color
        assert arr[0, 0, 0] == 200
        assert arr[0, 0, 1] == 200
        assert arr[0, 0, 2] == 200
    
    def test_render_to_bytes(self, renderer):
        instr = DrawingInstructions(
            points=[Point(0.5, 0.5, (255, 0, 0), 0.1)]
        )
        img_bytes = renderer.render_to_bytes(instr, format="PNG")
        assert isinstance(img_bytes, bytes)
        assert len(img_bytes) > 0
        # Verify it's valid PNG
        assert img_bytes[:4] == b'\x89PNG'
    
    def test_different_canvas_sizes(self):
        for size in [(64, 64), (256, 256), (512, 512)]:
            renderer = PrimitiveRenderer(canvas_size=size)
            instr = DrawingInstructions(
                points=[Point(0.5, 0.5, (255, 0, 0), 0.1)]
            )
            img = renderer.render(instr)
            assert img.size == size
