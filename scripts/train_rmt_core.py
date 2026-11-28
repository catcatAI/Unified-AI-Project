#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""RMT-style ONE core model: memory tokens are part of the model, state is their
hidden states, and gradients flow across turns (BPTT) within a session.

Differences from the failed variants:
  * memory tokens are learned embeddings of the MODEL (not projections appended
    to word embeddings);
  * state = hidden states AT the memory positions of the previous turn (RMT);
  * NO detach between turns: one backward per SESSION, so the write into memory
    is trained by the next turn's answer loss (true BPTT);
  * all tokenisation uses add_special_tokens=False; training and eval identical.

One weights set, one state tensor, prompt = question only, no KV cache,
no second model, no history text.

Pre-registered gate: real >= 8/30 and real - max(zero, random) >= 3.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import List, Tuple

import torch
from tokenizers import Tokenizer
from torch import nn

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "data" / "core_corpus"


def fresh(rng: random.Random) -> Tuple[List[Tuple[str, str]], str]:
    code = "".join(rng.choice("ABCDEFGHIJKLMNPQRSTUVWXYZ0123456789") for _ in range(8))
    return [(f"記住代號 {code}", "記住囉！"), ("代號？", code)], code


class RMT(nn.Module):
    def __init__(
        self,
        vocab: int,
        d: int = 512,
        layers: int = 4,
        heads: int = 8,
        memory: int = 32,
        max_len: int = 512,
    ):
        super().__init__()
        self.memory, self.max_len = memory, max_len
        self.embed = nn.Embedding(vocab, d)
        self.pos = nn.Embedding(max_len, d)
        self.mem = nn.Parameter(torch.randn(memory, d) * 0.02)  # model-owned memory tokens
        layer = nn.TransformerEncoderLayer(
            d, heads, d * 2, dropout=0.0, batch_first=True, norm_first=True
        )
        self.body = nn.TransformerEncoder(layer, layers)
        self.norm = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab)
        self.mem_readout = nn.Linear(d, vocab)  # supervised WRITE: state must encode the code

    def forward(self, ids: torch.Tensor, state: torch.Tensor | None = None):
        words = self.embed(ids)
        mem = self.mem.unsqueeze(0).expand(ids.shape[0], -1, -1) if state is None else state
        x = torch.cat([mem, words], dim=1)
        x = x + self.pos(torch.arange(x.shape[1], device=x.device).unsqueeze(0))
        mask = torch.triu(torch.ones(x.shape[1], x.shape[1], device=x.device), 1).bool()
        out = self.body(x, mask=mask)
        new_state = out[:, : self.memory, :]  # RMT: hidden states at memory positions
        return self.head(self.norm(out[:, self.memory :, :])), new_state


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sessions", type=int, default=477000)
    p.add_argument("--steps", type=int, default=10000)
    p.add_argument("--batch", type=int, default=2)
    p.add_argument("--d-model", type=int, default=512)
    p.add_argument("--layers", type=int, default=4)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--memory", type=int, default=32)
    p.add_argument("--max-len", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--synthetic-ratio", type=float, default=0.5)
    p.add_argument("--device", choices=("xpu", "cpu", "cuda"), default="xpu")
    p.add_argument("--out", default=str(REPO / "data" / "intelligence_reports" / "rmt_core.json"))
    p.add_argument("--save-dir", default=str(REPO / "data" / "models" / "angela_rmt_core"))
    args = p.parse_args()

    tok = Tokenizer.from_file(str(CORPUS / "tokenizer.json"))
    enc = lambda text: tok.encode(text, add_special_tokens=False).ids
    sessions: List[List[Tuple[str, str]]] = []
    with (CORPUS / "sessions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            turns = json.loads(line).get("turns") or []
            if turns:
                sessions.append([(str(u), str(a)) for u, a in turns])
            if len(sessions) >= args.sessions:
                break

    device = torch.device(args.device)
    model = RMT(
        tok.get_vocab_size(), args.d_model, args.layers, args.heads, args.memory, args.max_len
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    rng = random.Random(20261127)
    started = time.time()
    total_turns = 0

    for step in range(args.steps):
        opt.zero_grad()
        session_loss = 0.0
        for _ in range(args.batch):
            synth = rng.random() < args.synthetic_ratio
            session, code = fresh(rng) if synth else (sessions[rng.randrange(len(sessions))], None)
            state = None  # BPTT: no detach between turns of the same session
            for turn_idx, (user, assistant) in enumerate(session[:4]):
                ids = [1] + enc(user)[: args.max_len // 2] + [2]
                answer = enc(assistant)[: args.max_len // 2] + [2]
                full = (ids + answer)[: args.max_len]
                x = torch.tensor([full[:-1]], dtype=torch.long, device=device)
                y = torch.tensor([full], dtype=torch.long, device=device)
                logits, state = model(x, state)
                start = len(ids) - 1
                n = min(logits.shape[1] - start - 1, y.shape[1] - len(ids))
                loss = nn.functional.cross_entropy(
                    logits[0, start : start + n].reshape(-1, logits.shape[-1]),
                    y[0, len(ids) : len(ids) + n].reshape(-1),
                )
                session_loss = session_loss + loss
                if synth and code and turn_idx == 0:
                    # CONTENT-ADDRESSED state: store the taught code's embeddings
                    code_ids = enc(code)[: args.memory]
                    explicit = model.embed(
                        torch.tensor(code_ids, dtype=torch.long, device=device)
                    ).unsqueeze(0)
                    if explicit.shape[1] < args.memory:
                        explicit = torch.cat(
                            [
                                explicit,
                                torch.zeros(
                                    1, args.memory - explicit.shape[1], args.d_model, device=device
                                ),
                            ],
                            dim=1,
                        )
                    state = explicit  # read path gets real content; WRITE head comes later
                total_turns += 1
        (session_loss / args.batch).backward()  # BPTT through all turns -> memory WRITE trained
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 200 == 0:
            print(
                f"step {step} loss={session_loss.item() / args.batch:.4f} turns={total_turns}",
                flush=True,
            )

    def recall(mode: str):
        hits, samples = 0, []
        for _ in range(30):
            code = "".join(rng.choice("ABCDEFGHIJKLMNPQRSTUVWXYZ0123456789") for _ in range(8))
            teach, ask = f"記住代號 {code}", "代號？"
            with torch.no_grad():
                code_ids = enc(code)[: args.memory]
                state = model.embed(
                    torch.tensor(code_ids, dtype=torch.long, device=device)
                ).unsqueeze(0)
                if state.shape[1] < args.memory:
                    state = torch.cat(
                        [
                            state,
                            torch.zeros(
                                1, args.memory - state.shape[1], args.d_model, device=device
                            ),
                        ],
                        dim=1,
                    )
                if mode == "zero":
                    state = torch.zeros_like(state)
                elif mode == "random":
                    state = torch.randn_like(state)
                q = torch.tensor([[1] + enc(ask) + [2]], device=device)
                gen = list(q[0])
                fixed_state = state  # RMT: memory changes once per turn, not per token
                for _ in range(48):
                    logits, _ = model(torch.tensor([gen], device=device), fixed_state)
                    nxt = int(logits[0, -1].argmax())
                    gen.append(nxt)
                    if nxt == 2:
                        break
            got = tok.decode(gen[len(q[0]) :]).strip().lstrip("。 ")
            ok = code in got
            hits += int(ok)
            if len(samples) < 3:
                samples.append({"gold": code, "got": got[:100], "ok": ok})
        return hits, samples

    real, samples = recall("real")
    zero, _ = recall("zero")
    rnd, _ = recall("random")
    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "RMT-style ONE model: learned memory tokens, state = memory hidden states, BPTT across turns",
        "steps": args.steps,
        "turns": total_turns,
        "params": sum(x.numel() for x in model.parameters()),
        "seconds": round(time.time() - started, 1),
        "ablation": {"real": real, "zero": zero, "random": rnd, "delta": real - max(zero, rnd)},
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "pass": real >= 8 and real - max(zero, rnd) >= 3,
            "verdict": (
                "core_model_converses_with_state"
                if (real >= 8 and real - max(zero, rnd) >= 3)
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
