# =============================================================================
# ANGELA-MATRIX: [L4] [β] [B] [L8]
# =============================================================================
"""Web-search research audit trail (jsonl tail).

研究結果原先只活在 RAM TTL session＋使用者眼前的回應 JSON——無稽核軌跡
（audit 2026-10-18）。WebSearchTool 現把每次搜尋 append 到
``apps/backend/data/research_history/web_search.jsonl``；此路由暴露尾端。
"""

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web-search", tags=["web_search"])


@router.get("/history")
async def web_search_history(limit: int = 20) -> Dict[str, Any]:
    """Recent web-search audit records (query/provider/urls/timestamp, oldest first)."""
    try:
        from core.tools.web_search_tool import read_recent_history

        bounded = max(1, min(int(limit), 200))
        # jsonl tail 讀檔是同步 I/O——async handler 直跑會佔住事件迴圈。
        items = await asyncio.to_thread(read_recent_history, bounded)
        return {"ok": True, "count": len(items), "history": items}
    except Exception as e:
        logger.warning("web-search history read failed: %s", e, exc_info=True)
        return {"ok": False, "count": 0, "history": [], "error": str(e)}
