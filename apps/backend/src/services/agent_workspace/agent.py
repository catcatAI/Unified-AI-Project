"""代理工作區統一入口（AgentWorkspace）：把分散的代理能力整理成一個閉環操作面。

組成：
- ContextTree：樹狀上下文治理（全貌唯讀／執行器分層＋指令白名單）
- AppSessionManager：應用會話生命週期（open→read→act→save→close）＋確認門＋學習日誌
- 內建桌面代理（DesktopAgent）與瀏覽器代理（BrowserAgent）兩個 adapter，
  把 DesktopInteraction / BrowserController 包裝成可樹狀呈現的指令白名單。

AI 的使用流程：
    1. overview()        —— 不清楚狀況時看全貌（唯讀）
    2. focus(node_id)    —— 切到執行器視圖（只顯示當層＋白名單指令）
    3. act(session, cmd) —— 執行指令（危險指令過確認門）
    4. save / close      —— 保存並關閉，整個過程寫入學習日誌
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from services.agent_workspace.app_session import (
    AppAdapter,
    AppSessionManager,
    ActionSpec,
    DEFAULT_LOG_PATH,
)
from services.agent_workspace.context_tree import ContextNode, ContextTree

logger = logging.getLogger(__name__)


class DesktopAgent(AppAdapter):
    """把 DesktopInteraction 包裝成應用 adapter（桌面整理代理）。"""

    app_id = "desktop"
    label = "桌面整理代理"

    def __init__(self, interaction: Any = None) -> None:
        super().__init__()
        self._interaction = interaction
        self.register(ActionSpec("state", "讀取桌面狀態（檔案數／雜亂度）"), self._state)
        self.register(
            ActionSpec("organize", "依類別整理桌面檔案", dangerous=True), self._organize
        )
        self.register(
            ActionSpec("cleanup", "清理 N 天前的舊檔案", dangerous=True), self._cleanup
        )

    async def _state(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._interaction is None:
            return {"ok": False, "error": "DesktopInteraction 未注入"}
        state = self._interaction.get_desktop_state()
        return {
            "ok": True,
            "total_files": getattr(state, "total_files", 0),
            "total_size": getattr(state, "total_size", 0),
            "clutter_level": getattr(state, "clutter_level", 0.0),
        }

    async def _organize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._interaction is None:
            return {"ok": False, "error": "DesktopInteraction 未注入"}
        ops = await self._interaction.organize_desktop()
        return {"ok": True, "moved": len(ops)}

    async def _cleanup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._interaction is None:
            return {"ok": False, "error": "DesktopInteraction 未注入"}
        days_old = int(params.get("days_old", 30))
        ops = await self._interaction.cleanup_desktop(days_old=days_old)
        return {"ok": True, "cleaned": len(ops)}


class BrowserAgent(AppAdapter):
    """把 BrowserController 包裝成應用 adapter（瀏覽代理）。"""

    app_id = "browser"
    label = "瀏覽代理"

    def __init__(self, controller: Any = None) -> None:
        super().__init__()
        self._controller = controller
        self.register(ActionSpec("search", "搜尋關鍵字並回傳結果摘要"), self._search)
        self.register(ActionSpec("extract", "擷取指定網頁內容"), self._extract)
        self.register(
            ActionSpec("add_bookmark", "新增書籤", dangerous=True), self._add_bookmark
        )

    async def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._controller is None:
            return {"ok": False, "error": "BrowserController 未注入"}
        query = str(params.get("query", "")).strip()
        if not query:
            return {"ok": False, "error": "缺少 query"}
        result = await self._controller.search(query)
        return {"ok": True, "query": query, "result": result}

    async def _extract(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._controller is None:
            return {"ok": False, "error": "BrowserController 未注入"}
        url = str(params.get("url", "")).strip()
        if not url:
            return {"ok": False, "error": "缺少 url"}
        content = await self._controller.extract_content(url)
        if content is None:
            return {"ok": False, "error": f"擷取失敗：{url}"}
        return {"ok": True, "url": url, "title": getattr(content, "title", "")}

    async def _add_bookmark(self, params: Dict[str, Any]) -> Dict[str, Any]:
        if self._controller is None:
            return {"ok": False, "error": "BrowserController 未注入"}
        url = str(params.get("url", "")).strip()
        title = str(params.get("title", url))
        if not url:
            return {"ok": False, "error": "缺少 url"}
        bookmark = self._controller.add_bookmark(url=url, title=title)
        return {"ok": True, "bookmark_id": getattr(bookmark, "id", None)}


class AgentWorkspace:
    """代理工作區：上下文樹＋會話管理的統一門面（AI 的單一操作入口）。"""

    def __init__(
        self,
        session_manager: Optional[AppSessionManager] = None,
        view_budget: int = 4000,
        children_limit: int = 12,
    ) -> None:
        self.sessions = session_manager or AppSessionManager()
        self.tree = ContextTree(
            root=ContextNode(id="root", label="代理工作區", kind="workspace"),
            view_budget=view_budget,
            children_limit=children_limit,
        )
        self._rebuild_tree()

    # ---------- 樹狀上下文 ----------

    def _rebuild_tree(self) -> None:
        """依當前可用應用與開啟中會話重建上下文樹。"""
        root = ContextNode(id="root", label="代理工作區", kind="workspace")
        apps_node = ContextNode(
            id="apps",
            label="應用程式",
            kind="app_group",
            summary=f"{len(self.sessions.available_apps())} 個可用應用",
        )
        for app in self.sessions.available_apps():
            record = self.sessions.get_session(app["app_id"])
            state_summary = "未開啟"
            if record is not None:
                state_summary = f"開啟中（{record.state}，op={record.op_count}）"
            apps_node.children.append(
                    ContextNode(
                        id=f"app:{app['app_id']}",
                        label=app["label"],
                        kind="app",
                        summary=state_summary,
                        commands=["open"],
                        readonly=False,
                    )
                )
            if record is not None:
                adapter = self.sessions._adapters.get(app["app_id"])
                if adapter is not None:
                    apps_node.children[-1].children.append(
                        ContextNode(
                            id=f"session:{app['app_id']}",
                            label=f"會話 {record.session_id}",
                            kind="session",
                            summary=record.state,
                            commands=[s.name for s in adapter.specs()] + ["save", "close"],
                            readonly=False,
                        )
                    )
        root.children.append(apps_node)
        root.children.append(
            ContextNode(
                id="learning_log",
                label="學習日誌",
                kind="log",
                summary="教學／探索／成敗皆為學習資料",
            )
        )
        self.tree = ContextTree(
            root=root,
            view_budget=self.tree._budget if hasattr(self, "tree") else 4000,
            children_limit=self.tree._children_limit if hasattr(self, "tree") else 12,
        )

    def overview(self, max_depth: int = 3) -> Dict[str, Any]:
        """全貌視圖（唯讀）。"""
        self._rebuild_tree()
        return self.tree.overview(max_depth=max_depth)

    def focus(self, node_id: str) -> Dict[str, Any]:
        """執行器視圖（路徑列＋當層＋白名單指令）。"""
        self._rebuild_tree()
        return self.tree.focus(node_id)

    # ---------- 會話閉環（同時刷新樹） ----------

    async def open_app(self, app_id: str, purpose: str = "", source: str = "teaching") -> Dict[str, Any]:
        result = await self.sessions.open_app(app_id, purpose=purpose, source=source)
        self._rebuild_tree()
        return result

    async def read_app(self, app_id: str) -> Dict[str, Any]:
        return await self.sessions.read_app(app_id)

    async def act(
        self,
        app_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        confirm: bool = False,
        source: str = "exploration",
    ) -> Dict[str, Any]:
        result = await self.sessions.act(
            app_id, action, params=params, confirm=confirm, source=source
        )
        self._rebuild_tree()
        return result

    async def save_app(self, app_id: str) -> Dict[str, Any]:
        result = await self.sessions.save_app(app_id)
        self._rebuild_tree()
        return result

    async def close_app(self, app_id: str, confirm: bool = False) -> Dict[str, Any]:
        result = await self.sessions.close_app(app_id, confirm=confirm)
        self._rebuild_tree()
        return result

    def learning_tail(self, limit: int = 20) -> list:
        return self.sessions.learning_tail(limit=limit)


def build_default_workspace(
    log_path: Any = DEFAULT_LOG_PATH,
    desktop_interaction: Any = None,
    browser_controller: Any = None,
) -> AgentWorkspace:
    """以 DI getters 的單例組出預設工作區（能力缺失時降級為空 adapter 也可註冊）。"""
    manager = AppSessionManager(
        adapters={
            "desktop": DesktopAgent(desktop_interaction),
            "browser": BrowserAgent(browser_controller),
        },
        log_path=log_path,
    )
    return AgentWorkspace(session_manager=manager)
