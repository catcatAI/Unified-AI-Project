# =============================================================================
# ANGELA-MATRIX: L1 [γ] [A] [L0]
# =============================================================================
"""Guard: script and test paths cited in active docs must resolve.

Why this exists
---------------
Docs rot silently.  A purge deletes ``scripts/train_three_axis.py`` and every
guide that told the reader to run it keeps printing the same command, so the
reader gets a 404 or an ``ImportError`` and the repo's tests never notice --
none of them read markdown.

A 2026-10 audit found ~38 such references across the *active* docs
(``docs/03-technical-architecture/``, ``docs/05-development/``, module
``README``s): moved files cited at their old path, removed scripts still
presented as runnable, and a whole deleted subsystem (three-axis) documented
with a full command section.  Extending the same check to ``pytest <path>``
invocations immediately found more: a game-AI plan whose seven per-module test
files had been consolidated into four others, and a task-map row claiming four
E2E test files where two of the named ones do not exist.

Resolution rules (all three are needed to avoid false positives):

1. ``cd <dir>`` inside a code fence updates the working directory, so
   ``cd apps/backend`` + ``python scripts/x.py`` means
   ``apps/backend/scripts/x.py`` -- not a missing ``scripts/x.py``.
2. A document's own directory is tried first, because module ``README``s cite
   their siblings relatively.
3. The repository root is the final fallback.

Exemptions are explicit and must stay justified:

* dated reports / changelogs / completed fix logs -- editing those would
  falsify history, so they are records, not instructions;
* illustrative placeholder filenames (``your_script.py``, ``script.py``);
* docs whose *stated purpose* is to describe removed tooling; each entry in
  ``ALLOWED_UNRESOLVED_DOCS`` carries the reason and the removal commit.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

# Vendored / VCS / scratch dirs and the agent-tool workspace (which keeps its
# own planning docs, including tools it has not created yet).
SKIP_DIR_PARTS = frozenset({".git", ".venv", "node_modules", ".zenflow", ".angela", "09-archive"})

# Generated from the live tree, so it can only ever be as fresh as the tree;
# and the audit doc that deliberately enumerates the missing paths.
SKIP_FILENAMES = frozenset({"PROJECT_MAP_GENERATED.md", "CODE_AUDIT_DECISIONS_2026-10-13.md"})

# Frozen records: dated reports, changelogs, completed fix logs.
HISTORICAL_PREFIXES = (
    "docs/06-project-management/fixes/",
    "docs/03-technical-architecture/testing/",
    "docs/06-project-management/PROGRESS_",
    "docs/06-project-management/RESEARCH_",
    "docs/AUDIT_FINDINGS_",
    "docs/REFACTOR_PLAN.md",
    "CHANGELOG.md",
)

# Placeholder names used in examples ("run your own file like this").
# NOTE: real deleted files must NOT be listed here -- list them as a fixed
# doc instead; this set is only for names that were never real paths.
ILLUSTRATIVE = frozenset(
    {
        "script.py",
        "main.py",
        "my_script.py",
        "app.py",
        "example.py",
        "your_script.py",
        "data_processing.py",
        "path.py",
        "test_file.py",
        "test_specific.py",
    }
)

# Documents allowed to cite scripts that do not exist, because describing the
# removed subsystem IS their content. Each entry records why + the commit that
# removed it. A doc must carry a visible removal banner to qualify.
ALLOWED_UNRESOLVED_DOCS: Dict[str, str] = {
    "docs/03-technical-architecture/THREE_AXIS_SYSTEM.md": (
        "three-axis code removed in b26456bac; header + §8.6 marked as "
        "historical, commands stated to be non-runnable"
    ),
    "docs/03-technical-architecture/AUTO_FIX_SYSTEM_DETAILED_DESCRIPTION.md": (
        "auto-fix system removed in 311ad8d53; header marked as historical record"
    ),
    "apps/backend/CONTENT_ANALYSIS_MODULE_TEST_FIXES_SUMMARY.md": (
        "dated fix summary whose Verification section cites the removed "
        "tests/core_ai/ legacy layout; banner added, kept as a record"
    ),
}

_CALL_RE = re.compile(r"\bpython3?\s+(?P<path>[A-Za-z0-9_./\\-]+\.py)\b")
# `pytest <path>` and `python -m pytest <path>` -- the invocation form that hid
# the deleted per-module test files.
_TEST_CALL_RE = re.compile(r"\bpytest\s+(?P<path>[A-Za-z0-9_./\\-]+\.py)\b")
_CITED_RES = (_CALL_RE, _TEST_CALL_RE)
_CD_RE = re.compile(r"\bcd\s+(?P<dir>[A-Za-z0-9_./\\-]+)\s*(?:&&|$)")


def _iter_docs() -> List[Path]:
    docs: List[Path] = []
    for path in sorted(REPO_ROOT.rglob("*.md")):
        rel = path.relative_to(REPO_ROOT)
        if any(part in SKIP_DIR_PARTS for part in rel.parts):
            continue
        if rel.name in SKIP_FILENAMES or str(rel).startswith(HISTORICAL_PREFIXES):
            continue
        docs.append(path)
    return docs


def _cwd_updates(line: str, doc_dir: Path, cwd: Path) -> Path:
    """Apply a `cd <dir>` in `line`, relative to the doc dir or the current cwd."""
    match = _CD_RE.search(line)
    if not match or "cd " not in line:
        return cwd
    target = match.group("dir").replace("\\", "/").rstrip("/")
    if not target or target.startswith("-") or "<" in target:
        return cwd
    for candidate in (doc_dir / target, Path(target)):
        if (REPO_ROOT / candidate).is_dir():
            return candidate
    return cwd


def _unresolved_in(doc: Path) -> List[Tuple[int, str]]:
    """Line numbers + cited paths in `doc` that resolve nowhere."""
    doc_dir = doc.relative_to(REPO_ROOT).parent
    try:
        text = doc.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):  # pragma: no cover - defensive
        return []

    cwd = doc_dir
    hits: List[Tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            # Commented-out commands are deliberately not instructions
            # (this is also how fixes mark "this used to say X").
            continue
        cwd = _cwd_updates(line, doc_dir, cwd)
        for cited in _cited_paths(line):
            if _ignored(cited):
                continue
            if not any((REPO_ROOT / base / cited).is_file() for base in (cwd, doc_dir, Path(""))):
                hits.append((lineno, cited))
    return hits


def _cited_paths(line: str) -> List[str]:
    """Every ``.py`` path cited as a command on `line` (python or pytest form)."""
    return [
        m.group("path").replace("\\", "/") for regex in _CITED_RES for m in regex.finditer(line)
    ]


def _ignored(cited: str) -> bool:
    """Paths that must not be resolved: absolute, escaping, or placeholder."""
    return cited.startswith("/") or ".." in cited or Path(cited).name in ILLUSTRATIVE


def _collect() -> Tuple[Dict[str, List[Tuple[int, str]]], int]:
    """Return (unexpected unresolved refs per doc, count of resolved refs)."""
    unexpected: Dict[str, List[Tuple[int, str]]] = {}
    resolved = 0
    for doc in _iter_docs():
        rel = doc.relative_to(REPO_ROOT).as_posix()
        hits = _unresolved_in(doc)
        if rel in ALLOWED_UNRESOLVED_DOCS:
            continue
        if hits:
            unexpected[rel] = hits
        resolved += _resolved_count(doc)
    return unexpected, resolved


def _resolved_count(doc: Path) -> int:
    """Number of cited paths in `doc` that do resolve (non-vacuity check)."""
    doc_dir = doc.relative_to(REPO_ROOT).parent
    try:
        text = doc.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):  # pragma: no cover - defensive
        return 0
    cwd = doc_dir
    found = 0
    for line in text.splitlines():
        if line.strip().startswith("#"):
            continue
        cwd = _cwd_updates(line, doc_dir, cwd)
        for cited in _cited_paths(line):
            if _ignored(cited):
                continue
            if any((REPO_ROOT / base / cited).is_file() for base in (cwd, doc_dir, Path(""))):
                found += 1
    return found


def test_documented_script_paths_resolve() -> None:
    """No active doc may tell the reader to run a script or test that is gone."""
    unexpected, _ = _collect()
    rendered: List[str] = []
    for doc, hits in sorted(unexpected.items()):
        for lineno, cited in hits:
            rendered.append(f"{doc}:{lineno} -> {cited}")
    assert not unexpected, (
        "Active docs cite script paths that do not resolve "
        f"({len(rendered)} reference(s)). Either fix the path/command, mark the "
        "command as removed (comment it out with a reason), or -- only for docs "
        "whose subject IS the removed tooling -- add the doc to "
        "ALLOWED_UNRESOLVED_DOCS with its removal commit:\n  " + "\n  ".join(rendered)
    )


def test_allowlist_docs_exist() -> None:
    """A stale allowlist entry would silently re-enable the drift it exempts."""
    missing = [rel for rel in ALLOWED_UNRESOLVED_DOCS if not (REPO_ROOT / rel).is_file()]
    assert not missing, (
        "ALLOWED_UNRESOLVED_DOCS names documents that no longer exist; "
        f"remove these entries: {missing}"
    )


def test_scanner_is_not_vacuous() -> None:
    """The check must actually be reading the docs, not silently matching nothing.

    A floor (rather than an exact count) keeps this from breaking every time a
    doc legitimately drops or adds a command, while still failing if the
    scanner stops finding references entirely -- e.g. after a refactor that
    broke the regex.
    """
    _, resolved = _collect()
    assert resolved > 100, (
        f"Only {resolved} documented script references were resolved; the "
        "scanner is probably broken (expected to see the whole active docs set)."
    )
