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
import math
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
    # ``theta_max`` bounds the learned threshold (CORE_GAP §三十). The surrogate
    # gradient is sigmoid(alpha * (mem - theta)), so a threshold that drifts far
    # above the membrane distribution is a *free* way to stop learning: round-9
    # trained theta from 0.5 to 6.75, silenced 97% of its spikes and left
    # |mem| = 24.5, all while the loss curve looked fine. The threshold is a
    # parameter (that part works), so the bound is a projection after each step
    # rather than a reparametrisation: the forward path and every existing
    # checkpoint stay bit-identical while the value is held inside the band where
    # spikes carry gradient. 0 disables the bound (the historical behaviour).
    theta_max: float = 2.0
    # ``leak_floor`` keeps the membrane from *buying* short horizons.
    # Measured (probe_stability, 200 rows, 120 epochs): while the loss falls,
    # beta slides 0.900 -> 0.826 and sr(w_rec) climbs 0.55 -> 1.29, i.e. the
    # stack trades local integration for faster wire-through, and autonomous
    # activity after the input stops decays 0.54 -> 0.16. The trade is degenerate
    # (the product is what the task sees, and beta has a hard ceiling at 1), so
    # leaving both free lets every run sidle toward the same corner: no memory,
    # gain above 1, structure held only by the threshold clip. 0 disables.
    leak_floor: float = 0.0
    # ``gain_cap`` bounds the spectral radius of each recurrent matrix (power
    # iteration + rescale after the step). >1 means a perturbation grows for a
    # step, so the only thing keeping the stack bounded is the threshold, i.e.
    # saturation. 0 disables. Both bounds are projections, like theta_max, so a
    # checkpoint written without them loads and runs unchanged.
    gain_cap: float = 0.0
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

    def __post_init__(self) -> None:
        # Validate at config creation, not inside the net factory: a bad
        # readout is a caller error and should fail before any weights exist.
        if self.readout not in ("spike", "membrane"):
            raise ValueError(f"readout must be 'spike' or 'membrane', got {self.readout!r}")

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

# CORE_GAP §十八: the contract's own value grid. State-block values always carry
# one digit before the dot and two after, inside [-1.00, 1.00], so the graded
# alphabet is 201 atoms — closed, bounded, and independent of the data.
# ``dt`` is the one contract input that leaves the state range: its four rungs
# are 0.25 / 0.50 / 1.00 / 2.00, and 3 of them already sit in the value grid.
# Adding 2.00 keeps the *tested* feature (dt conditioning) in the same
# representation as everything else instead of splitting only that rung into
# digits, which would confuse the comparison rather than measure it.
_CONTRACT_EXTRA_ATOMS: Tuple[str, ...] = ("2.00",)
_VALUE_ATOMS: Tuple[str, ...] = (
    tuple(f"{i / 100:.2f}" for i in range(-100, 101)) + _CONTRACT_EXTRA_ATOMS
)
STATE_VALUE_ATOMS = frozenset(_VALUE_ATOMS)
_VALUE_CAND = re.compile(r"(-?\d\.\d\d)(?![0-9])")

# The same closed alphabet at a different precision. Round-7's 3-dp corpus writes
# ``0.261``, which the 2-dp candidate pattern above cannot match (it needs exactly
# two decimals and no third digit follows), so ``numeric_atoms=True`` silently did
# nothing on that corpus — measured: block accuracy 0.721 with the flag against
# 0.723 without, i.e. a no-op, because every value atom was still emitted digit by
# digit. ``value_decimals`` picks which grid the corpus is written on.
_VALUE_ATOMS_BY_DECIMALS: Dict[int, Tuple[str, ...]] = {
    2: _VALUE_ATOMS,
    3: tuple(f"{i / 1000:.3f}" for i in range(-1000, 1001)),
}


def _value_candidate(decimals: int) -> "re.Pattern[str]":
    return re.compile(rf"(-?\d\.\d{{{decimals}}})(?![0-9])")


def _tokenize_plain(text: str) -> List[str]:
    """The historical atomisation: words, and digits split one by one."""
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


def tokenize(text: str, numeric_atoms: bool = False, value_decimals: int = 2) -> List[str]:
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

    ``numeric_atoms=True`` changes one rule: a *contract value* — one digit, a
    dot, two decimals, inside ``[-1.00, 1.00]`` — becomes a single atom instead
    of three or four ids. That is the interface fix of CORE_GAP §十八: the
    graded block is six such values, and with digits split apart the model must
    do carrying arithmetic token by token, which neither the SNN nor a matched
    transformer ever learned (0/200 each). As an atom the same mapping is a
    201-way choice per field, i.e. the ``copy-with-scale`` operation the
    contract actually asks for. Everything else — response numbers, words,
    punctuation — keeps the historical atomisation, so unseen response values
    can still be composed and ``"".join(tokenize(x)) == x`` still holds.
    """
    raw = str(text or "")
    if not numeric_atoms:
        return _tokenize_plain(raw)
    atoms = _VALUE_ATOMS_BY_DECIMALS.get(int(value_decimals))
    if atoms is None:
        raise ValueError(
            f"value_decimals={value_decimals} has no alphabet; "
            f"choose one of {sorted(_VALUE_ATOMS_BY_DECIMALS)}"
        )
    grid = frozenset(atoms)
    cand = _value_candidate(int(value_decimals))
    out: List[str] = []
    for part in cand.split(raw):
        if not part:
            continue
        if part in grid:
            out.append(part)
        else:
            out.extend(_tokenize_plain(part))
    return out


class TokenVocab:
    """Word-atom vocabulary: same contract as :class:`CharVocab`, longer horizon.

    ``to_dict()`` adds ``kind: "token"`` so ``TokenSNN.load`` can dispatch
    without guessing; a missing kind means the historical character vocab.
    """

    kind = "token"

    def __init__(
        self, tokens: Sequence[str], numeric_atoms: bool = False, value_decimals: int = 2
    ) -> None:
        self.itos: List[str] = list(tokens)
        self.stoi: Dict[str, int] = {t: i for i, t in enumerate(self.itos)}
        self.numeric_atoms = bool(numeric_atoms)
        self.value_decimals = int(value_decimals)
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
        numeric_atoms: bool = False,
        value_decimals: int = 2,
    ) -> "TokenVocab":
        counts: Dict[str, int] = {}
        for text in texts:
            for atom in tokenize(text, numeric_atoms, value_decimals):
                counts[atom] = counts.get(atom, 0) + 1
        ordered = [a for a, n in counts.items() if n >= min_count and a not in SPECIALS]
        ordered.sort(key=lambda a: (-counts[a], a))
        if numeric_atoms:
            # The alphabet is closed *by contract*: seed every value atom ahead
            # of the data-driven list so (a) a gold value unseen in training is
            # still emittable and (b) max_vocab cannot truncate it — a budget
            # smaller than the alphabet keeps the alphabet and drops words,
            # because a missing value atom is unlearnable while a missing word
            # only degrades to <unk>.
            atoms = _VALUE_ATOMS_BY_DECIMALS[int(value_decimals)]
            closed = frozenset(atoms)
            extra = [a for a in ordered if a not in closed]
            return cls(
                list(atoms) + extra[: max(0, max_vocab - len(atoms))], True, int(value_decimals)
            )
        return cls(ordered[:max_vocab], numeric_atoms=numeric_atoms, value_decimals=value_decimals)

    def encode(self, text: str, add_eos: bool = False) -> List[int]:
        unk = self.stoi[UNK]
        ids = [
            self.stoi.get(atom, unk)
            for atom in tokenize(text, self.numeric_atoms, self.value_decimals)
        ]
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
        return {
            "kind": self.kind,
            "itos": self.itos,
            "numeric_atoms": self.numeric_atoms,
            "value_decimals": self.value_decimals,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenVocab":
        return cls(
            data["itos"],
            numeric_atoms=bool(data.get("numeric_atoms", False)),
            value_decimals=int(data.get("value_decimals", 2)),
        )

    def __len__(self) -> int:
        return len(self.itos)


def encode_ids(vocab: Any, prompt: str, answer: str, max_len: int) -> Tuple[List[int], int, int]:
    """``[BOS] prompt ['\\n'] answer [EOS]`` clipped to ``max_len``.

    Returns ``(ids, answer_start, response_end)``. It lives here, outside the
    model, because the distillation cache builder needs the *same* ids a run
    would feed the network — and a second copy of this arithmetic would drift
    from the first one silently (the ids are what the cached positions index).
    """
    prompt = prompt.strip()
    answer = answer.strip()
    budget = max_len
    body = answer.split(AL_OUT_MARK, 1)[0] if AL_OUT_MARK in answer else answer
    body_ids = vocab.encode(body)
    ids = [vocab.bos_id] + vocab.encode(prompt)
    prompt_len = len(ids)
    ids.append(vocab.stoi["\n"])
    prompt_len += 1  # first answer character
    ids.extend(vocab.encode(answer))
    ids.append(vocab.eos_id)
    response_end = prompt_len + len(body_ids)
    if len(ids) > budget:
        # Keep the beginning of the prompt and as much of the answer as fits.
        keep_tail = budget - prompt_len
        if keep_tail < 8:
            prompt_keep = max(4, budget - 32)
            ids = (
                ids[:prompt_keep]
                + [vocab.stoi["\n"]]
                + ids[prompt_len:][: budget - prompt_keep - 1]
            )
            prompt_len = prompt_keep + 1
        else:
            ids = ids[:budget]
        # truncation may have eaten the state block: never point past the row
        response_end = min(prompt_len + len(body_ids), len(ids))
    return ids, prompt_len, response_end


def _make_net(torch: Any, pad_id: int = 0) -> Any:
    """Define the nn.Module lazily so importing this file stays torch-free."""
    nn = torch.nn

    class _SpikeNet(torch.nn.Module):
        def __init__(self, vocab_size: int, cfg: TokenConfig) -> None:
            super().__init__()
            self.cfg = cfg
            self.n_layers = max(1, int(cfg.layers))
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
            self.w_skip = nn.ModuleList(
                [nn.Identity()]
                + [nn.Linear(cfg.d_emb, cfg.d_hidden) for _ in range(self.n_layers - 1)]
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

        def init_state(self, batch: int, device: Any = None) -> Any:
            """Zero (mem, spk) per layer — the state a sequence starts from.

            Exposed so autoregressive decoding can carry the state and advance
            one token at a time: ``generate()`` used to re-run the whole prefix
            for every new token (O(n²) forwards), which at 10^8 parameters is
            the difference between minutes and hours for a 115-item benchmark.
            """
            # The tensors follow the module's weights; ``device`` stays in the
            # signature so a caller can be explicit without it ever disagreeing
            # with where the parameters actually live.
            shape = (batch, self.cfg.d_hidden)
            mem = [self.embed.weight.new_zeros(shape) for _ in range(self.n_layers)]
            spk = [self.embed.weight.new_zeros(shape) for _ in range(self.n_layers)]
            return mem, spk

        def advance_hidden(self, token_ids: Any, state: Any) -> Any:
            """Feed one token per row; return (pre-head vector, new_state).

            ``advance`` applies the vocabulary head to this. Training only
            needs the head on answer positions (see ``TokenSNN.loss``), and the
            head is ``d_hidden x vocab`` — >90% of the compute per token at
            10^8 parameters — so the split matters.
            """
            mem, spk = state
            leak = torch.sigmoid(self.beta)
            # Accept (batch,) or (batch, 1): both mean one token per row. Without
            # the flatten a (batch, 1) input propagates an extra dimension
            # through the embedding and the head returns (batch, 1, vocab).
            x = self.embed(token_ids.reshape(-1))
            for _ in range(max(1, int(self.cfg.timesteps))):
                # ``drive`` carries the previous layer's spikes so layer 0
                # (fed by the embedding) needs no per-layer conditional.
                drive = x
                for layer in range(self.n_layers):
                    skip = self.w_skip[layer](x) if layer else 0.0
                    mem[layer] = (
                        leak * mem[layer]
                        + self.w_in[layer](drive)
                        + self.w_rec[layer](spk[layer])
                        + skip
                    )
                    spk[layer] = self._spike(mem[layer] - torch.abs(self.threshold))
                    drive = spk[layer]
            if self.cfg.readout == "membrane":
                out = self.out_norm(mem[self.n_layers - 1])
            else:
                out = spk[self.n_layers - 1]
            return out, (mem, spk)

        def advance(self, token_ids: Any, state: Any) -> Any:
            """Feed one token per row; return (logits, new_state)."""
            out, state = self.advance_hidden(token_ids, state)
            return self.head(out), state

        def encode(self, ids: Any) -> Any:
            """Per-token hidden vectors (batch, steps, d_hidden), no head."""
            batch, steps = ids.shape
            state = self.init_state(batch)
            outs = []
            for t in range(steps):
                out, state = self.advance_hidden(ids[:, t], state)
                outs.append(out)
            return torch.stack(outs, dim=1)

        def forward(self, ids: Any) -> Any:
            return self.head(self.encode(ids))

    return _SpikeNet


def resolve_device(torch: Any, wanted: str = "auto") -> str:
    """Pick a torch device: explicit name, or auto (xpu > cuda > cpu).

    ``auto`` prefers the GPU because surrogate-gradient BPTT through time is
    compute-bound; on CPU the same run is 1-2 orders of magnitude slower.
    Only floating-point dtypes the device supports are used — consumer Intel
    Arc cards have no FP64, so nothing here ever creates double tensors.

    Resolution lives in ``core.system.config.compute_device`` so GARDEN, the
    multimodal encoders and this trainer cannot drift apart (``cuda`` is not
    the same question as "is there an accelerator?" — an Intel Arc answers
    ``xpu``).  Signature kept for existing callers.
    """
    from core.system.config.compute_device import resolve_torch_device

    return resolve_torch_device(wanted, torch_module=torch)


def _kd_extra(kd: Any, rows: Sequence[int], box: List[Any]) -> Any:
    """Adapt ``kd(hidden, rows)`` into the ``extra(hidden)`` the loss expects.

    Reading the term back out through ``box`` lets ``train_on`` report the
    distillation objective separately from the hard-label one.
    """

    def extra(hidden: Any) -> Any:
        term = kd(hidden, rows)
        if term is not None:
            box.append(term)
        return term

    return extra


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
        return encode_ids(self.vocab, prompt, answer, self.config.max_len)

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

    def _ss_inputs(self, ids: Any, mask: Any, p: float) -> Any:
        """Scheduled-sampling inputs (one-step variant, Ghosh et al. 2016).

        Positions in the answer region carry the model's own teacher-forced
        prediction instead of the gold token, with probability ``p``; the loss
        is still scored against the untouched gold sequence (``targets`` in
        :meth:`loss`). Prompt positions are never replaced, so every sample
        still starts from the real question.

        Why: round 2 measured response_tf 23% teacher-forced but exact 0
        free-running — the model never trains on its own outputs, so a single
        wrong token derails the rest of the answer. One extra no-grad forward
        per batch buys training conditions that match greedy decoding.
        """
        torch = self.torch
        if p <= 0.0:
            return ids
        with torch.no_grad():
            # pred[t] is the model's guess for ids[t + 1]
            pred = self.net(ids)[:, :-1, :].argmax(dim=-1)
        guess = torch.full_like(ids, self.vocab.pad_id)
        guess[:, 1:] = pred  # input position t carries the model's guess for ids[t]
        choose = mask & (torch.rand(mask.shape, device=mask.device) < p)
        return torch.where(choose, guess, ids)

    def loss(
        self,
        ids: Any,
        mask: Any,
        weights: Any = None,
        targets: Any = None,
        extra: Any = None,
    ) -> Any:
        """Cross-entropy on masked positions, plus an optional soft-target term.

        ``extra(hidden)`` is called with the *same* shifted hidden states the
        hard-label term uses, so distillation adds a head pass over the
        distilled positions and nothing else — no second forward, no second
        encoding. It returns a scalar tensor (or ``None`` to contribute
        nothing), already scaled by the caller's weight.
        """
        torch = self.torch
        # The head is d_hidden x vocab: at 10^8 parameters it is >90% of the
        # per-token compute and of the activation memory, and it is needed only
        # where a target exists. Applying it to the selected positions is the
        # same arithmetic as computing (batch, steps, vocab) and masking.
        hidden = self.net.encode(ids)[:, :-1, :]
        gold = ids if targets is None else targets
        targets = gold[:, 1:]
        target_mask = mask[:, 1:]
        flat_mask = target_mask.reshape(-1)
        if int(flat_mask.sum()) == 0:
            return hidden.sum() * 0.0
        flat_hidden = hidden.reshape(-1, hidden.shape[-1])[flat_mask]
        flat_targets = targets.reshape(-1)[flat_mask]
        per_tok = torch.nn.functional.cross_entropy(
            self.net.head(flat_hidden), flat_targets, reduction="none"
        )
        if weights is None:
            base = per_tok.mean()
        else:
            w = weights[:, 1:].reshape(-1)[flat_mask]
            # Weighted *mean*, not sum: the scale stays comparable to an
            # unweighted run, so a tail weight never silently rescales the
            # learning rate.
            base = (per_tok * w).sum() / w.sum().clamp(min=1e-6)
        if extra is None:
            return base
        term = extra(hidden)
        return base if term is None else base + term

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
                # Vectorised: the old inner loop read one element per position,
                # i.e. four device→host syncs per token (a 7k-row split became
                # millions of syncs and minutes of wall time). Counting a slice
                # is the same arithmetic with four syncs per *row*.
                ok = (pred == target) & keep
                for i, cut in enumerate(cuts):
                    # token index = pos + 1; the row's last token is its eos.
                    # A marker-free answer has cut == eos, so its range is empty.
                    row_keep = int(keep[i].sum())
                    row_ok = int(ok[i].sum())
                    if cut >= len(rows[i]) - 1:
                        resp_hit += row_ok
                        resp_tot += row_keep
                        continue
                    lo = max(0, cut - 1)
                    hi = min(keep.shape[1], len(rows[i]) - 1)
                    tail_keep = int(keep[i, lo:hi].sum())
                    tail_ok = int(ok[i, lo:hi].sum())
                    tail_tot += tail_keep
                    tail_hit += tail_ok
                    resp_tot += row_keep - tail_keep
                    resp_hit += row_ok - tail_ok
        if was_training:
            self.net.train()
        return {
            "response_tf": round(resp_hit / max(1, resp_tot), 4),
            "tail_tf": round(tail_hit / max(1, tail_tot), 4),
            "response_tokens": resp_tot,
            "tail_tokens": tail_tot,
        }

    # -- dynamics -----------------------------------------------------------
    def dynamics(self, pairs: Sequence[Tuple[str, str]], n: int = 8) -> Dict[str, Any]:
        """Measure what the stack is actually doing on real rows.

        A spiking stack fails in three recognisable ways, and loss alone cannot
        tell them apart: it can be **dead** (no layer fires, nothing propagates),
        **saturated** (every unit fires every step, the rate carries no token),
        or **alive**. The decisive feature is the pre-activation mass near the
        threshold: that is the only region where the surrogate gradient is
        non-zero, so a layer with 44% firing but nothing near threshold is firing
        and learning nothing. This measures the forward pass only — no training,
        no grader — so it is cheap enough to print every run and compare runs.
        """
        torch = self.torch
        net = self.net
        was_training = net.training
        net.eval()
        captured: List[Tuple[Any, Any]] = []
        original = net._spike

        def spy(x: Any) -> Any:
            out = original(x)
            captured.append((x.detach(), out.detach()))
            return out

        net._spike = spy
        try:
            ids, _mask, _cuts = self.make_batch(list(pairs[:n]))
            with torch.no_grad():
                net(ids.to(self.device))
        finally:
            net._spike = original
            if was_training:
                net.train()
        layers = int(net.n_layers)
        steps = len(captured) // max(1, layers)
        out: Dict[str, Any] = {
            "rows": len(pairs[:n]),
            "layers": layers,
            # detach: these are parameters, and converting a requires_grad
            # tensor to a scalar warns (nothing here trains, but a noisy
            # warning in every run hides the numbers people should read).
            "beta": round(float(torch.sigmoid(net.beta.detach())), 4),
            "threshold": round(abs(float(net.threshold.detach())), 4),
            "per_layer": [],
        }
        for layer in range(layers):
            pre = torch.stack([captured[t * layers + layer][0] for t in range(steps)])
            spk = torch.stack([captured[t * layers + layer][1] for t in range(steps)])
            # the surrogate is sigmoid(5x): its derivative is 5*s*(1-s), i.e.
            # 1.25 at x=0, 0.33 at |x|=1 and 0.09 at |x|=2. Outside roughly +-2
            # the layer fires but receives almost no gradient.
            near = float((pre.abs() < 0.1).float().mean())
            sensitive = float((pre.abs() < 2.0).float().mean())
            out["per_layer"].append(
                {
                    "layer": layer,
                    "spike_rate": round(float(spk.mean()), 4),
                    "token_variance": round(float(spk.var(0).mean()), 6),
                    "near_threshold": round(near, 4),
                    "sensitive": round(sensitive, 4),
                    "mem_abs_mean": round(float(pre.abs().mean()), 4),
                }
            )
        rates = [row["spike_rate"] for row in out["per_layer"]]
        sensitive_fracs = [row["sensitive"] for row in out["per_layer"]]
        if min(rates) < 0.01 or max(rates) > 0.99:
            out["verdict"] = "dead-or-saturated"
        elif min(sensitive_fracs) < 0.01:
            out["verdict"] = "firing-without-gradient"
        else:
            out["verdict"] = "alive"
        return out

    # -- structure control ---------------------------------------------------
    def spectral_radius(self, weight: Any, iters: int = 100, tol: float = 1e-4) -> float:
        """Largest |eigenvalue| of one recurrent matrix, by power iteration.

        Iterates to convergence (relative 1e-4, max ``iters``) rather than a
        fixed count: a truncated estimate *under*-reads the radius, and the
        projection then leaves the matrix slightly above its cap — measured as
        1.20 on a matrix that was supposed to be capped at 1.0 with 12 sweeps.
        """
        torch = self.torch
        with torch.no_grad():
            v = torch.randn(weight.shape[1], device=weight.device)
            v = v / (v.norm() + 1e-12)
            prev, n = 0.0, 0.0
            for _ in range(iters):
                v = weight @ v
                n = float(v.norm())
                if n == 0.0:
                    return 0.0
                v = v / n
                if prev and abs(n - prev) <= tol * n:
                    break
                prev = n
        return n

    def _project_structure(self) -> None:
        """Hold the recurrent stack inside the band where it can hold state.

        Three free quantities can each buy a lower loss without learning the
        task: theta (silence the stack), beta (forget faster) and w_rec's gain
        (wire-through instead of integrate). Theta is bounded in ``theta_max``;
        this applies the other two, after the optimiser step, as projections:

        - ``leak_floor`` floors sigmoid(beta), so the memory horizon
          1/(1-beta) cannot shrink without bound.
        - ``gain_cap`` rescales any w_rec whose spectral radius exceeds the cap.
          >1 is the point where a perturbation grows per step and the threshold
          clip becomes the only bound.

        Projections rather than reparameterisation, for the same reason as
        theta: forward() is untouched, and checkpoints written with the bounds
        off load and run bit-identically.
        """
        torch = self.torch
        theta_max = float(getattr(self.config, "theta_max", 0.0) or 0.0)
        leak_floor = float(getattr(self.config, "leak_floor", 0.0) or 0.0)
        gain_cap = float(getattr(self.config, "gain_cap", 0.0) or 0.0)
        with torch.no_grad():
            if theta_max > 0.0 and hasattr(self.net, "threshold"):
                self.net.threshold.data.clamp_(0.0, theta_max)
            if leak_floor > 0.0 and hasattr(self.net, "beta"):
                lo = math.log(leak_floor / (1.0 - leak_floor))
                self.net.beta.data.clamp_(min=lo)
            if gain_cap > 0.0:
                for layer in getattr(self.net, "w_rec", []):
                    weight = layer.weight
                    radius = self.spectral_radius(weight)
                    if radius > gain_cap:
                        weight.mul_(gain_cap / radius)

    # -- training -----------------------------------------------------------
    def _batch_loss(
        self,
        chunk: Sequence[Tuple[str, str]],
        tail_weight: float,
        p_ss: float,
        extra: Any = None,
    ) -> Any:
        """Loss for one batch, weighted/scheduled-sampling only when requested.

        Kept out of ``train_on`` so the epoch loop reads as one story; the
        plain path (no tail weight, no scheduled sampling) is the common one
        and stays the cheap one.
        """
        if tail_weight == 1.0 and p_ss == 0.0:
            ids, mask, _ = self.make_batch(chunk)
            return self.loss(ids, mask, extra=extra)
        ids, mask, _, weights = self.make_batch_weighted(chunk, tail_weight)
        if p_ss > 0.0:
            return self.loss(
                self._ss_inputs(ids, mask, p_ss), mask, weights, targets=ids, extra=extra
            )
        return self.loss(ids, mask, weights, extra=extra)

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
        ss_final: float = 0.0,
        lr_at: Any = None,
        guard: bool = True,
        diverge_factor: float = 3.0,
        min_lr: float = 1e-5,
        should_stop: Any = None,
        kd: Any = None,
    ) -> List[Dict[str, float]]:
        """Train on ``pairs``.

        ``ss_final`` is the scheduled-sampling ceiling (0.0 = off, the
        teacher-forced behaviour): the mixing probability ramps linearly from
        ~0 to ``ss_final`` across the epochs, so early epochs learn the
        mapping from gold context and late epochs practise on the model's own
        predictions — the regime greedy decoding will actually run in.

        ``guard`` is the stability rule, and it exists because a run without it
        lost nineteen good epochs to a twentieth (2026-11-04, loss 1.04 -> 7.02
        at unchanged lr). Under the guard an epoch is allowed to oscillate: it
        may get worse and come back. What it may not do is run away. A
        non-finite epoch, or one more than ``diverge_factor`` times the best
        epoch so far, restores the best finite weights, halves the learning rate
        (floored at ``min_lr``) and continues. So "how do I train this" stops
        needing an answer: any lr either learns, oscillates, or steps itself
        down, but the checkpoint on disk is always a finite model that trained.

        History rows carry the evidence: ``lr`` actually used, ``skipped``
        non-finite batches, and ``rolled_back``. ``lr_at(epoch)`` overrides the
        base rate per epoch (schedules live in the caller); ``should_stop()`` is
        polled between epochs so validation can end a run early.

        ``kd(hidden, rows)`` adds a soft-target term to each batch. ``rows`` are
        indices into ``pairs`` (the same indices the shuffle produced), because
        a distillation target belongs to a corpus row, not to a batch slot.
        """
        torch = self.torch
        torch.manual_seed(seed)
        opt = torch.optim.Adam(self.net.parameters(), lr=lr)
        history: List[Dict[str, float]] = []
        best_loss = float("inf")
        best_state: Optional[Dict[str, Any]] = None
        lr_scale = 1.0
        order = list(range(len(pairs)))
        for epoch in range(epochs):
            epoch_lr = max(min_lr, (lr_at(epoch) if lr_at is not None else lr) * lr_scale)
            if should_stop is not None and should_stop():
                history.append(
                    {
                        "epoch": epoch,
                        "loss": float("nan"),
                        "lr": round(epoch_lr, 8),
                        "stopped": True,
                    }
                )
                break
            for group in opt.param_groups:
                group["lr"] = epoch_lr
            torch.manual_seed(seed + epoch)
            shuffled = order[:]
            import random

            random.Random(seed + epoch).shuffle(shuffled)
            p_ss = ss_final * (epoch + 1) / max(1, epochs) if ss_final > 0.0 else 0.0
            total = 0.0
            steps = 0
            skipped = 0
            kd_total = 0.0
            kd_steps = 0
            for start in range(0, len(shuffled), batch_size):
                batch_rows = shuffled[start : start + batch_size]
                chunk = [pairs[i] for i in batch_rows]
                opt.zero_grad()
                extra = None
                kd_box: List[Any] = []
                if kd is not None:
                    extra = _kd_extra(kd, batch_rows, kd_box)

                loss = self._batch_loss(chunk, tail_weight, p_ss, extra=extra)
                if not bool(torch.isfinite(loss)):
                    # one bad batch must not poison the weights for the epochs
                    # that follow: drop the step instead of stepping into NaN
                    opt.zero_grad(set_to_none=True)
                    skipped += 1
                    continue
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.net.parameters(), 1.0)
                opt.step()
                self._project_structure()
                total += float(loss.detach())
                steps += 1
                if kd_box:
                    kd_total += float(kd_box[0].detach())
                    kd_steps += 1
            row: Dict[str, Any] = {
                "epoch": epoch,
                "loss": total / max(1, steps) if steps else float("nan"),
                "lr": round(epoch_lr, 8),
                "skipped": skipped,
                "rolled_back": False,
            }
            if kd is not None:
                # Reported separately: a rising total loss with a falling KD
                # term means the soft target is pulling against the hard label,
                # and that is invisible in a single number.
                row["kd_loss"] = round(kd_total / kd_steps, 6) if kd_steps else None
                row["kd_batches"] = kd_steps
            if guard:
                best_loss, best_state, lr_scale, opt = self._guard_epoch(
                    row, best_loss, best_state, steps, lr, lr_scale, min_lr, diverge_factor, opt
                )
            history.append(row)
            if log is not None:
                log(row)
            if on_epoch is not None:
                on_epoch(row)
        return history

    def _guard_epoch(
        self,
        row: Dict[str, Any],
        best_loss: float,
        best_state: Optional[Dict[str, Any]],
        steps: int,
        lr: float,
        lr_scale: float,
        min_lr: float,
        diverge_factor: float,
        opt: Any,
    ) -> "tuple[float, Optional[Dict[str, Any]], float, Any]":
        """Roll back a diverged epoch; returns (best_loss, best_state, lr_scale, opt).

        The stability rule in ``train_on``: an epoch may oscillate, but a
        non-finite loss or one above ``diverge_factor`` times the best restores
        the best finite weights, halves the learning rate and rebuilds the
        optimiser (a stale Adam state would step the restored weights with the
        diverged ones' momentum). The caller keeps the history row.
        """
        loss_now = float(row["loss"])
        finite = math.isfinite(loss_now)
        runaway = finite and math.isfinite(best_loss) and loss_now > diverge_factor * best_loss
        if not finite or runaway:
            row["rolled_back"] = True
            row["rollback_from"] = None if not finite else round(loss_now, 4)
            if best_state is not None:
                self.net.load_state_dict(best_state)
            lr_scale = max(min_lr / max(1e-12, lr), lr_scale * 0.5)
            opt = self.torch.optim.Adam(self.net.parameters(), lr=max(min_lr, lr * lr_scale))
            row["loss"] = best_loss if math.isfinite(best_loss) else loss_now
            return best_loss, best_state, lr_scale, opt
        best_loss = min(best_loss, loss_now)
        if steps:
            best_state = {k: v.detach().clone() for k, v in self.net.state_dict().items()}
        return best_loss, best_state, lr_scale, opt

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
        was_training = self.net.training
        self.net.eval()
        out: List[int] = []
        try:
            with torch.no_grad():
                state = self.net.init_state(1, device=self.device)
                logits = None
                for token in ids:
                    logits, state = self.net.advance(
                        torch.tensor([[token]], dtype=torch.long, device=self.device), state
                    )
                if logits is None:  # empty prompt: start from the zero state
                    logits, state = self.net.advance(
                        torch.tensor([[self.vocab.bos_id]], dtype=torch.long, device=self.device),
                        state,
                    )
                row = logits[0]
                for _ in range(max_new):
                    if temperature <= 0:
                        nxt = int(torch.argmax(row).item())
                    else:
                        probs = torch.softmax(row / temperature, dim=-1)
                        nxt = int(torch.multinomial(probs, 1).item())
                    if nxt == self.vocab.eos_id:
                        break
                    if nxt == self.vocab.pad_id or nxt == self.vocab.bos_id:
                        break
                    out.append(nxt)
                    # one forward per new token instead of one per prefix token
                    logits, state = self.net.advance(
                        torch.tensor([[nxt]], dtype=torch.long, device=self.device), state
                    )
                    row = logits[0]
        finally:
            # leave the model in the mode the caller had: flipping to train()
            # unconditionally put an eval-time call site back into train mode.
            if was_training:
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
