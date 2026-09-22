#!/usr/bin/env python3
"""STATUS_MATRIX 生成器與核對器 — YAML 真相源 ↔ MD 生成視圖。

docs/status_matrix.yaml 是單一真相源；docs/STATUS_MATRIX.md 由本工具生成。
手改生成 MD 會被覆蓋；改狀態請改 YAML。

雙模式：
  generate（預設）  YAML → STATUS_MATRIX.md
  check             核對三層（--ci 退出碼契約：0 通過 / 1 違規 / 2 工具錯）
    1. 結構層    YAML 語法、必填欄位、status 合法值、id 唯一
    2. 實體層    implementation/tests 檔案存在性
    3. 語意層    verified ⇔ verify_command 雙向

只用 stdlib＋pyyaml（pyproject base 依賴）。
"""

import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

VALID_STATUSES = {"claimed", "implemented", "wired", "verified", "production"}
REQUIRED_FIELDS = ("id", "domain", "claim", "status")
# verified/production 必須可驗證；claimed 不得附實作宣稱外的證據門
STATUS_REQUIRES_VERIFY = {"verified", "production"}

STATUS_LABELS = {
    "claimed": "`claimed`",
    "implemented": "**implemented**",
    "wired": "**wired**",
    "verified": "**verified**",
    "production": "**production**",
}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_map_tool():
    """載入 gen_project_map（同目錄 importlib），複用其 AST 解析（單一事實源）。"""
    import importlib.util

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_project_map.py")
    spec = importlib.util.spec_from_file_location("gen_project_map", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_pipeline(root, data, map_mod=None, files=None, trees=None):
    """chat_pipeline 區段核對：entry/stages 模組存在＋被生產碼引用（wired）。

    map_mod：gen_project_map 模組（複用其 AST 解析，單一事實源）；
    缺省時退化為存在性檢查。
    """
    problems = []
    pipeline = data.get("chat_pipeline") or {}
    if not pipeline:
        return problems  # 區段可選：未定義即跳過
    entry = pipeline.get("entry")
    if not entry or not os.path.exists(os.path.join(root, entry)):
        problems.append(f"[chat_pipeline] entry 不存在：{entry}")
    if map_mod is None or files is None or trees is None:
        return problems
    imported = map_mod.import_index(trees)
    mod2file = {map_mod.rel_module_of(r): r for r in trees}

    def wired(p):
        """p（檔或目錄）被 p 以外的生產碼（非 tests）import 即接線。"""
        prefix = p if p.endswith("/") else p + "/"
        for m, who in imported.items():
            f = mod2file.get(m)
            inside = f == p or (f is not None and f.startswith(prefix))
            if not inside:
                continue
            for w in who:
                if w.startswith("tests/") or w == f or w.startswith(prefix):
                    continue
                return True
        return False

    for stage in pipeline.get("stages") or []:
        sid = stage.get("id") or "<stage>"
        mods = stage.get("modules") or []
        if not mods:
            problems.append(f"[pipeline:{sid}] 無 modules")
        for p in mods:
            if not os.path.exists(os.path.join(root, p)):
                problems.append(f"[pipeline:{sid}] 模組不存在：{p}")
            elif not wired(p):
                problems.append(f"[pipeline:{sid}] 模組無人引用（未接線）：{p}")
    return problems


def check_feature_tree(root, data):
    """feature_tree 核對：children 引用存在的節點 id；modules 路徑存在。"""
    problems = []
    tree = data.get("feature_tree") or []
    ids = {n.get("id") for n in tree if isinstance(n, dict)}
    for node in tree:
        nid = node.get("id") or "<node>"
        if not node.get("name"):
            problems.append(f"[tree:{nid}] 缺 name")
        for cid in node.get("children") or []:
            if cid not in ids:
                problems.append(f"[tree:{nid}] children 引用不存在的節點：{cid}")
        for p in node.get("modules") or []:
            if not os.path.exists(os.path.join(root, p)):
                problems.append(f"[tree:{nid}] 模組不存在：{p}")
    return problems


def check_lifecycle(root, data, files=None, trees=None):
    """lifecycle 核對：status 合法值；deleted 防復活門——三層名稱比對。

    路徑比對只能抓「原地復活」；亂找位置重實作要靠名稱：
      1. 檔名 basename：全倉任意目錄出現同名檔即違規。
      2. 符號名（symbols 欄）：AST 掃全倉 class/def 同名定義即違規——
         換檔案重寫同類也抓到。
      3. 路徑 token：精確路徑存在即違規。
    files/trees：地圖工具解析結果（省略時退化為僅路徑層）。
    """
    import ast as _ast

    problems = []
    valid = {"active", "partial", "planned", "deleted"}
    # 1/2 層預建索引：basename 索引＋符號定義索引
    by_basename = {}
    defined = {}  # symbol -> [(rel, kind)]
    if files is not None:
        for rel, _, _ in files:
            by_basename.setdefault(os.path.basename(rel), []).append(rel)
    if trees is not None:
        for rel, tree in trees.items():
            for node in tree.body:
                if isinstance(node, (_ast.ClassDef, _ast.FunctionDef, _ast.AsyncFunctionDef)):
                    defined.setdefault(node.name, []).append(rel)
    for item in data.get("lifecycle") or []:
        lid = item.get("id") or "<item>"
        status = item.get("status")
        if status not in valid:
            problems.append(
                f"[lifecycle:{lid}] status={status} 不合法（active/partial/planned/deleted）"
            )
        if status != "deleted":
            continue
        name = item.get("name") or ""
        # 3. 路徑 token（精確）
        tokens = [t for t in name.replace("（", "(").split() if "/" in t or t.endswith(".py")]
        for t in tokens:
            t_clean = t.strip("。；;，,")
            if os.path.exists(os.path.join(root, t_clean)):
                problems.append(f"[lifecycle:{lid}] 已刪除項目在磁碟復活：{t_clean}（勿重實作）")
        # 1. 檔名 basename（任意位置；basename_ok 豁免正典同名檔）
        ok_basenames = set(item.get("basename_ok") or [])
        for t in tokens:
            base = os.path.basename(t_clean)
            hits = [r for r in by_basename.get(base, []) if r != t_clean and r not in ok_basenames]
            if hits:
                problems.append(
                    f"[lifecycle:{lid}] 已刪檔名在他處重現：{base} → {hits[:3]}（亂找位置重實作）"
                )
        # 2. 符號名（AST 全倉）
        for sym in item.get("symbols") or []:
            hits = [r for r in defined.get(sym, []) if r != name]
            if hits:
                problems.append(
                    f"[lifecycle:{lid}] 已刪符號在他處重新定義：{sym} → {hits[:3]}（勿重實作）"
                )
    return problems


def check(root, data):
    """三層核對。回傳違規字串清單（空 = 通過）。"""
    problems = []
    features = data.get("features") or []
    if not features:
        return ["YAML 無 features 或為空"]

    seen_ids = set()
    for i, feat in enumerate(features):
        if not isinstance(feat, dict):
            problems.append(f"features[{i}] 不是映射")
            continue
        fid = feat.get("id") or f"<index {i}>"
        # 結構層
        for field in REQUIRED_FIELDS:
            if not feat.get(field):
                problems.append(f"[{fid}] 缺必填欄位 `{field}`")
        if feat.get("status") not in VALID_STATUSES:
            problems.append(
                f"[{fid}] status=`{feat.get('status')}` 不合法"
                f"（合法：{'/'.join(sorted(VALID_STATUSES))}）"
            )
        if fid in seen_ids:
            problems.append(f"[{fid}] id 重複")
        seen_ids.add(fid)
        if feat.get("status") == "claimed" and feat.get("evidence"):
            problems.append(f"[{fid}] claimed 不應附 evidence（無驗證即 claimed）")

        # 實體層：implementation / tests 路徑存在性
        for field in ("implementation", "tests"):
            for path in feat.get(field) or []:
                full = os.path.join(root, path)
                if not os.path.exists(full):
                    problems.append(f"[{fid}] {field} 路徑不存在：{path}")

        # 語意層：verified ⇔ verify_command 雙向
        has_cmd = bool(feat.get("verify_command"))
        needs = feat.get("status") in STATUS_REQUIRES_VERIFY
        if needs and not has_cmd:
            problems.append(f"[{fid}] status={feat['status']} 但缺 verify_command")
        if has_cmd and not needs:
            problems.append(
                f"[{fid}] 有 verify_command 但 status={feat['status']}"
                f"（{'+'.join(sorted(STATUS_REQUIRES_VERIFY))} 才需附）"
            )
    return problems


def render_pipeline_md(data):
    """chat_pipeline 區段 → MD 表。"""
    pipeline = data.get("chat_pipeline") or {}
    if not pipeline:
        return []
    lines = [
        "",
        "## Chat Pipeline（主對話管線）",
        "",
        f"> 入口：`{pipeline.get('entry', '—')}`。階段構成為真相源事實；路徑存在性與 wired 由 `check` 核對。",
        "",
        "| # | 階段 | 模組 |",
        "| --- | --- | --- |",
    ]
    for i, stage in enumerate(pipeline.get("stages") or [], 1):
        mods = "<br>".join(f"`{m}`" for m in stage.get("modules") or ["—"])
        lines.append(f"| {i} | {stage.get('name', '?')} | {mods} |")
    return lines


def render_tree_md(data):
    """feature_tree 區段 → MD 樹狀列表。"""
    tree = data.get("feature_tree") or []
    if not tree:
        return []
    by_id = {n.get("id"): n for n in tree}
    lines = ["", "## Feature Tree（產品能力樹）", "", "```", ""]

    def emit(node, depth, seen):
        if node is None or node.get("id") in seen:
            return
        seen.add(node.get("id"))
        lines.append("  " * depth + "- " + (node.get("name") or node.get("id", "?")))
        for cid in node.get("children") or []:
            emit(by_id.get(cid), depth + 1, seen)

    roots = [n for n in tree if not any(n.get("id") in (c.get("children") or []) for c in tree)]
    for r in roots:
        emit(r, 0, set())
    lines += ["```", ""]
    return lines


def render_lifecycle_md(data):
    """lifecycle 區段 → MD 表（deleted 為防復活門資料）。"""
    life = data.get("lifecycle") or []
    if not life:
        return []
    marks = {"active": "✅", "partial": "🟡", "planned": "🗓️", "deleted": "🗑️"}
    lines = [
        "",
        "## 生命週期（Active / Partial / Planned / Deleted）",
        "",
        "| 狀態 | 項目 | 備註 |",
        "| --- | --- | --- |",
    ]
    for item in life:
        st = item.get("status", "?")
        lines.append(
            f"| {marks.get(st, st)} {st} | {item.get('name', '?')} | {item.get('note', '')} |"
        )
    lines += [
        "",
        "> `deleted` 列表由工具做**防復活門**：同名路徑在磁碟再現即 CI 紅（勿重實作）。",
    ]
    return lines


def render_md(root, data):
    """YAML → STATUS_MATRIX.md（生成視圖）。"""
    features = data.get("features") or []
    meta = data.get("meta") or {}
    today = datetime.date.today()
    lines = [
        "<!--",
        "  本檔由 scripts/gen_status_matrix.py 自 docs/status_matrix.yaml 生成。",
        "  手改會被覆蓋；改狀態請改 YAML 真相源，再重跑生成器。",
        f"  真相源：docs/status_matrix.yaml（meta.version={meta.get('version', '?')}）",
        "-->",
        "",
        "# STATUS_MATRIX — 功能成熟度唯一總表",
        "",
        "> 本檔是**生成視圖**；單一真相源是 [`status_matrix.yaml`](status_matrix.yaml)。"
        "五級狀態：`claimed`（宣稱存在）→ `implemented`（程式存在）→ `wired`（生產路徑呼叫）→",
        "> `verified`（端到端測試證明）→ `production`（benchmark 達標）。"
        "每列必須附驗證指令與日期；無法附者降回 `claimed`。",
        "> 「架構完成度」≠「模型能力完成度」：確定性能力與神經泛化分開計分"
        "（見 INTELLIGENCE_ASSESSMENT）。",
        f"> 狀態快照：{today}（由 YAML 同步）。核對："
        "`python scripts/gen_status_matrix.py check`（0 通過 / 1 違規）。",
        "",
        "| 領域 | Claim（宣稱） | Implementation（實作） | 狀態 | 驗證指令／證據 | 最後驗證 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for feat in features:
        fid = feat.get("id", "?")
        impl = feat.get("implementation") or []
        impl_str = "<br>".join(f"`{p}`" for p in impl) if impl else "—（見證據欄）"
        verify = feat.get("verify_command") or ""
        evidence = feat.get("evidence") or ""
        verify_cell = (
            f"`{verify}`{'；' + evidence if evidence else ''}" if verify else (evidence or "—")
        )
        lines.append(
            f"| {feat.get('domain', '?')} | {feat.get('claim', '?')} | {impl_str} "
            f"| {STATUS_LABELS.get(feat.get('status'), feat.get('status'))} "
            f"| {verify_cell} | {feat.get('last_verified', '—')} |"
        )
    lines += render_pipeline_md(data)
    lines += render_tree_md(data)
    lines += render_lifecycle_md(data)
    lines += [
        "",
        "## 誠實缺口（正式版判斷依據）",
        "",
        "1. **路由重複決策**（Pipeline/Router/ModelBus 各自分類）— 架構債，最高優先收斂。",
        "2. **學習品質未證明** — 「字典增長」≠「能力增長」；需 hold-out 前後測成為常態門。",
        "3. **Dashboard E2E** — 新面板僅 wired，缺自動化瀏覽器測試。",
        "4. **mypy 540** — 棘輪門鎖定（`scripts/mypy_budget_gate.py`）；新增型別債 CI 直接紅燈。",
        "5. **公開 benchmark** — angela_bench 115 題管線與 CI 回歸門已建（`scripts/run_benchmarks.py --gate-native`）；跨 AI 對比待外部 LLM 端點實際接入跑分。",
        "6. **Luanti policy** — 訓練管線已通（hold-out 學習門鎖測試）；live 樣本待玩家在線累積；20 FPS 仍 ❌（10Hz＋2s poller）。",
        "7. **EmotionSystem 跨進程不共享** — 遊戲 agent 與主 server 生命階段已透過共享 lifecycle JSON 互通（R71c），情緒狀態仍各自 in-memory。",
        "",
        "> 調用方式查詢：見 **[`INVOCATION_MATRIX.md`](INVOCATION_MATRIX.md)**。"
        "本表答「能不能用、多成熟」；該表答「怎麼用、配什麼、怎麼驗證」。",
        "",
        "## 維護規則",
        "",
        "- 改狀態**只改 `docs/status_matrix.yaml`**，重跑"
        " `python scripts/gen_status_matrix.py`；手改本檔會被覆蓋。",
        "- 任何「看起來完成」必須附驗證指令＋日期，否則寫 `claimed`。",
        "- YAML 落實體核對：路徑不存在 / verified 無指令 → CI 紅燈；"
        "pipeline 階段模組須被生產碼引用（wired）；deleted 項目磁碟復活即紅（防重實作）。",
        "- 修復安全相關項目時，同時把 regression payload 加進 `tests/security/`。",
        "- 舊文件與本表衝突時，以本表為準並修訂舊文件。",
        "",
    ]
    return lines


def main():
    ap = argparse.ArgumentParser(description="STATUS_MATRIX 生成器＋核對器")
    ap.add_argument("mode", nargs="?", default="generate", choices=["generate", "check"])
    ap.add_argument("--yaml", default="docs/status_matrix.yaml")
    ap.add_argument("--output", default="docs/STATUS_MATRIX.md")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    if yaml is None:
        print("TOOL ERROR: pyyaml 未安裝（base 依賴應有；pip install pyyaml）")
        return 2
    root = os.path.abspath(args.root)
    yaml_path = os.path.join(root, args.yaml) if not os.path.isabs(args.yaml) else args.yaml
    try:
        data = load_yaml(yaml_path)
    except (OSError, yaml.YAMLError) as e:
        print(f"TOOL ERROR: {e}")
        return 2

    if args.mode == "check":
        problems = check(root, data)
        # 區段核對：pipeline wired / feature tree / lifecycle（含防復活門）
        map_mod = None
        files = trees = None
        try:
            map_mod = load_map_tool()
            files = map_mod.walk_files(root)
            trees = map_mod.parse_trees(root, files)
        except Exception as e:  # 地圖工具載入失敗 → 只報存在性層
            print(f"(warn) 地圖工具解析退化：{e}")
        problems += check_pipeline(root, data, map_mod, files, trees)
        problems += check_feature_tree(root, data)
        problems += check_lifecycle(root, data, files, trees)
        n_stages = len((data.get("chat_pipeline") or {}).get("stages") or [])
        n_tree = len(data.get("feature_tree") or [])
        n_life = len(data.get("lifecycle") or [])
        if problems:
            print(f"STATUS_MATRIX 核對：{len(problems)} 項違規")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(
            f"STATUS_MATRIX 核對通過：{len(data.get('features') or [])} 條目"
            f"＋pipeline {n_stages} 階段＋tree {n_tree} 節點＋lifecycle {n_life} 項，全綠"
        )
        return 0

    out_lines = render_md(root, data)
    out_path = os.path.join(root, args.output) if not os.path.isabs(args.output) else args.output
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(out_lines))
    except OSError as e:
        print(f"TOOL ERROR: {e}")
        return 2
    print(f"OK: {out_path}（{len(out_lines)} 行，{len(data.get('features') or [])} 條目）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
