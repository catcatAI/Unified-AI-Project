# =============================================================================
# ANGELA-MATRIX: L1 [γ] [A] [L0]
# =============================================================================
"""Guard: every project version declaration must match the source of truth.

Why this exists
---------------
``AGENTS.md`` (version governance, rule 3) requires that "all 14 version
locations stay in sync" and told the reader to find the list in
``MASTER_TASK_MAP.md`` -- **which never contained it**.  So the rule was
unfollowable and nothing enforced it: an archived audit
(``docs/09-archive/DOCUMENTATION_TRUTH_MAP_2026-06-07.md``) recorded the check
as "manual cross-check (not run)".

A hand-check is also unreliable here because the version is duplicated as a
*hardcoded string* in places that are user-visible: the FastAPI app version
reported by ``/docs``, the WebSocket ``server_version`` sent on every connect,
and the mobile endpoint's ``backend_version``.  A drift there ships silently.

This module makes the rule executable.  It enforces:

* Python ``core/version.py`` -- the code-side source of truth, checked by
  actually importing it, not by regex;
* every project manifest (``package.json`` / ``pyproject.toml`` / ``setup.py``);
* config files, ``__version__`` declarations and the hardcoded runtime strings;
* the human-facing ``VERSION:`` headers and the CHANGELOG's top release.

Sub-packages that version independently are exempted *explicitly* with a
reason, and the exemption list is itself checked so it cannot go stale.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]

SOURCE_FILE = "package.json"  # rule 3 names package.json as the trigger file

# Versioned independently of the product (vendored libs and standalone apps).
# Each entry needs a reason; the list is validated below.
INDEPENDENT_PACKAGES: Dict[str, str] = {
    "apps/crystal-cards/package.json": "standalone card app, own release train",
    "apps/desktop-app/electron_app/libs/live2dframework/package.json": "vendored upstream library",
    "apps/web-live2d-viewer/libs/live2dframework/package.json": "vendored upstream library",
    "apps/desktop-app/native_modules/node-coreaudio-capture/package.json": "native addon, own versioning",
    "apps/desktop-app/native_modules/node-pulseaudio-capture/package.json": "native addon, own versioning",
    "apps/desktop-app/native_modules/node-wasapi-capture/package.json": "native addon, own versioning",
}

# (relative path, description, regex whose group(1) is the declared version)
ENFORCED_PATTERNS: List[Tuple[str, str, str]] = [
    ("pyproject.toml", "root pyproject version", r'^\s*version\s*=\s*"([^"]+)"'),
    (
        "apps/backend/pyproject.toml",
        "backend pyproject version",
        r'^\s*version\s*=\s*"([^"]+)"',
    ),
    ("packages/cli/setup.py", "CLI setup.py version", r'version\s*=\s*"([^"]+)"'),
    (
        "configs/angela_config.json",
        "runtime config (JSON)",
        r'"version"\s*:\s*"([^"]+)"',
    ),
    (
        "configs/angela_config.yaml",
        "runtime config (YAML)",
        r'^\s*version\s*:\s*"?([0-9][^"\s]*)"?',
    ),
    (
        "apps/backend/src/__init__.py",
        "backend package __version__",
        r'__version__\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/core/autonomous/__init__.py",
        "core.autonomous __version__",
        r'__version__\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/core/i18n/__init__.py",
        "core.i18n __version__",
        r'__version__\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/core/metamorphosis/__init__.py",
        "core.metamorphosis __version__",
        r'__version__\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/core/sync/__init__.py",
        "core.sync __version__",
        r'__version__\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/services/main_api_server.py",
        "FastAPI app version (shown by /docs)",
        r'version\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/services/websocket_manager.py",
        "WebSocket server_version (sent to every client)",
        r'"server_version"\s*:\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/api/v1/endpoints/mobile.py",
        "mobile backend_version",
        r'"backend_version"\s*:\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/core/life/cyber_identity.py",
        "SelfModel.version default",
        r'version:\s*str\s*=\s*"([^"]+)"',
    ),
    (
        "apps/backend/src/integrations/luanti_connector.py",
        "Luanti client_version (sent on auth)",
        r'"client_version"\s*:\s*"([^"]+)"',
    ),
    ("README.md", "README VERSION header", r"VERSION:\s*([0-9][^\s]*)"),
    ("AGENTS.md", "AGENTS VERSION header", r"VERSION:\s*([0-9][^\s]*)"),
    ("CHANGELOG.md", "CHANGELOG top release", r"^##\s*\[([0-9][^\]]*)\]"),
]

# Documents where only the FIRST match is the current version: a changelog's
# older release headings are history, not drift.
FIRST_MATCH_ONLY = frozenset({"CHANGELOG.md"})

# A literal in backend source that claims the project's own version line.
_PROJECT_VERSION_LITERAL = r'["\'](\d+\.\d+\.\d+(?:-(?:dev|alpha|beta|rc)\d*)?)["\']'


def _source_version() -> str:
    return json.loads((REPO_ROOT / SOURCE_FILE).read_text(encoding="utf-8"))["version"]


def _declared(path: str, pattern: str) -> List[str]:
    text = (REPO_ROOT / path).read_text(encoding="utf-8")
    if path in FIRST_MATCH_ONLY:
        match = re.search(pattern, text, re.M)
        return [match.group(1)] if match else []
    return [m.group(1) for m in re.finditer(pattern, text, re.M)]


def _code_version() -> str:
    """The code-side version, obtained by importing it (not by parsing it)."""
    from core.version import __version__

    return __version__


def test_source_of_truth_exists() -> None:
    source = _source_version()
    assert re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.]+)?", source
    ), f"{SOURCE_FILE} version {source!r} is not a usable version string"


def test_enforced_locations_agree_with_source_of_truth() -> None:
    """Every enforced location must declare the same version as package.json."""
    source = _source_version()
    mismatches: List[str] = []

    for path, description, pattern in ENFORCED_PATTERNS:
        declared = _declared(path, pattern)
        if not declared:
            mismatches.append(f"{path} ({description}): no version found -- pattern broke?")
            continue
        for value in set(declared):
            if value != source:
                mismatches.append(f"{path} ({description}): {value} != {source}")

    assert not mismatches, (
        f"{len(mismatches)} version declaration(s) disagree with {SOURCE_FILE} "
        f"({source}). Update them in the same change:\n  " + "\n  ".join(mismatches)
    )


def test_code_version_module_matches_source_of_truth() -> None:
    """``core.version`` is what the running service reports; it must agree."""
    assert _code_version() == _source_version()


def test_manifests_agree_with_source_of_truth() -> None:
    """All non-exempt package.json files carry the product version."""
    source = _source_version()
    mismatches: List[str] = []
    for pkg in sorted(REPO_ROOT.rglob("package.json")):
        rel = pkg.relative_to(REPO_ROOT).as_posix()
        if "node_modules" in rel or rel.startswith(".venv/"):
            continue
        if rel in INDEPENDENT_PACKAGES:
            continue
        try:
            value = json.loads(pkg.read_text(encoding="utf-8")).get("version")
        except (OSError, json.JSONDecodeError) as e:
            mismatches.append(f"{rel}: unreadable ({e})")
            continue
        if value and value != source:
            mismatches.append(f"{rel}: {value} != {source}")
    assert not mismatches, (
        "package.json files drifted from the product version -- either fix them "
        "or add them to INDEPENDENT_PACKAGES with a reason:\n  " + "\n  ".join(mismatches)
    )


def test_no_stray_project_version_literals_in_backend() -> None:
    """Catch hardcoded project-version strings outside the enforced list.

    Only literals on the *same version line* as the source of truth are flagged,
    so unrelated numbers (a dependency's ``1.0.0``, or ``version.py`` comparing
    against the older ``7.4.0`` in its demo block) are ignored.  This is the
    check that catches a new ``"7.5.0"`` slipped into an API payload.
    """
    source = _source_version()
    line = ".".join(source.split("-")[0].split(".")[:2])  # e.g. "7.5"
    stray: List[str] = []

    for py in sorted((REPO_ROOT / "apps" / "backend" / "src").rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        if py.name == "version.py":
            # The version module *defines* versions; its __main__ demo block
            # deliberately compares against neighbouring releases (7.4.0,
            # 7.5.0 stable).  Its real value is verified by importing it above.
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):  # pragma: no cover - defensive
            continue
        for lineno, src_line in enumerate(text.splitlines(), 1):
            if src_line.strip().startswith("#"):
                continue
            for value in re.findall(_PROJECT_VERSION_LITERAL, src_line):
                if value.startswith(line) and value != source:
                    stray.append(f"{py.relative_to(REPO_ROOT)}:{lineno} -> {value}")

    assert not stray, (
        f"{len(stray)} hardcoded literal(s) claim a different build of the current "
        f"version line ({line}.x, expected {source}):\n  " + "\n  ".join(stray)
    )


def test_independent_package_exemptions_are_real() -> None:
    """A stale exemption would silently un-enforce a file."""
    missing = [rel for rel in INDEPENDENT_PACKAGES if not (REPO_ROOT / rel).is_file()]
    assert not missing, (
        "INDEPENDENT_PACKAGES names files that no longer exist; remove these "
        f"entries so the file is enforced again: {missing}"
    )
