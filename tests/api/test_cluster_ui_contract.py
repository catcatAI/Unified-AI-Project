# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""P1 第二條活鏈合約門：叢集監控面板（後端 shape × 前端讀路徑）。

`packages/shared-js/js/settings.js:updateMonitorUI` 輪詢
`/api/v1/system/cluster/status` 並讀 6 個葉路徑
（`hardware.cpu.usage/brand`、`hardware.memory.usage_percent/total`、
`hardware.performance_tier`、`hardware.ai_capability_score`）。
後端（`api/router.py:get_cluster_status`）任一改名/刪鍵，前端該格即靜默
空白（`if (el)` 守衛吞掉一切）。本門把 6 條葉路徑全列入判定。
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SETTINGS_JS = REPO / "packages/shared-js/js/settings.js"

# 前端實際讀的葉路徑（settings.js:392-408，讀檔錨定，非手抄）
_LEAF_ANCHORS = (
    "data.hardware.cpu.usage",
    "data.hardware.cpu.brand",
    "data.hardware.memory.usage_percent",
    "data.hardware.memory.total",
    "data.hardware.performance_tier",
    "data.hardware.ai_capability_score",
)


def _nested_get(data: dict, dotted: str):
    node = data
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _backend_payload() -> dict:
    from api.router import get_cluster_status

    return get_cluster_status()


def test_frontend_leaf_anchors_exist() -> None:
    """前端 6 葉路徑錨點存在（前端改讀別處即變紅）。"""
    assert SETTINGS_JS.is_file()
    text = SETTINGS_JS.read_text(encoding="utf-8")
    for anchor in _LEAF_ANCHORS:
        assert anchor in text, anchor


def test_backend_serves_all_frontend_leaves() -> None:
    """後端 6 葉路徑全有值（缺一即面板空白格）。"""
    payload = _backend_payload()
    for anchor in _LEAF_ANCHORS:
        leaf = anchor.removeprefix("data.")
        assert _nested_get(payload, leaf) is not None, anchor


def test_chain_overlap_adjudicated() -> None:
    """6/6 相交經解讀器裁決：少一條即 BLOCKED。"""
    from core.facts import Fact, adjudicate

    payload = _backend_payload()
    text = SETTINGS_JS.read_text(encoding="utf-8")
    covered = sum(
        1
        for anchor in _LEAF_ANCHORS
        if anchor in text and _nested_get(payload, anchor.removeprefix("data.")) is not None
    )
    report = adjudicate(
        [
            Fact(
                "chain_cluster_leaves_covered",
                float(covered),
                float(len(_LEAF_ANCHORS)),
                "ge",
                "leaves",
                "api/router.py+shared-js/settings.js",
                f"covered={covered}/{len(_LEAF_ANCHORS)}",
            )
        ]
    )
    assert report.ok is True, report.summary()
