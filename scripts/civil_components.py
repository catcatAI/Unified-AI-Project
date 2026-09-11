#!/usr/bin/env python3
"""土木預製件模板 × 基本面 × 輸入 — EC2 簡化式加速計算。

構件：beam（彎矩+剪力）、column（短柱軸壓）、slab（單向板 1m 帶）。
材料讀 data/materials/civil_materials.json；假設隨結果輸出。

免責：初步估算（preliminary），非施工圖依據；θ=45° 保守剪力、
短柱公式、最小配筋按 EC2 9.2.1。正式設計需持牌工程師簽證。
"""

import argparse
import json
import os
import sys

DB = os.path.join(
    os.path.dirname(__file__), "..", "data", "materials", "civil_materials.json"
)


def load_db():
    with open(DB, encoding="utf-8") as f:
        return json.load(f)


def beam(db, conc="C30/37", steel="B500B", b=300.0, d=450.0, As=1256.0,
         M_Ed_kNm=0.0, V_Ed_kN=0.0, Asw_s=0.0, L=6000.0):
    C, S, K = db["concrete"][conc], db["rebar"][steel], db["constants"]
    fcd, fyd = C["fck_MPa"] / K["gamma_c"], S["fyk_MPa"] / K["gamma_s"]
    x = As * fyd / (0.8 * b * fcd)
    z = d - 0.4 * x
    MRd = As * fyd * z / 1e6
    out = {"M_Rd_kNm": round(MRd, 1), "x_mm": round(x, 1), "z_mm": round(z, 1),
           "assumptions": ["rect stress block λ=0.8", "singly reinforced"]}
    if L and d:
        out["span_depth_ratio"] = round(L / d, 1)
        out["span_feasible_rc"] = bool(L / d <= 25)
        if L / d > 25:
            out["assumptions"].append("⚠️ L/d>25：RC 簡支梁不可行（改連續梁/鋼構/預力）")
    if M_Ed_kNm:
        As_req = M_Ed_kNm * 1e6 / (0.9 * d * fyd)
        out["As_req_mm2"] = round(As_req, 0)
        out["bending_ok"] = bool(MRd >= M_Ed_kNm)
    if V_Ed_kN:
        VRds = 0.9 * d * Asw_s * fyd / 1e3 if Asw_s else 0.0
        out["V_Rds_kN"] = round(VRds, 1)
        out["shear_ok"] = bool(VRds >= V_Ed_kN)
        out["assumptions"].append("shear θ=45° conservative")
    return out


def column(db, conc="C30/37", steel="B500B", b=300.0, h=300.0, As=1608.0, N_Ed_kN=0.0):
    C, S, K = db["concrete"][conc], db["rebar"][steel], db["constants"]
    fcd, fyd = C["fck_MPa"] / K["gamma_c"], S["fyk_MPa"] / K["gamma_s"]
    Ac = b * h
    NRd = (0.8 * Ac * fcd + As * fyd) / 1e3
    out = {"N_Rd_kN": round(NRd, 0),
           "assumptions": ["short braced column", "0.8 sustained-load factor"]}
    if N_Ed_kN:
        out["axial_ok"] = bool(NRd >= N_Ed_kN)
    return out


def slab(db, conc="C30/37", steel="B500B", h=150.0, cover=25.0,
         As=500.0, M_Ed_kNm=0.0):
    C, S, K = db["concrete"][conc], db["rebar"][steel], db["constants"]
    fcd, fyd = C["fck_MPa"] / K["gamma_c"], S["fyk_MPa"] / K["gamma_s"]
    b, d = 1000.0, h - cover
    x = As * fyd / (0.8 * b * fcd)
    z = d - 0.4 * x
    MRd = As * fyd * z / 1e6
    As_min = max(0.26 * C["fctm_MPa"] / S["fyk_MPa"] * b * d, 0.0013 * b * d)
    out = {"M_Rd_kNm_per_m": round(MRd, 1), "As_min_mm2_per_m": round(As_min, 0),
           "assumptions": ["1m strip", "EC2 9.2.1 min steel"]}
    if M_Ed_kNm:
        out["bending_ok"] = bool(MRd >= M_Ed_kNm)
    return out


def main():
    ap = argparse.ArgumentParser(description="civil component templates × materials DB")
    ap.add_argument("--component", choices=["beam", "column", "slab"], required=True)
    ap.add_argument("--conc", default="C30/37")
    ap.add_argument("--steel", default="B500B")
    ap.add_argument("--json", default="", help="extra inputs as JSON (b,d,As,M_Ed_kNm,...)")
    args = ap.parse_args()
    db = load_db()
    kw = json.loads(args.json) if args.json else {}
    fn = {"beam": beam, "column": column, "slab": slab}[args.component]
    print(json.dumps(fn(db, conc=args.conc, steel=args.steel, **kw),
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
