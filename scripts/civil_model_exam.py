#!/usr/bin/env python3
"""模型建模考試（專案/專案ai/小模型親自寫碼）：提示→去圍欄→Blender 執行→評分。

評分（100）：可解析 20＋可運行 30＋物件數對 25＋尺寸對 25。
"""

import re
import subprocess
import sys

QWEN = ("/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct-GGUF"
        "/snapshots/9217f5db79a29953eb74d5343926648285ec7e67"
        "/qwen2.5-0.5b-instruct-q4_k_m.gguf")
GEMMA = ("/home/cxuo/.cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
         "/snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93"
         "/gemma-4-E2B_q4_0-it.gguf")

PROMPT = ("写Blender Python脚本：清空场景，建两个相交的盒子当马路"
          "（A路30长8宽0.5高放原点，B路8长30宽0.5高放原点），"
          "再建4个小盒子当匝道放四角(15,15,0)等。只输出代码，不要解释")


def run(cmd, timeout):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-800:]
    except subprocess.TimeoutExpired:
        return 124, "超時"


def grade(name, model_path, threads, toks):
    from llama_cpp import Llama

    m = Llama(model_path, n_ctx=2048, n_threads=threads, verbose=False)
    r = m.create_chat_completion([{"role": "user", "content": PROMPT}],
                                 max_tokens=toks)
    code = re.sub(r"```[a-z]*", "", r["choices"][0]["message"]["content"])
    with open(f"/tmp/model_exam_{name}.py", "w", encoding="utf-8") as f:
        f.write(code)
    try:
        compile(code, "<exam>", "exec")
        s_parse, s_run = 20, 0
    except SyntaxError:
        return {"model": name, "score": 0, "note": "語法錯"}
    probe = ("\nimport bpy\nprint('EXAM-OBJ:' + str(len(bpy.data.objects)))\n"
             "import json as _j\nprint('EXAM-DIMS:' + _j.dumps("
             "{o.name: [round(v,1) for v in o.dimensions] for o in bpy.data.objects}))\n")
    with open(f"/tmp/model_exam_{name}.py", "a", encoding="utf-8") as f:
        f.write(probe)
    code2, out = run(["blender", "--background", "--python",
                      f"/tmp/model_exam_{name}.py"], 300)
    import json as _json
    nobjs, dims = 0, {}
    for line in out.splitlines():
        if "EXAM-OBJ:" in line:
            try:
                nobjs = int(line.split("EXAM-OBJ:")[1])
            except Exception:
                pass
        if "EXAM-DIMS:" in line:
            try:
                dims = _json.loads(line.split("EXAM-DIMS:")[1])
            except Exception:
                pass
    if nobjs == 0:
        return {"model": name, "score": 20, "note": "可解析不可運行"}
    s_obj = 25 if nobjs >= 6 else round(25 * nobjs / 6)
    road_ok = any(abs(d[0] - 30) < 1 and abs(d[1] - 8) < 1 for d in dims.values())
    s_dim = 25 if road_ok else 0
    return {"model": name, "score": 20 + 30 + s_obj + s_dim,
            "note": f"{nobjs} 物件，路尺寸{'對' if road_ok else '錯'}"}


def main():
    import argparse

    ap = argparse.ArgumentParser(description="modeling exam")
    ap.add_argument("--who", default="both", choices=["qwen", "gemma", "both"])
    args = ap.parse_args()
    out = []
    if args.who in ("qwen", "both"):
        out.append(grade("qwen", QWEN, 2, 400))
    if args.who in ("gemma", "both"):
        out.append(grade("gemma", GEMMA, 2, 500))
    for r in out:
        print(f"{r['model']}: {r['score']}/100（{r['note']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
