#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""From-scratch ONE core model with cross-attention memory state.

Instead of prepending state vectors to embeddings (too weak in the previous
runs), the previous turn's K hidden vectors become KEY/VALUE in a cross-attention
layer whose QUERY is the current turn's tokens. The model actively reads state.
One weights set, one state tensor, prompt = current question only, no KV cache,
no second model.

Pre-registered gate (unchanged): real >= 8/30 and real - max(zero, random) >= 3.
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


def fresh_synthetic(rng: random.Random) -> Tuple[List[Tuple[str, str]], str]:
    code = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789") for _ in range(8))
    # Answer is the code ONLY — no template tokens to dilute the recall loss.
    return [(f"記住代號 {code}", "記住囉！"), ("代號？", code)], code


class CoreModel(nn.Module):
    def __init__(
        self,
        vocab: int,
        d: int = 768,
        layers: int = 8,
        heads: int = 8,
        memory: int = 32,
        max_len: int = 768,
    ):
        super().__init__()
        self.memory, self.max_len = memory, max_len
        self.embed = nn.Embedding(vocab, d)
        self.pos = nn.Embedding(max_len, d)
        self.mem_k = nn.Linear(d, d, bias=False)
        self.mem_v = nn.Linear(d, d, bias=False)
        self.cross = nn.MultiheadAttention(d, heads, batch_first=True)
        self.norm1 = nn.LayerNorm(d)
        layer = nn.TransformerEncoderLayer(
            d, heads, d * 2, dropout=0.0, batch_first=True, norm_first=True
        )
        self.body = nn.TransformerEncoder(layer, layers)
        self.norm2 = nn.LayerNorm(d)
        self.head = nn.Linear(d, vocab)
        self.mem_readout = nn.Linear(
            d, vocab
        )  # explicit WRITE objective: state must encode the code

    def forward(self, ids: torch.Tensor, state: torch.Tensor | None = None):
        x = self.embed(ids) + self.pos(torch.arange(ids.shape[1], device=ids.device).unsqueeze(0))
        if state is not None:
            k, v = self.mem_k(state), self.mem_v(state)
            attended, _ = self.cross(x, k, v)
            x = self.norm1(x + attended)
        mask = torch.triu(torch.ones(x.shape[1], x.shape[1], device=ids.device), 1).bool()
        out = self.body(x, mask=mask)
        # Content-addressed anchors: sample K positions across the WHOLE turn
        # (not just the tail), so early tokens such as the taught code are in state.
        idx = torch.linspace(0, out.shape[1] - 1, self.memory, device=out.device).long()
        anchors = out[:, idx, :]
        new_state = anchors  # keep graph: WRITE loss trains the body that formed anchors
        return self.head(self.norm2(out)), new_state


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sessions", type=int, default=477000)
    p.add_argument("--steps", type=int, default=15000)
    p.add_argument("--batch", type=int, default=3)
    p.add_argument("--d-model", type=int, default=768)
    p.add_argument("--layers", type=int, default=8)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--memory", type=int, default=32)
    p.add_argument("--max-len", type=int, default=768)
    p.add_argument("--lr", type=float, default=2e-3)
    p.add_argument("--synthetic-ratio", type=float, default=0.5)
    p.add_argument("--device", choices=("xpu", "cpu", "cuda"), default="xpu")
    p.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "core_model_crossmem.json")
    )
    p.add_argument("--save-dir", default=str(REPO / "data" / "models" / "angela_core_crossmem"))
    args = p.parse_args()

    tok = Tokenizer.from_file(str(CORPUS / "tokenizer.json"))
    sessions: List[List[Tuple[str, str]]] = []
    with (CORPUS / "sessions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            turns = json.loads(line).get("turns") or []
            if turns:
                sessions.append([(str(u), str(a)) for u, a in turns])
            if len(sessions) >= args.sessions:
                break

    device = torch.device(args.device)
    model = CoreModel(
        tok.get_vocab_size(), args.d_model, args.layers, args.heads, args.memory, args.max_len
    ).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)

    def lr_lambda(s):
        return min(1.0, (s + 1) / 1000) * (
            0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi * min(1.0, s / max(1, args.steps))))
        )

    scheduler = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda)
    rng = random.Random(20261127)
    started = time.time()
    turns_seen = 0

    for step in range(args.steps):
        opt.zero_grad()
        step_loss, step_turns = 0.0, 0
        for _ in range(args.batch):
            synth = rng.random() < args.synthetic_ratio
            if synth:
                session, code = fresh_synthetic(rng)
            else:
                session, code = sessions[rng.randrange(len(sessions))], None
            state = None
            for turn_idx, (user, assistant) in enumerate(session[:6]):
                ids = [1] + tok.encode(user).ids[: args.max_len // 2] + [2]
                answer = tok.encode(assistant).ids[: args.max_len // 2] + [2]
                full = (ids + answer)[: args.max_len]
                x = torch.tensor([full[:-1]], dtype=torch.long, device=device)
                y = torch.tensor([full], dtype=torch.long, device=device)
                logits, state = model(x, state)
                prefix = logits.shape[1] - (y.shape[1] - 1)
                start = prefix + len(ids) - 1
                n = min(logits.shape[1] - start - 1, y.shape[1] - len(ids))
                loss = nn.functional.cross_entropy(
                    logits[0, start : start + n].reshape(-1, logits.shape[-1]),
                    y[0, len(ids) : len(ids) + n].reshape(-1),
                )
                total_loss = loss
                if synth and code and turn_idx == 0:
                    code_ids = tok.encode(code).ids[: args.memory]
                    aux = nn.functional.cross_entropy(
                        model.mem_readout(state[0, : len(code_ids)]).reshape(-1, logits.shape[-1]),
                        torch.tensor(code_ids, dtype=torch.long, device=device),
                    )
                    total_loss = loss + aux
                    if step % 500 == 0 and turn_idx == 0:
                        print(
                            f"aux step={step} aux={aux.item():.3f} main={loss.item():.3f}",
                            flush=True,
                        )
                (total_loss / args.batch).backward()
                state = state.detach()  # release this turn's graph before the next turn
                step_loss += loss.item()
                step_turns += 1
                turns_seen += 1
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        scheduler.step()
        if step % 200 == 0:
            print(
                f"step {step} loss={step_loss/max(1,step_turns):.4f} turns={turns_seen}", flush=True
            )

    def recall(mode):
        hits, samples = 0, []
        for _ in range(30):
            code = "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789") for _ in range(8))
            teach, ask, answer = f"記住代號 {code}", "代號？", code
            with torch.no_grad():
                t = torch.tensor([tok.encode(teach + "記住囉！").ids], device=device)
                _, state = model(t[:, :-1], None)
                if mode == "zero":
                    state = torch.zeros_like(state)
                elif mode == "random":
                    state = torch.randn_like(state)
                q = torch.tensor([tok.encode(ask).ids], device=device)
                gen = list(q[0].tolist())
                for _ in range(64):
                    logits, state = model(torch.tensor([gen], device=device), state)
                    nxt = int(logits[0, -1].argmax())
                    gen.append(nxt)
                    if nxt == 2:
                        break
            got = tok.decode(gen[len(q[0]) :]).strip().lstrip("。 ")
            ok = code in got
            hits += int(ok)
            if len(samples) < 3:
                samples.append({"gold": answer, "got": got[:120], "ok": ok})
        return hits, samples

    real, samples = recall("real")
    zero, _ = recall("zero")
    rnd, _ = recall("random")
    delta = real - max(zero, rnd)
    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "from scratch: one Transformer with cross-attention memory state",
        "steps": args.steps,
        "turns": turns_seen,
        "params": sum(x.numel() for x in model.parameters()),
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
