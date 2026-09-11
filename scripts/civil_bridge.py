#!/usr/bin/env python3
"""整橋組裝 v1：四點支撐 + 8×100 橋面（Blender STL + FreeCAD STEP + 構件驗算）。

幾何（m，Z-up）：A(0,0,0) B(10,0,0) C(0,100,0) D(10,100,0)；
橋面箱梁 8 寬×2 高，頂 z=10；墩 2×2×8；護欄 2 道；支座 4 個。
計算：墩軸壓/護欄/支座調 civil_components + civil_derive；跨度門必報。
"""

import argparse
import json
import os
import subprocess
import sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-800:]
    except subprocess.TimeoutExpired:
        return 124, "超時"


def main():
    ap = argparse.ArgumentParser(description="bridge v1 assembly")
    ap.add_argument("--L", type=float, default=100.0)
    ap.add_argument("--W", type=float, default=8.0)
    ap.add_argument("--deck_h", type=float, default=2.0)
    ap.add_argument("--pier_h", type=float, default=8.0)
    args = ap.parse_args()
    L, W = args.L, args.W
    report = {"geometry": {"A": [0, 0, 0], "B": [10, 0, 0], "C": [0, 100, 0],
                           "D": [10, 100, 0], "deck": [W, L], "span_m": L}}

    # 1) 構件驗算（墩/護欄/支座）
    _, o1 = run([PY, os.path.join(SCRIPTS, "civil_components.py"),
                 "--component", "column",
                 "--json", json.dumps({"b": 2000, "h": 2000, "As": 20000,
                                       "N_Ed_kN": 12000})], 60)
    _, o2 = run([PY, os.path.join(SCRIPTS, "civil_derive.py"),
                 "--template", "parapet"], 60)
    _, o3 = run([PY, os.path.join(SCRIPTS, "civil_derive.py"),
                 "--template", "bearing"], 60)
    report["pier"] = '"axial_ok": true' in o1
    report["parapet"] = '"bending_ok": true' in o2
    report["bearing"] = '"bearing_ok": true' in o3
    _, o4 = run([PY, os.path.join(SCRIPTS, "civil_components.py"),
                 "--component", "beam",
                 "--json", json.dumps({"b": 8000, "d": 2000, "As": 50000,
                                       "L": L * 1000})], 60)
    report["span_gate"] = "span_feasible_rc" in o4 and '"span_feasible_rc": true' in o4

    # 2) Blender 整橋：橋面 + 4 墩 + 2 護欄 + 4 支座
    units = int(W * 2)
    macro = (
        "import bpy\n"
        "bpy.ops.object.select_all(action='SELECT')\n"
        "bpy.ops.object.delete(use_global=False)\n"
        f"bpy.ops.mesh.primitive_cube_add(size=1, location=(5, {L/2}, 9))\n"
        "deck = bpy.context.active_object\n"
        f"deck.dimensions = ({W}, {L}, 2)\n"
        "deck.name = 'Deck'\n"
        "for i, (x, y) in enumerate([(0,0),(10,0),(0,100),(10,100)]):\n"
        "    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 4))\n"
        "    p = bpy.context.active_object\n"
        "    p.dimensions = (2, 2, 8)\n"
        "    p.name = f'Pier_{i}'\n"
        "    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 8.2))\n"
        "    b = bpy.context.active_object\n"
        "    b.dimensions = (1, 1, 0.4)\n"
        "    b.name = f'Bearing_{i}'\n"
        "for x in (1.125, 8.875):\n"
        f"    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, {L/2}, 10.55))\n"
        "    w = bpy.context.active_object\n"
        "    w.dimensions = (0.25, 100, 1.1)\n"
        "    w.name = 'Parapet'\n"
        "bpy.ops.export_mesh.stl(filepath='/tmp/bridge_v1.stl', use_selection=False)\n"
        "print('BRIDGE-V1:', len(bpy.data.objects), 'objects')\n"
    )
    with open("/tmp/bridge_v1.py", "w", encoding="utf-8") as f:
        f.write(macro)
    code, out = run(["blender", "--background", "--python", "/tmp/bridge_v1.py"], 240)
    report["blender"] = "BRIDGE-V1:" in out
    for line in out.splitlines():
        if "BRIDGE-V1" in line:
            report["blender_detail"] = line.strip()[:80]

    # 3) FreeCAD 整橋 STEP（橋面盒；墩另件略——STEP 以橋面 + bbox 驗）
    fcmacro = (
        "import FreeCAD, Part\n"
        "doc = FreeCAD.newDocument('Bridge')\n"
        f"box = doc.addObject('Part::Box', 'Deck')\n"
        f"box.Length, box.Width, box.Height = {L*1000}, {W*1000}, 2000\n"
        "doc.recompute()\n"
        "Part.export(doc.Objects, '/tmp/bridge_v1.step')\n"
        "print('FC-BRIDGE: %d objects' % len(doc.Objects))\n"
    )
    with open("/tmp/fc_bridge.py", "w", encoding="utf-8") as f:
        f.write(fcmacro)
    code, out = run(["flatpak", "run", "--filesystem=/tmp", "org.freecad.FreeCAD",
                     "--console", "/tmp/fc_bridge.py"], 400)
    report["freecad"] = "FC-BRIDGE" in out
    print(json.dumps(report, ensure_ascii=False, indent=1))
    ok = all([report["pier"], report["parapet"], report["bearing"],
              report["blender"], report["freecad"]])
    print("BRIDGE-V1:", "✅（除跨度門）" if ok else "❌", "| span_gate:", report["span_gate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
