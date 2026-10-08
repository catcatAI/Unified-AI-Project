#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E2真頭實驗：loop 文本是否伴隨更高的近期注意力質量（Qwen2.5-0.5B，eager）。

設計（預註冊）：
- 6 誘發 + 6 中性 prompt，貪婪解碼 30 tokens，同 seed 可重跑。
- 每步內聚度 = 全層全頭平均後、查詢位置對最近 8 鍵的質量；
  每完成分數 = 生成步均值；分組按 detect_loop 文本判定。
- 預測：mean(loop) > mean(non-loop)。任一組為空 → INCONCLUSIVE
  （不硬判，陷阱校準失敗即止）。
- 確定性對照：首 prompt 跑兩次逐字相同，否則整輪不可信。
- 誠實邊界：測的是 0.5B 通用 transformer 的內聚-loop 共生，
  不是 Angela、不是 Gemma；是機制證據，不是身份證據。

用法: `.venv/bin/python scripts/exp_head_inwardness.py [--json out.json]`
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
    "Repeat after me: AB AB AB AB AB AB AB AB AB AB",
    "Echo: la la la la la la la la la la la la",
    "Count out loud: one one one one one one one",
    "The word time appears many times: time time time time time time",
    "Write the letter A many times in a row:",
    "Say yes repeatedly: yes yes yes yes yes yes yes",
]
NEUTRAL_PROMPTS = [
    "List the days of the week in order:",
    "Count from 1 to 20:",
    "She sells seashells by the seashore.",
    "To be or not to be, that is the question.",
    "Once upon a time there was a",
    "The capital of France is",
]
MAX_TOKENS = 30
RECENT_K = 8
SNAPSHOT = (
    "/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct"
    "/snapshots/7ae557604adf67be50417f59c2c2f167def9a775"
)


def _score_completion(attentions, n_generated: int) -> float:
    """各生成步：全層全頭平均 → 查詢位置近期質量（單一 metric 定義）；再對步平均。"""
    import torch
    from ai.attention.inner_outer import attention_inwardness

    scores = []
    for step_attns in attentions[:n_generated]:
        stacked = torch.stack([layer[0].float() for layer in step_attns])
        mean_heads_layers = stacked.mean(dim=(0, 1))
        query_row = mean_heads_layers[-1].tolist()
        scores.append(attention_inwardness(query_row, RECENT_K))
        del stacked
    return sum(scores) / len(scores) if scores else 0.0


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
        t0 = time.time()
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
        return text, score, time.time() - t0

    rows = []
    for label, prompt in [("trap", p) for p in TRAP_PROMPTS] + [
        ("neutral", p) for p in NEUTRAL_PROMPTS
    ]:
        text, score, secs = run(prompt)
        rows.append(
            {
                "kind": label,
                "loop": detect_loop(text),
                "inwardness": round(score, 4),
                "secs": round(secs, 1),
                "tail": text[-80:],
            }
        )

    rep_text, _, _ = run(TRAP_PROMPTS[0])
    first_text = rows[0]["tail"]
    deterministic = rep_text[-80:] == first_text

    loop_scores = [r["inwardness"] for r in rows if r["loop"]]
    plain_scores = [r["inwardness"] for r in rows if not r["loop"]]
    conclusive = bool(loop_scores) and bool(plain_scores)
    gap = (
        (sum(loop_scores) / len(loop_scores) - sum(plain_scores) / len(plain_scores))
        if conclusive
        else 0.0
    )

    facts = [Fact("e2h.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", "")]
    if conclusive:
        facts.append(
            Fact(
                "e2h.loop_minus_plain",
                gap,
                0.0,
                "ge",
                "mass",
                "head-pairs",
                f"loop={sum(loop_scores)/len(loop_scores):.3f} plain={sum(plain_scores)/len(plain_scores):.3f}",
            )
        )
    report = adjudicate(facts)

    print("=" * 72)
    print("E2-HEAD inwardness vs loops (Qwen2.5-0.5B eager, greedy, K=8)")
    print("=" * 72)
    for r in rows:
        print(
            f"[{r['kind']:7s}] loop={int(r['loop'])} inward={r['inwardness']:.3f} {r['tail'][:60]!r}"
        )
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
