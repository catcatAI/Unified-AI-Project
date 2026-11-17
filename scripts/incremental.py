#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# LAYER: learning
# =============================================================================
"""Content-addressed units, so a change recomputes only what it touched.

The failure this prevents is expensive and silent: a 45-minute run is repeated
in full because one seed was added, or because an unrelated arm was edited, and
nothing in the output says which parts were already known.

A *unit* is one result plus the exact inputs that produced it. ``plan`` is that
input record — everything that can change the answer must be in it, because the
key is the digest of the plan and the key is the whole invalidation rule. The
cache stores the payload, the artifact paths with their digests, and the wall
clock; ``lookup`` returns a unit only when the plan matches **and** every
artifact still hashes to what was recorded. A missing file, an edited one, or a
half-written JSON is a miss, never a silent reuse.

Two rules make this honest rather than a way to avoid work:

1. The plan must be built by one function used by both the compute path and the
   lookup path (``probe_ladder85.arm_plan``), so the two cannot drift.
2. The plan includes ``impl`` — digests of the code that does the computing. An
   edit to the trainer therefore invalidates the units, which is correct: those
   results were produced by different code.

This module owns no domain knowledge; it is deliberately small and torch-free.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

SCHEMA = 1
#: Written next to each unit so a half-finished store is never read as a unit.
MANIFEST = "unit.json"


def canonical(value: Any) -> str:
    """A single canonical text form for a plan (sorted keys, no whitespace)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def file_digest(path: Path) -> str:
    sha = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return "sha256:" + sha.hexdigest()


def unit_key(plan: Mapping[str, Any]) -> str:
    """The invalidation rule itself: same plan -> same key, any change -> new key."""
    if not isinstance(plan, Mapping):
        raise TypeError("plan must be a mapping")
    return digest({"schema": SCHEMA, "plan": dict(plan)})


@dataclass
class Unit:
    key: str
    plan: Dict[str, Any]
    payload: Dict[str, Any]
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    seconds: float = 0.0
    created: float = 0.0
    schema: int = SCHEMA

    def artifact(self, name: str) -> Optional[Dict[str, Any]]:
        for item in self.artifacts:
            if item.get("name") == name:
                return item
        return None


class UnitCache:
    """One directory of units; ``base`` is what artifact paths are relative to."""

    def __init__(self, root: Path | str, base: Path | str | None = None) -> None:
        self.root = Path(root)
        self.base = Path(base) if base is not None else self.root

    # -- paths --------------------------------------------------------------
    def _relative(self, path: Path) -> str:
        path = Path(path).resolve()
        try:
            return os.path.relpath(path, self.base.resolve())
        except ValueError:
            return str(path)

    def _absolute(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else (self.base / path)

    def unit_dir(self, key: str) -> Path:
        # ``sha256:`` is not a portable directory name on every filesystem.
        return self.root / key.split(":", 1)[-1]

    # -- read ---------------------------------------------------------------
    def load(self, key: str) -> Optional[Unit]:
        path = self.unit_dir(key) / MANIFEST
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or int(data.get("schema", -1)) != SCHEMA:
            return None
        if data.get("key") != key:
            return None
        plan = data.get("plan")
        payload = data.get("payload")
        if not isinstance(plan, dict) or not isinstance(payload, dict):
            return None
        return Unit(
            key=key,
            plan=plan,
            payload=payload,
            artifacts=list(data.get("artifacts") or []),
            seconds=float(data.get("seconds", 0.0)),
            created=float(data.get("created", 0.0)),
            schema=SCHEMA,
        )

    def verify(self, unit: Unit) -> List[str]:
        """Everything that must still be true for this unit to be reusable."""
        problems: List[str] = []
        if unit_key(unit.plan) != unit.key:
            problems.append("plan does not hash to the recorded key")
        for item in unit.artifacts:
            name = item.get("name") or item.get("path")
            recorded = item.get("sha256")
            path = self._absolute(str(item.get("path")))
            if not path.is_file():
                problems.append(f"artifact missing: {name} ({item.get('path')})")
                continue
            if recorded and file_digest(path) != recorded:
                problems.append(f"artifact changed: {name} ({item.get('path')})")
        return problems

    def lookup(self, plan: Mapping[str, Any]) -> Optional[Unit]:
        key = unit_key(plan)
        unit = self.load(key)
        if unit is None:
            return None
        if unit.plan != dict(plan):
            return None
        if self.verify(unit):
            return None
        return unit

    def explain_miss(self, plan: Mapping[str, Any]) -> str:
        key = unit_key(plan)
        unit = self.load(key)
        if unit is None:
            return "no unit for this plan"
        if unit.plan != dict(plan):
            return "recorded plan differs from this plan"
        problems = self.verify(unit)
        return "; ".join(problems) if problems else "reusable"

    # -- write --------------------------------------------------------------
    def store(
        self,
        plan: Mapping[str, Any],
        payload: Mapping[str, Any],
        artifacts: Sequence[Any] = (),
        seconds: float = 0.0,
    ) -> Unit:
        """Register a result. An artifact is a path or a ``(role, path)`` pair.

        The role matters: callers ask for ``unit.artifact("opt_state")``, which
        a filename cannot answer when the file is called ``warm_0_2_opt.pt``.
        Without a role the filename is used, which is enough for a single-file
        artifact.
        """
        key = unit_key(plan)
        record: List[Dict[str, Any]] = []
        for item in artifacts:
            role, path = item if isinstance(item, tuple) else (None, item)
            path = Path(path)
            if not path.is_file():
                # Refuse to register an artifact that does not exist: a unit
                # whose file is missing is not a result, it is a promise.
                raise FileNotFoundError(str(path))
            record.append(
                {
                    "name": str(role) if role is not None else path.name,
                    "file": path.name,
                    "path": self._relative(path),
                    "sha256": file_digest(path),
                    "bytes": int(path.stat().st_size),
                }
            )
        unit = Unit(
            key=key,
            plan=dict(plan),
            payload=dict(payload),
            artifacts=record,
            seconds=float(seconds),
            created=time.time(),
        )
        target = self.unit_dir(key)
        target.mkdir(parents=True, exist_ok=True)
        temp = target / (MANIFEST + ".tmp")
        temp.write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "key": key,
                    "plan": unit.plan,
                    "payload": unit.payload,
                    "artifacts": unit.artifacts,
                    "seconds": unit.seconds,
                    "created": unit.created,
                },
                indent=1,
                sort_keys=True,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        temp.replace(target / MANIFEST)
        return unit

    # -- audit --------------------------------------------------------------
    def keys(self) -> List[str]:
        if not self.root.is_dir():
            return []
        return sorted(
            "sha256:" + path.name
            for path in self.root.iterdir()
            if path.is_dir() and (path / MANIFEST).is_file()
        )

    def validate_all(self) -> Dict[str, List[str]]:
        problems: Dict[str, List[str]] = {}
        for key in self.keys():
            unit = self.load(key)
            if unit is None:
                problems[key] = ["unreadable unit"]
                continue
            found = self.verify(unit)
            if found:
                problems[key] = found
        return problems


def impl_digest(paths: Iterable[Path]) -> str:
    """Digest of the code that computes a unit (an edit must invalidate it)."""
    parts = [[Path(p).name, file_digest(Path(p))] for p in paths]
    return digest(sorted(parts))
