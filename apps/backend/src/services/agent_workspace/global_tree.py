"""全域上下文樹（Global Context Tree）：整個 AI 系統的樹狀上下文治理層。

上下文系統是整個專案的核心（ai/context/），不是代理專屬工具——本模組把
**全部五類上下文**（工具／模型／代理／對話／記憶）與代理工作區的應用會話，
統一掛到同一棵樹上，套用同一套雙視圖規則：

- **全貌視圖（overview）**：AI 不清楚狀況時呈現系統全貌——唯讀，只能看與定位。
- **執行器視圖（focus）**：切到某節點後只顯示該層＋該層指令白名單，執行才需要。

連通性：對話上下文優先取 chat 正在用的同一個 DialogueContextManager
（backbone registry 單例，鍵 ``chat.dialogue_ctx``），確保樹上看到的與
對話系統實際使用的是同一份資料，而非平行副本。

上下文預算沿用 ContextTree：字元上限＋子節點摺疊，強迫下鑽、保護注意力。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from services.agent_workspace.agent import AgentWorkspace
from services.agent_workspace.context_tree import ContextNode, ContextTree

logger = logging.getLogger(__name__)

# 對話上下文在 backbone registry 的共用鍵（與 chat_routes 相同單例）
_DIALOGUE_BACKBONE_KEY = "chat.dialogue_ctx"


@dataclass
class GlobalContextProviders:
    """全域上下文的資料來源。所有欄位可為 None（缺席分支會優雅降級）。"""

    context_manager: Any = None  # ai.context.ContextManager
    dialogue_manager: Any = None  # DialogueContextManager
    memory_manager: Any = None  # MemoryContextManager
    tool_manager: Any = None  # ToolContextManager
    model_manager: Any = None  # ModelContextManager
    agent_manager: Any = None  # AgentContextManager
    workspace: Optional[AgentWorkspace] = None  # 代理工作區（應用會話樹）


class GlobalContextTree:
    """整個系統的統一上下文樹：五類上下文＋應用會話，雙視圖治理。"""

    def __init__(self, providers: Optional[GlobalContextProviders] = None) -> None:
        self._external_providers = providers
        self._tree: Optional[ContextTree] = None

    # ---------- 資料來源解析 ----------

    def _providers(self) -> GlobalContextProviders:
        """解析資料來源：外部注入優先，其次 backbone registry，最後單例降級。"""
        if self._external_providers is not None:
            return self._external_providers
        providers = GlobalContextProviders()
        try:
            from core.backbone import get_backbone

            cached = get_backbone().get_module("context.global_tree_providers")
            if isinstance(cached, GlobalContextProviders):
                return cached
        except Exception as exc:  # backbone 缺席時優雅降級
            logger.debug("backbone providers lookup skipped: %s", exc)
        try:
            from ai.context.manager_fixed import get_context_manager

            providers.context_manager = get_context_manager()
        except Exception as exc:
            logger.warning("ContextManager unavailable: %s", exc)
        return providers

    def _dialogue_manager(self, providers: GlobalContextProviders) -> Any:
        """對話上下文：優先 chat 正在用的同一份（backbone 單例），確保連通。"""
        if providers.dialogue_manager is not None:
            return providers.dialogue_manager
        try:
            from core.backbone import get_backbone

            shared = get_backbone().get_module(_DIALOGUE_BACKBONE_KEY)
            if shared is not None:
                return shared
        except Exception as exc:
            logger.debug("shared dialogue manager lookup skipped: %s", exc)
        return None

    def _ctxm(self, providers: GlobalContextProviders) -> Any:
        return providers.context_manager

    # ---------- 樹建構 ----------

    def _build_root(self) -> ContextNode:
        providers = self._providers()
        root = ContextNode(id="root", label="AI 系統上下文", kind="system")
        for section in (
            self._tools_node(providers),
            self._models_node(providers),
            self._agents_node(providers),
            self._dialogue_node(providers),
            self._memory_node(providers),
            self._sessions_root(providers),
            self._search_node(),
        ):
            if section is not None:
                root.children.append(section)
        return root

    def _tools_node(self, providers: GlobalContextProviders) -> Optional[ContextNode]:
        tm = providers.tool_manager
        cats: Dict[str, Any] = getattr(tm, "categories", {}) or {}
        if tm is None or not cats:
            return None
        node = ContextNode(
            id="ctx:tools",
            label="工具上下文",
            kind="context_section",
            summary=f"{len(cats)} 個工具分類",
        )
        node.children.extend(
            ContextNode(
                id=f"ctx:tool_cat:{cid}",
                label=str(getattr(cat, "name", cid)),
                kind="tool_category",
                summary=f"{len(getattr(cat, 'tools', []) or [])} 個工具",
            )
            for cid, cat in list(cats.items())[:20]
        )
        return node

    def _models_node(self, providers: GlobalContextProviders) -> Optional[ContextNode]:
        mm = providers.model_manager
        metrics: Dict[str, Any] = getattr(mm, "model_metrics", {}) or {}
        if mm is None or not metrics:
            return None
        node = ContextNode(
            id="ctx:models",
            label="模型上下文",
            kind="context_section",
            summary=f"{len(metrics)} 個模型",
        )
        node.children.extend(
            ContextNode(
                id=f"ctx:model:{mid}",
                label=str(mid),
                kind="model",
                summary=f"呼叫 {getattr(m, 'total_calls', 0)} 次",
            )
            for mid, m in list(metrics.items())[:20]
        )
        return node

    def _agents_node(self, providers: GlobalContextProviders) -> Optional[ContextNode]:
        am = providers.agent_manager
        collabs: Dict[str, Any] = getattr(am, "collaborations", {}) or {}
        if am is None or not collabs:
            return None
        node = ContextNode(
            id="ctx:agents",
            label="代理協作上下文",
            kind="context_section",
            summary=f"{len(collabs)} 個協作",
        )
        node.children.extend(
            ContextNode(
                id=f"ctx:collab:{cid}",
                label=f"協作 {cid}",
                kind="collaboration",
                summary=str(getattr(c, "status", "")),
            )
            for cid, c in list(collabs.items())[:20]
        )
        return node

    def _dialogue_node(self, providers: GlobalContextProviders) -> Optional[ContextNode]:
        dm = self._dialogue_manager(providers)
        convs: Dict[str, Any] = getattr(dm, "conversations", {}) or {}
        if dm is None or not convs:
            return None
        node = ContextNode(
            id="ctx:dialogue",
            label="對話上下文",
            kind="context_section",
            summary=f"{len(convs)} 個對話",
        )
        for cid, conv in list(convs.items())[:20]:
            summary_obj = getattr(conv, "context_summary", None)
            n_points = len(getattr(summary_obj, "key_points", []) or [])
            node.children.append(
                ContextNode(
                    id=f"ctx:conv:{cid}",
                    label=f"對話 {cid}",
                    kind="conversation",
                    summary=(
                        f"{len(getattr(conv, 'messages', []) or [])} 則訊息"
                        + (f"｜{n_points} 個重點" if n_points else "")
                    ),
                )
            )
        return node

    def _memory_node(self, providers: GlobalContextProviders) -> Optional[ContextNode]:
        mem_mgr = providers.memory_manager
        memories: Dict[str, Any] = getattr(mem_mgr, "memories", {}) or {}
        if mem_mgr is None and self._ctxm(providers) is None:
            return None
        node = ContextNode(
            id="ctx:memory",
            label="記憶上下文",
            kind="context_section",
            summary=f"{len(memories)} 則記憶",
        )
        by_type: Dict[str, int] = {}
        for mem in list(memories.values()):
            by_type[str(getattr(mem, "memory_type", "?"))] = (
                by_type.get(str(getattr(mem, "memory_type", "?")), 0) + 1
            )
        for mem_type, count in sorted(by_type.items()):
            node.children.append(
                ContextNode(
                    id=f"ctx:memory:{mem_type}",
                    label=f"{mem_type}",
                    kind="memory_group",
                    summary=f"{count} 則",
                )
            )
        ctxm = self._ctxm(providers)
        if ctxm is not None:
            node.children.append(
                ContextNode(
                    id="ctx:memory:store",
                    label="ContextManager 儲存層",
                    kind="context_store",
                    summary="create/get/update/search 可用",
                )
            )
        return node or None

    def _sessions_root(self, providers: GlobalContextProviders) -> Optional[ContextNode]:
        """代理工作區的應用會話子樹（與會話 API 同一份狀態）。"""
        ws = providers.workspace
        if ws is None:
            return None
        try:
            return ws.build_sessions_root()
        except Exception as exc:
            logger.warning("workspace sessions root unavailable: %s", exc)
            return None

    def _search_node(self) -> ContextNode:
        return ContextNode(
            id="ctx:search",
            label="全域搜尋",
            kind="search",
            summary="以關鍵字搜尋五類上下文",
        )

    # ---------- 公開視圖 ----------

    def overview(self, max_depth: int = 3) -> Dict[str, Any]:
        """系統全貌（唯讀）。"""
        self._tree = ContextTree(root=self._build_root())
        return self._tree.overview(max_depth=max_depth)

    def focus(self, node_id: str) -> Dict[str, Any]:
        """執行器視圖：路徑列＋當層＋指令白名單。"""
        if self._tree is None:
            self.overview()
        assert self._tree is not None
        return self._tree.focus(node_id)

    # ---------- 全域搜尋（跨五類上下文） ----------

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """跨上下文關鍵字搜尋，回傳結果清單＋AI 可讀的樹狀文字。"""
        providers = self._providers()
        q = query.strip().lower()
        if not q:
            return {"ok": False, "error": "缺少 query"}
        results: List[Dict[str, Any]] = []
        results.extend(self._search_context_manager(providers, q, limit))
        results.extend(self._search_memories(providers, q, limit))
        results.extend(self._search_conversations(providers, q, limit))
        results.extend(self._search_tools(providers, q, limit))
        results = results[:limit]
        lines = [f"搜尋「{query}」——{len(results)} 筆結果"] + [
            f"  [{r['type']}] {r['id']}：{r['summary']}" for r in results
        ]
        return {"ok": True, "query": query, "results": results, "text": "\n".join(lines)}

    def _search_context_manager(
        self, providers: GlobalContextProviders, q: str, limit: int
    ) -> List[Dict[str, Any]]:
        ctxm = self._ctxm(providers)
        if ctxm is None:
            return []
        try:
            found = ctxm.search_contexts(q) or []
        except Exception as exc:
            logger.debug("context_manager.search_contexts failed: %s", exc)
            return []
        out: List[Dict[str, Any]] = []
        for ctx in found[:limit]:
            content = getattr(ctx, "content", {}) or {}
            out.append(
                {
                    "type": str(getattr(getattr(ctx, "context_type", None), "value", "custom")),
                    "id": str(getattr(ctx, "context_id", "")),
                    "summary": str(content.get("name", ""))[:80],
                }
            )
        return out

    def _search_memories(
        self, providers: GlobalContextProviders, q: str, limit: int
    ) -> List[Dict[str, Any]]:
        memories: Dict[str, Any] = getattr(providers.memory_manager, "memories", {}) or {}
        out: List[Dict[str, Any]] = []
        for mid, mem in memories.items():
            content = str(getattr(mem, "content", ""))
            if q in content.lower():
                out.append(
                    {
                        "type": "memory",
                        "id": mid,
                        "summary": f"{content[:60]}…"
                        if len(content) > 60
                        else content,
                    }
                )
            if len(out) >= limit:
                break
        return out

    def _search_conversations(
        self, providers: GlobalContextProviders, q: str, limit: int
    ) -> List[Dict[str, Any]]:
        convs: Dict[str, Any] = getattr(
            self._dialogue_manager(providers), "conversations", {}
        ) or {}
        out: List[Dict[str, Any]] = []
        for cid, conv in convs.items():
            if q in str(cid).lower():
                out.append({"type": "conversation", "id": cid, "summary": "ID 命中"})
            if len(out) >= limit:
                break
        return out

    def _search_tools(
        self, providers: GlobalContextProviders, q: str, limit: int
    ) -> List[Dict[str, Any]]:
        tools: Dict[str, Any] = getattr(providers.tool_manager, "tools", {}) or {}
        out: List[Dict[str, Any]] = []
        for tid, tool in tools.items():
            name = str(getattr(tool, "name", ""))
            if q in name.lower() or q in str(tid).lower():
                out.append({"type": "tool", "id": tid, "summary": name})
            if len(out) >= limit:
                break
        return out


class UnifiedWorkspace:
    """統一門面：全域上下文樹（五類上下文＋搜尋）＋代理工作區會話閉環。

    AI 的單一入口：overview()/focus()/search() 走全域樹；
    open_app()/act()/save_app()/close_app() 委派會話閉環。
    """

    def __init__(self, workspace: AgentWorkspace, tree: GlobalContextTree) -> None:
        self.workspace = workspace
        self.global_tree = tree

    # ---------- 全域上下文視圖 ----------

    def overview(self, max_depth: int = 3) -> Dict[str, Any]:
        return self.global_tree.overview(max_depth=max_depth)

    def focus(self, node_id: str) -> Dict[str, Any]:
        return self.global_tree.focus(node_id)

    def search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        return self.global_tree.search(query, limit=limit)

    # ---------- 會話閉環（委派） ----------

    async def open_app(self, app_id: str, purpose: str = "", source: str = "teaching") -> Dict[str, Any]:
        return await self.workspace.open_app(app_id, purpose=purpose, source=source)

    async def read_app(self, app_id: str) -> Dict[str, Any]:
        return await self.workspace.read_app(app_id)

    async def act(
        self,
        app_id: str,
        action: str,
        params: Optional[Dict[str, Any]] = None,
        confirm: bool = False,
        source: str = "exploration",
    ) -> Dict[str, Any]:
        return await self.workspace.act(
            app_id, action, params=params, confirm=confirm, source=source
        )

    async def save_app(self, app_id: str) -> Dict[str, Any]:
        return await self.workspace.save_app(app_id)

    async def close_app(self, app_id: str, confirm: bool = False) -> Dict[str, Any]:
        return await self.workspace.close_app(app_id, confirm=confirm)

    def learning_tail(self, limit: int = 20) -> list:
        return self.workspace.learning_tail(limit=limit)
