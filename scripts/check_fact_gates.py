#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""全倉事實門：把 gate + audit + edge + UI 合約合成單一裁決，一次輸出。

用法: `.venv/bin/python scripts/check_fact_gates.py [--json out.json]`
退出碼：0 全綠；1 任一 must_pass 失敗（BLOCKED，附 verdict 向量定位）。

覆蓋四域（與測試共享黃金值，見 tests/*/test_*contract*.py 與
tests/core/test_fact_interpreter.py）：
  edge     硬體/edge_card 包絡三 verdict（重算，不信任轉錄數字）
  audit    卡架構審計 blocking 門（經 from_audit_corrections）
  chat     對話回應 × 前端讀鍵交集（P1 首條活鏈）
  cluster  監控面板 6 葉路徑（P1 第二條活鏈）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

REPO = Path(__file__).resolve().parents[1]


def _edge_facts():
    import yaml
    from core.facts import Fact

    spec = yaml.safe_load(
        (REPO / "hardware/assemblies/done/edge_card/edge_card_spec.yaml").read_text()
    )
    primary = spec["model_target"]["primary"]
    envelope = spec["model_target"]["working_set_gb"]
    budget = spec["performance_budget"]
    file_gb = primary["weights_gb_gguf_measured"]
    measured = file_gb + envelope["kv_cache_budget_gb"]["value"] + envelope["os_reserve_gb"]
    bw = budget["decode_assumptions"]["memory_bandwidth_gbs"]
    eta_min, _ = budget["decode_assumptions"]["stream_efficiency_range"]
    decode_low = round(bw * eta_min / file_gb, 1)
    payload_gbs = spec["host_interface"]["payload_gbs_each_direction"]
    load_s = round(file_gb / payload_gbs, 2)
    return [
        Fact("edge.envelope_vs_8gb", round(measured, 2), 8, "le", "GB", "edge_card_spec", ""),
        Fact(
            "edge.decode_bound_vs_15",
            decode_low,
            budget["decode_tok_s"]["target_e2b_q4_0_min"],
            "ge",
            "tok/s",
            "edge_card_spec",
            "",
        ),
        Fact(
            "edge.load_vs_5s",
            load_s,
            budget["host_link"]["cold_load_e2b_q4_0_from_host_s_max"],
            "le",
            "s",
            "edge_card_spec",
            "",
        ),
    ]


def _audit_facts():
    from ai.hardware.card_architecture_audit import ClaimedArchitecture, audit
    from core.facts import from_audit_corrections

    return from_audit_corrections(audit(ClaimedArchitecture())["corrections"]).verdicts


def _chat_facts():
    import re

    from api.routes.chat_routes import _format_chat_response
    from core.facts import Fact

    text = (REPO / "packages/shared-js/js/api-client.js").read_text()
    frontend = set(re.findall(r"data\.(response|message|content)\b", text))
    resp = _format_chat_response("hi", None, None, "2.0", "", "hi", 4000, "gate-script")
    overlap = set(resp) & frontend
    return [
        Fact(
            "chain.chat_response_overlap",
            float(len(overlap)),
            1.0,
            "ge",
            "keys",
            "chat_routes+api-client.js",
            f"overlap={sorted(overlap)}",
        )
    ]


def _cluster_facts():
    from api.router import get_cluster_status
    from core.facts import Fact

    anchors = (
        "data.hardware.cpu.usage",
        "data.hardware.cpu.brand",
        "data.hardware.memory.usage_percent",
        "data.hardware.memory.total",
        "data.hardware.performance_tier",
        "data.hardware.ai_capability_score",
    )
    text = (REPO / "packages/shared-js/js/settings.js").read_text()
    payload = get_cluster_status()

    def _get(dotted: str):
        node = payload
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return None
            node = node[part]
        return node

    covered = sum(1 for a in anchors if a in text and _get(a[5:]) is not None)
    return [
        Fact(
            "chain.cluster_leaves_covered",
            float(covered),
            float(len(anchors)),
            "ge",
            "leaves",
            "api/router.py+settings.js",
            f"covered={covered}/{len(anchors)}",
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    from core.facts import Report, adjudicate, merge_reports

    edge = adjudicate(_edge_facts())
    audit_report = Report()
    for v in _audit_facts():
        audit_report.add(v)
    chains = adjudicate(_chat_facts() + _cluster_facts())
    merged = merge_reports(edge, audit_report, chains)

    print("=" * 72)
    print("FACT GATES (edge + audit + chat-chain + cluster-chain)")
    print("=" * 72)
    print(merged.summary())
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(merged.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"json -> {args.json}")
    return 0 if merged.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
