#!/usr/bin/env python3
# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
# LAYER: learning
"""Round 6: one value is not a memory. Can the state hold two *bindings*?

``CORE_GAP_ANALYSIS.md`` §44 measured a single-slot carrier: teach one pair, ask
it back, and removing ``h`` removes the answer. The limitation it recorded was
that the name never mattered (``wrong_name`` 0.994) - the model returned "the
most recent value", which is a buffer, not a memory.

This round asks the next question and holds the arm fixed. Two teaching **turns**
(each one ``ai_step``, an ``al_step(120 s)`` between them, exactly the production
shape), then one query naming either of the two taught keys, and the answer is
that key's value. A single-slot carrier can score at most 0.5 here, and it scores
it by always returning the same one; ``other_value_rate`` names that failure
directly instead of hiding it inside an aggregate.

The only variable is the **training objective**:

* ``single`` - the §44 shape: one query per episode, loss on that answer only.
* ``both``   - both queries from the same teaching turns, both losses, so the
  objective cannot be satisfied by carrying one value and hedging. Evaluation is
  identical for both arms and always asks **one** key from a fresh state, so a
  model that learned a positional trick in training is caught by ``by_ask``.

Diagnostics, because "0.00" cannot tell "stored nothing" from "stored both and
cannot select": a linear readout of ``h`` alone is trained for the first-taught
value, the second-taught value, and the asked value. If the first two are
readable, storage works and selection is the bottleneck; if only one is, the
write path is overwriting.

Usage::

    ./.venv/bin/python scripts/train_state_binding.py --objective both \\
        --seed 20261115 --epochs 100 --out data/state_binding
    ./.venv/bin/python scripts/train_state_binding.py --smoke --objective both
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

TASK_VERSION = "state-binding-v1"
SEED = 20261115

CONSONANTS = "bdfgklmnprstvz"
VOWELS = "aeiou"
ALPHABET = CONSONANTS + VOWELS + "0123456789" + " .?="
SPECIALS = ("<pad>", "<bos>", "<eos>", "<unk>")

NAME_SYLLABLES = 2
VALUE_SYLLABLES = 3
PAIRS_PER_EPISODE = 2
# "value ." - the answer shape is fixed, so generation length is not ground-truth
# dependent (the ``wrong_name`` control has no ground truth to read it from).
ANSWER_CHARS = VALUE_SYLLABLES * 2 + 2

# Fixed before the run (§45.4). A different value is a new round.
HIDDEN = 128
EMB = 64
CHUNK_SECONDS = 60.0
LEARNING_RATE = 3e-3
BATCH = 128
MAX_EPOCHS = 100
EARLY_STOP_PATIENCE = 0
TURN_GAP_S = 120.0

DEFAULTS = {"train": 20_000, "dev": 3_000, "heldout": 3_000, "wrong": 1_000}
SMOKE = {"train": 600, "dev": 200, "heldout": 200, "wrong": 100}


class CharTable:
    """Character ids over a closed alphabet (specials first, so ids are stable)."""

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
    n_names: int = 900,
    n_heldout_names: int = 600,
) -> Dict[str, List[Dict[str, Any]]]:
    """Deterministic episodes of two bindings each.

    An episode is ``{"taught": [[name, value], [name, value]], "ask": 0|1}``;
    ``ask`` indexes the pair the query names. ``wrong_name`` teaches two pairs
    and asks a third, never-taught name, so the control shares the data shape.
    """
    sizes = dict(DEFAULTS if sizes is None else sizes)
    rng = random.Random(seed)

    names = _distinct_words(rng, n_names, NAME_SYLLABLES)
    heldout_names = _distinct_words(rng, n_heldout_names, NAME_SYLLABLES, exclude=set(names))
    episodes = sizes["train"] + sizes["dev"] + sizes["heldout"] + sizes["wrong"]
    values = _distinct_words(rng, episodes * PAIRS_PER_EPISODE, VALUE_SYLLABLES, exclude=set(names))
    cursor = 0

    def pairs(pool: Sequence[str], count: int) -> List[List[List[str]]]:
        nonlocal cursor
        out: List[List[List[str]]] = []
        for _ in range(count):
            picked = rng.sample(pool, PAIRS_PER_EPISODE)
            vals = values[cursor : cursor + PAIRS_PER_EPISODE]
            cursor += PAIRS_PER_EPISODE
            out.append([[n, v] for n, v in zip(picked, vals)])
        return out

    def episodes_from(pool: Sequence[str], count: int) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for taught in pairs(pool, count):
            out.append({"taught": taught, "ask": rng.randrange(PAIRS_PER_EPISODE)})
        return out

    train = episodes_from(names, sizes["train"])
    dev = episodes_from(names, sizes["dev"])
    heldout = episodes_from(heldout_names, sizes["heldout"])

    wrong: List[Dict[str, Any]] = []
    for taught in pairs(names, sizes["wrong"]):
        # The asked name is never one of the taught ones, so any correct-looking
        # value must have come from the state rather than from the query.
        closer = heldout_names[len(wrong) % len(heldout_names)]
        # No ground truth exists: the question names a third key that was never
        # taught, so the only thing to measure is whether a *taught* value comes
        # out anyway (which is what a single-slot carrier would do).
        wrong.append({"taught": taught, "ask": None, "query_name": closer})

    return {
        "train": train,
        "dev": dev,
        "heldout_names": heldout,
        # Cold is the *same questions* with the teaching turns skipped.
        "cold": [dict(episode) for episode in heldout],
        "wrong_name": wrong,
    }


def leak_check(splits: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Mechanical: no value reused across splits, no held-out name is trained."""

    def taught_values(rows: Sequence[Dict[str, Any]]) -> set:
        return {value for episode in rows for _, value in episode["taught"]}

    def taught_names(rows: Sequence[Dict[str, Any]]) -> set:
        return {name for episode in rows for name, _ in episode["taught"]}

    train_values = taught_values(splits["train"])
    overlaps = {
        "dev": len(train_values & taught_values(splits["dev"])),
        "heldout_names": len(train_values & taught_values(splits["heldout_names"])),
        "wrong_name": len(train_values & taught_values(splits["wrong_name"])),
    }
    dev_heldout = len(taught_values(splits["dev"]) & taught_values(splits["heldout_names"]))
    name_overlap = len(taught_names(splits["train"]) & taught_names(splits["heldout_names"]))
    duplicated = len(splits["train"]) * PAIRS_PER_EPISODE - len(train_values)
    alphabet = set(ALPHABET)
    chars_outside = sum(
        1
        for rows in splits.values()
        for episode in rows
        for pair in episode["taught"]
        for ch in pair[0] + pair[1]
        if ch not in alphabet
    )
    asked_untrained = sum(
        1
        for episode in splits["wrong_name"]
        if episode.get("query_name") in {name for name, _ in episode["taught"]}
    )
    # The asked key must be one of the two taught keys, otherwise "selection"
    # is not what the gates measure. ``wrong_name`` has no asked key by design.
    bad_ask = sum(
        1
        for name in ("train", "dev", "heldout_names")
        for episode in splits[name]
        if episode["ask"] not in range(len(episode["taught"]))
    )
    return {
        "value_overlap_with_train": overlaps,
        "dev_heldout_value_overlap": dev_heldout,
        "train_heldout_name_overlap": name_overlap,
        "duplicate_values_inside_train": duplicated,
        "chars_outside_alphabet": chars_outside,
        "wrong_name_queries_a_taught_key": asked_untrained,
        "ask_index_out_of_range": bad_ask,
        "clean": (
            not any(overlaps.values())
            and dev_heldout == 0
            and name_overlap == 0
            and duplicated == 0
            and chars_outside == 0
            and asked_untrained == 0
            and bad_ask == 0
        ),
    }


def teach_text(pair: Sequence[str]) -> str:
    return f"remember {pair[0]} = {pair[1]} ."


def query_text(episode: Dict[str, Any], index: Optional[int] = None) -> str:
    if "query_name" in episode and index is None:
        return f"{episode['query_name']} ?"
    chosen = episode["ask"] if index is None else index
    return f"{episode['taught'][chosen][0]} ?"


def answer_text(episode: Dict[str, Any], index: Optional[int] = None) -> str:
    chosen = episode["ask"] if index is None else index
    if chosen is None:
        raise ValueError("episode has no ground-truth answer (wrong_name control)")
    return f"{episode['taught'][chosen][1]} ."


def encode_episode(table: CharTable, episode: Dict[str, Any]) -> Dict[str, Any]:
    encoded: Dict[str, Any] = {
        "teach": [[table.bos_id] + table.encode(teach_text(pair)) for pair in episode["taught"]],
        "query": table.encode(query_text(episode)),
    }
    if episode["ask"] is not None:
        encoded["answer"] = table.encode(answer_text(episode)) + [table.eos_id]
        # The two-question objective asks each taught key from the same state.
        encoded["both"] = [
            {
                "query": table.encode(query_text(episode, index)),
                "answer": table.encode(answer_text(episode, index)) + [table.eos_id],
            }
            for index in range(len(episode["taught"]))
        ]
    return encoded


def digest(episodes: Sequence[Dict[str, Any]]) -> str:
    payload = "\n".join(
        ",".join(f"{name}:{value}" for name, value in episode["taught"])
        + f"|{episode['ask']}"
        + (f"|{episode['query_name']}" if "query_name" in episode else "")
        for episode in episodes
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


def build_core(table: CharTable, device: str, hidden: int = HIDDEN, emb: int = EMB):
    from ai.core.stateful_decoder import GRUCore

    return GRUCore(
        len(table),
        hidden=hidden,
        emb=emb,
        chunk_seconds=CHUNK_SECONDS,
        seed=SEED,
        device=device,
    )


def _batches(items: Sequence[Any], size: int) -> List[Sequence[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _tensor(rows: Sequence[Sequence[int]], device: str):
    import torch

    return torch.tensor([list(row) for row in rows], dtype=torch.long, device=device)


def _teach(core: Any, rows: Sequence[Dict[str, Any]], state: Any, device: str) -> Any:
    """Two teaching turns, an al_step between them (the production shape)."""
    for index in range(PAIRS_PER_EPISODE):
        core.ai_step(_tensor([row["teach"][index] for row in rows], device), state)
        core.al_step(TURN_GAP_S, state)
    return state


def evaluate(
    core: Any,
    table: CharTable,
    episodes: Sequence[Dict[str, Any]],
    *,
    device: str,
    teach: bool = True,
    zero_state: bool = False,
    batch_size: int = BATCH,
) -> Dict[str, Any]:
    """Ask one key from a fresh state; report exact, per-position and hedging.

    ``wrong_name`` has no ground truth, so it reports ``taught_value_rate``: how
    often *some* taught value comes out even though a third key was asked.
    """
    import torch

    encoded = [encode_episode(table, episode) for episode in episodes]
    exact = other = taught_out = scored_n = 0
    per = [0, 0]
    per_n = [0, 0]
    samples: List[str] = []
    max_new = ANSWER_CHARS
    was_training = core.modules()[0].training
    core.eval()
    try:
        with torch.no_grad():
            for start in range(0, len(encoded), batch_size):
                rows = encoded[start : start + batch_size]
                truth = episodes[start : start + batch_size]
                batch = len(rows)
                state = core.init_state(batch)
                if teach:
                    _teach(core, rows, state, device)
                if zero_state:
                    # Same object, same weights, same prompt: only ``h`` differs.
                    state.tensors["h"] = torch.zeros_like(state.tensors["h"])
                logits, state = core.ai_step(_tensor([row["query"] for row in rows], device), state)
                generated: List[List[int]] = [[] for _ in range(batch)]
                for _ in range(max_new):
                    tokens = logits[:, -1, :].argmax(dim=-1)
                    for position in range(batch):
                        generated[position].append(int(tokens[position]))
                    logits, state = core.ai_step(tokens.unsqueeze(1), state)
                for position, episode in enumerate(truth):
                    head = table.decode(generated[position]).split(".")[0].strip()
                    taught = {value for _, value in episode["taught"]}
                    index = episode["ask"]
                    if index is None:
                        # Control: was a taught value emitted for an untaught key?
                        if head in taught:
                            taught_out += 1
                    else:
                        want = episode["taught"][index][1]
                        scored_n += 1
                        if head == want:
                            exact += 1
                        elif head in taught:
                            other += 1
                        if index < len(per):
                            per_n[index] += 1
                            if head == want:
                                per[index] += 1
                    if len(samples) < 5:
                        samples.append(f"{query_text(episode)} -> {head!r}")
    finally:
        if was_training:
            core.train()

    total = len(episodes)
    return {
        "n": total,
        "scored": scored_n,
        "exact": round(exact / scored_n, 4) if scored_n else None,
        "other_value_rate": round(other / scored_n, 4) if scored_n else None,
        "taught_value_rate": round(taught_out / total, 4) if total and not scored_n else None,
        "by_ask": [round(per[i] / per_n[i], 4) if per_n[i] else None for i in range(len(per))],
        "samples": samples,
    }


def evaluate_both(
    core: Any, table: CharTable, episodes: Sequence[Dict[str, Any]], *, device: str
) -> Dict[str, Any]:
    """Diagnostic: ask both keys from one state, in teaching order.

    This is the training shape of the ``both`` objective. It is *not* the
    capability being claimed - that is the single query above - but a gap between
    them would say the objective taught a sequence, not a binding.
    """
    import torch

    encoded = [encode_episode(table, episode) for episode in episodes]
    max_new = ANSWER_CHARS
    text: List[List[str]] = [[], []]
    was_training = core.modules()[0].training
    core.eval()
    try:
        with torch.no_grad():
            for start in range(0, len(encoded), BATCH):
                rows = encoded[start : start + BATCH]
                batch = len(rows)
                state = core.init_state(batch)
                _teach(core, rows, state, device)
                for index in range(PAIRS_PER_EPISODE):
                    logits, state = core.ai_step(
                        _tensor([row["both"][index]["query"] for row in rows], device), state
                    )
                    generated: List[List[int]] = [[] for _ in range(batch)]
                    for _ in range(max_new):
                        tokens = logits[:, -1, :].argmax(dim=-1)
                        for position in range(batch):
                            generated[position].append(int(tokens[position]))
                        logits, state = core.ai_step(tokens.unsqueeze(1), state)
                    for position in range(batch):
                        text[index].append(table.decode(generated[position]).split(".")[0].strip())
    finally:
        if was_training:
            core.train()
    out = {}
    for index in range(PAIRS_PER_EPISODE):
        hits = sum(
            1 for episode, got in zip(episodes, text[index]) if got == episode["taught"][index][1]
        )
        out[f"key{index}"] = round(hits / len(episodes), 4)
    out["both_exact"] = round(
        sum(
            1
            for i in range(len(episodes))
            if all(text[j][i] == episodes[i]["taught"][j][1] for j in range(PAIRS_PER_EPISODE))
        )
        / len(episodes),
        4,
    )
    return out


def answer_loss(
    core: Any,
    table: CharTable,
    episodes: Sequence[Dict[str, Any]],
    *,
    device: str,
    batch_size: int = BATCH,
) -> float:
    """Teacher-forced cross-entropy on the answer tokens of the asked key.

    This is the *selection* signal, not a score. ``exact`` is a step function: it
    stays at 0 until the model is nearly right, so a rule keyed on it freezes the
    epochs before the jump (§43 stopped at epoch 9/24 for exactly that reason, and
    with ``patience=0`` the same rule would silently keep epoch 1's weights when
    every epoch ties at 0). Loss is continuous, so it can say "this epoch is
    better" while exact still reads 0.
    """
    import torch

    encoded = [encode_episode(table, episode) for episode in episodes]
    was_training = core.modules()[0].training
    core.eval()
    total = 0.0
    tokens = 0
    try:
        with torch.no_grad():
            for start in range(0, len(encoded), batch_size):
                rows = encoded[start : start + batch_size]
                ask_len = len(rows[0]["query"])
                state = core.init_state(len(rows))
                _teach(core, rows, state, device)
                seq = [row["query"] + row["answer"] for row in rows]
                inputs = _tensor([s[:-1] for s in seq], device)
                targets = _tensor([s[1:] for s in seq], device)
                logits, _ = core.ai_step(inputs, state)
                scored = logits[:, ask_len - 1 :, :].reshape(-1, len(table))
                flat = targets[:, ask_len - 1 :].reshape(-1)
                total += float(torch.nn.functional.cross_entropy(scored, flat, reduction="sum"))
                tokens += int(flat.numel())
    finally:
        if was_training:
            core.train()
    return total / max(1, tokens)


def train(
    core: Any,
    table: CharTable,
    train_episodes: Sequence[Dict[str, Any]],
    dev_episodes: Sequence[Dict[str, Any]],
    *,
    objective: str,
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
    best_loss = float("inf")
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
            if objective == "both":
                # Same teaching turns, one question, a *fresh* state per question:
                # the shape the evaluation uses. The only thing that differs from
                # the ``single`` arm is which questions the loss covers, so a
                # difference between the arms is the objective, not the layout.
                loss = None
                for index in range(PAIRS_PER_EPISODE):
                    state = core.init_state(len(rows))
                    _teach(core, rows, state, device)
                    # Every query in a batch has the same length (names are a
                    # fixed number of syllables), so one prefix scores them all.
                    ask_len = len(rows[0]["both"][index]["query"])
                    seq = [
                        row["both"][index]["query"] + row["both"][index]["answer"] for row in rows
                    ]
                    inputs = _tensor([s[:-1] for s in seq], device)
                    targets = _tensor([s[1:] for s in seq], device)
                    logits, _ = core.ai_step(inputs, state)
                    scored = logits[:, ask_len - 1 :, :].reshape(-1, len(table))
                    part = torch.nn.functional.cross_entropy(
                        scored, targets[:, ask_len - 1 :].reshape(-1)
                    )
                    loss = part if loss is None else loss + part
                loss = loss / PAIRS_PER_EPISODE
            else:
                state = core.init_state(len(rows))
                _teach(core, rows, state, device)
                seq = [row["query"] + row["answer"] for row in rows]
                inputs = _tensor([s[:-1] for s in seq], device)
                targets = _tensor([s[1:] for s in seq], device)
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

        dev_loss = answer_loss(core, table, dev_episodes, device=device)
        history.append(
            {
                "epoch": epoch,
                "loss": round(running / max(1, seen), 4),
                "dev_loss": round(dev_loss, 4),
            }
        )
        if dev_loss < best_loss - 1e-9:
            best_loss = dev_loss
            best_epoch = epoch
            best_state = copy.deepcopy(core.state_dict())
            stale = 0
        else:
            stale += 1
            # ``patience=0`` means "no early stopping": the registered budget is
            # fixed before the run, so the schedule cannot depend on the score.
            if patience and stale >= patience:
                break

    if best_state is not None:
        core.load_state_dict(best_state)
    return {
        "epochs_run": len(history),
        "best_epoch": best_epoch,
        "best_dev_loss": round(best_loss, 6),
        "selection": "lowest dev answer loss (exact is a step function)",
        "seconds": round(time.time() - started, 2),
        "history": history,
    }


def state_probe(
    core: Any,
    table: CharTable,
    episodes: Sequence[Dict[str, Any]],
    *,
    device: str,
    steps: int = 600,
    lr: float = 1e-2,
) -> Dict[str, Any]:
    """Linear readouts of ``h``: first-taught, second-taught, and asked value."""
    import torch

    encoded = [encode_episode(table, episode) for episode in episodes]
    features: List[Any] = []
    core.eval()
    with torch.no_grad():
        for start in range(0, len(encoded), BATCH):
            rows = encoded[start : start + BATCH]
            state = core.init_state(len(rows))
            _teach(core, rows, state, device)
            features.append(state.tensors["h"].detach())
    matrix = torch.cat(features, dim=0)

    def probe(targets: Sequence[str]) -> Dict[str, Any]:
        width = len(targets[0])
        gold = torch.tensor(
            [[table.stoi.get(ch, table.unk_id) for ch in text] for text in targets],
            dtype=torch.long,
            device=device,
        )
        half = len(matrix) // 2
        head = torch.nn.Linear(matrix.shape[1], width * len(table)).to(device)
        optimiser = torch.optim.Adam(head.parameters(), lr=lr)
        for _ in range(steps):
            logits = head(matrix[:half]).reshape(half, width, len(table))
            loss = torch.nn.functional.cross_entropy(
                logits.reshape(-1, len(table)), gold[:half].reshape(-1)
            )
            optimiser.zero_grad(set_to_none=True)
            loss.backward()
            optimiser.step()
        with torch.no_grad():
            logits = head(matrix[half:]).reshape(len(matrix) - half, width, len(table))
            match = logits.argmax(dim=-1) == gold[half:]
        return {
            "char_accuracy": round(float(match.float().mean()), 4),
            "full_exact": round(float(match.all(dim=1).float().mean()), 4),
        }

    return {
        "slot0_first_taught": probe([episode["taught"][0][1] for episode in episodes]),
        "slot1_second_taught": probe([episode["taught"][1][1] for episode in episodes]),
        "asked": probe([episode["taught"][episode["ask"]][1] for episode in episodes]),
    }


def run(args: argparse.Namespace, stamp: str) -> Dict[str, Any]:
    import torch  # fail early with a clear message

    device = _device()
    table = CharTable()
    sizes = dict(SMOKE if args.smoke else DEFAULTS)
    epochs_budget = 2 if args.smoke else args.epochs
    splits = build_splits(seed=args.seed, sizes=sizes)
    leaks = leak_check(splits)

    report: Dict[str, Any] = {
        "task_version": TASK_VERSION,
        "objective": args.objective,
        "git_head": _git_head(),
        "device": device,
        "config": {
            "hidden": args.width,
            "emb": EMB,
            "chunk_seconds": CHUNK_SECONDS,
            "lr": LEARNING_RATE,
            "batch": BATCH,
            "max_epochs": epochs_budget,
            "early_stop_patience": args.patience,
            "turn_gap_s": TURN_GAP_S,
            "seed": args.seed,
            "init_seed": SEED,
            "pairs_per_episode": PAIRS_PER_EPISODE,
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
        report["all_pass"] = False
        report["aborted"] = "leak check failed"
        return report

    core = build_core(table, device, hidden=args.width)
    report["params"] = core.parameter_count()
    report["weights_hash"] = core.weights_hash()

    report["training"] = train(
        core,
        table,
        splits["train"],
        splits["dev"],
        objective=args.objective,
        device=device,
        epochs=epochs_budget,
        batch_size=BATCH,
        lr=LEARNING_RATE,
        patience=args.patience,
        seed=args.seed,
    )

    started = time.time()
    results = {
        "dev": evaluate(core, table, splits["dev"], device=device),
        "heldout_names": evaluate(core, table, splits["heldout_names"], device=device),
        "zero_state": evaluate(
            core, table, splits["heldout_names"], device=device, zero_state=True
        ),
        "cold": evaluate(core, table, splits["cold"], device=device, teach=False),
        "wrong_name": evaluate(core, table, splits["wrong_name"], device=device),
        "both_sequential": evaluate_both(core, table, splits["dev"], device=device),
    }
    elapsed = time.time() - started
    report["results"] = results
    report["diagnostics"] = {
        "probe_dev": state_probe(core, table, splits["dev"], device=device),
        "probe_heldout": state_probe(core, table, splits["heldout_names"], device=device),
    }
    report["cost"] = {
        "params": report["params"],
        "train_seconds": report["training"]["seconds"],
        "eval_seconds": round(elapsed, 2),
        "device": device,
    }

    dev = results["dev"]["exact"]
    held = results["heldout_names"]["exact"]
    zero = results["zero_state"]["exact"]
    cold = results["cold"]["exact"]
    # B5 reads both split that are scored: a positional shortcut can look fine
    # on dev and fall apart on held-out names, and the reverse.
    per_position = [
        value
        for split in ("dev", "heldout_names")
        for value in results[split]["by_ask"]
        if value is not None
    ]
    hedging = max(results["dev"]["other_value_rate"], results["heldout_names"]["other_value_rate"])
    checks = {
        "B1_dev_exact_ge_0.60": dev >= 0.60,
        "B2_heldout_exact_ge_0.30": held >= 0.30,
        "B3_zero_state_le_0.05_and_gap_ge_0.25": (zero <= 0.05) and (held - zero) >= 0.25,
        "B4_cold_exact_le_0.02": cold <= 0.02,
        "B5_selects_not_hedges": bool(per_position)
        and min(per_position) >= 0.50
        and hedging <= 0.25,
        "B6_cost_recorded": all(
            report["cost"][key] not in (None, 0) for key in ("params", "train_seconds")
        ),
    }
    report["checks"] = checks
    report["all_pass"] = all(checks.values())

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = out_dir / f"state_binding_{args.objective}_{stamp}.pt"
    torch.save(
        {
            "task_version": TASK_VERSION,
            "objective": args.objective,
            "config": core.config(),
            "state_dict": core.state_dict(),
            "vocab": table.to_dict(),
        },
        str(checkpoint),
    )
    report["checkpoint"] = str(checkpoint)
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Round 6: can the state hold two bindings?")
    parser.add_argument("--out", default="data/state_binding")
    parser.add_argument("--objective", choices=("single", "both"), default="both")
    parser.add_argument("--width", type=int, default=HIDDEN)
    parser.add_argument("--epochs", type=int, default=MAX_EPOCHS)
    parser.add_argument(
        "--patience", type=int, default=EARLY_STOP_PATIENCE, help="0 disables early stopping"
    )
    parser.add_argument("--seed", type=int, default=SEED, help="data split seed")
    parser.add_argument("--smoke", action="store_true", help="tiny data, 2 epochs")
    parser.add_argument("--require-pass", action="store_true", help="exit 1 unless gates pass")
    args = parser.parse_args(argv)

    started = time.time()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    report = run(args, stamp)
    report["wall_seconds"] = round(time.time() - started, 2)

    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"state_binding_{args.objective}_{stamp}.json"
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"\ntask            : {report['task_version']} objective={report['objective']} "
        f"width={report['config']['hidden']} device={report['device']}"
    )
    print(f"params          : {report.get('params')}")
    print(f"leak check      : clean={report['leak_check']['clean']}")
    print(
        f"training        : {report['training']['epochs_run']} epochs, "
        f"{report['training']['seconds']}s, best epoch {report['training']['best_epoch']} "
        f"(dev loss {report['training']['best_dev_loss']})"
    )
    print("\n            split            n     exact   other  by_ask")
    for name in ("dev", "heldout_names", "zero_state", "cold", "wrong_name"):
        entry = report["results"][name]
        exact = "   n/a" if entry["exact"] is None else f"{entry['exact']:6.3f}"
        other = (
            "   n/a" if entry["other_value_rate"] is None else f"{entry['other_value_rate']:6.3f}"
        )
        extra = ""
        if entry.get("taught_value_rate") is not None:
            extra = f"  taught_value={entry['taught_value_rate']:.3f}"
        print(f"  {name:22s} {entry['n']:5d}  {exact}  {other}  {entry['by_ask']}{extra}")
    print(f"  both_sequential (diag)  {report['results']['both_sequential']}")
    print("\n  probes (char / full)")
    for name, entry in report["diagnostics"]["probe_dev"].items():
        print(f"    dev      {name:22s} {entry['char_accuracy']:6.3f} {entry['full_exact']:6.3f}")
    for name, entry in report["diagnostics"]["probe_heldout"].items():
        print(f"    heldout  {name:22s} {entry['char_accuracy']:6.3f} {entry['full_exact']:6.3f}")
    print("\n  checks")
    for name, passed in report["checks"].items():
        print(f"    {'PASS' if passed else 'FAIL'}  {name}")
    print(f"\nall_pass        : {report['all_pass']}")
    print(f"report          : {path}")
    print(f"checkpoint      : {report.get('checkpoint')}")
    return 0 if (report["all_pass"] or not args.require_pass) else 1


if __name__ == "__main__":
    raise SystemExit(main())
