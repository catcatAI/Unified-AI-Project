# =============================================================================
# ANGELA-MATRIX: [L5] [β] [A] [L4]
# =============================================================================
"""What belongs where: memory / knowledge / reasoning / learning / surface.

WHY this exists
---------------
The same failure keeps recurring: a store + a matcher is built, it answers
fluently, and it is reported as "learning" or "intelligence". The words then
mean nothing, because the same behaviour is produced by a dict and by a brain.

The five layers are decided by *what carries the capability*, never by how it
looks from outside. Placement test, in order:

1. **learning** — does the answer survive deletion of the source (the text, the
   record, the conversation)? If yes, the capability is in parameters and this
   is learning. If no, it is memory/retrieval, however fluent it looked.
2. **memory** — is the answer a record of what *this user* said/sees, i.e.
   attributable and revocable? Then it is memory: it may be stale or wrong, it
   must say where it came from, and it must never be asserted as a fact.
3. **knowledge** — is it a proposition with a publishable source (corpus,
   curated base) that is true independently of who asked? Then it is knowledge:
   it needs provenance, and it may be retrieved or verified but never invented
   by a surface layer.
4. **reasoning** — is the answer *derived* and reproducible from inputs
   (formula, logic, proof), rather than looked up? Then it is reasoning, and it
   must not be a stored string.
5. **surface** — does it only decide *where* a request goes or *how* it is
   phrased (routing, templates, formatting)? Then it is surface and it may not
   be the origin of 1-4.

Enforcement lives in ``docs/06-project-management/LAYER_REGISTRY.json`` (one
entry per claim: layer, implementing module, evidence probe, last result) and
``scripts/check_layer_separation.py``. A module that claims a layer must carry
a ``# LAYER: <layer>`` marker in its header; a learning claim must have a probe
that deletes the source; a memory module may not answer through the knowledge
path.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

MARKER = "# LAYER:"
HEADER_LINES = 40


class Layer(str, Enum):
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    LEARNING = "learning"
    SURFACE = "surface"


VALID_STATUS = ("pass", "fail", "n/a")
REQUIRED_FIELDS = ("id", "claim", "layer", "implemented_in", "evidence", "result")
_PATH_RULES = (
    ("/ai/memory/", Layer.MEMORY),
    ("/ai/knowledge/", Layer.KNOWLEDGE),
)


def read_marker(path: Path) -> Optional[str]:
    """The declared layer of a module (first 40 lines), or None."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[:HEADER_LINES]
    except OSError:
        return None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(MARKER):
            return (
                stripped[len(MARKER) :].strip().split()[0].lower()
                if stripped[len(MARKER) :].strip()
                else None
            )
    return None


def _imports_memory(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        names: List[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module] + [f"{node.module}.{alias.name}" for alias in node.names]
        if any("ai.memory" in name or name.startswith("ai.memory") for name in names):
            return True
    return False


@dataclass
class Problem:
    entry: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.entry}: [{self.rule}] {self.detail}"


def validate_entry(entry: Dict[str, Any], repo: Path) -> List[Problem]:
    problems: List[Problem] = []
    entry_id = str(entry.get("id") or "<missing id>")

    def bad(rule: str, detail: str) -> None:
        problems.append(Problem(entry_id, rule, detail))

    for field in REQUIRED_FIELDS:
        if not entry.get(field):
            bad("fields", f"missing {field}")
    if problems:
        return problems

    try:
        layer = Layer(str(entry["layer"]))
    except ValueError:
        bad("layer", f"unknown layer {entry['layer']!r}")
        return problems

    implementation = repo / str(entry["implemented_in"])
    if not implementation.is_file():
        bad("implemented_in", f"{entry['implemented_in']} does not exist")
        return problems

    marker = read_marker(implementation)
    if marker != layer.value:
        bad(
            "marker",
            f"{entry['implemented_in']} declares {marker!r}, registry says {layer.value!r}",
        )

    for fragment, expected in _PATH_RULES:
        if fragment in str(entry["implemented_in"]) and layer is not expected:
            bad("path", f"{fragment} must be layer {expected.value}, got {layer.value}")

    if layer is Layer.KNOWLEDGE and _imports_memory(implementation):
        bad("knowledge", "a knowledge module may not import the memory layer")

    evidence = entry["evidence"] or {}
    probe = repo / str(evidence.get("probe") or "")
    if not evidence.get("probe") or not probe.is_file():
        bad("evidence", f"probe {evidence.get('probe')!r} does not exist")
    if not evidence.get("method"):
        bad("evidence", "evidence.method is required (what does the probe measure?)")
    if layer is Layer.LEARNING and evidence.get("source_deleted") is not True:
        bad(
            "learning",
            "a learning claim needs evidence.source_deleted=true "
            "(otherwise the probe only measures storage)",
        )

    result = entry["result"] or {}
    if result.get("status") not in VALID_STATUS:
        bad("result", f"status must be one of {VALID_STATUS}")
    if not result.get("measured_at"):
        bad("result", "measured_at is required")

    forbidden = set(str(item) for item in (entry.get("must_not_be_used_as") or []))
    if layer is not Layer.LEARNING and "learning" not in forbidden:
        bad("must_not_be_used_as", "every non-learning claim must forbid 'learning'")
    if layer is Layer.MEMORY and not {"knowledge", "intelligence"} <= forbidden:
        bad(
            "must_not_be_used_as",
            "memory must forbid both 'knowledge' and 'intelligence'",
        )
    if layer is Layer.SURFACE and "knowledge" not in forbidden:
        bad("must_not_be_used_as", "surface must forbid 'knowledge'")
    return problems


def validate_registry(registry: Dict[str, Any], repo: Path) -> List[Problem]:
    problems: List[Problem] = []
    entries = registry.get("claims") or []
    if not entries:
        return [Problem("<registry>", "claims", "no claims registered")]
    seen = set()
    for entry in entries:
        entry_id = str(entry.get("id") or "")
        if entry_id in seen:
            problems.append(Problem(entry_id, "unique", "duplicate claim id"))
        seen.add(entry_id)
        problems.extend(validate_entry(entry, repo))
    return problems
