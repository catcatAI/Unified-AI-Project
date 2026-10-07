# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""P1 第三條活鏈合約門：維運狀態（後端 shape × 前端讀鍵）。

`packages/shared-js/js/api-client.js:getStatus()` 取
`data.status/metrics/service/timestamp`（全帶 `||`  fallback，
缺鍵即靜默降級為 idle/空 metrics）；後端
`api/routes/ops_routes.py:get_ops_status` 恰供這四鍵。
任一改名，面板靜默顯示 offline/idle。本門鎖死交集。
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
API_CLIENT = REPO / "packages/shared-js/js/api-client.js"

_LEAF_ANCHORS = (
    "data.status",
    "data.metrics",
    "data.service",
    "data.timestamp",
)

_BACKEND_KEYS = ("status", "metrics", "service", "timestamp")


async def _backend_payload() -> dict:
    from api.routes.ops_routes import get_ops_status

    return await get_ops_status()


def test_frontend_leaf_anchors_exist() -> None:
    """前端 4 葉路徑錨點存在（getStatus 改讀別處即變紅）。"""
    assert API_CLIENT.is_file()
    text = API_CLIENT.read_text(encoding="utf-8")
    for anchor in _LEAF_ANCHORS:
        assert anchor in text, anchor


@pytest.mark.asyncio
async def test_backend_serves_all_frontend_leaves() -> None:
    """後端 4 鍵全有值（缺一即面板靜默降級）。"""
    payload = await _backend_payload()
    for key in _BACKEND_KEYS:
        assert payload.get(key) is not None, key
    assert isinstance(payload["metrics"], dict)


@pytest.mark.asyncio
async def test_chain_overlap_adjudicated() -> None:
    """4/4 相交經解讀器裁決：少一條即 BLOCKED。"""
    from core.facts import Fact, adjudicate

    payload = await _backend_payload()
    text = API_CLIENT.read_text(encoding="utf-8")
    covered = sum(
        1 for key in _BACKEND_KEYS if f"data.{key}" in text and payload.get(key) is not None
    )
    report = adjudicate(
        [
            Fact(
                "chain_ops_leaves_covered",
                float(covered),
                float(len(_BACKEND_KEYS)),
                "ge",
                "leaves",
                "api/routes/ops_routes.py+shared-js/api-client.js",
                f"covered={covered}/{len(_BACKEND_KEYS)}",
            )
        ]
    )
    assert report.ok is True, report.summary()
