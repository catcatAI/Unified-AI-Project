#!/usr/bin/env python3
"""視圖與平面圖（從 .blend 落盤檔開——視圖必與模型同一數據源）。

三視圖+等軸測（EEVEE 首選，失敗轉 Cycles CPU）+ 平面 DXF（橋面輪廓+墩+梯位+尺寸）。
用法：civil_views.py --blend /tmp/footbridge.blend --outdir data/.cache/views
"""

import argparse
import math
import os
import subprocess
import sys


def run(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-1500:]
    except subprocess.TimeoutExpired:
        return 124, "超時"


RENDER_MACRO = """
import bpy, math, sys
blend, outdir, cx, cy, cz, dist = sys.argv[-6:]
cx, cy, cz, dist = float(cx), float(cy), float(cz), float(dist)
bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.resolution_x = 640
scene.render.resolution_y = 480
scene.render.film_transparent = False
try:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
except Exception:
    pass
try:
    scene.render.engine = 'BLENDER_EEVEE'
except Exception:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        prefs.preferences.compute_device_type = 'NONE'
bpy.ops.object.light_add(type='SUN', location=(cx - dist, cy - dist, cz + dist))
cam_data = bpy.data.cameras.new('ViewCam')
cam = bpy.data.objects.new('ViewCam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
# Track-to 空物體鎖定目標——免手算旋轉
trk = bpy.data.objects.new('TrackTarget', None)
scene.collection.objects.link(trk)
trk.location = (cx, cy, cz)
con = cam.constraints.new('TRACK_TO')
con.target = trk
con.track_axis = 'TRACK_NEGATIVE_Z'
con.up_axis = 'UP_Y'
views = {
    'front': (cx, cy - dist, cz),
    'top': (cx, cy, cz + dist),
    'side': (cx - dist, cy, cz),
    'iso': (cx - dist, cy - dist, cz + dist),
}
import os as _os
for name, loc in views.items():
    cam.location = loc
    bpy.context.view_layer.update()
    scene.render.filepath = _os.path.join(outdir, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER-OK:', name)
"""


def main():
    ap = argparse.ArgumentParser(description="views + plan from .blend")
    ap.add_argument("--blend", required=True)
    ap.add_argument("--outdir", default="data/.cache/views")
    ap.add_argument("--center", default="0,0,2.5")
    ap.add_argument("--dist", type=float, default=40.0)
    ap.add_argument("--plan", default="", help="plan JSON: deck/piers/stairs rects")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    macro = "/tmp/civil_views_macro.py"
    with open(macro, "w", encoding="utf-8") as f:
        f.write(RENDER_MACRO)
    cx, cy, cz = args.center.split(",")
    code, out = run(["blender", "--background", "--python", macro, "--",
                     args.blend, os.path.abspath(args.outdir), cx, cy, cz,
                     str(args.dist)], 600)
    n_ok = out.count("RENDER-OK:")
    print(f"視圖：{n_ok}/4")
    for line in out.splitlines():
        if "RENDER-OK" in line or "Error" in line:
            print("  " + line.strip()[:100])
    if args.plan:
        import json as _json
        import ezdxf

        spec = _json.loads(args.plan)
        doc = ezdxf.new()
        msp = doc.modelspace()
        for r in spec.get("rects", []):
            x, y, w, h = r["x"], r["y"], r["w"], r["h"]
            msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)],
                               close=True)
            if r.get("label"):
                msp.add_text(r["label"], height=0.8).set_placement((x, y + h + 0.5))
        for d in spec.get("dims", []):
            msp.add_linear_dim(base=(d["x"], d["y"]), p1=tuple(d["p1"]),
                               p2=tuple(d["p2"])).render()
        path = os.path.join(args.outdir, "plan.dxf")
        doc.saveas(path)
        back = ezdxf.readfile(path)
        n_ent = sum(1 for _ in back.modelspace())
        print(f"平面圖：{n_ent} 圖元 -> {path} ✅")
    return 0 if n_ok == 4 else 1


if __name__ == "__main__":
    raise SystemExit(main())
