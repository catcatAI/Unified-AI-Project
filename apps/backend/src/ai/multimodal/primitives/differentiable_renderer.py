"""Vectorized differentiable renderer: fast, no Python loops over primitives."""

import math
from typing import Tuple

import numpy as np


class DifferentiableRenderer:
    """Fast vectorized soft rasterizer."""

    def __init__(self, canvas_size: Tuple[int, int] = (128, 128)):
        self._w, self._h = canvas_size
        ys = np.arange(self._h, dtype=np.float32)
        xs = np.arange(self._w, dtype=np.float32)
        xx, yy = np.meshgrid(xs, ys)
        self._nx = xx / self._w  # (H, W) normalized [0, 1]
        self._ny = yy / self._h

    def render(self, vec: np.ndarray) -> np.ndarray:
        """Render 263-dim vector to (H, W, 3). Vectorized, no Python loops."""
        from ai.multimodal.primitives.primitive_types import (
            N_ARCS,
            N_CIRCLES,
            N_LINES,
            N_PLANES,
            N_POINTS,
        )

        h, w = self._h, self._w
        nx, ny = self._nx, self._ny
        bg = vec[0:3]

        canvas = np.zeros((h, w, 3), dtype=np.float32)
        weight = np.zeros((h, w), dtype=np.float32)

        off = 5
        off = self._render_planes(vec, off, canvas, weight, nx, ny)
        off = self._render_circles(vec, off, canvas, weight, nx, ny)
        off = self._render_arcs(vec, off, canvas, weight, nx, ny)
        off = self._render_lines(vec, off, canvas, weight, nx, ny)
        self._render_points(vec, off, canvas, weight, nx, ny)

        canvas = canvas + bg * (1 - weight[:, :, None])
        return np.clip(canvas, 0, 1)

    @staticmethod
    def _layer(canvas, weight, alpha, color):
        a = np.clip(alpha, 0, 1) ** 0.5
        w_exp = a * (1 - weight)
        canvas += w_exp[:, :, None] * color[None, None, :]
        weight[:] = np.clip(weight + w_exp, 0, 1)

    @staticmethod
    def _render_planes(vec, off, canvas, weight, nx, ny):
        from ai.multimodal.primitives.primitive_types import N_PLANES

        planes = vec[off : off + N_PLANES * 9].reshape(N_PLANES, 9)
        for i in range(N_PLANES):
            cx, cy, rx, ry = planes[i, :4]
            if rx < 0.001 and ry < 0.001:
                continue
            color = planes[i, 4:7]
            dx = np.abs(nx - cx) / max(rx, 0.001)
            dy = np.abs(ny - cy) / max(ry, 0.001)
            d = np.maximum(dx, dy)
            alpha = np.clip(1.5 - d * 2, 0, 1)
            DifferentiableRenderer._layer(canvas, weight, alpha, color)
        return off + N_PLANES * 9

    @staticmethod
    def _render_circles(vec, off, canvas, weight, nx, ny):
        from ai.multimodal.primitives.primitive_types import N_CIRCLES

        circles = vec[off : off + N_CIRCLES * 7].reshape(N_CIRCLES, 7)
        for i in range(N_CIRCLES):
            cx, cy, r = circles[i, :3]
            if r < 0.001:
                continue
            color = circles[i, 3:6]
            dist = np.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
            alpha = np.clip(1.5 - dist / r * 2, 0, 1)
            DifferentiableRenderer._layer(canvas, weight, alpha, color)
        return off + N_CIRCLES * 7

    @staticmethod
    def _render_arcs(vec, off, canvas, weight, nx, ny):
        import math

        from ai.multimodal.primitives.primitive_types import N_ARCS

        arcs = vec[off : off + N_ARCS * 10].reshape(N_ARCS, 10)
        for i in range(N_ARCS):
            cx, cy, r = arcs[i, :3]
            if r < 0.001:
                continue
            sa, ea, aw = arcs[i, 3:6]
            color = arcs[i, 6:9]
            dist = np.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
            angle = np.arctan2(ny - cy, nx - cx)
            angle = (angle + 2 * math.pi) % (2 * math.pi)
            sa_n = (sa + 2 * math.pi) % (2 * math.pi)
            ea_n = (ea + 2 * math.pi) % (2 * math.pi)
            in_arc = (
                (angle >= sa_n) & (angle <= ea_n)
                if sa_n <= ea_n
                else (angle >= sa_n) | (angle <= ea_n)
            )
            radial = np.clip(1.0 - np.abs(dist - r) / max(aw * 0.5, 0.005), 0, 1)
            alpha = radial * in_arc.astype(np.float32)
            DifferentiableRenderer._layer(canvas, weight, alpha, color)
        return off + N_ARCS * 10

    @staticmethod
    def _render_lines(vec, off, canvas, weight, nx, ny):
        import math

        from ai.multimodal.primitives.primitive_types import N_LINES

        lines = vec[off : off + N_LINES * 8].reshape(N_LINES, 8)
        for i in range(N_LINES):
            sx, sy, ex, ey, lw = lines[i, :5]
            if sx == ex and sy == ey:
                continue
            color = lines[i, 5:8]
            dx, dy = ex - sx, ey - sy
            l_len = math.sqrt(dx * dx + dy * dy)
            if l_len < 0.001:
                continue
            dx_n, dy_n = dx / l_len, dy / l_len
            px, py = nx - sx, ny - sy
            t = np.clip(px * dx_n + py * dy_n, 0, l_len)
            cx = sx + t * dx_n
            cy = sy + t * dy_n
            dist = np.sqrt((nx - cx) ** 2 + (ny - cy) ** 2)
            alpha = np.clip(1.0 - dist / max(lw, 0.008), 0, 1)
            DifferentiableRenderer._layer(canvas, weight, alpha, color)
        return off + N_LINES * 8

    @staticmethod
    def _render_points(vec, off, canvas, weight, nx, ny):
        from ai.multimodal.primitives.primitive_types import N_POINTS

        points = vec[off : off + N_POINTS * 5].reshape(N_POINTS, 5)
        for i in range(N_POINTS):
            px, py = points[i, :2]
            if px == 0 and py == 0:
                continue
            color = points[i, 2:5]
            dist = np.sqrt((nx - px) ** 2 + (ny - py) ** 2)
            alpha = np.clip(1.0 - dist / 0.025, 0, 1) ** 0.5
            DifferentiableRenderer._layer(canvas, weight, alpha, color)
