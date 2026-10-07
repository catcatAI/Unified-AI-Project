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
SPEC_PATH = REPO / "hardware/edge_card/edge_card_spec.yaml"
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
