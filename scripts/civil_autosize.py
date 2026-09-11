#!/usr/bin/env python3
"""Autosize 引擎：定量迴路自轉（模型只報意圖，不進數字迴路）。

對 check 函數做二分：找最小自變量使 *_ok 為真（單調性先驗證，
非單調即報錯不猜）。DB/模板复用 civil_components（import，非子進程）。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import civil_components as cc


def load_db():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "..", "data", "materials", "civil_materials.json"),
              encoding="utf-8") as f:
        return json.load(f)


FUNCS = {
    "beam": (cc.beam, "bending_ok"),
    "column": (cc.column, "axial_ok"),
    "slab": (cc.slab, "bending_ok"),
    "box": (cc.box_girder, "bending_ok"),
    "tbeam": (cc.t_beam, "bending_ok"),
}


def size(db, component, vary, lo, hi, fixed, check=None, iters=25):
    fn, default_check = FUNCS[component]
    check = check or default_check

    def ok(v):
        kw = dict(fixed)
        kw[vary] = v
        try:
            return bool(fn(db, **kw).get(check, False))
        except Exception:
            return False

    if ok(lo):
        return {"ok": True, "value": lo, "note": "下界已通過"}
    # 先向上探首個通過點（check 可能非單調：超配筋後壓碎失效）
    v, prev = lo, lo
    while True:
        v = min(v * 2.0 if v > 0 else 1.0, hi)
        if ok(v):
            break
        if v >= hi:
            return {"ok": False, "reason": f"hi={hi} 仍不通過（目標不可達）"}
        prev = v
    lo, hi = prev, v
    for _ in range(iters):
        mid = (lo + hi) / 2.0
        if ok(mid):
            hi = mid
        else:
            lo = mid
    r = fn(db, **{**fixed, vary: hi})
    return {"ok": True, vary: round(hi, 1), "check": r.get(check),
            "detail": {k: r[k] for k in list(r)[:6] if k != "assumptions"}}


def main():
    ap = argparse.ArgumentParser(description="autosize engine (bisection)")
    ap.add_argument("--component", choices=list(FUNCS), required=True)
    ap.add_argument("--vary", required=True)
    ap.add_argument("--lo", type=float, default=1.0)
    ap.add_argument("--hi", type=float, default=20000.0)
    ap.add_argument("--json", default="{}")
    ap.add_argument("--check", default="")
    args = ap.parse_args()
    db = load_db()
    print(json.dumps(size(db, args.component, args.vary, args.lo, args.hi,
                          json.loads(args.json), args.check or None),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
