# =============================================================================
# ANGELA-MATRIX: [L5] [β] [B] [L3]
# =============================================================================
"""自主研究 API — 專案AI自產《後續研究與升級路徑完整報告》。

POST /research/upgrade-report        — 執行完整研究管線（web/polish 可選），回 {ok,path,problems,stats}
GET  /research/upgrade-report/latest — 回傳最新已生成報告（路徑/時間/開頭內容）
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/research", tags=["Research"])

_run_lock = asyncio.Lock()


def _find_latest(root: str) -> Optional[str]:
    import glob as _glob

    files = sorted(_glob.glob(os.path.join(root, "docs", "RESEARCH_UPGRADE_REPORT_*.md")))
    return files[-1] if files else None


@router.post("/upgrade-report")
async def run_upgrade_report(payload: Dict[str, Any] = Body(default={})) -> Dict[str, Any]:
    """執行自主研究全流程（單飛：同一時間只跑一份，防重複產物）。"""
    if _run_lock.locked():
        return {"ok": False, "error": "upgrade report already running"}
    async with _run_lock:
        try:
            from ai.research import run_upgrade_research

            res = await run_upgrade_research(
                web=bool(payload.get("web", True)),
                polish=bool(payload.get("polish", True)),
                out_path=payload.get("out"),
            )
            return {
                "ok": res["ok"],
                "path": res["path"],
                "problems": res["problems"],
                "stats": res["stats"],
            }
        except Exception as exc:  # noqa: BLE001 — 端點必須回結構化錯誤
            logger.warning("upgrade report generation failed: %s", exc, exc_info=True)
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


@router.get("/upgrade-report/latest")
async def latest_upgrade_report() -> Dict[str, Any]:
    """最新報告摘要（未生成時 exists=False）。"""
    try:
        from ai.research.upgrade_research import _repo_root

        path = _find_latest(str(_repo_root()))
        if not path:
            return {"ok": True, "exists": False}
        st = os.stat(path)
        with open(path, encoding="utf-8") as fh:
            head = fh.read(2000)
        return {
            "ok": True,
            "exists": True,
            "path": path,
            "generated_at": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
            "chars": st.st_size,
            "head": head,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("latest upgrade report unavailable: %s", exc, exc_info=True)
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
