#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""全倉單一檢查門：事實（facts）+ 定義（definitions），一次跑完、一次裁決。

單一工具的意義：多個小工具會「不打開就被掠過」——所有檢查集中在這一個
入口，跑一次即全部被檢視（含定義稽核，2026-10-14 自
scripts/gen_definitions_audit.py 併入）。

用法: `.venv/bin/python scripts/check_fact_gates.py [--json out.json]
      [--max-age-days N] [--write-definitions-audit [PATH]]`

退出碼：0 全綠；1 任一 must_pass 失敗（BLOCKED，附 verdict 向量定位）。

覆蓋九域（與測試共享黃金值，見 tests/*/test_*contract*.py 與
tests/core/test_fact_interpreter.py）：
  edge        硬體/edge_card 包絡三 verdict（重算，不信任轉錄數字）
  audit       卡架構審計：歷史宣稱 corrections 記 INFO（審計抓稻草人是它的
              本職）；修訂後設計（L1 提到駐留需求）的 blocking 門才是 gate
  chat        對話回應 × 前端讀鍵交集（P1 首條活鏈）
  cluster     監控面板 6 葉路徑（P1 第二條活鏈）
  config      程式引用的設定鍵必須存在於 YAML（幽靈鍵偵測，與
              tests/test_config_coverage.py 共享黃金值）
  version     package.json 與 core/version.py 版本一致
  docs        活躍文件引用的 script/test 路徑必須可解析（複用
              tests/test_documented_paths.py 的同一套解析規則）
  modules     模組系統現實：scanner 對缺目錄必須安全（must_pass）；
              目錄存在與否、發現模組數記 INFO（休眠是事實，不是失敗）
  definitions 定義稽核（四桶：未定義／定義有誤／定義差／定義合理）：
              i18n prompt 鍵、magic_numbers 鍵、StateMatrix 槽（Python
              DEFAULT_DIMENSIONS / matrix.default.yaml / JS 鏡像三源對齊）、
              CNS 事件、GLOSSARY 數值宣稱、influence_map、get_parameter、
              ResponseCategory — 未定義=0、三源分歧=0、死鍵=0、錯軸=0
              為 must_pass；孤兒事件 21 為棘輪（只減不增，新增即擋門）；
              多重釋義（定義差）記 INFO（記錄，不是缺陷）

`--write-definitions-audit [PATH]`：用同一次掃描寫出定義稽核 MD 四桶報告
（預設 docs/06-project-management/fixes/DEFINITIONS_AUDIT_2026-10-14.md；
寫出後自動跑 prettier --write）。

`--max-age-days N`：帶 measured_at 的事實超過 N 天列為過期（只警告，
不擋門——量測會腐爛，判新鮮度不判對錯）。
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "apps/backend/src"
TESTS = REPO / "tests"
AXES = ("alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta")
MEASURED_AT = "2026-10-13"
DEFS_AUDIT_MD = "docs/06-project-management/fixes/DEFINITIONS_AUDIT_2026-10-14.md"


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


# ===========================================================================
# 定義稽核（原 scripts/gen_definitions_audit.py，2026-10-14 併入本單一工具）
# ===========================================================================
# ---------------------------------------------------------------------------
# Human/AI perspective notes for multi-interpretation terms (定義差 bucket).
# Keys are auto-detected; values give the two sanctioned readings.
# ---------------------------------------------------------------------------
TERM_PERSPECTIVES: Dict[str, Dict[str, str]] = {
    "trust": {
        "sources": "γ 軸槽（情感信任）/ δ 軸槽（社交信任）/ influence_map 類型 / EmotionType.TRUST",
        "human": "感覺層：相信對方、放心交托（情感態）",
        "ai": "機制層：γ=主觀可信度訊號；δ=關係黏著度；influence=PAD 漂移量",
    },
    "complexity": {
        "sources": "ε 軸槽（問題複雜度）/ θ 軸槽（認知複雜度）/ ripple schema",
        "human": "事情有多難懂",
        "ai": "ε=輸入結構度量；θ=自身認知負荷——同一詞、兩個測量點",
    },
    "stress": {
        "sources": "influence_map 類型 / ac.stress_cap 鍵 / heartbeat 健康 / 生理 cortisol",
        "human": "感到緊繃、有壓力",
        "ai": "至少 3 個獨立機制各自記 stress，無共享狀態",
    },
    "engagement": {
        "sources": "δ 軸槽 / resp_msg_ratio 互動回饋 / avg_engagement 聚合",
        "human": "對方有多投入這段互動",
        "ai": "δ=關係參與度狀態；回饋比=訊號計算——狀態 vs 計量",
    },
    "memory": {
        "sources": "zeta memory_depth 槽 / HAM memory / vector store / dialogue context",
        "human": "記得什麼",
        "ai": "4 個不互通的儲存子系統各有一套 memory 語義",
    },
    "attention": {
        "sources": "δ 軸槽 / mf_attention_weight（生命強度公式）/ 注意力機制",
        "human": "注意力放在哪",
        "ai": "δ=社交關注狀態；公式權重=喚醒係數——同名不同量綱",
    },
    "calm": {
        "sources": "γ 軸槽（本次補齊）/ influence_map 類型 (0.1,-0.2,0) / 失控優先級 calm routing",
        "human": "平靜",
        "ai": "γ 槽=狀態量；influence=事件量；routing mode=行為策略",
    },
    "identity": {
        "sources": "zeta identity_continuity 槽 / soul_core IDENTITY / protocols identity_id",
        "human": "我是誰",
        "ai": "zeta=敘事連續度量；soul_core=枚舉；identity_id=實體編號",
    },
}

# Fix log rendered into the MD (updated as fixes land).
FIX_NOTES: List[Tuple[str, str]] = [
    (
        "core/engine/state_matrix.py",
        "DEFAULT_DIMENSIONS（live 定義源）補齊 11 個使用中未定義槽："
        "alpha+=vitality/tension、beta+=clarity/creativity、gamma+=love/calm、"
        "delta+=engagement/intimacy、theta+=doubt/caution/self_reflection/meta_accuracy"
        "（與 JS 鏡像同步）、zeta 改名 identity→identity_continuity (0.75)、"
        "memory_access→memory_depth (0.6)（舊名零讀寫者，新名為座標讀取器/影響規則/JS 正式名）",
    ),
    (
        "core/engine/state_matrix_types.py",
        "① 座標 epsilon 雙讀 abstraction_level|abstraction 簡化為 abstraction"
        "（abstraction_level 為 YAML 草稿槽、epsilon 從未持有，雙讀永遠落 fallback）；"
        "② DimensionState.update() 靜默丟鍵改 logger.warning（未定義槽不再無聲消失）",
    ),
    (
        "ai/alignment/emotion_system.py",
        "influence_map 補 trust: (0.3, -0.1, 0.1) — apply_influence("
        "'interaction_feedback', 'trust', …) 先前查無此鍵 → PAD 漂移靜默 no-op；"
        "係數為標明的設計者 heuristic（正效價/低喚醒/微支配，同 oxytocin 型）",
    ),
    (
        "configs/standard/matrix/matrix.default.yaml",
        "死配置對齊 live：gamma 補 disgust/surprise、epsilon complexity 0.0→0.5、"
        "theta 換為正式 12 槽（棄 abstraction_level）、zeta temporal 0.8→0.5 / "
        "narrative 0.7→0.5、cn_name 全數對齊 DEFAULT。weight/coordinate/anchor "
        "維持原草稿值並在檔頭標明（接線＝行為變更，需人工定奪）",
    ),
    (
        "packages/shared-js/js/state-matrix.js",
        "θ 軸補 6 槽（novelty/complexity/ambiguity/dimension_fit/creation_urge/"
        "correction_urge）使後端 θ 狀態可同步進鏡像；epsilon complexity 0.0→0.5；"
        "zeta memory_depth 0.3→0.6、identity_continuity 0.5→0.75；cn_name 對齊；"
        "修正檔頭錯誤標頭（γ 原標『物理维度』、δ 原標『精神维度-mood/…』與實際槽不符）"
        "（desktop 副本由 sync_shared_js.py 同步）",
    ),
    (
        "docs/00-overview/GLOSSARY.md",
        "4 處失準數值改為實測：ED3N ~5,500→~7,500 lines (26 files)、"
        "GARDEN ~2,600→~6,000 lines (9 files)、GVV 14/~62→16 files/85 tests、"
        "StateMatrix 1,244 行/6 軸→1,751 行/7 軸 αβγδεθζ；"
        "「8 軸尚未實作」改述為 ζ 已實作、η=Python 獨立子系統/JS 第 8 軸",
    ),
    (
        "core/i18n/locales/prompts.{zh-CN,en-US}.json",
        "移除 4 個零引用死定義：angela.planning_error / generation_error / "
        "decompose_prompt / integrate_prompt（94→90 鍵，雙語 parity 維持 0）",
    ),
    (
        "services/llm/prompt_builder.py",
        "angela.bio.uninitialized 定義接線：bio dict 為空時回傳該模板"
        "（原註冊+locale 皆有、零渲染 = 死定義；現為 1 註冊 + 1 呼叫）",
    ),
    (
        "tests/core/autonomous/test_state_matrix_adapter.py",
        "錯軸/不存在槽名改正：alpha.focus→energy、gamma.excitement→happiness、"
        "epsilon.awareness→logic、zeta.surprise→temporal_coherence；"
        "專屬 zeta 測試改 memory_depth；temporal 記錄 focus→energy"
        "（原資料示範錯誤定義）",
    ),
    (
        "tests/core/backbone/test_subscriptions.py",
        "domain→axis 寫入測試資料 focus@alpha 改為 focus@beta + energy@alpha"
        "（同步機制不變，測試資料不再示範錯軸定義）",
    ),
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def py_files(root: Path) -> List[Path]:
    return sorted(root.rglob("*.py"))


def ast_literal_assign(src: str, name: str) -> Optional[Any]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in ast.walk(tree):
        targets: List[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id == name and node.value is not None:
                try:
                    return ast.literal_eval(node.value)
                except (ValueError, SyntaxError):
                    return None
    return None


def brace_block(src: str, start: int) -> str:
    """Return the {...} block whose '{' is at/after index start."""
    i = src.find("{", start)
    if i < 0:
        return ""
    depth = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i : j + 1]
    return src[i:]


def section(text: str, heading: str) -> str:
    """Text of markdown section starting at `heading` line (## level)."""
    m = re.search(rf"^{re.escape(heading)}.*$", text, re.M)
    if not m:
        return ""
    nxt = re.search(r"^##\s", text[m.end() :], re.M)
    end = m.end() + (nxt.start() if nxt else len(text))
    return text[m.start() : end]


# ---------------------------------------------------------------------------
# A. i18n prompt keys
# ---------------------------------------------------------------------------
def audit_prompt_keys() -> Dict[str, Any]:
    used: Set[str] = set()
    for p in py_files(SRC):
        for m in re.finditer(r"(?<![A-Za-z_])prompt\(\s*f?(['\"])(.*?)\1", read(p), re.S):
            key = m.group(2)
            if "{" not in key:
                used.add(key)
    zh = json.loads(read(SRC / "core/i18n/locales/prompts.zh-TW.json"))
    en = json.loads(read(SRC / "core/i18n/locales/prompts.en-US.json"))

    def flatten(d: Dict[str, Any], prefix: str = "") -> Set[str]:
        out: Set[str] = set()
        for k, v in d.items():
            full = f"{prefix}{k}"
            if isinstance(v, dict):
                out |= flatten(v, full + ".")
            else:
                out.add(full)
        return out

    zh_keys, en_keys = flatten(zh), flatten(en)
    # Any literal occurrence of the key anywhere in src counts as referenced.
    all_src = "\n".join(read(p) for p in py_files(SRC))

    def refs(k: str) -> int:
        return all_src.count(f'"{k}"') + all_src.count(f"'{k}'")

    truly_unused = sorted(k for k in zh_keys if k not in used and refs(k) <= 1)
    referenced = {k for k in zh_keys if k in used or refs(k) >= 2}
    return {
        "used": used,
        "zh": zh_keys,
        "en": en_keys,
        "parity_diff": (zh_keys ^ en_keys),
        "undefined": sorted(used - zh_keys),
        "never_referenced": truly_unused,
        "count_used": len(used),
        "count_zh": len(zh_keys),
        "count_en": len(en_keys),
        "count_referenced": len(referenced),
    }


# ---------------------------------------------------------------------------
# B. magic_numbers keys
# ---------------------------------------------------------------------------
def audit_magic_keys() -> Dict[str, Any]:
    mn_path = SRC / "core/system/config/magic_numbers.py"
    mn_src = read(mn_path)
    tree = ast.parse(mn_src)
    accessors: Set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            body_src = ast.get_source_segment(mn_src, node) or ""
            if "_get(" in body_src or "_get_compute_config(" in body_src:
                accessors.add(node.name)
    call_re = re.compile(r"\b(" + "|".join(sorted(accessors)) + r")\(\s*['\"]([^'\"]+)['\"]")
    used: Set[str] = set()
    for p in py_files(SRC):
        for m in call_re.finditer(read(p)):
            used.add(m.group(2))
    resolved: Set[str] = set()
    runtime_ok = False
    try:
        sys.path.insert(0, str(SRC))
        from core.system.config import magic_numbers as mn  # type: ignore

        sentinel = object()
        for k in used:
            if mn._get(k, sentinel) is not sentinel:
                resolved.add(k)
        runtime_ok = True
    except Exception as exc:  # pragma: no cover - env-dependent
        print(f"[B] runtime resolve unavailable: {exc}")
    return {
        "accessors": sorted(accessors),
        "used": used,
        "resolved": resolved,
        "inline_only": sorted(used - resolved),
        "runtime_ok": runtime_ok,
    }


# ---------------------------------------------------------------------------
# C. StateMatrix slot definitions
# ---------------------------------------------------------------------------
def load_python_default() -> Dict[str, Any]:
    return ast_literal_assign(read(SRC / "core/engine/state_matrix.py"), "DEFAULT_DIMENSIONS") or {}


def load_yaml_dims() -> Dict[str, Any]:
    yp = REPO / "apps/backend/configs/standard/matrix/matrix.default.yaml"
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(read(yp)) or {}
        return data.get("dimensions", {}) or {}
    except Exception as exc:  # pragma: no cover
        print(f"[C] yaml load failed: {exc}")
        return {}


def load_js_axes() -> Dict[str, Dict[str, Any]]:
    js_path = REPO / "packages/shared-js/js/state-matrix.js"
    src = read(js_path)
    axes: Dict[str, Dict[str, Any]] = {}
    for name in AXES + ("eta",):
        m = re.search(rf"this\.{name}\s*=\s*\{{", src)
        if not m:
            continue
        block = brace_block(src, m.start())
        vm = re.search(r"values:\s*\{", block)
        vals: Dict[str, float] = {}
        if vm:
            vblock = brace_block(block, vm.start())
            for km in re.finditer(r"(\w+)\s*:\s*(-?\d+(?:\.\d+)?)", vblock):
                vals[km.group(1)] = float(km.group(2))
        cn = re.search(r"cn_name:\s*'([^']+)'", block)
        w = re.search(rf"config\.{name}_weight\s*\|\|\s*([\d.]+)", block)
        axes[name] = {
            "initial_values": vals,
            "cn_name": cn.group(1) if cn else "",
            "weight": float(w.group(1)) if w else 1.0,
        }
    return axes


def collect_usage(src_root: Path) -> Dict[str, Any]:
    upd_re = re.compile(r"\bupdate_(alpha|beta|gamma|delta|epsilon|theta|zeta)\(\s*([^)]*)\)")
    val_re = re.compile(r"\.(\w+)\.values\[\s*['\"](\w+)['\"]\s*\]")
    valget_re = re.compile(r"\.(\w+)\.values\.get\(\s*['\"](\w+)['\"]")
    upd_kwargs: Set[str] = set()
    val_keys: Set[str] = set()
    val_pairs: List[Tuple[str, str]] = []
    dynamic = 0
    for p in py_files(src_root):
        text = read(p)
        for m in upd_re.finditer(text):
            args = m.group(2)
            if "{" in args or "**" in args:
                dynamic += 1
                continue
            for km in re.finditer(r"(\w+)\s*=", args):
                upd_kwargs.add(km.group(1))
        for m in val_re.finditer(text):
            val_keys.add(m.group(2))
            val_pairs.append((m.group(1), m.group(2)))
        for m in valget_re.finditer(text):
            val_keys.add(m.group(2))
            val_pairs.append((m.group(1), m.group(2)))
    # coordinate readers inside state_matrix_types.compute_coordinate
    coord_keys: Set[str] = set()
    smt = read(SRC / "core/engine/state_matrix_types.py")
    for m in re.finditer(r"\bv\.get\(\s*['\"](\w+)['\"]", smt):
        coord_keys.add(m.group(1))
    axis_schema = ast_literal_assign(read(SRC / "ai/memory/domain_ripple.py"), "_AXIS_SCHEMA") or {}
    cog_map = (
        ast_literal_assign(read(SRC / "ai/memory/domain_ripple.py"), "_COGNITION_DELTA_MAP") or {}
    )
    influence_rules = (
        ast_literal_assign(read(SRC / "core/engine/influence_applicator.py"), "INFLUENCE_RULES")
        or {}
    )
    inf_src_keys: Set[str] = set()
    inf_tgt_keys: Set[str] = set()
    for _src, targets in (influence_rules or {}).items():
        for _tgt, rules in (targets or {}).items():
            for rule in rules or []:
                inf_src_keys.add(rule[0])
                inf_tgt_keys.add(rule[1])
    schema_keys: Set[str] = set()
    for _ax, ks in (axis_schema or {}).items():
        schema_keys |= set(ks)
    # wrong-axis placements in test parametrize tuples — only meaningful for
    # tests that drive the StateMatrix itself (timeline/backbone axis-pair
    # tuples are a different definition domain).
    misplaced: List[Tuple[str, str, str]] = []
    for p in py_files(TESTS):
        text = read(p)
        if "StateMatrix4D" not in text and "StateMatrixAdapter" not in text:
            continue
        for m in re.finditer(
            r'\(\s*"(alpha|beta|gamma|delta|epsilon|theta|zeta)"\s*,\s*"(\w+)"\s*,',
            text,
        ):
            if m.group(2) in AXES:
                continue  # axis tuple (…), not a (axis, slot) pair
            misplaced.append((str(p.relative_to(REPO)), m.group(1), m.group(2)))
    misplaced = sorted(set(misplaced))
    return {
        "update_kwargs": upd_kwargs,
        "value_keys": val_keys,
        "value_pairs": val_pairs,
        "coord_keys": coord_keys,
        "axis_schema": axis_schema,
        "schema_keys": schema_keys,
        "influence_rules": influence_rules,
        "inf_src": inf_src_keys,
        "inf_tgt": inf_tgt_keys,
        "cog_map": cog_map,
        "dynamic_updates": dynamic,
        "misplaced": misplaced,
    }


def audit_slots() -> Dict[str, Any]:
    default = load_python_default()
    yaml_dims = load_yaml_dims()
    js_axes = load_js_axes()
    usage = collect_usage(SRC)
    default_keys: Dict[str, Set[str]] = {
        ax: set((d.get("initial_values") or {})) for ax, d in default.items()
    }
    all_default: Set[str] = set().union(*default_keys.values()) if default_keys else set()
    # which axis a slot belongs to (per definition)
    slot_axis: Dict[str, Set[str]] = {}
    for ax, ks in default_keys.items():
        for k in ks:
            slot_axis.setdefault(k, set()).add(ax)

    used_union = (
        usage["update_kwargs"]
        | usage["value_keys"]
        | usage["coord_keys"]
        | usage["schema_keys"]
        | usage["inf_src"]
        | usage["inf_tgt"]
        | {v[1] for v in usage["cog_map"].values() if isinstance(v, (tuple, list)) and len(v) > 1}
    )
    undefined = sorted(k for k in used_union if k not in all_default)
    never_used = sorted(k for k in all_default if k not in used_union)

    # YAML vs Python divergence
    yaml_diffs: List[str] = []
    for ax in AXES:
        yd = (yaml_dims.get(ax) or {}).get("initial_values") or {}
        pd = default_keys.get(ax, set())
        if set(yd) != pd:
            yaml_diffs.append(
                f"{ax}: YAML-only={sorted(set(yd) - pd)} Python-only={sorted(pd - set(yd))}"
            )
        for k in set(yd) & pd:
            yv = yd[k]
            pv = (default[ax]["initial_values"] or {})[k]
            if abs(float(yv) - float(pv)) > 1e-9:
                yaml_diffs.append(f"{ax}.{k}: YAML={yv} Python={pv}")
        ycn = (yaml_dims.get(ax) or {}).get("cn_name")
        pcn = (default.get(ax) or {}).get("cn_name")
        if ycn and pcn and ycn != pcn:
            yaml_diffs.append(f"{ax}: cn_name YAML={ycn!r} Python={pcn!r}")
    for ax in yaml_dims:
        if ax not in default:
            yaml_diffs.append(f"{ax}: exists only in YAML")

    # JS vs Python divergence (eta handled separately)
    js_diffs: List[str] = []
    for ax in AXES:
        jd = (js_axes.get(ax) or {}).get("initial_values") or {}
        pd = default_keys.get(ax, set())
        if set(jd) != pd:
            js_diffs.append(
                f"{ax}: JS-only={sorted(set(jd) - pd)} Python-only={sorted(pd - set(jd))}"
            )
        for k in set(jd) & pd:
            jv = jd[k]
            pv = (default[ax]["initial_values"] or {})[k]
            if abs(float(jv) - float(pv)) > 1e-9:
                js_diffs.append(f"{ax}.{k}: JS={jv} Python={pv}")
        jcn = (js_axes.get(ax) or {}).get("cn_name")
        pcn = (default.get(ax) or {}).get("cn_name")
        if jcn and pcn and jcn != pcn:
            js_diffs.append(f"{ax}: cn_name JS={jcn!r} Python={pcn!r}")
    js_extra_axes = [a for a in js_axes if a not in default]

    # wrong-axis receiver pairs in src (receiver axis vs slot axis)
    wrong_receiver: List[str] = []
    for recv, key in usage["value_pairs"]:
        if key in slot_axis and recv in slot_axis[key] or recv not in AXES:
            continue
        wrong_receiver.append(
            f"{recv}.values[{key!r}] (slot defined on {sorted(slot_axis.get(key, []))})"
        )

    # cross-axis duplicate slot names (multi-interpretation)
    dup_slots = {k: sorted(v) for k, v in slot_axis.items() if len(v) > 1}

    # wrong-axis test placements
    bad_test_fields = [
        (f, ax, key) for f, ax, key in usage["misplaced"] if key not in default_keys.get(ax, set())
    ]

    return {
        "default": default,
        "default_keys": default_keys,
        "yaml": yaml_dims,
        "js": js_axes,
        "usage": usage,
        "undefined": undefined,
        "never_used": never_used,
        "yaml_diffs": yaml_diffs,
        "js_diffs": js_diffs,
        "js_extra_axes": js_extra_axes,
        "wrong_receiver": sorted(set(wrong_receiver)),
        "dup_slots": dup_slots,
        "bad_test_fields": bad_test_fields,
    }


# ---------------------------------------------------------------------------
# D. events
# ---------------------------------------------------------------------------
def _telemetry_allowlist() -> Dict[str, str]:
    """The documented telemetry-only events (no in-process consumer by design).

    Read from the codebase (core/system/state_store/telemetry_events.py) so
    the reviewed list lives with the code, not in this script.
    """
    path = SRC / "core" / "system" / "state_store" / "telemetry_events.py"
    if not path.exists():
        return {}
    text = read(path)
    return dict(re.findall(r'^\s*"([^"]+)":\s*"([^"]*)"', text, re.M))


def audit_events() -> Dict[str, Any]:
    call_re = re.compile(
        r"\b(emit_event|subscribe_event)\(\s*(?:['\"]([^'\"]+)['\"]|([A-Z][A-Z0-9_]*))"
    )
    const_re = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=\s*['\"]([^'\"]+)['\"]", re.M)
    emitted: Set[str] = set()
    subscribed: Set[str] = set()
    for p in py_files(SRC):
        text = read(p)
        consts = dict(const_re.findall(text))
        for m in call_re.finditer(text):
            name = m.group(2) or consts.get(m.group(3) or "", None)
            if not name:
                continue
            (emitted if m.group(1) == "emit_event" else subscribed).add(name)
    allowlist = _telemetry_allowlist()
    # A stale allowlist entry (an event that is no longer emitted) is a
    # defect in the list, not a silent no-op.
    stale_allowlist = sorted(set(allowlist) - emitted)
    unexplained = sorted(emitted - subscribed - set(allowlist))
    return {
        "emitted": sorted(emitted),
        "subscribed": sorted(subscribed),
        "orphans": unexplained,
        "telemetry_only": sorted(set(allowlist) & emitted),
        "stale_allowlist": stale_allowlist,
        "never_emitted": sorted(subscribed - emitted),
    }


# ---------------------------------------------------------------------------
# E. GLOSSARY claims
# ---------------------------------------------------------------------------
def count_lines(paths: List[Path]) -> int:
    n = 0
    for p in paths:
        try:
            n += len(read(p).splitlines())
        except OSError:
            pass
    return n


def audit_glossary() -> List[Dict[str, Any]]:
    gpath = REPO / "docs/00-overview/GLOSSARY.md"
    text = read(gpath)

    def measure_dir(d: Path) -> Tuple[int, int]:
        files = sorted(d.rglob("*.py"))
        return len(files), count_lines(files)

    def measure_tests(d: Path) -> int:
        n = 0
        for p in sorted(d.rglob("test_*.py")):
            n += len(re.findall(r"(?:async )?def test_", read(p)))
        return n

    ed3n_files, ed3n_lines = measure_dir(SRC / "ai/ed3n")
    garden_files, garden_lines = measure_dir(SRC / "ai/garden")
    gvv_files = len(sorted((SRC / "ai/multimodal/primitives").rglob("*.py")))
    gvv_tests = measure_tests(TESTS / "ai/multimodal/primitives")
    sm_lines = len(read(SRC / "core/engine/state_matrix.py").splitlines())
    default = load_python_default()

    checks: List[Dict[str, Any]] = []

    def add(name: str, pattern: str, measured: Any, sec_hint: str = "") -> None:
        hay = section(text, f"### {sec_hint}") if sec_hint else text
        hay_norm = re.sub(r"\s+", " ", hay)
        text_norm = re.sub(r"\s+", " ", text)
        m = re.search(pattern, hay_norm) or re.search(pattern, text_norm)
        claim = m.group(0) if m else "(claim not found)"
        nums = [g for g in (m.groups() if m else ()) if g] if m else []
        ok = False
        if m:
            try:
                claimed = [int(x.replace(",", "")) for x in nums]
                mv = [int(measured)] if isinstance(measured, int) else list(measured)
                if len(claimed) == len(mv):
                    if "~" in claim:
                        # approximate claim (e.g. "~7,500 lines") → 5% tolerance
                        ok = all(abs(c - v) <= max(1, int(c * 0.05)) for c, v in zip(claimed, mv))
                    else:
                        ok = claimed == mv
            except ValueError:
                ok = False
        checks.append({"name": name, "claim": claim, "measured": measured, "ok": ok})

    add("ED3N 規模", r"~?([\d,]+) lines across (\d+) files", (ed3n_lines, ed3n_files), "ED3N")
    add(
        "GARDEN 規模",
        r"~?([\d,]+) lines across (\d+) files",
        (garden_lines, garden_files),
        "GARDEN",
    )
    add("GVV 規模", r"(\d+) source files, ~?(\d+) tests", (gvv_files, gvv_tests), "GVV")
    add(
        "StateMatrix 行數",
        r"`core/engine/state_matrix\.py`, ([\d,]+) 行",
        sm_lines,
        "8D State Matrix (理想目標) / StateMatrix4D (實際)",
    )
    add(
        "StateMatrix 軸數",
        r"(\d+) 軸 αβγδεθ",
        len(default),
        "8D State Matrix (理想目標) / StateMatrix4D (實際)",
    )
    return checks


# ---------------------------------------------------------------------------
# F. multi-source term inventory
# ---------------------------------------------------------------------------
def audit_terms(slot_audit: Dict[str, Any]) -> List[Dict[str, str]]:
    glossary = read(REPO / "docs/00-overview/GLOSSARY.md")
    default = slot_audit["default"]
    all_slots = (
        set().union(*slot_audit["default_keys"].values()) if slot_audit["default_keys"] else set()
    )
    rows: List[Dict[str, str]] = []
    for term, meta in TERM_PERSPECTIVES.items():
        hits: List[str] = []
        if term in all_slots:
            axes = [ax for ax, ks in slot_audit["default_keys"].items() if term in ks]
            hits.append("StateMatrix 槽 @" + "/".join(axes))
        if re.search(rf"^### .*{re.escape(term)}", glossary, re.M | re.I):
            hits.append("GLOSSARY 條目")
        map_keys = ast_literal_assign(read(SRC / "ai/alignment/emotion_system.py"), "influence_map")
        rows.append(
            {
                "term": term,
                "sources": meta["sources"] + ("；" + "; ".join(hits) if hits else ""),
                "human": meta["human"],
                "ai": meta["ai"],
            }
        )
    # zeta duplicate detection is covered by dup_slots elsewhere
    return rows


# ---------------------------------------------------------------------------
# G. explicit markers + sanity checks
# ---------------------------------------------------------------------------
def audit_markers_and_sanity() -> Dict[str, Any]:
    markers: List[str] = []
    for p in py_files(SRC):
        for i, line in enumerate(read(p).splitlines(), 1):
            if "定義（" in line or "Definition:" in line:
                markers.append(f"{p.relative_to(REPO)}:{i}")
    # get_parameter
    thresholds = (
        ast_literal_assign(read(SRC / "core/life/dynamic_parameters.py"), "_DEFAULT_THRESHOLDS")
        or {}
    )
    param_calls: Set[str] = set()
    for p in py_files(SRC):
        for m in re.finditer(r"get_parameter\(\s*['\"](\w+)['\"]", read(p)):
            param_calls.add(m.group(1))
    param_missing = sorted(param_calls - set(thresholds))
    # influence_map
    inf_map = (
        ast_literal_assign(read(SRC / "ai/alignment/emotion_system.py"), "influence_map") or {}
    )
    call_types: Set[str] = set()
    for p in py_files(SRC):
        for m in re.finditer(
            r"apply_influence\(\s*['\"][^'\"]+['\"]\s*,\s*['\"](\w+)['\"]", read(p)
        ):
            call_types.add(m.group(1))
    inf_missing = sorted(call_types - set(inf_map))
    inf_unused = sorted(set(inf_map) - call_types)
    # ResponseCategory
    rc: Dict[str, Any] = {"found": False}
    rc_file = None
    for p in py_files(SRC):
        if re.search(r"class ResponseCategory\(", read(p)):
            rc_file = p
            break
    if rc_file:
        tree = ast.parse(read(rc_file))
        vals: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "ResponseCategory":
                for st in node.body:
                    if isinstance(st, ast.Assign):
                        for t in st.targets:
                            if isinstance(t, ast.Name):
                                vals.add(t.id)
        rc = {"found": True, "file": str(rc_file.relative_to(REPO)), "values": vals}
    # template categories (only the "category" field — "type" is a different axis)
    tmpl_missing: List[str] = []
    tmpl = list(SRC.rglob("templates_data.json"))
    if tmpl and rc.get("values"):
        data = json.loads(read(tmpl[0]))
        cats: Set[str] = set()

        def walk(o: Any) -> None:
            if isinstance(o, dict):
                for k, v in o.items():
                    if k == "category" and isinstance(v, str):
                        cats.add(v.lower())
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(data)
        tmpl_missing = sorted(cats - {v.lower() for v in rc["values"]})
    return {
        "markers": markers,
        "param_missing": param_missing,
        "param_count": len(param_calls),
        "inf_missing": inf_missing,
        "inf_unused": inf_unused,
        "rc": rc,
        "tmpl_missing": tmpl_missing,
    }


# ---------------------------------------------------------------------------
# MD rendering
# ---------------------------------------------------------------------------
def render_md(
    prompt: Dict[str, Any],
    magic: Dict[str, Any],
    slots: Dict[str, Any],
    events: Dict[str, Any],
    gloss: List[Dict[str, Any]],
    terms: List[Dict[str, str]],
    sanity: Dict[str, Any],
) -> str:
    L: List[str] = []
    a = L.append
    a("# 定義稽核報告 (Definitions Audit) — 2026-10-14")
    a("")
    a(
        "> 本檔由 `scripts/check_fact_gates.py --write-definitions-audit` **自動掃描生成**，請勿手改內容本體。"
    )
    a(
        "> 重跑：`.venv/bin/python scripts/check_fact_gates.py --write-definitions-audit [<本檔>]` "
        "（寫出後自動跑 prettier --write，輸出即符合 CI 格式）"
    )
    a("> 分類：未定義／定義有誤／定義差（多重釋義：同對象於不同視角可多重詮釋）／定義合理。")
    a("")

    n_undef = len(slots["undefined"]) + len(prompt["undefined"]) + len(sanity["inf_missing"])
    n_wrong = (
        sum(1 for c in gloss if not c["ok"])
        + len(slots["yaml_diffs"])
        + len(slots["js_diffs"])
        + len(events["orphans"])
        + len(prompt["never_referenced"])
        + len(slots["bad_test_fields"])
        + len(slots["wrong_receiver"])
    )
    a("## 摘要")
    a("")
    a("| 桶 | 項數 |")
    a("| --- | --- |")
    a(f"| 未定義 | {n_undef} |")
    a(f"| 定義有誤 | {n_wrong} |")
    a(
        f"| 定義差（多重釋義） | {len(slots['dup_slots']) + len(terms) + len(slots['js_extra_axes'])} |"
    )
    a(f"| 定義合理（已驗證） | {len(sanity['markers'])}+ 處顯式定義標記 |")
    a("")
    if FIX_NOTES:
        a("## 修復記錄（本次）")
        a("")
        for f, note in FIX_NOTES:
            a(f"- `{f}` — {note}")
        a("")
        a("### 已評估、決策保留（非本次修復）")
        a("")
        a(
            "- **21 個遙測預留事件**（emit 無 in-process subscribe）：文件宣稱的閉環多以"
            "直接函數呼叫（PriorityNegotiator voter、get_system_health 等）實現，事件為"
            "外部觀察者預留。2026-10-20 起逐筆記錄於"
            "`core/system/state_store/telemetry_events.py`（每筆附「為何無消費者」"
            "的理由），稽核掃描時扣除，故「未解釋的孤兒事件」為 0；清單若與程式"
            "不一致（事件已不再發射）會被 `defs.stale_telemetry_allowlist` 擋下。"
        )
        a(
            "- **權重三方分歧**（Python 全 1.0 / YAML ε0.3θ0.8ζ0.2 / JS ε0.3θ0.2ζ0.3）："
            "YAML 為死配置、JS 權重影響本地影響力衰減 — 統一即改行為，各保留現值。"
        )
        a(
            "- **matrix.default.yaml 未接線**：槽定義已與 DEFAULT_DIMENSIONS 完全對齊"
            "（對齊後接線＝行為不變），接線本身涉及 formula 配置載入器變更，另案處理。"
        )
        a(
            "- **StateMatrixAdapter 寬進 vs DimensionState 嚴格**：兩種 update 合約並存 — "
            "adapter 為 Phase 7 代理層（dict 透傳），改為嚴格會破壞其既有用途，記錄為"
            "定義差。"
        )
        a("")

    # ---- bucket 1
    a("## 一、未定義（使用中但無定義）")
    a("")
    if slots["undefined"]:
        a("### StateMatrix 槽")
        a("")
        for k in slots["undefined"]:
            a(
                f"- `{k}` — 被座標讀取器／影響規則／ripple schema／update_* 呼叫使用，但不在任何槽定義中"
            )
    if prompt["undefined"]:
        a("### i18n prompt 鍵")
        a("")
        for k in prompt["undefined"]:
            a(f"- `{k}`")
    if sanity["inf_missing"]:
        a("### 情緒 influence_map 類型")
        a("")
        for k in sanity["inf_missing"]:
            a(f"- `{k}` — `apply_influence()` 呼叫傳入，map 無此鍵 → PAD 靜默 no-op")
    if not (slots["undefined"] or prompt["undefined"] or sanity["inf_missing"]):
        a("（無 — 全部使用中的定義皆可解析。）")
    a("")

    # ---- bucket 2
    a("## 二、定義有誤（有定義但錯誤／失準）")
    a("")
    bad_gloss = [c for c in gloss if not c["ok"]]
    if bad_gloss:
        a("### GLOSSARY 數值宣稱失準")
        a("")
        a("| 項目 | 文件宣稱 | 實測 |")
        a("| --- | --- | --- |")
        for c in bad_gloss:
            a(f"| {c['name']} | {c['claim']} | {c['measured']} |")
        a("")
    if slots["yaml_diffs"]:
        a("### matrix.default.yaml（死配置）與 Python DEFAULT_DIMENSIONS 分歧")
        a("")
        for d in slots["yaml_diffs"]:
            a(f"- {d}")
        a("")
        a(
            '> 該 YAML 未被 `get_formula_config("matrix")` 載入（`_CONFIG["formula"]` 無 `matrix` key），'
        )
        a("> 運行時完全走 `DEFAULT_DIMENSIONS` fallback — 屬「定義寫在配置、運行時未使用」。")
        a("")
    if slots["js_diffs"]:
        a("### JS 鏡像 (packages/shared-js/js/state-matrix.js) 與 Python 分歧")
        a("")
        for d in slots["js_diffs"]:
            a(f"- {d}")
        a("")
    if slots["bad_test_fields"]:
        a("### 測試參數化使用錯軸槽位（定義錯誤示範）")
        a("")
        for f, ax, key in slots["bad_test_fields"]:
            a(f"- `{f}`: `({ax}, {key})` — 該槽不屬於 `{ax}` 軸")
        a("")
    if prompt["never_referenced"]:
        a("### 死定義（i18n prompt 鍵，零引用）")
        a("")
        for k in prompt["never_referenced"]:
            a(f"- `{k}`")
        a("")
    if events["orphans"]:
        a("### 孤兒事件（emit 有、subscribe 無 → 發了無人聽）")
        a("")
        for e in events["orphans"]:
            a(f"- `{e}`")
        a("")
        a(
            f"（subscribe 無 emit：{', '.join('`' + e + '`' for e in events['never_emitted']) or '無'}）"
        )
        a("")
        a("> 決策：保留 — 見「已評估、決策保留」；emit 無消費者目前無害（無訂閱即 return）。")
        a("")
    if slots["wrong_receiver"]:
        a("### 接收者軸與槽定義軸不符（src）")
        a("")
        for w in slots["wrong_receiver"]:
            a(f"- {w}")
        a("")
    if (
        not bad_gloss
        and not slots["yaml_diffs"]
        and not slots["js_diffs"]
        and not slots["bad_test_fields"]
        and not prompt["never_referenced"]
        and not events["orphans"]
        and not slots["wrong_receiver"]
    ):
        a("（無。）")
        a("")

    # ---- bucket 3
    a("## 三、定義差（多重釋義 — 同對象、多視角／多源）")
    a("")
    if slots["dup_slots"]:
        a("### 同名槽跨軸（同一詞、兩個測量點）")
        a("")
        for k, axs in sorted(slots["dup_slots"].items()):
            a(f"- `{k}` @ {'/'.join(axs)}")
        a("")
    if slots["js_extra_axes"]:
        a("### 軸數規格分歧")
        a("")
        a(
            f"- Python `StateMatrix4D` = {len(slots['default'])} 軸；JS 鏡像另含 {slots['js_extra_axes']} 軸；"
            "GLOSSARY「8 軸規格為理想目標」— η 在 Python 為獨立子系統 (eta_axis.py)、在 JS 為矩陣第 8 軸。"
        )
        a("- 決策：保留各自現狀（改任一邊皆為行為變更），以本表記錄視角差異。")
        a("")
    if terms:
        a("### 多重釋義詞表（人類視角 vs AI 機制視角）")
        a("")
        a("| 詞 | 定義源 | 人類視角（世界為上下文） | AI 視角（經人的過濾／代碼機制） |")
        a("| --- | --- | --- | --- |")
        for t in terms:
            a(f"| {t['term']} | {t['sources']} | {t['human']} | {t['ai']} |")
        a("")
    a("### 語義／行為層多重定義（文件記錄）")
    a("")
    a(
        "- **update 語義二元**：`DimensionState.update()` 嚴格（未定義鍵丟棄）vs "
        "`StateMatrixAdapter._update_axis` 寬進（任意鍵皆收）vs JS `update*()` 嚴格 — 三處同名 update、兩種合約。"
    )
    a(
        "- **權重三方分歧**：Python 全 1.0 vs matrix.default.yaml (ε0.3/θ0.8/ζ0.2) vs JS (ε0.3/θ0.2/ζ0.3) — "
        "後兩者一為死配置、一影響 JS 本地影響力衰減；決策：各自保留現值（統一即行為變更），接線前需人工定奪。"
    )
    a("")

    # ---- bucket 4
    a("## 四、定義合理（驗證通過）")
    a("")
    ok_gloss = [c for c in gloss if c["ok"]]
    if ok_gloss:
        a(f"- GLOSSARY 數值宣稱 {len(ok_gloss)}/{len(gloss)} 項與實測一致。")
    a(
        f"- i18n prompt：使用 {prompt['count_used']} 鍵、zh {prompt['count_zh']} / en {prompt['count_en']}、"
        f"雙語 parity diff={len(prompt['parity_diff'])}、未定義={len(prompt['undefined'])}。"
    )
    if magic["runtime_ok"]:
        a(
            f"- magic_numbers：{len(magic['used'])} 個使用中鍵、YAML 可解析 {len(magic['resolved'])}、"
            f"僅 inline default（設計如此，呼叫點有預設值）{len(magic['inline_only'])}、"
            f"未定義且崩潰=0（所有取用器簽名帶 default 參數）。"
        )
    a(
        f"- `get_parameter`：{sanity['param_count']} 個呼叫鍵全部在 `_DEFAULT_THRESHOLDS`"
        + (f"（缺：{sanity['param_missing']}）" if sanity["param_missing"] else "。")
    )
    if sanity["rc"].get("found"):
        a(
            f"- `ResponseCategory`（{sanity['rc']['file']}）：模板 JSON 類別未定義="
            + (f"{sanity['tmpl_missing']}" if sanity["tmpl_missing"] else "無")
            + "。"
        )
    if sanity["inf_unused"]:
        a(
            f"- influence_map 有定義但目前無呼叫的類型（備用，非缺陷）：{', '.join(sanity['inf_unused'])}。"
        )
    a(f"- 顯式定義標記（`定義（`/`Definition:`）共 {len(sanity['markers'])} 處，格式良。")
    a("")

    # ---- raw appendix
    a("## 附錄：掃描事實")
    a("")
    a(f"- StateMatrix 鍵：DEFAULT {dict((k, len(v)) for k, v in slots['default_keys'].items())}")
    a(
        f"- 事件：emit {len(events['emitted'])} / subscribe {len(events['subscribed'])} → 孤兒 {len(events['orphans'])}"
    )
    a(f"- 錯誤軸測試欄位 {len(slots['bad_test_fields'])}；跨軸同名槽 {len(slots['dup_slots'])}")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# definitions domain: scan bundle -> Fact verdicts -> optional MD report
# ---------------------------------------------------------------------------
def scan_definitions() -> Dict[str, Any]:
    """執行定義稽核掃描（門與 MD 報告共用同一次結果）。"""
    slots = audit_slots()
    return {
        "prompt": audit_prompt_keys(),
        "magic": audit_magic_keys(),
        "slots": slots,
        "events": audit_events(),
        "gloss": audit_glossary(),
        "terms": audit_terms(slots),
        "sanity": audit_markers_and_sanity(),
    }


def _definitions_bucket_counts(scan: Dict[str, Any]) -> Tuple[int, int, int]:
    """四桶計數（與 render_md 摘要同公式）。"""
    prompt, slots, sanity = scan["prompt"], scan["slots"], scan["sanity"]
    events, gloss, terms = scan["events"], scan["gloss"], scan["terms"]
    n_und = len(slots["undefined"]) + len(prompt["undefined"]) + len(sanity["inf_missing"])
    n_wrong = (
        sum(1 for c in gloss if not c["ok"])
        + len(slots["yaml_diffs"])
        + len(slots["js_diffs"])
        + len(events["orphans"])
        + len(prompt["never_referenced"])
        + len(slots["bad_test_fields"])
        + len(slots["wrong_receiver"])
    )
    n_multi = len(slots["dup_slots"]) + len(terms) + len(slots["js_extra_axes"])
    return n_und, n_wrong, n_multi


def _defs_facts(scan: Dict[str, Any]) -> List[Any]:
    """definitions 域：未定義/失準/分歧/死鍵=0 為門；孤兒事件=棘輪；多重釋義=INFO。"""
    from core.facts import Fact

    prompt, magic, slots = scan["prompt"], scan["magic"], scan["slots"]
    events, gloss, terms, sanity = (
        scan["events"],
        scan["gloss"],
        scan["terms"],
        scan["sanity"],
    )
    gloss_bad = [c for c in gloss if not c["ok"]]
    multi = len(slots["dup_slots"]) + len(terms) + len(slots["js_extra_axes"])
    return [
        Fact(
            "defs.und_slots",
            float(len(slots["undefined"])),
            0.0,
            "le",
            "slots",
            "state_matrix.py DEFAULT_DIMENSIONS",
            f"undefined={sorted(slots['undefined'])}",
        ),
        Fact(
            "defs.und_prompt_keys",
            float(len(prompt["undefined"])),
            0.0,
            "le",
            "keys",
            "prompts.{zh-CN,en-US}.json",
            f"undefined={sorted(prompt['undefined'])}",
        ),
        Fact(
            "defs.und_influence_types",
            float(len(sanity["inf_missing"])),
            0.0,
            "le",
            "types",
            "emotion_system.influence_map",
            f"missing={sanity['inf_missing']}",
        ),
        Fact(
            "defs.glossary_claims_mismatch",
            float(len(gloss_bad)),
            0.0,
            "le",
            "claims",
            "docs/00-overview/GLOSSARY.md",
            "; ".join(f"{c['name']}: claim={c['claim']}" for c in gloss_bad) or "all match",
        ),
        Fact(
            "defs.yaml_slot_divergence",
            float(len(slots["yaml_diffs"])),
            0.0,
            "le",
            "diffs",
            "configs/standard/matrix/matrix.default.yaml",
            f"diffs={slots['yaml_diffs']}",
        ),
        Fact(
            "defs.js_slot_divergence",
            float(len(slots["js_diffs"])),
            0.0,
            "le",
            "diffs",
            "packages/shared-js/js/state-matrix.js",
            f"diffs={slots['js_diffs']}",
        ),
        Fact(
            "defs.test_axis_misplacements",
            float(len(slots["bad_test_fields"])),
            0.0,
            "le",
            "fields",
            "tests (StateMatrix-driven)",
            f"fields={slots['bad_test_fields']}",
        ),
        Fact(
            "defs.dead_prompt_keys",
            float(len(prompt["never_referenced"])),
            0.0,
            "le",
            "keys",
            "prompts locales",
            f"dead={prompt['never_referenced']}",
        ),
        Fact(
            "defs.wrong_receiver_pairs",
            float(len(slots["wrong_receiver"])),
            0.0,
            "le",
            "pairs",
            "src .values receivers",
            f"pairs={slots['wrong_receiver']}",
        ),
        Fact(
            "defs.prompt_locale_parity",
            float(len(prompt["parity_diff"])),
            0.0,
            "le",
            "keys",
            "zh-CN vs en-US",
            f"diff={sorted(prompt['parity_diff'])}",
        ),
        # 棘輪：鎖定「未解釋的孤兒事件」數量。已記錄為遙測預留（無 in-process
        # 消費者，資料同樣在 state store 裡）的事件列在
        # core/system/state_store/telemetry_events.py，掃描時扣除；因此這裡擋的是
        # 真正沒有交代的事件。基線 0（2026-10-20 起：21 筆全部有逐條理由）。
        Fact(
            "defs.orphan_events_ratchet",
            float(len(events["orphans"])),
            0.0,
            "le",
            "events",
            "src emit_event vs subscribe_event（已扣除具名遙測清單）",
            f"orphans({len(events['orphans'])})={events['orphans']} "
            f"telemetry_only({len(events['telemetry_only'])}) "
            f"stale_allowlist({len(events['stale_allowlist'])})",
        ),
        Fact(
            "defs.stale_telemetry_allowlist",
            float(len(events["stale_allowlist"])),
            0.0,
            "le",
            "events",
            "具名遙測清單裡不得有已不再發射的事件",
            f"stale={events['stale_allowlist']}",
        ),
        Fact(
            "defs.get_parameter_keys_resolve",
            float(len(sanity["param_missing"])),
            0.0,
            "le",
            "keys",
            "dynamic_parameters._DEFAULT_THRESHOLDS",
            f"missing={sanity['param_missing']} of {sanity['param_count']}",
        ),
        Fact(
            "defs.template_categories_resolve",
            float(len(sanity["tmpl_missing"])),
            0.0,
            "le",
            "cats",
            "templates_data.json category vs ResponseCategory",
            f"missing={sanity['tmpl_missing']}",
        ),
        Fact(
            "defs.magic_runtime_resolve",
            1.0 if magic["runtime_ok"] else 0.0,
            1.0,
            "ge",
            "ok",
            "core/system/config/magic_numbers",
            (
                f"runtime_ok={magic['runtime_ok']} "
                f"(used={len(magic['used'])}, inline_only={len(magic['inline_only'])})"
            ),
        ),
        # INFO：多重釋義是視角記錄，不是缺陷（決策保留，詳見 MD 報告「定義差」桶）
        Fact(
            "defs.multi_interpretations",
            float(multi),
            0.0,
            "ge",
            "records",
            "dup_slots+terms+js_axes",
            f"dup={sorted(slots['dup_slots'])} terms={len(terms)} js_extra={slots['js_extra_axes']}",
            must_pass=False,
        ),
        Fact(
            "defs.explicit_markers",
            float(len(sanity["markers"])),
            1.0,
            "ge",
            "markers",
            "src 定義（/Definition: 標記",
            f"markers={len(sanity['markers'])}",
            must_pass=False,
        ),
    ]


def write_definitions_audit_md(scan: Dict[str, Any], path_str: str) -> Path:
    """寫出定義稽核 MD 四桶報告，並自動 prettier --write（單一工具、零手續）。"""
    md = render_md(
        scan["prompt"],
        scan["magic"],
        scan["slots"],
        scan["events"],
        scan["gloss"],
        scan["terms"],
        scan["sanity"],
    )
    out = Path(path_str)
    if not out.is_absolute():
        out = REPO / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    try:
        import subprocess

        proc = subprocess.run(
            ["npx", "prettier", "--write", str(out)],
            cwd=REPO,
            timeout=90,
            capture_output=True,
        )
        if proc.returncode != 0:
            print(
                f"  prettier auto-format failed (rc={proc.returncode}); "
                f"run `npx prettier --write {out}` manually"
            )
    except Exception as exc:
        print(f"  prettier auto-format skipped ({exc}); run `npx prettier --write` manually")
    try:
        shown = out.relative_to(REPO)
    except ValueError:
        shown = out
    print(f"wrote {shown} ({out.stat().st_size} bytes)")
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=-1,
        help="列出 measured_at 超過 N 天的事實（只警告，不擋門）",
    )
    parser.add_argument(
        "--write-definitions-audit",
        nargs="?",
        const=DEFS_AUDIT_MD,
        default=None,
        metavar="PATH",
        help=("寫出定義稽核 MD 四桶報告" f"（預設 {DEFS_AUDIT_MD}；與門共用同一次掃描）"),
    )
    args = parser.parse_args(argv)

    from core.facts import Report, adjudicate, merge_reports, stale_facts

    edge_facts = _edge_facts()
    audit_report = Report()
    for v in _audit_facts():
        audit_report.add(v)
    chain_facts = _chat_facts() + _cluster_facts()
    defs_scan = scan_definitions()
    defs_facts = _defs_facts(defs_scan)
    hygiene_facts = _config_facts() + _version_facts() + _docs_facts() + _modules_facts()
    merged = merge_reports(
        adjudicate(edge_facts),
        audit_report,
        adjudicate(chain_facts),
        adjudicate(defs_facts),
        adjudicate(hygiene_facts),
    )

    if args.write_definitions_audit is not None:
        write_definitions_audit_md(defs_scan, args.write_definitions_audit)

    print("=" * 72)
    print("FACT GATES (edge + audit + chat-chain + cluster-chain + definitions + hygiene)")
    print("=" * 72)
    print(merged.summary())
    n_und, n_wrong, n_multi = _definitions_bucket_counts(defs_scan)
    print(f"definitions buckets: 未定義={n_und} 定義有誤={n_wrong} 定義差={n_multi}")
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
