#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
# =============================================================================
"""E5 誘導頭消融：哪些頭驅動重複環（Qwen2.5-0.5B，因果檢驗）。

兩階段（發現與檢驗嚴格分離，prompt 零重疊）：
- 發現（描述性，不裁決）：E2-head 的 12 prompt 上，每頭 loop-vs-plain 的
  近期質量差排序，取 top-5 為候選 loop 頭，另取固定種子隨機 5 頭為對照。
- 因果（預註冊裁決）：E2-token 的 6 飽和陷阱上，三條件貪婪生成——完整、
  候選消融、隨機消融（逐層逐步清零指定頭輸出）。預測：
  loop_rate(candidate) 比 intact 與 random 皆低至少 2/6，且三條件各
  >=4/6 非空（否則 INCONCLUSIVE：消融打壞生成本身時，loop 率無意義）。
- 確定性對照：intact 首 prompt 重跑逐字相同。

用法: `.venv/bin/python scripts/exp_head_ablation.py [--json out.json]`
退出碼：0 預測成立；1 不成立/空組/推理失敗。
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

SNAPSHOT = (
    "/home/cxuo/.cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct"
    "/snapshots/7ae557604adf67be50417f59c2c2f167def9a775"
)
MAX_TOKENS = 30
RECENT_K = 8
TOP_K = 5
N_HEADS = 14

DISCOVERY_TRAPS = [
    "Repeat after me: AB AB AB AB AB AB AB AB AB AB",
    "Echo: la la la la la la la la la la la la",
    "Count out loud: one one one one one one one",
    "The word time appears many times: time time time time time time",
    "Write the letter A many times in a row:",
    "Say yes repeatedly: yes yes yes yes yes yes yes",
]
DISCOVERY_NEUTRALS = [
    "List the days of the week in order:",
    "Count from 1 to 20:",
    "She sells seashells by the seashore.",
    "To be or not to be, that is the question.",
    "Once upon a time there was a",
    "The capital of France is",
]
CAUSAL_TRAPS = [
    "Tick tock tick tock tick tock tick tock tick",
    "Knock knock knock knock knock knock knock",
    "No no no no no no no no no",
    "Stop stop stop stop stop stop stop stop",
    "Hello hello hello hello hello hello hello",
    "Okay okay okay okay okay okay okay okay",
]


def _head_masses(model, tok, prompt: str):
    """每頭近期質量：{layer: [head_mass]}，均值 over 生成步。"""
    import torch

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
    acc = {}
    n = 0
    for step_attns in out.attentions:
        n += 1
        for li, layer in enumerate(step_attns):
            # 逐頭質量：先去 batch 維再取頭，絕不預平均 heads
            tensor = layer.float()
            tensor = tensor[0] if tensor.dim() == 4 else tensor
            # -> (heads, q, kv)
            n_heads = tensor.shape[0]
            slot = acc.setdefault(li, [[0.0] * n_heads, 0])
            for h in range(n_heads):
                row = tensor[h, -1, :].tolist()
                slot[0][h] += sum(row[-RECENT_K:])
            slot[1] += 1
    per_head = {li: [v / slot[1] for v in slot[0]] for li, slot in acc.items()}
    return text, per_head


def main() -> int:
    t_start = time.time()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument(
        "--ctrl-seed",
        type=int,
        default=0,
        help="random-control head sample seed (replication uses 1)",
    )
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
    n_layers = len(model.model.layers)

    # ---- 發現：每頭 loop-vs-plain 差排序（描述性） ----
    loop_m = [[0.0] * N_HEADS for _ in range(n_layers)]
    plain_m = [[0.0] * N_HEADS for _ in range(n_layers)]
    n_loop = n_plain = 0
    discovery_texts = []
    for prompt in DISCOVERY_TRAPS + DISCOVERY_NEUTRALS:
        text, per_head = _head_masses(model, tok, prompt)
        discovery_texts.append(text)
        bucket = loop_m if detect_loop(text) else plain_m
        for li in range(n_layers):
            for h in range(N_HEADS):
                bucket[li][h] += per_head[li][h]
        if detect_loop(text):
            n_loop += 1
        else:
            n_plain += 1
    gaps = sorted(
        (
            (loop_m[li][h] / max(n_loop, 1) - plain_m[li][h] / max(n_plain, 1), li, h)
            for li in range(n_layers)
            for h in range(N_HEADS)
        ),
        reverse=True,
    )
    candidates = [(li, h) for _, li, h in gaps[:TOP_K]]
    rng = random.Random(args.ctrl_seed)
    all_heads = [(li, h) for li in range(n_layers) for h in range(N_HEADS)]
    random_heads = [x for x in rng.sample(all_heads, TOP_K * 3) if x not in set(candidates)][:TOP_K]

    # ---- 因果：三條件消融 ----
    head_dim = model.config.hidden_size // model.config.num_attention_heads

    def generate_ablated(prompt: str, ablate: set) -> str:
        handles = []

        def _zero(li_heads):
            def _hook(_m, _i, out):
                hidden = out[0] if isinstance(out, tuple) else out
                for hh in li_heads:
                    hidden[..., hh * head_dim : (hh + 1) * head_dim] = 0.0
                return out

            return _hook

        by_layer: dict = {}
        for li, h in ablate:
            by_layer.setdefault(li, []).append(h)
        for li, hs in by_layer.items():
            handles.append(model.model.layers[li].register_forward_hook(_zero(hs)))
        try:
            inp = tok(prompt, return_tensors="pt")
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=MAX_TOKENS, do_sample=False)
            return tok.decode(out[0][inp["input_ids"].shape[1] :], skip_special_tokens=True)
        finally:
            for handle in handles:
                handle.remove()

    conditions = {}
    for name, ablate in (
        ("intact", set()),
        ("candidate", set(candidates)),
        ("random", set(random_heads)),
    ):
        texts = [generate_ablated(p, ablate) for p in CAUSAL_TRAPS]
        non_empty = [t for t in texts if t.strip()]
        rate = sum(1 for t in texts if detect_loop(t)) / len(texts)
        conditions[name] = {
            "rate": rate,
            "non_empty": len(non_empty),
            "tails": [t[-60:] for t in texts],
        }

    rep = generate_ablated(CAUSAL_TRAPS[0], set())
    det_texts = [generate_ablated(CAUSAL_TRAPS[0], set())]
    deterministic = det_texts[0] == rep
    ok_counts = all(c["non_empty"] >= 4 for c in conditions.values())
    gap_r = conditions["random"]["rate"] - conditions["candidate"]["rate"]
    gap_i = conditions["intact"]["rate"] - conditions["candidate"]["rate"]

    facts = [
        Fact("e5.determinism", float(deterministic), 1.0, "ge", "bool", "seed-repeat", ""),
        Fact("e5.non_empty_counts", float(ok_counts), 1.0, "ge", "bool", "ablation-sanity", ""),
    ]
    if ok_counts:
        facts.append(
            Fact(
                "e5.cand_beats_random",
                gap_r,
                2 / 6,
                "ge",
                "rate",
                "ablation",
                f"cand={conditions['candidate']['rate']} rand={conditions['random']['rate']}",
            )
        )
        facts.append(
            Fact(
                "e5.cand_beats_intact",
                gap_i,
                2 / 6,
                "ge",
                "rate",
                "ablation",
                f"cand={conditions['candidate']['rate']} intact={conditions['intact']['rate']}",
            )
        )
    report = adjudicate(facts)

    print("=" * 72)
    print("E5 head-ablation causality (candidate top-5 loop heads vs random-5)")
    print("=" * 72)
    print(f"candidates: {candidates}")
    print(f"random ctrl: {random_heads}")
    for name, c in conditions.items():
        print(f"[{name:9s}] loop_rate={c['rate']:.3f} non_empty={c['non_empty']}/6")
    print(f"deterministic: {deterministic}, elapsed_min={(time.time()-t_start)/60:.1f}")
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "candidates": candidates,
                    "random": random_heads,
                    "conditions": conditions,
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
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
