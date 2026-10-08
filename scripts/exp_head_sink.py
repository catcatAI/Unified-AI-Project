#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E2真頭實驗 round 2：loop 文本是否伴隨更高的句首匯質量（新 prompt 集）。

動機：上一輪（exp_head_inwardness.py）在舊 prompt 集上發現 loop 組近期質量
更低（gap -0.067），事後假設為 attention-sink 類現象。本輪用**全新 12 個
prompt**（舊集零重疊，禁事後撈取）檢驗該假設。

設計（預註冊）：Qwen2.5-0.5B eager，貪婪 30 tokens；匯質量 = 全層全頭平均後
查詢位置前 4 鍵質量，逐步平均；分組按 detect_loop 文本判定。
預測：mean(loop) > mean(non-loop)。任一組為空 → INCONCLUSIVE。
確定性對照：首 prompt 重跑逐字相同。

用法: `.venv/bin/python scripts/exp_head_sink.py [--json out.json]`
退出碼：0 預測成立；1 不成立/空組/推理失敗。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

TRAP_PROMPTS = [
    "Knock knock knock knock knock knock knock",
    "Tick tock tick tock tick tock tick tock tick",
    "No no no no no no no no no",
    "Stop stop stop stop stop stop stop stop",
    "Hello hello hello hello hello hello hello",
    "Okay okay okay okay okay okay okay okay",
]
NEUTRAL_PROMPTS = [
    "Explain why the sky is blue:",
    "What is the boiling point of water?",
    "Describe a mountain landscape:",
    "How do airplanes stay in the air?",
    "What year did humans land on the Moon?",
    "Name three primary colors:",
]
MAX_TOKENS = 30
SINK_K = 4
SNAPSHOT = (
    "/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct"
    "/snapshots/7ae557604adf67be50417f59c2c2f167def9a775"
)


def _score_completion(attentions, n_generated: int) -> tuple:
    """回傳 (全局均值, 每層均值)：全局供裁決，分層僅描述性報告（不裁決）。"""
    import torch
    from ai.attention.inner_outer import attention_sink_mass

    scores = []
    per_layer_sums: list = []
    n_layers = 0
    for step_attns in attentions[:n_generated]:
        stacked = torch.stack([layer[0].float() for layer in step_attns])
        n_layers = stacked.shape[0]
        if not per_layer_sums:
            per_layer_sums = [0.0] * n_layers
        mean_heads_layers = stacked.mean(dim=(0, 1))
        query_row = mean_heads_layers[-1].tolist()
        scores.append(attention_sink_mass(query_row, SINK_K))
        for li in range(n_layers):
            layer_mean = stacked[li].mean(dim=0)[-1].tolist()
            per_layer_sums[li] += attention_sink_mass(layer_mean, SINK_K)
        del stacked
    n = len(scores) or 1
    global_mean = sum(scores) / len(scores) if scores else 0.0
    return global_mean, [s / n for s in per_layer_sums]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    import torch
    from ai.attention.degeneracy import detect_loop
    from core.facts import Fact, adjudicate
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(SNAPSHOT, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        SNAPSHOT, local_files_only=True, dtype=torch.float32, attn_implementation="eager"
    )
    model.eval()

    def run(prompt: str) -> tuple:
        inp = tok(prompt, return_tensors="pt")
        with torch.no_grad():
            out = model.generate(
                **inp,
                max_new_tokens=MAX_TOKENS,
                do_sample=False,
                output_attentions=True,
                return_dict_in_generate=True,
            )
        text = tok.decode(out.sequences[0][inp["input_ids"].shape[1] :], skip_special_tokens=True)
        score = _score_completion(out.attentions, MAX_TOKENS)
        return text, score

    rows = []
    for label, prompt in [("trap", p) for p in TRAP_PROMPTS] + [
        ("neutral", p) for p in NEUTRAL_PROMPTS
    ]:
        text, score = run(prompt)
        rows.append(
            {
                "kind": label,
                "loop": detect_loop(text),
                "sink": round(score[0], 4),
                "layers": [round(v, 4) for v in score[1]],
                "tail": text[-80:],
            }
        )

    rep_text, _ = run(TRAP_PROMPTS[0])
    deterministic = rep_text[-80:] == rows[0]["tail"]

    loop_scores = [r["sink"] for r in rows if r["loop"]]
    plain_scores = [r["sink"] for r in rows if not r["loop"]]
    conclusive = bool(loop_scores) and bool(plain_scores)
    gap = (
        (sum(loop_scores) / len(loop_scores) - sum(plain_scores) / len(plain_scores))
        if conclusive
        else 0.0
    )

    facts = [Fact("e2s.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", "")]
    if conclusive:
        facts.append(
            Fact(
                "e2s.loop_minus_plain",
                gap,
                0.0,
                "ge",
                "mass",
                "sink-pairs",
                f"loop={sum(loop_scores)/len(loop_scores):.3f} plain={sum(plain_scores)/len(plain_scores):.3f}",
            )
        )
    report = adjudicate(facts)

    print("=" * 72)
    print("E2-SINK sink mass vs loops (Qwen2.5-0.5B eager, greedy, K=4, fresh prompts)")
    print("=" * 72)
    for r in rows:
        print(f"[{r['kind']:7s}] loop={int(r['loop'])} sink={r['sink']:.3f} {r['tail'][:60]!r}")
    print(f"deterministic: {deterministic}, conclusive: {conclusive}, gap: {gap:.3f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "rows": rows,
                    "gap": gap,
                    "deterministic": deterministic,
                    "verdict": report.as_dict(),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"json -> {args.json}")
    if not deterministic:
        return 1
    return 0 if (conclusive and report.ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
