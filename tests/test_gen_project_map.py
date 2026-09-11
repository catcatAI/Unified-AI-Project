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


def test_orphan_config_gate_tagged(tiny_tree):
    mod = load_tool()
    # rlaif_buffer fake module to trigger the gate path
    base = os.path.join(tiny_tree, "apps", "backend", "src", "pkg")
    with open(os.path.join(base, "rlaif_buffer.py"), "w", encoding="utf-8") as f:
        f.write("Z = 4\n")
    rels = _orphan_lines(mod, tiny_tree)
    gated = [line for line in rels if "rlaif_buffer.py" in line]
    assert gated and "配置門控候選" in gated[0]


def test_dep_usage_unused_and_noqa(tmp_path):
    mod = load_tool()
    d = tmp_path / "s"
    d.mkdir()
    (d / "a.py").write_text(
        "import os\nimport sys\nprint(os.name)\n", encoding="utf-8"
    )
    (d / "b.py").write_text(
        "from x import y  # noqa: F401\nprint(1)\n", encoding="utf-8"
    )
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
    (d / "e.py").write_text(
        "from __future__ import annotations\nX: int = 1\n", encoding="utf-8"
    )
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
