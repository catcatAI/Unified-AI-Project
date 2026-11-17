#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""§90: same corpus, same vocabulary, same budget, same seed — only the cell differs.

§89.18 narrowed the checkpoint table to a question it could not answer: the four
columns differ in corpus, vocabulary, budget *and* size at once, so 3/40 vs 0/40
is not a capability ranking. The fair comparison it asked for is this file:

* corpus — ``distill_train.jsonl``, all 5,144 rows, for both arms;
* vocabulary — the **checkpoint's own** 3,577 tokens (``token_snn_distill.pt``),
  so out-of-vocabulary rows are identical on both sides and identical to §89's
  ``distill`` column;
* budget — 100 epochs x 81 batches = 8,100 optimiser steps, batch 64, Adam
  lr 3e-3 cosine to 1e-5, gradient clip 1.0, teacher forcing, the stability
  guard on, no KD / scheduled sampling / tail weight;
* seed — 0 and 1, drawn the same way for both arms (``torch.manual_seed(seed)``
  before construction, ``seed + epoch`` per epoch inside ``train_on``);
* selection — the best **validation-loss** epoch on ``distill_val.jsonl``
  (281 rows), the same rule ``train_token_snn`` applies when ``--eval-every``
  is set, and never the frozen test;
* score — ``probe_core_callers.measure_holdout`` / ``measure_suites``, i.e. the
  §89 producer (``generate(max_new=48)``) and the strict scorer, on the same
  frozen 248-row hold-out and the same 65 items.

The only thing that changes is the recurrence: ``TokenSNN``'s LIF cells vs a
``nn.GRU`` of matched parameter count (``d_hidden=418`` -> 2,489,219 against
2,491,227, -0.08%). Everything else — embeddings, head, shifted masked CE,
greedy loop, optimizer, schedule — is the same code path.

Decision rule (written in ``CORE_GAP_ANALYSIS.md`` §90 before this ran): see
``decide()``. §90.8 fixes the wall-clock guard at 10,800 s and the GPU duty
ceiling at 50% (``scripts/gpu_limit.py --run --target 0.5``).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab  # noqa: E402
from compare_snn_gru import (  # noqa: E402
    GRUDecoder,
    count_params,
    gru_param_count,
)
from probe_core_callers import (  # noqa: E402
    _aggregate_holdout,
    _aggregate_suites,
    _registered_items,
    items_digest,
    measure_holdout,
    measure_suites,
    rows_digest,
    sha256_file,
)
from train_token_snn import exact_match, fits, read_pairs  # noqa: E402

DATA = REPO_ROOT / "apps" / "backend" / "data"
MODELS = DATA / "models"
PROCESSED = DATA / "processed"
OUT_DIR = REPO_ROOT / "data" / "e2_recipe_ab"

TRAIN = PROCESSED / "distill_train.jsonl"
VAL = PROCESSED / "distill_val.jsonl"
HOLDOUT = PROCESSED / "distill_val_holdout.jsonl"
REFERENCE = MODELS / "token_snn_distill.pt"

ARMS: Tuple[str, ...] = ("snn", "gru")
SEEDS: Tuple[int, ...] = (0, 1)

#: §90.2 — the budget is the recorded distill run's, so "same flour" is literal.
EPOCHS = 100
BATCH = 64
LR = 3e-3
MIN_LR = 1e-5
MAX_LEN = 192

#: §90.2 — GRU hidden size matched by ``match_gru_hidden`` to the SNN's params.
GRU_HIDDEN = 418

#: §90.5 — a difference smaller than this many hold-out rows is not a difference.
#: At n = 248 and p ~ 0.11 one binomial SE is ~2.0 pp, so 10 rows = 4.0 pp = 2 SE.
MOVE_ROWS = 10

#: §90.8 — stop before starting an arm rather than run past this wall clock.
MAX_SECONDS = 10800.0

#: Set by ``run()`` so ``train_arm`` can tag the phase it is in (§90.12).
SAMPLER: Optional[Any] = None

# Filled by ``run()`` before any arm trains; module-level so ``train_arm`` reads
# the same rows the report digests describe.
train_fit: List[Tuple[str, str]] = []
val_fit: List[Tuple[str, str]] = []
items: List[Any] = []


# -- recipe -----------------------------------------------------------------
def cosine_lr(epoch: int, epochs: int, lr: float = LR, min_lr: float = MIN_LR) -> float:
    """``train_token_snn.schedule`` with ``--warmup 0 --lr-schedule cosine``."""
    span = max(1, epochs)
    done = min(1.0, max(0.0, epoch / span))
    return min_lr + 0.5 * (lr - min_lr) * (1 + math.cos(math.pi * done))


def val_loss(model: TokenSNN, pairs: Sequence[Tuple[str, str]], batch: int = BATCH) -> float:
    """The CLI's validation loss: one teacher-forced pass, no generation."""
    import torch

    was = model.net.training
    model.net.eval()
    total, steps = 0.0, 0
    try:
        with torch.no_grad():
            for start in range(0, len(pairs), batch):
                chunk = list(pairs[start : start + batch])
                ids, mask, _ = model.make_batch(chunk)
                got = float(model.loss(ids, mask).detach())
                if math.isfinite(got):
                    total += got
                    steps += 1
    finally:
        if was:
            model.net.train()
    return total / steps if steps else float("nan")


def load_vocab() -> Tuple[TokenVocab, TokenConfig]:
    """§90.2: the vocabulary and config come from the checkpoint, not the corpus.

    Building a fresh vocabulary here would move the OOV rows — and the OOV rows
    are exactly the ones no model can answer — so both arms and §89's ``distill``
    column would stop being the same measurement.
    """
    import torch

    payload = torch.load(str(REFERENCE), map_location="cpu", weights_only=True)
    vocab = TokenVocab.from_dict(payload["vocab"])
    cfg = TokenConfig(**payload["config"])
    return vocab, cfg


def nearest_gru_hidden(vocab_size: int, cfg: TokenConfig, target: int) -> Tuple[int, int]:
    """Nearest GRU hidden size by parameter count, over a range wide enough here.

    ``compare_snn_gru.match_gru_hidden`` centres its search on
    ``sqrt(target/3)``, which assumes the recurrent block dominates. At this
    vocabulary (3,577 tokens) the head dominates instead, so that centre (911)
    sits 7x away from the real answer (418). The sweep is explicit, and the
    result is recorded in the report next to the SNN count.
    """
    best = (float("inf"), 0, 0)
    for d in range(2, 2001):
        n = gru_param_count(vocab_size, cfg, d)
        if abs(n - target) < best[0]:
            best = (float(abs(n - target)), d, n)
    return best[1], best[2]


def build_model(kind: str, vocab: TokenVocab, cfg: TokenConfig, device: str) -> TokenSNN:
    if kind == "snn":
        return TokenSNN(vocab, cfg, device=device)
    if kind == "gru":
        return GRUDecoder(vocab, cfg, device=device, d_hidden=GRU_HIDDEN)
    raise ValueError(f"unknown arm {kind!r}")


def _display(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_model(kind: str, path: Path, device: str = "cpu") -> TokenSNN:
    """Reload an arm checkpoint without touching ``GRUDecoder.load``."""
    if kind == "snn":
        return TokenSNN.load(path, map_location="cpu", device=device)
    import torch

    payload = torch.load(str(path), map_location="cpu", weights_only=True)
    if payload.get("kind") != "gru":
        raise ValueError(f"{path} is not a §90 GRU checkpoint")
    vocab = TokenVocab.from_dict(payload["vocab"])
    cfg = TokenConfig(**payload["config"])
    model = GRUDecoder(vocab, cfg, device=device, d_hidden=int(payload["d_hidden"]))
    model.net.load_state_dict(payload["state"])
    model.net.eval()
    return model


# -- resources --------------------------------------------------------------
def _cpu_share() -> float:
    row = [int(x) for x in Path("/proc/stat").read_text().splitlines()[0].split()[1:]]
    total = sum(row)
    idle = row[3] + (row[4] if len(row) > 4 else 0)
    return total, idle


def _proc_ticks() -> int:
    """utime + stime of this process, in clock ticks."""
    fields = Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()
    return int(fields[11]) + int(fields[12])


class Sampler(threading.Thread):
    """1 Hz sample: whole-machine CPU/RAM/swap/GPU **and this process's CPU**.

    §90.11 recorded an unattributed 80% whole-machine peak: the machine sample
    cannot tell our two training threads apart from another application. The
    process counter (``/proc/self/stat``) and the phase tag make the next run
    attributable — reporting only, nothing about training changes.
    """

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.stop_flag = threading.Event()
        self.samples: List[Dict[str, Any]] = []
        self.phase = "start"

    def run(self) -> None:
        try:
            total0, idle0 = _cpu_share()
            ticks0 = _proc_ticks()
        except Exception:  # pragma: no cover - /proc is Linux-only
            return
        while not self.stop_flag.is_set():
            wall0 = time.monotonic()
            self.stop_flag.wait(1.0)
            wall = max(1e-6, time.monotonic() - wall0)
            try:
                total1, idle1 = _cpu_share()
                ticks1 = _proc_ticks()
                dt, di = max(1, total1 - total0), idle1 - idle0
                total0, idle0 = total1, idle1
                hz = float(os.sysconf("SC_CLK_TCK"))
                proc = 100.0 * (ticks1 - ticks0) / (hz * wall)
                ticks0 = ticks1
                cpu = 100.0 * (1.0 - di / dt)
                mem = {}
                for line in Path("/proc/meminfo").read_text().splitlines():
                    key, _, rest = line.partition(":")
                    mem[key] = int(rest.split()[0])
                ram = 100.0 * (1.0 - mem["MemAvailable"] / mem["MemTotal"])
                swap = 100.0 * (1.0 - mem["SwapFree"] / max(1, mem["SwapTotal"]))
                gpu = -1.0
                for path in sorted(Path("/sys/class/drm").glob("card*/device/gpu_busy_percent")):
                    try:
                        gpu = max(gpu, float(path.read_text().strip()))
                    except OSError:
                        pass
                self.samples.append(
                    {
                        "cpu": cpu,
                        "proc": proc,
                        "ram": ram,
                        "swap": swap,
                        "gpu_busy": gpu,
                        "phase": self.phase,
                    }
                )
            except Exception:
                continue

    def summary(self) -> Dict[str, Any]:
        if not self.samples:
            return {}
        cells = {
            key: [s[key] for s in self.samples if s[key] >= 0]
            for key in ("cpu", "proc", "ram", "swap", "gpu_busy")
        }
        out: Dict[str, Any] = {
            f"{key}_max": round(max(values), 2) for key, values in cells.items() if values
        }
        phases: Dict[str, Dict[str, float]] = {}
        for sample in self.samples:
            cell = phases.setdefault(sample["phase"], {"n": 0, "cpu_max": 0.0, "proc_max": 0.0})
            cell["n"] += 1
            cell["cpu_max"] = round(max(cell["cpu_max"], sample["cpu"]), 2)
            cell["proc_max"] = round(max(cell["proc_max"], sample["proc"]), 2)
        out["by_phase"] = phases
        out["samples"] = len(self.samples)
        return out


# -- one arm ----------------------------------------------------------------
def train_arm(
    kind: str,
    seed: int,
    vocab: TokenVocab,
    cfg: TokenConfig,
    device: str,
    score: bool = True,
    restore: bool = True,
) -> Dict[str, Any]:
    import torch

    torch.manual_seed(seed)
    model = build_model(kind, vocab, cfg, device)
    params = int(count_params(model))

    history: List[Dict[str, Any]] = []
    val_curve: List[Dict[str, float]] = []
    best: Dict[str, Any] = {"loss": float("inf"), "epoch": -1, "state": None}

    def log_row(row: Dict[str, Any]) -> None:
        loss = float(row["loss"])
        record = {"epoch": int(row["epoch"]) + 1, "loss": round(loss, 6), "lr": row.get("lr")}
        history.append(record)
        if not math.isfinite(loss):
            return
        got = val_loss(model, val_fit)
        val_curve.append({"epoch": record["epoch"], "val_loss": round(got, 6)})
        if math.isfinite(got) and got < best["loss"]:
            best["loss"] = got
            best["epoch"] = record["epoch"]
            best["state"] = {k: v.detach().clone() for k, v in model.net.state_dict().items()}

    started = time.time()
    if SAMPLER is not None:
        SAMPLER.phase = "train"
    model.train_on(
        train_fit,
        epochs=EPOCHS,
        batch_size=BATCH,
        lr=LR,
        log=log_row,
        lr_at=lambda epoch: cosine_lr(epoch, EPOCHS),
        guard=True,
        min_lr=MIN_LR,
        seed=seed,
    )
    train_seconds = time.time() - started

    restored = ""
    if restore and best["state"] is not None and val_curve:
        last = val_curve[-1]["val_loss"]
        if math.isfinite(best["loss"]) and best["loss"] < last:
            model.net.load_state_dict(best["state"])
            restored = f"epoch {best['epoch']} (val_loss={best['loss']:.4f}) over {last:.4f}"

    out = OUT_DIR / "checkpoints" / f"{kind}_seed{seed}.pt"
    model.save(out)

    if SAMPLER is not None:
        SAMPLER.phase = "eval"
    train_match = {"n": 0, "exact": 0.0}
    tf: Dict[str, Any] = {}
    holdout_rows: List[Dict[str, Any]] = []
    suite_rows: List[Dict[str, Any]] = []
    if score:
        with contextlib.redirect_stdout(io.StringIO()):
            train_match = exact_match(model, train_fit, 200, seed=1)
        tf = model.tf_accuracy(fits(read_pairs(HOLDOUT), vocab, cfg.max_len))
        model.net.to("cpu")
        model.device = "cpu"
        holdout_rows = measure_holdout(model)
        suite_rows = measure_suites(items, model)

    if SAMPLER is not None:
        SAMPLER.phase = "between"
    return {
        "arm": kind,
        "seed": seed,
        "params": params,
        "checkpoint": _display(out),
        "sha256": sha256_file(out),
        "train_seconds": round(train_seconds, 1),
        "steps": EPOCHS * math.ceil(len(train_fit) / BATCH),
        "restored": restored,
        "restore": bool(restore),
        "history": history,
        "val_curve": val_curve,
        "best_val": None if not math.isfinite(best["loss"]) else round(best["loss"], 6),
        "best_epoch": best["epoch"],
        "train_exact_200": train_match,
        "tf_holdout": tf,
        "holdout": _aggregate_holdout(holdout_rows) if score else {},
        "holdout_rows": holdout_rows,
        "suites": _aggregate_suites(suite_rows) if score else {},
        "suite_rows": suite_rows,
        "scored": bool(score),
    }


# -- decision (registered §90.5) --------------------------------------------
def decide(runs: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_arm: Dict[str, List[int]] = {arm: [] for arm in ARMS}
    for run in runs:
        value = run.get("holdout", {}).get("exact_raw")
        if run["arm"] in by_arm and value is not None:
            by_arm[run["arm"]].append(int(value))
    if not all(by_arm[arm] for arm in ARMS):
        return {"verdict": "not-decided-missing-arm", "by_arm": by_arm}
    snn, gru = by_arm["snn"], by_arm["gru"]
    mean_snn = sum(snn) / len(snn)
    mean_gru = sum(gru) / len(gru)
    delta = mean_gru - mean_snn
    separated = (min(gru) > max(snn)) or (max(gru) < min(snn))
    if delta >= MOVE_ROWS and separated:
        verdict = "recipe-moves"
    elif -delta >= MOVE_ROWS and separated:
        verdict = "recipe-moves-against"
    else:
        verdict = "recipe-invariant"
    return {
        "verdict": verdict,
        "by_arm": by_arm,
        "mean_snn_rows": round(mean_snn, 2),
        "mean_gru_rows": round(mean_gru, 2),
        "delta_rows": round(delta, 2),
        "delta_pp": round(100.0 * delta / 248.0, 2),
        "ranges_separated": separated,
        "move_rows": MOVE_ROWS,
        "n_rows": 248,
    }


# -- run --------------------------------------------------------------------
def run(args: argparse.Namespace) -> Dict[str, Any]:
    global train_fit, val_fit, items, SAMPLER

    vocab, cfg = load_vocab()
    train_pairs = read_pairs(TRAIN)
    val_pairs = read_pairs(VAL)
    train_fit = fits(train_pairs, vocab, cfg.max_len)
    val_fit = fits(val_pairs, vocab, cfg.max_len)
    items = _registered_items()

    print(
        f"vocab={len(vocab)} train={len(train_pairs)} (fit {len(train_fit)}) "
        f"val={len(val_pairs)} (fit {len(val_fit)}) items={len(items)}",
        flush=True,
    )
    snn_params = int(count_params(build_model("snn", vocab, cfg, "cpu")))
    matched_hidden, matched_params = nearest_gru_hidden(len(vocab), cfg, snn_params)
    print(
        f"params: snn={snn_params} gru(d={GRU_HIDDEN})="
        f"{gru_param_count(len(vocab), cfg, GRU_HIDDEN)} "
        f"(nearest to the SNN: d={matched_hidden} -> {matched_params})",
        flush=True,
    )

    sampler = Sampler()
    sampler.start()
    SAMPLER = sampler
    report: Dict[str, Any] = {
        "epochs": EPOCHS,
        "batch": BATCH,
        "lr": LR,
        "min_lr": MIN_LR,
        "steps_per_epoch": math.ceil(len(train_fit) / BATCH),
        "seeds": list(SEEDS),
        "gru_hidden": GRU_HIDDEN,
        "gru_nearest_hidden": matched_hidden,
        "gru_nearest_params": matched_params,
        "snn_params": snn_params,
        "train_rows": len(train_pairs),
        "train_fit": len(train_fit),
        "val_fit": len(val_fit),
        "vocab_size": len(vocab),
        "train_digest": rows_digest(train_pairs),
        "holdout_digest": rows_digest(read_pairs(HOLDOUT)),
        "items_digest": items_digest([item.id for item in items]),
        "reference_checkpoint": str(REFERENCE.relative_to(REPO_ROOT)),
        "reference_sha256": sha256_file(REFERENCE),
        "runs": [],
        "device": None,
    }
    import torch

    device = (
        args.device if args.device != "auto" else ("xpu" if torch.xpu.is_available() else "cpu")
    )
    report["device"] = device
    started = time.time()
    try:
        for kind in ARMS:
            for seed in SEEDS:
                if time.time() - started > MAX_SECONDS:
                    report["stopped_early"] = True
                    break
                print(f"\n== {kind} seed {seed} ==", flush=True)
                row = train_arm(
                    kind,
                    seed,
                    vocab,
                    cfg,
                    device,
                    score=not args.no_score,
                    restore=not args.no_restore,
                )
                print(
                    f"   holdout exact_raw {row['holdout'].get('exact_raw', 'n/a')}"
                    f"/{row['holdout'].get('n', 'n/a')}"
                    f"  math {row['suites'].get('math', 'n/a')}/40"
                    f"  knowledge {row['suites'].get('knowledge', 'n/a')}/15"
                    f"  code {row['suites'].get('code', 'n/a')}/10"
                    f"  ({row['train_seconds']}s)",
                    flush=True,
                )
                report["runs"].append(row)
                (OUT_DIR / "report.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            if report.get("stopped_early"):
                break
    finally:
        sampler.stop_flag.set()
        sampler.join(timeout=5)

    report["resource"] = sampler.summary()
    report["wall_seconds"] = round(time.time() - started, 1)
    report["decision"] = decide(report["runs"])
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nwrote {OUT_DIR / 'report.json'}", flush=True)
    print(json.dumps(report["decision"], ensure_ascii=False, indent=2), flush=True)
    return report


def check(report_path: Path) -> Tuple[bool, str]:
    """Recompute every aggregate from the stored rows; re-run one hold-out arm."""
    report = json.loads(report_path.read_text(encoding="utf-8"))
    problems: List[str] = []
    if report["holdout_digest"] != rows_digest(read_pairs(HOLDOUT)):
        problems.append("hold-out rows changed since the run")
    if report["items_digest"] != items_digest([item.id for item in _registered_items()]):
        problems.append("the 65 registered items changed since the run")
    expected = {arm: [] for arm in ARMS}
    for row in report["runs"]:
        recomputed = _aggregate_holdout(row["holdout_rows"])
        if recomputed != row["holdout"]:
            problems.append(
                f"{row['arm']} seed{row['seed']}: hold-out aggregate does not recompute"
            )
        if _aggregate_suites(row["suite_rows"]) != row["suites"]:
            problems.append(f"{row['arm']} seed{row['seed']}: suite aggregate does not recompute")
        path = REPO_ROOT / row["checkpoint"]
        if not path.is_file():
            problems.append(f"missing checkpoint {row['checkpoint']}")
        elif sha256_file(path) != row["sha256"]:
            problems.append(f"sha256 changed for {row['checkpoint']}")
        expected[row["arm"]].append(int(row["holdout"]["exact_raw"]))
    if decide(report["runs"])["verdict"] != report["decision"]["verdict"]:
        problems.append("decision does not recompute")
    first = report["runs"][0]
    model = load_model(first["arm"], REPO_ROOT / first["checkpoint"])
    rerun = measure_holdout(model)
    differing = sum(1 for a, b in zip(rerun, first["holdout_rows"]) if a["answer"] != b["answer"])
    if differing:
        problems.append(f"hold-out regenerated {differing} different answers")
    if problems:
        return False, "; ".join(problems)
    return True, (
        f"check OK ({len(report['runs'])} runs recomputed, "
        f"{first['arm']} seed{first['seed']} hold-out re-run row-for-row)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--device", default="auto")
    ap.add_argument("--epochs", type=int, default=EPOCHS, help="smoke only; §90 is 100")
    ap.add_argument("--seeds", default=",".join(str(s) for s in SEEDS), help="smoke only")
    ap.add_argument("--no-score", action="store_true", help="smoke only: train, do not measure")
    ap.add_argument(
        "--no-restore",
        action="store_true",
        help="§90.11 diagnostic: keep the final epoch instead of the best val_loss epoch",
    )
    ap.add_argument("--check", default="")
    return ap


def main() -> int:
    global OUT_DIR, EPOCHS, SEEDS
    args = build_parser().parse_args()
    if args.check:
        ok, message = check(Path(args.check))
        print(message)
        return 0 if ok else 1
    OUT_DIR = Path(args.out_dir)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    EPOCHS = int(args.epochs)
    SEEDS = tuple(int(s) for s in str(args.seeds).split(",") if s.strip())
    run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
