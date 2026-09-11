# 在 Blender 內執行：blender --background --python civil_blender.py -- --b 300 --d 450 --L 6000
# 參數化梁：箱體 + 角部縱筋（圓柱）→ 導出 STL。單位：mm 轉 m。
import argparse
import os
import sys

import bpy


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--b", type=float, default=300.0)
    ap.add_argument("--d", type=float, default=450.0)
    ap.add_argument("--L", type=float, default=6000.0)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--dia", type=float, default=20.0)
    ap.add_argument("--cover", type=float, default=30.0)
    ap.add_argument("--out", default="")
    try:
        i = sys.argv.index("--")
        args = ap.parse_args(sys.argv[i + 1:])
    except ValueError:
        args = ap.parse_args([])
    return args


def main():
    a = parse()
    sc = 0.001
    b, d, L = a.b * sc, a.d * sc, a.L * sc
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    bpy.ops.mesh.primitive_cube_add(size=1)
    box = bpy.context.active_object
    box.dimensions = (L, b, d)  # X=長，Y=寬，Z=高（Z-up）
    box.name = "Girder"
    r = a.dia / 2 * sc
    c = a.cover * sc
    ys = [-(b / 2 - c - r) + i * ((b - 2 * c - 2 * r) / max(a.n // 2 - 1, 1))
          for i in range(a.n // 2)]
    n_bar = 0
    import math
    for z in (-(d / 2 - c - r), d / 2 - c - r):
        for y in ys[: a.n // 2]:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=r, depth=L, location=(0, y, z),
                rotation=(0, math.pi / 2, 0))
            n_bar += 1
    out = a.out or "/tmp/girder.stl"
    bpy.ops.export_mesh.stl(filepath=out, use_selection=False)
    print(f"BLENDER: box + {n_bar} rebars -> {out}")
    print(f"OBJECTS: {len(bpy.data.objects)}")


main()
