# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [A] [L2]
# =============================================================================
"""Core adapters for the single-core contract: one recurrence, two step functions.

Two arms live here, and they differ **only** in the recurrence:

* :class:`GRUCore` — the P1 first arm (non-linear, learned recurrence);
* :class:`SSMCore` — the P3 arm (diagonal linear recurrence, time enters as
  decay, so the semigroup holds by construction rather than by training).

Everything a core needs in order to obey the contract (state object, weights
hash, checkpointing) is in :class:`StatefulCore`, so a new arm cannot quietly
grow its own state format. Neither arm is wired into production: they exist to
make the contract measurable. The rule they have to satisfy (contract R1) is
that ``ai_step`` and ``al_step`` share one set of weights and one state object:

* both mutate the ``h`` tensor inside the same :class:`~ai.core.core_state.CoreState`
  (``ai_step`` feeds token embeddings into the recurrence, ``al_step`` advances
  the same recurrence by elapsed time with no external token);

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
from typing import Any, Dict, Optional, Tuple

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

    def init_state(
        self,
        batch_size: int,
        *,
        user_id: str = "",
        session_id: str = "",
        born_at: Optional[str] = None,
    ) -> CoreState:
        """A new persistent state; only for a new session (contract R5)."""
        torch = self._torch
        return CoreState.create(
            model_kind=self.model_kind,
            weights_hash=self.weights_hash(),
            user_id=user_id,
            session_id=session_id,
            tensors={"h": torch.zeros(batch_size, self.hidden, device=self.device)},
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


__all__ = ["GRUCore", "SSMCore", "StatefulCore"]
