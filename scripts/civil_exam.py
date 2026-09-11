#!/usr/bin/env python3
"""土木建模例題集（完成功能驗收）：每題有期望值，容差判定，全綠才算完工。

覆蓋：材料庫/梁/柱/板/箱/T/鋼/預力/護欄/支座/跨度門/DXF/handler定尺寸。
重型（Blender/FreeCAD/FEM）已單獨驗證，本表不計時重跑。
"""

import json
import subprocess
import sys

PY = sys.executable
SCRIPTS = __import__("os").path.dirname(__file__)
PASS, FAIL = "✅", "❌"


def sh(*args, timeout=120):
    p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    o = p.stdout
    return json.loads(o[o.index("{"):o.rindex("}") + 1])


def close(a, b, tol):
    return abs(a - b) <= tol


results = []


def exam(name, ok, detail=""):
    results.append(ok)
    print(f"{PASS if ok else FAIL} {name} {detail}")


def main():
    db = None
    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "beam",
           "--json", json.dumps({"b": 300, "d": 450, "As": 1256}))
    exam("beam M_Rd=220.9", close(r["M_Rd_kNm"], 220.9, 0.5), str(r["M_Rd_kNm"]))

    p = subprocess.run([PY, f"{SCRIPTS}/civil_autosize.py", "--component", "beam",
                        "--vary", "As",
                        "--json", json.dumps({"b": 300, "d": 500, "M_Ed_kNm": 400})],
                       capture_output=True, text=True, timeout=120)
    o = p.stdout
    r = json.loads(o[o.index("{"):o.rindex("}") + 1])
    exam("autosize As≈2186", r.get("ok") and close(r.get("As", 0), 2186, 60),
         str(r.get("As")))

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "column",
           "--json", json.dumps({"b": 300, "h": 300, "As": 1608}))
    exam("column N_Rd=2139", close(r["N_Rd_kN"], 2139, 3), str(r["N_Rd_kN"]))

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "slab",
           "--json", json.dumps({"h": 150, "As": 500}))
    exam("slab As_min=188", close(r["As_min_mm2_per_m"], 188, 3),
         str(r["As_min_mm2_per_m"]))

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "box",
           "--json", json.dumps({"B": 8000, "H": 2000}))
    exam("box self=122.5", close(r["self_weight_kN_m"], 122.5, 0.5),
         str(r["self_weight_kN_m"]))

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "tbeam",
           "--json", json.dumps({"bw": 300, "hf": 150, "l0": 20000, "bi": 2000,
                                 "d": 500, "As": 2000, "M_Ed_kNm": 400}))
    exam("tbeam beff=4300&M=430.4",
         close(r["beff_mm"], 4300, 5) and close(r["M_Rd_kNm"], 430.4, 1.0),
         f"{r['beff_mm']}/{r['M_Rd_kNm']}")

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "steel",
           "--json", json.dumps({"A": 7600, "Iy": 45900000, "L": 5000}))
    exam("steel Nb=1715",
         close(r["N_b_Rd_kN"], 1715, 3) and close(r["chi"], 0.636, 0.005),
         f"{r['N_b_Rd_kN']}/{r['chi']}")

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "prestressed",
           "--conc", "C40/50",
           "--json", json.dumps({"b": 1000, "h": 1500, "P_kN": 12000,
                                 "e_mm": 500, "M_kNm": 8000}))
    exam("prestressed ok", r.get("stress_ok") is True,
         f"{r.get('sigma_top_MPa')}/{r.get('sigma_bot_MPa')}")

    p = subprocess.run([PY, f"{SCRIPTS}/civil_derive.py", "--template", "parapet"],
                       capture_output=True, text=True, timeout=60)
    exam("parapet As=194.7", '"As_req": 194.7' in p.stdout, "derive")

    p = subprocess.run([PY, f"{SCRIPTS}/civil_derive.py", "--template", "bearing"],
                       capture_output=True, text=True, timeout=60)
    exam("bearing sigma=12.5", '"sigma": 12.5' in p.stdout, "derive")

    r = sh(PY, f"{SCRIPTS}/civil_components.py", "--component", "beam",
           "--json", json.dumps({"b": 8000, "d": 2000, "As": 50000, "L": 100000}))
    exam("span gate false", r.get("span_feasible_rc") is False,
         str(r.get("span_depth_ratio")))

    p = subprocess.run([PY, f"{SCRIPTS}/civil_dxf.py"], capture_output=True,
                       text=True, timeout=60)
    exam("dxf 4CIRCLE", "CIRCLE 4" in p.stdout, "reflux")

    p = subprocess.run(
        [PY, "-c",
         "import sys,asyncio;sys.path.insert(0,'apps/backend/src');"
         "from services.handlers.civil_model_handler import CivilModelHandler;"
         "print(asyncio.run(CivilModelHandler().handle('梁配筋設計 M_Ed=400 b=300 d=500')))"],
        capture_output=True, text=True, timeout=120, cwd=".",
    )
    exam("handler sizing As=2186", "As=2186" in p.stdout, "chat path")

    n, ok = len(results), sum(results)
    print(f"例題：{ok}/{n} = {ok/n:.0%}")
    return 0 if ok == n else 1


if __name__ == "__main__":
    raise SystemExit(main())
