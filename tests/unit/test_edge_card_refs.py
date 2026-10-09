# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""P2 地圖引用門（最小版）：edge 卡 spec 的來源引用閉合性。

`test_edge_card_spec.py` 驗證數值；本檔驗證引用結構：
- 所有 `src_*` 引用都有定義（無懸空），所有定義都有引用（無死出處）。
- `internal_spec` 類來源的路徑在磁碟上真實存在。
改引用不斷定義（或反之）即紅燈。交集經解讀器裁決。
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "hardware/assemblies/done/edge_card/edge_card_spec.yaml"
_SRC_TOKEN = re.compile(r"src_[a-z0-9_]+")


def _load() -> tuple[dict, str]:
    text = SPEC_PATH.read_text(encoding="utf-8")
    return yaml.safe_load(text), text


def test_source_ids_are_closed() -> None:
    """引用 = 定義：無懸空、無死出處。"""
    spec, text = _load()
    defined = set(spec["sources"])
    used = set(_SRC_TOKEN.findall(text))
    dangling = sorted(used - defined)
    dead = sorted(defined - used)
    assert not dangling, f"懸空來源: {dangling}"
    assert not dead, f"死出處: {dead}"


def test_internal_spec_paths_exist() -> None:
    """internal_spec 類 URL 必須是倉內真實路徑。"""
    spec, _ = _load()
    missing = [
        (sid, src["url"])
        for sid, src in spec["sources"].items()
        if src.get("type") == "internal_spec" and not (REPO / src["url"]).exists()
    ]
    assert not missing, f"路徑不存在: {missing}"


def test_ref_closure_adjudicated() -> None:
    """閉合性經解讀器裁決：三事實全過才綠。"""
    from core.facts import Fact, adjudicate

    spec, text = _load()
    defined = set(spec["sources"])
    used = set(_SRC_TOKEN.findall(text))
    internal_missing = sum(
        1
        for src in spec["sources"].values()
        if src.get("type") == "internal_spec" and not (REPO / src["url"]).exists()
    )
    report = adjudicate(
        [
            Fact(
                "refs.no_dangling",
                float(len(used - defined)),
                0.0,
                "le",
                "count",
                "edge_card_spec.sources",
                "",
            ),
            Fact(
                "refs.no_dead",
                float(len(defined - used)),
                0.0,
                "le",
                "count",
                "edge_card_spec.sources",
                "",
            ),
            Fact(
                "refs.internal_paths_exist",
                float(internal_missing),
                0.0,
                "le",
                "count",
                "edge_card_spec.sources",
                "",
            ),
        ]
    )
    assert report.ok is True, report.summary()


# -----------------------------------------------------------------------------
# 硬體文檔引用普查：零引用文檔必須點名在冊，新增即紅燈
# -----------------------------------------------------------------------------
_KNOWN_UNREFERENCED = frozenset(
    {
        # 長期自研矽計畫文檔：程式未讀，決策依據，刪改需人類覆核
        "ai_compute_card_task",
        "component_registry",
        "concept_design",
        "secondary_compute_draft",
        "mvu_reference_spec",
        "DERIVED_ESTIMATES",
    }
)
_SCAN_ROOTS = ("apps/backend/src", "tests", "scripts", "packages/shared-js/js")
_SCAN_SUFFIXES = (".py", ".js", ".yaml")


def _referenced_stems() -> set:
    """倉內程式實際出現過的硬體文檔 stem 集合（子字串匹配）。"""
    haystacks = []
    for root in _SCAN_ROOTS:
        base = REPO / root
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.suffix not in _SCAN_SUFFIXES or not path.is_file():
                continue
            try:
                haystacks.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    corpus = "\n".join(haystacks)
    stems = set()
    for doc in (REPO / "hardware").rglob("*"):
        if doc.suffix not in (".yaml", ".md") or not doc.is_file() or doc.name == "README.md":
            continue
        stem = doc.stem
        if stem in corpus:
            stems.add(stem)
    return stems


def test_hardware_docs_referenced_or_listed() -> None:
    """每份硬體文檔要麼被程式引用，要麼點名在冊；新增零引用文檔即紅燈。"""
    docs = set()
    for doc in (REPO / "hardware").rglob("*"):
        if doc.suffix not in (".yaml", ".md") or not doc.is_file() or doc.name == "README.md":
            continue
        docs.add(doc.stem)
    unreferenced = docs - _referenced_stems()
    # 子集關係蘊含雙向：新增零引用即紅；已知項被引用化後自動除名，無需改表。
    assert unreferenced <= _KNOWN_UNREFERENCED, f"新增零引用文檔需點名: {sorted(unreferenced)}"


def test_hardware_census_adjudicated() -> None:
    """普查經解讀器裁決：未知零引用數為 0 才綠。"""
    from core.facts import Fact, adjudicate

    docs = set()
    for doc in (REPO / "hardware").rglob("*"):
        if doc.suffix not in (".yaml", ".md") or not doc.is_file() or doc.name == "README.md":
            continue
        docs.add(doc.stem)
    unknown = (docs - _referenced_stems()) - _KNOWN_UNREFERENCED
    report = adjudicate(
        [
            Fact(
                "refs.no_unknown_unreferenced_docs",
                float(len(unknown)),
                0.0,
                "le",
                "count",
                "hardware/ census",
                f"unknown={sorted(unknown)}",
            )
        ]
    )
    assert report.ok is True, report.summary()
