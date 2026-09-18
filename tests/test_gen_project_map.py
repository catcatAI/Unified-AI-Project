"""gen_project_map.py 單元測試 — 工具 verdicts 的地基，先證工具對。

Hermetic: tmp_path 自建迷你樹，不依賴倉庫內容。
"""

import importlib.util
import os

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
TOOL = os.path.join(REPO_ROOT, "scripts", "gen_project_map.py")


def load_tool():
    spec = importlib.util.spec_from_file_location("gen_project_map", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def tiny_tree(tmp_path):
    base = tmp_path / "apps" / "backend" / "src"
    (base / "pkg").mkdir(parents=True)
    (base / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    (base / "pkg" / "used.py").write_text("VALUE = 1\n", encoding="utf-8")
    (base / "pkg" / "user.py").write_text(
        "from pkg.used import VALUE\nprint(VALUE)\n", encoding="utf-8"
    )
    (base / "pkg" / "orphan.py").write_text("X = 2\n", encoding="utf-8")
    (base / "pkg" / "rel.py").write_text(
        "from .used import VALUE\nprint(VALUE)\n", encoding="utf-8"
    )
    cfg = tmp_path / "apps" / "backend" / "configs"
    cfg.mkdir(parents=True)
    (cfg / "app.yaml").write_text("rlaif_buffer:\n  enabled: false\n", encoding="utf-8")
    (base / "pkg" / "gated.py").write_text("Y = 3\n", encoding="utf-8")
    return str(tmp_path)


def _orphan_lines(mod, root):
    files = mod.walk_files(root)
    lines = mod.block_orphans(root, files)
    return [line for line in lines if line.strip().startswith("- `")]


def test_orphan_lists_unreferenced(tiny_tree):
    mod = load_tool()
    rels = _orphan_lines(mod, tiny_tree)
    assert any("orphan.py" in line for line in rels)
    # 被引用的 used.py 不得列入；只引用別人、自己無人引用的 user.py 列入才是正確語義
    assert not any("used.py" in line for line in rels)
    assert any("user.py" in line for line in rels)


def test_orphan_relative_import_resolves(tiny_tree):
    mod = load_tool()
    rels = _orphan_lines(mod, tiny_tree)
    # rel.py 用相對導入，used.py 不得因解析失敗而被誤列
    assert not any("used.py" in line for line in rels)


def test_orphan_config_gate_is_L3_folded(tiny_tree):
    mod = load_tool()
    # rlaif_buffer fake module to trigger the gate path
    base = os.path.join(tiny_tree, "apps", "backend", "src", "pkg")
    with open(os.path.join(base, "rlaif_buffer.py"), "w", encoding="utf-8") as f:
        f.write("Z = 4\n")
    files = mod.walk_files(tiny_tree)
    lines = mod.block_orphans(tiny_tree, files)
    text = "\n".join(lines)
    # L3 只折疊計數：檔名不展開，但 L3 計數必須 ≥1
    assert not any("rlaif_buffer.py" in line for line in _orphan_lines(mod, tiny_tree))
    assert "L3=" in text
    import re

    m = re.search(r"L3=(\d+)", text)
    assert m and int(m.group(1)) >= 1


def test_orphan_entry_like_is_L2_folded(tiny_tree):
    mod = load_tool()
    base = os.path.join(tiny_tree, "apps", "backend", "src", "pkg")
    with open(os.path.join(base, "cli.py"), "w", encoding="utf-8") as f:
        f.write("Q = 5\n")
    rels = _orphan_lines(mod, tiny_tree)
    # 疑似入口不進 L1 展開；普通孤兒仍展開並帶 L1 標記
    assert not any("cli.py" in line for line in rels)
    assert any("orphan.py" in line and "L1" in line for line in rels)


def test_domain_budgets_ok_and_over(tiny_tree):
    mod = load_tool()
    files = mod.walk_files(tiny_tree)
    usage = mod.domain_file_usage(tiny_tree, files)
    assert usage["apps/backend/src"] >= 5
    assert mod.check_domain_budgets(usage, {"apps/backend/src": 10000}) == []
    over = mod.check_domain_budgets(usage, {"apps/backend/src": 1})
    assert over and over[0][0] == "apps/backend/src"


def test_render_diag_stable_keys(tmp_path):
    mod = load_tool()
    usage = {
        "apps/backend/src": 10,
        "scripts": 5,
        "apps/desktop-app": 1,
        "packages/": 0,
        "rest": 3,
    }
    diag = mod.render_diag("ok", 100, 10000, usage, [], {"L1": 0, "L2": 0, "L3": 0}, "")
    text = "\n".join(diag)
    assert diag[0] == "## DIAG"
    for key in (
        "status: ok",
        "total: 100",
        "budget: 10000",
        "domains:",
        "apps/backend/src: 10/1400",
        "orphans: L1=0 L2=0 L3=0",
        "actions:",
    ):
        assert key in text, key


def test_main_over_budget_returns_1_with_diag(tmp_path, monkeypatch):
    mod = load_tool()
    tiny = tmp_path / "t"
    (tiny / "scripts").mkdir(parents=True)
    (tiny / "scripts" / "a.py").write_text("X = 1\n", encoding="utf-8")
    out = str(tmp_path / "map.md")
    monkeypatch.setattr(
        "sys.argv",
        ["gen_project_map.py", "--root", str(tiny), "--output", out, "--budget", "1"],
    )
    rc = mod.main()
    assert rc == 1
    body = open(out, encoding="utf-8").read()
    assert "## DIAG" in body and "status: fail" in body


def _run_map(mod, monkeypatch, root, out, *extra):
    import sys

    monkeypatch.setattr(
        "sys.argv",
        [
            "gen_project_map.py",
            "--root",
            str(root),
            "--output",
            str(out),
            "--history",
            str(out) + ".hist.jsonl",
            *extra,
        ],
    )
    return mod.main()


def test_trend_insufficient_then_stable(tmp_path, monkeypatch):
    mod = load_tool()
    tiny = tmp_path / "t"
    (tiny / "scripts").mkdir(parents=True)
    (tiny / "scripts" / "a.py").write_text("X = 1\n", encoding="utf-8")
    out = tmp_path / "map.md"
    assert _run_map(mod, monkeypatch, tiny, out) == 0
    assert "insufficient history" in out.read_text(encoding="utf-8")
    assert _run_map(mod, monkeypatch, tiny, out) == 0
    body = out.read_text(encoding="utf-8")
    assert "verdict: stable" in body


def test_trend_degrading_on_growth(tmp_path, monkeypatch):
    mod = load_tool()
    tiny = tmp_path / "t"
    (tiny / "scripts").mkdir(parents=True)
    out = tmp_path / "map.md"
    for round_ in range(3):
        d = tiny / "scripts" / f"batch{round_}"
        d.mkdir(parents=True)
        for i in range(30):
            (d / f"f{i}.py").write_text("X = 1\n", encoding="utf-8")
        assert _run_map(mod, monkeypatch, tiny, out) == 0
    assert "verdict: degrading" in out.read_text(encoding="utf-8")


def test_no_history_flag(tmp_path, monkeypatch):
    mod = load_tool()
    tiny = tmp_path / "t"
    (tiny / "scripts").mkdir(parents=True)
    (tiny / "scripts" / "a.py").write_text("X = 1\n", encoding="utf-8")
    out = tmp_path / "map.md"
    assert _run_map(mod, monkeypatch, tiny, out, "--no-history") == 0
    body = out.read_text(encoding="utf-8")
    assert "history disabled" in body and "## DIAG" in body
    assert not (tmp_path / "map.md.hist.jsonl").exists()


def test_history_corrupt_tolerated(tmp_path, monkeypatch):
    mod = load_tool()
    tiny = tmp_path / "t"
    (tiny / "scripts").mkdir(parents=True)
    (tiny / "scripts" / "a.py").write_text("X = 1\n", encoding="utf-8")
    out = tmp_path / "map.md"
    hist = tmp_path / "map.md.hist.jsonl"
    hist.write_text("NOT JSON{{{\n", encoding="utf-8")
    assert _run_map(mod, monkeypatch, tiny, out) == 0
    assert "insufficient history" in out.read_text(encoding="utf-8")


def test_self_artifacts_excluded_from_scan(tmp_path):
    mod = load_tool()
    tiny = tmp_path / "t"
    (tiny / "docs").mkdir(parents=True)
    (tiny / "docs" / "PROJECT_MAP_GENERATED.md").write_text("old\n", encoding="utf-8")
    (tiny / "docs" / ".project_map_history.jsonl").write_text("{}\n", encoding="utf-8")
    (tiny / "docs" / "NOTE.md").write_text("n\n", encoding="utf-8")
    rels = [rel for rel, _, _ in mod.walk_files(str(tiny))]
    assert "docs/NOTE.md" in rels
    assert not any("PROJECT_MAP_GENERATED.md" in r for r in rels)
    assert not any(".project_map_history.jsonl" in r for r in rels)


def test_dep_usage_unused_and_noqa(tmp_path):
    mod = load_tool()
    d = tmp_path / "s"
    d.mkdir()
    (d / "a.py").write_text("import os\nimport sys\nprint(os.name)\n", encoding="utf-8")
    (d / "b.py").write_text("from x import y  # noqa: F401\nprint(1)\n", encoding="utf-8")
    files = mod.walk_files(str(tmp_path))
    lines = mod.block_dep_usage(str(tmp_path), files)
    text = "\n".join(lines)
    assert "a.py" in text and "sys" in text
    assert "b.py" not in text


def test_dep_usage_string_annotation_counts(tmp_path):
    mod = load_tool()
    d = tmp_path / "s"
    d.mkdir()
    (d / "c.py").write_text(
        "from m import Thing\ndef f(x: 'Thing') -> None:\n    pass\n",
        encoding="utf-8",
    )
    files = mod.walk_files(str(tmp_path))
    lines = mod.block_dep_usage(str(tmp_path), files)
    assert not any("c.py" in line for line in lines)


def test_dep_usage_future_excluded(tmp_path):
    mod = load_tool()
    d = tmp_path / "s"
    d.mkdir()
    (d / "e.py").write_text("from __future__ import annotations\nX: int = 1\n", encoding="utf-8")
    files = mod.walk_files(str(tmp_path))
    lines = mod.block_dep_usage(str(tmp_path), files)
    assert not any("e.py" in line for line in lines)


def test_eager_heavy_top_vs_function(tmp_path):
    mod = load_tool()
    d = tmp_path / "apps" / "backend" / "src"
    d.mkdir(parents=True)
    (d / "bad.py").write_text("import torch\nprint(torch.__version__)\n", encoding="utf-8")
    (d / "ok.py").write_text(
        "def f():\n    import torch\n    return torch.__version__\n", encoding="utf-8"
    )
    files = mod.walk_files(str(tmp_path))
    lines = mod.block_dep_usage(str(tmp_path), files)
    text = "\n".join(lines)
    assert "bad.py" in text and "ok.py" not in text
