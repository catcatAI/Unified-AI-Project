#!/usr/bin/env python3
"""立交專項考試：互通式立交規劃判斷（埋三個缺陷，看專案抓幾個）。

條件（出題人補齊，用戶只給粗框）：
- 中心 O；A 走廊參考點 P_A：方位角 74°、距 O 780m；立交節點 N=P_A
- A 高架沿徑向（74°方向）穿過 N；B 高架垂直交叉（164°方向）
- 地面輔道沿高架兩側；匝道：A高架 2出3入、B高架 4出4入、A平面 1入2出、B平面 6出6入
- 設計假設：單車道匝道 1400pcu/h；環道最小半徑 60m@40km/h；
  最緊環道實測 R=55m（埋點3）；交織長度另案（無布局圖不評）

埋點：①A高架 2出3入不平衡 ②A平面 1入2出不平衡 ③R=55<60不合規。
評分 100：清點 20＋平衡判定 30＋幾何 20＋容量 15＋形式 15（人工）。
"""

import argparse
import json

SPEC = {
    "groups": {
        "A-elev": {"out": 2, "in": 3},
        "B-elev": {"out": 4, "in": 4},
        "A-sur": {"out": 2, "in": 1},
        "B-sur": {"out": 6, "in": 6},
    },
    "min_loop_R": 60.0,
    "tightest_loop_R": 55.0,
    "ramp_cap_pcu": 1400,
}


def analyze():
    g = SPEC["groups"]
    total = sum(v["out"] + v["in"] for v in g.values())
    # 走廊級車道平衡：出入必須相等（差1即不平衡——AASHTO合流分流守恆）
    balance = {k: v["out"] == v["in"] for k, v in g.items()}
    cap = {k: (v["out"] + v["in"]) * SPEC["ramp_cap_pcu"] for k, v in g.items()}
    geo_ok = SPEC["tightest_loop_R"] >= SPEC["min_loop_R"]
    return {"total_ramps": total, "balance": balance,
            "capacity_pcu": cap, "geometry_ok": geo_ok,
            "truth_imbalanced": sorted(k for k, v in balance.items() if not v)}


def ask_model(model_path, prompt, n_ctx, threads, n_tok=400):
    from llama_cpp import Llama

    m = Llama(model_path, n_ctx=n_ctx, n_threads=threads, verbose=False)
    r = m.create_chat_completion([{"role": "user", "content": prompt}],
                                 max_tokens=n_tok)
    return r["choices"][0]["message"]["content"]


QWEN = ("/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct-GGUF"
        "/snapshots/9217f5db79a29953eb74d5343926648285ec7e67"
        "/qwen2.5-0.5b-instruct-q4_k_m.gguf")
GEMMA = ("/home/cxuo/.cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
         "/snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93"
         "/gemma-4-E2B_q4_0-it.gguf")


def main():
    ap = argparse.ArgumentParser(description="interchange exam")
    ap.add_argument("--ask", default="none", choices=["none", "qwen", "gemma", "both"])
    args = ap.parse_args()
    truth = analyze()
    print(json.dumps(truth, ensure_ascii=False, indent=1))
    print(f"真值：共 {truth['total_ramps']} 條匝道；不平衡組 {truth['truth_imbalanced']}；"
          f"幾何 {'✅' if truth['geometry_ok'] else '❌ R55<60'}")
    spec_text = (
        "某互通立交：A高架2出3入，B高架4出4入，A平面1入2出，B平面6出6入，"
        "共28條匝道；最緊環道半徑55米（規範最小60米）。"
        "只答三行，不許演算：第一行共幾條，第二行哪幾組出入不平衡，"
        "第三行幾何是否合規（比較55和60）"
    )
    if args.ask in ("qwen", "both"):
        try:
            print("QWEN:", ask_model(QWEN, spec_text, 1024, 2)[:300])
        except Exception as e:
            print("QWEN ERR:", str(e)[:100])
    if args.ask in ("gemma", "both"):
        try:
            print("GEMMA:", ask_model(GEMMA, spec_text, 1024, 2)[:400])
        except Exception as e:
            print("GEMMA ERR:", str(e)[:100])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
