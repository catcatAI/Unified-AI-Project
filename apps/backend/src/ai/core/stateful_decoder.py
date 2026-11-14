# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# =============================================================================
"""Core adapters for the single-core contract: one recurrence, two step functions.

Five arms live here, and they differ **only** in what the state is:

* :class:`GRUCore` — the P1 first arm (non-linear, learned recurrence);
* :class:`SSMCore` — the P3 arm (diagonal linear recurrence, time enters as
  decay, so the semigroup holds by construction rather than by training);
* :class:`SlotMemoryCore` — the round-7 arm (round 6's design requirement): the
  same recurrence plus a key-addressed store, so the state can hold two
  bindings instead of one vector's worth of "the most recent value".
* :class:`TurnStoreCore` — the §55 arm: the GRU recurrence plus a store written
  once per turn and read only into the output head, so credit does not have to
  travel back through every token (the measured obstacle in §49.16-§54).
* :class:`TokenCacheCore` — the §59 arm: the same store, but written once per
  **token**, because §58 showed the per-turn write averages the roster's eight
  value -> name pairs into one vector before any readout can address them.

Everything a core needs in order to obey the contract (state object, weights
hash, checkpointing) is in :class:`StatefulCore`, so a new arm cannot quietly
grow its own state format. None of these arms is wired into production: they
exist to make the contract measurable. The rule they have to satisfy (contract
R1) is that ``ai_step`` and ``al_step`` share one set of weights and one state
object:

* both mutate the state tensors inside the same
  :class:`~ai.core.core_state.CoreState` (``ai_step`` feeds token embeddings
  into the recurrence, ``al_step`` advances the same recurrence by elapsed time
  with no external token);

There is deliberately no second trunk, no second model, and no clock module
that "knows" the time on the model's behalf: if ``al_step`` is not called, the
elapsed time simply does not exist for the model. That is what makes T5 (skip
``al_step``) a real falsifier instead of a formality.

torch is imported lazily so that ``ai.core.core_state`` and the rest of the
package stay importable without the ``ml`` extra (the base install has numpy
only). Constructing either arm without torch raises a clear error.

Limits (do not over-read a passing run):
* one synthetic task, small model, CPU; nothing here is a language capability;
* the weights are random unless trained by the caller;
* ``state_version``/``ticks`` are recorded for provenance, not used as inputs.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from ai.core.core_state import CoreState, CoreStateInvalid
from ai.core.core_step import DEFAULT_MAX_CHUNK_S


def _require_torch() -> Any:
    try:
        import torch  # noqa: F401  (lazy: base install has no torch)
    except ImportError as exc:  # pragma: no cover - depends on the install tier
        raise RuntimeError(
            "GRUCore needs torch; install the optional 'ml' extra "
            "(pip install -e 'apps/backend[ml]')"
        ) from exc
    return torch


class StatefulCore:
    """State, hashing and checkpoint plumbing shared by every core arm.

    R1 says one substrate: one weights hash and one state object. Keeping these
    methods here means a second arm cannot grow a second state format or a
    second hash — ``export_state``, ``attach_state`` and ``weights_hash`` are
    the contract's, not the recurrence's.

    A subclass supplies :meth:`modules`, :meth:`_modules_by_name`, its own
    ``ai_step``/``al_step``, and (only if it has non-module parameters) an
    override of :meth:`extra_parameters`.
    """

    model_kind = "core"
    token_count: int
    hidden: int
    emb: int
    chunk_seconds: float
    device: str
    _torch: Any
    _weights_hash: Optional[str] = None
    _parameter_count: Optional[int] = None

    def modules(self) -> Tuple[Any, ...]:
        raise NotImplementedError

    def _modules_by_name(self) -> Tuple[Tuple[str, Any], ...]:
        raise NotImplementedError

    def extra_parameters(self) -> Tuple[Tuple[str, Any], ...]:
        """Parameters that are not inside a module (e.g. an SSM time constant)."""
        return ()

    def parameters(self) -> Any:
        for module in self.modules():
            for parameter in module.parameters():
                yield parameter
        for _name, parameter in self.extra_parameters():
            yield parameter

    def parameter_count(self) -> int:
        cached = self._parameter_count
        if cached is None:
            cached = int(sum(p.numel() for p in self.parameters()))
            self._parameter_count = cached
        return cached

    def to(self, device: str) -> "StatefulCore":
        for module in self.modules():
            module.to(device)
        for _name, parameter in self.extra_parameters():
            parameter.data = parameter.data.to(device)
        self.device = device
        self._weights_hash = None
        return self

    def train(self, mode: bool = True) -> "StatefulCore":
        for module in self.modules():
            module.train(mode)
        return self

    def eval(self) -> "StatefulCore":
        return self.train(False)

    def weights_hash(self) -> str:
        """Hash of the actual tensors; changes if a single weight changes."""
        cached = self._weights_hash
        if cached is None:
            digest = hashlib.sha256()
            for name, parameter in sorted(self._named_parameters()):
                array = parameter.detach().to("cpu").contiguous().numpy()
                digest.update(name.encode("utf-8"))
                digest.update(str(array.dtype).encode("ascii"))
                digest.update(repr(array.shape).encode("ascii"))
                digest.update(array.tobytes())
            cached = "sha256:" + digest.hexdigest()
            self._weights_hash = cached
        return cached

    def _named_parameters(self) -> Any:
        for module_name, module in self._modules_by_name():
            yield from module.named_parameters(prefix=module_name)
        for name, parameter in self.extra_parameters():
            yield name, parameter

    def invalidate_hash(self) -> None:
        """Call after an optimiser step (the hash must never be stale)."""
        self._weights_hash = None

    # -- state --------------------------------------------------------------

    def state_tensors(self, batch_size: int) -> Dict[str, Any]:
        """The tensors a fresh state starts with.

        One tensor is the default (``h``, the working memory of every arm so
        far). An arm whose capacity is *addressed* rather than recurrent
        overrides this, so a second storage tensor cannot be smuggled in by a
        caller: the schema of the state stays the core's business.
        """
        torch = self._torch
        return {"h": torch.zeros(batch_size, self.hidden, device=self.device)}

    def init_state(
        self,
        batch_size: int,
        *,
        user_id: str = "",
        session_id: str = "",
        born_at: Optional[str] = None,
    ) -> CoreState:
        """A new persistent state; only for a new session (contract R5)."""
        return CoreState.create(
            model_kind=self.model_kind,
            weights_hash=self.weights_hash(),
            user_id=user_id,
            session_id=session_id,
            tensors=self.state_tensors(batch_size),
            now=born_at,
        )

    def export_state(self, state: CoreState) -> CoreState:
        """Detached numpy copy for ``CoreState.save`` (no autograd graph)."""
        tensors: Dict[str, np.ndarray] = {}
        for name, value in state.tensors.items():
            array = value
            if hasattr(array, "detach"):
                array = array.detach().to("cpu").numpy()
            tensors[name] = np.array(array, copy=True)
        return CoreState(
            schema_version=state.schema_version,
            model_kind=state.model_kind,
            weights_hash=state.weights_hash,
            user_id=state.user_id,
            session_id=state.session_id,
            born_at=state.born_at,
            last_update=state.last_update,
            ticks=state.ticks,
            last_dt_s=state.last_dt_s,
            state_version=state.state_version,
            tensors=tensors,
        )

    def attach_state(self, state: CoreState) -> CoreState:
        """Turn a loaded (numpy) state back into tensors the cell can consume.

        Refuses a state that was not produced by **these** weights or by this
        arm (contract R1/R5): a ``gru`` state attached to an ``ssm`` core would
        otherwise be accepted silently whenever the hidden size happens to
        match, and the model would answer from a state that never existed for
        it. ``CoreState.load(expected_weights_hash=...)`` guards the file path;
        this guards the in-memory path.
        """
        torch = self._torch
        if state.model_kind != self.model_kind:
            raise CoreStateInvalid(
                f"state is {state.model_kind!r} but this core is {self.model_kind!r}"
            )
        expected = self.weights_hash()
        if state.weights_hash != expected:
            raise CoreStateInvalid(
                "state weights_hash does not match this core's weights "
                f"({state.weights_hash[:19]}… != {expected[:19]}…); "
                "reset the state instead of attaching it"
            )
        tensors: Dict[str, Any] = {}
        for name, value in state.tensors.items():
            if hasattr(value, "detach"):
                tensors[name] = value
            else:
                tensors[name] = torch.as_tensor(
                    np.asarray(value), dtype=torch.float32, device=self.device
                )
        return CoreState(
            schema_version=state.schema_version,
            model_kind=state.model_kind,
            weights_hash=state.weights_hash,
            user_id=state.user_id,
            session_id=state.session_id,
            born_at=state.born_at,
            last_update=state.last_update,
            ticks=state.ticks,
            last_dt_s=state.last_dt_s,
            state_version=state.state_version,
            tensors=tensors,
        )

    def _hidden(self, state: CoreState) -> Any:
        hidden = state.tensors.get("h")
        if hidden is None:
            raise CoreStateInvalid("state has no 'h' tensor")
        if not hasattr(hidden, "detach"):
            raise CoreStateInvalid("state 'h' must be a torch tensor; call attach_state()")
        return hidden

    # -- the decode interface the trainer uses ------------------------------

    def token_logits(self, tensors: Dict[str, Any]) -> Any:
        """Logits for one decoding step from a tensor mapping.

        The trainer decodes from a *snapshot* of the state (one per turn), not
        from the live object, so this takes the tensors directly. A core with a
        store must override it - the store is part of what a step reads.
        """
        raise NotImplementedError(f"{type(self).__name__} has no token_logits()")

    def consume(self, tokens: Any, tensors: Dict[str, Any]) -> Dict[str, Any]:
        """Advance the recurrence by one token and return a new tensor mapping.

        Must not mutate the input mapping: auxiliary losses hold several past
        boundaries alive at once, and a decoder that wrote back would change the
        evidence an earlier boundary is scored on.
        """
        raise NotImplementedError(f"{type(self).__name__} has no consume()")

    def end_turn(self, tensors: Dict[str, Any]) -> Dict[str, Any]:
        """Optional turn-end hook; cores without a store return the state as is."""
        return dict(tensors)

    def cache_write(self, tensors: Dict[str, Any], states: Any, valid: Any) -> Dict[str, Any]:
        """Optional per-token write hook; cores without a token cache ignore it.

        §59 needs the write to happen from the *same* stacked states the turn
        was computed from, so the trainer calls this unconditionally and a core
        without a cache inherits this no-op (rather than the trainer probing for
        the method, which would silently skip a core that renamed it).
        """
        return dict(tensors)

    # -- checkpointing ------------------------------------------------------

    def state_dict(self) -> Dict[str, Any]:
        payload = {
            module_name: module.state_dict() for module_name, module in self._modules_by_name()
        }
        extras = {name: parameter.detach().clone() for name, parameter in self.extra_parameters()}
        if extras:
            payload["__extra__"] = extras
        return payload

    def load_state_dict(self, payload: Dict[str, Any]) -> None:
        for module_name, module in self._modules_by_name():
            module.load_state_dict(payload[module_name])
        extras = payload.get("__extra__", {})
        torch = self._torch
        with torch.no_grad():
            for name, parameter in self.extra_parameters():
                if name in extras:
                    parameter.copy_(extras[name])
        self.invalidate_hash()

    def save_weights(self, path: str) -> None:
        torch = self._torch
        torch.save(
            {"config": self.config(), "state_dict": self.state_dict()},
            path,
        )

    def load_weights(self, path: str, *, strict_config: bool = True) -> "StatefulCore":
        torch = self._torch
        payload = torch.load(path, map_location=self.device, weights_only=True)
        config = payload.get("config", {})
        if strict_config and config:
            expected = self.config()
            for key in ("token_count", "hidden", "emb", "chunk_seconds", "model_kind"):
                if key in config and config[key] != expected[key]:
                    raise CoreStateInvalid(
                        f"checkpoint {key}={config[key]!r} != model {expected[key]!r}"
                    )
        self.load_state_dict(payload["state_dict"])
        return self

    def config(self) -> Dict[str, Any]:
        return {
            "model_kind": self.model_kind,
            "token_count": self.token_count,
            "hidden": self.hidden,
            "emb": self.emb,
            "chunk_seconds": self.chunk_seconds,
            "parameter_count": self.parameter_count(),
        }


class GRUCore(StatefulCore):
    """A single ``GRUCell`` with two entry points and one state.

    Parameters are fixed by the pre-registration in ``CORE_GAP_ANALYSIS.md``
    §37.3: ``d_hidden=64``, ``d_emb=32``, chunk ≤ 60 s. A different size is
    allowed for tests, but a *scored* run must use the registered values — the
    probe script passes them explicitly and records them in its report.
    """

    model_kind = "gru"

    def __init__(
        self,
        token_count: int,
        *,
        hidden: int = 64,
        emb: int = 32,
        chunk_seconds: float = DEFAULT_MAX_CHUNK_S,
        seed: Optional[int] = None,
        device: str = "cpu",
    ) -> None:
        if token_count <= 1:
            raise ValueError("token_count must be > 1")
        if hidden <= 0 or emb <= 0:
            raise ValueError("hidden and emb must be > 0")
        if chunk_seconds <= 0 or not math.isfinite(chunk_seconds):
            raise ValueError("chunk_seconds must be finite and > 0")

        torch = _require_torch()
        self._torch = torch
        self.token_count = token_count
        self.hidden = hidden
        self.emb = emb
        self.chunk_seconds = float(chunk_seconds)
        self.device = device

        if seed is not None:
            torch.manual_seed(seed)

        nn = torch.nn
        self.embedding = nn.Embedding(token_count, emb)
        self.cell = nn.GRUCell(emb, hidden)
        self.dt_proj = nn.Linear(1, emb)
        self.head = nn.Linear(hidden, token_count)
        if device != "cpu":
            self.to(device)

        self._weights_hash: Optional[str] = None
        self._parameter_count: Optional[int] = None

    # -- introspection ------------------------------------------------------

    def modules(self) -> Tuple[Any, ...]:
        """The trainable modules; one optimizer covers all of them."""
        return (self.embedding, self.cell, self.dt_proj, self.head)

    def _modules_by_name(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("embedding", self.embedding),
            ("cell", self.cell),
            ("dt_proj", self.dt_proj),
            ("head", self.head),
        )

    # -- the decode interface the trainer uses ------------------------------

    def token_logits(self, tensors: Dict[str, Any]) -> Any:
        """``head(h)`` - the decode step, bitwise the old ``core.head(current)``."""
        return self.head(tensors["h"])

    def consume(self, tokens: Any, tensors: Dict[str, Any]) -> Dict[str, Any]:
        """``h <- cell(embedding(token), h)``; the store (if any) is untouched."""
        return {**tensors, "h": self.cell(self.embedding(tokens), tensors["h"])}

    # -- the two cycles -----------------------------------------------------

    def ai_step(self, tokens: Any, state: CoreState) -> Tuple[Any, CoreState]:
        """``tokens``: LongTensor ``[B, L]`` → ``(logits [B, L, V], state)``."""
        torch = self._torch
        if tokens.ndim != 2:
            raise ValueError(f"tokens must be [B, L], got shape {tuple(tokens.shape)}")
        hidden = self._hidden(state)
        if tokens.shape[0] != hidden.shape[0]:
            raise ValueError("batch size of tokens and state disagree")

        outputs = []
        for position in range(tokens.shape[1]):
            inputs = self.embedding(tokens[:, position])
            hidden = self.cell(inputs, hidden)
            outputs.append(self.head(hidden))
        logits = torch.stack(outputs, dim=1)

        state.tensors["h"] = hidden
        state.bump()
        return logits, state

    def al_step(self, dt_s: Any, state: CoreState) -> CoreState:
        """Advance the same recurrence by ``dt_s`` without any external token.

        ``dt_s`` is a scalar or a per-sample tensor/list (``[B]``), so a batch
        of sessions with different gaps is still one exact computation:
        each sample gets ``ceil(dt_i / chunk_seconds)`` updates of
        ``dt_i / n_i`` seconds, and the samples that need fewer updates are
        **left untouched** after they finish (no zero-input padding, which
        would change ``h`` for the wrong reason).

        ``dt_s <= 0`` returns the **same** state unchanged (bitwise), which is
        the contract's zero-time identity. ``ticks`` counts chunks, not calls.
        """
        torch = self._torch
        hidden = self._hidden(state)
        batch = int(hidden.shape[0])

        if isinstance(dt_s, (int, float)) and not isinstance(dt_s, bool):
            dt = torch.full((batch,), float(dt_s), dtype=hidden.dtype, device=hidden.device)
        else:
            dt = torch.as_tensor(dt_s, dtype=hidden.dtype, device=hidden.device).reshape(-1)
            if int(dt.shape[0]) != batch:
                raise ValueError(f"dt batch {int(dt.shape[0])} != state batch {batch}")

        if not bool(torch.isfinite(dt).all()):
            raise ValueError("dt must be finite")
        if bool((dt < 0).any()):
            raise ValueError("dt must be >= 0")

        counts = [
            int(math.ceil(float(value) / self.chunk_seconds)) if float(value) > 0.0 else 0
            for value in dt.detach().to("cpu").tolist()
        ]
        max_chunks = max(counts) if counts else 0
        if max_chunks == 0:
            return state

        count_tensor = torch.as_tensor(counts, dtype=torch.int64, device=hidden.device)
        for step in range(max_chunks):
            active = (count_tensor > step).nonzero(as_tuple=False).reshape(-1)
            if int(active.numel()) == 0:
                continue
            chunks = count_tensor[active].to(hidden.dtype)
            feature = (dt[active] / chunks / self.chunk_seconds).unsqueeze(1)
            updated = self.cell(self.dt_proj(feature), hidden[active])
            hidden = hidden.index_copy(0, active, updated)

        state.tensors["h"] = hidden
        state.ticks += max_chunks
        state.last_dt_s = float(dt.detach().max().to("cpu"))
        state.bump()
        return state


class TurnStoreCore(GRUCore):
    """§55 stage T: the same recurrence, plus one write at each turn's end.

    Stage S measured the cost of credit assignment rather than a capacity wall:
    the same 124,611-parameter carrier fits 32 sessions, but only at 1,600
    updates/session, and the 800-session pantry arm was given 20. This arm keeps
    every part of :class:`GRUCore` that the contract pins - ``embedding`` →
    ``cell``, ``dt_proj``, ``al_step``, ``chunk_seconds`` - and adds a
    key-addressed store written **once per turn**, so the answer does not have to
    travel back through every token of every turn.

    The state carries ``h`` ``[B, H]`` and the store ``k`` ``[B, S, D]`` /
    ``v`` ``[B, S, D]``. At a turn's end the controller writes

    * ``a = softmax(scale_w * W_s h)`` - which slot receives this turn;
    * ``g = sigmoid(W_g h)`` - how strongly, starting at bias -2.0;
    * ``slot <- slot * (1 - a g) + a g * W_{k|v} h``.

    Reading is content-addressed: ``r = Σ softmax(scale * W_q h · kᵀ) v`` and the
    output is ``head([h, r])``. Two things are deliberate and each has a measured
    reason in §55.2: the write is per turn, not per token (the moving-average
    window is ``1/s`` tokens, so a ~100-byte turn would erase itself mid-turn),
    and ``r`` enters **only the output head**, never the cell (feeding it back
    made the ablation beat the scored arm in §46.13). ``al_step`` is inherited
    unchanged: time advances the controller and leaves the store alone, because
    slots are content, not a clock.

    ``memory=False`` is the R4 ablation: every parameter is kept, ``r ≡ 0`` and
    no write happens. With L's blocks copied, ``head([h, 0])`` is L's
    ``head(h)``, so the ablation's *function* is the GRU arm's and only its
    random stream differs.
    """

    model_kind = "turnstore"

    def __init__(
        self,
        token_count: int,
        *,
        hidden: int = 64,
        emb: int = 32,
        chunk_seconds: float = DEFAULT_MAX_CHUNK_S,
        seed: Optional[int] = None,
        device: str = "cpu",
        slots: int = 16,
        slot_dim: int = 64,
        value_dim: int = 64,
        memory: bool = True,
    ) -> None:
        if slots <= 0 or slot_dim <= 0 or value_dim <= 0:
            raise ValueError("slots, slot_dim and value_dim must be > 0")
        super().__init__(
            token_count,
            hidden=hidden,
            emb=emb,
            chunk_seconds=chunk_seconds,
            seed=seed,
            device=device,
        )
        torch = self._torch
        nn = torch.nn
        self.slots = int(slots)
        self.slot_dim = int(slot_dim)
        self.value_dim = int(value_dim)
        self.memory = bool(memory)

        self.key_proj = nn.Linear(hidden, self.slot_dim)
        self.value_proj = nn.Linear(hidden, self.value_dim)
        self.query_proj = nn.Linear(hidden, self.slot_dim)
        self.slot_gate = nn.Linear(hidden, self.slots)
        self.write_gate = nn.Linear(hidden, 1)
        # ``head`` sees the controller plus the current read. The ablation keeps
        # the same shape and zeroes the read, so it stays a drop-in for GRUCore.
        self.head = nn.Linear(hidden + self.value_dim, token_count)
        # Start by writing slowly and learn when to commit (§46.4b's prior).
        nn.init.constant_(self.write_gate.bias, -2.0)
        self.log_read_scale = nn.Parameter(torch.tensor(math.log(4.0)))
        self.log_write_scale = nn.Parameter(torch.tensor(math.log(4.0)))
        if device != "cpu":
            self.to(device)

        self._weights_hash = None
        self._parameter_count = None

    # -- introspection ------------------------------------------------------

    def modules(self) -> Tuple[Any, ...]:
        return (
            self.embedding,
            self.cell,
            self.dt_proj,
            self.key_proj,
            self.value_proj,
            self.query_proj,
            self.slot_gate,
            self.write_gate,
            self.head,
        )

    def _modules_by_name(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("embedding", self.embedding),
            ("cell", self.cell),
            ("dt_proj", self.dt_proj),
            ("key_proj", self.key_proj),
            ("value_proj", self.value_proj),
            ("query_proj", self.query_proj),
            ("slot_gate", self.slot_gate),
            ("write_gate", self.write_gate),
            ("head", self.head),
        )

    def extra_parameters(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("log_read_scale", self.log_read_scale),
            ("log_write_scale", self.log_write_scale),
        )

    def config(self) -> Dict[str, Any]:
        payload = super().config()
        payload.update(
            {
                "slots": self.slots,
                "slot_dim": self.slot_dim,
                "value_dim": self.value_dim,
                "memory": self.memory,
            }
        )
        return payload

    # -- state --------------------------------------------------------------

    def state_tensors(self, batch_size: int) -> Dict[str, Any]:
        torch = self._torch
        return {
            "h": torch.zeros(batch_size, self.hidden, device=self.device),
            "k": torch.zeros(batch_size, self.slots, self.slot_dim, device=self.device),
            "v": torch.zeros(batch_size, self.slots, self.value_dim, device=self.device),
        }

    def _store(self, tensors: Dict[str, Any]) -> Tuple[Any, Any]:
        keys = tensors.get("k")
        values = tensors.get("v")
        if keys is None or values is None:
            raise CoreStateInvalid("state has no 'k'/'v' tensors")
        return keys, values

    # -- the one step interface the trainer uses ----------------------------

    def read_vector(self, tensors: Dict[str, Any]) -> Any:
        """The content the current ``h`` addresses (all zeros when ``memory`` is off)."""
        torch = self._torch
        hidden = tensors["h"]
        if not self.memory:
            return torch.zeros(
                hidden.shape[0],
                self.value_dim,
                dtype=hidden.dtype,
                device=hidden.device,
            )
        keys, values = self._store(tensors)
        query = self.query_proj(hidden)
        scores = torch.bmm(keys, query.unsqueeze(2)).squeeze(2)
        weights = torch.softmax(torch.exp(self.log_read_scale) * scores, dim=-1)
        return torch.bmm(weights.unsqueeze(1), values).squeeze(1)

    def token_logits(self, tensors: Dict[str, Any]) -> Any:
        """Logits for one step, from ``[h, read]`` - the store never enters ``h``."""
        torch = self._torch
        return self.head(torch.cat([tensors["h"], self.read_vector(tensors)], dim=-1))

    def consume(self, tokens: Any, tensors: Dict[str, Any]) -> Dict[str, Any]:
        """Advance ``h`` by one token, leaving the store untouched."""
        return {**tensors, "h": self.cell(self.embedding(tokens), tensors["h"])}

    def end_turn(self, tensors: Dict[str, Any]) -> Dict[str, Any]:
        """One write per turn: address, strength, then a moving average."""
        if not self.memory:
            return dict(tensors)
        torch = self._torch
        hidden = tensors["h"]
        keys, values = self._store(tensors)
        weights = torch.softmax(torch.exp(self.log_write_scale) * self.slot_gate(hidden), dim=-1)
        strength = torch.sigmoid(self.write_gate(hidden))
        share = (strength * weights).unsqueeze(-1)
        new_keys = self.key_proj(hidden).unsqueeze(1)
        new_values = self.value_proj(hidden).unsqueeze(1)
        return {
            **tensors,
            "k": keys * (1.0 - share) + share * new_keys,
            "v": values * (1.0 - share) + share * new_values,
        }

    # -- the two cycles -----------------------------------------------------

    def ai_step(self, tokens: Any, state: CoreState) -> Tuple[Any, CoreState]:
        """``tokens``: LongTensor ``[B, L]`` → ``(logits [B, L, V], state)``.

        Identical to :meth:`GRUCore.ai_step` except that every step's logits see
        the current store. No write happens here; a turn-end write is explicit
        (:meth:`end_turn`) so a caller cannot accidentally write mid-turn.
        """
        torch = self._torch
        if tokens.ndim != 2:
            raise ValueError(f"tokens must be [B, L], got shape {tuple(tokens.shape)}")
        tensors = dict(state.tensors)
        if tokens.shape[0] != tensors["h"].shape[0]:
            raise ValueError("batch size of tokens and state disagree")

        outputs = []
        for position in range(tokens.shape[1]):
            tensors = self.consume(tokens[:, position], tensors)
            outputs.append(self.token_logits(tensors))
        logits = torch.stack(outputs, dim=1)

        for name, value in tensors.items():
            state.tensors[name] = value
        state.bump()
        return logits, state


class TokenCacheCore(GRUCore):
    """§59 stage B: the same recurrence, plus one addressable slot per token.

    §58 measured the binding this arm is built for. The probe could fit the
    training states (in-sample 0.9725) but the held-out states decoded at 0.1100
    against a chance of 0.1591: :class:`TurnStoreCore` memorises the sessions it
    was trained on and carries nothing transferable. The reason is visible in
    the task: the roster turn states eight value -> name pairs in one turn, and
    a per-turn write averages all eight into a single vector before any readout
    can address them (its in-roster rate was 0.61 / 0.535, i.e. barely above the
    content-free 0.5457).

    So the write granularity is the one variable. Everything the contract pins
    stays: ``embedding`` -> ``cell``, ``dt_proj``, ``al_step``, ``chunk_seconds``,
    ``h``. The state gains a bounded token cache:

    * ``ck [B, S, D]``, ``cv [B, S, D]``, ``mask [B, S]`` alongside ``h``;
    * a token's entry is ``W_k h_t`` / ``W_v h_t`` appended at position ``t``,
      truncated to the **first** ``S`` tokens (not a ring): the roster is turn
      2-3 of 11, so keeping the head of the session means the pairs cannot be
      evicted by later filler;
    * padding never enters: ``mask`` is the sample's real length, so a padded
      position is addressed out with a large negative score;
    * reading is ``softmax(scale * W_q h . ck^T) . cv`` and enters **only the
      output head** - the same rule §55.2 measured (feeding a read back into the
      cell made the ablation beat the scored arm in §46.13);
    * ``memory=False`` keeps every parameter, writes nothing and returns a zero
      read, so the ablation is a drop-in for the parameter-matched control.

    Writes are functional (``cat`` then slice), never in-place: several
    boundaries stay alive at once for the auxiliary loss, and an in-place store
    update would change the evidence an earlier boundary is scored on.
    """

    model_kind = "tokencache"

    def __init__(
        self,
        token_count: int,
        *,
        hidden: int = 64,
        emb: int = 32,
        chunk_seconds: float = DEFAULT_MAX_CHUNK_S,
        seed: Optional[int] = None,
        device: str = "cpu",
        slots: int = 1024,
        slot_dim: int = 64,
        value_dim: int = 64,
        memory: bool = True,
    ) -> None:
        if slots <= 0 or slot_dim <= 0 or value_dim <= 0:
            raise ValueError("slots, slot_dim and value_dim must be > 0")
        super().__init__(
            token_count,
            hidden=hidden,
            emb=emb,
            chunk_seconds=chunk_seconds,
            seed=seed,
            device=device,
        )
        torch = self._torch
        nn = torch.nn
        self.slots = int(slots)
        self.slot_dim = int(slot_dim)
        self.value_dim = int(value_dim)
        self.memory = bool(memory)

        self.key_proj = nn.Linear(hidden, self.slot_dim)
        self.value_proj = nn.Linear(hidden, self.value_dim)
        self.query_proj = nn.Linear(hidden, self.slot_dim)
        self.head = nn.Linear(hidden + self.value_dim, token_count)
        self.log_read_scale = nn.Parameter(torch.tensor(math.log(4.0)))
        if device != "cpu":
            self.to(device)

        self._weights_hash = None
        self._parameter_count = None

    # -- introspection ------------------------------------------------------

    def modules(self) -> Tuple[Any, ...]:
        return (
            self.embedding,
            self.cell,
            self.dt_proj,
            self.key_proj,
            self.value_proj,
            self.query_proj,
            self.head,
        )

    def _modules_by_name(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("embedding", self.embedding),
            ("cell", self.cell),
            ("dt_proj", self.dt_proj),
            ("key_proj", self.key_proj),
            ("value_proj", self.value_proj),
            ("query_proj", self.query_proj),
            ("head", self.head),
        )

    def extra_parameters(self) -> Tuple[Tuple[str, Any], ...]:
        return (("log_read_scale", self.log_read_scale),)

    def config(self) -> Dict[str, Any]:
        payload = super().config()
        payload.update(
            {
                "slots": self.slots,
                "slot_dim": self.slot_dim,
                "value_dim": self.value_dim,
                "memory": self.memory,
            }
        )
        return payload

    # -- state --------------------------------------------------------------

    def state_tensors(self, batch_size: int) -> Dict[str, Any]:
        """``h`` plus an *empty* cache; it grows by ``cat`` as tokens arrive."""
        torch = self._torch
        return {
            "h": torch.zeros(batch_size, self.hidden, device=self.device),
            "ck": torch.zeros(batch_size, 0, self.slot_dim, device=self.device),
            "cv": torch.zeros(batch_size, 0, self.value_dim, device=self.device),
            "mask": torch.zeros(batch_size, 0, device=self.device),
        }

    def cache_write(self, tensors: Dict[str, Any], states: Any, valid: Any) -> Dict[str, Any]:
        """Append one entry per token: ``states`` ``[B, T, H]``, ``valid`` ``[B, T]``.

        The slice to ``slots`` keeps the **first** ``S`` tokens of the session;
        a session longer than that loses its tail, and §59.4's B4 records how
        much. Padding is carried in ``mask`` so it is never read, not dropped
        from the tensor (positions must stay aligned with the token order).
        """
        if not self.memory:
            return dict(tensors)
        torch = self._torch
        keys = torch.cat([tensors["ck"], self.key_proj(states)], dim=1)[:, : self.slots]
        values = torch.cat([tensors["cv"], self.value_proj(states)], dim=1)[:, : self.slots]
        mask = torch.cat([tensors["mask"], valid.to(states.dtype)], dim=1)[:, : self.slots]
        return {**tensors, "ck": keys, "cv": values, "mask": mask}

    # -- the decode interface -----------------------------------------------

    def read_vector(self, tensors: Dict[str, Any]) -> Any:
        """Content-addressed read over the token cache (all zeros when off)."""
        torch = self._torch
        hidden = tensors["h"]
        keys = tensors.get("ck")
        if not self.memory or keys is None or int(keys.shape[1]) == 0:
            return torch.zeros(
                hidden.shape[0],
                self.value_dim,
                dtype=hidden.dtype,
                device=hidden.device,
            )
        query = self.query_proj(hidden)
        scores = torch.bmm(keys, query.unsqueeze(2)).squeeze(2)
        scores = scores * torch.exp(self.log_read_scale)
        scores = scores.masked_fill(tensors["mask"] <= 0, -1.0e9)
        weights = torch.softmax(scores, dim=-1)
        return torch.bmm(weights.unsqueeze(1), tensors["cv"]).squeeze(1)

    def token_logits(self, tensors: Dict[str, Any]) -> Any:
        """Logits from ``[h, read]`` - the cache never enters ``h``."""
        torch = self._torch
        return self.head(torch.cat([tensors["h"], self.read_vector(tensors)], dim=-1))

    # -- the two cycles -----------------------------------------------------

    def ai_step(self, tokens: Any, state: CoreState) -> Tuple[Any, CoreState]:
        """``tokens``: LongTensor ``[B, L]`` → ``(logits [B, L, V], state)``.

        Each token is consumed, written to the cache, then read: the first
        step's logits therefore see the first token (never an empty cache,
        which would make the read a zero vector for the wrong reason).
        """
        torch = self._torch
        if tokens.ndim != 2:
            raise ValueError(f"tokens must be [B, L], got shape {tuple(tokens.shape)}")
        tensors = dict(state.tensors)
        batch = int(tokens.shape[0])
        if batch != tensors["h"].shape[0]:
            raise ValueError("batch size of tokens and state disagree")

        outputs = []
        ones = torch.ones((batch, 1), dtype=tensors["h"].dtype, device=tensors["h"].device)
        for position in range(tokens.shape[1]):
            tensors = self.consume(tokens[:, position], tensors)
            tensors = self.cache_write(tensors, tensors["h"].unsqueeze(1), ones)
            outputs.append(self.token_logits(tensors))
        logits = torch.stack(outputs, dim=1)

        for name, value in tensors.items():
            state.tensors[name] = value
        state.bump()
        return logits, state


class SSMCore(StatefulCore):
    """Diagonal linear SSM: time is the recurrence, not an input feature.

    State update (contract §4; P3 arm):

    * ``al_step(dt)``: ``h <- h * exp(-dt / tau)``, per hidden dimension;
    * ``ai_step(tokens)``: ``h <- h + W_in E[token]``, then a linear readout.

    ``tau`` is per dimension and log-spaced at initialisation over
    ``[tau_min, tau_max]`` (default 20–2000 s), so the state carries both slow
    channels (content survives a 400 s gap) and fast ones (the ratio between
    channels carries elapsed time). It is learned from there; the range is
    written down before the run, not fitted to it.

    The semigroup ``al_step(dt1) ; al_step(dt2) == al_step(dt1+dt2)`` holds
    **exactly** (a product of exponentials). §40 therefore treats it as an
    architectural property, not as evidence that training learned continuity:
    the capability checks are still T1/T3/T5.

    Chunking is the shared one from :func:`ai.core.core_step.chunk_dt`, so
    ``ticks`` means the same thing as in :class:`GRUCore`.
    """

    model_kind = "ssm"

    def __init__(
        self,
        token_count: int,
        *,
        hidden: int = 64,
        emb: int = 32,
        chunk_seconds: float = DEFAULT_MAX_CHUNK_S,
        seed: Optional[int] = None,
        device: str = "cpu",
        tau_min: float = 20.0,
        tau_max: float = 2000.0,
    ) -> None:
        if token_count <= 1:
            raise ValueError("token_count must be > 1")
        if hidden <= 0 or emb <= 0:
            raise ValueError("hidden and emb must be > 0")
        if chunk_seconds <= 0 or not math.isfinite(chunk_seconds):
            raise ValueError("chunk_seconds must be finite and > 0")
        if tau_min <= 0 or not math.isfinite(tau_min):
            raise ValueError("tau_min must be finite and > 0")
        if tau_max <= tau_min or not math.isfinite(tau_max):
            raise ValueError("tau_max must be finite and > tau_min")

        torch = _require_torch()
        self._torch = torch
        self.token_count = token_count
        self.hidden = hidden
        self.emb = emb
        self.chunk_seconds = float(chunk_seconds)
        self.device = device
        self.tau_min = float(tau_min)
        self.tau_max = float(tau_max)

        if seed is not None:
            torch.manual_seed(seed)

        nn = torch.nn
        self.embedding = nn.Embedding(token_count, emb)
        self.in_proj = nn.Linear(emb, hidden, bias=False)
        self.head = nn.Linear(hidden, token_count)

        # Log-spaced time constants: one fast end (chunk scale) and one slow end
        # (session scale). Initialised explicitly so it does not depend on the
        # seed, and stored as a log so tau stays positive under any step.
        taus = torch.exp(torch.linspace(math.log(self.tau_min), math.log(self.tau_max), hidden))
        self.tau_log = nn.Parameter(torch.log(taus))
        if device != "cpu":
            self.to(device)

        self._weights_hash: Optional[str] = None
        self._parameter_count: Optional[int] = None

    # -- introspection ------------------------------------------------------

    def modules(self) -> Tuple[Any, ...]:
        return (self.embedding, self.in_proj, self.head)

    def _modules_by_name(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("embedding", self.embedding),
            ("in_proj", self.in_proj),
            ("head", self.head),
        )

    def extra_parameters(self) -> Tuple[Tuple[str, Any], ...]:
        return (("tau_log", self.tau_log),)

    def tau(self) -> Any:
        """Positive per-dimension time constants in seconds (shape ``[hidden]``)."""
        return self._torch.exp(self.tau_log)

    # -- the two cycles -----------------------------------------------------

    def ai_step(self, tokens: Any, state: CoreState) -> Tuple[Any, CoreState]:
        """``tokens``: LongTensor ``[B, L]`` → ``(logits [B, L, V], state)``."""
        torch = self._torch
        if tokens.ndim != 2:
            raise ValueError(f"tokens must be [B, L], got shape {tuple(tokens.shape)}")
        hidden = self._hidden(state)
        if tokens.shape[0] != hidden.shape[0]:
            raise ValueError("batch size of tokens and state disagree")

        outputs = []
        for position in range(tokens.shape[1]):
            hidden = hidden + self.in_proj(self.embedding(tokens[:, position]))
            outputs.append(self.head(hidden))
        logits = torch.stack(outputs, dim=1)

        state.tensors["h"] = hidden
        state.bump()
        return logits, state

    def al_step(self, dt_s: Any, state: CoreState) -> CoreState:
        """Advance the same state by ``dt_s`` of pure decay (no tokens).

        ``dt_s`` accepts a scalar or a ``[B]`` tensor, like :class:`GRUCore`.
        Each sample is decayed once per chunk with ``exp(-dt_i / n_i / tau)``,
        whose product is ``exp(-dt_i / tau)`` — the semigroup identity is exact
        up to float rounding, not an approximation the model has to learn.
        """
        torch = self._torch
        hidden = self._hidden(state)
        batch = int(hidden.shape[0])

        if isinstance(dt_s, (int, float)) and not isinstance(dt_s, bool):
            dt = torch.full((batch,), float(dt_s), dtype=hidden.dtype, device=hidden.device)
        else:
            dt = torch.as_tensor(dt_s, dtype=hidden.dtype, device=hidden.device).reshape(-1)
            if int(dt.shape[0]) != batch:
                raise ValueError(f"dt batch {int(dt.shape[0])} != state batch {batch}")

        if not bool(torch.isfinite(dt).all()):
            raise ValueError("dt must be finite")
        if bool((dt < 0).any()):
            raise ValueError("dt must be >= 0")

        counts = [
            int(math.ceil(float(value) / self.chunk_seconds)) if float(value) > 0.0 else 0
            for value in dt.detach().to("cpu").tolist()
        ]
        max_chunks = max(counts) if counts else 0
        if max_chunks == 0:
            return state

        tau = self.tau()
        count_tensor = torch.as_tensor(counts, dtype=torch.int64, device=hidden.device)
        for step in range(max_chunks):
            active = (count_tensor > step).nonzero(as_tuple=False).reshape(-1)
            if int(active.numel()) == 0:
                continue
            chunks = count_tensor[active].to(hidden.dtype)
            chunk_seconds = dt[active] / chunks
            decay = torch.exp(-chunk_seconds.unsqueeze(1) / tau)
            hidden = hidden.index_copy(0, active, hidden[active] * decay)

        state.tensors["h"] = hidden
        state.ticks += max_chunks
        state.last_dt_s = float(dt.detach().max().to("cpu"))
        state.bump()
        return state

    def config(self) -> Dict[str, Any]:
        payload = super().config()
        payload.update({"tau_min": self.tau_min, "tau_max": self.tau_max})
        return payload


class SlotMemoryCore(StatefulCore):
    """A key-addressed store: the state is a set of slots, not one vector.

    Round 6 (§45) closed with a design requirement rather than a score: the
    state held *one* value because ``h`` is one vector that the recurrence
    overwrites, and a linear readout could not recover either taught value
    (0.28-0.41 characters, chance 0.027). Two bindings need an address, not a
    bigger buffer.

    This arm changes the **structure** and nothing else. The working memory is
    still a :class:`torch.nn.GRUCell` ``h``; alongside it the state carries
    ``slot_k`` ``[B, K, D]`` and ``slot_v`` ``[B, K, Dv]``. At every token the
    controller (``h``) does three things with learned projections:

    * **address** - ``q = W_q h`` and ``a = softmax(scale * q·slot_k / sqrt(D))``;
      the read ``r = Σ_k a_k slot_v[k]`` is what the output head sees;
    * **select** - ``w = softmax(scale_w * W_w h)`` says which slot this token
      belongs to;
    * **write** - ``slot <- slot * (1 - g w) + (g w) * new`` with
      ``g = sigmoid(W_g h)`` and ``new`` from ``W_k h`` / ``W_v h``.

    Read happens *before* the write at the same token, so the question reads
    what was taught and only then may (if ``g`` allows) add itself. The read is
    also an input to the **next** step of the controller, not only to the output
    head: without that, the store could influence one decoded character and an
    eight-character value could never survive the eight steps that spell it. Nothing
    here is a dictionary bolted on the side: the write distribution, the
    strength, the key and the value are all functions of ``h`` under the same
    weights, and ``al_step`` mutates the same object. The ablation
    (``memory=False``) keeps every parameter and every other operation and sets
    ``r ≡ 0`` with no writes, so the contribution of the store is measured
    rather than assumed (contract R4).

    ``al_step`` advances ``h`` exactly as :class:`GRUCore` does and leaves the
    slots alone: addresses are content, and time acts on the controller that
    reads them. That is a design choice, written here before the run, and it is
    why T5 (skip ``al_step``) is *not* used as evidence in this round.
    """

    model_kind = "slots"

    def __init__(
        self,
        token_count: int,
        *,
        hidden: int = 64,
        emb: int = 32,
        chunk_seconds: float = DEFAULT_MAX_CHUNK_S,
        seed: Optional[int] = None,
        device: str = "cpu",
        slots: int = 4,
        slot_dim: int = 64,
        value_dim: int = 64,
        memory: bool = True,
    ) -> None:
        if token_count <= 1:
            raise ValueError("token_count must be > 1")
        if hidden <= 0 or emb <= 0:
            raise ValueError("hidden and emb must be > 0")
        if slots <= 0 or slot_dim <= 0 or value_dim <= 0:
            raise ValueError("slots, slot_dim and value_dim must be > 0")
        if chunk_seconds <= 0 or not math.isfinite(chunk_seconds):
            raise ValueError("chunk_seconds must be finite and > 0")

        torch = _require_torch()
        self._torch = torch
        self.token_count = token_count
        self.hidden = hidden
        self.emb = emb
        self.chunk_seconds = float(chunk_seconds)
        self.device = device
        self.slots = int(slots)
        self.slot_dim = int(slot_dim)
        self.value_dim = int(value_dim)
        self.memory = bool(memory)

        if seed is not None:
            torch.manual_seed(seed)

        nn = torch.nn
        self.embedding = nn.Embedding(token_count, emb)
        self.cell = nn.GRUCell(emb + self.value_dim, hidden)
        self.dt_proj = nn.Linear(1, emb)
        self.key_proj = nn.Linear(hidden, self.slot_dim)
        self.value_proj = nn.Linear(hidden, self.value_dim)
        self.query_proj = nn.Linear(hidden, self.slot_dim)
        self.write_logits = nn.Linear(hidden, self.slots)
        self.write_gate = nn.Linear(hidden, 1)
        self.head = nn.Linear(hidden + self.value_dim, token_count)
        # A write is an exponential moving average: ``slot <- slot(1-s) + s*new``.
        # With the default bias the initial rate is sigmoid(0) = 0.5 per token, so
        # the store forgets in ~2 tokens - measured on the dev seed, the read was
        # identical for both questions because turn 1 had been erased. A memory
        # controller should start by writing slowly and learn when to commit;
        # bias -2.0 gives 0.12 per token (~68% of a nine-token turn retained, both
        # turns still present). This is an initialisation prior, declared before
        # the registered run, not a fitted value: what to write, where, and how to
        # address it are still learned.
        nn.init.constant_(self.write_gate.bias, -2.0)
        # Sharpness of addressing and of slot selection. Stored as a log so it
        # stays positive under any step; initialised to 4.0 (a soft but not
        # uniform choice) rather than fitted to the task.
        self.log_read_scale = nn.Parameter(torch.tensor(math.log(4.0)))
        self.log_write_scale = nn.Parameter(torch.tensor(math.log(4.0)))
        if device != "cpu":
            self.to(device)

        self._weights_hash: Optional[str] = None
        self._parameter_count: Optional[int] = None

    # -- introspection ------------------------------------------------------

    def modules(self) -> Tuple[Any, ...]:
        """The trainable modules; one optimizer covers all of them."""
        return (
            self.embedding,
            self.cell,
            self.dt_proj,
            self.key_proj,
            self.value_proj,
            self.query_proj,
            self.write_logits,
            self.write_gate,
            self.head,
        )

    def _modules_by_name(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("embedding", self.embedding),
            ("cell", self.cell),
            ("dt_proj", self.dt_proj),
            ("key_proj", self.key_proj),
            ("value_proj", self.value_proj),
            ("query_proj", self.query_proj),
            ("write_logits", self.write_logits),
            ("write_gate", self.write_gate),
            ("head", self.head),
        )

    def extra_parameters(self) -> Tuple[Tuple[str, Any], ...]:
        return (
            ("log_read_scale", self.log_read_scale),
            ("log_write_scale", self.log_write_scale),
        )

    # -- state --------------------------------------------------------------

    def state_tensors(self, batch_size: int) -> Dict[str, Any]:
        torch = self._torch
        return {
            "h": torch.zeros(batch_size, self.hidden, device=self.device),
            "slot_k": torch.zeros(batch_size, self.slots, self.slot_dim, device=self.device),
            "slot_v": torch.zeros(batch_size, self.slots, self.value_dim, device=self.device),
        }

    def _slots(self, state: CoreState) -> Tuple[Any, Any]:
        keys = state.tensors.get("slot_k")
        values = state.tensors.get("slot_v")
        if keys is None or values is None:
            raise CoreStateInvalid("state has no 'slot_k'/'slot_v' tensors")
        if not hasattr(keys, "detach") or not hasattr(values, "detach"):
            raise CoreStateInvalid("slots must be torch tensors; call attach_state()")
        return keys, values

    # -- the memory ---------------------------------------------------------

    def _address(self, hidden: Any, keys: Any, values: Any) -> Tuple[Any, Any]:
        """``(addressing weights, read)`` - the one place addressing happens.

        Returning the weights too is what lets the diagnostic report the slot
        that *produced* the answer instead of the one that would be read after
        the same token's write.
        """
        torch = self._torch
        query = self.query_proj(hidden)
        scores = torch.bmm(keys, query.unsqueeze(2)).squeeze(2)
        scores = scores / math.sqrt(float(self.slot_dim))
        weights = torch.softmax(torch.exp(self.log_read_scale) * scores, dim=-1)
        return weights, torch.bmm(weights.unsqueeze(1), values).squeeze(1)

    def read_vector_tensors(self, hidden: Any, keys: Any, values: Any) -> Any:
        """Content-addressed read: ``softmax(scale * q·slot_k) · slot_v``.

        Takes the tensors directly so ``ai_step`` can read the pre-write store
        without constructing a second ``CoreState`` per token.
        """
        return self._address(hidden, keys, values)[1]

    def read_vector(self, state: CoreState) -> Any:
        """The content the current ``h`` addresses, read-only (no write).

        Public so a probe can ask "is the answer in the store?" separately from
        "did the decoder say it?" - the distinction §45 needed and could not
        make with a single vector.
        """
        hidden = self._hidden(state)
        keys, values = self._slots(state)
        return self.read_vector_tensors(hidden, keys, values)

    def attention(self, state: CoreState) -> Any:
        """The addressing distribution (diagnostic: which slot is being read)."""
        hidden = self._hidden(state)
        keys, values = self._slots(state)
        return self._address(hidden, keys, values)[0]

    # -- the two cycles -----------------------------------------------------

    def ai_step(self, tokens: Any, state: CoreState, *, return_trace: bool = False) -> Any:
        """``tokens``: LongTensor ``[B, L]`` → ``(logits [B, L, V], state)``.

        ``return_trace=True`` adds ``{"read": [B, L, Dv], "attention": [B, L, K]}``
        so a diagnostic can look at what a given token addressed *at the time*,
        before that token's own write. Tracing never changes the state.
        """
        torch = self._torch
        if tokens.ndim != 2:
            raise ValueError(f"tokens must be [B, L], got shape {tuple(tokens.shape)}")
        hidden = self._hidden(state)
        keys, values = self._slots(state)
        if tokens.shape[0] != hidden.shape[0]:
            raise ValueError("batch size of tokens and state disagree")

        write_scale = torch.exp(self.log_write_scale)
        context = torch.zeros(
            hidden.shape[0], self.value_dim, dtype=hidden.dtype, device=hidden.device
        )
        outputs = []
        trace_read: List[Any] = []
        trace_attention: List[Any] = []
        for position in range(tokens.shape[1]):
            inputs = self.embedding(tokens[:, position])
            hidden = self.cell(torch.cat([inputs, context], dim=-1), hidden)

            read = torch.zeros(
                hidden.shape[0], self.value_dim, dtype=hidden.dtype, device=hidden.device
            )
            if self.memory:
                # Read first: the question sees what was taught, not itself.
                weights, read = self._address(hidden, keys, values)
                if return_trace:
                    trace_attention.append(weights)
            if return_trace:
                trace_read.append(read)
            outputs.append(self.head(torch.cat([hidden, read], dim=-1)))
            # What was read becomes part of the next step's input, so the value
            # can survive the tokens that spell it out.
            context = read

            if self.memory:
                # Write with the *same* projections the read uses, so the key
                # that a turn stores and the key a question asks for live in one
                # space (that is the whole point of "addressed").
                weight = torch.softmax(write_scale * self.write_logits(hidden), dim=-1)
                strength = torch.sigmoid(self.write_gate(hidden))
                share = (strength * weight).unsqueeze(-1)
                new_keys = self.key_proj(hidden).unsqueeze(1)
                new_values = self.value_proj(hidden).unsqueeze(1)
                keys = keys * (1.0 - share) + share * new_keys
                values = values * (1.0 - share) + share * new_values

        logits = torch.stack(outputs, dim=1)
        state.tensors["h"] = hidden
        state.tensors["slot_k"] = keys
        state.tensors["slot_v"] = values
        state.bump()
        if not return_trace:
            return logits, state
        trace = {
            "read": torch.stack(trace_read, dim=1),
            "attention": torch.stack(trace_attention, dim=1) if trace_attention else None,
        }
        return logits, state, trace

    def al_step(self, dt_s: Any, state: CoreState) -> CoreState:
        """Advance the controller by ``dt_s``; the slots are content, not time.

        Identical arithmetic to :class:`GRUCore` (this is the same recurrence
        with the same ``dt_proj``), so a run can be compared with §44/§45
        without a second time model entering as a confound.
        """
        torch = self._torch
        hidden = self._hidden(state)
        batch = int(hidden.shape[0])

        if isinstance(dt_s, (int, float)) and not isinstance(dt_s, bool):
            dt = torch.full((batch,), float(dt_s), dtype=hidden.dtype, device=hidden.device)
        else:
            dt = torch.as_tensor(dt_s, dtype=hidden.dtype, device=hidden.device).reshape(-1)
            if int(dt.shape[0]) != batch:
                raise ValueError(f"dt batch {int(dt.shape[0])} != state batch {batch}")

        if not bool(torch.isfinite(dt).all()):
            raise ValueError("dt must be finite")
        if bool((dt < 0).any()):
            raise ValueError("dt must be >= 0")

        counts = [
            int(math.ceil(float(value) / self.chunk_seconds)) if float(value) > 0.0 else 0
            for value in dt.detach().to("cpu").tolist()
        ]
        max_chunks = max(counts) if counts else 0
        if max_chunks == 0:
            return state

        count_tensor = torch.as_tensor(counts, dtype=torch.int64, device=hidden.device)
        for step in range(max_chunks):
            active = (count_tensor > step).nonzero(as_tuple=False).reshape(-1)
            if int(active.numel()) == 0:
                continue
            chunks = count_tensor[active].to(hidden.dtype)
            feature = (dt[active] / chunks / self.chunk_seconds).unsqueeze(1)
            # No token and nothing read during the gap: the controller input is
            # the time feature plus a zero read.
            inputs = torch.cat(
                [
                    self.dt_proj(feature),
                    torch.zeros(
                        int(active.numel()),
                        self.value_dim,
                        dtype=hidden.dtype,
                        device=hidden.device,
                    ),
                ],
                dim=-1,
            )
            updated = self.cell(inputs, hidden[active])
            hidden = hidden.index_copy(0, active, updated)

        state.tensors["h"] = hidden
        state.ticks += max_chunks
        state.last_dt_s = float(dt.detach().max().to("cpu"))
        state.bump()
        return state

    def config(self) -> Dict[str, Any]:
        payload = super().config()
        payload.update(
            {
                "slots": self.slots,
                "slot_dim": self.slot_dim,
                "value_dim": self.value_dim,
                "memory": self.memory,
            }
        )
        return payload


__all__ = ["GRUCore", "SSMCore", "SlotMemoryCore", "StatefulCore"]
