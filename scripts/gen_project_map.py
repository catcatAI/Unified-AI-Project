#!/usr/bin/env python3
"""專案地圖生成器 — 依賴排錯 + 碰撞定位 + 行為理解，萬行預算封頂。

三區塊：
  1. 依賴（AST 掃 import，第三方/倉內分開，排錯用）
  2. 碰撞索引（同檔名多路徑，深→淺；重名全展開，其餘按目錄捲）
  3. 行為核心（驗收門 + 配置鍵 + 大檔，半自動指標）

預算即診斷：輸出超 `--budget` 行即 exit 1 + 兇手排行（超標=專案有病）。
只用 stdlib。產物標 Generated，手不改。
"""

import argparse
import ast
import datetime
import hashlib
import os
import sys

EXCLUDE_DIRS = {
    ".git", ".venv", "node_modules", "__pycache__", ".pytest_cache",
    "data", ".cache", "checkpoints", ".hypothesis", "dist", "build",
    ".mypy_cache", ".ruff_cache",
}
SKIP_EXT = {".pyc", ".pyo", ".pyd", ".so", ".o"}


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
    """
    from collections import defaultdict

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
    lines = ["### 疑似孤兒檔（候選）", ""]
    lines.append(f"- 共 {len(orphans)} 檔（動態加載盲區見上，個案定性前不刪）")
    for rel in sorted(orphans)[:40]:
        lines.append(f"  - `{rel}`")
    if len(orphans) > 40:
        lines.append(f"  - …{len(orphans) - 40} 未展開")
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
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    name = (a.asname or (a.name or "").split(".")[0])
                    if name and name != "*":
                        bound[name] = a.name
            elif isinstance(node, ast.ImportFrom):
                if any(a.name == "*" for a in node.names):
                    continue
                for a in node.names:
                    if a.name and a.name != "*":
                        bound[a.asname or a.name] = node.module or ""
        if not bound:
            continue
        used = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used.add(node.id)
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
    return lines


def main():
    ap = argparse.ArgumentParser(description="專案地圖生成器（三區塊+萬行預算門）")
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="docs/PROJECT_MAP_GENERATED.md")
    ap.add_argument("--budget", type=int, default=10000)
    args = ap.parse_args()
    root = os.path.abspath(args.root)

    files = walk_files(root)
    b1 = block_dependencies(root, files)
    b2 = block_collisions(root, files)
    b3 = block_behavior(root, files)
    body = b1 + b2 + b3
    counts = {"區塊一依賴": len(b1), "區塊二碰撞": len(b2), "區塊三行為": len(b3)}
    total = len(body)

    head = [
        "<!-- Generated by scripts/gen_project_map.py — 手不改，重跑覆蓋 -->",
        f"# 專案地圖（生成於 {datetime.date.today()}，{len(files)} 檔）",
        "",
    ]
    if total > args.budget:
        head.append(f"> ⛔ 超預算：{total} > {args.budget} 行——專案有病，先治病。吃行大戶：")
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
            head.append(f"> - {k}：{v} 行")
        head.append("")
        out = head + body
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\n".join(out))
        print(f"OVER BUDGET: {total} > {args.budget} {counts}")
        return 1
    out = head + [f"> ✅ {total}/{args.budget} 行，預算內。", ""] + body
    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print(f"OK: {total}/{args.budget} lines {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
