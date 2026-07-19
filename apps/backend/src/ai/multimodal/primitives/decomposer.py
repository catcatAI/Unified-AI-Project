"""Spatial decomposer: extracts points, lines, planes, circles, arcs from images."""

import math
import os
import sys
from typing import List, Tuple

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))
from ai.multimodal.primitives.primitive_types import (
    Arc,
    Circle,
    DrawingInstructions,
    Line,
    Plane,
    Point,
)


def grid_colors(
    arr: np.ndarray, grid_h: int = 4, grid_w: int = 4
) -> List[List[Tuple[int, int, int]]]:
    """Extract dominant color per grid cell."""
    h, w, _ = arr.shape
    cell_h = h // grid_h
    cell_w = w // grid_w
    colors = []
    for gy in range(grid_h):
        row = []
        for gx in range(grid_w):
            y0, y1 = gy * cell_h, (gy + 1) * cell_h
            x0, x1 = gx * cell_w, (gx + 1) * cell_w
            cell = arr[y0:y1, x0:x1]
            r = int(np.median(cell[:, :, 0]))
            g = int(np.median(cell[:, :, 1]))
            b = int(np.median(cell[:, :, 2]))
            row.append((r, g, b))
        colors.append(row)
    return colors


def find_regions(grid: List[List[Tuple[int, int, int]]], threshold: int = 50) -> List[dict]:
    """Find connected regions of similar color."""
    gh = len(grid)
    gw = len(grid[0])
    visited = [[False] * gw for _ in range(gh)]
    regions = []

    for gy in range(gh):
        for gx in range(gw):
            if visited[gy][gx]:
                continue
            seed = grid[gy][gx]
            queue = [(gy, gx)]
            visited[gy][gx] = True
            cells = []
            while queue:
                cy, cx = queue.pop(0)
                cells.append((cy, cx))
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < gh and 0 <= nx < gw and not visited[ny][nx]:
                        diff = sum((a - b) ** 2 for a, b in zip(seed, grid[ny][nx])) ** 0.5
                        if diff < threshold:
                            visited[ny][nx] = True
                            queue.append((ny, nx))
            if cells:
                avg = tuple(int(np.mean([grid[cy][cx][k] for cy, cx in cells])) for k in range(3))
                regions.append({"cells": cells, "color": avg, "count": len(cells)})
    regions.sort(key=lambda r: r["count"], reverse=True)
    return regions


def fit_circle(points_xy: List[Tuple[float, float]]) -> Tuple[float, float, float]:
    """Least-squares circle fit to a set of 2D points."""
    if len(points_xy) < 3:
        return 0.5, 0.5, 0.0
    xs = np.array([p[0] for p in points_xy])
    ys = np.array([p[1] for p in points_xy])
    # Simple: bounding box center + average radius
    cx = (xs.min() + xs.max()) / 2
    cy = (ys.min() + ys.max()) / 2
    radii = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    r = float(np.mean(radii))
    return float(cx), float(cy), r


def extract_arcs_from_edges(arr: np.ndarray, grid_size: int = 4, max_arcs: int = 3) -> List[Arc]:
    """Extract curved arcs from edge curvature analysis."""
    gray = np.mean(arr, axis=2).astype(np.uint8)
    pil = Image.fromarray(gray)
    edges = pil.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edges)

    h, w = arr.shape[:2]
    coords = np.argwhere(edge_arr > 25)
    if len(coords) < 10:
        return []

    # Divide edge pixels into angular sectors around center
    center_y, center_x = h / 2, w / 2
    angles = np.arctan2(coords[:, 0] - center_y, coords[:, 1] - center_x)

    # Find sectors with high curvature (many edges in a small angular range)
    n_sectors = 12
    sector_edges = []
    for i in range(n_sectors):
        a0 = -math.pi + i * (2 * math.pi / n_sectors)
        a1 = a0 + 2 * math.pi / n_sectors
        mask = (angles >= a0) & (angles < a1)
        sector_coords = coords[mask]
        if len(sector_coords) >= 5:
            # Compute curvature: variance of distances from center
            dists = np.sqrt(
                (sector_coords[:, 0] - center_y) ** 2 + (sector_coords[:, 1] - center_x) ** 2
            )
            mean_dist = np.mean(dists) / min(h, w)
            mean_angle = (a0 + a1) / 2
            # Sample color
            mid_idx = len(sector_coords) // 2
            ry, rx = sector_coords[mid_idx]
            color = (int(arr[ry, rx, 0]), int(arr[ry, rx, 1]), int(arr[ry, rx, 2]))
            sector_edges.append((mean_angle, mean_dist, color))

    # Create arcs from consecutive sectors
    arcs = []
    for i in range(min(max_arcs, len(sector_edges) - 1)):
        a1, r1, c1 = sector_edges[i]
        a2, r2, c2 = sector_edges[i + 1]
        r_avg = (r1 + r2) / 2
        cx, cy = 0.5, 0.5
        arcs.append(Arc(cx, cy, r_avg, a1, a2, 0.015, c1))

    return arcs


def decompose_spatial(
    img_arr: np.ndarray, grid_size: int = 6, color_threshold: int = 50
) -> DrawingInstructions:
    arr = img_arr.astype(np.float32)
    h, w = arr.shape[:2]

    g_colors = grid_colors(arr, grid_size, grid_size)
    regions = find_regions(g_colors, threshold=color_threshold)

    planes, circles = _extract_planes_and_circles(
        arr, g_colors, regions, h, w, grid_size, color_threshold
    )
    points = _extract_boundary_points(arr, regions, h, w, grid_size)
    lines = _extract_edge_lines(arr, h, w)
    arcs = extract_arcs_from_edges(arr, grid_size, max_arcs=3)

    bg_color = regions[0]["color"] if regions else (128, 128, 128)

    return DrawingInstructions(
        points=points[:15],
        lines=lines[:10],
        planes=planes[:5],
        circles=circles[:4],
        arcs=arcs[:3],
        background_color=bg_color,
    )


def _extract_planes_and_circles(arr, g_colors, regions, h, w, grid_size, color_threshold):
    cell_h = h / grid_size
    cell_w = w / grid_size
    planes = []
    circles = []
    for region in regions[:6]:
        cells = region["cells"]
        color = region["color"]
        if len(cells) < 2:
            continue
        min_y = min(cy for cy, cx in cells)
        max_y = max(cy for cy, cx in cells)
        min_x = min(cx for cy, cx in cells)
        max_x = max(cx for cy, cx in cells)
        nx0 = min_x * cell_w / w
        ny0 = min_y * cell_h / h
        nx1 = (max_x + 1) * cell_w / w
        ny1 = (max_y + 1) * cell_h / h
        planes.append(
            Plane(
                [
                    Point(nx0, ny0, (0, 0, 0), 0),
                    Point(nx1, ny0, (0, 0, 0), 0),
                    Point(nx1, ny1, (0, 0, 0), 0),
                    Point(nx0, ny1, (0, 0, 0), 0),
                ],
                color,
                (0, 0, 0),
                0.01,
            )
        )
        pts = [((cx + 0.5) * cell_w / w, (cy + 0.5) * cell_h / h) for cy, cx in cells]
        ccx, ccy, cr = fit_circle(pts)
        if cr > 0.02:
            circles.append(Circle(ccx, ccy, cr, color, (0, 0, 0), 0.0))
    return planes, circles


def _extract_boundary_points(arr, regions, h, w, grid_size):
    cell_h = h / grid_size
    cell_w = w / grid_size
    points = []
    for region in regions[:5]:
        cells = region["cells"]
        color = region["color"]
        for cy, cx in cells:
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = cy + dy, cx + dx
                if ny < 0 or ny >= grid_size or nx < 0 or nx >= grid_size:
                    px = (cx + 0.5) * cell_w / w
                    py = (cy + 0.5) * cell_h / h
                    points.append(Point(px, py, color, 0.04))
                    break
    return points


def _extract_edge_lines(arr, h, w):
    from PIL import ImageFilter

    gray = np.mean(arr, axis=2).astype(np.uint8)
    edge_img = Image.fromarray(gray).filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edge_img)
    edge_coords = np.argwhere(edge_arr > 20)
    lines = []
    if len(edge_coords) > 5:
        center_y, center_x = h / 2, w / 2
        angles = np.arctan2(edge_coords[:, 0] - center_y, edge_coords[:, 1] - center_x)
        sorted_idx = np.argsort(angles)
        n_lines = min(10, len(edge_coords) // 4)
        sector_size = max(1, len(edge_coords) // n_lines)
        prev = None
        for i in range(n_lines):
            start = i * sector_size
            end = min(start + sector_size, len(edge_coords))
            sector = edge_coords[sorted_idx[start:end]]
            cy = float(np.mean(sector[:, 0])) / h
            cx = float(np.mean(sector[:, 1])) / w
            ry, rx = int(np.mean(sector[:, 0])), int(np.mean(sector[:, 1]))
            color = (
                int(arr[min(ry, h - 1), min(rx, w - 1), 0]),
                int(arr[min(ry, h - 1), min(rx, w - 1), 1]),
                int(arr[min(ry, h - 1), min(rx, w - 1), 2]),
            )
            if prev is not None:
                lines.append(
                    Line(
                        Point(prev[0], prev[1], color, 0.03),
                        Point(cx, cy, color, 0.03),
                        0.015,
                        color,
                    )
                )
            prev = (cx, cy, color)
    return lines


if __name__ == "__main__":
    import json

    data_dir = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "..",
        "..",
        "data",
        "multimodal",
        "cifar10",
    )
    idx = json.load(open(os.path.join(data_dir, "index.json")))

    for cls in idx["classes"][:5]:
        cls_dir = os.path.join(data_dir, cls)
        f = sorted(os.listdir(cls_dir))[0]
        img = np.load(os.path.join(cls_dir, f))
        instr = decompose_spatial(img)
        vec = instr.to_vector()
        nz = np.count_nonzero(vec)
        print(
            f"{cls}: {len(instr.points)}pts {len(instr.lines)}lines {len(instr.planes)}planes {len(instr.circles)}circles {len(instr.arcs)}arcs vec={len(vec)} nonzero={nz}"
        )
