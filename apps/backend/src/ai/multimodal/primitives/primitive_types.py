"""Primitive type definitions for compositional image generation."""

from dataclasses import dataclass, field
from typing import List, Tuple
import numpy as np


@dataclass
class Point:
    """A point primitive with position, color, and size."""
    x: float  # 0-1 normalized
    y: float  # 0-1 normalized
    color: Tuple[int, int, int]  # RGB 0-255
    size: float  # 0-1 normalized
    
    def __post_init__(self):
        self.x = max(0.0, min(1.0, self.x))
        self.y = max(0.0, min(1.0, self.y))
        self.size = max(0.0, min(1.0, self.size))
        self.color = tuple(max(0, min(255, c)) for c in self.color)


@dataclass
class Line:
    """A line primitive with start/end points, width, and color."""
    start: Point
    end: Point
    width: float  # 0-1 normalized
    color: Tuple[int, int, int]
    
    def __post_init__(self):
        self.width = max(0.0, min(1.0, self.width))
        self.color = tuple(max(0, min(255, c)) for c in self.color)


@dataclass
class Plane:
    """A plane primitive (filled polygon) with vertices and colors."""
    points: List[Point]  # Polygon vertices
    fill_color: Tuple[int, int, int]
    outline_color: Tuple[int, int, int]
    outline_width: float
    
    def __post_init__(self):
        self.fill_color = tuple(max(0, min(255, c)) for c in self.fill_color)
        self.outline_color = tuple(max(0, min(255, c)) for c in self.outline_color)
        self.outline_width = max(0.0, min(1.0, self.outline_width))


@dataclass
class DrawingInstructions:
    """Complete set of drawing instructions for rendering."""
    points: List[Point] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    planes: List[Plane] = field(default_factory=list)
    background_color: Tuple[int, int, int] = (255, 255, 255)
    canvas_size: Tuple[int, int] = (128, 128)
    
    def to_vector(self) -> np.ndarray:
        """Convert instructions to fixed-size vector for ML.
        
        Vector layout:
        - [0:3] background_color (normalized)
        - [3:5] canvas_size (normalized)
        - [5:5+n_points*5] points (x, y, r, g, b, size per point)
        - [5+n_points*5:...] lines (start_x, start_y, end_x, end_y, width, r, g, b)
        - [...] planes (simplified: center_x, center_y, radius, fill_r, fill_g, fill_b)
        """
        vec = []
        
        # Background color (3)
        vec.extend([c / 255.0 for c in self.background_color])
        
        # Canvas size (2) - normalize to 0-1
        vec.extend([self.canvas_size[0] / 256.0, self.canvas_size[1] / 256.0])
        
        # Points (max 10, 5 values each = 50)
        for i, p in enumerate(self.points[:10]):
            vec.extend([p.x, p.y, p.color[0] / 255.0, p.color[1] / 255.0, p.color[2] / 255.0])
        # Pad to 10 points
        for i in range(max(0, 10 - len(self.points))):
            vec.extend([0.0] * 5)
        
        # Lines (max 5, 8 values each = 40)
        for i, l in enumerate(self.lines[:5]):
            vec.extend([l.start.x, l.start.y, l.end.x, l.end.y, l.width,
                       l.color[0] / 255.0, l.color[1] / 255.0, l.color[2] / 255.0])
        # Pad to 5 lines
        for i in range(max(0, 5 - len(self.lines))):
            vec.extend([0.0] * 8)
        
        # Planes (max 3, 7 values each = 21)
        for i, pl in enumerate(self.planes[:3]):
            # Compute center and approximate radius
            if pl.points:
                xs = [p.x for p in pl.points]
                ys = [p.y for p in pl.points]
                cx = sum(xs) / len(xs)
                cy = sum(ys) / len(ys)
                radius = max(max(xs) - min(xs), max(ys) - min(ys)) / 2
            else:
                cx, cy, radius = 0.5, 0.5, 0.0
            vec.extend([cx, cy, radius,
                       pl.fill_color[0] / 255.0, pl.fill_color[1] / 255.0, pl.fill_color[2] / 255.0,
                       pl.outline_width])
        # Pad to 3 planes
        for i in range(max(0, 3 - len(self.planes))):
            vec.extend([0.0] * 7)
        
        return np.array(vec, dtype=np.float32)
    
    @classmethod
    def from_vector(cls, vec: np.ndarray, canvas_size: Tuple[int, int] = (128, 128)) -> 'DrawingInstructions':
        """Create DrawingInstructions from vector representation."""
        if len(vec) != 116:  # 3 + 2 + 50 + 40 + 21
            raise ValueError(f"Expected vector of length 116, got {len(vec)}")
        
        # Parse background color
        bg_color = tuple(int(c * 255) for c in vec[0:3])
        
        # Parse points (10 points, 5 values each)
        points = []
        for i in range(10):
            start = 5 + i * 5
            x, y, r, g, b = vec[start:start + 5]
            if x > 0 or y > 0:  # Non-zero point
                points.append(Point(x, y, (int(r * 255), int(g * 255), int(b * 255)), 0.05))
        
        # Parse lines (5 lines, 8 values each)
        lines = []
        for i in range(5):
            start = 55 + i * 8
            sx, sy, ex, ey, w, r, g, b = vec[start:start + 8]
            if sx > 0 or sy > 0 or ex > 0 or ey > 0:  # Non-zero line
                lines.append(Line(
                    Point(sx, sy, (0, 0, 0), 0.0),
                    Point(ex, ey, (0, 0, 0), 0.0),
                    w,
                    (int(r * 255), int(g * 255), int(b * 255))
                ))
        
        # Parse planes (3 planes, 7 values each)
        planes = []
        for i in range(3):
            start = 95 + i * 7
            cx, cy, radius, fr, fg, fb, ow = vec[start:start + 7]
            if radius > 0:  # Non-zero plane
                # Create square polygon around center
                half = radius / 2
                plane_points = [
                    Point(cx - half, cy - half, (0, 0, 0), 0.0),
                    Point(cx + half, cy - half, (0, 0, 0), 0.0),
                    Point(cx + half, cy + half, (0, 0, 0), 0.0),
                    Point(cx - half, cy + half, (0, 0, 0), 0.0),
                ]
                planes.append(Plane(
                    plane_points,
                    (int(fr * 255), int(fg * 255), int(fb * 255)),
                    (0, 0, 0),
                    ow
                ))
        
        return cls(
            points=points,
            lines=lines,
            planes=planes,
            background_color=bg_color,
            canvas_size=canvas_size
        )
