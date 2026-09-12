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


def box_girder(db, conc="C30/37", steel="B500B", B=8000.0, H=2000.0,
               tw=300.0, tf_top=250.0, tf_bot=250.0, As=20000.0, M_Ed_kNm=0.0):
    """空心箱梁（橋面本體）：截面特性 + 自重 + 彎矩概算。"""
    C, S, K = db["concrete"][conc], db["rebar"][steel], db["constants"]
    fcd, fyd = C["fck_MPa"] / K["gamma_c"], S["fyk_MPa"] / K["gamma_s"]
    bi, hi = B - 2 * tw, H - tf_top - tf_bot
    A = B * H - bi * hi
    I = (B * H ** 3 - bi * hi ** 3) / 12.0
    W = I / (H / 2.0)
    self_w = A * K["concrete_unit_weight_kN_m3"] / 1e6
    d = H - tf_bot - 100.0
    z = 0.9 * d
    MRd = As * fyd * z / 1e6
    out = {"A_mm2": round(A, 0), "I_mm4": round(I, 0), "W_mm3": round(W, 0),
           "self_weight_kN_m": round(self_w, 1), "M_Rd_kNm": round(MRd, 0),
           "assumptions": ["thin-wall box", "z=0.9d approx", "no shear lag/torsion"]}
    if M_Ed_kNm:
        out["bending_ok"] = bool(MRd >= M_Ed_kNm)
    return out


def t_beam(db, conc="C30/37", steel="B500B", bw=300.0, hf=150.0, l0=20000.0,
           bi=2000.0, d=500.0, As=2000.0, M_Ed_kNm=0.0):
    """T 梁（含 EC2 有效翼緣 beff）：中性軸在翼緣內按矩形計，否則告警。"""
    C, S, K = db["concrete"][conc], db["rebar"][steel], db["constants"]
    fcd, fyd = C["fck_MPa"] / K["gamma_c"], S["fyk_MPa"] / K["gamma_s"]
    beff_i = min(0.2 * bi + 0.1 * l0, 0.2 * l0, bi)
    beff = bw + 2 * beff_i
    x = As * fyd / (0.8 * beff * fcd)
    out = {"beff_mm": round(beff, 0), "x_mm": round(x, 1),
           "assumptions": ["EC2 beff", "NA-in-flange only"]}
    if x > hf:
        out["warning"] = "中性軸出翼緣，真T梁另算（排隊）"
        out["M_Rd_kNm"] = 0.0
    else:
        z = d - 0.4 * x
        MRd = As * fyd * z / 1e6
        out["M_Rd_kNm"] = round(MRd, 1)
        if M_Ed_kNm:
            out["bending_ok"] = bool(MRd >= M_Ed_kNm)
    return out


def steel_member(db, grade="S355", A=7600.0, Iy=45.9e6, L=5000.0,
                 N_Ed_kN=0.0, curve_alpha=0.49):
    """鋼桁桿件（EC3）：受拉 A·fy/γM0；受壓歐拉+χ 折減（曲線 c，α=0.49）。"""
    S, K = db["structural_steel"][grade], db["constants"]
    fy, E = S["fy_MPa"], K["steel_E_MPa"]
    Nt = A * fy / K["gamma_M0"] / 1000.0
    Ncr = (3.14159265 ** 2) * E * Iy / L ** 2 / 1000.0
    lam = (A * fy / (Ncr * 1000.0)) ** 0.5
    phi = 0.5 * (1 + curve_alpha * (lam - 0.2) + lam ** 2)
    chi = 1.0 / (phi + (phi ** 2 - lam ** 2) ** 0.5)
    Nb = chi * A * fy / K["gamma_M1"] / 1000.0
    out = {"N_t_Rd_kN": round(Nt, 0), "N_b_Rd_kN": round(Nb, 0),
           "lambda_bar": round(lam, 3), "chi": round(chi, 3),
           "assumptions": ["EC3 curve c", "pinned-pinned", "single axis"]}
    if N_Ed_kN:
        out["tension_ok"] = bool(Nt >= abs(N_Ed_kN))
        out["buckling_ok"] = bool(Nb >= abs(N_Ed_kN))
    return out


def prestressed(db, conc="C40/50", b=1000.0, h=1500.0, P_kN=12000.0,
                e_mm=500.0, M_kNm=8000.0):
    """預力梁使用階段應力（P/A ± (M−P·e)/W；壓<0.6fck，拉<fctm）。"""
    C, K = db["concrete"][conc], db["constants"]
    fck, fctm = C["fck_MPa"], C["fctm_MPa"]
    A = b * h
    W = b * h ** 2 / 6.0
    pm = P_kN * 1000.0 / A
    bm = (M_kNm * 1e6 - P_kN * 1000.0 * e_mm) / W
    s_top, s_bot = -pm + bm, -pm - bm
    out = {"sigma_top_MPa": round(s_top, 2), "sigma_bot_MPa": round(s_bot, 2),
           "lim_comp_MPa": round(0.6 * fck, 1), "lim_tens_MPa": round(fctm, 2),
           "assumptions": ["uncracked", "no losses split (use effective P)"]}
    out["stress_ok"] = bool(s_top <= fctm and s_bot <= fctm
                            and s_top >= -0.6 * fck and s_bot >= -0.6 * fck)
    return out


def main():
    ap = argparse.ArgumentParser(description="civil component templates × materials DB")
    ap.add_argument("--component", choices=["beam", "column", "slab", "box", "tbeam",
                                            "steel", "prestressed"],
                    required=True)
    ap.add_argument("--conc", default="C30/37")
    ap.add_argument("--steel", default="B500B")
    ap.add_argument("--json", default="", help="extra inputs as JSON (b,d,As,M_Ed_kNm,...)")
    args = ap.parse_args()
    db = load_db()
    kw = json.loads(args.json) if args.json else {}
    kw.pop("grade", None)
    kw.pop("conc", None)
    kw.pop("steel", None)
    fn = {"beam": beam, "column": column, "slab": slab,
          "box": box_girder, "tbeam": t_beam,
          "steel": steel_member, "prestressed": prestressed}[args.component]
    if args.component == "steel":
        grade = args.steel if args.steel in db["structural_steel"] else "S355"
        print(json.dumps(fn(db, grade=grade, **kw), ensure_ascii=False, indent=1))
    elif args.component == "prestressed":
        print(json.dumps(fn(db, conc=args.conc, **kw), ensure_ascii=False, indent=1))
    else:
        print(json.dumps(fn(db, conc=args.conc, steel=args.steel, **kw),
                         ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
