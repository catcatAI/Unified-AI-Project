"""代理工作區 API：樹狀上下文（全貌唯讀／執行器分層）＋應用會話閉環。

- GET  /agent/context/overview          全貌視圖（唯讀）
- GET  /agent/context/focus/{node_id}  執行器視圖（當層＋指令白名單）
- POST /agent/session/open|read|act|save|close  會話生命週期
- GET  /agent/learning                  學習日誌尾端（教學／探索／成敗皆為學習資料）
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from api.lifespan import get_agent_workspace
from fastapi import APIRouter, Body, Depends, HTTPException

if TYPE_CHECKING:
    from services.agent_workspace.global_tree import UnifiedWorkspace

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/agent/context/overview")
async def agent_context_overview(
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """AI 不清楚狀況時的全貌（唯讀樹狀）。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    return workspace.overview()


@router.get("/agent/context/focus/{node_id}")
async def agent_context_focus(
    node_id: str,
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """切換到執行器視圖：只顯示當前樹狀分層＋該層指令白名單。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    result = workspace.focus(node_id)
    if result.get("error"):
        raise HTTPException(404, str(result["error"]))
    return result


@router.get("/agent/context/search")
async def agent_context_search(
    query: str,
    limit: int = 10,
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """跨五類上下文的全域搜尋（工具／模型／代理／對話／記憶）。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    return workspace.search(query, limit=limit)


@router.post("/agent/session/open")
async def agent_session_open(
    body: Dict[str, Any] = Body(default={}),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """開啟應用會話。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    app_id = str(body.get("app_id", "")).strip()
    if not app_id:
        raise HTTPException(422, "缺少 app_id")
    purpose = str(body.get("purpose", ""))
    source = str(body.get("source", "teaching"))
    return await workspace.open_app(app_id, purpose=purpose, source=source)


@router.post("/agent/session/read")
async def agent_session_read(
    body: Dict[str, Any] = Body(default={}),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """讀取應用當前狀態（AI 識別）。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    app_id = str(body.get("app_id", "")).strip()
    if not app_id:
        raise HTTPException(422, "缺少 app_id")
    return await workspace.read_app(app_id)


@router.post("/agent/session/act")
async def agent_session_act(
    body: Dict[str, Any] = Body(default={}),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """執行會話指令（危險指令回 pending_confirmation，需 confirm=True 重送）。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    app_id = str(body.get("app_id", "")).strip()
    action = str(body.get("action", "")).strip()
    if not app_id or not action:
        raise HTTPException(422, "缺少 app_id 或 action")
    params: Optional[Dict[str, Any]] = (
        body.get("params") if isinstance(body.get("params"), dict) else None
    )
    confirm = bool(body.get("confirm", False))
    source = str(body.get("source", "exploration"))
    return await workspace.act(app_id, action, params=params, confirm=confirm, source=source)


@router.post("/agent/session/save")
async def agent_session_save(
    body: Dict[str, Any] = Body(default={}),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """保存會話。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    app_id = str(body.get("app_id", "")).strip()
    if not app_id:
        raise HTTPException(422, "缺少 app_id")
    return await workspace.save_app(app_id)


@router.post("/agent/session/close")
async def agent_session_close(
    body: Dict[str, Any] = Body(default={}),
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """關閉會話（有未保存變更時需 confirm=True）。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    app_id = str(body.get("app_id", "")).strip()
    if not app_id:
        raise HTTPException(422, "缺少 app_id")
    confirm = bool(body.get("confirm", False))
    return await workspace.close_app(app_id, confirm=confirm)


@router.get("/agent/learning")
async def agent_learning_tail(
    limit: int = 20,
    workspace: "UnifiedWorkspace" = Depends(get_agent_workspace),
) -> dict:
    """學習日誌尾端：教學、自主探索、成功與失敗都是學習資料。"""
    if workspace is None:
        raise HTTPException(503, "AgentWorkspace not available")
    return {"ok": True, "entries": workspace.learning_tail(limit=max(1, min(limit, 200)))}
