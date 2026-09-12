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
"""

import argparse
import ast
import datetime
import hashlib
import os
import re
import sys

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    "data", ".cache", "checkpoints", ".hypothesis", "dist", "build",
    ".mypy_cache", ".ruff_cache",
}
SKIP_EXT = {".pyc", ".pyo", ".pyd", ".so", ".o"}

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


def render_diag(status, total, budget, usage, over_domains, counts, top_block):
    """固定機器可讀尾段（CI 只依賴退出碼 + 本段鍵名；鍵名穩定，勿改）。"""
    lines = ["## DIAG", "", f"status: {status}", f"total: {total}", f"budget: {budget}"]
    lines.append("domains:")
    for dom in list(DOMAIN_FILE_BUDGETS) + ["rest"]:
        b = DOMAIN_FILE_BUDGETS.get(dom)
        lines.append(f"  {dom}: {usage.get(dom, 0)}/{b if b is not None else 'unlimited'}")
    lines.append(
        f"orphans: L1={counts.get('L1', 0)} L2={counts.get('L2', 0)} L3={counts.get('L3', 0)}"
    )
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


def walk_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")
        )
        for fn in sorted(filenames):
            if os.path.splitext(fn)[1] in SKIP_EXT:
                continue
            fp = os.path.join(dirpath, fn)
            try:
                st = os.stat(fp)
            except OSError:
                continue
            rel = os.path.relpath(fp, root)
            out.append((rel, st.st_size, st.st_mtime))
    return out


def block_dependencies(root, files):
    import sys as _sys

    stdlib = set(getattr(_sys, "stdlib_module_names", ()))
    third, first, edges = {}, {}, 0
    roots = ("apps", "packages", "core", "ai", "api", "hsp",
             "services", "tests", "scripts", "tools")
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
    lines.append(f"- Python 檔掃描：{sum(1 for r, _, _ in files if r.endswith('.py'))}，import 邊：{edges}")
    lines.append("- 第三方 Top（引用檔數）：")
    for mod, n in sorted(third.items(), key=lambda kv: -kv[1])[:15]:
        lines.append(f"  - `{mod}`：{n}")
    lines.append("- 倉內根 Top：")
    for mod, n in sorted(first.items(), key=lambda kv: -kv[1])[:15]:
        lines.append(f"  - `{mod}`：{n}")
    lines.append("")
    lines.extend(block_orphans(root, files))
    return lines


def block_orphans(root, files):
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

    imported = defaultdict(set)
    trees = {}
    for rel, _, _ in files:
        if not rel.endswith(".py"):
            continue
        try:
            with open(os.path.join(root, rel), encoding="utf-8") as f:
                trees[rel] = ast.parse(f.read())
        except (OSError, SyntaxError, ValueError):
            continue
    for rel, tree in trees.items():
        parts = rel[:-3].split("/")
        base = parts[:-1]  # __init__ 與模組皆去尾一層（包路徑）
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name:
                        imported[a.name].add(rel)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    pre = base[:len(base) - node.level + 1] if node.level > 1 else base
                    if node.module:
                        full = ".".join(pre + node.module.split("."))
                        if full:
                            imported[full].add(rel)
                    else:
                        # from . import a, b（函數級延遲聚合常見式）— 成員即子模組
                        for a in node.names:
                            if a.name and a.name != "*":
                                imported[".".join(pre + [a.name])].add(rel)
                elif node.module:
                    imported[node.module].add(rel)
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
    _LAST_ORPHAN_COUNTS.update(
        {"L1": len(graded["L1"]), "L2": graded["L2"], "L3": graded["L3"]}
    )
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
        if len(items) <= 25:
            lines.append(f"  - `{label}`：{len(items)} 檔，{tot // 1024}KB")
            for rel, size in sorted(items):
                lines.append(f"    - `{os.path.basename(rel)}`（{size // 1024}KB）")
        else:
            lines.append(f"  - `{label}`：{len(items)} 檔，{tot // 1024}KB（…{len(items)} 未展開，用工具查）")
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
    "torch", "transformers", "chromadb", "sentence_transformers", "pandas",
    "sklearn", "scipy", "redis", "spacy", "tensorflow", "cv2", "PIL",
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
                    name = (a.asname or (a.name or "").split(".")[0])
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
                if any("noqa" in (srclines[node.lineno - 1] if 0 < node.lineno <= len(srclines) else "")
                       for _ in [0]):
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
            if not (isinstance(ret, ast.Return) and isinstance(ret.value, ast.Constant)
                    and ret.value.value is True):
                continue
            if not any(isinstance(h.type, ast.Name) and h.type.id == "ImportError"
                       for h in node.handlers):
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


def main():
    """契約：0 預算內 / 1 超預算（總行數或任一分域）/ 2 工具自身錯誤。"""
    ap = argparse.ArgumentParser(description="專案地圖生成器（三區塊+萬行預算門）")
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="docs/PROJECT_MAP_GENERATED.md")
    ap.add_argument("--budget", type=int, default=10000)
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    try:
        files = walk_files(root)
        usage = domain_file_usage(root, files)
        over_domains = check_domain_budgets(usage)
        b1 = block_dependencies(root, files)
        b2 = block_collisions(root, files)
        b3 = block_behavior(root, files)
    except Exception as e:
        print(f"TOOL ERROR: {e}")
        return 2
    body = b1 + b2 + b3
    counts = {"區塊一依賴": len(b1), "區塊二碰撞": len(b2), "區塊三行為": len(b3)}
    total = len(body)
    # 預算只計三區塊行數；頁首與 ## DIAG 尾段不計（門檻穩定）。
    top_block = max(counts.items(), key=lambda kv: kv[1])[0]
    failed = total > args.budget or bool(over_domains)

    head = [
        "<!-- Generated by scripts/gen_project_map.py — 手不改，重跑覆蓋 -->",
        f"# 專案地圖（生成於 {datetime.date.today()}，{len(files)} 檔）",
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
    )
    out = head + body + diag
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
