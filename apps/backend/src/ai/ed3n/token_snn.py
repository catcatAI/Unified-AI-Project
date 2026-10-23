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
    beta: float = 0.9
    threshold: float = 0.5
    surrogate_alpha: float = 5.0
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
            self.embed = nn.Embedding(vocab_size, cfg.d_emb, padding_idx=0)
            self.w_in = nn.Linear(cfg.d_emb, cfg.d_hidden)
            self.w_rec = nn.Linear(cfg.d_hidden, cfg.d_hidden, bias=False)
            self.head = nn.Linear(cfg.d_hidden, vocab_size)
            self.beta = nn.Parameter(torch.tensor(cfg.beta))
            self.threshold = nn.Parameter(torch.tensor(cfg.threshold))

        def _spike(self, x: Any) -> Any:
            # Surrogate gradient: hard forward value, fast-sigmoid derivative.
            hard = (x >= 0).to(x.dtype)
            soft = torch.sigmoid(self.cfg.surrogate_alpha * x)
            return hard.detach() + soft - soft.detach()

        def forward(self, ids: Any) -> Any:
            batch, steps = ids.shape
            v = self.embed.weight.new_zeros((batch, self.cfg.d_hidden))
            s = self.embed.weight.new_zeros((batch, self.cfg.d_hidden))
            logits = []
            for t in range(steps):
                x = self.embed(ids[:, t])
                v = torch.sigmoid(self.beta) * v + self.w_in(x) + self.w_rec(s)
                s = self._spike(v - torch.abs(self.threshold))
                logits.append(self.head(s))
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

    # -- training -----------------------------------------------------------
    def train_on(
        self,
        pairs: Sequence[Tuple[str, str]],
        epochs: int = 1,
        batch_size: int = 32,
        lr: float = 3e-3,
        seed: int = 0,
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
