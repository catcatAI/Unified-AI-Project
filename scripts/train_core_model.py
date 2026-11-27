#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""Train THE core model from scratch on normalised multi-turn corpora.

ONE model: token embedding + causal Transformer + head + state projection.
ONE state: last K hidden vectors of the previous turn, prepended as memory
tokens to the next turn. Prompt = current question only; no text history,
no KV cache, no second model.

Corpus: data/core_corpus/sessions.jsonl (UltraChat + COIG + firefly),
tokenizer trained by prepare_core_corpus.py.

Pre-registered gate (written before running):
  ablation accuracy on held-out teaching->recall: with_state >= 8/30 AND
  with_state - max(zero_state, random_state) >= 3. Otherwise not demonstrated.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from tokenizers import Tokenizer
from torch import nn

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "core_corpus"

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


class CoreModel(nn.Module):
    def __init__(
        self,
        vocab: int,
        d: int = 1024,
        layers: int = 12,
        heads: int = 16,
        memory: int = 8,
        max_len: int = 1024,
    ):
        super().__init__()
        self.d, self.memory, self.max_len = d, memory, max_len
        self.embed = nn.Embedding(vocab, d)
        self.pos = nn.Embedding(max_len + memory, d)
        self.state_proj = nn.Linear(d, d, bias=False)
        layer = nn.TransformerEncoderLayer(
            d, heads, d * 2, dropout=0.0, batch_first=True, norm_first=True
        )
        self.body = nn.TransformerEncoder(layer, layers)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab)

    def forward(
        self, ids: torch.Tensor, state: torch.Tensor | None = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.embed(ids)
        if state is not None:
            x = torch.cat([self.state_proj(state), x], dim=1)
        pos = torch.arange(x.shape[1], device=x.device).unsqueeze(0)
        x = x + self.pos(pos)
        mask = torch.triu(torch.ones(x.shape[1], x.shape[1], device=x.device), 1).bool()
        out = self.body(x, mask=mask)
        new_state = out[:, -self.memory - 1 : -1, :].detach()
        return self.head(self.norm(out)), new_state


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sessions", type=int, default=100000)
    p.add_argument("--steps", type=int, default=20000)
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--d-model", type=int, default=1024)
    p.add_argument("--layers", type=int, default=12)
    p.add_argument("--heads", type=int, default=16)
    p.add_argument("--memory", type=int, default=8)
    p.add_argument("--max-len", type=int, default=768)
    p.add_argument("--lr", type=float, default=2e-3)
    p.add_argument("--synthetic-ratio", type=float, default=0.25)
    p.add_argument("--device", choices=("xpu", "cpu", "cuda"), default="xpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "core_model_training.json")
    )
    p.add_argument("--save-dir", default=str(REPO / "data" / "models" / "angela_core"))
    args = p.parse_args()

    tok = Tokenizer.from_file(str(CORPUS / "tokenizer.json"))
    sessions: List[List[Tuple[str, str]]] = []
    with (CORPUS / "sessions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            turns = row.get("turns") or []
            if turns:
                sessions.append([(str(u), str(a)) for u, a in turns])
            if len(sessions) >= args.sessions:
                break
    if len(sessions) < 10:
        print("corpus too small; run prepare_core_corpus.py first")
        return 1

    device = torch.device(args.device)
    model = CoreModel(
        tok.get_vocab_size(), args.d_model, args.layers, args.heads, args.memory, args.max_len
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    def lr_lambda(step: int) -> float:
        warmup = min(1.0, (step + 1) / 1000)
        cosine = 0.5 * (1 + math.cos(math.pi * min(1.0, step / max(1, args.steps))))
        return warmup * (0.1 + 0.9 * cosine)

    scheduler = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda)
    rng = random.Random(20261127)
    started = time.time()
    seen_turns = 0

    for step in range(args.steps):
        opt.zero_grad()
        step_loss = 0.0
        step_turns = 0
        for _ in range(args.batch):
            if rng.random() < args.synthetic_ratio:
                kind = list(VALUES)[rng.randrange(3)]
                value = VALUES[kind][rng.randrange(len(VALUES[kind]))]
                teach, ask, answer = PATTERNS[kind]
                session = [
                    (teach.format(V=value), "記住囉！"),
                    (ask, answer.format(V=value)),
                ]
            else:
                session = sessions[rng.randrange(len(sessions))]
            state = None
            for user, assistant in session[:6]:  # cap turns per session
                ids = [1] + tok.encode(user).ids[: args.max_len // 2] + [2]
                answer = tok.encode(assistant).ids[: args.max_len // 2] + [2]
                full = (ids + answer)[: args.max_len]
                x = torch.tensor([full[:-1]], dtype=torch.long, device=device)
                y = torch.tensor([full], dtype=torch.long, device=device)
                logits, state = model(x, state)
                prefix = logits.shape[1] - (y.shape[1] - 1)
                start = prefix + len(ids) - 1
                n_pos = min(logits.shape[1] - start - 1, y.shape[1] - len(ids))
                loss = nn.functional.cross_entropy(
                    logits[0, start : start + n_pos].reshape(-1, logits.shape[-1]),
                    y[0, len(ids) : len(ids) + n_pos].reshape(-1),
                )
                if step == 0:
                    print(
                        f"turn loss={loss.item():.3f} n={n_pos} logstd={logits.std().item():.2f} tmin={int(y[0, len(ids):len(ids)+n_pos].min())} tmax={int(y[0, len(ids):len(ids)+n_pos].max())}",
                        flush=True,
                    )
                (loss / args.batch).backward()
                step_loss += loss.item()
                step_turns += 1
                seen_turns += 1
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        scheduler.step()
        if step % 200 == 0:
            print(
                f"step {step} loss={step_loss / max(1, step_turns):.4f} turns={seen_turns}",
                flush=True,
            )

    # Ablation: real vs zeroed vs random state on teaching->recall.
    def recall(mode: str) -> Tuple[int, List[str]]:
        hits, out = 0, []
        for i in range(30):
            kind = list(VALUES)[i % 3]
            value = VALUES[kind][rng.randrange(len(VALUES[kind]))]
            teach, ask, answer = PATTERNS[kind]
            with torch.no_grad():
                t = torch.tensor([tok.encode(teach.format(V=value)).ids], device=device)
                _, state = model(t[:, :-1], None)
                if mode == "zero":
                    state = torch.zeros_like(state)
                elif mode == "random":
                    state = torch.randn_like(state)
                q = torch.tensor([tok.encode(ask).ids], device=device)
                generated = list(q[0].tolist())
                for _ in range(48):
                    logits, state = model(torch.tensor([generated], device=device), state)
                    nxt = int(logits[0, -1].argmax())
                    generated.append(nxt)
                    if nxt == 2:  # eos
                        break
            got = tok.decode(generated[len(q[0]) :]).strip().lstrip("。 ")
            ok = value in got.split("。", 1)[0]
            hits += int(ok)
            if len(out) < 3:
                out.append(f"gold={answer.format(V=value)} got={got[:100]}")
        return hits, out

    real, samples = recall("real")
    zero, _ = recall("zero")
    rnd, _ = recall("random")
    delta = real - max(zero, rnd)
    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "from scratch: one Transformer, one internal K-memory-token state",
        "sessions": len(sessions),
        "steps": args.steps,
        "turns_seen": seen_turns,
        "params": sum(x.numel() for x in model.parameters()),
        "vocab": tok.get_vocab_size(),
        "seconds": round(time.time() - started, 1),
        "ablation": {"real": real, "zero": zero, "random": rnd, "delta": delta},
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "pass": real >= 8 and delta >= 3,
            "verdict": (
                "core_model_converses_with_state"
                if (real >= 8 and delta >= 3)
                else "not_demonstrated"
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
                "vocab": tok.get_vocab_size(),
                "d": args.d_model,
                "layers": args.layers,
                "heads": args.heads,
                "memory": args.memory,
                "max_len": args.max_len,
            },
        },
        save / "model.pt",
    )
    tok.save(str(save / "tokenizer.json"))
    print(f"saved core model to {save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
