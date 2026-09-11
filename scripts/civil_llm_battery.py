#!/usr/bin/env python3
"""小模型工程題庫（5 題）：無示例值 + 打回兩輪，對照手算答案。

Q1 梁彎矩（手算 2044）/ Q2 柱軸壓（手算 1287）/ Q3 剪力箍筋（手算 0.85）
Q4 護欄遷移（手算 195，±安全側判定）/ Q5 定性（人工閱卷）。
"""

import json
import re
import subprocess
import sys

MODEL = (
    "/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct-GGUF"
    "/snapshots/9217f5db79a29953eb74d5343926648285ec7e67"
    "/qwen2.5-0.5b-instruct-q4_k_m.gguf"
)


def run_comp(comp, kw, flags=None):
    cmd = [sys.executable, "scripts/civil_components.py", "--component", comp]
    if flags:
        cmd += flags
    cmd += ["--json", json.dumps(kw)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    o = p.stdout
    return json.loads(o[o.index("{"):o.rindex("}") + 1])


def run_derive(tpl, over):
    p = subprocess.run(
        [sys.executable, "scripts/civil_derive.py", "--template", tpl,
         "--json", json.dumps(over)],
        capture_output=True, text=True, timeout=60,
    )
    o = p.stdout
    m = re.search(r"\{[^{}]*\"results\"[^{}]*\}", o, re.S)
    blobs = re.findall(r"\{[^{}]+\}", o)
    for b in blobs:
        try:
            d = json.loads(b)
            if "results" in d:
                return d
        except Exception:
            continue
    return {}


def ask(m, msgs, n=100):
    return m.create_chat_completion(msgs, max_tokens=n)["choices"][0]["message"]["content"]


def jparse(t):
    m = re.search(r"\{[^{}]*\}", t)
    return json.loads(m.group(0)) if m else {}


def main():
    from llama_cpp import Llama

    m = Llama(MODEL, n_ctx=2048, n_threads=4, verbose=False)
    log = []

    def loop(qid, prompt, check, rounds=3):
        hist = [{"role": "user", "content": prompt}]
        traj = []
        for r in range(rounds):
            t = ask(m, hist)
            try:
                p = jparse(t)
            except Exception:
                p = {}
            if not p:
                fb = "只要JSON"
                traj.append({"r": r + 1, "out": t[:60], "verdict": "format"})
            else:
                ok, info = check(p)
                traj.append({"r": r + 1, "out": p, "verdict": info, "pass": ok})
                if ok:
                    break
                fb = f"{info}，調整重出JSON"
            hist += [{"role": "assistant", "content": t},
                     {"role": "user", "content": fb}]
        log.append({"q": qid, "traj": traj})
        passed = any(x.get("pass") for x in traj)
        print(f"{qid}: {'PASS' if passed else 'FAIL'} {json.dumps(traj, ensure_ascii=False)[:300]}")

    def chk_beam(p):
        r = run_comp("beam", {"b": 300, "d": 500, "As": p.get("As", 0), "M_Ed_kNm": 400})
        return bool(r.get("bending_ok")), f"M_Rd={r.get('M_Rd_kNm')}"

    def chk_col(p):
        r = run_comp("column", {"b": 300, "h": 300, "As": p.get("As", 0), "N_Ed_kN": 2000})
        return bool(r.get("axial_ok")), f"N_Rd={r.get('N_Rd_kN')}"

    def chk_shear(p):
        r = run_comp("beam", {"b": 300, "d": 450, "As": 1256,
                              "V_Ed_kN": 150, "Asw_s": p.get("Asw_s", 0)})
        return bool(r.get("shear_ok")), f"V_Rds={r.get('V_Rds_kN')}"

    def chk_parapet(p):
        d = run_derive("parapet", {})
        req = d.get("results", {}).get("As_req", 195)
        a = p.get("As", 0)
        ok = req <= a <= 3 * req
        return ok, f"As={a} req={req}"

    loop("Q1-beam", "设计RC梁抗弯M_Ed=400kNm，截面b=300d=500。只输出JSON如{\"b\":0,\"d\":0,\"As\":0}", chk_beam)
    loop("Q2-column", "设计RC柱轴压N_Ed=2000kN，截面300x300。只输出JSON如{\"As\":0}", chk_col)
    loop("Q3-shear", "设计RC梁剪力V_Ed=150kN，b=300d=450。只输出JSON如{\"Asw_s\":0}（每mm箍筋面积）", chk_shear)
    loop("Q4-parapet", "设计护栏悬臂，顶部水平力F=20kN作用800mm高，墙厚250mm。只输出JSON如{\"As\":0}（每米配筋mm2）", chk_parapet)
    t5 = ask(m, [{"role": "user",
                "content": "100米单跨钢筋混凝土梁桥行不行？一句话为什么，只说结论"}])
    log.append({"q": "Q5-span", "resp": t5[:200]})
    print("Q5-span:", t5[:200])
    json.dump(log, open("/tmp/battery_log.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("log -> /tmp/battery_log.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
