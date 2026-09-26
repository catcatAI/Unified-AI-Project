#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
"""
sync_shared_js.py — vendor the shared renderer modules into each front-end and
prove every <script src> actually resolves.

WHY this exists
`apps/desktop-app/electron_app/index.html` loaded its 32 shared modules from
``../../../packages/shared-js/js/…`` — a path that exists in the source tree but
NOT inside the packaged app, because electron-builder's ``files`` globs cannot
reach outside the app directory. The built AppImage therefore shipped an app
whose every shared module 404'd: ``new AngelaApp()`` threw a ReferenceError and
the window stayed on the "Loading Angela AI…" overlay forever. The same class of
failure hit the web viewer, whose only server (``python -m http.server`` rooted
at the viewer directory) cannot serve ``../..`` either.

Both surfaces now load the modules from a vendored copy *inside* the surface
directory, so development and the packaged artifact load exactly the same files.
The copy is generated (git-ignored) and re-verified on every start/build, so the
two can never drift silently.

Usage
    python3 scripts/sync_shared_js.py            # vendor + verify all surfaces
    python3 scripts/sync_shared_js.py --check    # verify only, no writes
    python3 scripts/sync_shared_js.py --surface desktop
"""

import argparse
import filecmp
import os
import re
import shutil
import sys
from typing import Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(ROOT, "packages", "shared-js", "js")

# surface -> (surface dir, vendored dir relative to surface, HTML entry points)
SURFACES: Dict[str, Tuple[str, str, Tuple[str, ...]]] = {
    "desktop": (
        os.path.join(ROOT, "apps", "desktop-app", "electron_app"),
        os.path.join("libs", "shared-js"),
        ("index.html", "settings.html", "multimodal-panel.html"),
    ),
    "web": (
        os.path.join(ROOT, "apps", "web-live2d-viewer"),
        os.path.join("js", "shared-js"),
        ("index.html",),
    ),
}

_SCRIPT_SRC = re.compile(r'<script[^>]+src="([^"]+)"', re.IGNORECASE)
_VENDOR_TAG = "/shared-js/"

# Assets that may legitimately be absent because the surface degrades without
# them. The Cubism Framework bundle is built by webpack from TypeScript sources
# and is not produced by any pnpm script; Live2DManager renders through its own
# WebGL path when it is missing, so it is reported as a warning, not an error.
OPTIONAL_SUFFIXES = ("live2dcubismframework.bundle.js",)


def _log(message: str) -> None:
    print(f"[sync-shared-js] {message}")


def _surface_paths(name: str) -> Tuple[str, str, Tuple[str, ...]]:
    return SURFACES[name]


def _source_files() -> List[str]:
    if not os.path.isdir(SOURCE_DIR):
        raise SystemExit(f"shared-js source directory missing: {SOURCE_DIR}")
    return sorted(
        fname
        for fname in os.listdir(SOURCE_DIR)
        if fname.endswith(".js") and os.path.isfile(os.path.join(SOURCE_DIR, fname))
    )


def _vendor_target(surface_dir: str, vendored_rel: str, filename: str) -> str:
    return os.path.join(surface_dir, vendored_rel, filename)


def vendor(surface: str, check_only: bool) -> Tuple[int, int]:
    """Copy changed shared modules into the surface. Returns (copied, skipped)."""
    surface_dir, vendored_rel, _ = _surface_paths(surface)
    copied = skipped = 0
    target_dir = os.path.join(surface_dir, vendored_rel)
    for filename in _source_files():
        src = os.path.join(SOURCE_DIR, filename)
        dst = _vendor_target(surface_dir, vendored_rel, filename)
        if os.path.isfile(dst) and filecmp.cmp(src, dst, shallow=False):
            skipped += 1
            continue
        if check_only:
            copied += 1
            continue
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    return copied, skipped


def _referenced_shared_js(surface: str) -> Dict[str, List[str]]:
    """filename -> HTML files that reference it (through the vendored path)."""
    surface_dir, _, entries = _surface_paths(surface)
    refs: Dict[str, List[str]] = {}
    for entry in entries:
        html_path = os.path.join(surface_dir, entry)
        if not os.path.isfile(html_path):
            continue
        with open(html_path, encoding="utf-8") as fh:
            for src in _SCRIPT_SRC.findall(fh.read()):
                if _VENDOR_TAG in src or "shared-js" in src:
                    filename = os.path.basename(src.split("?")[0])
                    refs.setdefault(filename, []).append(entry)
    return refs


def verify(surface: str, check_only: bool) -> int:
    """Check that every referenced script resolves. Returns a failure count."""
    surface_dir, vendored_rel, entries = _surface_paths(surface)
    available = set(_source_files())
    failures: List[str] = []
    warnings: List[str] = []

    for entry in entries:
        html_path = os.path.join(surface_dir, entry)
        if not os.path.isfile(html_path):
            failures.append(f"{entry}: missing HTML entry point")
            continue
        with open(html_path, encoding="utf-8") as fh:
            sources = _SCRIPT_SRC.findall(fh.read())
        for src in sources:
            if src.startswith(("http://", "https://", "//", "data:")):
                continue
            target = os.path.normpath(os.path.join(surface_dir, src))
            if os.path.isfile(target):
                continue
            filename = os.path.basename(src.split("?")[0])
            if any(filename.endswith(opt) for opt in OPTIONAL_SUFFIXES):
                warnings.append(f"{entry}: optional asset missing -> {src}")
                continue
            if "shared-js" in src and filename not in available:
                failures.append(f"{entry}: references unknown shared module -> {src}")
            else:
                failures.append(f"{entry}: unresolvable script -> {src}")

    label = os.path.relpath(surface_dir, ROOT)
    for warning in warnings:
        _log(f"WARN [{label}] {warning}")
    if failures:
        for failure in failures:
            _log(f"ERROR [{label}] {failure}")
        return len(failures)
    _log(f"OK [{label}] every <script src> in {', '.join(entries)} resolves")
    return 0


def gitignore_entries() -> List[str]:
    return [
        "apps/desktop-app/electron_app/libs/shared-js/",
        "apps/web-live2d-viewer/js/shared-js/",
    ]


def ensure_gitignore() -> int:
    """Keep the generated copies out of git so drift is impossible in commits."""
    path = os.path.join(ROOT, ".gitignore")
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    missing = [entry for entry in gitignore_entries() if entry not in content]
    if not missing:
        return 0
    with open(path, "a", encoding="utf-8") as fh:
        if not content.endswith("\n"):
            fh.write("\n")
        fh.write("\n# Vendored copies of packages/shared-js (generated by\n")
        fh.write("# scripts/sync_shared_js.py; never commit these).\n")
        for entry in missing:
            fh.write(f"{entry}\n")
    _log(f"added {len(missing)} .gitignore entr(ies) for the vendored copies")
    return len(missing)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify only; do not write the vendored copies",
    )
    parser.add_argument(
        "--surface",
        choices=sorted(SURFACES),
        help="restrict to one surface (default: all)",
    )
    args = parser.parse_args(argv)

    surfaces = [args.surface] if args.surface else sorted(SURFACES)
    if not args.check:
        ensure_gitignore()

    total_failures = 0
    for surface in surfaces:
        copied, skipped = vendor(surface, args.check)
        if not args.check:
            _log(f"[{surface}] vendored {copied} file(s), {skipped} unchanged")
        total_failures += verify(surface, args.check)

    if total_failures:
        _log(
            f"{total_failures} unresolvable <script src> reference(s). "
            "The window will hang on the loading overlay — fix before shipping."
        )
        return 1
    _log("all surfaces verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
