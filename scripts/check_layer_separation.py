#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L5] [βγ] [A] [L4]
# =============================================================================
"""Layer separation gate: memory / knowledge / reasoning / learning / surface.

Fails when a claim is filed under the wrong layer, when its implementing module
declares a different layer, when a learning claim has no probe that deletes the
source, or when memory is wired into the knowledge path.

The registry lives in ``docs/06-project-management/LAYER_REGISTRY.json``; the
taxonomy is in ``docs/06-project-management/LAYER_SEPARATION.md``.

Usage: `./.venv/bin/python scripts/check_layer_separation.py [--json PATH]`
Exit code: 0 when there is no violation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "backend" / "src"))

REGISTRY = REPO / "docs" / "06-project-management" / "LAYER_REGISTRY.json"
CHAT_ROUTES = REPO / "apps" / "backend" / "src" / "api" / "routes" / "chat_routes.py"
KNOWLEDGE_BASE = REPO / "apps" / "backend" / "src" / "ai" / "knowledge_base.py"


def structural_problems() -> list[str]:
    """Invariants that hold regardless of what the registry says."""
    problems: list[str] = []
    chat = CHAT_ROUTES.read_text(encoding="utf-8") if CHAT_ROUTES.is_file() else ""
    if '"source": "memory"' not in chat:
        problems.append("chat_routes: the taught-fact path must label source=memory")
    if "你教過我" not in chat:
        problems.append("chat_routes: a memory answer must be attributed (你教過我…)")
    knowledge = KNOWLEDGE_BASE.read_text(encoding="utf-8") if KNOWLEDGE_BASE.is_file() else ""
    if "taught_facts" in knowledge:
        problems.append("knowledge_base: the knowledge path must not consult the memory layer")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Layer separation gate")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    from ai.meta.layers import validate_registry

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    problems = validate_registry(registry, REPO)
    structural = structural_problems()

    print("=" * 72)
    print("LAYER SEPARATION")
    print("=" * 72)
    for entry in registry.get("claims") or []:
        result = entry.get("result") or {}
        print(
            f"  {entry.get('id', '?'):<24} {entry.get('layer', '?'):<10} "
            f"{result.get('status', '?'):<5} {result.get('value', '')[:48]}"
        )
    print("-" * 72)
    if problems or structural:
        for problem in problems:
            print(f"  VIOLATION {problem}")
        for problem in structural:
            print(f"  VIOLATION {problem}")
        print(f"  => {len(problems) + len(structural)} violation(s)")
    else:
        print("  => ALL PASS (layers, markers, evidence, and the memory/knowledge split)")
    print("=" * 72)

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "violations": [str(p) for p in problems] + structural,
                    "claims": len(registry.get("claims") or []),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return 1 if (problems or structural) else 0


if __name__ == "__main__":
    raise SystemExit(main())
