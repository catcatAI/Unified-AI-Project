# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L2]
# =============================================================================
"""Layered conversation context for multi-role play (Phase 0).

A role sees ``shared_base`` (filtered by per-message visibility) followed by its
own ``private_overlay``. Nothing here copies the shared list — it is held by
reference, so the primary role's growth is visible to every reader, which is the
whole point of a shared base.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Set

DEFAULT_TOKEN_BUDGET = 4096


def _as_ids(value: Any) -> Optional[Set[str]]:
    """Normalise a message's ``visible_to`` marker to a set (None = public)."""
    if value is None:
        return None
    if isinstance(value, str):
        return {value}
    return {str(v) for v in value}


@dataclass
class RoleContext:
    """One role's view of the conversation."""

    role_id: str
    shared_base: List[Dict[str, Any]] = field(default_factory=list)
    private_overlay: List[Dict[str, Any]] = field(default_factory=list)
    visible_to: Set[str] = field(default_factory=set)
    token_budget: int = DEFAULT_TOKEN_BUDGET

    def __post_init__(self) -> None:
        self.role_id = (self.role_id or "").strip()
        if not self.role_id:
            raise ValueError("role_id must be a non-empty string")
        if self.token_budget <= 0:
            raise ValueError("token_budget must be positive")
        self.visible_to = set(self.visible_to) or {self.role_id}

    def add_shared(
        self, message: Dict[str, Any], visible_to: Optional[Iterable[str]] = None
    ) -> Dict[str, Any]:
        """Append to the shared base; ``visible_to`` omits → visible to everyone."""
        msg = dict(message)
        ids = _as_ids(visible_to)
        if ids is not None:
            msg["visible_to"] = ids
        self.shared_base.append(msg)
        return msg

    def add_private(
        self, message: Dict[str, Any], visible_to: Optional[Iterable[str]] = None
    ) -> Dict[str, Any]:
        """Append to this role's overlay, optionally widening who may read it."""
        msg = dict(message)
        self.private_overlay.append(msg)
        if visible_to is not None:
            self.visible_to |= _as_ids(visible_to) or set()
        return msg

    def merged_messages(self, viewer: Optional[str] = None) -> List[Dict[str, Any]]:
        """Shared base (visibility-filtered) + private overlay for ``viewer``."""
        viewer_id = viewer or self.role_id
        merged: List[Dict[str, Any]] = []
        for msg in self.shared_base:
            allowed = _as_ids(msg.get("visible_to"))
            if allowed is None or viewer_id in allowed:
                merged.append(msg)
        if viewer_id == self.role_id or viewer_id in self.visible_to:
            merged.extend(self.private_overlay)
        return merged

    def estimate_tokens(
        self, messages: Optional[List[Dict[str, Any]]] = None, chars_per_token: float = 4.0
    ) -> int:
        """Cheap heuristic (~4 chars/token); good enough for budget routing."""
        if chars_per_token <= 0:
            raise ValueError("chars_per_token must be positive")
        items = self.merged_messages() if messages is None else messages
        chars = sum(len(str(m.get("content", ""))) for m in items)
        return int(chars / chars_per_token)

    def is_over_budget(self, viewer: Optional[str] = None) -> bool:
        return self.estimate_tokens(self.merged_messages(viewer)) > self.token_budget
