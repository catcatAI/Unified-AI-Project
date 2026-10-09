# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""P1 第四條活鏈合約門：multimodal quality dashboard（後端 shape × 前端讀鍵）。

`packages/shared-js/js/multimodal-panel.js:400-465` 讀 `data.success`、
`data.vision.avg_ssim/avg_psnr/total_calls/avg_time_ms`、
`data.audio.avg_snr/total_calls/avg_time_ms`、`data.overall_health`、
`data.total_requests`；後端 `multimodal_routes/quality/dashboard` 回
`{"success": True, **dashboard_simple()}`。任一改名即面板空白格。
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PANEL_JS = REPO / "packages/shared-js/js/multimodal-panel.js"

_LEAF_ANCHORS = (
    "data.success",
    "data.vision",
    "avg_ssim",
    "avg_psnr",
    "data.audio",
    "avg_snr",
    "data.overall_health",
    "data.total_requests",
    "total_calls",
    "avg_time_ms",
)


def _backend_payload() -> dict:
    from services.cross_modal_quality import CrossModalQualityDashboard

    return {"success": True, **CrossModalQualityDashboard().dashboard_simple()}


def test_frontend_leaf_anchors_exist() -> None:
    """前端讀鍵錨點存在（面板改讀別處即變紅）。"""
    assert PANEL_JS.is_file()
    text = PANEL_JS.read_text(encoding="utf-8")
    for anchor in _LEAF_ANCHORS:
        assert anchor in text, anchor


def test_backend_serves_all_frontend_leaves() -> None:
    """後端 payload 含面板全部鍵（缺一即空白格）。"""
    payload = _backend_payload()
    assert payload["success"] is True
    for section in ("vision", "audio"):
        for key in ("total_calls", "avg_time_ms"):
            assert payload[section][key] is not None
    assert payload["vision"]["avg_ssim"] is not None
    assert payload["vision"]["avg_psnr"] is not None
    assert payload["audio"]["avg_snr"] is not None
    assert payload["overall_health"] is not None
    assert payload["total_requests"] is not None


def test_chain_overlap_adjudicated() -> None:
    """10/10 相交經解讀器裁決：少一條即 BLOCKED。"""
    from core.facts import Fact, adjudicate

    payload = _backend_payload()
    text = PANEL_JS.read_text(encoding="utf-8")
    hits = [a for a in _LEAF_ANCHORS if a in text]
    backend_ok = (
        payload.get("success") is True
        and payload.get("overall_health") is not None
        and payload.get("total_requests") is not None
    )
    covered = len(hits) + (1 if backend_ok else 0)
    report = adjudicate(
        [
            Fact(
                "chain_multimodal_leaves_covered",
                float(covered),
                float(len(_LEAF_ANCHORS) + 1),
                "ge",
                "leaves",
                "api/routes/multimodal_routes.py+shared-js/multimodal-panel.js",
                f"covered={covered}/{len(_LEAF_ANCHORS) + 1}",
            )
        ]
    )
    assert report.ok is True, report.summary()
