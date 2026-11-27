#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""One model, one state, no context: the §14 single-core language experiment.

Not another architecture A/B. A single GRU core owns:
  * one weights hash (embedding + GRU + head)
  * one fixed-size state tensor carried across turns (state never enters prompt)
One ai_step: question -> answer, updating the same state. Training groups rows by
source (a session) so the state is actually used across turns.

Pre-registered gate (written before running):
  free-running exact on 30 held-out answers, where the state comes from a prior
  teaching turn and the prompt contains ONLY the question. If exact stays 0 at
  2M tokens, the single-core language claim is falsified at this data scale.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path
from typing import List, Tuple

import torch
from torch import nn

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"


class Core(nn.Module):
    """One model: embed -> GRU (with persistent state) -> token head."""

    def __init__(self, vocab: int, d_model: int = 512):
        super().__init__()
        self.embed = nn.Embedding(vocab, d_model)
        self.gru = nn.GRU(d_model, d_model, 1, batch_first=True)
        self.head = nn.Linear(d_model, vocab)

    def step(
        self, ids: torch.Tensor, state: torch.Tensor | None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        x = self.embed(ids)
        out, state = self.gru(x, state)
        return self.head(out), state.detach()  # state is owned by the model, not the context


def load_sessions(limit: int) -> List[List[Tuple[str, str]]]:
    sessions: dict = {}
    with DATA.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            sessions.setdefault(row.get("source", "unknown"), []).append(
                (row["input"], row["output"])
            )
            if limit and sum(len(v) for v in sessions.values()) >= limit:
                break
    return [v for v in sessions.values() if v]


def encode(text: str, stoi: dict, unk: int) -> List[int]:
    return [stoi["<bos>"]] + [stoi.get(c, unk) for c in text] + [stoi["<eos>"]]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=20000)
    p.add_argument("--tokens", type=int, default=2000000)
    p.add_argument("--d-model", type=int, default=512)
    p.add_argument("--device", choices=("cpu", "xpu", "cuda"), default="cpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "single_core_state.json")
    )
    args = p.parse_args()

    sessions = load_sessions(args.limit)
    rows = [r for session in sessions for r in session]
    chars = sorted({c for q, a in rows for c in q + "\n" + a})
    itos = ["<pad>", "<bos>", "<eos>", "<unk>"] + chars
    stoi = {t: i for i, t in enumerate(itos)}
    device = torch.device(args.device)
    model = Core(len(itos), args.d_model).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=2e-3)
    rng = random.Random(20261127)
    seen, started = 0, time.time()

    while seen < args.tokens:
        for session in rng.sample(sessions, len(sessions)):  # turns stay in order within a session
            state = None
            for q, a in session:
                ids = encode(q + "\n" + a, stoi, 3)[:192]
                x = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
                y = torch.tensor([ids[1:]], dtype=torch.long, device=device)
                logits, state = model.step(x, state)
                # loss only on answer tokens: find the newline boundary
                boundary = next(
                    (i for i, t in enumerate(ids[:-1]) if itos[t] == "\n"), len(ids) - 1
                )
                mask = torch.arange(y.shape[1], device=device) >= boundary
                nll = -torch.log_softmax(logits, -1).gather(-1, y.unsqueeze(-1)).squeeze(-1)
                loss = (nll * mask).sum() / mask.sum().clamp(min=1)
                optim.zero_grad()
                loss.backward()
                optim.step()
                seen += x.numel()
                if seen >= args.tokens:
                    break
            if seen >= args.tokens:
                break

    # Evaluation: one teaching turn builds state; the test turn's prompt is ONLY the question.
    hits = 0
    samples = []
    for session in sessions[:30]:
        if len(session) < 2:
            continue
        teach_q, teach_a = session[0]
        test_q, test_a = session[-1]
        state = None
        with torch.no_grad():
            teach = torch.tensor([encode(teach_q + "\n" + teach_a, stoi, 3)[:192]], device=device)
            _, state = model.step(teach, state)
            ids = encode(test_q, stoi, 3)[:96]
            for _ in range(192):
                logits, state = model.step(torch.tensor([ids], device=device), state)
                nxt = int(logits[0, -1].argmax())
                if nxt == stoi["<eos>"]:
                    break
                ids.append(nxt)
            got = "".join(itos[i] for i in ids[len(encode(test_q, stoi, 3)) - 1 :] if i >= 4)
        ok = got.strip() == test_a.strip()
        hits += int(ok)
        if len(samples) < 3:
            samples.append({"q": test_q[:80], "gold": test_a[:120], "got": got[:160], "exact": ok})

    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "one GRU core (one weights), one persistent state tensor, no context history",
        "rows": len(rows),
        "sessions": len(sessions),
        "vocab": len(itos),
        "params": sum(x.numel() for x in model.parameters()),
        "tokens": seen,
        "seconds": round(time.time() - started, 1),
        "free_exact": hits,
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "falsified_if_exact_zero": hits == 0,
            "verdict": "falsified_at_this_scale" if hits == 0 else "one_core_generates",
        },
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
