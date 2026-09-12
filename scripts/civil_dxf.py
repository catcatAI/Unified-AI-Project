#!/usr/bin/env python3
"""梁配筋截面 DXF（計算結果→2D 圖紙，FreeCAD/LibreCAD 可開）。

輸入：b/d（mm）、鋼筋（n 根、直徑、保護層）、標註（M_Rd/材料）。
輸出：data/.cache/beam_section.dxf（git 忽略）。回流驗證：讀回計圖元。
"""

import argparse
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "data", ".cache", "beam_section.dxf")


def main():
    import ezdxf

    ap = argparse.ArgumentParser(description="beam section DXF")
    ap.add_argument("--b", type=float, default=300.0)
    ap.add_argument("--d", type=float, default=450.0)
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--dia", type=float, default=20.0)
    ap.add_argument("--cover", type=float, default=30.0)
    ap.add_argument("--label", default="C30/37 B500B M_Rd=220.9kNm")
    args = ap.parse_args()

    doc = ezdxf.new()
    msp = doc.modelspace()
    b, d = args.b, args.d
    msp.add_lwpolyline([(0, 0), (b, 0), (b, d), (0, d)], close=True)
    r = args.dia / 2
    c = args.cover + r
    xs = [c + i * (b - 2 * c) / max(args.n // 2 - 1, 1) for i in range(args.n // 2)]
    n_bar = 0
    for y in (c, d - c):
        for x in xs[: args.n // 2]:
            msp.add_circle((x, y), r)
            n_bar += 1
    if args.n % 2:
        msp.add_circle((b / 2, d / 2), r)
        n_bar += 1
    msp.add_text(args.label, height=20).set_placement((0, d + 30))
    msp.add_text(f"b={b} d={d} {args.n}-D{args.dia}", height=20).set_placement((0, -50))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc.saveas(OUT)
    print(f"DXF: {n_bar} bars + section + labels -> {OUT}")

    # 回流驗證：讀回計數
    back = ezdxf.readfile(OUT)
    m2 = back.modelspace()
    ncirc = sum(1 for _ in m2.query("CIRCLE"))
    ntxt = sum(1 for _ in m2.query("TEXT"))
    print(f"回流驗證：CIRCLE {ncirc}（期望 {n_bar}），TEXT {ntxt} {'✅' if ncirc == n_bar else '❌'}")
    return 0 if ncirc == n_bar else 1


if __name__ == "__main__":
    raise SystemExit(main())
