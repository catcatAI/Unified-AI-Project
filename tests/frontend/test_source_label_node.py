"""Bridge for the source-label node:test suite + a backend/UI contract check.

WHY two things in one file:

1. Root ``pnpm test`` is ``pytest tests/``, so a plain ``.mjs`` never enters the
   default gate; this bridge keeps ``test_source_label.mjs`` in it (skipped when
   node is unavailable).
2. The front-end mapping is only useful if it covers what the backend actually
   emits. ``_route_map`` in ``chat_routes.py`` is the single place routes are
   derived, so it is parsed here and every value must resolve to an explicit
   bucket — a new backend route must not silently render as "未知".
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
JS = ROOT / "packages" / "shared-js" / "js" / "source-label.js"
CHAT_ROUTES = ROOT / "apps" / "backend" / "src" / "api" / "routes" / "chat_routes.py"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node runtime not available")


def _backend_routes() -> set:
    """Every ``route`` value the chat response builder can derive."""
    text = CHAT_ROUTES.read_text(encoding="utf-8")
    block = text.split("_route_map = {", 1)[1].split("}", 1)[0]
    return {value for _, value in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', block)}


def test_source_label_node_suite():
    script = Path(__file__).resolve().parent / "test_source_label.mjs"
    proc = subprocess.run(
        [NODE, "--test", str(script)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"node --test failed (rc={proc.returncode})\n"
        f"--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}"
    )
    assert "fail 0" in proc.stdout, f"expected 0 failures:\n{proc.stdout}"


def test_every_backend_route_has_an_explicit_label():
    routes = _backend_routes()
    assert "computed" in routes and "knowledge" in routes and "memory" in routes

    probe = (
        "const m = require(process.argv[1]);"
        "const routes = JSON.parse(process.argv[2]);"
        "console.log(JSON.stringify(routes.map((r) => [r, m.labelFor(r).key])));"
    )
    proc = subprocess.run(
        [NODE, "-e", probe, str(JS), json.dumps(sorted(routes))],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    resolved = dict(json.loads(proc.stdout))
    unmapped = sorted(route for route, bucket in resolved.items() if bucket == "unknown")
    assert unmapped == [], f"backend routes without a user-visible source label: {unmapped}"
