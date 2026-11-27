#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L4] [βγδ] [B] [L3-L5]
# =============================================================================
"""M0: pre-registered architecture A/B on the 149k language corpus.

NOT a repeat of §36 (992 AI+AL pairs) or MVE-1 (atoms). Same data, same
next-token objective, same token budget for every arm; val CE + free-running
exact on held-out answers are the only readouts.

Pre-registered falsification (write before running):
  * if the Transformer-6L arm's val CE > 3.5 → the bottleneck is tokenization/
    data, not the recurrent/spiking architecture; stop the architecture line.
  * an arm with free-running exact 0 is not "comparable" even if CE is low.

Usage
    ./.venv/bin/python scripts/probe_core_lm_ab.py --arms lif,gru,transformer,hybrid \
        --limit 20000 --tokens 200000 --out data/intelligence_reports/core_lm_ab.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
from torch import nn

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "apps" / "backend" / "data" / "processed" / "core_train.jsonl"


def _device() -> torch.device:
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return torch.device("xpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_rows(limit: int) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    with DATA.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            rows.append((item["input"], item["output"]))
            if limit and len(rows) >= limit:
                break
    return rows


def split(rows: List[Tuple[str, str]], val_ratio: float = 0.05):
    train, val = [], []
    for q, a in rows:
        digest = hashlib.sha1(f"core-lm-v1:{q}".encode()).hexdigest()
        bucket = int(digest[:8], 16) / 0xFFFFFFFF
        (val if bucket < val_ratio else train).append((q, a))
    return train, val


class CharVocab:
    def __init__(self, rows: List[Tuple[str, str]], max_size: int = 4096):
        counts: Counter = Counter()
        for q, a in rows:
            counts.update(q + "\n" + a)
        chars = [c for c, _ in counts.most_common(max_size - 3)]
        self.itos = ["<pad>", "<bos>", "<eos>"] + chars
        self.stoi = {c: i for i, c in enumerate(self.itos)}

    def encode(self, text: str) -> List[int]:
        return (
            [self.stoi["<bos>"]]
            + [self.stoi[c] for c in text if c in self.stoi]
            + [self.stoi["<eos>"]]
        )

    def decode(self, ids: List[int]) -> str:
        return "".join(self.itos[i] for i in ids if i >= 3)


class SubwordVocab:
    """Word/punctuation subwords + char fallback — a different representation
    from the baseline char vocab. NOT full BPE; named honestly."""

    def __init__(self, rows: List[Tuple[str, str]], target: int = 4096):
        import re
        from collections import Counter

        pattern = r"[A-Za-z0-9]+|\s+|."
        counts: Counter = Counter()
        for q, a in rows:
            counts.update(re.findall(pattern, q + "\n" + a))
        tokens = [t for t, _ in counts.most_common(target - 4)]
        self.itos = ["<pad>", "<bos>", "<eos>", "<unk>"] + tokens
        self.stoi = {t: i for i, t in enumerate(self.itos)}
        self._pattern = pattern

    def encode(self, text: str) -> List[int]:
        import re

        ids = [self.stoi["<bos>"]]
        for token in re.findall(self._pattern, text):
            if token in self.stoi:
                ids.append(self.stoi[token])
            else:
                ids.extend(self.stoi.get(c, self.stoi["<unk>"]) for c in token)
        return ids + [self.stoi["<eos>"]]

    def decode(self, ids: List[int]) -> str:
        return "".join(self.itos[i] for i in ids if i >= 4 and i < len(self.itos))


class LifCell(nn.Module):
    """Single-layer LIF with a surrogate-gradient hard sigmoid (SLAYER-style)."""

    def __init__(self, d_model: int, beta: float = 0.9, threshold: float = 1.0):
        super().__init__()
        self.rec = nn.Linear(d_model, d_model)
        self.beta, self.threshold = beta, threshold

    def forward(self, x: torch.Tensor, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        mem = self.beta * state + (1 - self.beta) * self.rec(x)
        spike = (mem - self.threshold).sigmoid() * 4.0 - 2.0  # surrogate; used for grads
        return spike, mem.detach()


class Arm(nn.Module):
    def __init__(self, kind: str, vocab: int, d_model: int = 256, layers: int = 2):
        super().__init__()
        self.kind = kind
        self.embed = nn.Embedding(vocab, d_model)
        self.pos = nn.Embedding(512, d_model)
        if kind == "transformer":
            layer = nn.TransformerEncoderLayer(
                d_model, 4, d_model * 2, dropout=0.0, batch_first=True
            )
            self.body = nn.TransformerEncoder(layer, 6 if layers == 6 else layers)
            self.readout = None
        elif kind == "gru":
            self.body = nn.GRU(d_model, d_model, 2, batch_first=True)
            self.readout = None
        elif kind == "lif":
            self.body = LifCell(d_model)
            self.readout = None
        elif kind == "hybrid":
            self.body = nn.GRU(d_model, d_model, 1, batch_first=True)
            self.attn = nn.MultiheadAttention(d_model, 4, batch_first=True)
            self.readout = None
        else:
            raise ValueError(kind)
        self.head = nn.Linear(d_model, vocab)

    def forward(self, ids: torch.Tensor) -> torch.Tensor:
        positions = torch.arange(ids.shape[1], device=ids.device).unsqueeze(0)
        x = self.embed(ids) + self.pos(positions)
        if self.kind == "transformer":
            mask = torch.triu(torch.ones(ids.shape[1], ids.shape[1], device=ids.device), 1).bool()
            x = self.body(x, mask=mask)
        elif self.kind in ("gru", "hybrid"):
            x, _ = self.body(x)
            if self.kind == "hybrid":
                x, _ = self.attn(x, x, x)
        else:
            mem = torch.zeros(x.shape[0], x.shape[2], device=x.device)
            out = []
            for t in range(x.shape[1]):
                spike, mem = self.body(x[:, t], mem)
                out.append(spike)
            x = torch.stack(out, dim=1)
        return self.head(x)


def batches(
    rows: List[Tuple[int, ...]],
    batch: int,
    device: torch.device,
    qlens: Optional[List[int]] = None,
):
    for start in range(0, len(rows), batch):
        chunk = rows[start : start + batch]
        width = max(len(r) for r in chunk)
        padded = torch.full((len(chunk), width), 0, dtype=torch.long, device=device)
        for i, row in enumerate(chunk):
            padded[i, : len(row)] = torch.tensor(row, dtype=torch.long, device=device)
        y = padded[:, 1:].clone()  # view would corrupt x when masking -100
        if qlens is not None:
            for i, q in enumerate(qlens[start : start + batch]):
                y[i, : max(0, min(q - 1, y.shape[1]))] = -100  # ignore question tokens
        yield padded[:, :-1], y


def greedy_answer(
    model: Arm, vocab: CharVocab, prompt: str, gold: str, device, max_new: int = 192
) -> Tuple[bool, str]:
    ids = [vocab.stoi["<bos>"]] + [vocab.stoi[c] for c in prompt if c in vocab.stoi]
    with torch.no_grad():
        for _ in range(max_new):
            x = torch.tensor([ids], dtype=torch.long, device=device)
            next_id = int(model(x)[0, -1].argmax().item())
            if next_id == vocab.stoi["<eos>"]:
                break
            ids.append(next_id)
    text = vocab.decode(ids[len(vocab.encode(prompt)) - 1 :]).strip()
    return text.strip() == gold.strip(), text[:160]


def train_arm(
    kind: str,
    train_rows,
    val_rows,
    vocab: CharVocab,
    tokens: int,
    device,
    seed: int,
    d_model: int = 256,
    loss_mode: str = "full",
):
    torch.manual_seed(seed)
    newline = vocab.stoi.get("\n", vocab.stoi["<unk>"] if "<unk>" in vocab.stoi else 0)
    encoded, qlens = [], []
    for q, a in train_rows:
        q_ids = [vocab.stoi["<bos>"]] + [vocab.stoi[c] for c in q if c in vocab.stoi]
        ids = (
            q_ids
            + [newline]
            + [vocab.stoi[c] for c in a if c in vocab.stoi]
            + [vocab.stoi["<eos>"]]
        )
        encoded.append(ids[:192])
        qlens.append(min(len(q_ids) + 1, len(ids[:192])))
    model = Arm(kind, len(vocab.itos), d_model=d_model).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=2e-3)
    seen, started = 0, time.time()
    rng = random.Random(seed)
    while seen < tokens:
        model.train()
        order = list(zip(encoded, qlens))
        rng.shuffle(order)
        ids_batch, q_batch = zip(*order)
        for x, y in batches(list(ids_batch), 8, device, q_batch if loss_mode == "answer" else None):
            if seen >= tokens:
                break
            if (
                int(x.max()) >= model.embed.num_embeddings
                or int(x.min()) < 0
                or x.shape[1] > model.pos.num_embeddings
            ):
                print(
                    f"BAD x min={int(x.min())} max={int(x.max())} width={x.shape[1]} emb={model.embed.num_embeddings} pos={model.pos.num_embeddings}",
                    flush=True,
                )
                raise SystemExit(3)
            logits = model(x)
            targets = y.clamp(min=0).unsqueeze(-1)
            nll = -torch.log_softmax(logits, dim=-1).gather(-1, targets).squeeze(-1)
            valid = (y != -100).to(logits.dtype)
            loss = (nll * valid).sum() / valid.sum().clamp(min=1)
            optim.zero_grad()
            loss.backward()
            optim.step()
            seen += x.numel()
    model.eval()
    val_ids, val_qlens = [], []
    for q, a in val_rows[:200]:
        q_ids = [vocab.stoi["<bos>"]] + [vocab.stoi[c] for c in q if c in vocab.stoi]
        ids = (
            q_ids
            + [newline]
            + [vocab.stoi[c] for c in a if c in vocab.stoi]
            + [vocab.stoi["<eos>"]]
        )
        val_ids.append(ids[:192])
        val_qlens.append(min(len(q_ids) + 1, len(ids[:192])))
    val_loss, n = 0.0, 0
    with torch.no_grad():
        for x, y in batches(val_ids, 8, device, val_qlens if loss_mode == "answer" else None):
            valid = y != -100
            val_loss += nn.functional.cross_entropy(
                model(x).reshape(-1, len(vocab.itos))[valid.reshape(-1)],
                y.reshape(-1)[valid.reshape(-1)],
            ).item() * int(valid.sum())
            n += int(valid.sum())
    hits = 0
    samples = []
    for q, a in val_rows[:30]:
        ok, text = greedy_answer(model, vocab, q + "\n", a, device)
        hits += int(ok)
        if len(samples) < 3:
            samples.append({"q": q[:80], "gold": a[:120], "got": text, "exact": ok})
    return {
        "kind": kind,
        "params": sum(p.numel() for p in model.parameters()),
        "tokens": seen,
        "val_ce": round(val_loss / max(n, 1), 4),
        "free_exact_30": hits,
        "samples": samples,
        "seconds": round(time.time() - started, 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arms", default="lif,gru,transformer,hybrid")
    parser.add_argument("--limit", type=int, default=20000)
    parser.add_argument("--tokens", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=20261127)
    parser.add_argument("--d-model", type=int, default=256)
    parser.add_argument("--vocab", choices=("char", "subword"), default="char")
    parser.add_argument("--loss", choices=("full", "answer"), default="full")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "xpu", "cuda"),
        default="auto",
        help="XPU can die under heavy concurrent load (UR_RESULT_ERROR_DEVICE_LOST)",
    )
    parser.add_argument(
        "--out", default=str(REPO / "data" / "intelligence_reports" / "core_lm_ab.json")
    )
    args = parser.parse_args()

    rows = load_rows(args.limit)
    train_rows, val_rows = split(rows)
    vocab = SubwordVocab(train_rows) if args.vocab == "subword" else CharVocab(train_rows)
    device = _device() if args.device == "auto" else torch.device(args.device)
    results = [
        train_arm(
            kind,
            train_rows,
            val_rows,
            vocab,
            args.tokens,
            device,
            args.seed,
            args.d_model,
            args.loss,
        )
        for kind in args.arms.split(",")
    ]
    transformer = next((r for r in results if r["kind"] == "transformer"), None)
    gate = {
        "registered_before_run": True,
        "transformer_val_ce_le_3_5": bool(transformer and transformer["val_ce"] <= 3.5),
        "verdict": (
            "not_evaluated"
            if transformer is None
            else (
                "data_or_tokenization_bottleneck"
                if transformer["val_ce"] > 3.5
                else "architecture_comparable"
            )
        ),
    }
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset": str(DATA.relative_to(REPO)),
        "rows": {"n": len(rows), "train": len(train_rows), "val": len(val_rows)},
        "vocab": len(vocab.itos),
        "device": str(device),
        "arms": results,
        "gate": gate,
        "note": "same 149k corpus/objective/token budget for every arm; free-running exact on 30 held-out answers; falsification registered in gate",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
