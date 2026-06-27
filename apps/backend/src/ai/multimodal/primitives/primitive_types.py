"""Primitive type definitions for compositional image generation.

Expanded types: Point, Line, Plane, Circle, Arc
Vector layout expanded to ~200 dims for richer representation.
"""

import math
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
class Circle:
    """A circle primitive with center, radius, and color."""
    cx: float  # 0-1 normalized
    cy: float  # 0-1 normalized
    radius: float  # 0-1 normalized
    fill_color: Tuple[int, int, int]
    outline_color: Tuple[int, int, int]
    outline_width: float

    def __post_init__(self):
        self.cx = max(0.0, min(1.0, self.cx))
        self.cy = max(0.0, min(1.0, self.cy))
        self.radius = max(0.0, min(0.5, self.radius))
        self.fill_color = tuple(max(0, min(255, c)) for c in self.fill_color)
        self.outline_color = tuple(max(0, min(255, c)) for c in self.outline_color)
        self.outline_width = max(0.0, min(1.0, self.outline_width))


@dataclass
class Arc:
    """An arc primitive with center, radius, angle range, and color."""
    cx: float  # 0-1 normalized
    cy: float  # 0-1 normalized
    radius: float  # 0-1 normalized
    start_angle: float  # radians
    end_angle: float  # radians
    width: float  # line width
    color: Tuple[int, int, int]

    def __post_init__(self):
        self.cx = max(0.0, min(1.0, self.cx))
        self.cy = max(0.0, min(1.0, self.cy))
        self.radius = max(0.0, min(0.5, self.radius))
        self.width = max(0.0, min(1.0, self.width))
        self.color = tuple(max(0, min(255, c)) for c in self.color)


# ── Vector layout constants ──────────────────────────────────────
# [0:5]   header (bg_color 3 + canvas 2)
# [5:80]  15 points × 5 (x,y,r,g,b)
# [80:160] 10 lines × 8 (sx,sy,ex,ey,w,r,g,b)
# [160:205] 5 planes × 9 (cx,cy,rx,ry,fr,fg,fb,ow,_)  # simplified rect
# [205:233] 4 circles × 7 (cx,cy,r,fr,fg,fb,ow)
# [233:263] 3 arcs × 10 (cx,cy,r,start,end,w,r,g,b,_)
TOTAL_DIM = 263

N_POINTS = 15
N_LINES = 10
N_PLANES = 5
N_CIRCLES = 4
N_ARCS = 3


@dataclass
class DrawingInstructions:
    """Complete set of drawing instructions for rendering."""
    points: List[Point] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    planes: List[Plane] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    background_color: Tuple[int, int, int] = (255, 255, 255)
    canvas_size: Tuple[int, int] = (128, 128)

    def to_vector(self) -> np.ndarray:
        """Convert instructions to fixed-size vector for ML."""
        vec = []

        # Header
        vec.extend([c / 255.0 for c in self.background_color])
        vec.extend([self.canvas_size[0] / 256.0, self.canvas_size[1] / 256.0])

        # Points (15 × 5 = 75)
        for p in self.points[:N_POINTS]:
            vec.extend([p.x, p.y, p.color[0] / 255.0, p.color[1] / 255.0, p.color[2] / 255.0])
        for _ in range(max(0, N_POINTS - len(self.points))):
            vec.extend([0.0] * 5)

        # Lines (10 × 8 = 80)
        for l in self.lines[:N_LINES]:
            vec.extend([l.start.x, l.start.y, l.end.x, l.end.y, l.width,
                        l.color[0] / 255.0, l.color[1] / 255.0, l.color[2] / 255.0])
        for _ in range(max(0, N_LINES - len(self.lines))):
            vec.extend([0.0] * 8)

        # Planes (5 × 9 = 45) — simplified as bounding rect: cx, cy, rx, ry, fill_r, fill_g, fill_b, outline_w, _
        for pl in self.planes[:N_PLANES]:
            if pl.points:
                xs = [p.x for p in pl.points]
                ys = [p.y for p in pl.points]
                cx = (min(xs) + max(xs)) / 2
                cy = (min(ys) + max(ys)) / 2
                rx = (max(xs) - min(xs)) / 2
                ry = (max(ys) - min(ys)) / 2
            else:
                cx, cy, rx, ry = 0.5, 0.5, 0.0, 0.0
            vec.extend([cx, cy, rx, ry,
                        pl.fill_color[0] / 255.0, pl.fill_color[1] / 255.0, pl.fill_color[2] / 255.0,
                        pl.outline_width, 0.0])
        for _ in range(max(0, N_PLANES - len(self.planes))):
            vec.extend([0.0] * 9)

        # Circles (4 × 7 = 28)
        for c in self.circles[:N_CIRCLES]:
            vec.extend([c.cx, c.cy, c.radius,
                        c.fill_color[0] / 255.0, c.fill_color[1] / 255.0, c.fill_color[2] / 255.0,
                        c.outline_width])
        for _ in range(max(0, N_CIRCLES - len(self.circles))):
            vec.extend([0.0] * 7)

        # Arcs (3 × 10 = 30)
        for a in self.arcs[:N_ARCS]:
            vec.extend([a.cx, a.cy, a.radius,
                        a.start_angle / (2 * math.pi), a.end_angle / (2 * math.pi),
                        a.width,
                        a.color[0] / 255.0, a.color[1] / 255.0, a.color[2] / 255.0,
                        0.0])
        for _ in range(max(0, N_ARCS - len(self.arcs))):
            vec.extend([0.0] * 10)

        return np.array(vec, dtype=np.float32)

    @classmethod
    def from_vector(cls, vec: np.ndarray, canvas_size: Tuple[int, int] = (128, 128)) -> 'DrawingInstructions':
        """Create DrawingInstructions from vector representation."""
        if len(vec) != TOTAL_DIM:
            raise ValueError(f"Expected vector of length {TOTAL_DIM}, got {len(vec)}")

        bg_color = tuple(int(c * 255) for c in vec[0:3])

        # Points
        points = []
        for i in range(N_POINTS):
            s = 5 + i * 5
            x, y, r, g, b = vec[s:s + 5]
            if x > 0 or y > 0:
                points.append(Point(x, y, (int(r * 255), int(g * 255), int(b * 255)), 0.05))

        # Lines
        off = 5 + N_POINTS * 5
        lines = []
        for i in range(N_LINES):
            s = off + i * 8
            sx, sy, ex, ey, w, r, g, b = vec[s:s + 8]
            if sx > 0 or sy > 0 or ex > 0 or ey > 0:
                lines.append(Line(
                    Point(sx, sy, (0, 0, 0), 0.0), Point(ex, ey, (0, 0, 0), 0.0),
                    w, (int(r * 255), int(g * 255), int(b * 255))))

        # Planes
        off += N_LINES * 8
        planes = []
        for i in range(N_PLANES):
            s = off + i * 9
            cx, cy, rx, ry, fr, fg, fb, ow, _ = vec[s:s + 9]
            if rx > 0 or ry > 0:
                planes.append(Plane(
                    [Point(cx - rx, cy - ry, (0, 0, 0), 0), Point(cx + rx, cy - ry, (0, 0, 0), 0),
                     Point(cx + rx, cy + ry, (0, 0, 0), 0), Point(cx - rx, cy + ry, (0, 0, 0), 0)],
                    (int(fr * 255), int(fg * 255), int(fb * 255)), (0, 0, 0), ow))

        # Circles
        off += N_PLANES * 9
        circles = []
        for i in range(N_CIRCLES):
            s = off + i * 7
            cx, cy, r, fr, fg, fb, ow = vec[s:s + 7]
            if r > 0:
                circles.append(Circle(cx, cy, r,
                    (int(fr * 255), int(fg * 255), int(fb * 255)), (0, 0, 0), ow))

        # Arcs
        off += N_CIRCLES * 7
        arcs = []
        for i in range(N_ARCS):
            s = off + i * 10
            cx, cy, r, sa, ea, w, cr, cg, cb, _ = vec[s:s + 10]
            if r > 0:
                arcs.append(Arc(cx, cy, r,
                    sa * 2 * math.pi, ea * 2 * math.pi, w,
                    (int(cr * 255), int(cg * 255), int(cb * 255))))

        return cls(points=points, lines=lines, planes=planes, circles=circles, arcs=arcs,
                   background_color=bg_color, canvas_size=canvas_size)
