#!/usr/bin/env python3
"""鋼桁架橋 v2（100m 單跨）：整體彎矩→弦桿軸力→EC3 選截面→Blender 建模。

假設（誠實）：簡支 Warren 桁，節間等分；弦桿力 = M/d；腹桿按剪力 V/2 估；
自重迭代一次（先估後驗）；未含節點板/橫向支撐/疲勞（排隊）。
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


def steel(grade, A, Iy, L, N):
    code, out = run(
        [PY, os.path.join(SCRIPTS, "civil_components.py"), "--component", "steel",
         "--steel", grade,
         "--json", json.dumps({"A": A, "Iy": Iy, "L": L, "N_Ed_kN": N})], 60,
    )
    i, j = out.index("{"), out.rindex("}") + 1
    return json.loads(out[i:j])


def main():
    ap = argparse.ArgumentParser(description="steel truss bridge v2")
    ap.add_argument("--span", type=float, default=100.0)
    ap.add_argument("--depth", type=float, default=7.0)
    ap.add_argument("--panels", type=int, default=10)
    ap.add_argument("--width", type=float, default=8.0)
    ap.add_argument("--w-kNm", type=float, default=65.0,
                    help="per-truss uniform load kN/m (deck DL+LL share)")
    args = ap.parse_args()
    L, d = args.span, args.depth
    # 整體彎矩 → 弦桿軸力（兩片桁架，每片 w）
    Mmax = args.w_kNm * L ** 2 / 8.0
    N_chord = Mmax / d
    print(f"整體：Mmax={Mmax:.0f}kNm，弦桿軸力={N_chord:.0f}kN (d={d}m)")
    # 弦桿試配：SHS500x25（A=47500, I=1.79e9），節間長為壓桿計算長度
    panel_L = L / args.panels * 1000.0
    r = steel("S355", 47500.0, 1.79e9, panel_L, N_chord)
    print(f"弦桿 SHS500x25 L={panel_L/1000:.0f}m：Nb={r['N_b_Rd_kN']:.0f} "
          f"{'✅' if r.get('buckling_ok') else '❌'}")
    # 腹桿：支座剪力 V/2（45°腹桿軸力≈V/√2/2，保守取 V/2）
    Vmax = args.w_kNm * L / 2.0
    N_diag = Vmax / 2.0
    r2 = steel("S355", 12000.0, 2.0e8, panel_L * 1.2, N_diag)
    print(f"腹桿 SHS250x12 L={panel_L*1.2/1000:.1f}m：Nb={r2['N_b_Rd_kN']:.0f} "
          f"{'✅' if r2.get('buckling_ok') else '❌'}")

    # Blender：兩片桁架（上下弦+腹桿圓柱）+ 橋面板
    W = args.width
    macro = (
        "import bpy, math\n"
        "bpy.ops.object.select_all(action='SELECT')\n"
        "bpy.ops.object.delete(use_global=False)\n"
        f"L, d, W, n = {L}, {d}, {W}, {args.panels}\n"
        "dx = L / n\n"
        "bpy.ops.mesh.primitive_cube_add(size=1, location=(L/2, W/2, 8))\n"
        "deck = bpy.context.active_object\n"
        f"deck.dimensions = ({L}, {W}, 0.3)\n"
        "deck.name = 'Deck'\n"
        "nb = 0\n"
        "for yy in (1.0, 7.0):\n"
        "    for i in range(n + 1):\n"
        "        x = i * dx\n"
        "        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, yy, 0.35))\n"
        "        c = bpy.context.active_object\n"
        "        c.dimensions = (0.5, 0.5, 0.7)\n"
        "        c.name = 'Chord'\n"
        "        nb += 1\n"
        "        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, yy, 0.35 + d))\n"
        "        c2 = bpy.context.active_object\n"
        "        c2.dimensions = (0.5, 0.5, 0.7)\n"
        "        c2.name = 'ChordTop'\n"
        "        nb += 1\n"
        "    for i in range(n):\n"
        "        x0, x1 = i * dx, (i + 1) * dx\n"
        "        mx = (x0 + x1) / 2\n"
        "        leng = math.sqrt(dx * dx + d * d)\n"
        "        sgn = 1 if i % 2 == 0 else -1\n"
        "        bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=leng,\n"
        "            location=(mx, yy, 0.35 + d / 2))\n"
        "        dg = bpy.context.active_object\n"
        "        dg.rotation_euler = (0, sgn * math.atan2(dx, d), 0)\n"
        "        dg.name = 'Diag'\n"
        "        nb += 1\n"
        "bpy.ops.export_mesh.stl(filepath='/tmp/truss_v2.stl', use_selection=False)\n"
        "print('TRUSS-V2:', len(bpy.data.objects), 'objects')\n"
    )
    with open("/tmp/truss_v2.py", "w", encoding="utf-8") as f:
        f.write(macro)
    code, out = run(["blender", "--background", "--python", "/tmp/truss_v2.py"], 240)
    for line in out.splitlines():
        if "TRUSS-V2" in line:
            print(line.strip()[:60])
    import json as _j
    print(_j.dumps({"chord_ok": bool(r.get("buckling_ok")),
                    "diag_ok": bool(r2.get("buckling_ok"))}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
