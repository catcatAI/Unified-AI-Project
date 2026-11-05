# =============================================================================
# ANGELA-MATRIX: [L2] [β] [B] [L1]
# =============================================================================
"""Single source of truth for picking a torch device.

Why this module exists
----------------------
``torch.cuda.is_available()`` is not the same question as "is there an
accelerator?".  This machine ships an Intel Arc GPU driven by ``torch``'s XPU
backend: ``cuda.is_available()`` is ``False`` while ``torch.xpu.is_available()``
is ``True``.  Code that hardcoded ``"cuda"`` therefore declared a device it
could never use, and ``TensorSNNCore`` stored that string without ever moving a
tensor — "GPU configured, CPU executed", with no error to notice.

Every component that needs a torch device resolves it here, so there is exactly
one answer to the question and one place to change it.

Notes
-----
* ``auto`` prefers ``xpu`` > ``cuda`` > ``cpu`` (the order token-SNN has used
  since it was written; a machine exposing both is rare and either choice is a
  GPU).
* Explicit requests are honoured only when the backend is actually available;
  otherwise the call degrades to ``cpu`` *and logs why* instead of failing at
  the first tensor op.
* Torch is imported lazily: importing this module never pulls torch into a
  process that does not use it.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def device_available(name: str, torch_module: Optional[Any] = None) -> bool:
    """Return True when ``name`` can actually be used as a torch device."""
    name = (name or "cpu").strip().lower()
    if name == "cpu":
        return True
    torch = torch_module
    if torch is None:
        try:
            import torch as _torch  # lazy: keep torch out of import time
        except Exception:
            return False
        torch = _torch
    try:
        if name == "cuda":
            return bool(torch.cuda.is_available())
        if name == "xpu":
            return bool(hasattr(torch, "xpu") and torch.xpu.is_available())
        if name == "mps":
            backends = getattr(torch, "backends", None)
            mps = getattr(backends, "mps", None) if backends is not None else None
            return bool(mps is not None and mps.is_available())
    except Exception:  # pragma: no cover — probing must never raise
        logger.debug("device probe failed for %r", name, exc_info=True)
        return False
    # Unknown names are not trusted: constructing ``torch.device("whatever")``
    # succeeds without proving the backend exists, and the failure would only
    # surface later at the first tensor op.
    return False


def move_batch_to_device(batch: Any, device: str) -> Any:
    """Move a dict / transformers ``BatchEncoding`` of tensors to ``device``.

    A model moved to an accelerator and inputs left on the host fail with a
    device-mismatch error, so every encoder moves both.  CPU is a no-op and
    anything unexpected leaves the batch untouched (the model then runs on its
    own device, which is where the error would surface anyway).
    """
    if device == "cpu" or batch is None:
        return batch
    try:
        return {k: (v.to(device) if hasattr(v, "to") else v) for k, v in batch.items()}
    except Exception:  # pragma: no cover — defensive only
        logger.debug("could not move input batch to %s", device, exc_info=True)
        return batch


def resolve_torch_device(wanted: str = "auto", torch_module: Optional[Any] = None) -> str:
    """Pick a torch device: explicit name when usable, else ``xpu``>``cuda``>``cpu``.

    ``wanted`` may be ``"auto"``/``""``/``None`` for automatic selection.  An
    explicit device that is not available degrades to ``cpu`` with a warning —
    callers must never build tensors on a device the runtime cannot use.
    """
    wanted = (wanted or "auto").strip().lower()
    if wanted not in ("auto", ""):
        if device_available(wanted, torch_module):
            return wanted
        logger.warning("Requested torch device %r is unavailable; falling back to cpu", wanted)
        return "cpu"
    for candidate in ("xpu", "cuda"):
        if device_available(candidate, torch_module):
            return candidate
    return "cpu"


def feature_compute_enabled(feature: str, default: bool = True) -> bool:
    """Whether ``compute.<feature>.mode`` allows acceleration for this feature.

    ``off`` means "force CPU-only" (see ``configs/system/compute.default.yaml``),
    so a feature whose config says ``off`` must not silently run on an
    accelerator just because one is available.  If the config cannot be read we
    fail open: the feature still works, it is simply not pinned to CPU.
    """
    try:
        from core.system.config.magic_numbers import compute_bool

        return bool(compute_bool(feature, default))
    except Exception:  # pragma: no cover — config import must never disable a feature
        logger.debug("could not read compute.%s mode", feature, exc_info=True)
        return True


def resolve_feature_device(
    feature: str,
    wanted: str = "auto",
    torch_module: Optional[Any] = None,
) -> str:
    """Device for a named compute feature: ``off`` → cpu, else the resolver.

    Use this instead of ``resolve_torch_device`` inside a feature that has its
    own ``compute.<feature>.mode`` entry, so the setting is actually honoured
    (the declared-vs-used bug this module exists to stop).
    """
    if not feature_compute_enabled(feature):
        logger.info("compute.%s is off; running on cpu", feature)
        return "cpu"
    return resolve_torch_device(wanted, torch_module=torch_module)
