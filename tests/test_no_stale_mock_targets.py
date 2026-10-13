# =============================================================================
# ANGELA-MATRIX: L1 [γ] [A] [L0]
# =============================================================================
"""Guard: no test may patch/import a module path that does not exist.

Why this exists
---------------
``unittest.mock.patch`` and ``pytest.importorskip`` both fail *silently* when a
purge deletes the module they name:

* ``importorskip`` turns a permanently missing module into a permanently
  ``SKIPPED`` test, hiding the gap forever.
* ``patch`` only needs an *attribute* chain.  This repo's package
  ``__init__`` files expose a sentinel ``__getattr__`` that fabricates a dummy
  object for any unknown name, so patching
  ``core.<deleted_module>.<Class>.<method>`` "succeeds" against garbage and
  the test then asserts on the mock it just created -- a false pass that never
  touches production code.

This module scans the test tree for those dotted targets and fails when the
module behind them cannot be located, so a future purge cannot silently
reintroduce the problem.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = (REPO_ROOT / "tests", REPO_ROOT / "apps" / "backend" / "tests")

# Targets that only exist on one platform and are therefore guarded by an
# explicit platform check + pytest.skip() in the test that uses them.
ALLOWLIST = frozenset({"ctypes.windll"})

_PATCH_RE = re.compile(
    r"""(?:\bpatch|\bmonkeypatch\.setattr|\bsetattr)\(\s*["']([A-Za-z_][\w.]*)["']"""
)
_IMPORTORSKIP_RE = re.compile(r"""importorskip\(\s*["']([A-Za-z_][\w.]*)["']""")

_MODULE_CACHE: Dict[str, bool] = {}


def _is_module(dotted: str) -> bool:
    if dotted in _MODULE_CACHE:
        return _MODULE_CACHE[dotted]
    try:
        spec = importlib.util.find_spec(dotted)
    except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
        spec = None
    except Exception:  # pragma: no cover - a broken package must not mask a hit
        spec = None
    result = spec is not None
    _MODULE_CACHE[dotted] = result
    return result


def _longest_module_prefix(parts) -> int:
    for end in range(len(parts), 0, -1):
        if _is_module(".".join(parts[:end])):
            return end
    return 0


def _stale_patch_target(target: str) -> bool:
    """True when the target names a module path that has been purged.

    A healthy target resolves down to ``pkg.sub.Class.attr`` (prefix
    ``pkg.sub``).  A purged one only resolves to the *root* package -- the
    sentinel ``__getattr__`` on the root package then fabricates every
    remaining component, which is exactly how the deleted-module patches
    slipped through.
    """
    parts = target.split(".")
    if len(parts) < 2:
        return False
    if any(target == a or target.startswith(a + ".") for a in ALLOWLIST):
        return False
    longest = _longest_module_prefix(parts)
    if longest == 0:
        return True
    return longest == 1 and len(parts) >= 3


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _collect() -> List[Tuple[Path, int, str]]:
    hits: List[Tuple[Path, int, str]] = []
    self_path = Path(__file__).resolve()
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if path.resolve() == self_path:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:  # pragma: no cover - defensive
                continue
            for regex, kind, checker in (
                (_PATCH_RE, "patch", _stale_patch_target),
                (_IMPORTORSKIP_RE, "importorskip", lambda d: not _is_module(d)),
            ):
                for match in regex.finditer(text):
                    lineno = _line_of(text, match.start())
                    line = text.splitlines()[lineno - 1]
                    stripped = line.lstrip()
                    if stripped.startswith("#") or '"""' in stripped:
                        continue
                    if checker(match.group(1)):
                        hits.append((path, lineno, f"[{kind}] {match.group(1)}"))
    hits.sort(key=lambda h: (str(h[0]), h[1]))
    return hits


def test_no_stale_patch_or_importorskip_targets():
    """Every ``patch(...)`` / ``importorskip(...)`` string target must exist."""
    hits = _collect()
    rendered = [f"{path.relative_to(REPO_ROOT)}:{lineno} {detail}" for path, lineno, detail in hits]
    assert not hits, (
        "Tests target modules that no longer exist -- they cannot exercise "
        f"production code ({len(hits)} hit(s)):\n  " + "\n  ".join(rendered)
    )
