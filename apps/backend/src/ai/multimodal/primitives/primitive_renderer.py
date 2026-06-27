"""Render drawing instructions to images using PIL."""

import math
from typing import Tuple

from PIL import Image, ImageDraw

from .primitive_types import Arc, Circle, DrawingInstructions, Line, Plane, Point


class PrimitiveRenderer:
    """Renders DrawingInstructions to PIL Images."""

    def __init__(self, canvas_size: Tuple[int, int] = (128, 128)):
        self._canvas_size = canvas_size

    def render(self, instructions: DrawingInstructions) -> Image.Image:
        """Render drawing instructions to PIL Image."""
        img = Image.new("RGB", self._canvas_size, instructions.background_color)
        draw = ImageDraw.Draw(img)

        # Draw planes first (background)
        for plane in instructions.planes:
            self._draw_plane(draw, plane)

        # Draw circles
        for circle in instructions.circles:
            self._draw_circle(draw, circle)

        # Draw arcs
        for arc in instructions.arcs:
            self._draw_arc(draw, arc)

        # Draw lines
        for line in instructions.lines:
            self._draw_line(draw, line)

        # Draw points last (foreground)
        for point in instructions.points:
            self._draw_point(draw, point)

        return img

    def _draw_point(self, draw: ImageDraw, point: Point):
        """Draw a point as a filled circle."""
        x = int(point.x * self._canvas_size[0])
        y = int(point.y * self._canvas_size[1])
        r = max(1, int(point.size * min(self._canvas_size) * 0.1))
        draw.ellipse([x - r, y - r, x + r, y + r], fill=point.color)

    def _draw_line(self, draw: ImageDraw, line: Line):
        """Draw a line."""
        start = (int(line.start.x * self._canvas_size[0]),
                 int(line.start.y * self._canvas_size[1]))
        end = (int(line.end.x * self._canvas_size[0]),
               int(line.end.y * self._canvas_size[1]))
        width = max(1, int(line.width * min(self._canvas_size) * 0.05))
        draw.line([start, end], fill=line.color, width=width)

    def _draw_plane(self, draw: ImageDraw, plane: Plane):
        """Draw a filled polygon."""
        if not plane.points:
            return
        points = [(int(p.x * self._canvas_size[0]),
                    int(p.y * self._canvas_size[1])) for p in plane.points]
        draw.polygon(points, fill=plane.fill_color, outline=plane.outline_color)

    def _draw_circle(self, draw: ImageDraw, circle: Circle):
        """Draw a filled circle with optional outline."""
        cx = int(circle.cx * self._canvas_size[0])
        cy = int(circle.cy * self._canvas_size[1])
        r = int(circle.radius * min(self._canvas_size) * 0.5)
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.ellipse(bbox, fill=circle.fill_color, outline=circle.outline_color)

    def _draw_arc(self, draw: ImageDraw, arc: Arc):
        """Draw an arc."""
        cx = int(arc.cx * self._canvas_size[0])
        cy = int(arc.cy * self._canvas_size[1])
        r = int(arc.radius * min(self._canvas_size) * 0.5)
        bbox = [cx - r, cy - r, cx + r, cy + r]
        # PIL arc uses degrees
        start_deg = math.degrees(arc.start_angle)
        end_deg = math.degrees(arc.end_angle)
        width = max(1, int(arc.width * min(self._canvas_size) * 0.03))
        draw.arc(bbox, start_deg, end_deg, fill=arc.color, width=width)

    def render_to_bytes(self, instructions: DrawingInstructions,
                        format: str = "PNG") -> bytes:
        """Render to image bytes."""
        img = self.render(instructions)
        import io
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        return buffer.getvalue()
