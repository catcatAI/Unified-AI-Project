# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""Token-level spiking decoder trained with surrogate gradients.

Why this module exists
----------------------
``DictionaryLayer.encode()`` represents text as CC-CEDICT/JMdict *glosses*
(``encode("12 + 7")`` -> ``m2``, ``cedict_1_divided_by_16...``). Two different
questions therefore share most keys, and ``StepDecoder`` prints gloss surfaces:
the association trainer can reach acc=1.0 and the decoder still emits word
salad. That is a representation problem, not a training budget problem.

This module replaces the representation and the objective:

* **tokens** — a vocabulary built from the training data, in two kinds:
  ``CharVocab`` (characters, the original) or ``TokenVocab`` (self-delimiting
  word atoms — a word absorbs its leading whitespace, GPT-2 style, and
  numbers split into digits, so a 74-character question costs ~16-25 steps
  instead of 74 and unseen numbers still compose). Measured on the same
  pairs: character level stops
  learning at ~70 steps (init CE 24 nats, 0/300 memorised) while ~18 steps
  learns normally — so long questions need the token kind.
* **differentiable output** — LIF neurons with a surrogate gradient
  (Neftci, Mostafa & Zenke 2019) followed by a linear next-token head,
* **objective** — cross-entropy on the *answer* tokens only (teacher forcing),
  so the model learns conditional generation rather than association.

It is intentionally small (embedding -> LIF -> linear), CPU-friendly, and
torch-optional: importing this module does not import torch; ``build_model``
does. Nothing here is loaded by the production chat path — wiring it in is a
separate, measurable step.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PAD, BOS, EOS, UNK = "<pad>", "<bos>", "<eos>", "<unk>"
SPECIALS = (PAD, BOS, EOS, UNK)
# Marker between the free-text response and the AL state block in the AI+AL
# data format (``prepare_ai_al_training_data.py``). Answers without it — the
# whole core corpus — are treated as one response, so nothing here changes
# for them.
AL_OUT_MARK = "<al_out>"


@dataclass
class TokenConfig:
    d_emb: int = 96
    d_hidden: int = 192
    # ``beta`` is the membrane leak used *directly* (0.9 keeps 35% of the
    # state after 10 steps). It used to be pushed through ``sigmoid()``
    # before use, so a configured 0.9 silently ran at sigmoid(0.9)=0.711
    # (3% after 10 steps) — a parameterisation bug that shortened every
    # memory horizon. The parameter is now stored as its logit, so the
    # effective value equals the configured value.
    beta: float = 0.9
    threshold: float = 0.5
    surrogate_alpha: float = 5.0
    # ``readout`` selects what the output head reads each step:
    #   "membrane" — the membrane potential (SLAYER, Shrestha & Orchard
    #                2018: read the last layer's state instead of its
    #                threshold crossings). The recurrence stays spiking in
    #                both cases; only the readout differs. This is the
    #                measured winner at equal budget (CORE_GAP_ANALYSIS §7),
    #                so it is the default.
    #   "spike"    — binary spikes (the original head; kept as the A/B
    #                control, reproducible with --readout spike).
    readout: str = "membrane"
    # ``layers`` stacks LIF layers (input drives layer 0, spikes drive the
    # next layer). Depth costs ~1x compute per added layer on CPU.
    layers: int = 1
    # ``timesteps`` runs each token through the network K times before the
    # head reads it (input expansion — the standard temporal-resolution
    # knob in SNN sequence models). Costs Kx compute in forward and
    # generate; gives the recurrent dynamics K updates per token.
    timesteps: int = 1
    max_len: int = 192
    min_count: int = 2
    max_vocab: int = 12000

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CharVocab:
    """Character-level vocabulary with a closed set of special tokens."""

    def __init__(self, tokens: Sequence[str]) -> None:
        self.itos: List[str] = list(tokens)
        self.stoi: Dict[str, int] = {t: i for i, t in enumerate(self.itos)}
        for special in (*SPECIALS, "\n"):
            if special not in self.stoi:
                self.stoi[special] = len(self.itos)
                self.itos.append(special)

    @property
    def pad_id(self) -> int:
        return self.stoi[PAD]

    @property
    def bos_id(self) -> int:
        return self.stoi[BOS]

    @property
    def eos_id(self) -> int:
        return self.stoi[EOS]

    @classmethod
    def build(
        cls,
        texts: Iterable[str],
        min_count: int = 2,
        max_vocab: int = 12000,
    ) -> "CharVocab":
        counts: Dict[str, int] = {}
        for text in texts:
            for ch in text:
                counts[ch] = counts.get(ch, 0) + 1
        ordered = [ch for ch, n in counts.items() if n >= min_count and ch not in SPECIALS]
        ordered.sort(key=lambda ch: (-counts[ch], ch))
        return cls(ordered[:max_vocab])

    def encode(self, text: str, add_eos: bool = False) -> List[int]:
        ids = [self.stoi.get(ch, self.stoi[UNK]) for ch in text]
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids: Iterable[int], skip_special: bool = True) -> str:
        out = []
        for i in ids:
            if i < 0 or i >= len(self.itos):
                continue
            token = self.itos[i]
            if skip_special and token in SPECIALS:
                if token == EOS:
                    break
                continue
            out.append(token)
        return "".join(out)

    def to_dict(self) -> Dict[str, Any]:
        return {"itos": self.itos}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharVocab":
        return cls(data["itos"])

    def __len__(self) -> int:
        return len(self.itos)


# One atom at a time, with a catch-all so "".join(tokenize(s)) == s always:
# ASCII words / numbers (with . , and a trailing %) / CJK characters /
# punctuation / a whitespace run *with the one character that follows it* /
# anything unmatched as a single character.
#
# The ``\s+.`` grouping is deliberate (GPT-2-style leading-space atoms):
# ``tokenize("the cat") == ["the", " c", "at"]`` — a word absorbs the
# whitespace *before* it, so decode is a plain join. The final ``.`` must
# stay a *separate* alternative: without it, a trailing whitespace run
# (nothing follows to absorb) and chars like ``_`` match no alternative and
# are silently dropped — join(tokenize(s)) != s. Ordered alternation means
# the catch-all only fires where nothing else matched, so atom boundaries
# for text that already tokenized fully are unchanged (checkpoint vocab
# compatibility).
_ATOM = re.compile(
    r"[A-Za-z]+" r"|\d+(?:[.,]\d+)*%?" r"|[\u3400-\u4dbf\u4e00-\u9fff]" r"|[^\w\s]" r"|\s+." r"|.",
    re.S,
)


def tokenize(text: str) -> List[str]:
    """Split text into self-delimiting atoms (decode is a plain join).

    * a word absorbs the whitespace *before* it — ``tokenize("the cat") ==
      ["the", " c", "at"]`` (leading-space atoms, GPT-2 style) — so joining
      needs no rules and roundtrips exactly; leading whitespace with nothing
      behind it stays alone;
    * numbers split into single digits, so an answer value never seen in
      training (``"214.0"``) can still be composed instead of becoming
      ``<unk>``;
    * a bare ``"\n"`` never comes out of tokenize (it is always absorbed or
      followed); the vocabulary still reserves it as the prompt/answer
      separator (``encode_pair`` inserts the id directly).
    """
    out: List[str] = []
    for atom in _ATOM.findall(str(text or "")):
        if atom.isspace():
            if "\n" in atom or not out:
                out.append(atom)
            else:
                out[-1] += atom
        elif atom[0].isdigit():
            out.extend(atom)
        else:
            out.append(atom)
    return out


class TokenVocab:
    """Word-atom vocabulary: same contract as :class:`CharVocab`, longer horizon.

    ``to_dict()`` adds ``kind: "token"`` so ``TokenSNN.load`` can dispatch
    without guessing; a missing kind means the historical character vocab.
    """

    kind = "token"

    def __init__(self, tokens: Sequence[str]) -> None:
        self.itos: List[str] = list(tokens)
        self.stoi: Dict[str, int] = {t: i for i, t in enumerate(self.itos)}
        for special in (*SPECIALS, "\n"):
            if special not in self.stoi:
                self.stoi[special] = len(self.itos)
                self.itos.append(special)

    @property
    def pad_id(self) -> int:
        return self.stoi[PAD]

    @property
    def bos_id(self) -> int:
        return self.stoi[BOS]

    @property
    def eos_id(self) -> int:
        return self.stoi[EOS]

    @property
    def unk_id(self) -> int:
        return self.stoi[UNK]

    @classmethod
    def build(
        cls,
        texts: Iterable[str],
        min_count: int = 1,
        max_vocab: int = 12000,
    ) -> "TokenVocab":
        counts: Dict[str, int] = {}
        for text in texts:
            for atom in tokenize(text):
                counts[atom] = counts.get(atom, 0) + 1
        ordered = [a for a, n in counts.items() if n >= min_count and a not in SPECIALS]
        ordered.sort(key=lambda a: (-counts[a], a))
        return cls(ordered[:max_vocab])

    def encode(self, text: str, add_eos: bool = False) -> List[int]:
        unk = self.stoi[UNK]
        ids = [self.stoi.get(atom, unk) for atom in tokenize(text)]
        if add_eos:
            ids.append(self.eos_id)
        return ids

    def decode(self, ids: Iterable[int], skip_special: bool = True) -> str:
        out = []
        for i in ids:
            if i < 0 or i >= len(self.itos):
                continue
            token = self.itos[i]
            if skip_special and token in SPECIALS:
                if token == EOS:
                    break
                continue
            out.append(token)
        return "".join(out)

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "itos": self.itos}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenVocab":
        return cls(data["itos"])

    def __len__(self) -> int:
        return len(self.itos)


def _make_net(torch: Any, pad_id: int = 0) -> Any:
    """Define the nn.Module lazily so importing this file stays torch-free."""
    nn = torch.nn

    class _SpikeNet(torch.nn.Module):
        def __init__(self, vocab_size: int, cfg: TokenConfig) -> None:
            super().__init__()
            self.cfg = cfg
            self.n_layers = max(1, int(cfg.layers))
            if cfg.readout not in ("spike", "membrane"):
                raise ValueError(f"readout must be 'spike' or 'membrane', got {cfg.readout!r}")
            # padding_idx must be the *real* PAD id: CharVocab/TokenVocab
            # append specials after the content tokens, so PAD is not 0 —
            # hard-coding 0 used to freeze the most frequent token's embedding
            # at the zero vector and give PAD a trained one.
            self.embed = nn.Embedding(vocab_size, cfg.d_emb, padding_idx=pad_id)
            self.w_in = nn.ModuleList(
                nn.Linear(cfg.d_emb if i == 0 else cfg.d_hidden, cfg.d_hidden)
                for i in range(self.n_layers)
            )
            self.w_rec = nn.ModuleList(
                nn.Linear(cfg.d_hidden, cfg.d_hidden, bias=False) for _ in range(self.n_layers)
            )
            self.head = nn.Linear(cfg.d_hidden, vocab_size)
            # Membrane potential accumulates with steady-state gain ~1/(1-leak)
            # (=10x at beta 0.9), so raw membrane saturates the softmax on
            # long inputs (measured: init CE 19 nats at 18 chars, 24+ at 74).
            # Normalise before the head; the spike readout (A/B control) is
            # left untouched because a binary vector has no meaningful scale.
            self.out_norm = nn.LayerNorm(cfg.d_hidden)
            # Store the logit so sigmoid(parameter) == cfg.beta exactly.
            self.beta = nn.Parameter(
                torch.logit(torch.tensor(float(cfg.beta)).clamp(1e-4, 1 - 1e-4))
            )
            self.threshold = nn.Parameter(torch.tensor(cfg.threshold))

        def _spike(self, x: Any) -> Any:
            # Surrogate gradient: hard forward value, fast-sigmoid derivative.
            hard = (x >= 0).to(x.dtype)
            soft = torch.sigmoid(self.cfg.surrogate_alpha * x)
            return hard.detach() + soft - soft.detach()

        def forward(self, ids: Any) -> Any:
            batch, steps = ids.shape
            leak = torch.sigmoid(self.beta)
            mem = [
                self.embed.weight.new_zeros((batch, self.cfg.d_hidden))
                for _ in range(self.n_layers)
            ]
            spk = [
                self.embed.weight.new_zeros((batch, self.cfg.d_hidden))
                for _ in range(self.n_layers)
            ]
            logits = []
            for t in range(steps):
                x = self.embed(ids[:, t])
                for _ in range(max(1, int(self.cfg.timesteps))):
                    for layer in range(self.n_layers):
                        drive = x if layer == 0 else spk[layer - 1]
                        mem[layer] = (
                            leak * mem[layer]
                            + self.w_in[layer](drive)
                            + self.w_rec[layer](spk[layer])
                        )
                        spk[layer] = self._spike(mem[layer] - torch.abs(self.threshold))
                out = (
                    mem[self.n_layers - 1]
                    if self.cfg.readout == "membrane"
                    else spk[self.n_layers - 1]
                )
                if self.cfg.readout == "membrane":
                    out = self.out_norm(out)
                logits.append(self.head(out))
            return torch.stack(logits, dim=1)

    return _SpikeNet


def resolve_device(torch: Any, wanted: str = "auto") -> str:
    """Pick a torch device: explicit name, or auto (xpu > cuda > cpu).

    ``auto`` prefers the GPU because surrogate-gradient BPTT through time is
    compute-bound; on CPU the same run is 1-2 orders of magnitude slower.
    Only floating-point dtypes the device supports are used — consumer Intel
    Arc cards have no FP64, so nothing here ever creates double tensors.
    """
    if wanted and wanted != "auto":
        return wanted
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


class TokenSNN:
    """Small token-level SNN language model (torch required at build time)."""

    def __init__(
        self,
        vocab: Any,
        config: Optional[TokenConfig] = None,
        device: str = "auto",
    ) -> None:
        import torch  # lazy: keeps torch out of import time

        self.torch = torch
        self.vocab = vocab
        self.config = config or TokenConfig()
        self.device = resolve_device(torch, device)
        net_cls = _make_net(torch, pad_id=vocab.pad_id)
        self.net = net_cls(len(vocab), self.config).to(self.device)

    # -- batching -----------------------------------------------------------
    def encode_pair(self, prompt: str, answer: str) -> Tuple[List[int], int]:
        """Return ids and the index where the answer starts."""
        ids, start, _ = self._encode(prompt, answer)
        return ids, start

    def _encode(self, prompt: str, answer: str) -> Tuple[List[int], int, int]:
        """(ids, answer_start, response_end).

        ``response_end`` is where ``<al_out>`` begins, so a weighted loss and
        the split accuracy can tell the free-text response apart from the
        formulaic state block. Round-1 measurement (2026-10-30): the state
        block is 34% of answer tokens and reached 77-80% teacher-forced while
        the response sat at 14-26% — the easy part was carrying the loss. An
        answer without the marker ends where the answer ends, i.e. it is all
        response.
        """
        prompt = prompt.strip()
        answer = answer.strip()
        budget = self.config.max_len
        body = answer.split(AL_OUT_MARK, 1)[0] if AL_OUT_MARK in answer else answer
        body_ids = self.vocab.encode(body)
        ids = [self.vocab.bos_id] + self.vocab.encode(prompt)
        prompt_len = len(ids)
        ids.append(self.vocab.stoi["\n"])
        prompt_len += 1  # first answer character
        ids.extend(self.vocab.encode(answer))
        ids.append(self.vocab.eos_id)
        response_end = prompt_len + len(body_ids)
        if len(ids) > budget:
            # Keep the beginning of the prompt and as much of the answer as fits.
            keep_tail = budget - prompt_len
            if keep_tail < 8:
                prompt_keep = max(4, budget - 32)
                ids = (
                    ids[:prompt_keep]
                    + [self.vocab.stoi["\n"]]
                    + ids[prompt_len:][: budget - prompt_keep - 1]
                )
                prompt_len = prompt_keep + 1
            else:
                ids = ids[:budget]
            # truncation may have eaten the state block: never point past the row
            response_end = min(prompt_len + len(body_ids), len(ids))
        return ids, prompt_len, response_end

    def make_batch(self, pairs: Sequence[Tuple[str, str]]) -> Tuple[Any, Any, Any]:
        torch = self.torch
        rows = []
        starts = []
        for prompt, answer in pairs:
            ids, start = self.encode_pair(prompt, answer)
            rows.append(ids)
            starts.append(start)
        width = max(len(r) for r in rows)
        ids_t = torch.full(
            (len(rows), width), self.vocab.pad_id, dtype=torch.long, device=self.device
        )
        mask = torch.zeros((len(rows), width), dtype=torch.bool, device=self.device)
        for i, (row, start) in enumerate(zip(rows, starts)):
            ids_t[i, : len(row)] = torch.tensor(row, dtype=torch.long, device=self.device)
            mask[i, start : len(row)] = True
        return ids_t, mask, starts

    def make_batch_weighted(
        self, pairs: Sequence[Tuple[str, str]], tail_weight: float = 1.0
    ) -> Tuple[Any, Any, List[int], Any]:
        """The make_batch contents plus a per-position loss weight.

        Positions from ``<al_out>`` onward (the AL state block) get
        ``tail_weight``; everything before keeps 1.0. Weights outside the
        answer region are irrelevant — ``loss`` multiplies them by the mask.
        """
        torch = self.torch
        rows: List[List[int]] = []
        starts: List[int] = []
        cuts: List[int] = []
        for prompt, answer in pairs:
            ids, start, cut = self._encode(prompt, answer)
            rows.append(ids)
            starts.append(start)
            cuts.append(cut)
        width = max(len(r) for r in rows)
        ids_t = torch.full(
            (len(rows), width), self.vocab.pad_id, dtype=torch.long, device=self.device
        )
        mask = torch.zeros((len(rows), width), dtype=torch.bool, device=self.device)
        weights = torch.ones((len(rows), width), dtype=torch.float, device=self.device)
        for i, (row, start, cut) in enumerate(zip(rows, starts, cuts)):
            ids_t[i, : len(row)] = torch.tensor(row, dtype=torch.long, device=self.device)
            mask[i, start : len(row)] = True
            # `cut` lands on the eos of a marker-free answer; that eos ends the
            # response, so it must not be down-weighted. The state block only
            # exists when the marker sits *before* the eos.
            if cut < len(row) - 1:
                weights[i, cut:] = tail_weight
        return ids_t, mask, starts, weights

    def loss(self, ids: Any, mask: Any, weights: Any = None) -> Any:
        torch = self.torch
        logits = self.net(ids)
        # Predict token t+1 from prefix <= t, only where the target is answer/eos.
        logits = logits[:, :-1, :]
        targets = ids[:, 1:]
        target_mask = mask[:, 1:]
        flat_logits = logits.reshape(-1, logits.shape[-1])
        flat_targets = targets.reshape(-1)
        flat_mask = target_mask.reshape(-1)
        if int(flat_mask.sum()) == 0:
            return logits.sum() * 0.0
        per_tok = torch.nn.functional.cross_entropy(
            flat_logits[flat_mask], flat_targets[flat_mask], reduction="none"
        )
        if weights is None:
            return per_tok.mean()
        w = weights[:, 1:].reshape(-1)[flat_mask]
        # Weighted *mean*, not sum: the scale stays comparable to an unweighted
        # run, so a tail weight never silently rescales the learning rate.
        return (per_tok * w).sum() / w.sum().clamp(min=1e-6)

    # -- diagnostics ---------------------------------------------------------
    def tf_accuracy(self, pairs: Sequence[Tuple[str, str]]) -> Dict[str, float]:
        """Teacher-forced per-token accuracy over answer positions.

        A memorisation/optimisation signal only: 100% here with 0% exact
        means greedy decoding drifts (exposure bias), while a low value here
        means the model has not learned the mapping at all.
        """
        torch = self.torch
        was_training = self.net.training
        self.net.eval()
        hits = 0
        total = 0
        with torch.no_grad():
            for start in range(0, len(pairs), 32):
                ids, mask, _ = self.make_batch(list(pairs[start : start + 32]))
                pred = self.net(ids)[:, :-1, :].argmax(dim=-1)
                target = ids[:, 1:]
                keep = mask[:, 1:]
                hits += int(((pred == target) & keep).sum().item())
                total += int(keep.sum().item())
        if was_training:
            self.net.train()
        return {"tokens": total, "tf_acc": round(hits / max(1, total), 4)}

    def split_tf_accuracy(self, pairs: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
        """Teacher-forced accuracy split into response vs ``<al_out>`` state block.

        Why this exists: the aggregate ``tf_accuracy`` is *not* comparable
        across runs whose answer mix differs — round 1's headline 61.76% was
        inflated by the formulaic state block (77-80% there vs 14-26% on the
        response itself). Answer without the marker: the tail bucket is empty
        and the response number equals the aggregate one.
        """
        torch = self.torch
        was_training = self.net.training
        self.net.eval()
        resp_hit = resp_tot = tail_hit = tail_tot = 0
        with torch.no_grad():
            for start in range(0, len(pairs), 32):
                chunk = list(pairs[start : start + 32])
                rows, starts, cuts = [], [], []
                for prompt, answer in chunk:
                    ids, a_start, cut = self._encode(prompt, answer)
                    rows.append(ids)
                    starts.append(a_start)
                    cuts.append(cut)
                width = max(len(r) for r in rows)
                ids_t = torch.full(
                    (len(rows), width),
                    self.vocab.pad_id,
                    dtype=torch.long,
                    device=self.device,
                )
                mask = torch.zeros((len(rows), width), dtype=torch.bool, device=self.device)
                for i, (row, a_start) in enumerate(zip(rows, starts)):
                    ids_t[i, : len(row)] = torch.tensor(row, dtype=torch.long, device=self.device)
                    mask[i, a_start : len(row)] = True
                pred = self.net(ids_t)[:, :-1, :].argmax(dim=-1)
                target = ids_t[:, 1:]
                keep = mask[:, 1:]
                for i, cut in enumerate(cuts):
                    # token index = pos + 1; the row's last token is its eos.
                    # A marker-free answer has cut == eos, so its range is empty.
                    tail_from, tail_to = (
                        (cut, len(rows[i]) - 1) if cut < len(rows[i]) - 1 else (1, 0)
                    )
                    for pos in range(width - 1):
                        if not bool(keep[i, pos]):
                            continue
                        ok = bool(pred[i, pos] == target[i, pos])
                        if tail_from <= pos + 1 <= tail_to:
                            tail_hit += int(ok)
                            tail_tot += 1
                        else:
                            resp_hit += int(ok)
                            resp_tot += 1
        if was_training:
            self.net.train()
        return {
            "response_tf": round(resp_hit / max(1, resp_tot), 4),
            "tail_tf": round(tail_hit / max(1, tail_tot), 4),
            "response_tokens": resp_tot,
            "tail_tokens": tail_tot,
        }

    # -- training -----------------------------------------------------------
    def train_on(
        self,
        pairs: Sequence[Tuple[str, str]],
        epochs: int = 1,
        batch_size: int = 32,
        lr: float = 3e-3,
        seed: int = 0,
        log: Any = None,
        on_epoch: Any = None,
        tail_weight: float = 1.0,
    ) -> List[Dict[str, float]]:
        torch = self.torch
        torch.manual_seed(seed)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        history: List[Dict[str, float]] = []
        order = list(range(len(pairs)))
        for epoch in range(epochs):
            torch.manual_seed(seed + epoch)
            shuffled = order[:]
            import random

            random.Random(seed + epoch).shuffle(shuffled)
            total = 0.0
            steps = 0
            for start in range(0, len(shuffled), batch_size):
                chunk = [pairs[i] for i in shuffled[start : start + batch_size]]
                opt.zero_grad()
                if tail_weight == 1.0:
                    ids, mask, _ = self.make_batch(chunk)
                    loss = self.loss(ids, mask)
                else:
                    ids, mask, _, weights = self.make_batch_weighted(chunk, tail_weight)
                    loss = self.loss(ids, mask, weights)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                opt.step()
                total += float(loss.detach())
                steps += 1
            history.append({"epoch": epoch, "loss": total / max(1, steps)})
            if log is not None:
                log(history[-1])
            if on_epoch is not None:
                on_epoch(history[-1])
        return history

    # -- inference ----------------------------------------------------------
    def generate(
        self,
        prompt: str,
        max_new: int = 64,
        temperature: float = 0.0,
    ) -> str:
        torch = self.torch
        ids, _ = self.encode_pair(prompt, "")
        ids = ids[:-1] if ids and ids[-1] == self.vocab.eos_id else ids
        ids = ids[: self.config.max_len - 1]
        self.net.eval()
        out: List[int] = []
        with torch.no_grad():
            cur = torch.tensor([ids], dtype=torch.long, device=self.device)
            for _ in range(max_new):
                logits = self.net(cur)[0, -1]
                if temperature <= 0:
                    nxt = int(torch.argmax(logits).item())
                else:
                    probs = torch.softmax(logits / temperature, dim=-1)
                    nxt = int(torch.multinomial(probs, 1).item())
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

    # -- persistence --------------------------------------------------------
    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.torch.save(
            {
                "vocab": self.vocab.to_dict(),
                "config": self.config.to_dict(),
                "state": self.net.state_dict(),
            },
            str(path),
        )

    @classmethod
    def load(cls, path: Path | str, map_location: str = "cpu", device: str = "auto") -> "TokenSNN":
        import torch

        # weights_only=True: the checkpoint is {vocab: dict, config: dict, state_dict}.
        # Loading pickled objects would let a crafted checkpoint execute code.
        payload = torch.load(str(path), map_location=map_location, weights_only=True)
        vocab_data = payload["vocab"]
        vocab_cls = TokenVocab if vocab_data.get("kind") == "token" else CharVocab
        vocab = vocab_cls.from_dict(vocab_data)
        model = cls(vocab, TokenConfig(**payload["config"]), device=device)
        model.net.load_state_dict(payload["state"])
        model.net.eval()
        return model


__all__ = [
    "CharVocab",
    "TokenVocab",
    "TokenConfig",
    "TokenSNN",
    "tokenize",
    "resolve_device",
    "SPECIALS",
    "PAD",
    "BOS",
    "EOS",
    "UNK",
]
