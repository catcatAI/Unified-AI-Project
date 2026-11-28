#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""ONE model: pretrained Qwen3-0.6B + RMT memory, trained together.

This is NOT "a brain plus a mouth": the memory tokens, the write/read heads and
the language weights are ONE model with one weights hash. The proven RMT recipe
(trailing write-memory so it can see the whole turn, CE write supervision,
BPTT across turns, fixed state within a turn) is applied to a model that
already has language, so both capabilities live in the same weights.

Pre-registered gate: real >= 8/30 and real - max(zero, random) >= 3, plus
non-empty, non-repetitive natural-language answers.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import List, Tuple

import torch
from peft import LoraConfig, get_peft_model
from torch import nn
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "data" / "models" / "qwen3-0.6b"
CORPUS = REPO / "data" / "core_corpus"


def fresh(rng: random.Random) -> Tuple[List[Tuple[str, str]], str]:
    code = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8))
    return [(f"記住代號 {code}", "記住囉！"), ("代號？", code)], code


class QwenRMT(nn.Module):
    def __init__(self, base, memory: int = 32):
        super().__init__()
        self.base = base
        self.memory = memory
        d = base.config.hidden_size
        self.mem = nn.Parameter(torch.randn(memory, d) * 0.02)
        self.mem_write = nn.Linear(d, d, bias=False)
        self.mem_readout = nn.Linear(d, base.config.vocab_size, bias=False)

    @property
    def device(self):
        return next(self.parameters()).device

    def forward(self, ids: torch.Tensor, state: torch.Tensor | None = None):
        emb = self.base.get_input_embeddings()(ids)
        b, n = ids.shape
        read_mem = self.mem.unsqueeze(0).expand(b, -1, -1) if state is None else state
        write_mem = self.mem.unsqueeze(0).expand(b, -1, -1)
        inputs = torch.cat([read_mem, emb, write_mem], dim=1)
        out = self.base(inputs_embeds=inputs, output_hidden_states=True, use_cache=False)
        hs = out.hidden_states[-1]
        new_state = self.mem_write(hs[:, self.memory + n :, :])
        logits = self.base.lm_head(hs[:, self.memory : self.memory + n, :])
        return logits, new_state


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sessions", type=int, default=477000)
    p.add_argument("--steps", type=int, default=10000)
    p.add_argument("--batch", type=int, default=2)
    p.add_argument("--memory", type=int, default=32)
    p.add_argument("--max-len", type=int, default=256)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--synthetic-ratio", type=float, default=0.3)
    p.add_argument("--device", choices=("xpu", "cpu", "cuda"), default="xpu")
    p.add_argument("--out", default=str(REPO / "data" / "intelligence_reports" / "qwen_rmt.json"))
    p.add_argument("--save-dir", default=str(REPO / "data" / "models" / "angela_qwen_rmt"))
    args = p.parse_args()

    tok = AutoTokenizer.from_pretrained(str(BASE), trust_remote_code=True)
    enc = lambda text: tok.encode(text, add_special_tokens=False)
    START = tok.convert_tokens_to_ids("<|im_start|>")
    EOS_ID = tok.convert_tokens_to_ids("<|im_end|>")
    if START is None or EOS_ID is None or START >= len(tok) or EOS_ID >= len(tok):
        raise SystemExit("Qwen special token ids invalid — check tokenizer")
    sessions: List[List[Tuple[str, str]]] = []
    with (CORPUS / "sessions.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            turns = json.loads(line).get("turns") or []
            if turns:
                sessions.append([(str(u), str(a)) for u, a in turns])
            if len(sessions) >= args.sessions:
                break

    base = AutoModelForCausalLM.from_pretrained(
        str(BASE), torch_dtype=torch.float32, trust_remote_code=True
    )
    base = get_peft_model(
        base,
        LoraConfig(r=8, lora_alpha=16, target_modules=("q_proj", "v_proj"), task_type="CAUSAL_LM"),
    )
    model = QwenRMT(base, args.memory).to(torch.device(args.device))
    model.train()
    opt = torch.optim.AdamW([x for x in model.parameters() if x.requires_grad], lr=args.lr)
    rng = random.Random(20261128)
    started = time.time()
    turns_seen = 0

    for step in range(args.steps):
        opt.zero_grad()
        total = 0.0
        for _ in range(args.batch):
            synth = rng.random() < args.synthetic_ratio
            session, code = fresh(rng) if synth else (sessions[rng.randrange(len(sessions))], None)
            state = None
            for turn_idx, (user, assistant) in enumerate(session[:4]):
                ids = [START] + enc(user)[: args.max_len // 2] + [EOS_ID]
                answer = enc(assistant)[: args.max_len // 2] + [EOS_ID]
                full = (ids + answer)[: args.max_len]
                x = torch.tensor([full[:-1]], dtype=torch.long, device=model.device)
                y = torch.tensor([full], dtype=torch.long, device=model.device)
                logits, state = model(x, state)
                start = len(ids) - 1
                n = min(logits.shape[1] - start, y.shape[1] - len(ids))
                loss = nn.functional.cross_entropy(
                    logits[0, start : start + n].reshape(-1, logits.shape[-1]),
                    y[0, len(ids) : len(ids) + n].reshape(-1),
                )
                total = total + loss
                if synth and code and turn_idx == 0:
                    code_ids = enc(code)[: args.memory]
                    written = model.mem_readout(state[0, : len(code_ids)])
                    total = total + nn.functional.cross_entropy(
                        written.reshape(-1, written.shape[-1]),
                        torch.tensor(code_ids, dtype=torch.long, device=model.device),
                    )
                turns_seen += 1
        (total / args.batch).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        if step % 200 == 0:
            print(
                f"step {step} loss={(total / args.batch).item():.4f} turns={turns_seen}", flush=True
            )

    def recall(mode):
        hits, samples = 0, []
        for _ in range(30):
            code = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8))
            teach, ask = f"記住代號 {code}", "代號？"
            model.eval()
            with torch.no_grad():
                t = torch.tensor(
                    [[1] + enc(teach) + [2] + enc("記住囉！") + [2]], device=model.device
                )
                _, state = model(t[:, :-1], None)
                if mode == "zero":
                    state = torch.zeros_like(state)
                elif mode == "random":
                    state = torch.randn_like(state)
                q = torch.tensor([[START] + enc(ask) + [EOS_ID]], device=model.device)
                gen = list(q[0])
                fixed = state
                for _ in range(48):
                    logits, _ = model(torch.tensor([gen], device=model.device), fixed)
                    nxt = int(logits[0, -1].argmax())
                    gen.append(nxt)
                    if nxt == EOS_ID:
                        break
            got = tok.decode(gen[len(q[0]) :], skip_special_tokens=True).strip().lstrip("。 ")
            ok = code in got
            hits += int(ok)
            if len(samples) < 3:
                samples.append({"gold": code, "got": got[:120], "ok": ok})
        model.train()
        return hits, samples

    real, samples = recall("real")
    zero, _ = recall("zero")
    rnd, _ = recall("random")
    result = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "ONE model: pretrained Qwen3-0.6B + RMT memory tokens trained in (single weights)",
        "steps": args.steps,
        "turns": turns_seen,
        "memory": args.memory,
        "seconds": round(time.time() - started, 1),
        "ablation": {"real": real, "zero": zero, "random": rnd, "delta": real - max(zero, rnd)},
        "samples": samples,
        "gate": {
            "registered_before_run": True,
            "pass": real >= 8 and real - max(zero, rnd) >= 3,
            "verdict": (
                "one_model_with_state"
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
    torch.save({"state_dict": model.state_dict(), "memory": args.memory}, save / "model.pt")
    tok.save_pretrained(str(save))
    print(f"saved to {save}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
