#!/usr/bin/env python
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2-L4]
# =============================================================================
"""Grade a causal transformer on the same AI+AL pairs as the SNN.

Why this exists
---------------
R4-R8 read gate **0/200** on the MVE-1 boundary for the token-level SNN. A 0
from one architecture says nothing about the *task* until a second, standard
architecture is run under identical conditions: same tokenizer, same batches,
same masked weighted objective, same epoch budget, same greedy decode, same
grading code. If the transformer also reads 0, the bottleneck is the task's
representation (state values and ``dt`` arrive as text atoms, so answering
requires three-digit arithmetic in token space) rather than the SNN's spiking
recurrence. If it clears the gate, the SNN is the problem and capacity is the
right next variable.

Fairness levers kept identical on purpose
-----------------------------------------
* **encoding** — this script does not re-implement the data format. It builds a
  ``TokenSNN`` for its ``_encode`` / ``make_batch_weighted`` only, so prompt
  framing, the ``\\n`` answer separator, the ``<al_out>`` cut and the loss
  weights are byte-identical to the SNN's.
* **objective** — cross-entropy on answer positions only, weighted mean with
  ``--tail-weight`` (1.0 = off), gradient clip 1.0, Adam ``lr`` 3e-3.
* **budget** — same epochs, batch and ``max_len``; the wall clock each side
  spends is reported rather than equalised, because equal *epochs* is the
  honest knob and the transformer is the faster optimiser.
* **grading** — ``probe_emergence_boundary.probe(model=...)``, the same
  instrument that produces the registered readings, including the affine
  learnability ceiling.

Not claimed: that a transformer at this size is "another AI scheme" in the
sense of being competitive with modern LLMs. It is the smallest standard
sequence model that shares the SNN's interface, which is what a comparison
needs.

Usage::

    ./.venv/bin/python scripts/compare_al_baselines.py \\
        --checkpoint data/checkpoints/ai_al_round8.pt --epochs 100 --device xpu
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
for extra in (ROOT / "apps" / "backend" / "src", ROOT / "scripts"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import probe_emergence_boundary as probemod  # noqa: E402  (needs the path above)
from ai.ed3n.token_snn import (  # noqa: E402
    AL_OUT_MARK,
    TokenConfig,
    TokenSNN,
    TokenVocab,
    CharVocab,
    resolve_device,
)

DEFAULT_TRAIN = ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_round7_train.jsonl"
DEFAULT_VAL = ROOT / "apps" / "backend" / "data" / "processed" / "ai_al_round7_val.jsonl"
REPORTS = ROOT / "data" / "intelligence_reports"


def read_pairs(path: Path) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    if not path.is_file():
        return pairs
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        pairs.append((str(row["input"]), str(row["output"])))
    return pairs


def fits(pairs: Sequence[Tuple[str, str]], vocab: Any, max_len: int) -> List[Tuple[str, str]]:
    keep = []
    for prompt, answer in pairs:
        need = 1 + len(vocab.encode(prompt.strip())) + 1 + len(vocab.encode(answer.strip())) + 1
        if need <= max_len:
            keep.append((prompt, answer))
    return keep


def _transformer(
    torch: Any, pad_id: int, cfg: TokenConfig, d_model: int = 256, ff: int = 512, layers: int = 2
) -> Any:
    """Causal transformer decoder: the cheapest standard sequence model.

    Sized to the SNN's *parameter count* (~1.24M, of which 1.05M is its 1024x1024
    recurrent matrix) rather than to its embedding width: the point of the
    baseline is that a standard architecture with the same capacity, data and
    objective fails or succeeds on the same task. Depth is 2 -- the SNN runs a
    single LIF layer, so the baseline is deliberately given the deeper setting
    and a 0 from it is strictly informative.
    """
    nn = torch.nn
    d = int(d_model)
    nhead = 4 if d % 4 == 0 else 1

    class _Transformer(torch.nn.Module):
        def __init__(self, vocab_size: int) -> None:
            super().__init__()
            self.embed = nn.Embedding(vocab_size, d, padding_idx=pad_id)
            self.pos = nn.Embedding(int(cfg.max_len) + 8, d)
            layer = nn.TransformerEncoderLayer(
                d_model=d,
                nhead=nhead,
                dim_feedforward=ff,
                dropout=0.0,
                batch_first=True,
                norm_first=True,
            )
            self.blocks = nn.TransformerEncoder(
                layer, num_layers=int(layers), enable_nested_tensor=False
            )
            self.out_norm = nn.LayerNorm(d)
            self.head = nn.Linear(d, vocab_size)

        def forward(self, ids: Any) -> Any:
            steps = ids.shape[1]
            pos = torch.arange(steps, device=ids.device).clamp(max=self.pos.num_embeddings - 1)
            x = self.embed(ids) + self.pos(pos)[None, :, :]
            pad = ids == pad_id
            mask = torch.triu(
                torch.ones((steps, steps), dtype=torch.bool, device=ids.device), diagonal=1
            )
            x = self.blocks(x, mask=mask, src_key_padding_mask=pad)
            return self.head(self.out_norm(x))

    return _Transformer


class BaselineLM:
    """The slice of ``TokenSNN``'s interface the instrument actually uses.

    ``encoder`` is a real ``TokenSNN`` used *only* for ``_encode`` /
    ``make_batch_weighted``: tokenisation, masking and loss weights therefore
    come from one implementation, not two.
    """

    def __init__(
        self,
        vocab: Any,
        cfg: TokenConfig,
        device: str = "auto",
        d_model: int = 256,
        ff: int = 512,
        layers: int = 2,
    ) -> None:
        import torch

        self.torch = torch
        self.vocab = vocab
        self.config = cfg
        self.device = resolve_device(torch, device)
        self.encoder = TokenSNN(vocab, cfg, device=self.device)
        self.net = _transformer(torch, vocab.pad_id, cfg, d_model, ff, layers)(len(vocab)).to(
            self.device
        )

    # -- training -----------------------------------------------------------
    def _ss_inputs(self, ids: Any, mask: Any, p: float) -> Any:
        """One-step scheduled sampling, mirrored from ``TokenSNN._ss_inputs``.

        Without it the baseline trains under a regime it is never graded in:
        R8's SNN ran ``--ss-final 0.5``, so a teacher-forced-only baseline would
        be handicapped by an asymmetry in *my* harness, not by its architecture.
        Answer positions carry the model's own prediction with probability
        ``p``; the loss is still scored against the untouched gold ids.
        """
        torch = self.torch
        if p <= 0.0:
            return ids
        with torch.no_grad():
            pred = self.net(ids)[:, :-1, :].argmax(dim=-1)
        guess = torch.full_like(ids, self.vocab.pad_id)
        guess[:, 1:] = pred
        choose = mask & (torch.rand(mask.shape, device=mask.device) < p)
        return torch.where(choose, guess, ids)

    def loss(self, ids: Any, mask: Any, weights: Any = None, targets: Any = None) -> Any:
        torch = self.torch
        logits = self.net(ids)[:, :-1, :]
        gold = ids if targets is None else targets
        targets = gold[:, 1:]
        keep = mask[:, 1:]
        flat_logits = logits.reshape(-1, logits.shape[-1])
        flat_targets = targets.reshape(-1)
        flat_keep = keep.reshape(-1)
        if int(flat_keep.sum()) == 0:
            return logits.sum() * 0.0
        per_tok = torch.nn.functional.cross_entropy(
            flat_logits[flat_keep], flat_targets[flat_keep], reduction="none"
        )
        if weights is None:
            return per_tok.mean()
        w = weights[:, 1:].reshape(-1)[flat_keep]
        return (per_tok * w).sum() / w.sum().clamp(min=1e-6)

    def train_on(
        self,
        pairs: Sequence[Tuple[str, str]],
        epochs: int = 100,
        batch_size: int = 32,
        lr: float = 3e-3,
        seed: int = 0,
        tail_weight: float = 1.0,
        ss_final: float = 0.0,
        log: Any = None,
    ) -> List[Dict[str, float]]:
        torch = self.torch
        torch.manual_seed(seed)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        history: List[Dict[str, float]] = []
        order = list(range(len(pairs)))
        for epoch in range(epochs):
            torch.manual_seed(seed + epoch)
            shuffled = order[:]
            random.Random(seed + epoch).shuffle(shuffled)
            p_ss = ss_final * (epoch + 1) / max(1, epochs) if ss_final > 0.0 else 0.0
            total = 0.0
            steps = 0
            for start in range(0, len(shuffled), batch_size):
                chunk = [pairs[i] for i in shuffled[start : start + batch_size]]
                ids, mask, _, weights = self.encoder.make_batch_weighted(chunk, tail_weight)
                opt.zero_grad()
                if tail_weight == 1.0 and p_ss == 0.0:
                    loss = self.loss(ids, mask)
                elif p_ss > 0.0:
                    loss = self.loss(
                        self._ss_inputs(ids, mask, p_ss), mask, weights, targets=ids
                    )
                else:
                    loss = self.loss(ids, mask, weights)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                opt.step()
                total += float(loss.detach())
                steps += 1
            history.append({"epoch": epoch, "loss": total / max(1, steps)})
            if log is not None:
                log(history[-1])
        return history

    # -- inference ----------------------------------------------------------
    def split_tf_accuracy(self, pairs: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
        """Teacher-forced accuracy split response / ``<al_out>`` block.

        Mirrors ``TokenSNN.split_tf_accuracy`` (same cut from ``_encode``, same
        answer-only mask) so the two columns mean the same thing. It answers a
        question the gate cannot: a high tail number with a 0 gate means the
        mapping is fit but greedy decoding drifts, while a low one means the
        mapping itself was never learned.
        """
        torch = self.torch
        was_training = self.net.training
        self.net.eval()
        resp_hit = resp_tot = tail_hit = tail_tot = 0
        with torch.no_grad():
            for start in range(0, len(pairs), 32):
                chunk = list(pairs[start : start + 32])
                ids, mask, _, _ = self.encoder.make_batch_weighted(chunk, 1.0)
                pred = self.net(ids)[:, :-1, :].argmax(dim=-1)
                target = ids[:, 1:]
                keep = mask[:, 1:]
                for i, (prompt, answer) in enumerate(chunk):
                    _, _, cut = self.encoder._encode(prompt, answer)
                    width = len(self.encoder._encode(prompt, answer)[0])
                    tail_from, tail_to = (cut, width - 1) if cut < width - 1 else (1, 0)
                    for pos in range(ids.shape[1] - 1):
                        if not bool(keep[i, pos]):
                            continue
                        ok = int(pred[i, pos] == target[i, pos])
                        if tail_from <= pos + 1 <= tail_to:
                            tail_hit += ok
                            tail_tot += 1
                        else:
                            resp_hit += ok
                            resp_tot += 1
        if was_training:
            self.net.train()
        return {
            "response_tf": round(resp_hit / max(1, resp_tot), 4),
            "tail_tf": round(tail_hit / max(1, tail_tot), 4),
            "response_tokens": resp_tot,
            "tail_tokens": tail_tot,
        }

    def generate(self, prompt: str, max_new: int = 64, temperature: float = 0.0) -> str:
        """Greedy decode, mirrored from ``TokenSNN.generate``.

        Same prompt framing, same stop set (eos/pad/bos), same budget; only the
        network differs. ``temperature`` is accepted for interface parity.
        """
        torch = self.torch
        ids, _ = self.encoder.encode_pair(prompt, "")
        ids = ids[:-1] if ids and ids[-1] == self.vocab.eos_id else ids
        ids = ids[: self.config.max_len - 1]
        self.net.eval()
        out: List[int] = []
        with torch.no_grad():
            cur = torch.tensor([ids], dtype=torch.long, device=self.device)
            for _ in range(max_new):
                logits = self.net(cur)[0, -1]
                nxt = int(torch.argmax(logits).item())
                if nxt == self.vocab.eos_id:
                    break
                if nxt == self.vocab.pad_id or nxt == self.vocab.bos_id:
                    break
                out.append(nxt)
                cur = torch.cat(
                    [cur, torch.tensor([[nxt]], dtype=torch.long, device=self.device)], dim=1
                )
        self.net.train()
        return str(self.vocab.decode(out))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.torch.save({"state": self.net.state_dict(), "config": self.config.to_dict()}, str(path))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--checkpoint", default=str(ROOT / "data" / "checkpoints" / "ai_al_round8.pt"),
                    help="SNN checkpoint: source of the tokenizer, max_len and the SNN reading")
    ap.add_argument("--train", default=str(DEFAULT_TRAIN))
    ap.add_argument("--val", default=str(DEFAULT_VAL))
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--tail-weight", type=float, default=1.0)
    ap.add_argument(
        "--ss-final",
        type=float,
        default=0.5,
        help="scheduled-sampling ceiling, matching the SNN round it is compared to "
        "(0.0 = off); a mismatched value silently changes the training regime",
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--d-model", type=int, default=256)
    ap.add_argument("--ff", type=int, default=512)
    ap.add_argument("--layers", type=int, default=2)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--which", default="all", choices=("holdout", "reference", "all"))
    ap.add_argument("--sensitivity-rows", type=int, default=24)
    ap.add_argument("--limit", type=int, default=0, help="probe only the first N rows (debug)")
    ap.add_argument("--out", default=str(REPORTS / "baseline_transformer.pt"))
    ap.add_argument("--report", default=str(REPORTS / "mve1_emergence_boundary_transformer.json"))
    ap.add_argument("--summary", default=str(REPORTS / "mve1_architecture_comparison.json"))
    ap.add_argument("--skip-snn", action="store_true", help="do not re-read the SNN checkpoint")
    args = ap.parse_args(argv)

    import torch

    ckpt = Path(args.checkpoint)
    payload = torch.load(str(ckpt), map_location="cpu", weights_only=True)
    vocab_data = payload["vocab"]
    vocab = (
        TokenVocab.from_dict(vocab_data)
        if vocab_data.get("kind") == "token"
        else CharVocab.from_dict(vocab_data)
    )
    cfg = TokenConfig(**payload["config"])

    train = fits(read_pairs(Path(args.train)), vocab, cfg.max_len)
    val = fits(read_pairs(Path(args.val)), vocab, cfg.max_len)
    if not train:
        print(f"no usable pairs in {args.train}")
        return 1
    print(
        f"vocab={len(vocab)} train={len(train)} val={len(val)} max_len={cfg.max_len} "
        f"epochs={args.epochs} tail_weight={args.tail_weight}",
        flush=True,
    )

    started = time.time()
    model = BaselineLM(
        vocab, cfg, device=args.device, d_model=args.d_model, ff=args.ff, layers=args.layers
    )
    n_params = sum(p.numel() for p in model.net.parameters())
    snn_params = sum(p.numel() for p in model.encoder.net.parameters())
    print(f"device={model.device} transformer_params={n_params:,} snn_params={snn_params:,}", flush=True)

    def log(row: Dict[str, float]) -> None:
        if (row["epoch"] + 1) % 5 == 0 or row["epoch"] == 0:
            print(f"  epoch {row['epoch'] + 1}: loss={row['loss']:.4f}", flush=True)

    history = model.train_on(
        train,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
        seed=args.seed,
        tail_weight=args.tail_weight,
        ss_final=args.ss_final,
        log=log,
    )
    train_seconds = round(time.time() - started, 1)
    model.save(Path(args.out))
    print(f"saved {args.out} (loss min {min(h['loss'] for h in history):.4f})", flush=True)
    tf_split = model.split_tf_accuracy(val) if val else None
    print(f"teacher-forced split: {tf_split}", flush=True)

    # The instrument grades whatever object it is handed; this is the same call
    # that produced the registered SNN readings.
    rc = probemod.probe(
        checkpoint=str(args.out),
        which=args.which,
        device=str(model.device),
        report=Path(args.report),
        limit=args.limit,
        sensitivity_rows=args.sensitivity_rows,
        model=model,
    )
    if rc != 0:
        return rc

    transformer = json.loads(Path(args.report).read_text(encoding="utf-8"))
    summary: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "conditions": {
            "train": str(args.train),
            "val": str(args.val),
            "pairs": {"train": len(train), "val": len(val)},
            "vocab": len(vocab),
            "max_len": cfg.max_len,
            "epochs": args.epochs,
            "batch": args.batch,
            "lr": args.lr,
            "tail_weight": args.tail_weight,
            "ss_final": args.ss_final,
            "greedy": True,
            "objective": "CE on answer positions, weighted mean, clip 1.0",
        },
        "transformer": {
            "params": n_params,
            "layers": args.layers,
            "d_model": args.d_model,
            "ff": args.ff,
            "train_seconds": train_seconds,
            "loss_min": round(min(h["loss"] for h in history), 4),
            "tf_split": tf_split,
            "gate": transformer.get("gate"),
            "holdout": transformer.get("holdout"),
            "format_ok": transformer.get("format_ok"),
            "marker_ok": transformer.get("marker_ok"),
            "copy_accuracy": transformer.get("copy_accuracy"),
            "input_output_correlation": transformer.get("input_output_correlation"),
            "output_diversity": {
                k: v
                for k, v in (transformer.get("output_diversity") or {}).items()
                if k != "modal"
            },
            "report": str(args.report),
        },
        "snn": None,
    }

    if not args.skip_snn:
        snn = TokenSNN.load(ckpt, map_location="cpu", device=args.device)
        snn_report = REPORTS / "mve1_emergence_boundary.json"
        if snn_report.is_file():
            old = json.loads(snn_report.read_text(encoding="utf-8"))
            train_report = REPORTS / "ai_al_round8.json"
            snn_tf = None
            if train_report.is_file():
                snn_tf = json.loads(train_report.read_text(encoding="utf-8")).get(
                    "eval_tf_split"
                )
            summary["snn"] = {
                "checkpoint": str(ckpt),
                "params": snn_params,
                "tf_split": snn_tf,
                "gate": old.get("gate"),
                "holdout": old.get("holdout"),
                "format_ok": old.get("format_ok"),
                "marker_ok": old.get("marker_ok"),
                "copy_accuracy": old.get("copy_accuracy"),
                "input_output_correlation": old.get("input_output_correlation"),
                "output_diversity": {
                    k: v
                    for k, v in (old.get("output_diversity") or {}).items()
                    if k != "modal"
                },
                "report": str(snn_report),
            }
        del snn

    summary["learnability"] = transformer.get("learnability")
    summary["gold_input_correlation"] = transformer.get("gold_input_correlation")
    out = Path(args.summary)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def _gate(entry: Optional[Dict[str, Any]]) -> str:
        if not entry:
            return "n/a"
        h = entry.get("holdout") or {}
        return f"{h.get('family_hits', '?')}/{h.get('n', '?')}"

    print("\narchitecture comparison (identical data, tokenizer, objective, grading)")
    print(f"  gate holdout   snn={_gate(summary['snn'])}  transformer={_gate(summary['transformer'])}")
    for key in ("format_ok", "marker_ok"):
        print(
            f"  {key:<14} snn={str((summary['snn'] or {}).get(key, 'n/a')):<6} "
            f"transformer={summary['transformer'].get(key)}"
        )
    print(f"  copy_accuracy  snn={(summary['snn'] or {}).get('copy_accuracy')}")
    print(f"                 transformer={summary['transformer'].get('copy_accuracy')}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
