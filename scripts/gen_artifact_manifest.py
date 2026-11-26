#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
"""Generate a manifest for the project's measurable artifacts.

This EXTENDS the format already used by scripts/prepare_core_training_data.py
(``files`` → sha256, ``report`` → provenance), it does not invent a new one.
Artifacts live under gitignored ``data/``, so the manifest is local too: a fresh
clone has neither, and the fact gate reports that as INFO (not a failure).

Usage
    python3 scripts/gen_artifact_manifest.py [--root REPO] [--out PATH] [--check]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCHEMA_VERSION = "artifact-manifest-v1"
HASH_LIMIT_BYTES = 128 * 1024 * 1024  # larger binaries: record size, not hash

# Runtime state mutates on every server tick — record for traceability but
# never gate its hash (otherwise the gate cries wolf on a normal run).
VOLATILE_PREFIXES = (
    "data/checkpoints/lifecycle/",
    "data/checkpoints/msba/",
    "data/state/",
    "data/angela_memory/",
)

# Critical artifacts a reader expects to trace (the current score chain).
CRITICAL = (
    "data/intelligence_reports/core_control.json",
    "data/intelligence_reports/native_dialogue.json",
    "data/intelligence_reports/paraphrase.json",
    "data/intelligence_reports/provenance_census.json",
    "data/intelligence_reports/token_snn_108m.json",
    "apps/backend/data/processed/core_train_manifest.json",
    "resources/canon/catalog.json",
    "docs/06-project-management/intelligence_report.json",
)

PRODUCERS = {
    "angela_bench": "scripts/run_benchmarks.py",
    "core_control": "scripts/probe_core_control.py",
    "native_dialogue": "scripts/probe_native_dialogue.py",
    "paraphrase": "scripts/probe_paraphrase.py",
    "provenance_census": "scripts/census_reply_provenance.py",
    "token_snn": "scripts/train_token_snn.py",
    "intelligence_report": "scripts/report_intelligence.py",
    "core_train_manifest": "scripts/prepare_core_training_data.py",
    "catalog": "resources/canon/MASTER_SPEC.md",
}


def _producer(rel: str) -> str:
    name = Path(rel).name
    stem = Path(rel).stem
    return PRODUCERS.get(stem, PRODUCERS.get(name, "unregistered"))


def _sha256(path: Path) -> Tuple[Optional[str], Optional[str]]:
    if path.stat().st_size > HASH_LIMIT_BYTES:
        return None, f"size>{HASH_LIMIT_BYTES} bytes: hash skipped by policy"
    return hashlib.sha256(path.read_bytes()).hexdigest(), None


def collect(root: Path) -> List[dict]:
    """Scan the artifact roots and return one entry per file."""
    patterns = (
        ("data/intelligence_reports", "*.json", "intelligence"),
        ("data/checkpoints", "*.json", "checkpoint"),
        ("apps/backend/data/models", "*.json", "model"),
        ("apps/backend/data/processed", "*_manifest.json", "training-data"),
        ("resources/canon", "catalog.json", "canon"),
        ("docs/06-project-management", "intelligence_report.json", "report"),
    )
    entries: List[dict] = []
    seen = set()
    for folder, pattern, namespace in patterns:
        for path in sorted((root / folder).rglob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            if rel.startswith(VOLATILE_PREFIXES):
                entries.append(
                    {
                        "path": rel,
                        "type": path.suffix.lstrip("."),
                        "namespace": "runtime-volatile",
                        "producer": "runtime",
                        "schema_version": SCHEMA_VERSION,
                        "size": path.stat().st_size,
                        "sha256": None,
                        "skip_reason": "runtime volatile state — hash not gated",
                        "verified": False,
                    }
                )
                continue
            digest, reason = _sha256(path)
            entries.append(
                {
                    "path": rel,
                    "type": path.suffix.lstrip("."),
                    "namespace": namespace,
                    "producer": _producer(rel),
                    "schema_version": SCHEMA_VERSION,
                    "size": path.stat().st_size,
                    "sha256": digest,
                    "skip_reason": reason,
                    "verified": digest is not None,
                }
            )
    return entries


def build(root: Path) -> dict:
    entries = collect(root)
    by_path = {entry["path"]: entry for entry in entries}
    return {
        "generated_by": "scripts/gen_artifact_manifest.py",
        "schema_version": SCHEMA_VERSION,
        "critical": list(CRITICAL),
        "critical_present": [p for p in CRITICAL if p in by_path],
        "entries": entries,
        "count": len(entries),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--out", default=None)
    parser.add_argument("--check", action="store_true", help="verify stored hashes")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    out = Path(args.out) if args.out else root / "data" / "artifact_manifest.json"
    manifest = build(root)

    if args.check:
        if not out.is_file():
            print(f"no manifest at {out} — run without --check first", file=sys.stderr)
            return 1
        stored = json.loads(out.read_text(encoding="utf-8"))
        old = {e["path"]: e["sha256"] for e in stored.get("entries", []) if e.get("verified")}
        new = {e["path"]: e["sha256"] for e in manifest["entries"] if e.get("verified")}
        critical = [
            p for p in stored.get("critical", []) if p in (stored.get("critical_present") or [])
        ]
        missing = [p for p in critical if p not in new]
        changed = [p for p in old if p in new and old[p] != new[p]]
        if missing or changed:
            print(f"FAIL: missing={missing} changed={changed}")
            return 1
        print(f"OK: {len(new)} entries, critical {len(stored.get('critical_present', []))}")
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}: {manifest['count']} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
