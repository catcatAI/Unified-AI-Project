#!/usr/bin/env python3
# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
# LAYER: learning
"""Round 5: does the state carry content, and does generation read it back?

``CORE_GAP_ANALYSIS.md`` §43 registers this before the run. The short version:

* Turn 1 teaches one pair, ``remember <name> = <value> .``, with **no loss**.
* ``al_step(120 s)`` — the production turn gap.
* Turn 2 asks ``<name> ?`` and the model must generate ``<value> .``.

The value never appears in turn 2's input, so the state is the only channel that
carries it. Every split except ``train`` is made of strings never seen in
training, so a table cannot pass; the leak check is mechanical and is recorded
in the report.

What the four measurements are for:

* ``dev`` — same name pool as training, fresh values: did the *mechanism* form?
* ``heldout_names`` — new names, fresh values, with the turn gap: the G2 number.
* ``zero_state`` — same questions with ``h`` zeroed after teaching: the answer
  must come from the state, so this must collapse. If it does not, the run is
  void and the report says so rather than explaining the good number away.
* ``cold`` — the teaching turn skipped entirely: independent evidence for the
  same thing, and it also catches a high-frequency string being emitted.

``wrong_name`` is a *diagnostic*: teach one name, ask a different, untaught one.
It separates "the value was carried" from "the pair was used".

This round does not touch production and does not use any benchmark item, so it
cannot move the core score. It changes *why* the score is 0.00.

Usage::

    ./.venv/bin/python scripts/train_state_content.py --out data/state_content
    ./.venv/bin/python scripts/train_state_content.py --smoke      # ~1 minute
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

TASK_VERSION = "state-content-v1"
SEED = 20261113

# Closed alphabets: every character a name or value can contain is in ALPHABET,
# so a held-out word is a new *combination*, never an unknown token.
CONSONANTS = "bdfgklmnprstvz"
VOWELS = "aeiou"
ALPHABET = CONSONANTS + VOWELS + "0123456789" + " .?="
SPECIALS = ("<pad>", "<bos>", "<eos>", "<unk>")

NAME_SYLLABLES = 2
VALUE_SYLLABLES = 3

# Fixed by §43.4. Changing one of these is a new round, not a rerun.
HIDDEN = 128
EMB = 64
CHUNK_SECONDS = 60.0
LEARNING_RATE = 3e-3
BATCH = 128
MAX_EPOCHS = 24
EARLY_STOP_PATIENCE = 3
TURN_GAP_S = 120.0

DEFAULTS = {"train": 20_000, "dev": 3_000, "heldout": 3_000, "wrong": 1_000}
SMOKE = {"train": 600, "dev": 200, "heldout": 200, "wrong": 100}


# --------------------------------------------------------------------------- #
# vocabulary
# --------------------------------------------------------------------------- #
class CharTable:
    """Character ids with a closed alphabet (specials first, so ids are stable)."""

    def __init__(self, alphabet: str = ALPHABET) -> None:
        self.itos: List[str] = list(SPECIALS) + list(dict.fromkeys(alphabet))
        self.stoi: Dict[str, int] = {ch: i for i, ch in enumerate(self.itos)}

    @property
    def pad_id(self) -> int:
        return self.stoi["<pad>"]

    @property
    def bos_id(self) -> int:
        return self.stoi["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.stoi["<eos>"]

    @property
    def unk_id(self) -> int:
        return self.stoi["<unk>"]

    def __len__(self) -> int:
        return len(self.itos)

    def encode(self, text: str) -> List[int]:
        unk = self.unk_id
        return [self.stoi.get(ch, unk) for ch in text]

    def decode(self, ids: Sequence[int]) -> str:
        out: List[str] = []
        for index in ids:
            if index < 0 or index >= len(self.itos):
                continue
            token = self.itos[index]
            if token in SPECIALS:
                if token == "<eos>":
                    break
                continue
            out.append(token)
        return "".join(out)

    def to_dict(self) -> Dict[str, Any]:
        return {"alphabet": "".join(self.itos[len(SPECIALS) :]), "specials": list(SPECIALS)}


# --------------------------------------------------------------------------- #
# task
# --------------------------------------------------------------------------- #
def _word(rng: random.Random, syllables: int) -> str:
    return "".join(rng.choice(CONSONANTS) + rng.choice(VOWELS) for _ in range(syllables))


def _distinct_words(
    rng: random.Random, count: int, syllables: int, exclude: Optional[set] = None
) -> List[str]:
    banned = set(exclude or ())
    out: List[str] = []
    seen: set = set()
    # 14 onsets x 5 vowels = 70 syllables per slot; 70**2 = 4,900 names and
    # 70**3 = 343,000 values, so the loop terminates long before any ceiling.
    while len(out) < count:
        word = _word(rng, syllables)
        if word in seen or word in banned:
            continue
        seen.add(word)
        out.append(word)
    return out


def build_splits(
    seed: int = SEED,
    sizes: Optional[Dict[str, int]] = None,
    n_train_names: int = 500,
    n_heldout_names: int = 500,
) -> Dict[str, List[Dict[str, str]]]:
    """Deterministic episodes; every split is disjoint in *values*.

    An episode is ``{teach_name, query_name, value}``. For everything except
    ``wrong_name`` the two names are the same; keeping both fields makes the
    control a data change rather than a second code path.
    """
    sizes = dict(DEFAULTS if sizes is None else sizes)
    rng = random.Random(seed)

    train_names = _distinct_words(rng, n_train_names, NAME_SYLLABLES)
    heldout_names = _distinct_words(rng, n_heldout_names, NAME_SYLLABLES, exclude=set(train_names))
    total_values = sizes["train"] + sizes["dev"] + sizes["heldout"] + sizes["wrong"]
    values = _distinct_words(rng, total_values, VALUE_SYLLABLES, exclude=set(train_names))

    cursor = 0

    def take(count: int) -> List[str]:
        nonlocal cursor
        chunk = values[cursor : cursor + count]
        cursor += count
        return chunk

    def episodes(names: Sequence[str], count: int) -> List[Dict[str, str]]:
        picked = take(count)
        return [
            {"teach_name": names[i % len(names)], "query_name": names[i % len(names)], "value": v}
            for i, v in enumerate(picked)
        ]

    train = episodes(train_names, sizes["train"])
    dev = episodes(train_names, sizes["dev"])
    heldout = episodes(heldout_names, sizes["heldout"])

    wrong_values = take(sizes["wrong"])
    wrong = [
        {
            "teach_name": train_names[i % len(train_names)],
            "query_name": heldout_names[i % len(heldout_names)],
            "value": value,
        }
        for i, value in enumerate(wrong_values)
    ]

    return {
        "train": train,
        "dev": dev,
        "heldout_names": heldout,
        # Cold is the *same questions* as heldout with the teaching turn
        # skipped; a separate sample would let a different draw explain a gap.
        "cold": [dict(episode) for episode in heldout],
        "wrong_name": wrong,
    }


def leak_check(splits: Dict[str, List[Dict[str, str]]]) -> Dict[str, Any]:
    """Mechanical: no value is reused across splits, no held-out name is trained."""

    def values(name: str) -> set:
        return {episode["value"] for episode in splits[name]}

    def names(name: str) -> set:
        return {episode["teach_name"] for episode in splits[name]}

    train_values = values("train")
    overlaps = {
        "dev": len(train_values & values("dev")),
        "heldout_names": len(train_values & values("heldout_names")),
        "wrong_name": len(train_values & values("wrong_name")),
    }
    dev_heldout = len(values("dev") & values("heldout_names"))
    name_overlap = len(names("train") & names("heldout_names"))
    duplicated_in_train = len(splits["train"]) - len(train_values)
    # A character outside the alphabet would become <unk>, which makes the word
    # unrepresentable no matter how good the model is — a silent impossibility
    # rather than a hard task.
    alphabet = set(ALPHABET)
    chars_outside = sum(
        1
        for rows in splits.values()
        for episode in rows
        for ch in episode["teach_name"] + episode["query_name"] + episode["value"]
        if ch not in alphabet
    )
    return {
        "value_overlap_with_train": overlaps,
        "dev_heldout_value_overlap": dev_heldout,
        "train_heldout_name_overlap": name_overlap,
        "duplicate_values_inside_train": duplicated_in_train,
        "chars_outside_alphabet": chars_outside,
        "clean": (
            not any(overlaps.values())
            and dev_heldout == 0
            and name_overlap == 0
            and duplicated_in_train == 0
            and chars_outside == 0
        ),
    }


def teach_text(episode: Dict[str, str]) -> str:
    return f"remember {episode['teach_name']} = {episode['value']} ."


def query_text(episode: Dict[str, str]) -> str:
    return f"{episode['query_name']} ?"


def answer_text(episode: Dict[str, str]) -> str:
    return f"{episode['value']} ."


def encode_episode(table: CharTable, episode: Dict[str, str]) -> Dict[str, List[int]]:
    return {
        "teach": [table.bos_id] + table.encode(teach_text(episode)),
        "query": table.encode(query_text(episode)),
        "answer": table.encode(answer_text(episode)) + [table.eos_id],
    }


def digest(episodes: Sequence[Dict[str, str]]) -> str:
    payload = "\n".join(
        f"{ep['teach_name']},{ep['query_name']},{ep['value']}" for ep in episodes
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


# --------------------------------------------------------------------------- #
# training / evaluation
# --------------------------------------------------------------------------- #
def _device() -> str:
    from core.system.config.compute_device import resolve_torch_device

    return resolve_torch_device("auto")


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


def build_core(table: CharTable, device: str):
    from ai.core.stateful_decoder import GRUCore

    return GRUCore(
        len(table),
        hidden=HIDDEN,
        emb=EMB,
        chunk_seconds=CHUNK_SECONDS,
        seed=SEED,
        device=device,
    )


def _batches(items: Sequence[Any], size: int) -> List[Sequence[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _tensor(rows: Sequence[Sequence[int]], device: str):
    import torch

    return torch.tensor([list(row) for row in rows], dtype=torch.long, device=device)


def evaluate(
    core: Any,
    table: CharTable,
    episodes: Sequence[Dict[str, str]],
    *,
    device: str,
    teach: bool = True,
    zero_state: bool = False,
    turn_gap_s: float = TURN_GAP_S,
    batch_size: int = BATCH,
) -> Dict[str, Any]:
    """Greedy generation from the state; returns exact match and char accuracy."""
    import torch

    torch_mod = torch
    exact = 0
    chars_right = 0
    chars_total = 0
    decoded_sample: List[str] = []
    max_new = len(answer_text(episodes[0]))  # "value ." is fixed length

    encoded = [encode_episode(table, episode) for episode in episodes]
    was_training = core.modules()[0].training
    core.eval()
    try:
        with torch_mod.no_grad():
            for start in range(0, len(encoded), batch_size):
                rows = encoded[start : start + batch_size]
                truth = episodes[start : start + batch_size]
                batch = len(rows)
                state = core.init_state(batch)
                if teach:
                    core.ai_step(_tensor([row["teach"] for row in rows], device), state)
                if turn_gap_s > 0:
                    core.al_step(turn_gap_s, state)
                if zero_state:
                    # Same object, same weights, same prompt: only ``h`` differs.
                    state.tensors["h"] = torch_mod.zeros_like(state.tensors["h"])
                logits, state = core.ai_step(_tensor([row["query"] for row in rows], device), state)
                generated: List[List[int]] = [[] for _ in range(batch)]
                for _ in range(max_new):
                    tokens = logits[:, -1, :].argmax(dim=-1)
                    for position in range(batch):
                        generated[position].append(int(tokens[position]))
                    logits, state = core.ai_step(tokens.unsqueeze(1), state)
                for position, episode in enumerate(truth):
                    text = table.decode(generated[position])
                    head = text.split(".")[0].strip()
                    if head == episode["value"]:
                        exact += 1
                    chars_total += len(episode["value"])
                    chars_right += sum(
                        1
                        for a, b in zip(head.ljust(len(episode["value"])), episode["value"])
                        if a == b
                    )
                    if len(decoded_sample) < 5:
                        decoded_sample.append(f"{query_text(episode)} -> {text!r}")
    finally:
        if was_training:
            core.train()

    total = len(episodes)
    return {
        "n": total,
        "exact": round(exact / total, 4) if total else 0.0,
        "char_accuracy": round(chars_right / chars_total, 4) if chars_total else 0.0,
        "samples": decoded_sample,
    }


def teacher_forced_accuracy(
    core: Any,
    table: CharTable,
    episodes: Sequence[Dict[str, str]],
    *,
    device: str,
    batch_size: int = BATCH,
) -> Dict[str, Any]:
    """Accuracy when the gold prefix is fed back, i.e. no generation drift.

    This is a *diagnostic*, not a gate. Exact match can be 0 for two very
    different reasons: the state never held the value, or it held it and
    free-running generation wandered off. Teacher forcing separates them — if
    the next character is right given the true prefix, the information is in
    the state; if it is chance even then, it is not.
    """
    import torch

    encoded = [encode_episode(table, episode) for episode in episodes]
    query_len = len(encoded[0]["query"])
    right = 0
    total = 0
    full = 0
    core.eval()
    with torch.no_grad():
        for start in range(0, len(encoded), batch_size):
            rows = encoded[start : start + batch_size]
            state = core.init_state(len(rows))
            core.ai_step(_tensor([row["teach"] for row in rows], device), state)
            core.al_step(TURN_GAP_S, state)
            sequence = [row["query"] + row["answer"] for row in rows]
            logits, _ = core.ai_step(_tensor([seq[:-1] for seq in sequence], device), state)
            predicted = logits[:, query_len - 1 :, :].argmax(dim=-1)
            gold = _tensor([row["answer"] for row in rows], device)
            match = predicted == gold
            right += int(match.sum())
            total += int(match.numel())
            full += int(match.all(dim=1).sum())
    return {
        "n": len(episodes),
        "char_accuracy": round(right / total, 4) if total else 0.0,
        "full_exact": round(full / max(1, len(episodes)), 4),
    }


def state_probe(
    core: Any,
    table: CharTable,
    episodes: Sequence[Dict[str, str]],
    *,
    device: str,
    batch_size: int = BATCH,
    steps: int = 400,
) -> Dict[str, Any]:
    """Can a linear readout recover the value from ``h`` alone?

    Diagnostic, not a gate. If the probe can name the value but the model
    cannot generate it, the state *holds* the content and the language head is
    the bottleneck; if the probe is at chance, the content never reached ``h``
    and no head could have read it. The probe is trained on half the split and
    scored on the other half.
    """
    import torch

    encoded = [encode_episode(table, episode) for episode in episodes]
    hidden_states: List[Any] = []
    targets: List[List[int]] = []
    core.eval()
    with torch.no_grad():
        for start in range(0, len(encoded), batch_size):
            rows = encoded[start : start + batch_size]
            state = core.init_state(len(rows))
            core.ai_step(_tensor([row["teach"] for row in rows], device), state)
            core.al_step(TURN_GAP_S, state)
            _, state = core.ai_step(_tensor([row["query"] for row in rows], device), state)
            hidden_states.append(state.tensors["h"].detach())
            for episode in episodes[start : start + batch_size]:
                targets.append([table.stoi.get(ch, table.unk_id) for ch in episode["value"]])

    features = torch.cat(hidden_states, dim=0)
    gold = torch.tensor(targets, dtype=torch.long, device=device)
    width = gold.shape[1]
    half = len(features) // 2
    probe = torch.nn.Linear(features.shape[1], width * len(table)).to(device)
    optimiser = torch.optim.Adam(probe.parameters(), lr=1e-2)
    for _ in range(steps):
        logits = probe(features[:half]).reshape(half, width, len(table))
        loss = torch.nn.functional.cross_entropy(
            logits.reshape(-1, len(table)), gold[:half].reshape(-1)
        )
        optimiser.zero_grad(set_to_none=True)
        loss.backward()
        optimiser.step()

    with torch.no_grad():
        logits = probe(features[half:]).reshape(len(features) - half, width, len(table))
        predicted = logits.argmax(dim=-1)
        match = predicted == gold[half:]
    return {
        "n": int(gold.shape[0]),
        "char_accuracy": round(float(match.float().mean()), 4),
        "full_exact": round(float(match.all(dim=1).float().mean()), 4),
    }


def train(
    core: Any,
    table: CharTable,
    train_episodes: Sequence[Dict[str, str]],
    dev_episodes: Sequence[Dict[str, str]],
    *,
    device: str,
    epochs: int,
    batch_size: int,
    lr: float,
    patience: int,
    seed: int = SEED,
) -> Dict[str, Any]:
    import torch

    encoded = [encode_episode(table, episode) for episode in train_episodes]
    query_len = len(encoded[0]["query"])
    optimiser = torch.optim.Adam(list(core.parameters()), lr=lr)
    best_exact = -1.0
    best_state: Optional[Dict[str, Any]] = None
    best_epoch = 0
    stale = 0
    history: List[Dict[str, Any]] = []
    started = time.time()

    core.train()
    for epoch in range(1, epochs + 1):
        order = list(range(len(encoded)))
        random.Random(seed + epoch).shuffle(order)
        running = 0.0
        seen = 0
        for chunk in _batches(order, batch_size):
            rows = [encoded[i] for i in chunk]
            state = core.init_state(len(rows))
            core.ai_step(_tensor([row["teach"] for row in rows], device), state)
            core.al_step(TURN_GAP_S, state)
            sequence = [row["query"] + row["answer"] for row in rows]
            inputs = _tensor([seq[:-1] for seq in sequence], device)
            targets = _tensor([seq[1:] for seq in sequence], device)
            logits, _ = core.ai_step(inputs, state)
            scored = logits[:, query_len - 1 :, :].reshape(-1, len(table))
            loss = torch.nn.functional.cross_entropy(
                scored, targets[:, query_len - 1 :].reshape(-1)
            )
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(list(core.parameters()), 1.0)
            optimiser.step()
            core.invalidate_hash()
            running += float(loss.detach().cpu())
            seen += 1

        dev = evaluate(core, table, dev_episodes, device=device)
        history.append(
            {
                "epoch": epoch,
                "loss": round(running / max(1, seen), 4),
                "dev_exact": dev["exact"],
                "dev_char": dev["char_accuracy"],
            }
        )
        if dev["exact"] > best_exact + 1e-9:
            best_exact = dev["exact"]
            best_epoch = epoch
            best_state = copy.deepcopy(core.state_dict())
            stale = 0
        else:
            stale += 1
            # ``patience=0`` means "no early stopping": exact match is a step
            # function that sits at 0 until the model is nearly right, so a
            # rule keyed on it fires while the loss is still falling (measured
            # in §43: it stopped at epoch 9 of 24 with loss 0.845 and falling).
            if patience and stale >= patience:
                break

    if best_state is not None:
        core.load_state_dict(best_state)
    return {
        "epochs_run": len(history),
        "best_epoch": best_epoch,
        "best_dev_exact": round(best_exact, 4),
        "seconds": round(time.time() - started, 2),
        "history": history,
    }


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def run(args: argparse.Namespace, stamp: str) -> Dict[str, Any]:
    import torch  # noqa: F401  (fail early with a clear message)

    device = _device()
    table = CharTable()
    sizes = dict(SMOKE if args.smoke else DEFAULTS)
    # The *effective* budget, not the module default: a report that says
    # "max_epochs: 24" after a 60-epoch run is a record of the wrong run.
    epochs_budget = 2 if args.smoke else args.epochs
    splits = build_splits(seed=args.seed, sizes=sizes)
    leaks = leak_check(splits)

    report: Dict[str, Any] = {
        "task_version": TASK_VERSION,
        "git_head": _git_head(),
        "device": device,
        "config": {
            "hidden": HIDDEN,
            "emb": EMB,
            "chunk_seconds": CHUNK_SECONDS,
            "lr": LEARNING_RATE,
            "batch": BATCH,
            "max_epochs": epochs_budget,
            "early_stop_patience": args.patience,
            "turn_gap_s": TURN_GAP_S,
            "seed": args.seed,
            "name_syllables": NAME_SYLLABLES,
            "value_syllables": VALUE_SYLLABLES,
            "token_count": len(table),
            "alphabet": table.to_dict()["alphabet"],
        },
        "sizes": {name: len(rows) for name, rows in splits.items()},
        "digests": {name: digest(rows) for name, rows in splits.items()},
        "leak_check": leaks,
    }
    if not leaks["clean"]:
        # A dirty split makes every number below meaningless; stop before
        # training rather than report a table-contaminated result.
        report["all_pass"] = False
        report["aborted"] = "leak check failed"
        return report

    core = build_core(table, device)
    report["params"] = core.parameter_count()
    report["weights_hash"] = core.weights_hash()

    report["training"] = train(
        core,
        table,
        splits["train"],
        splits["dev"],
        device=device,
        epochs=epochs_budget,
        batch_size=BATCH,
        lr=LEARNING_RATE,
        patience=args.patience,
        seed=args.seed,
    )

    forward_started = time.time()
    results = {
        "dev": evaluate(core, table, splits["dev"], device=device),
        "heldout_names": evaluate(core, table, splits["heldout_names"], device=device),
        "heldout_names_no_al": evaluate(
            core, table, splits["heldout_names"], device=device, turn_gap_s=0.0
        ),
        "zero_state": evaluate(
            core, table, splits["heldout_names"], device=device, zero_state=True
        ),
        "cold": evaluate(core, table, splits["cold"], device=device, teach=False),
        "wrong_name": evaluate(core, table, splits["wrong_name"], device=device),
    }
    elapsed = time.time() - forward_started
    # Diagnostics (not gates): where in the chain the value is lost.
    report["diagnostics"] = {
        "teacher_forced_dev": teacher_forced_accuracy(core, table, splits["dev"], device=device),
        "teacher_forced_heldout": teacher_forced_accuracy(
            core, table, splits["heldout_names"], device=device
        ),
        "probe_dev": state_probe(core, table, splits["dev"], device=device),
        "probe_heldout": state_probe(core, table, splits["heldout_names"], device=device),
    }
    episodes_scored = sum(entry["n"] for entry in results.values())
    report["results"] = results
    report["cost"] = {
        "params": report["params"],
        "train_seconds": report["training"]["seconds"],
        "eval_seconds": round(elapsed, 2),
        "episodes_scored": episodes_scored,
        "seconds_per_episode": round(elapsed / max(1, episodes_scored), 5),
        "device": device,
    }

    dev = results["dev"]["exact"]
    held = results["heldout_names"]["exact"]
    zero = results["zero_state"]["exact"]
    cold = results["cold"]["exact"]
    checks = {
        "G1_dev_exact_ge_0.60": dev >= 0.60,
        "G2_heldout_exact_ge_0.30": held >= 0.30,
        "G3_zero_state_le_0.05_and_gap_ge_0.25": (zero <= 0.05) and (held - zero) >= 0.25,
        "G4_cold_exact_le_0.02": cold <= 0.02,
        "G5_cost_recorded": all(
            report["cost"][key] not in (None, 0)
            for key in ("params", "train_seconds", "seconds_per_episode")
        ),
    }
    report["checks"] = checks
    report["all_pass"] = all(checks.values())
    report["wrong_name_rate"] = results["wrong_name"]["exact"]

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = out_dir / f"state_content_{stamp}.pt"
    import torch as torch_module

    torch_module.save(
        {
            "task_version": TASK_VERSION,
            "config": core.config(),
            "state_dict": core.state_dict(),
            "vocab": table.to_dict(),
        },
        str(checkpoint),
    )
    report["checkpoint"] = str(checkpoint)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Round 5: does the state carry content?")
    parser.add_argument("--out", default="data/state_content")
    parser.add_argument("--smoke", action="store_true", help="tiny data, 2 epochs")
    parser.add_argument("--epochs", type=int, default=MAX_EPOCHS)
    parser.add_argument(
        "--patience", type=int, default=EARLY_STOP_PATIENCE, help="0 disables early stopping"
    )
    parser.add_argument("--seed", type=int, default=SEED, help="data split seed")
    parser.add_argument("--require-pass", action="store_true", help="exit 1 unless all gates pass")
    args = parser.parse_args(argv)

    started = time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    report = run(args, stamp)
    report["wall_seconds"] = round(time.time() - started, 2)

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"state_content_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\ntask            : {report['task_version']}  device={report['device']}")
    print(f"params          : {report.get('params')}")
    print(f"leak check      : {report['leak_check']}")
    print(
        f"training        : {report['training']['epochs_run']} epochs, "
        f"{report['training']['seconds']}s, best dev {report['training']['best_dev_exact']}"
    )
    print("\n            split            n     exact   char")
    for name in ("dev", "heldout_names", "heldout_names_no_al", "zero_state", "cold", "wrong_name"):
        entry = report["results"][name]
        print(f"  {name:22s} {entry['n']:5d}  {entry['exact']:7.3f}  {entry['char_accuracy']:6.3f}")
    print("\n  diagnostics      char   full")
    for name, entry in report["diagnostics"].items():
        print(f"  {name:22s} {entry['char_accuracy']:6.3f} {entry['full_exact']:6.3f}")
    print("\n  checks")
    for name, passed in report["checks"].items():
        print(f"    {'PASS' if passed else 'FAIL'}  {name}")
    print(f"\nall_pass        : {report['all_pass']}")
    print(f"report          : {path}")
    print(f"checkpoint      : {report.get('checkpoint')}")
    if report["all_pass"]:
        print("\nstate carries content, generation reads it, and removing the state collapses it")
    else:
        print("\nsome bar was missed - see CORE_GAP_ANALYSIS.md §43.6 for what that means")
    return 0 if (report["all_pass"] or not args.require_pass) else 1


if __name__ == "__main__":
    raise SystemExit(main())
