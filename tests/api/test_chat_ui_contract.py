# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""P1 首條活鏈合約門：後端對話回應 × 前端讀鍵。

 Kap：`packages/shared-js/js/api-client.js` 用
`data.response || data.message`（送訊息）與
`data.response || data.content || data.message`（端點探測）取值。
若後端把 `response` 改名，前端靜默顯示 'No response'——兩端各自全綠、
中間斷裂。本門斷言鍵交集非空，並經事實解讀器單一裁決點輸出。
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
API_CLIENT = REPO / "packages/shared-js/js/api-client.js"

# 前端實際讀的回應鍵（讀檔解析，非手抄，改了前端此處自動跟著變）
_FRONTEND_KEY_PATTERN = re.compile(r"data\.(response|message|content)\b")


def _frontend_read_keys() -> set:
    return set(_FRONTEND_KEY_PATTERN.findall(API_CLIENT.read_text(encoding="utf-8")))


def _backend_response_keys() -> set:
    from api.routes.chat_routes import _format_chat_response

    resp = _format_chat_response("hi", None, None, "2.0", "", "hi", 4000, "sess-contract-1")
    return set(resp)


def test_frontend_contract_anchor_exists() -> None:
    """前端合約錨點存在：讀鍵集合非空且含 response。"""
    assert API_CLIENT.is_file()
    assert _frontend_read_keys() >= {"response"}


def test_backend_keeps_frontend_keys() -> None:
    """後端回應鍵必須覆蓋前端讀鍵的核心交集（response）。"""
    assert "response" in _backend_response_keys()


def test_chain_overlap_adjudicated() -> None:
    """交集經解讀器裁決：空交集即 BLOCKED，不是一句全綠。"""
    from core.facts import Fact, adjudicate

    overlap = _backend_response_keys() & _frontend_read_keys()
    report = adjudicate(
        [
            Fact(
                "chain_chat_response_overlap",
                float(len(overlap)),
                1.0,
                "ge",
                "keys",
                "api.routes.chat_routes+shared-js/api-client.js",
                f"overlap={sorted(overlap)}",
            )
        ]
    )
    assert report.ok is True, report.summary()
    assert "response" in overlap
