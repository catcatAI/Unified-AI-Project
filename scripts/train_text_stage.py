#!/usr/bin/env python3
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# LAYER: learning
"""Stage L: can the core compress and *generate* text before it reasons?

Registered in ``CORE_GAP_ANALYSIS.md`` §47. The pantry corpus (stage P) has no
single turn that answers it, but the core cannot yet read a paragraph at all;
measuring reasoning on a carrier that cannot represent text would measure the
constraints we piled on to compensate. So language first, and the language stage
is registered before it runs.

Everything measured here uses the **same** ``GRUCore`` class and the same
``CoreState`` v1 as the state-binding rounds. No new model class, so the language
stage and the pantry stage cannot silently become different carriers.

Representation (fixed by §47.4)::

    0 = <pad>, 1 = <bos>, 2 = <eos>, 3..258 = byte 0..255

That is invertible (``decode(encode(x)) == x``), has no out-of-vocabulary token,
and makes BPC a per-byte number with no "how many bytes per token" conversion.

Corpus (§47.3)::

    general train     apps/backend/data/processed/core_train.jsonl   first 3.0 MB
    general hold-out  apps/backend/data/processed/core_val.jsonl     first 300 kB
    testimony train   pantry v2 train split (800 sessions)           1,014,924 B
    testimony hold-out pantry v2 held-out split (200 sessions)         254,050 B

Text overlap across the pantry splits is **intended** and recorded in §47.3: L
learns the language, P measures reasoning on unseen answer tuples. The hold-out
here is 200 sessions that are not in the training stream.

Gates (§47.6), all fixed before the run::

    L1  hold-out BPC < interpolated bigram floor
    L2  hold-out BPC < interpolated trigram floor
    L3  100 greedy 24-byte continuations: >= 90 distinct, mean longest common
        prefix with the truth > the trigram's
    L4  BPC with the carried state < BPC with the state reset every window
    L5  checkpoint loads into the same class (model_kind "gru", schema v1)
    L6  no oracle field or camera tag in the text stream
    L7  cost (parameters, seconds, device) recorded

The floors are computable, not chosen: counts come from the training bytes, the
interpolation weight is selected on the **last 5% of training**, and the
hold-out is only ever measured.

Usage::

    ./.venv/bin/python scripts/train_text_stage.py --seed 20261116 --epochs 5 \\
        --general-bytes 3000000 --general-holdout-bytes 300000 \\
        --pantry-sessions 1000 --out data/text_stage
    ./.venv/bin/python scripts/train_text_stage.py --check data/text_stage/<report>.json

What a pass would mean: the core can compress text and generate more than one
mode. What it would not mean: pantry transfer, "intelligence", or Chinese
ability (English and testimony are reported separately). §47.11.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

TASK_VERSION = "text-stage-v1"

# §47.4 - the vocabulary is a function of the representation, not a knob.
PAD_ID = 0
BOS_ID = 1
EOS_ID = 2
BYTE_OFFSET = 3
VOCAB_SIZE = BYTE_OFFSET + 256  # 259

# §47.5 - fixed before the run. A different value is a different registration.
SEED = 20261116
LEARNING_RATE = 1e-3
BATCH = 32
WINDOW = 128
RESET_EVERY = 4096
EPOCHS = 5
HIDDEN = 128
EMB = 64
CHUNK_SECONDS = 60.0

# §47.3 - the registered corpus sizes, checked rather than assumed.
GENERAL_BYTES = 3_000_000
GENERAL_HOLDOUT_BYTES = 300_000
PANTRY_SESSIONS = 1000
PANTRY_SEED = 20261113
PANTRY_TRAIN_BYTES = 1_014_924
PANTRY_HOLDOUT_BYTES = 254_050

GENERAL_TRAIN = "apps/backend/data/processed/core_train.jsonl"
GENERAL_HOLDOUT = "apps/backend/data/processed/core_val.jsonl"
PANTRY_SCRIPT = "scripts/gen_pantry_ecosystem.py"

DEV_FRACTION = 0.05  # the tail of the training bytes, where lambda is chosen
L3_PREFIXES = 100
L3_PREFIX_BYTES = 32
L3_CONTINUATION = 24
L3_MIN_DISTINCT = 90

# Interpolation grids. Reported, not tuned on the hold-out.
BIGRAM_LAMBDAS = (0.0, 0.3, 0.5, 0.7, 0.9, 0.97, 0.99)
TRIGRAM_GRID = (
    (0.0, 0.97),
    (0.3, 0.6),
    (0.5, 0.4),
    (0.7, 0.25),
    (0.8, 0.15),
    (0.9, 0.08),
    (0.95, 0.04),
    (0.97, 0.02),
)

SAMPLE_CONTINUATIONS = 20


# --------------------------------------------------------------------------- #
# representation
# --------------------------------------------------------------------------- #
class ByteTable:
    """Bytes as token ids. Invertible, closed, and the same ids everywhere."""

    pad_id = PAD_ID
    bos_id = BOS_ID
    eos_id = EOS_ID

    def __len__(self) -> int:
        return VOCAB_SIZE

    def encode(self, data: bytes) -> List[int]:
        return [BYTE_OFFSET + byte for byte in data]

    def decode(self, ids: Sequence[int]) -> bytes:
        out = bytearray()
        for token in ids:
            if token >= BYTE_OFFSET:
                out.append(token - BYTE_OFFSET)
        return bytes(out)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "kind": "byte",
            "token_count": VOCAB_SIZE,
            "specials": {"pad": PAD_ID, "bos": BOS_ID, "eos": EOS_ID},
            "byte_offset": BYTE_OFFSET,
        }


# --------------------------------------------------------------------------- #
# corpus
# --------------------------------------------------------------------------- #
def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            check=False,
            timeout=30,
        )
        return out.stdout.decode("utf-8", "replace").strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _resolved(value: Optional[str], default: str) -> Path:
    path = Path(value or default)
    return path if path.is_absolute() else REPO_ROOT / path


def load_general(path: Path, budget: int) -> bytes:
    """Whole lines only, up to ``budget`` bytes.

    Cutting mid-line would make the stream depend on the byte budget rather than
    on the data, and the registered number is "the first N bytes of whole
    lines".
    """
    if not path.exists():
        raise SystemExit(f"missing general corpus: {path}")
    out = bytearray()
    with path.open("rb") as handle:
        for raw in handle:
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = f"{row.get('input', '')} {row.get('output', '')}\n"
            encoded = text.encode("utf-8")
            if len(out) + len(encoded) > budget:
                break
            out.extend(encoded)
    if not out:
        raise SystemExit(f"no usable lines in {path}")
    return bytes(out)


def load_pantry(path: Optional[Path], sessions: int) -> Tuple[bytes, bytes, Dict[str, Any]]:
    """Pantry v2 testimony, or an existing corpus file (tests use the latter)."""
    if path is not None:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
        train = b"".join(
            ("\n".join(turn["user_input"] for turn in row["turns"]) + "\n").encode("utf-8")
            for row in rows
            if row["session_meta"]["split"] == "train"
        )
        heldout = b"".join(
            ("\n".join(turn["user_input"] for turn in row["turns"]) + "\n").encode("utf-8")
            for row in rows
            if row["session_meta"]["split"] == "heldout"
        )
        return train, heldout, {"source": str(path), "generated": False}

    spec = importlib.util.spec_from_file_location(
        "pantry_for_text_stage", REPO_ROOT / PANTRY_SCRIPT
    )
    if spec is None or spec.loader is None:  # pragma: no cover - repo layout broken
        raise SystemExit(f"cannot load {PANTRY_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_for_text_stage"] = module
    spec.loader.exec_module(module)
    splits = module.PantryEcosystemSynthesizer(
        seed=PANTRY_SEED, sessions=sessions, heldout_fraction=0.2
    ).generate()

    def render(rows: Sequence[Dict[str, Any]]) -> bytes:
        return b"".join(
            ("\n".join(turn["user_input"] for turn in row["turns"]) + "\n").encode("utf-8")
            for row in rows
        )

    return (
        render(splits["train"]),
        render(splits["heldout"]),
        {
            "source": PANTRY_SCRIPT,
            "generated": True,
            "seed": PANTRY_SEED,
            "sessions": sessions,
        },
    )


def oracle_tokens(rows: Sequence[Dict[str, Any]]) -> List[str]:
    """The structured answer fields, for L6."""
    tokens: List[str] = []
    for row in rows:
        oracle = row.get("ground_truth_oracle") or {}
        tokens.append(str(oracle.get("evidence_tag") or ""))
    return [token for token in tokens if token]


# --------------------------------------------------------------------------- #
# floors: what a count-based model achieves on the same bytes
# --------------------------------------------------------------------------- #
class CountFloors:
    """Interpolated unigram / bigram / trigram rates over raw bytes.

    Counts come from training bytes only. The interpolation weights are chosen
    on the tail of the training bytes (``DEV_FRACTION``), so the hold-out is
    never used to pick a baseline. Both floors are then recomputed on the full
    training bytes and measured once on the hold-out.
    """

    def __init__(self, train: bytes, *, smooth: float = 0.1) -> None:
        if len(train) < 64:
            raise ValueError("need at least 64 training bytes for a floor")
        self.smooth = float(smooth)
        self.train = train
        self.vocab = 256
        self.uni: collections.Counter = collections.Counter()
        self.bi: collections.Counter = collections.Counter()
        self.tri: collections.Counter = collections.Counter()
        self.bi_context: collections.Counter = collections.Counter()
        self.tri_context: collections.Counter = collections.Counter()

    def _observe(self, data: bytes) -> None:
        previous = None
        previous2 = None
        for byte in data:
            self.uni[byte] += 1
            if previous is not None:
                self.bi[(previous, byte)] += 1
                self.bi_context[previous] += 1
            if previous2 is not None and previous is not None:
                self.tri[(previous2, previous, byte)] += 1
                self.tri_context[(previous2, previous)] += 1
            previous2, previous = previous, byte

    def fit(self, data: bytes) -> "CountFloors":
        self.train = data
        self._observe(data)
        return self

    def clone(self) -> "CountFloors":
        other = CountFloors(self.train, smooth=self.smooth)
        other.uni = collections.Counter(self.uni)
        other.bi = collections.Counter(self.bi)
        other.tri = collections.Counter(self.tri)
        other.bi_context = collections.Counter(self.bi_context)
        other.tri_context = collections.Counter(self.tri_context)
        return other

    # -- probabilities -----------------------------------------------------

    def _p_uni(self, byte: int) -> float:
        total = sum(self.uni.values())
        denom = total + self.smooth * self.vocab
        return (self.uni[byte] + self.smooth) / max(1.0, denom)

    def _p_bi(self, previous: Optional[int], byte: int) -> float:
        if previous is None:
            return self._p_uni(byte)
        denom = self.bi_context[previous] + self.smooth * self.vocab
        return (self.bi.get((previous, byte), 0) + self.smooth) / max(1e-9, denom)

    def _p_tri(self, previous2: Optional[int], previous: Optional[int], byte: int) -> float:
        if previous2 is None or previous is None:
            return self._p_bi(previous, byte)
        denom = self.tri_context.get((previous2, previous), 0) + self.smooth * self.vocab
        if denom <= 0:
            return self._p_bi(previous, byte)
        return (self.tri.get((previous2, previous, byte), 0) + self.smooth) / denom

    def nll_bigram(self, data: bytes, lam: float) -> Tuple[float, int]:
        total = 0.0
        previous = None
        for byte in data:
            p = lam * self._p_bi(previous, byte) + (1.0 - lam) * self._p_uni(byte)
            total -= math.log(max(p, 1e-300))
            previous = byte
        return total, len(data)

    def nll_trigram(self, data: bytes, lam_tri: float, lam_bi: float) -> Tuple[float, int]:
        total = 0.0
        previous = None
        previous2 = None
        lam_uni = max(0.0, 1.0 - lam_tri - lam_bi)
        for byte in data:
            p = (
                lam_tri * self._p_tri(previous2, previous, byte)
                + lam_bi * self._p_bi(previous, byte)
                + lam_uni * self._p_uni(byte)
            )
            total -= math.log(max(p, 1e-300))
            previous2, previous = previous, byte
        return total, len(data)

    def choose_lambdas(self, dev: bytes) -> Dict[str, Any]:
        """Pick the strongest floor on the training tail, and report the grid."""
        bigram = []
        for lam in BIGRAM_LAMBDAS:
            nll, count = self.nll_bigram(dev, lam)
            bigram.append({"lambda": lam, "bpc": nll / max(1, count) / math.log(2)})
        trigram = []
        for lam_tri, lam_bi in TRIGRAM_GRID:
            nll, count = self.nll_trigram(dev, lam_tri, lam_bi)
            trigram.append(
                {
                    "lambda_trigram": lam_tri,
                    "lambda_bigram": lam_bi,
                    "lambda_unigram": round(max(0.0, 1.0 - lam_tri - lam_bi), 4),
                    "bpc": nll / max(1, count) / math.log(2),
                }
            )
        best_bigram = min(bigram, key=lambda row: row["bpc"])
        best_trigram = min(trigram, key=lambda row: row["bpc"])
        return {
            "dev_bytes": len(dev),
            "bigram": best_bigram,
            "trigram": best_trigram,
            "grids": {"bigram": bigram, "trigram": trigram},
        }

    def evaluate(
        self, data: bytes, *, lam_bi: float, lam_tri: float, lam_bigram: float
    ) -> Dict[str, float]:
        bigram_nll, bigram_n = self.nll_bigram(data, lam_bigram)
        tri_nll, tri_n = self.nll_trigram(data, lam_tri, lam_bi)
        return {
            "bigram_bpc": bigram_nll / max(1, bigram_n) / math.log(2),
            "trigram_bpc": tri_nll / max(1, tri_n) / math.log(2),
        }

    # -- greedy continuation (for L3's control) ----------------------------

    def greedy_continuation(
        self, prefix: bytes, length: int, *, lam_tri: float, lam_bi: float
    ) -> bytes:
        lam_uni = max(0.0, 1.0 - lam_tri - lam_bi)
        context = list(prefix[-2:])
        out = bytearray()
        for _ in range(length):
            previous2 = context[-2] if len(context) >= 2 else None
            previous = context[-1] if context else None
            best_byte = 0
            best_p = -1.0
            for byte in range(256):
                p = (
                    lam_tri * self._p_tri(previous2, previous, byte)
                    + lam_bi * self._p_bi(previous, byte)
                    + lam_uni * self._p_uni(byte)
                )
                if p > best_p:
                    best_p = p
                    best_byte = byte
            out.append(best_byte)
            context.append(best_byte)
        return bytes(out)


# --------------------------------------------------------------------------- #
# model
# --------------------------------------------------------------------------- #
def build_core(*, hidden: int, emb: int, device: str, seed: int = SEED):
    from ai.core.stateful_decoder import GRUCore

    return GRUCore(
        VOCAB_SIZE,
        hidden=hidden,
        emb=emb,
        chunk_seconds=CHUNK_SECONDS,
        seed=seed,
        device=device,
    )


def _resolve_device(wanted: str) -> str:
    from core.system.config.compute_device import resolve_torch_device

    return resolve_torch_device(wanted)


def _detach(state: Any) -> Any:
    """Keep the state content, drop the graph: truncated BPTT per window."""
    for name, value in state.tensors.items():
        if hasattr(value, "detach"):
            state.tensors[name] = value.detach()
    return state


def _segments(data: bytes, size: int) -> List[bytes]:
    return [data[start : start + size] for start in range(0, len(data) - size + 1, size)]


def _tensor(rows: Sequence[Sequence[int]], device: str):
    import torch

    return torch.as_tensor([list(row) for row in rows], dtype=torch.long, device=device)


def train(
    core: Any,
    data: bytes,
    *,
    device: str,
    epochs: int,
    batch: int,
    window: int,
    reset_every: int,
    lr: float,
    seed: int = SEED,
) -> Dict[str, Any]:
    """One pass per epoch over 4096-byte segments, 128-byte windows.

    The state is created at each segment boundary (the registered reset) and
    carried across the 32 windows inside it. Gradients are truncated at each
    window - BPTT over 4096 sequential cells would not fit - while the state's
    *content* still crosses the boundary, which is what L4 measures.
    """
    import torch
    import torch.nn.functional as F

    segments = _segments(data, reset_every)
    if not segments:
        raise SystemExit(f"training bytes ({len(data)}) are shorter than one segment")
    steps_per_segment = reset_every // window
    optimiser = torch.optim.Adam(list(core.parameters()), lr=lr)
    shuffler = torch.Generator().manual_seed(seed)
    history: List[Dict[str, Any]] = []
    started = time.time()
    core.train()

    for epoch in range(1, epochs + 1):
        order = torch.randperm(len(segments), generator=shuffler).tolist()
        running = 0.0
        batches = 0
        seen = 0
        for start in range(0, len(order), batch):
            group = [segments[index] for index in order[start : start + batch]]
            state = core.init_state(len(group))
            for step in range(steps_per_segment):
                offset = step * window
                inputs = [segment[offset : offset + window] for segment in group]
                targets = [segment[offset + 1 : offset + window + 1] for segment in group]
                # The final window ends at the segment boundary, so its last byte
                # has no target inside the segment: that position is simply not
                # scored, rather than inventing the next segment's first byte.
                lengths = {len(row) for row in targets}
                if len(lengths) != 1:
                    raise SystemExit("windows within a batch disagree in length")
                token_ids = [[BYTE_OFFSET + byte for byte in row] for row in inputs]
                target_ids = [[BYTE_OFFSET + byte for byte in row] for row in targets]
                width = lengths.pop()
                logits, state = core.ai_step(_tensor(token_ids, device), state)
                logits = logits[:, :width, :]
                target_tensor = _tensor(target_ids, device)
                loss = F.cross_entropy(
                    logits.reshape(-1, VOCAB_SIZE),
                    target_tensor.reshape(-1),
                    ignore_index=-100,
                )
                optimiser.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(list(core.parameters()), 1.0)
                optimiser.step()
                core.invalidate_hash()
                _detach(state)
                running += float(loss.detach().cpu())
                seen += 1
            batches += 1
        history.append(
            {
                "epoch": epoch,
                "windows": seen,
                "mean_window_loss": round(running / max(1, seen), 4),
                "seconds": round(time.time() - started, 1),
            }
        )
        print(
            f"  epoch {epoch}/{epochs}  windows={seen}  "
            f"loss={history[-1]['mean_window_loss']:.4f}  "
            f"elapsed={history[-1]['seconds']:.0f}s",
            flush=True,
        )
    return {
        "epochs_run": len(history),
        "windows": sum(row["windows"] for row in history),
        "seconds": round(time.time() - started, 2),
        "history": history,
    }


def evaluate_bpc(
    core: Any,
    data: bytes,
    *,
    device: str,
    batch: int,
    window: int,
    reset_every: int,
) -> Dict[str, Any]:
    """Bits per byte over full ``reset_every`` chunks; the remainder is dropped."""
    import torch
    import torch.nn.functional as F

    chunks = _segments(data, reset_every)
    if not chunks:
        return {"bpc": None, "bytes": 0, "windows": 0}
    steps = reset_every // window
    total_nll = 0.0
    total_tokens = 0
    was_training = core.modules()[0].training
    core.eval()
    try:
        with torch.no_grad():
            for start in range(0, len(chunks), batch):
                group = chunks[start : start + batch]
                state = core.init_state(len(group))
                for step in range(steps):
                    offset = step * window
                    widths = {len(segment[offset + 1 : offset + window + 1]) for segment in group}
                    if len(widths) != 1:
                        raise SystemExit("evaluation chunks disagree in length")
                    width = widths.pop()
                    token_ids = [
                        [BYTE_OFFSET + byte for byte in segment[offset : offset + window]]
                        for segment in group
                    ]
                    target_ids = [
                        [BYTE_OFFSET + byte for byte in segment[offset + 1 : offset + width + 1]]
                        for segment in group
                    ]
                    logits, state = core.ai_step(_tensor(token_ids, device), state)
                    logits = logits[:, :width, :]
                    target_tensor = _tensor(target_ids, device)
                    total_nll += float(
                        F.cross_entropy(
                            logits.reshape(-1, VOCAB_SIZE),
                            target_tensor.reshape(-1),
                            reduction="sum",
                        ).cpu()
                    )
                    total_tokens += int(target_tensor.numel())
    finally:
        if was_training:
            core.train()
    return {
        "bpc": total_nll / max(1, total_tokens) / math.log(2),
        "bytes": total_tokens,
        "windows": int(total_tokens / max(1, window)),
    }


def evaluate_bpc_reset(
    core: Any, data: bytes, *, device: str, batch: int, window: int
) -> Dict[str, Any]:
    """L4's control: same weights, same bytes, state thrown away every window."""
    import torch
    import torch.nn.functional as F

    chunks = _segments(data, window)
    if not chunks:
        return {"bpc": None, "bytes": 0}
    total_nll = 0.0
    total_tokens = 0
    was_training = core.modules()[0].training
    core.eval()
    try:
        with torch.no_grad():
            for start in range(0, len(chunks), batch):
                group = chunks[start : start + batch]
                state = core.init_state(len(group))
                token_ids = [[BYTE_OFFSET + byte for byte in segment] for segment in group]
                target_ids = [[BYTE_OFFSET + byte for byte in segment[1:]] for segment in group]
                # The last byte of a window has no target; the teacher-forced
                # logits one position earlier are enough, so score 127 bytes.
                logits, _ = core.ai_step(_tensor(token_ids, device), state)
                logits = logits[:, :-1, :]
                target_tensor = _tensor(target_ids, device)
                total_nll += float(
                    F.cross_entropy(
                        logits.reshape(-1, VOCAB_SIZE),
                        target_tensor.reshape(-1),
                        reduction="sum",
                    ).cpu()
                )
                total_tokens += int(target_tensor.numel())
    finally:
        if was_training:
            core.train()
    return {"bpc": total_nll / max(1, total_tokens) / math.log(2), "bytes": total_tokens}


def generate(core: Any, prefix: bytes, length: int, *, device: str) -> bytes:
    """Greedy continuation from a fresh state (no batch, no sampling)."""
    import torch

    core.eval()
    with torch.no_grad():
        state = core.init_state(1)
        logits, state = core.ai_step(
            _tensor([[BYTE_OFFSET + byte for byte in prefix]], device), state
        )
        token = int(torch.argmax(logits[0, -1]).cpu())
        out = bytearray()
        for index in range(length):
            if token >= BYTE_OFFSET:
                out.append(token - BYTE_OFFSET)
            logits, state = core.ai_step(_tensor([[token]], device), state)
            token = int(torch.argmax(logits[0, -1]).cpu())
    return bytes(out)


def _common_prefix(left: bytes, right: bytes) -> int:
    count = 0
    for a, b in zip(left, right):
        if a != b:
            break
        count += 1
    return count


def generation_gate(
    core: Any,
    holdout: bytes,
    floors: CountFloors,
    *,
    device: str,
    lambdas: Dict[str, float],
) -> Dict[str, Any]:
    """L3: many distinct continuations, and closer to the truth than trigram."""
    usable = len(holdout) - L3_PREFIX_BYTES - L3_CONTINUATION - 1
    if usable <= L3_PREFIXES:
        raise SystemExit("hold-out is too short for the L3 prefixes")
    stride = usable // L3_PREFIXES
    entries: List[Dict[str, Any]] = []
    for index in range(L3_PREFIXES):
        start = index * stride
        prefix = holdout[start : start + L3_PREFIX_BYTES]
        truth = holdout[start + L3_PREFIX_BYTES : start + L3_PREFIX_BYTES + L3_CONTINUATION]
        produced = generate(core, prefix, L3_CONTINUATION, device=device)
        control = floors.greedy_continuation(
            prefix,
            L3_CONTINUATION,
            lam_tri=lambdas["trigram"],
            lam_bi=lambdas["bigram"],
        )
        entries.append(
            {
                "prefix": prefix.decode("utf-8", "replace"),
                "truth": truth.decode("utf-8", "replace"),
                "model": produced.decode("utf-8", "replace"),
                "trigram": control.decode("utf-8", "replace"),
                "model_lcp": _common_prefix(produced, truth),
                "trigram_lcp": _common_prefix(control, truth),
            }
        )
    distinct = len({entry["model"] for entry in entries})
    model_lcp = sum(entry["model_lcp"] for entry in entries) / len(entries)
    trigram_lcp = sum(entry["trigram_lcp"] for entry in entries) / len(entries)
    return {
        "n": len(entries),
        "distinct": distinct,
        "mean_model_lcp": round(model_lcp, 3),
        "mean_trigram_lcp": round(trigram_lcp, 3),
        "samples": entries[:SAMPLE_CONTINUATIONS],
    }


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def gate_values(report: Dict[str, Any]) -> Dict[str, bool]:
    """Recompute L1-L4, L6, L7 from recorded numbers (L5 needs the checkpoint)."""
    results = report.get("results") or {}
    floors = report.get("floors") or {}
    generation = report.get("generation") or {}
    heldout = (results.get("heldout") or {}).get("bpc")
    bigram = (floors.get("holdout") or {}).get("bigram_bpc")
    trigram = (floors.get("holdout") or {}).get("trigram_bpc")
    carried = (results.get("heldout") or {}).get("bpc")
    reset = (results.get("heldout_reset") or {}).get("bpc")
    leak = report.get("leak_check") or {}
    cost = report.get("cost") or {}
    return {
        "L1_heldout_bpc_lt_bigram": (
            heldout is not None and bigram is not None and heldout < bigram
        ),
        "L2_heldout_bpc_lt_trigram": (
            heldout is not None and trigram is not None and heldout < trigram
        ),
        "L3_distinct_and_closer_than_trigram": (
            generation.get("distinct") is not None
            and generation["distinct"] >= L3_MIN_DISTINCT
            and generation.get("mean_model_lcp") is not None
            and generation.get("mean_trigram_lcp") is not None
            and generation["mean_model_lcp"] > generation["mean_trigram_lcp"]
        ),
        "L4_carried_state_beats_reset": (
            carried is not None and reset is not None and carried < reset
        ),
        "L6_no_oracle_in_text": bool(leak.get("clean")),
        "L7_cost_recorded": all(
            cost.get(key) not in (None, 0) for key in ("params", "train_seconds", "device")
        ),
    }


def check_report(path: Path) -> List[str]:
    """Re-verify a finished run without retraining (§47.10)."""
    problems: List[str] = []
    if not path.exists():
        return [f"{path} does not exist"]
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("task_version") != TASK_VERSION:
        problems.append(f"task_version {report.get('task_version')!r} != {TASK_VERSION!r}")

    recorded = report.get("gates") or {}
    recomputed = gate_values(report)
    for name, value in recomputed.items():
        if recorded.get(name) != value:
            problems.append(f"{name}: recorded {recorded.get(name)!r} but recomputes to {value!r}")

    # L5 cannot be read off numbers: load the checkpoint into the same class.
    checkpoint = report.get("checkpoint")
    config = report.get("config") or {}
    if not checkpoint or not Path(checkpoint).exists():
        problems.append("checkpoint is missing, so L5 cannot be re-verified")
    else:
        try:
            core = build_core(
                hidden=int(config.get("hidden", HIDDEN)),
                emb=int(config.get("emb", EMB)),
                device="cpu",
            )
            core.load_weights(checkpoint, strict_config=True)
            if core.config().get("model_kind") != "gru":
                problems.append("checkpoint model_kind is not 'gru'")
            state = core.init_state(1)
            if state.schema_version != 1:
                problems.append(f"state schema_version {state.schema_version} != 1")
        except Exception as exc:  # a check must report, not crash
            problems.append(f"L5 reload failed: {exc}")

    stored = report.get("leak_check") or {}
    if stored.get("clean") is not True:
        problems.append("L6 was not clean when recorded")
    return problems


# --------------------------------------------------------------------------- #
# driver
# --------------------------------------------------------------------------- #
def run(args: argparse.Namespace, stamp: str) -> Dict[str, Any]:
    import torch  # fail early with a clear message

    device = _resolve_device(args.device)
    started = time.time()

    general_train = load_general(_resolved(args.general_path, GENERAL_TRAIN), args.general_bytes)
    general_holdout = load_general(
        _resolved(args.general_holdout_path, GENERAL_HOLDOUT), args.general_holdout_bytes
    )
    pantry_path = Path(args.pantry_path) if args.pantry_path else None
    pantry_train, pantry_holdout, pantry_meta = load_pantry(pantry_path, args.pantry_sessions)

    corpus_checks: Dict[str, Any] = {
        "general_train_bytes": len(general_train),
        "general_holdout_bytes": len(general_holdout),
        "testimony_train_bytes": len(pantry_train),
        "testimony_holdout_bytes": len(pantry_holdout),
        "pantry": pantry_meta,
    }
    if pantry_path is None:
        corpus_checks["registered_sizes_match"] = (
            len(pantry_train) == PANTRY_TRAIN_BYTES and len(pantry_holdout) == PANTRY_HOLDOUT_BYTES
        )
        if not corpus_checks["registered_sizes_match"]:
            raise SystemExit(
                "the generated testimony does not match the registered sizes "
                f"({len(pantry_train)}/{len(pantry_holdout)} vs "
                f"{PANTRY_TRAIN_BYTES}/{PANTRY_HOLDOUT_BYTES}); the corpus or the "
                "generator changed since §47.3 was written"
            )

    # L6: the structured answer must not be in the text stream.
    streams = general_train + general_holdout + pantry_train + pantry_holdout
    leaks: List[str] = []
    for token in ("ground_truth_oracle", "expected_final_deduction", "evidence_tag"):
        if token.encode("utf-8") in streams:
            leaks.append(f"field name {token!r} appears in the text")
    rows: List[Dict[str, Any]] = []
    if pantry_path is None:
        spec = importlib.util.spec_from_file_location(
            "pantry_for_leak_check", REPO_ROOT / PANTRY_SCRIPT
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["pantry_for_leak_check"] = module
        spec.loader.exec_module(module)
        splits = module.PantryEcosystemSynthesizer(
            seed=PANTRY_SEED, sessions=args.pantry_sessions, heldout_fraction=0.2
        ).generate()
        rows = splits["train"] + splits["heldout"]
    else:
        rows = [
            json.loads(line)
            for line in pantry_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
    for tag in oracle_tokens(rows):
        if tag.encode("utf-8") in streams:
            leaks.append(f"camera tag {tag!r} appears in the text")
    leak_check = {
        "clean": not leaks,
        "problems": leaks,
        "note": (
            "names appear by design (the roll call); this gate is on the structured "
            "answer (camera tag and oracle field names), not on person names"
        ),
    }

    train_bytes = general_train + pantry_train
    report: Dict[str, Any] = {
        "task_version": TASK_VERSION,
        "git_head": _git_head(),
        "device": device,
        "config": {
            "token_count": VOCAB_SIZE,
            "hidden": args.hidden,
            "emb": args.emb,
            "chunk_seconds": CHUNK_SECONDS,
            "lr": args.lr,
            "batch": args.batch,
            "window": args.window,
            "reset_every": args.reset_every,
            "epochs": args.epochs,
            "seed": args.seed,
            "representation": ByteTable().to_dict(),
        },
        "corpus": {
            **corpus_checks,
            "train_bytes": len(train_bytes),
            "digests": {
                "general_train": _digest(general_train),
                "general_holdout": _digest(general_holdout),
                "testimony_train": _digest(pantry_train),
                "testimony_holdout": _digest(pantry_holdout),
            },
        },
        "leak_check": leak_check,
        "sizes": {
            "train": len(train_bytes),
            "heldout": len(general_holdout) + len(pantry_holdout),
        },
    }
    if not leak_check["clean"]:
        report["gates"] = gate_values(report)
        report["all_pass"] = False
        report["aborted"] = "leak check failed"
        return report

    # Floors: counts on the first 95% of the training bytes, lambda on the tail.
    split = int(len(train_bytes) * (1.0 - DEV_FRACTION))
    floor_fit = CountFloors(train_bytes[:split]).fit(train_bytes[:split])
    chosen = floor_fit.choose_lambdas(train_bytes[split:])
    floors = CountFloors(train_bytes).fit(train_bytes)
    lambdas = {
        "bigram": chosen["bigram"]["lambda"],
        "trigram": chosen["trigram"]["lambda_trigram"],
        "bigram_in_trigram": chosen["trigram"]["lambda_bigram"],
    }
    combined_holdout = general_holdout + pantry_holdout
    holdout_floors = floors.evaluate(
        combined_holdout,
        lam_bi=lambdas["bigram_in_trigram"],
        lam_tri=lambdas["trigram"],
        lam_bigram=lambdas["bigram"],
    )
    general_floors = floors.evaluate(
        general_holdout,
        lam_bi=lambdas["bigram_in_trigram"],
        lam_tri=lambdas["trigram"],
        lam_bigram=lambdas["bigram"],
    )
    testimony_floors = floors.evaluate(
        pantry_holdout,
        lam_bi=lambdas["bigram_in_trigram"],
        lam_tri=lambdas["trigram"],
        lam_bigram=lambdas["bigram"],
    )
    report["floors"] = {
        "lambda_selection": chosen,
        "lambdas": lambdas,
        "holdout": holdout_floors,
        "general": general_floors,
        "testimony": testimony_floors,
    }

    core = build_core(hidden=args.hidden, emb=args.emb, device=device)
    report["params"] = core.parameter_count()
    report["weights_hash"] = core.weights_hash()
    print(
        f"text stage: device={device} params={report['params']} "
        f"train={len(train_bytes)} B holdout={len(combined_holdout)} B",
        flush=True,
    )

    report["training"] = train(
        core,
        train_bytes,
        device=device,
        epochs=args.epochs,
        batch=args.batch,
        window=args.window,
        reset_every=args.reset_every,
        lr=args.lr,
        seed=args.seed,
    )

    heldout = {
        "combined": evaluate_bpc(
            core,
            combined_holdout,
            device=device,
            batch=args.batch,
            window=args.window,
            reset_every=args.reset_every,
        ),
        "general": evaluate_bpc(
            core,
            general_holdout,
            device=device,
            batch=args.batch,
            window=args.window,
            reset_every=args.reset_every,
        ),
        "testimony": evaluate_bpc(
            core,
            pantry_holdout,
            device=device,
            batch=args.batch,
            window=args.window,
            reset_every=args.reset_every,
        ),
    }
    reset_control = evaluate_bpc_reset(
        core,
        combined_holdout,
        device=device,
        batch=args.batch,
        window=args.window,
    )
    report["results"] = {
        "heldout": heldout["combined"],
        "heldout_general": heldout["general"],
        "heldout_testimony": heldout["testimony"],
        "heldout_reset": reset_control,
        # Diagnostics, not gates: unigram is the zero-order line.
        "heldout_unigram_bpc": None,
    }
    unigram = CountFloors(train_bytes).fit(train_bytes)
    unigram_nll, unigram_n = unigram.nll_bigram(combined_holdout, 0.0)
    report["results"]["heldout_unigram_bpc"] = unigram_nll / max(1, unigram_n) / math.log(2)

    report["generation"] = generation_gate(
        core,
        combined_holdout,
        floors,
        device=device,
        lambdas={
            "trigram": lambdas["trigram"],
            "bigram": lambdas["bigram_in_trigram"],
        },
    )

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = out_dir / f"text_stage_{stamp}.pt"
    core.save_weights(str(checkpoint))
    report["checkpoint"] = str(checkpoint)

    # L5: the same class and the same state schema, verified by loading it back.
    l5_ok = True
    l5_detail: Dict[str, Any] = {}
    try:
        reloaded = build_core(hidden=args.hidden, emb=args.emb, device="cpu")
        reloaded.load_weights(str(checkpoint), strict_config=True)
        state = reloaded.init_state(1)
        l5_detail = {
            "model_kind": reloaded.config().get("model_kind"),
            "state_schema": state.schema_version,
            "token_count": reloaded.config().get("token_count"),
            "strict_config": True,
        }
        l5_ok = (
            l5_detail["model_kind"] == "gru"
            and l5_detail["state_schema"] == 1
            and l5_detail["token_count"] == VOCAB_SIZE
        )
    except Exception as exc:  # report, do not crash: L5 is a gate, not a precondition
        l5_detail = {"error": str(exc)}
        l5_ok = False
    report["reload"] = l5_detail

    # Cost first: L7 is read from it, and a gate evaluated before its input
    # exists reports a false failure.
    report["cost"] = {
        "params": report["params"],
        "train_seconds": report["training"]["seconds"],
        "eval_seconds": round(time.time() - started - report["training"]["seconds"], 2),
        "device": device,
    }
    gates = gate_values(report)
    gates["L5_checkpoint_loads_same_class"] = l5_ok
    report["gates"] = gates
    report["all_pass"] = all(value is True for value in gates.values())
    report["wall_seconds"] = round(time.time() - started, 2)
    return report


def _print(report: Dict[str, Any], path: Path) -> None:
    print(
        f"\ntask      : {report['task_version']}  device={report['device']}  "
        f"params={report.get('params')}"
    )
    floors = report.get("floors") or {}
    results = report.get("results") or {}
    print(
        f"corpus    : general {report['corpus']['general_train_bytes']} B / "
        f"{report['corpus']['general_holdout_bytes']} B, "
        f"testimony {report['corpus']['testimony_train_bytes']} B / "
        f"{report['corpus']['testimony_holdout_bytes']} B"
    )
    print("\n              split      bpc")
    for name, key in (
        ("held-out combined", "heldout"),
        ("  general", "heldout_general"),
        ("  testimony", "heldout_testimony"),
        ("  reset control", "heldout_reset"),
    ):
        entry = results.get(key) or {}
        value = "n/a" if entry.get("bpc") is None else f"{entry['bpc']:.4f}"
        print(f"  {name:20s} {value}")

    def _number(value: Any) -> str:
        return "n/a" if value is None else f"{value:.4f}"

    holdout_floors = floors.get("holdout") or {}
    print(
        f"  bigram floor        {_number(holdout_floors.get('bigram_bpc'))}\n"
        f"  trigram floor       {_number(holdout_floors.get('trigram_bpc'))}\n"
        f"  unigram             {_number(results.get('heldout_unigram_bpc'))}"
    )
    generation = report.get("generation") or {}
    print(
        f"\ngeneration: {generation.get('distinct')}/{generation.get('n')} distinct, "
        f"model lcp {generation.get('mean_model_lcp')} vs trigram "
        f"{generation.get('mean_trigram_lcp')}"
    )
    print("\n  gates")
    for name, value in (report.get("gates") or {}).items():
        print(f"    {'PASS' if value is True else 'FAIL'}  {name}")
    print(f"\nall_pass   : {report.get('all_pass')}")
    print(f"report     : {path}")
    print(f"checkpoint : {report.get('checkpoint')}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Stage L: byte-level text for the core")
    parser.add_argument("--out", default="data/text_stage")
    parser.add_argument("--check", metavar="REPORT.json", help="re-verify a finished run")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--epochs", type=int, default=EPOCHS)
    parser.add_argument("--hidden", type=int, default=HIDDEN)
    parser.add_argument("--emb", type=int, default=EMB)
    parser.add_argument("--lr", type=float, default=LEARNING_RATE)
    parser.add_argument("--batch", type=int, default=BATCH)
    parser.add_argument("--window", type=int, default=WINDOW)
    parser.add_argument("--reset-every", type=int, default=RESET_EVERY)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--general-path", default=None)
    parser.add_argument("--general-holdout-path", default=None)
    parser.add_argument("--pantry-path", default=None)
    parser.add_argument("--general-bytes", type=int, default=GENERAL_BYTES)
    parser.add_argument("--general-holdout-bytes", type=int, default=GENERAL_HOLDOUT_BYTES)
    parser.add_argument("--pantry-sessions", type=int, default=PANTRY_SESSIONS)
    parser.add_argument("--require-pass", action="store_true", help="exit 1 unless gates pass")
    args = parser.parse_args(argv)

    if args.check:
        path = Path(args.check)
        if not path.is_absolute():
            path = REPO_ROOT / path
        problems = check_report(path)
        if problems:
            print(f"FAIL {path}")
            for problem in problems:
                print(f"  - {problem}")
            return 1
        print(f"OK {path}")
        return 0

    stamp = time.strftime("%Y%m%d-%H%M%S")
    started = time.time()
    report = run(args, stamp)
    report.setdefault("wall_seconds", round(time.time() - started, 2))

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"text_stage_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    _print(report, path)
    if report.get("aborted"):
        return 1
    return 0 if (report.get("all_pass") or not args.require_pass) else 1


if __name__ == "__main__":
    raise SystemExit(main())
