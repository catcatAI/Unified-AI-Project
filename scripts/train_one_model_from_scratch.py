#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""From-scratch ONE model with an internal state (memory tokens).

No pretrained weights. One model = token embedding + causal Transformer + head
+ state projection. State = K vectors from the previous turn's hidden states,
prepended as memory tokens to the next turn. The prompt contains ONLY the
current question; no text history, no KV cache, no second model.

Pipeline: (1) pretrain on Wikipedia intro text, carrying state across chunks;
(2) SFT on core_train instruction pairs; (3) measure state influence by
ablation: real state vs zeroed state vs random state on a teaching->recall task.

Pre-registered gate: with_state recall must exceed zeroed_state recall by >=3
of 30 AND with_state >= 8/30; otherwise the state influence is not demonstrated.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sqlite3
import time
from pathlib import Path
from typing import List, Tuple

import torch
from torch import nn

REPO = Path(__file__).resolve().parent.parent
WIKI = REPO / "data" / "knowledge" / "wiki.sqlite"
INSTRUCT = REPO / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"

VALUES = {
    "name": ["小明", "小華", "阿哲", "美玲", "志強", "嘉紋"],
    "colour": ["藍色", "綠色", "紅色", "紫色", "橙色", "黑色"],
    "city": ["台北", "新竹", "台中", "台南", "高雄", "花蓮"],
}
PATTERNS = {
    "name": ("我的名字是{V}。", "我叫什麼名字？", "你叫{V}。"),
    "colour": ("我最喜歡的顏色是{V}。", "我最喜歡的顏色是什麼？", "你最喜歡的顏色是{V}。"),
    "city": ("我住在{V}。", "我住在哪裡？", "你住在{V}。"),
}


class OneModel(nn.Module):
    def __init__(
        self,
        vocab: int,
        d: int = 384,
        layers: int = 6,
        heads: int = 4,
        memory: int = 4,
        max_len: int = 256,
    ):
        super().__init__()
        self.d, self.memory, self.max_len = d, memory, max_len
        self.embed = nn.Embedding(vocab, d)
        self.pos = nn.Embedding(max_len + memory, d)
        self.state_proj = nn.Linear(d, d, bias=False)
        layer = nn.TransformerEncoderLayer(d, heads, d * 2, dropout=0.0, batch_first=True)
        self.body = nn.TransformerEncoder(layer, layers)
        self.head = nn.Linear(d, vocab)

    def forward(
        self, ids: torch.Tensor, state: torch.Tensor | None = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.embed(ids)
        b, n = ids.shape
        positions = torch.arange(n, device=ids.device).unsqueeze(0)
        if state is not None:
            mem = self.state_proj(state)  # (b, K, d) from previous turn
            x = torch.cat([mem, x], dim=1)
            positions = torch.arange(n + self.memory, device=ids.device).unsqueeze(0)
        x = x + self.pos(positions)
        mask = torch.triu(torch.ones(x.shape[1], x.shape[1], device=ids.device), 1).bool()
        out = self.body(x, mask=mask)
        new_state = out[:, -self.memory - 1 : -1, :].detach()
        return self.head(out), new_state


def load_wiki(limit: int) -> List[str]:
    con = sqlite3.connect(str(WIKI))
    texts = []
    for (body,) in con.execute("select body from pages limit ?", (limit,)):
        text = body[:1200].replace("\n", " ")
        if len(text) > 200:
            texts.append(text)
    return texts


def load_instructions(limit: int) -> List[Tuple[str, str]]:
    out = []
    with INSTRUCT.open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            out.append((row["input"], row["output"]))
            if len(out) >= limit:
                break
    return out


def encode(text: str, stoi: dict, unk: int) -> List[int]:
    return [stoi["<bos>"]] + [stoi.get(c, unk) for c in text] + [stoi["<eos>"]]


def ce(logits: torch.Tensor, ids: torch.Tensor, skip: int = 0, mem: int = 0) -> torch.Tensor:
    prefix = logits.shape[1] - (ids.shape[1] - 1)  # memory tokens prepended by the model
    shift = logits[:, prefix + skip :].reshape(-1, logits.shape[-1])
    target = ids[:, skip + 1 :].reshape(-1)
    return nn.functional.cross_entropy(shift, target)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--wiki-docs", type=int, default=20000)
    p.add_argument("--instructions", type=int, default=20000)
    p.add_argument("--pretrain-steps", type=int, default=600)
    p.add_argument("--sft-steps", type=int, default=600)
    p.add_argument("--tokens-per-step", type=int, default=256)
    p.add_argument("--d-model", type=int, default=384)
    p.add_argument("--layers", type=int, default=6)
    p.add_argument("--memory", type=int, default=4)
    p.add_argument("--device", choices=("cpu", "xpu", "cuda"), default="xpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "one_model_from_scratch.json")
    )
    p.add_argument("--save-dir", default=str(REPO / "data" / "models" / "angela_one_model"))
    args = p.parse_args()

    wiki = load_wiki(args.wiki_docs)
    instructions = load_instructions(args.instructions)
    chars = sorted({c for t in wiki + [q + a for q, a in instructions] for c in t})
    itos = ["<pad>", "<bos>", "<eos>", "<unk>"] + chars
    stoi = {t: i for i, t in enumerate(itos)}
    device = torch.device(args.device)
    model = OneModel(len(itos), args.d_model, args.layers, memory=args.memory).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3)
    started = time.time()
    rng = random.Random(20261127)

    # Phase 1: language pretraining on wiki, state carried across chunks of one article.
    for step in range(args.pretrain_steps):
        doc = wiki[step % len(wiki)]
        ids = encode(doc, stoi, 3)[: args.tokens_per_step + 1]
        state = None
        for start in range(0, len(ids) - 1, 64):
            chunk = ids[start : start + 65]
            if len(chunk) < 2:
                continue
            x = torch.tensor([chunk[:-1]], dtype=torch.long, device=device)
            y = torch.tensor([chunk], dtype=torch.long, device=device)
            logits, state = model(x, state)
            loss = ce(logits, y, mem=state.shape[1] if state is not None else 0)
            opt.zero_grad()
            loss.backward()
            opt.step()
        if step % 100 == 0:
            print(f"pretrain {step} loss={loss.item():.3f}", flush=True)

    # Phase 2: SFT on instruction pairs, state carried across turns (same core).
    state = None
    for step in range(args.sft_steps):
        q, a = instructions[step % len(instructions)]
        ids = encode(q + "\n" + a, stoi, 3)[: args.tokens_per_step + 1]
        x = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
        y = torch.tensor([ids], dtype=torch.long, device=device)
        boundary = next((i for i, t in enumerate(ids) if itos[t] == "\n"), 0)
        logits, state = model(x, state)
        loss = ce(logits, y, skip=boundary)
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 100 == 0:
            print(f"sft {step} loss={loss.item():.3f}", flush=True)

    # Phase 3: state influence via ablation on teaching->recall.
    def recall(mode: str) -> Tuple[int, List[str]]:
        hits, out = 0, []
        for i in range(30):
            kind = list(VALUES)[i % 3]
            value = VALUES[kind][rng.randrange(len(VALUES[kind]))]
            teach, ask, answer = PATTERNS[kind]
            t = torch.tensor([encode(teach.format(V=value), stoi, 3)], device=device)
            q = torch.tensor([encode(ask, stoi, 3)], device=device)
            with torch.no_grad():
                _, state = model(t[:, :-1], None)
                if mode == "zero":
                    state = torch.zeros_like(state)
                elif mode == "random":
                    state = torch.randn_like(state)
                generated = list(q[0].tolist())
                for _ in range(48):
                    logits, state = model(torch.tensor([generated], device=device), state)
                    nxt = int(logits[0, -1].argmax())
                    generated.append(nxt)
                    if nxt == stoi["<eos>"]:
                        break
            got = "".join(itos[x] for x in generated[len(q[0]) :] if x >= 4).lstrip("。 ")
            ok = value in got.split("。", 1)[0]
            hits += int(ok)
            if len(out) < 3:
                out.append(f"gold={answer.format(V=value)} got={got[:80]}")
        return hits, out

    real, real_samples = recall("real")
    zero, _ = recall("zero")
    random_s, _ = recall("random")
    delta = real - max(zero, random_s)
    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "from scratch: one Transformer + internal K memory-token state, no pretrained weights",
        "wiki_docs": len(wiki),
        "instructions": len(instructions),
        "vocab": len(itos),
        "params": sum(x.numel() for x in model.parameters()),
        "seconds": round(time.time() - started, 1),
        "ablation": {
            "real_state": real,
            "zeroed_state": zero,
            "random_state": random_s,
            "delta": delta,
        },
        "samples": real_samples,
        "gate": {
            "registered_before_run": True,
            "pass": real >= 8 and delta >= 3,
            "verdict": (
                "state_affects_dialogue" if (real >= 8 and delta >= 3) else "not_demonstrated"
            ),
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    save = Path(args.save_dir)
    save.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "config": {
                "vocab": len(itos),
                "d": args.d_model,
                "layers": args.layers,
                "memory": args.memory,
            },
        },
        save / "model.pt",
    )
    (save / "vocab.json").write_text(json.dumps({"itos": itos}, ensure_ascii=False))
    print(f"saved single model to {save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
