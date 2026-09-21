"""gen_status_matrix.py 測試 — 三層核對與生成視圖的地基。"""

import importlib.util
import os

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..")
TOOL = os.path.join(REPO_ROOT, "scripts", "gen_status_matrix.py")

yaml = pytest.importorskip("yaml")


def load_tool():
    spec = importlib.util.spec_from_file_location("gen_status_matrix", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_yaml(tmp_path, text):
    p = tmp_path / "status.yaml"
    p.write_text(text, encoding="utf-8")
    return str(p)


VALID_MIN = (
    "features:\n"
    "  - id: f1\n"
    "    domain: d\n"
    "    claim: c\n"
    "    status: verified\n"
    "    implementation: [a.py]\n"
    "    verify_command: 'true'\n"
)


def test_check_pass_on_valid(tmp_path):
    mod = load_tool()
    (tmp_path / "a.py").write_text("x=1", encoding="utf-8")
    data = yaml.safe_load(open(write_yaml(tmp_path, VALID_MIN), encoding="utf-8"))
    assert mod.check(str(tmp_path), data) == []


def test_check_missing_required_field(tmp_path):
    mod = load_tool()
    data = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                "features:\n  - id: f1\n    status: wired\n    domain: d\n",
            ),
            encoding="utf-8",
        )
    )
    problems = mod.check(str(tmp_path), data)
    assert any("claim" in p for p in problems)


def test_check_bad_status_value(tmp_path):
    mod = load_tool()
    data = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                "features:\n"
                "  - id: f1\n"
                "    domain: d\n"
                "    claim: c\n"
                "    status: done\n",
            ),
            encoding="utf-8",
        )
    )
    problems = mod.check(str(tmp_path), data)
    assert any("不合法" in p for p in problems)


def test_check_duplicate_id(tmp_path):
    mod = load_tool()
    data = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                VALID_MIN + "  - id: f1\n    domain: d\n    claim: c\n    status: wired\n",
            ),
            encoding="utf-8",
        )
    )
    problems = mod.check(str(tmp_path), data)
    assert any("重複" in p for p in problems)


def test_check_entity_missing_path(tmp_path):
    mod = load_tool()
    data = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                "features:\n"
                "  - id: f1\n"
                "    domain: d\n"
                "    claim: c\n"
                "    status: wired\n"
                "    implementation: [ghost/dir]\n",
            ),
            encoding="utf-8",
        )
    )
    problems = mod.check(str(tmp_path), data)
    assert any("ghost/dir" in p for p in problems)


def test_check_semantic_bidirectional(tmp_path):
    mod = load_tool()
    # verified 無指令 → 違規
    data = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                "features:\n"
                "  - id: f1\n"
                "    domain: d\n"
                "    claim: c\n"
                "    status: verified\n",
            ),
            encoding="utf-8",
        )
    )
    assert any("缺 verify_command" in p for p in mod.check(str(tmp_path), data))
    # wired 有指令 → 違規（反向）
    (tmp_path / "a.py").write_text("x=1", encoding="utf-8")
    data2 = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                "features:\n"
                "  - id: f2\n"
                "    domain: d\n"
                "    claim: c\n"
                "    status: wired\n"
                "    verify_command: 'true'\n",
            ),
            encoding="utf-8",
        )
    )
    assert any("反向" in p or "才需附" in p for p in mod.check(str(tmp_path), data2))


def test_check_claimed_with_evidence(tmp_path):
    mod = load_tool()
    data = yaml.safe_load(
        open(
            write_yaml(
                tmp_path,
                "features:\n"
                "  - id: f1\n"
                "    domain: d\n"
                "    claim: c\n"
                "    status: claimed\n"
                "    evidence: 35 passed\n",
            ),
            encoding="utf-8",
        )
    )
    assert any("claimed" in p for p in mod.check(str(tmp_path), data))


def test_check_real_repo_yaml_green():
    mod = load_tool()
    root = os.path.abspath(os.path.join(REPO_ROOT))
    data = mod.load_yaml(os.path.join(root, "docs", "status_matrix.yaml"))
    assert mod.check(root, data) == []


def test_render_md_contains_rows(tmp_path):
    mod = load_tool()
    (tmp_path / "a.py").write_text("x=1", encoding="utf-8")
    data = yaml.safe_load(open(write_yaml(tmp_path, VALID_MIN), encoding="utf-8"))
    lines = mod.render_md(str(tmp_path), data)
    text = "\n".join(lines)
    assert "# STATUS_MATRIX" in text
    assert "| d |" in text and "**verified**" in text
    assert "status_matrix.yaml" in text  # 真相源指回


def test_main_check_mode_rc(tmp_path, monkeypatch):
    mod = load_tool()
    (tmp_path / "a.py").write_text("x=1", encoding="utf-8")
    y = write_yaml(tmp_path, VALID_MIN)
    monkeypatch.setattr(
        "sys.argv",
        ["gen_status_matrix.py", "check", "--yaml", y, "--root", str(tmp_path)],
    )
    assert mod.main() == 0
    # 壞 YAML → rc 1
    bad = write_yaml(
        tmp_path, "features:\n  - id: x\n    status: bogus\n    domain: d\n    claim: c\n"
    )
    monkeypatch.setattr(
        "sys.argv",
        ["gen_status_matrix.py", "check", "--yaml", bad, "--root", str(tmp_path)],
    )
    assert mod.main() == 1
