#!/usr/bin/env python3
"""專案地圖生成器 — 依賴排錯 + 碰撞定位 + 行為理解，萬行預算封頂。

三區塊：
  1. 依賴（AST 掃 import，第三方/倉內分開，排錯用）
  2. 碰撞索引（同檔名多路徑，深→淺；重名全展開，其餘按目錄捲）
  3. 行為核心（驗收門 + 配置鍵 + 大檔，半自動指標）

預算即診斷：輸出超 `--budget` 行即 exit 1 + 兇手排行（超標=專案有病）。
只用 stdlib。產物標 Generated，手不改。

P0：分域檔案預算（超任一域亦 exit 1）+ `## DIAG` 機器可讀尾段 +
孤兒 L1/L2/L3 分級（僅 L1 展開）。退出碼：0 內 / 1 超標 / 2 工具錯。
P1：`## TREND` 快照（jsonl 輪轉 20 次，只報告不進門；--no-history 可關）。
P2（R75）：區塊四實時結構（入口點/路由/模組樹/callers/測試映射/
STATUS_MATRIX 交叉核對）+ `--module` 查詢模式（不寫檔）。
STATUS_MATRIX YAML 核對獨立門：scripts/gen_status_matrix.py check。
"""

import argparse
import ast
import datetime
import hashlib
import json
import os
import re
import sys

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "data",
    ".cache",
    "checkpoints",
    ".hypothesis",
    "dist",
    "build",
    ".mypy_cache",
    ".ruff_cache",
}
SKIP_EXT = {".pyc", ".pyo", ".pyd", ".so", ".o"}
# 工具自身產物不量（自量衛生）：生成地圖 + 歷史快照若被掃入，
# 每次跑步都會因「多了上次的自己」而漂移（實測：歷史檔使 docs/ 25→26 檔，
# 觸發 25 檔折疊懸崖，總數擺動 25 行）。
SKIP_NAMES = {"PROJECT_MAP_GENERATED.md", ".project_map_history.jsonl"}

# 已知有意鏡像根：組內路徑全落此即壓成一行（雙端資產/test 產物，定性過）
MIRROR_ROOTS = (
    "apps/desktop-app/electron_app/resources",
    "apps/desktop-app/electron_app/models",
    "apps/web-live2d-viewer/",
    "resources/",
    "test_models/",
)

# 分域檔案預算（P0）：總輸出預算之外，按子系統點名。超任一域即 exit 1。
# 基準 2026-09-12：backend 706 / scripts 257 / desktop 435 / packages 58（約 2x 寬限）。
# 域外其餘只報告、不設限。調整時同步更新此註解的基準日期與數值。
DOMAIN_FILE_BUDGETS = {
    "apps/backend/src": 1400,
    "scripts": 600,
    "apps/desktop-app": 900,
    "packages/": 300,
}

# STATUS_MATRIX 核對結果（block_structure 留下，main 組 DIAG 用）。
_LAST_STATUS_VERIFY = {"total": 0, "ok": 0, "problems": []}
# 本輪掃描的全檔清單（main 填充；verify_status_matrix 用 YAML 路徑存在性核對）。
_LAST_FILES = []

# 孤兒置信度分級（P0）：L1 高疑才展開；L2 疑似入口 / L3 配置門控只折疊計數。
ENTRY_LIKE_STEMS = {
    "main",
    "app",
    "server",
    "cli",
    "manage",
    "wsgi",
    "asgi",
    "desktop",
    "game",
    "launcher",
    "bootstrap",
    "daemon",
    "worker",
    "scheduler",
    "setup",
    "conftest",
}
ENTRY_LIKE_PREFIXES = ("run_", "serve_", "start_", "launch_")

# block_orphans 每次調用後在此留下分級計數（main 組 DIAG 用；函數簽名不變）。
_LAST_ORPHAN_COUNTS = {"L1": 0, "L2": 0, "L3": 0}


def domain_file_usage(root, files):
    """各域檔案數（輸入規模，非輸出 Responsibility 行數）。未列域歸 rest（只報告）。"""
    usage = {d: 0 for d in DOMAIN_FILE_BUDGETS}
    usage["rest"] = 0
    for rel, _, _ in files:
        for dom in DOMAIN_FILE_BUDGETS:
            prefix = dom if dom.endswith("/") else dom + "/"
            if rel.startswith(prefix):
                usage[dom] += 1
                break
        else:
            usage["rest"] += 1
    return usage


def check_domain_budgets(usage, budgets=None):
    """回傳 [(domain, used, budget)] 超標清單；空即全域內。"""
    budgets = DOMAIN_FILE_BUDGETS if budgets is None else budgets
    return [(d, usage.get(d, 0), b) for d, b in budgets.items() if usage.get(d, 0) > b]


def grade_orphan(rel, gated):
    """孤兒置信度：L3 配置門控 > L2 疑似入口 > L1 高疑。"""
    if gated:
        return "L3"
    stem = os.path.splitext(os.path.basename(rel))[0]
    if stem in ENTRY_LIKE_STEMS or stem.startswith(ENTRY_LIKE_PREFIXES):
        return "L2"
    return "L1"


def render_diag(status, total, budget, usage, over_domains, counts, top_block, status_verify=None):
    """固定機器可讀尾段（CI 只依賴退出碼 + 本段鍵名；鍵名穩定，勿改）。"""
    lines = ["## DIAG", "", f"status: {status}", f"total: {total}", f"budget: {budget}"]
    lines.append("domains:")
    for dom in list(DOMAIN_FILE_BUDGETS) + ["rest"]:
        b = DOMAIN_FILE_BUDGETS.get(dom)
        lines.append(f"  {dom}: {usage.get(dom, 0)}/{b if b is not None else 'unlimited'}")
    lines.append(
        f"orphans: L1={counts.get('L1', 0)} L2={counts.get('L2', 0)} L3={counts.get('L3', 0)}"
    )
    if status_verify and status_verify.get("total"):
        lines.append(f"status_matrix: {status_verify.get('ok', 0)}/{status_verify['total']} ok")
        for p in status_verify.get("problems", [])[:5]:
            lines.append(f"  - {p}")
    lines.append("actions:")
    acts = []
    if over_domains:
        acts += [f"reduce_domain: {d} ({u} > {b})" for d, u, b in over_domains]
    if status == "fail" and top_block:
        acts.append(f"reduce_output: {top_block}")
    if counts.get("L1", 0):
        acts.append(f"review_L1_orphans: {counts['L1']}")
    lines.append(f"  - {acts[0]}" if acts else "  - none")
    for a in acts[1:]:
        lines.append(f"  - {a}")
    lines.append("")
    return lines


# 趨勢快照（P1）：只報告、不進門（惡化也不 exit 1，不斷 CI）。
# 歷史檔 gitignored（本地趨勢）；損毀/缺失一律視為空，不拖累主流程。
HISTORY_KEEP = 20


def load_history(path):
    try:
        with open(path, encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        return [r for r in rows if isinstance(r, dict) and "total" in r][-HISTORY_KEEP:]
    except (OSError, ValueError):
        return []


def append_history(path, record):
    """附加一筆並輪轉；失敗回 False（呼叫方繼續，不影響退出碼）。"""
    try:
        hist = load_history(path)
        hist.append(record)
        hist = hist[-HISTORY_KEEP:]
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in hist:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        return True
    except OSError:
        return False


def render_trend(hist):
    """由舊→新算 verdict：連 3 次上升=degrading；只看快照，不看單次噪聲。"""
    lines = ["## TREND", ""]
    if len(hist) < 2:
        lines += ["runs: %d" % len(hist), "verdict: insufficient history", ""]
        return lines
    prev, cur = hist[-2], hist[-1]
    d_total = cur["total"] - prev["total"]
    d_l1 = cur.get("L1", 0) - prev.get("L1", 0)
    # 尾段連續上升步數（由新往舊數，斷即停）
    rises = 0
    for i in range(len(hist) - 1, 0, -1):
        if hist[i]["total"] > hist[i - 1]["total"]:
            rises += 1
        else:
            break
    if rises >= 2:
        verdict = f"degrading ({rises + 1} consecutive rises)"
    elif d_total < 0:
        verdict = "improving"
    elif d_total == 0 and d_l1 <= 0:
        verdict = "stable"
    else:
        verdict = "watch (up once)"
    lines += [
        f"runs: {len(hist)}",
        f"prev_total: {prev['total']} / delta: {d_total:+d}",
        f"prev_L1: {prev.get('L1', 0)} / delta: {d_l1:+d}",
        f"verdict: {verdict}",
        "",
    ]
    return lines


def parse_trees(root, files, trees=None):
    """共享 AST 解析（一輪掃描多區塊重用；返回 dict 供呼叫方直接傳回）。"""
    if trees is not None:
        return trees
    trees = {}
    for rel, _, _ in files:
        if not rel.endswith(".py"):
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                trees[rel] = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
    return trees


def imports_of(tree, rel):
    """單檔 import 解析為候選模組名集合（相對導入展開）。"""
    parts = rel[:-3].split("/")
    base = parts[:-1]
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name:
                    out.add(a.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                pre = base[: len(base) - node.level + 1] if node.level > 1 else base
                if node.module:
                    out.add(".".join(pre + node.module.split(".")))
                else:
                    for a in node.names:
                        if a.name and a.name != "*":
                            out.add(".".join(pre + [a.name]))
            elif node.module:
                out.add(node.module)
    return out


def import_index(trees):
    """模組名 → 引用它的檔案集合（block_orphans 同款解析邏輯，提升共享）。"""
    from collections import defaultdict

    imported = defaultdict(set)
    for rel, tree in trees.items():
        for mod in imports_of(tree, rel):
            imported[mod].add(rel)
    return imported


def walk_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith("."))
        for fn in sorted(filenames):
            if os.path.splitext(fn)[1] in SKIP_EXT:
                continue
            if fn in SKIP_NAMES:
                continue
            fp = os.path.join(dirpath, fn)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            rel = os.path.relpath(fp, root)
            out.append((rel, st.st_size, st.st_mtime))
    return out


def block_dependencies(root, files, trees=None):
    import sys as _sys

    stdlib = set(getattr(_sys, "stdlib_module_names", ()))
    third, first, edges = {}, {}, 0
    roots = (
        "apps",
        "packages",
        "core",
        "ai",
        "api",
        "hsp",
        "services",
        "tests",
        "scripts",
        "tools",
    )
    for rel, _, _ in files:
        if not rel.endswith(".py"):
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
        seen = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    seen.add((a.name or "").split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    seen.add(".relative")
                elif node.module:
                    seen.add(node.module.split(".")[0])
        for top in seen:
            if not top:
                continue
            edges += 1
            if top in stdlib or top == "__future__":
                continue
            elif top == ".relative" or top in roots:
                first[top] = first.get(top, 0) + 1
            else:
                third[top] = third.get(top, 0) + 1
    lines = ["## 區塊一：依賴（排錯用）", ""]
    lines.append(
        f"- Python 檔掃描：{sum(1 for r, _, _ in files if r.endswith('.py'))}，import 邊：{edges}"
    )
    lines.append("- 第三方 Top（引用檔數）：")
    for mod, n in sorted(third.items(), key=lambda kv: -kv[1])[:15]:
        lines.append(f"  - `{mod}`：{n}")
    lines.append("- 倉內根 Top：")
    for mod, n in sorted(first.items(), key=lambda kv: -kv[1])[:15]:
        lines.append(f"  - `{mod}`：{n}")
    lines.append("")
    lines.extend(block_orphans(root, files, parse_trees(root, files, trees)))
    return lines


def block_orphans(root, files, trees=None):
    """疑似孤兒檔：無任何靜態 import 指向（候選，非判決）。

    方法局限（已驗證）：相對導入已解析、`__init__` 基已修正；但懶
    `__getattr__`、importlib、字串路由、端點聚合器天生隱身；入口檔
    （cli/desktop/game）按性質即根，不算賬。
    配置門控識別：檔名幹出現在 configs/* 即標註（rlaif 教訓：靜態孤兒
    可能是有意關閉的功能，不可亂判死刑）。
    """
    from collections import defaultdict

    cfg_text = ""
    for rel, _, _ in files:
        if "/configs/" in rel and rel.endswith((".yaml", ".yml", ".json")):
            try:
                with open(os.path.join(root, rel), encoding="utf-8") as f:
                    cfg_text += f.read() + "\n"
            except OSError:
                continue

    trees = parse_trees(root, files, trees)
    imported = import_index(trees)
    orphans = []
    for rel in trees:
        if os.path.basename(rel) in ("__init__.py", "__main__.py"):
            continue
        if rel.startswith(("scripts/", "tests/", "apps/backend/tests/")):
            continue
        if not rel.startswith(("apps/backend/src/", "packages/")):
            continue
        parts = rel[:-3].split("/")
        dots = [".".join(parts[i:]) for i in range(len(parts))]
        tails = [".".join(parts[-2:]), parts[-1]]
        if not any(d in imported for d in dots) and not any(t in imported for t in tails):
            orphans.append(rel)
    lines = ["### 疑似孤兒檔（候選，分級）", ""]
    graded = {"L1": [], "L2": 0, "L3": 0}
    for rel in sorted(orphans):
        stem = os.path.splitext(os.path.basename(rel))[0]
        norm = lambda s: s.replace("_", "").replace("-", "")
        # 短通用詞（app/config）在配置文本恆命中——只信長特徵名
        gated = len(norm(stem)) >= 10 and norm(stem) in norm(cfg_text)
        level = grade_orphan(rel, gated)
        if level == "L1":
            graded["L1"].append(rel)
        elif level == "L2":
            graded["L2"] += 1
        else:
            graded["L3"] += 1
    _LAST_ORPHAN_COUNTS.update({"L1": len(graded["L1"]), "L2": graded["L2"], "L3": graded["L3"]})
    lines.append(
        f"- 共 {len(orphans)} 檔（L1={len(graded['L1'])} 高疑 / "
        f"L2={graded['L2']} 疑似入口 / L3={graded['L3']} 配置門控；"
        "動態加載盲區見上，個案定性前不刪）"
    )
    for rel in graded["L1"][:40]:
        lines.append(f"  - `{rel}`（L1 高疑）")
    if len(graded["L1"]) > 40:
        lines.append(f"  - …{len(graded['L1']) - 40} L1 未展開")
    lines.append(f"  - L2 疑似入口 ×{graded['L2']}（折疊，不展開）")
    lines.append(f"  - L3 配置門控 ×{graded['L3']}（折疊，不展開）")
    lines.append("")
    return lines


def block_collisions(root, files):
    from collections import defaultdict

    by_name = defaultdict(list)
    for rel, size, mt in files:
        by_name[os.path.basename(rel)].append((rel, size, mt))
    coll = {k: v for k, v in by_name.items() if len(v) > 1}
    lines = ["## 區塊二：碰撞索引（深→淺，定位用）", ""]
    lines.append(f"- 重名檔：{len(coll)} 組，共 {sum(len(v) for v in coll.values())} 條路徑")
    for name in sorted(coll):
        hits = sorted(coll[name], key=lambda t: (-t[0].count(os.sep), t[0]))
        if all(h[0].startswith(MIRROR_ROOTS) for h in hits):
            lines.append(f"### `{name}` ×{len(hits)}（已知鏡像，壓縮）")
            lines.append("")
            continue
        lines.append(f"### `{name}` ×{len(hits)}")
        md5s = set()
        for rel, size, mt in hits:
            try:
                with open(os.path.join(root, rel), "rb") as f:
                    md5s.add(hashlib.md5(f.read()).hexdigest()[:8])
            except OSError:
                md5s.add("????????")
            day = datetime.datetime.fromtimestamp(mt).strftime("%Y-%m-%d")
            lines.append(f"- `{rel}`（{size // 1024}KB，{day}）")
        if len(md5s) == 1:
            lines.append(f"- ⚠️ 內容完全相同（一字不差雙胞胎，{sorted(md5s)[0]}）")
        lines.append("")
    # 全量兜底：按目錄捲（深→淺），小目錄列檔名
    dirs = defaultdict(list)
    for rel, size, _ in files:
        dirs[os.path.dirname(rel)].append((rel, size))
    lines.append(f"- 全量兜底：{len(files)} 檔 / {len(dirs)} 目錄")
    for d in sorted(dirs, key=lambda x: (-x.count(os.sep), x)):
        items = dirs[d]
        tot = sum(s for _, s in items)
        label = d if d else "(根)"
        # 已知限制：25 檔折疊是懸崖（某域 25→26 檔時總數擺動 ~25 行）；
        # TREND 只認「連 3 次上升」，單次懸崖不判 degrading。
        if len(items) <= 25:
            lines.append(f"  - `{label}`：{len(items)} 檔，{tot // 1024}KB")
            for rel, size in sorted(items):
                lines.append(f"    - `{os.path.basename(rel)}`（{size // 1024}KB）")
        else:
            lines.append(
                f"  - `{label}`：{len(items)} 檔，{tot // 1024}KB（…{len(items)} 未展開，用工具查）"
            )
    lines.append("")
    return lines


def block_structure(root, files, trees):
    """區塊四：實時結構（永不過期的推導事實）。

    - Runtime Entry Points（`__main__` 守衛，入口偵測補孤兒 L2 啟發式）
    - API/WebSocket Routes（FastAPI 裝飾器 AST 掃描）
    - Module Tree（src 包結構，>25 檔摺疊）
    - Callers/Callees（import 圖內部邊 Top）
    - Tests by Feature（測試檔 import → 模組反向映射）
    - Config/Agents 概況
    - STATUS_MATRIX 交叉核對（宣稱 vs 實體）
    """
    from collections import defaultdict

    lines = ["## 區塊四：實時結構（工具推導，永不過期）", ""]

    # --- Runtime Entry Points ---
    entries = sorted(
        rel
        for rel, tree in trees.items()
        if any(
            isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare)
            and getattr(n.test.left, "id", "") == "__name__"
            and any(
                isinstance(c, ast.Constant) and c.value == "__main__" for c in n.test.comparators
            )
            for n in tree.body
        )
    )
    lines.append(f"### Runtime Entry Points（{len(entries)}）")
    lines.append("")
    for rel in entries[:60]:
        lines.append(f"- `{rel}`")
    if len(entries) > 60:
        lines.append(f"- …{len(entries) - 60} 未展開（--module 查詢）")
    lines.append("")

    # --- API/WebSocket Routes ---
    route_re = re.compile(r"@(\w+)\.(get|post|put|delete|patch|websocket)\(\s*[\"']([^\"']+)[\"']")
    routes = []
    for rel, tree in sorted(trees.items()):
        if "/api/" not in rel:
            continue
        try:
            src = open(os.path.join(root, rel), encoding="utf-8").read()
        except OSError:
            continue
        for m in route_re.finditer(src):
            routes.append((rel, m.group(2).upper(), m.group(3)))
    ws = [r for r in routes if r[1] == "WEBSOCKET"]
    lines.append(f"### API/WebSocket Routes（{len(routes)}，含 {len(ws)} WS）")
    lines.append("")
    by_file = defaultdict(list)
    for rel, verb, path in routes:
        by_file[rel].append((verb, path))
    for rel in sorted(by_file):
        vs = by_file[rel]
        ws_n = sum(1 for v, _ in vs if v == "WEBSOCKET")
        tag = f"（含 {ws_n} WS）" if ws_n else ""
        lines.append(f"- `{rel}`：{len(vs)} 條{tag}")
        shown = sorted(vs)[:12]
        for verb, path in shown:
            lines.append(f"  - `{verb} {path}`")
        if len(vs) > 12:
            lines.append(f"  - …{len(vs) - 12} 未展開")
    lines.append("")

    # --- Module Tree（src 包）---
    pkgs = defaultdict(list)
    for rel in trees:
        parts = rel.split("/")
        if len(parts) >= 5 and parts[0] == "apps" and parts[2] == "src":
            pkgs["/".join(parts[:-1])].append(parts[-1])
    lines.append(f"### Module Tree（src 包 {len(pkgs)} 個）")
    lines.append("")
    shown = 0
    for pkg in sorted(pkgs, key=lambda p: (-p.count("/"), p)):
        mods = pkgs[pkg]
        if shown >= 45:
            lines.append(f"- …其餘 {len(pkgs) - shown} 包未展開（--module 查詢）")
            break
        if len(mods) <= 25:
            names = ", ".join(m[:-3] if m.endswith(".py") else m + "/" for m in sorted(mods))
            lines.append(f"- `{pkg}`：{names}")
            shown += 1
        else:
            lines.append(f"- `{pkg}`：{len(mods)} 模組（>25 摺疊，--module 查詢）")
            shown += 1
    lines.append("")

    # --- Callers/Callees（內部 import 邊 Top）---
    imported = import_index(trees)
    mod2file = {}
    for rel in trees:
        parts = rel[:-3].split("/")
        for i in range(len(parts)):
            mod2file[".".join(parts[i:])] = rel
    edges = []
    for mod, who in imported.items():
        f = mod2file.get(mod)
        if f and mod != rel_module_of(f):
            for w in sorted(who):
                if w != f:
                    edges.append((w, f, mod))
    top_edges = sorted(edges, key=lambda e: -len(imported.get(e[2], ())))[:25]
    lines.append("### 被引用最多模組 Top 25（callers 數）")
    lines.append("")
    for w, f, mod in top_edges:
        n = len(imported.get(mod, ()))
        lines.append(f"- `{mod}` ← {n} 檔（例：`{os.path.basename(w)}`）")
    lines.append("")

    # --- Tests by Feature ---
    test_of = defaultdict(set)
    for mod, who in imported.items():
        f = mod2file.get(mod)
        if not f:
            continue
        for w in who:
            if w.startswith("tests/"):
                test_of[f].add(w)
    covered = {f for f in test_of if test_of[f]}
    all_src = [
        f for f in trees if f.startswith("apps/backend/src/") and not f.endswith("__init__.py")
    ]
    covered_src = [
        f
        for f in all_src
        if any(m2 == f for m2 in (mod2file.get(m) for m in imported)) and f in covered
    ]
    n_uncovered = len([f for f in all_src if f not in covered])
    lines.append(
        f"### Tests by Feature（backend src {len(all_src)} 模組，{len(covered)} 有測試指向）"
    )
    lines.append("")
    for f in sorted(covered)[:40]:
        ts = sorted(test_of[f])
        lines.append(f"- `{f}` ← {len(ts)} 測試（{os.path.basename(ts[0])}…）")
    if len(covered) > 40:
        lines.append(f"- …{len(covered) - 40} 未展開")
    lines.append(f"- 無測試指向：{n_uncovered} 模組")
    lines.append("")

    # --- Config / Agents 概況 ---
    n_cfg = sum(1 for rel, _, _ in files if rel.startswith("apps/backend/configs/"))
    agent_files = [
        rel
        for rel in trees
        if rel.startswith("apps/backend/src/ai/agents/") and rel.endswith("_agent.py")
    ]
    prov_files = [
        rel
        for rel in trees
        if rel.startswith("apps/backend/src/services/llm/providers/")
        and os.path.basename(rel) not in ("__init__.py", "base.py", "registry.py")
    ]
    lines.append(
        f"### Config/Agents/Providers（configs {n_cfg} 檔；specialized agents {len(agent_files)}；LLM providers {len(prov_files)}）"
    )
    lines.append("")
    lines.append("- providers：" + ", ".join(sorted(os.path.basename(p)[:-3] for p in prov_files)))
    lines.append("")

    # --- STATUS_MATRIX 交叉核對 ---
    lines.extend(verify_status_matrix(root, trees))
    return lines


def rel_module_of(rel):
    """檔案路徑 → 模組名（去 .py，apps/backend/src/ → ai.xxx 形式約定）。"""
    parts = rel[:-3].split("/")
    if rel.startswith("apps/backend/src/"):
        return ".".join(parts[3:])
    return ".".join(parts)


def verify_status_matrix(root, trees):
    """STATUS_MATRIX YAML 宣稱 vs 實體核對（交叉驗證）。"""
    try:
        import yaml  # 延遲導入：pyyaml 在 base 依賴，缺了只降級不崩

        with open(os.path.join(root, "docs/status_matrix.yaml"), encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except ImportError:
        return ["### STATUS_MATRIX 核對（pyyaml 缺，跳過）", ""]
    except (OSError, yaml.YAMLError) as e:
        return [f"### STATUS_MATRIX 核對（讀取失敗：{e}）", ""]

    features = data.get("features") or []
    problems = []
    files_set = set(trees) | {entry[0] for entry in _LAST_FILES}

    def path_exists(path):
        """檔案或目錄皆可：精確匹配、掃描前綴、磁碟存在三路皆收。"""
        if path in files_set:
            return True
        prefix = path if path.endswith("/") else path + "/"
        if any(f.startswith(prefix) for f in files_set):
            return True
        return os.path.exists(os.path.join(root, path))

    for feat in features:
        fid = feat.get("id", "?")
        for path in feat.get("implementation", []) or []:
            if not path_exists(path):
                problems.append(f"[{fid}] implementation 不存在：{path}")
        for path in feat.get("tests", []) or []:
            if not path_exists(path):
                problems.append(f"[{fid}] tests 不存在：{path}")
    _LAST_STATUS_VERIFY.update(
        total=len(features),
        ok=len(features) - len(problems),
        problems=problems,
    )
    lines = [f"### STATUS_MATRIX 核對（{len(features)} 條目）", ""]
    if problems:
        lines.append(f"- ⛔ {len(problems)} 項宣稱與實體不符：")
        for p in problems[:20]:
            lines.append(f"  - {p}")
    else:
        lines.append("- ✅ 全部 implementation/tests 路徑存在（宣稱有實體）")
    lines.append("")
    return lines


def block_behavior(root, files):
    lines = ["## 區塊三：行為核心（理解用）", ""]
    fv = os.path.join(root, "scripts/final_verification.py")
    gates = []
    try:
        import re

        src = open(fv, encoding="utf-8").read()
        gates = re.findall(r'checks\.append\(\("([^"]+)"', src)
    except OSError:
        pass
    lines.append(f"- 驗收門（{len(gates)}）：")
    for g in gates:
        lines.append(f"  - {g}")
    ymls = [r for r, _, _ in files if r.endswith((".yaml", ".yml"))]
    lines.append(f"- 配置檔：{len(ymls)}")
    for rel in sorted(ymls)[:20]:
        lines.append(f"  - `{rel}`")
    pys = []
    for rel, _, _ in files:
        if rel.endswith(".py") and not rel.startswith("tests/"):
            try:
                with open(os.path.join(root, rel), encoding="utf-8") as f:
                    pys.append((rel, sum(1 for _ in f)))
            except OSError:
                continue
    lines.append("- 最大源碼檔 Top 10（行數）：")
    for rel, n in sorted(pys, key=lambda t: -t[1])[:10]:
        lines.append(f"  - `{rel}`：{n}")
    lines.append("")
    lines.extend(block_dep_usage(root, files))
    return lines


HEAVY_DEPS = {
    "torch",
    "transformers",
    "chromadb",
    "sentence_transformers",
    "pandas",
    "sklearn",
    "scipy",
    "redis",
    "spacy",
    "tensorflow",
    "cv2",
    "PIL",
}
# Eager-check subset: base-tier members (Pillow/scipy per pyproject) excluded —
# only non-base heavies (ml/vector tiers) must stay lazy (§X #259).
EAGER_HEAVY = HEAVY_DEPS - {"PIL", "scipy"}


def block_dep_usage(root, files):
    """各檔依賴使用情況：有參與演算 vs 寫而不用（特別標記）。

    只列有未使用 import 的檔（乾淨的不佔預算）；__init__.py 跳過
    （重導出語義，誤報重災區）。星號/動態導入無法判定，不列。
    """
    lines = ["### 依賴使用（演算參與）", ""]
    bad_files, bad_total, heavy_hits = 0, 0, []
    probe_files = 0
    shown = 0
    for rel, _, _ in sorted(files):
        if not rel.endswith(".py") or os.path.basename(rel) == "__init__.py":
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
        bound = {}  # 本地名 -> 來源模組
        noqa_lines = set()
        try:
            srclines = open(os.path.join(root, rel), encoding="utf-8").read().split("\n")
        except OSError:
            srclines = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    name = a.asname or (a.name or "").split(".")[0]
                    if name and name != "*":
                        bound[name] = a.name
            elif isinstance(node, ast.ImportFrom):
                if node.module == "__future__":
                    continue  # 編譯期 pragma，非依賴
                if any(a.name == "*" for a in node.names):
                    continue
                for a in node.names:
                    if a.name and a.name != "*":
                        bound[a.asname or a.name] = node.module or ""
        # noqa 意圖重導出 + 字串註解用量一併視為使用（僅註解位置字串，
        # 不含 docstring——否則"Uses transformers"之類文案會洗白真未用）
        ann_strs = []
        for node in ast.walk(tree):
            for field in ("annotation", "returns"):
                v = getattr(node, field, None)
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    ann_strs.append(v.value)
            if isinstance(node, ast.AnnAssign) and isinstance(node.annotation, ast.Constant):
                if isinstance(node.annotation.value, str):
                    ann_strs.append(node.annotation.value)
        str_used = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", " ".join(ann_strs)))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)) and hasattr(node, "lineno"):
                if any(
                    "noqa"
                    in (srclines[node.lineno - 1] if 0 < node.lineno <= len(srclines) else "")
                    for _ in [0]
                ):
                    for a in node.names:
                        str_used.add(a.asname or a.name)
        if not bound:
            continue
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
        used |= str_used
        # 可用性探針：try 內僅 import + return True（except ImportError）——有意為之，不算未使用
        probes = set()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
            if len(node.body) != 2:
                continue
            imp, ret = node.body
            if not isinstance(imp, ast.Import):
                continue
            if not (
                isinstance(ret, ast.Return)
                and isinstance(ret.value, ast.Constant)
                and ret.value.value is True
            ):
                continue
            if not any(
                isinstance(h.type, ast.Name) and h.type.id == "ImportError" for h in node.handlers
            ):
                continue
            for a in imp.names:
                if a.asname:
                    probes.add(a.asname)
                elif a.name:
                    probes.add(a.name.split(".")[0])
        # 按頂層模組聚合：同模組任一名被用即算參與（殺 deferred-import 噪音）
        from collections import defaultdict

        mod_names = defaultdict(list)
        for k, v in bound.items():
            mod_names[(v or "").split(".")[0]].append(k)
        unused = []
        probed = []
        for top, names in mod_names.items():
            if top and not any(n in used for n in names):
                if all(n in probes for n in names):
                    probed.append(top)
                else:
                    unused.extend((n, next(v for k, v in bound.items() if k == n)) for n in names)
        if not unused:
            if probed:
                probe_files += 1
            continue
        bad_files += 1
        bad_total += len(unused)
        marks = []
        for k, v in sorted(unused):
            top = (v or "").split(".")[0]
            tag = " 🔥重依賴" if top in HEAVY_DEPS else ""
            marks.append(f"{k}←{v}{tag}")
            if tag:
                heavy_hits.append(rel)
        if probed:
            probe_files += 1
            marks.append(f"可用性探針:{','.join(sorted(set(probed)))}")
        if shown < 200:
            lines.append(f"- `{rel}`：未使用 {len(unused)}（{'; '.join(marks)}）")
            shown += 1
    lines.append(f"- 有未使用 import 的檔：{bad_files}，共 {bad_total} 項（僅列前 200）")
    lines.append(f"- 其中重依賴未使用：{len(set(heavy_hits))} 檔")
    lines.append(f"- 可用性探針檔（有意為之，不計入）：{probe_files}")
    lines.append("")
    lines.extend(block_eager_heavy(root, files))
    return lines


def block_eager_heavy(root, files):
    """頂層 eager 重依賴（§X #259 懶加載紀律）：模組層 `import torch` 即違規。

    只認 tree.body 直屬 Import（try/函數內延遲不算）；`__init__` 單列。
    """
    lines = ["### 頂層 eager 重依賴（違規即列）", ""]
    bad = []
    for rel, _, _ in sorted(files):
        if not rel.endswith(".py"):
            continue
        if not rel.startswith("apps/backend/src/"):
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
        for node in tree.body:
            mods = []
            if isinstance(node, ast.Import):
                mods = [(a.asname or a.name.split(".")[0], a.name) for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [(a.asname or a.name, node.module) for a in node.names]
            for local, mod in mods:
                if (mod or "").split(".")[0] in EAGER_HEAVY:
                    bad.append((rel, (mod or "").split(".")[0], local))
    lines.append(f"- 違規：{len(bad)} 項")
    for rel, top, local in bad[:30]:
        lines.append(f"  - `{rel}`：`{top}`（as {local}）")
    if len(bad) > 30:
        lines.append(f"  - …{len(bad) - 30} 未展開")
    lines.append("")
    return lines


def cmd_module(args):
    """查詢模式：--module <path-substring> 即時輸出該模組的實時情報。

    退出碼：0 找到 / 1 無匹配 / 2 工具錯。永不寫檔（查詢不產生副產物）。
    """
    root = os.path.abspath(args.root)
    try:
        files = walk_files(root)
        trees = parse_trees(root, files)
    except Exception as e:
        print(f"TOOL ERROR: {e}")
        return 2
    needle = args.module
    matches = sorted(rel for rel in trees if needle in rel.replace("/", ".") or needle in rel)
    if not matches:
        print(f"NO MATCH: {needle}")
        return 1
    imported = import_index(trees)
    for rel in matches[: args.limit]:
        mod = rel_module_of(rel)
        callers = sorted(
            w
            for m, who in imported.items()
            if m == mod or m.startswith(mod + ".")
            for w in who
            if w != rel
        )
        tree = trees[rel]
        imports = sorted(imports_of(tree, rel))
        src_imports = [m for m in imports if mod2file_exists(m, trees)]
        tests = sorted(
            w
            for m, who in imported.items()
            if m == mod or m.startswith(mod + ".")
            for w in who
            if w.startswith("tests/")
        )
        try:
            n_lines = sum(1 for _ in open(os.path.join(root, rel), encoding="utf-8"))
        except OSError:
            n_lines = 0
        print(f"## {rel}")
        print(
            f"lines: {n_lines} | imports(倉內): {len(src_imports)} | callers: {len(callers)} | tests: {len(tests)}"
        )
        if src_imports:
            print("imports:")
            for m in src_imports[:20]:
                print(f"  -> {m}")
        if callers:
            print("called_by:")
            for w in callers[:20]:
                print(f"  <- {w}")
        if tests:
            print("tests:")
            for t in tests[:20]:
                print(f"  - {t}")
        defs = [
            f"{type(n).__name__}:{getattr(n, 'name', '?')}"
            for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        if defs:
            print(
                f"top-level defs ({len(defs)}): {', '.join(defs[:15])}{' …' if len(defs) > 15 else ''}"
            )
        print()
    return 0


def mod2file_exists(mod, trees):
    for rel in trees:
        if rel_module_of(rel) == mod or rel_module_of(rel).startswith(mod + "."):
            return True
    return False


def main():
    """契約：0 預算內 / 1 超預算（總行數或任一分域）/ 2 工具自身錯誤。"""
    ap = argparse.ArgumentParser(description="專案地圖生成器（四區塊+萬行預算門+查詢模式）")
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="docs/PROJECT_MAP_GENERATED.md")
    ap.add_argument("--budget", type=int, default=10000)
    ap.add_argument("--history", default="docs/.project_map_history.jsonl")
    ap.add_argument("--no-history", action="store_true")
    ap.add_argument(
        "--module",
        default=None,
        help="查詢模式：輸出匹配模組的實時 callers/callees/tests/defs，不寫檔",
    )
    ap.add_argument("--limit", type=int, default=5, help="查詢模式最多顯示檔數")
    args = ap.parse_args()
    if args.module:
        return cmd_module(args)
    root = os.path.abspath(args.root)

    try:
        files = walk_files(root)
        _LAST_FILES.clear()
        _LAST_FILES.extend(files)
        usage = domain_file_usage(root, files)
        over_domains = check_domain_budgets(usage)
        trees = parse_trees(root, files)
        b1 = block_dependencies(root, files, trees)
        b2 = block_collisions(root, files)
        b4 = block_structure(root, files, trees)
        b3 = block_behavior(root, files)
    except Exception as e:
        print(f"TOOL ERROR: {e}")
        return 2
    body = b1 + b2 + b4 + b3
    counts = {
        "區塊一依賴": len(b1),
        "區塊二碰撞": len(b2),
        "區塊四結構": len(b4),
        "區塊三行為": len(b3),
    }
    total = len(body)
    # 預算只計三區塊行數；頁首與 ## DIAG 尾段不計（門檻穩定）。
    top_block = max(counts.items(), key=lambda kv: kv[1])[0]
    failed = total > args.budget or bool(over_domains)

    head = [
        "<!-- Generated by scripts/gen_project_map.py — 手不改，重跑覆蓋 -->",
        f"# 專案地圖（生成於 {datetime.date.today()}，{len(files)} 檔）",
        "",
        "> 查詢模式：`python scripts/gen_project_map.py --module <path-片段>`",
        "> 即時輸出 callers/callees/tests/defs（不寫檔，永不過期）。",
        "",
    ]
    if failed:
        head.append(f"> ⛔ 超預算：{total} > {args.budget} 行——專案有病，先治病。吃行大戶：")
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
            head.append(f"> - {k}：{v} 行")
        for d, u, b in over_domains:
            head.append(f"> - 分域超標 `{d}`：{u} > {b} 檔")
        head.append("")
    else:
        head.append(f"> ✅ {total}/{args.budget} 行，預算內。")
        head.append("")
    diag = render_diag(
        "fail" if failed else "ok",
        total,
        args.budget,
        usage,
        over_domains,
        dict(_LAST_ORPHAN_COUNTS),
        top_block if failed else "",
        status_verify=dict(_LAST_STATUS_VERIFY),
    )
    # 趨勢：歷史只記三區塊行數+孤兒+分域（與預算同口徑）；TREND 段不計入預算。
    trend = []
    if not args.no_history:
        record = {
            "date": str(datetime.date.today()),
            "total": total,
            "L1": _LAST_ORPHAN_COUNTS.get("L1", 0),
            "L2": _LAST_ORPHAN_COUNTS.get("L2", 0),
            "L3": _LAST_ORPHAN_COUNTS.get("L3", 0),
            "backend": usage.get("apps/backend/src", 0),
            "scripts": usage.get("scripts", 0),
            "desktop": usage.get("apps/desktop-app", 0),
            "packages": usage.get("packages/", 0),
        }
        ok_hist = append_history(args.history, record)
        hist = load_history(args.history) if ok_hist else []
        trend = render_trend(hist if hist else [record])
    else:
        trend = ["## TREND", "", "runs: 0", "verdict: history disabled", ""]
    out = head + body + trend + diag
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
    except OSError as e:
        print(f"TOOL ERROR: {e}")
        return 2
    print("\n".join(diag))
    if failed:
        print(f"OVER BUDGET: {total} > {args.budget} {counts} domains={over_domains}")
        return 1
    print(f"OK: {total}/{args.budget} lines {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
