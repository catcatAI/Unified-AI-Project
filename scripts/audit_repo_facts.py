#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""倉庫事實審計門：語義不變量一次裁決，不再一點一滴手查。

覆蓋（每條都是 Fact，解讀器一次輸出向量）：
  版本一致、測試數同步、硬體文檔普查、edge 引用閉合、
  三條 UI 合約交集、核心包覆蓋率、TODO/裸 except 零容忍。

用法: `.venv/bin/python scripts/audit_repo_facts.py [--json out.json]`
退出碼：0 全綠；1 任一 must_pass 失敗（看 summary 定位）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

REPO = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "7.5.0-dev"


def _collect_count() -> int:
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "--collect-only",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    match = re.findall(r"(\d+) tests collected", out.stdout)
    return int(match[-1]) if match else -1


def _package_coverage(package: str, test_files: list) -> float:
    out = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *test_files,
            f"--cov={package}",
            "--cov-report=term-missing",
            "-q",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    match = re.search(rf"^{re.escape(package)}\s+\d+\s+\d+\s+([\d.]+)%", out.stdout, re.M)
    if not match:
        total = re.search(r"^TOTAL\s+\d+\s+\d+\s+([\d.]+)%", out.stdout, re.M)
        return float(total.group(1)) if total else -1.0
    return float(match.group(1))


def _grep_count(pattern: str, root: Path, suffix: str = ".py") -> int:
    rx = re.compile(pattern)
    hits = 0
    for path in root.rglob(f"*{suffix}"):
        if "__pycache__" in str(path) or ".venv" in str(path):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits += len(rx.findall(text))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    import yaml
    from core.facts import Fact, adjudicate

    facts: list = []

    # ---- 1. 版本一致 ----
    version_files = {
        "VERSION": (REPO / "VERSION").read_text(encoding="utf-8").strip(),
        "package.json": json.loads((REPO / "package.json").read_text())["version"],
        "apps/backend/pyproject.toml": None,
    }
    mismatched = [k for k, v in version_files.items() if v is not None and v != EXPECTED_VERSION]
    backend_pyproject = (REPO / "apps/backend/pyproject.toml").read_text()
    if f'version = "{EXPECTED_VERSION}"' not in backend_pyproject:
        mismatched.append("apps/backend/pyproject.toml")
    facts.append(
        Fact(
            "audit.versions_consistent",
            float(len(mismatched)),
            0.0,
            "le",
            "files",
            "version-locations",
            f"mismatched={mismatched}",
        )
    )

    # ---- 2. 測試數同步 ----
    collected = _collect_count()
    readme = (REPO / "tests/README.md").read_text(encoding="utf-8")
    documented = [int(n.replace(",", "")) for n in re.findall(r"([\d,]+) tests collected", readme)]
    drift = min([abs(collected - d) for d in documented], default=-1)
    facts.append(
        Fact(
            "audit.test_count_synced",
            float(drift),
            0.0,
            "le",
            "tests",
            "tests/README.md",
            f"collected={collected} documented={documented}",
        )
    )

    # ---- 3. 硬體文檔普查 ----
    known_unreferenced = frozenset(
        {
            "ai_compute_card_task",
            "component_registry",
            "concept_design",
            "secondary_compute_draft",
            "mvu_reference_spec",
            "DERIVED_ESTIMATES",
        }
    )
    docs = set()
    for doc in (REPO / "hardware").rglob("*"):
        if doc.suffix not in (".yaml", ".md") or not doc.is_file() or doc.name == "README.md":
            continue
        docs.add(doc.stem)
    corpus_parts = []
    for root, suffix in (
        ("apps/backend/src", ".py"),
        ("tests", ".py"),
        ("scripts", ".py"),
        ("packages/shared-js/js", ".js"),
    ):
        base = REPO / root
        if base.is_dir():
            for path in base.rglob(f"*{suffix}"):
                if "__pycache__" in str(path):
                    continue
                try:
                    corpus_parts.append(path.read_text(encoding="utf-8", errors="replace"))
                except OSError:
                    continue
    corpus = "\n".join(corpus_parts)
    unknown = sorted(s for s in docs if s not in corpus and s not in known_unreferenced)
    facts.append(
        Fact(
            "audit.no_unknown_unreferenced_docs",
            float(len(unknown)),
            0.0,
            "le",
            "docs",
            "hardware/ census",
            f"unknown={unknown}",
        )
    )

    # ---- 4. edge 引用閉合 ----
    spec_text = (REPO / "hardware/edge_card/edge_card_spec.yaml").read_text(encoding="utf-8")
    spec = yaml.safe_load(spec_text)
    defined = set(spec["sources"])
    used = set(re.findall(r"src_[a-z0-9_]+", spec_text))
    bad_refs = len(used - defined) + len(defined - used)
    missing_paths = sum(
        1
        for src in spec["sources"].values()
        if src.get("type") == "internal_spec" and not (REPO / src["url"]).exists()
    )
    facts.append(
        Fact(
            "audit.edge_refs_closed",
            float(bad_refs + missing_paths),
            0.0,
            "le",
            "count",
            "edge_card_spec",
            "",
        )
    )

    # ---- 5. 三條 UI 合約交集 ----
    from api.router import get_cluster_status
    from api.routes.chat_routes import _format_chat_response

    api_client = (REPO / "packages/shared-js/js/api-client.js").read_text(encoding="utf-8")
    settings_js = (REPO / "packages/shared-js/js/settings.js").read_text(encoding="utf-8")
    chat_keys = set(re.findall(r"data\.(response|message|content)\b", api_client))
    chat_resp = _format_chat_response("hi", None, None, "2.0", "", "hi", 4000, "audit-gate")
    chat_overlap = len(set(chat_resp) & chat_keys)
    cluster_anchors = (
        "data.hardware.cpu.usage",
        "data.hardware.cpu.brand",
        "data.hardware.memory.usage_percent",
        "data.hardware.memory.total",
        "data.hardware.performance_tier",
        "data.hardware.ai_capability_score",
    )

    def _nested(data: dict, dotted: str):
        node = data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    cluster_payload = get_cluster_status()
    cluster_covered = sum(
        1
        for a in cluster_anchors
        if a in settings_js and _nested(cluster_payload, a.removeprefix("data.")) is not None
    )
    import asyncio

    from api.routes.ops_routes import get_ops_status

    ops_payload = asyncio.run(get_ops_status())
    ops_covered = sum(
        1
        for k in ("status", "metrics", "service", "timestamp")
        if f"data.{k}" in api_client and ops_payload.get(k) is not None
    )
    facts.append(
        Fact("audit.chat_overlap", float(chat_overlap), 1.0, "ge", "keys", "chat-chain", "")
    )
    facts.append(
        Fact(
            "audit.cluster_covered",
            float(cluster_covered),
            6.0,
            "ge",
            "leaves",
            "cluster-chain",
            "",
        )
    )
    facts.append(Fact("audit.ops_covered", float(ops_covered), 4.0, "ge", "keys", "ops-chain", ""))

    # ---- 6. 核心包覆蓋率 ----
    cov_facts = _package_coverage("core.facts", ["tests/core/test_fact_interpreter.py"])
    cov_hw = _package_coverage(
        "apps/backend/src/ai/hardware",
        [
            "tests/unit/test_cim_verify.py",
            "tests/unit/test_cim_weight_strip.py",
            "tests/unit/test_cim_strip_reference.py",
            "tests/unit/test_flatten_sky130_spice.py",
            "tests/unit/test_mvu_reference_branches.py",
            "tests/unit/test_ai_card_reference_branches.py",
            "tests/unit/test_card_architecture_audit_branches.py",
            "tests/unit/test_rtl_generator_branches.py",
            "tests/unit/test_hardware_branch_closures.py",
            "tests/unit/test_hardware_standards_catalog.py",
            "tests/ai/agents/test_eda_agent_branches.py",
            "tests/unit/test_edge_card_spec.py",
            "tests/unit/test_edge_card_refs.py",
            "tests/unit/test_edge_card_sim.py",
            "tests/unit/test_ai_card_reference.py",
            "tests/unit/test_card_architecture_audit.py",
        ],
    )
    facts.append(Fact("audit.coverage_facts", cov_facts, 100.0, "ge", "%", "pytest-cov", ""))
    facts.append(Fact("audit.coverage_hardware", cov_hw, 100.0, "ge", "%", "pytest-cov", ""))

    # ---- 7. TODO/裸 except 零容忍 ----
    # 全大寫獨立詞匹配（\b），故 unicode 佔位符 XXXX 不計入。
    todo_hits = _grep_count(r"\b(TODO|FIXME|HACK|XXX)\b", REPO / "apps/backend/src")
    bare_except = _grep_count(r"^\s*except\s*:", REPO / "apps/backend/src")
    facts.append(Fact("audit.no_todo_markers", float(todo_hits), 0.0, "le", "hits", "src scan", ""))
    facts.append(
        Fact("audit.no_bare_except", float(bare_except), 0.0, "le", "hits", "src scan", "")
    )

    report = adjudicate(facts)
    print("=" * 72)
    print("REPO FACT AUDIT (versions/counts/refs/contracts/coverage/hygiene)")
    print("=" * 72)
    print(report.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps({"verdict": report.as_dict()}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"json -> {args.json}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
