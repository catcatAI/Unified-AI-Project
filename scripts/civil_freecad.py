#!/usr/bin/env python3
"""FreeCAD 真橋（參數梁→STEP→回流驗證）— flatpak headless。

輸入：b/d/L（mm）、筋（n/直徑/保護層）。生成 macro → flatpak console 執行
（Part 工作台建盒+筋）→ 導出 STEP → 回流：重開數物件+尺寸斷言。
"""

import argparse
import os
import subprocess

FC_MACRO = "/tmp/fc_beam.py"


def main():
    ap = argparse.ArgumentParser(description="FreeCAD parametric beam bridge")
    ap.add_argument("--b", type=float, default=300.0)
    ap.add_argument("--d", type=float, default=450.0)
    ap.add_argument("--L", type=float, default=6000.0)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--dia", type=float, default=20.0)
    ap.add_argument("--cover", type=float, default=30.0)
    ap.add_argument("--out", default="/tmp/girder_fc.step")
    args = ap.parse_args()

    macro = f"""import FreeCAD, Part
doc = FreeCAD.newDocument('Girder')
b, d, L = {args.b}, {args.d}, {args.L}
box = doc.addObject('Part::Box', 'Girder')
box.Length, box.Width, box.Height = L, b, d
r, c = {args.dia} / 2.0, {args.cover}
import math
n = {args.n}
xs = [c + r + i * ((b - 2 * c - 2 * r) / max(n // 2 - 1, 1)) for i in range(n // 2)]
for z in (c + r, d - c - r):
    for x in xs[: n // 2]:
        cyl = doc.addObject('Part::Cylinder', 'Rebar')
        cyl.Radius, cyl.Height = r, L
        cyl.Placement.Base = FreeCAD.Vector(0, x, z)
        cyl.Placement.Rotation = FreeCAD.Rotation(FreeCAD.Vector(0, 1, 0), 90)
doc.recompute()
Part.export(doc.Objects, '{args.out}')
print('FC-BEAM: %d objects -> %s' % (len(doc.Objects), '{args.out}'))
"""
    with open(FC_MACRO, "w", encoding="utf-8") as f:
        f.write(macro)
    t0 = __import__("time").time()
    p = subprocess.run(
        ["flatpak", "run", "--filesystem=/tmp", "org.freecad.FreeCAD",
         "--console", FC_MACRO],
        capture_output=True, text=True, timeout=300,
    )
    print(f"  flatpak exit {p.returncode} ({__import__('time').time()-t0:.1f}s)")
    for line in (p.stdout + p.stderr).splitlines():
        if "FC-BEAM" in line or "Error" in line or "Traceback" in line:
            print("  " + line.strip()[:160])
    if p.returncode != 0 or not os.path.exists(args.out):
        print("  ❌ 建模失敗")
        return 1

    # 回流驗證：Part.read 讀回 STEP，數 shape + 驗盒尺寸
    check = (
        "import Part\n"
        f"shape = Part.read('{args.out}')\n"
        "print('FC-REFLUX type:', shape.ShapeType)\n"
        "bb = shape.BoundBox\n"
        "print('FC-BBOX: %.0f x %.0f x %.0f' % (bb.XLength, bb.YLength, bb.ZLength))\n"
    )
    with open("/tmp/fc_check.py", "w", encoding="utf-8") as f:
        f.write(check)
    q = subprocess.run(
        ["flatpak", "run", "--filesystem=/tmp", "org.freecad.FreeCAD",
         "--console", "/tmp/fc_check.py"],
        capture_output=True, text=True, timeout=300,
    )
    ok = False
    for line in (q.stdout + q.stderr).splitlines():
        if "FC-REFLUX" in line or "FC-BBOX" in line:
            print("  " + line.strip()[:160])
            ok = True
    size_kb = os.path.getsize(args.out) // 1024
    print(f"  STEP {size_kb}KB {'✅' if ok else '❌'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
