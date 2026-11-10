"""STATUS_MATRIX verified 宣稱的可重驗性門（事實門 matrix.*）。

WHY：`docs/status_matrix.yaml` 是功能成熟度的唯一總表，但在此之前**沒有任何東西讀它**。
結構檢查只確認欄位存在，於是「配置與路由存在」這種句子配上含 `<endpoint>` 的指令也能算
verified——沒有人能照著重跑；用 `ls` 證明三支檔案在，也能宣稱行為可用。宣稱比證據走得
更遠時，專案自己不該沉默。

這裡守兩件事：
1. verified 功能指向的 implementation/tests 路徑必須還在（檔案被改名或刪掉就紅）。
2. verified 的證據必須帶量測數字、驗證指令必須能照抄執行、不得只做存在性檢查；條數進
   棘輪（scripts/matrix_evidence_budget.txt，只減不增）。

另外守 RELEASE_CRITERIA「明確不支援項」表與其文檔的同步（docs.unsupported_items_documented）。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="gate")
def _gate():
    return _load("check_fact_gates")


# --------------------------------------------------------------------------
# 預算檔
# --------------------------------------------------------------------------
def test_budget_file_is_a_non_negative_integer():
    text = (SCRIPTS / "matrix_evidence_budget.txt").read_text(encoding="utf-8")

    assert text.strip().lstrip("-").isdigit(), f"預算必須是單一整數，實際是 {text!r}"
    assert int(text.strip()) >= 0


def test_the_gate_reads_the_budget_file(gate, tmp_path, monkeypatch):
    budget = tmp_path / "matrix_evidence_budget.txt"
    budget.write_text("3\n", encoding="utf-8")
    monkeypatch.setattr(gate, "MATRIX_EVIDENCE_BUDGET", budget)

    assert gate._matrix_evidence_budget() == 3


def test_a_missing_budget_fails_closed(gate, tmp_path, monkeypatch):
    # 讀不到預算就當零容忍：寧可紅一次逼人把預算寫回來，也不要默默放行。
    monkeypatch.setattr(gate, "MATRIX_EVIDENCE_BUDGET", tmp_path / "nope.txt")

    assert gate._matrix_evidence_budget() == 0


# --------------------------------------------------------------------------
# 三種機械判準
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    "row, expected",
    [
        # 可重驗：指令照抄就能跑、證據帶數字。
        (
            {
                "verify_command": "pytest tests/core/hsp/",
                "evidence": "tests/core/hsp/ 74 passed（2026-10-20 實測）",
            },
            [],
        ),
        # 佔位符：抄不動，等於沒有指令。
        (
            {
                "verify_command": "python scripts/run_benchmarks.py --base-url <endpoint>",
                "evidence": "配置與路由存在",
            },
            ["unrunnable placeholder", "no measured number"],
        ),
        # 只證明檔案存在，不證明行為。
        (
            {
                "verify_command": "ls docs/user_guide/unsupported.md",
                "evidence": "三文檔存在且同步",
            },
            ["existence-only", "no measured number"],
        ),
        # 沒有指令。
        ({"evidence": "1 項"}, ["no verify_command"]),
    ],
)
def test_weak_evidence_reasons(gate, row, expected):
    reasons = gate._weak_evidence_reasons(row)
    joined = " | ".join(reasons)

    for needle in expected:
        assert needle in joined, f"缺少判定 {needle!r}，實得 {reasons}"


def test_a_metavar_alone_is_enough_to_be_weak(gate):
    # 數字在也沒用：含佔位符的指令沒有人能重跑。
    reasons = gate._weak_evidence_reasons(
        {
            "verify_command": "python scripts/x.py --target <name>",
            "evidence": "2026-10-20 實測 12 passed",
        }
    )

    assert reasons and "unrunnable placeholder" in reasons[0]


def test_label_key_normalises_fullwidth_punctuation(gate):
    assert gate._label_key("分散式部署／多節點協同") == gate._label_key("分散式部署/多節點協同")
    assert gate._label_key("COMMAND／設備控制（打開設置）") == "COMMAND/設備控制(打開設置)"


# --------------------------------------------------------------------------
# 對活檔案量測：門必須真的有東西可擋（非空轉）
# --------------------------------------------------------------------------
def test_the_matrix_actually_has_verified_rows(gate):
    # 0 條 verified 會讓「全部可重驗」與「表格壞掉讀不到」無法區分。
    assert len(gate._matrix_features("verified")) > 0


def test_every_verified_claim_is_mechanically_recheckable(gate):
    weak = [
        (row.get("id"), gate._weak_evidence_reasons(row))
        for row in gate._matrix_features("verified")
    ]
    weak = [(fid, why) for fid, why in weak if why]

    assert weak == [], f"verified 宣稱無法重驗：{weak}"


def test_every_verified_claim_points_at_existing_code(gate):
    broken = []
    for row in gate._matrix_features("verified"):
        for key in ("implementation", "tests"):
            value = row.get(key) or []
            value = [value] if isinstance(value, str) else value
            broken.extend(
                f"{row.get('id')}: {rel}" for rel in value if not (REPO_ROOT / str(rel)).exists()
            )

    assert broken == [], f"verified 宣稱指向已不存在的路徑：{broken}"


def test_the_unsupported_table_is_really_checked(gate):
    # 這條若變成 0/0 就是空轉（表被改名或解析不到），所以要求分母 > 0。
    fact = gate._unsupported_documented_facts()[0]

    assert fact.value == 0, fact.evidence
    numerator, denominator = fact.evidence.split(" ")[0].split("/")
    assert int(denominator) >= 9, f"只比對了 {denominator} 列，表格解析可能壞掉"
    assert numerator == denominator, fact.evidence
