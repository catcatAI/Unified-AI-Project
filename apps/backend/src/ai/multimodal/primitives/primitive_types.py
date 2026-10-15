"""Primitive type definitions for compositional image generation.

Expanded types: Point, Line, Plane, Circle, Arc
Vector layout expanded to ~200 dims for richer representation.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, List, Tuple

import numpy as np


@dataclass
class Point:
    """A point primitive with position, color, and size."""

    x: float  # 0-1 normalized
    y: float  # 0-1 normalized
    color: Tuple[int, ...]  # RGB 0-255
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
    color: Tuple[int, ...]

    def __post_init__(self):
        self.width = max(0.0, min(1.0, self.width))
        self.color = tuple(max(0, min(255, c)) for c in self.color)


@dataclass
class Plane:
    """A plane primitive (filled polygon) with vertices and colors."""

    points: List[Point]  # Polygon vertices
    fill_color: Tuple[int, ...]
    outline_color: Tuple[int, ...]
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
    fill_color: Tuple[int, ...]
    outline_color: Tuple[int, ...]
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
    color: Tuple[int, ...]

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

# ── Dynamic slot helpers (vvv 坑1) ─────────────────────────────────
# TOTAL_DIM is fixed 263 for backward compat, but vvv calls for dynamic
# slots (few objects -> few slots, crowded scenes -> more). This helper
# estimates needed slots from region count so callers can clamp K and avoid
# wasting 263 dims on empty primitives or fragmenting single objects.
# Three-level split: background (planes) / subject (circles+arcs) / detail (points+lines).


def estimate_slots(n_regions: int) -> int:
    """Heuristic: regions -> suggested visual words K (3..20, clamped).

    Keeps K small for simple scenes (saves compute) and larger for crowded
    scenes (preserves decoupling). Caller should do
    ``k = min(estimate_slots(n_regions), len(instructions))``.
    """
    if n_regions <= 2:
        return 5
    if n_regions <= 6:
        return 10
    if n_regions <= 12:
        return 15
    return 20


def level_slot_counts(n_regions: int) -> dict:
    """Three-level split for vvv multi-level slots.

    Returns dict with background/subject/detail K budgets that sum to
    estimate_slots(). Keeps single-object scenes from over-fragmenting.
    """
    total = estimate_slots(n_regions)
    # background ~30%, subject ~40%, detail ~30%
    bg = max(2, int(total * 0.3))
    subj = max(2, int(total * 0.4))
    detail = max(1, total - bg - subj)
    return {"background": bg, "subject": subj, "detail": detail, "total": total}


@dataclass
class DrawingInstructions:
    """Complete set of drawing instructions for rendering."""

    points: List[Point] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    planes: List[Plane] = field(default_factory=list)
    circles: List[Circle] = field(default_factory=list)
    arcs: List[Arc] = field(default_factory=list)
    background_color: Tuple[int, ...] = (255, 255, 255)
    canvas_size: Tuple[int, int] = (128, 128)

    @staticmethod
    def _vector_block(items: List[Any], n_slots: int, width: int, encode: Callable) -> List[float]:
        """Encode up to n_slots items, then zero-pad the block to n_slots*width."""
        vec: List[float] = []
        for item in items[:n_slots]:
            vec.extend(encode(item))
        for _ in range(max(0, n_slots - len(items))):
            vec.extend([0.0] * width)
        return vec

    @staticmethod
    def _plane_vec(pl: Plane) -> List[float]:
        """Plane → 9-dim bbox encoding (cx, cy, rx, ry, fill RGB, outline_w, _)."""
        if pl.points:
            xs = [p.x for p in pl.points]
            ys = [p.y for p in pl.points]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            rx = (max(xs) - min(xs)) / 2
            ry = (max(ys) - min(ys)) / 2
        else:
            cx, cy, rx, ry = 0.5, 0.5, 0.0, 0.0
        return [
            cx,
            cy,
            rx,
            ry,
            pl.fill_color[0] / 255.0,
            pl.fill_color[1] / 255.0,
            pl.fill_color[2] / 255.0,
            pl.outline_width,
            0.0,
        ]

    def to_vector(self) -> np.ndarray:
        """Convert instructions to fixed-size vector for ML."""
        vec: List[float] = []

        # Header
        vec.extend([c / 255.0 for c in self.background_color])
        vec.extend([self.canvas_size[0] / 256.0, self.canvas_size[1] / 256.0])

        # Points (15 × 5 = 75)
        vec.extend(
            self._vector_block(
                self.points,
                N_POINTS,
                5,
                lambda p: [p.x, p.y, p.color[0] / 255.0, p.color[1] / 255.0, p.color[2] / 255.0],
            )
        )

        # Lines (10 × 8 = 80)
        vec.extend(
            self._vector_block(
                self.lines,
                N_LINES,
                8,
                lambda l: [
                    l.start.x,
                    l.start.y,
                    l.end.x,
                    l.end.y,
                    l.width,
                    l.color[0] / 255.0,
                    l.color[1] / 255.0,
                    l.color[2] / 255.0,
                ],
            )
        )

        # Planes (5 × 9 = 45) — simplified as bounding rect
        vec.extend(self._vector_block(self.planes, N_PLANES, 9, self._plane_vec))

        # Circles (4 × 7 = 28)
        vec.extend(
            self._vector_block(
                self.circles,
                N_CIRCLES,
                7,
                lambda c: [
                    c.cx,
                    c.cy,
                    c.radius,
                    c.fill_color[0] / 255.0,
                    c.fill_color[1] / 255.0,
                    c.fill_color[2] / 255.0,
                    c.outline_width,
                ],
            )
        )

        # Arcs (3 × 10 = 30)
        vec.extend(
            self._vector_block(
                self.arcs,
                N_ARCS,
                10,
                lambda a: [
                    a.cx,
                    a.cy,
                    a.radius,
                    a.start_angle / (2 * math.pi),
                    a.end_angle / (2 * math.pi),
                    a.width,
                    a.color[0] / 255.0,
                    a.color[1] / 255.0,
                    a.color[2] / 255.0,
                    0.0,
                ],
            )
        )

        return np.array(vec, dtype=np.float32)

    @classmethod
    def _points_from_vec(cls, vec: np.ndarray) -> List[Point]:
        points: List[Point] = []
        for i in range(N_POINTS):
            s = 5 + i * 5
            x, y, r, g, b = vec[s : s + 5]
            if x > 0 or y > 0:
                points.append(Point(x, y, (int(r * 255), int(g * 255), int(b * 255)), 0.05))
        return points

    @classmethod
    def _lines_from_vec(cls, vec: np.ndarray) -> List[Line]:
        base = 5 + N_POINTS * 5
        lines: List[Line] = []
        for i in range(N_LINES):
            s = base + i * 8
            sx, sy, ex, ey, w, r, g, b = vec[s : s + 8]
            if sx > 0 or sy > 0 or ex > 0 or ey > 0:
                lines.append(
                    Line(
                        Point(sx, sy, (0, 0, 0), 0.0),
                        Point(ex, ey, (0, 0, 0), 0.0),
                        w,
                        (int(r * 255), int(g * 255), int(b * 255)),
                    )
                )
        return lines

    @classmethod
    def _planes_from_vec(cls, vec: np.ndarray) -> List[Plane]:
        base = 5 + N_POINTS * 5 + N_LINES * 8
        planes: List[Plane] = []
        for i in range(N_PLANES):
            s = base + i * 9
            cx, cy, rx, ry, fr, fg, fb, ow, _ = vec[s : s + 9]
            if rx > 0 or ry > 0:
                planes.append(
                    Plane(
                        [
                            Point(cx - rx, cy - ry, (0, 0, 0), 0),
                            Point(cx + rx, cy - ry, (0, 0, 0), 0),
                            Point(cx + rx, cy + ry, (0, 0, 0), 0),
                            Point(cx - rx, cy + ry, (0, 0, 0), 0),
                        ],
                        (int(fr * 255), int(fg * 255), int(fb * 255)),
                        (0, 0, 0),
                        ow,
                    )
                )
        return planes

    @classmethod
    def _circles_from_vec(cls, vec: np.ndarray) -> List[Circle]:
        base = 5 + N_POINTS * 5 + N_LINES * 8 + N_PLANES * 9
        circles: List[Circle] = []
        for i in range(N_CIRCLES):
            s = base + i * 7
            cx, cy, r, fr, fg, fb, ow = vec[s : s + 7]
            if r > 0:
                circles.append(
                    Circle(cx, cy, r, (int(fr * 255), int(fg * 255), int(fb * 255)), (0, 0, 0), ow)
                )
        return circles

    @classmethod
    def _arcs_from_vec(cls, vec: np.ndarray) -> List[Arc]:
        base = 5 + N_POINTS * 5 + N_LINES * 8 + N_PLANES * 9 + N_CIRCLES * 7
        arcs: List[Arc] = []
        for i in range(N_ARCS):
            s = base + i * 10
            cx, cy, r, sa, ea, w, cr, cg, cb, _ = vec[s : s + 10]
            if r > 0:
                arcs.append(
                    Arc(
                        cx,
                        cy,
                        r,
                        sa * 2 * math.pi,
                        ea * 2 * math.pi,
                        w,
                        (int(cr * 255), int(cg * 255), int(cb * 255)),
                    )
                )
        return arcs

    @classmethod
    def from_vector(
        cls, vec: np.ndarray, canvas_size: Tuple[int, int] = (128, 128)
    ) -> "DrawingInstructions":
        """Create DrawingInstructions from vector representation."""
        if len(vec) != TOTAL_DIM:
            raise ValueError(f"Expected vector of length {TOTAL_DIM}, got {len(vec)}")

        bg_color = tuple(int(c * 255) for c in vec[0:3])

        return cls(
            points=cls._points_from_vec(vec),
            lines=cls._lines_from_vec(vec),
            planes=cls._planes_from_vec(vec),
            circles=cls._circles_from_vec(vec),
            arcs=cls._arcs_from_vec(vec),
            background_color=bg_color,
            canvas_size=canvas_size,
        )
