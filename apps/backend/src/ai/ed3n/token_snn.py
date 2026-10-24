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

* **tokens** — a character vocabulary built from the training data (CJK
  characters are individual tokens; ASCII words are characters too, which is
  enough for the sizes used here and needs no third-party tokenizer),
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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PAD, BOS, EOS, UNK = "<pad>", "<bos>", "<eos>", "<unk>"
SPECIALS = (PAD, BOS, EOS, UNK)


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


def _make_net(torch: Any) -> Any:
    """Define the nn.Module lazily so importing this file stays torch-free."""
    nn = torch.nn

    class _SpikeNet(nn.Module):
        def __init__(self, vocab_size: int, cfg: TokenConfig) -> None:
            super().__init__()
            self.cfg = cfg
            self.n_layers = max(1, int(cfg.layers))
            if cfg.readout not in ("spike", "membrane"):
                raise ValueError(f"readout must be 'spike' or 'membrane', got {cfg.readout!r}")
            self.embed = nn.Embedding(vocab_size, cfg.d_emb, padding_idx=0)
            self.w_in = nn.ModuleList(
                nn.Linear(cfg.d_emb if i == 0 else cfg.d_hidden, cfg.d_hidden)
                for i in range(self.n_layers)
            )
            self.w_rec = nn.ModuleList(
                nn.Linear(cfg.d_hidden, cfg.d_hidden, bias=False) for _ in range(self.n_layers)
            )
            self.head = nn.Linear(cfg.d_hidden, vocab_size)
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
                logits.append(self.head(out))
            return torch.stack(logits, dim=1)

    return _SpikeNet


class TokenSNN:
    """Small token-level SNN language model (torch required at build time)."""

    def __init__(self, vocab: CharVocab, config: Optional[TokenConfig] = None) -> None:
        import torch  # lazy: keeps torch out of import time

        self.torch = torch
        self.vocab = vocab
        self.config = config or TokenConfig()
        net_cls = _make_net(torch)
        self.net = net_cls(len(vocab), self.config)

    # -- batching -----------------------------------------------------------
    def encode_pair(self, prompt: str, answer: str) -> Tuple[List[int], int]:
        """Return ids and the index where the answer starts."""
        prompt = prompt.strip()
        answer = answer.strip()
        budget = self.config.max_len
        ids = [self.vocab.bos_id] + self.vocab.encode(prompt)
        prompt_len = len(ids)
        ids.append(self.vocab.stoi["\n"])
        prompt_len += 1  # first answer character
        ids.extend(self.vocab.encode(answer))
        ids.append(self.vocab.eos_id)
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
        return ids, prompt_len

    def make_batch(self, pairs: Sequence[Tuple[str, str]]) -> Tuple[Any, Any, Any]:
        torch = self.torch
        rows = []
        starts = []
        for prompt, answer in pairs:
            ids, start = self.encode_pair(prompt, answer)
            rows.append(ids)
            starts.append(start)
        width = max(len(r) for r in rows)
        ids_t = torch.full((len(rows), width), self.vocab.pad_id, dtype=torch.long)
        mask = torch.zeros((len(rows), width), dtype=torch.bool)
        for i, (row, start) in enumerate(zip(rows, starts)):
            ids_t[i, : len(row)] = torch.tensor(row, dtype=torch.long)
            mask[i, start : len(row)] = True
        return ids_t, mask, starts

    def loss(self, ids: Any, mask: Any) -> Any:
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
        return torch.nn.functional.cross_entropy(flat_logits[flat_mask], flat_targets[flat_mask])

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
                ids, mask, _ = self.make_batch(chunk)
                opt.zero_grad()
                loss = self.loss(ids, mask)
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
            cur = torch.tensor([ids], dtype=torch.long)
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
                cur = torch.cat([cur, torch.tensor([[nxt]], dtype=torch.long)], dim=1)
        self.net.train()
        return self.vocab.decode(out)

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
    def load(cls, path: Path | str, map_location: str = "cpu") -> "TokenSNN":
        import torch

        payload = torch.load(str(path), map_location=map_location, weights_only=False)
        vocab = CharVocab.from_dict(payload["vocab"])
        model = cls(vocab, TokenConfig(**payload["config"]))
        model.net.load_state_dict(payload["state"])
        model.net.eval()
        return model


__all__ = ["CharVocab", "TokenConfig", "TokenSNN", "SPECIALS", "PAD", "BOS", "EOS", "UNK"]
