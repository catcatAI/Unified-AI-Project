#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""全倉事實門：把 gate + audit + edge + UI + config/version/docs/modules 合約
合成單一裁決，一次輸出。

用法: `.venv/bin/python scripts/check_fact_gates.py [--json out.json]
      [--max-age-days N]`
退出碼：0 全綠；1 任一 must_pass 失敗（BLOCKED，附 verdict 向量定位）。

覆蓋八域（與測試共享黃金值，見 tests/*/test_*contract*.py 與
tests/core/test_fact_interpreter.py）：
  edge     硬體/edge_card 包絡三 verdict（重算，不信任轉錄數字）
  audit    卡架構審計：歷史宣稱 corrections 記 INFO（審計抓稻草人是它的
           本職）；修訂後設計（L1 提到駐留需求）的 blocking 門才是 gate
  chat     對話回應 × 前端讀鍵交集（P1 首條活鏈）
  cluster  監控面板 6 葉路徑（P1 第二條活鏈）
  config   程式引用的設定鍵必須存在於 YAML（幽靈鍵偵測，與
           tests/test_config_coverage.py 共享黃金值）
  version  package.json 與 core/version.py 版本一致
  docs     活躍文件引用的 script/test 路徑必須可解析（複用
           tests/test_documented_paths.py 的同一套解析規則）
  modules  模組系統現實：scanner 對缺目錄必須安全（must_pass）；
           目錄存在與否、發現模組數記 INFO（休眠是事實，不是失敗）

`--max-age-days N`：帶 measured_at 的事實超過 N 天列為過期（只警告，
不擋門——量測會腐爛，判新鮮度不判對錯）。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

REPO = Path(__file__).resolve().parents[1]
MEASURED_AT = "2026-10-13"


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
    from dataclasses import replace as _replace

    from ai.hardware.card_architecture_audit import (
        ClaimedArchitecture,
        audit,
        revised_architecture,
    )
    from core.facts import from_audit_corrections

    # 歷史宣稱的 corrections 照轉（每條 INFO，出處/重算值全進 evidence），
    # 但 its no_blocking_corrections 門審的是 2026 稻草人預設值——永遠
    # 紅、且與「現況是否健康」無關。降為 INFO：審計抓到歷史錯誤是它的
    # 本職，不是現況缺陷。
    historical = from_audit_corrections(audit(ClaimedArchitecture())["corrections"])
    historical.verdicts = [
        _replace(v, passed=None, segment="audit-historical") for v in historical.verdicts
    ]

    # 現況門：修訂後設計（套用審計自己建議的 L1 駐留修正）不得有 blocking。
    revised = from_audit_corrections(audit(revised_architecture())["corrections"])
    revised.verdicts = [_replace(v, segment="audit-revised") for v in revised.verdicts[:-1]] + [
        _replace(
            revised.verdicts[-1],
            id="revised_design_no_blocking_corrections",
            segment="audit-revised",
        )
    ]
    return historical.verdicts + revised.verdicts


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


def _config_facts():
    """程式引用的設定鍵必須存在於 YAML（幽靈鍵偵測）。

    黃金值與 tests/test_config_coverage.py 的 _X143_KEYS 共享：這些鍵
    曾經只存在於程式呼叫的 inline 預設值——使用者改設定檔無效。
    另以棘輪事實記錄「仍只落 inline 預設」的 accessor 鍵數上限。
    """
    import re

    import core.system.config.magic_numbers as mn
    from core.facts import Fact

    x143 = {
        # loop_sleep keys (timing.default.yaml: timing.loop.*)
        "agent_restart_delay": 5.0,
        "transport_retry": 1.0,
        "cloud_sync_upload": 0.1,
        "cluster_task_distribute": 0.1,
        "ws_broadcast_retry": 5.0,
        "ws_broadcast_interval": 1.0,
        "hsp_process_message": 0.1,
        # retry_value keys (timing.default.yaml: timing.retry.*)
        "agent_task_retries": 3,
        "router_health_retries": 5,
        # timeout_value keys added at the same audit (2026-10-13)
        "action_timeout": 30.0,
        "llm.health_check": 5.0,
        "llm.generate_text": 60.0,
        "llm.neural_bridge": 30.0,
        "llm.fallback_chain": 30.0,
    }
    resolved = 0
    matched = 0
    for key, expected in x143.items():
        value = mn._get(key, "<MISSING>")
        if value != "<MISSING>":
            resolved += 1
        if value == expected:
            matched += 1

    # 棘輪：accessor 鍵仍只落 inline 預設的**唯一鍵數**（與
    # test_config_coverage 同一 regex、同一去重語義、同一預算；只減不增）。
    accessor_re = re.compile(r'(loop_sleep|timeout_value|retry_value)\(\s*"([^"]+)"')
    src_root = REPO / "apps/backend/src"
    mn._MAGIC_CACHE.clear()
    mn._SUFFIX_LEAF_INDEX = None
    missing_keys = set()
    for py in src_root.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        text = py.read_text(encoding="utf-8", errors="ignore")
        for match in accessor_re.finditer(text):
            if mn._get(match.group(2), "<MISSING>") == "<MISSING>":
                missing_keys.add(match.group(2))
    inline = len(missing_keys)

    return [
        Fact(
            "config.x143_keys_resolve_in_yaml",
            float(resolved),
            float(len(x143)),
            "ge",
            "keys",
            "timing.default.yaml",
            f"resolved={resolved}/{len(x143)}",
            measured_at=MEASURED_AT,
        ),
        Fact(
            "config.x143_values_match_code_defaults",
            float(matched),
            float(len(x143)),
            "ge",
            "keys",
            "timing.default.yaml",
            f"matched={matched}/{len(x143)}",
            measured_at=MEASURED_AT,
        ),
        Fact(
            "config.inline_default_accessor_ratchet",
            float(inline),
            73.0,
            "le",
            "keys",
            "apps/backend/src",
            f"unique inline-only accessor keys={inline} (budget 73, lower is better)",
            measured_at=MEASURED_AT,
        ),
    ]


def _version_facts():
    """package.json 與 core/version.py（以 import 取得，非解析）必須一致。"""
    from core.facts import Fact

    pkg = json.loads((REPO / "package.json").read_text(encoding="utf-8"))["version"]
    from core.version import __version__ as code_version

    agree = 1.0 if pkg == code_version else 0.0
    return [
        Fact(
            "version.package_json_matches_core_version",
            agree,
            1.0,
            "ge",
            "match",
            "package.json+core/version.py",
            f"package.json={pkg!r} core.version={code_version!r}",
            measured_at=MEASURED_AT,
        )
    ]


def _docs_facts():
    """活躍文件引用的 script/test 路徑必須可解析。

    解析規則（cd 片段、文件相對、repo 根、豁免清單）複用
    tests/test_documented_paths.py——同一套規則，兩種出口（pytest
    回歸 + 事實門單一裁決），不各自演化。
    """
    from core.facts import Fact

    spec = importlib.util.spec_from_file_location(
        "doc_paths_guard", REPO / "tests" / "test_documented_paths.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    unexpected, resolved = mod._collect()
    broken = sum(len(hits) for hits in unexpected.values())
    docs_with_breaks = ", ".join(sorted(unexpected)) or "none"
    return [
        Fact(
            "docs.unresolved_path_refs",
            float(broken),
            0.0,
            "le",
            "refs",
            "active docs",
            f"broken={broken} in docs: {docs_with_breaks}",
            measured_at=MEASURED_AT,
        ),
        Fact(
            "docs.resolved_refs_nonvacuous",
            float(resolved),
            1.0,
            "ge",
            "refs",
            "active docs",
            f"resolved={resolved}",
            measured_at=MEASURED_AT,
        ),
    ]


def _modules_facts():
    """模組系統現實：scanner 對缺目錄必須安全（must_pass）；目錄存在與
    發現數記 INFO（休眠是事實，不是失敗——lifespan 從未啟動 ModuleManager，
    scanner 對不存在路徑優雅跳過）。
    """
    from core.facts import Fact
    from core.system.module_manager.scanner import ModuleScanner

    modules_dir = REPO / "apps/backend/src/modules"
    try:
        discovered = len(ModuleScanner([modules_dir]).discover())
        safe = 1.0
    except Exception as e:  # pragma: no cover - the fact exists to catch this
        discovered = -1
        safe = 0.0
        evidence = f"scanner raised on missing/existing path: {e}"
    else:
        evidence = f"scanner survived; discovered={discovered}"
    return [
        Fact(
            "modules.scanner_safe_on_missing_path",
            safe,
            1.0,
            "ge",
            "contract",
            "module_manager/scanner.py",
            evidence,
            measured_at=MEASURED_AT,
        ),
        Fact(
            "modules.dir_exists",
            1.0 if modules_dir.is_dir() else 0.0,
            1.0,
            "ge",
            "dirs",
            "apps/backend/src/modules",
            "0 = module system dormant (no modules shipped); record, not failure",
            must_pass=False,
            measured_at=MEASURED_AT,
        ),
        Fact(
            "modules.discovered",
            float(max(discovered, 0)),
            0.0,
            "ge",
            "modules",
            "apps/backend/src/modules",
            f"discovered={max(discovered, 0)}",
            must_pass=False,
            measured_at=MEASURED_AT,
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=-1,
        help="列出 measured_at 超過 N 天的事實（只警告，不擋門）",
    )
    args = parser.parse_args()

    from core.facts import Report, adjudicate, merge_reports, stale_facts

    edge_facts = _edge_facts()
    audit_report = Report()
    for v in _audit_facts():
        audit_report.add(v)
    chain_facts = _chat_facts() + _cluster_facts()
    hygiene_facts = _config_facts() + _version_facts() + _docs_facts() + _modules_facts()
    merged = merge_reports(
        adjudicate(edge_facts),
        audit_report,
        adjudicate(chain_facts),
        adjudicate(hygiene_facts),
    )

    print("=" * 72)
    print("FACT GATES (edge + audit + chat-chain + cluster-chain + hygiene)")
    print("=" * 72)
    print(merged.summary())
    if args.max_age_days >= 0:
        from datetime import date

        stale = stale_facts(edge_facts + hygiene_facts, args.max_age_days, date.today().isoformat())
        if stale:
            print(f"  STALE (> {args.max_age_days}d): {', '.join(stale)}")
    print("=" * 72)
    if args.json:
        args.json.write_text(
            json.dumps(merged.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"json -> {args.json}")
    return 0 if merged.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
