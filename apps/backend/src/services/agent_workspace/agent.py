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
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from services.agent_workspace.app_session import (
    DEFAULT_LOG_PATH,
    ActionSpec,
    AppAdapter,
    AppSessionManager,
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
        self.register(ActionSpec("organize", "依類別整理桌面檔案", dangerous=True), self._organize)
        self.register(ActionSpec("cleanup", "清理 N 天前的舊檔案", dangerous=True), self._cleanup)

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
        self.register(ActionSpec("add_bookmark", "新增書籤", dangerous=True), self._add_bookmark)

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


# ---------- 可動態掛載的應用（白名單種類） ----------

_MOUNT_ROOTS: List[Path] = [
    Path.home(),
    Path(os.environ.get("ANGELA_WORKSPACE", os.getcwd())),
    Path("/tmp"),
]

# Shell denylist: obvious destructors blocked even after confirmation.
_SHELL_DENY = (
    "rm -rf /",
    "mkfs",
    " dd ",
    ":(){",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
    "iptables",
    "> /dev/sd",
)


def _is_mount_safe_path(target: Path) -> bool:
    """Jail paths under mount roots (mirrors DesktopInteraction._is_safe_path)."""
    try:
        resolved = target.resolve()
    except Exception:
        return False
    for root in _MOUNT_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


class ShellAdapter(AppAdapter):
    """受控命令執行（開發／維運操作）。run 恆為危險指令，需 confirm=True。

    Safety: confirm gate (framework) + cwd jail + denylist + timeout +
    output truncation. No interactive commands.
    """

    app_id = "shell"
    label = "命令執行"

    def __init__(self, workdir: Any = None) -> None:
        super().__init__()
        self._workdir = Path(str(workdir or os.environ.get("ANGELA_WORKSPACE", os.getcwd())))
        self.register(
            ActionSpec("run", "執行 shell 指令（需確認，有超時與輸出截斷）", dangerous=True),
            self._run,
        )

    async def _run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        cmd = str(params.get("cmd", "") or "").strip()
        if not cmd:
            return {"ok": False, "error": "缺少 cmd"}
        lowered = f" {cmd.lower()} "
        if any(d.strip().lower() in lowered for d in _SHELL_DENY if d.strip()):
            return {"ok": False, "error": "拒絕危險指令"}
        explicit_cwd = str(params.get("cwd", "") or "").strip()
        cwd = Path(explicit_cwd) if explicit_cwd else Path(self._workdir)
        if not cwd.is_absolute():
            cwd = Path(os.getcwd()) / cwd
        if not (cwd.exists() and cwd.is_dir()):
            if explicit_cwd:
                return {"ok": False, "error": f"工作目錄不存在：{cwd}"}
            # Default workdir (e.g. ANGELA_WORKSPACE=./workspace) missing:
            # fall back to the process cwd instead of failing every run.
            cwd = Path(os.getcwd())
        if not _is_mount_safe_path(cwd):
            return {"ok": False, "error": f"工作目錄越界：{cwd}"}
        try:
            timeout = float(params.get("timeout", 60))
        except (TypeError, ValueError):
            timeout = 60.0
        timeout = min(max(timeout, 1.0), 300.0)
        try:
            proc = await _run_shell(cmd, str(cwd), timeout)
        except Exception as exc:
            return {"ok": False, "error": f"執行失敗：{exc}"}
        return proc


async def _run_shell(cmd: str, cwd: str, timeout: float) -> Dict[str, Any]:
    """Blocking subprocess offloaded to a worker thread (keeps loop responsive)."""
    import asyncio as _asyncio

    def _call() -> Dict[str, Any]:
        try:
            done = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"超時（>{timeout:.0f}s）"}
        out = (done.stdout or "")[-4000:]
        err = (done.stderr or "")[-1000:]
        return {
            "ok": done.returncode == 0,
            "returncode": done.returncode,
            "stdout": out,
            "stderr": err,
        }

    return await _asyncio.to_thread(_call)


class FilesAdapter(AppAdapter):
    """沙盒文件操作（list/read 安全，write 危險需確認），路徑監禁。"""

    app_id = "files"
    label = "文件操作"

    def __init__(self) -> None:
        super().__init__()
        self.register(ActionSpec("list", "列出目錄（限監禁範圍）"), self._list)
        self.register(ActionSpec("read", "讀取文字檔（64KB 上限）"), self._read)
        self.register(
            ActionSpec("write", "寫入文字檔（1MB 上限，需確認）", dangerous=True),
            self._write,
        )

    async def _list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = Path(str(params.get("path", "") or ""))
        if not _is_mount_safe_path(path):
            return {"ok": False, "error": f"路徑越界：{path}"}
        try:
            if not path.is_dir():
                return {"ok": False, "error": f"非目錄：{path}"}
            names = sorted(p.name for p in path.iterdir())[:200]
            return {"ok": True, "path": str(path), "entries": names, "count": len(names)}
        except Exception as exc:
            return {"ok": False, "error": f"列舉失敗：{exc}"}

    async def _read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = Path(str(params.get("path", "") or ""))
        if not _is_mount_safe_path(path):
            return {"ok": False, "error": f"路徑越界：{path}"}
        try:
            if not path.is_file():
                return {"ok": False, "error": f"非檔案：{path}"}
            if path.stat().st_size > 65536:
                return {"ok": False, "error": "檔案過大（>64KB）"}
            return {
                "ok": True,
                "path": str(path),
                "content": path.read_text(encoding="utf-8", errors="replace"),
            }
        except Exception as exc:
            return {"ok": False, "error": f"讀取失敗：{exc}"}

    async def _write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        path = Path(str(params.get("path", "") or ""))
        content = str(params.get("content", "") or "")
        if not _is_mount_safe_path(path):
            return {"ok": False, "error": f"路徑越界：{path}"}
        if len(content.encode("utf-8")) > 1048576:
            return {"ok": False, "error": "內容過大（>1MB）"}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {"ok": True, "path": str(path), "bytes": len(content.encode("utf-8"))}
        except Exception as exc:
            return {"ok": False, "error": f"寫入失敗：{exc}"}


# 可掛載種類白名單：主 AI 只能掛這些，任意類別永遠進不來。
MOUNT_KIND_REGISTRY: Dict[str, Any] = {
    "shell": ShellAdapter,
    "files": FilesAdapter,
}

# 中文別名（主 AI 意圖解析用）。
MOUNT_KIND_ALIASES: Dict[str, str] = {
    "shell": "shell",
    "終端": "shell",
    "命令行": "shell",
    "命令列": "shell",
    "終端機": "shell",
    "files": "files",
    "文件": "files",
    "檔案": "files",
    "文件操作": "files",
}


# ANGELA-MATRIX: L6 [βγδ] [A] [L3]
class EdaWorkspaceAdapter(AppAdapter):
    """把既有 EdaAgent 暴露到統一工作區，不建立第二份 EDA 實例。"""

    app_id = "eda"
    label = "硬體設計工程"

    def __init__(self, agent_provider: Optional[Callable[[], Any]] = None) -> None:
        super().__init__()
        self._agent_provider = agent_provider
        self.register(
            ActionSpec("probe_tools", "探測目前可用的本機 EDA 工具"),
            self._probe_tools,
        )
        self.register(
            ActionSpec(
                "run_ai_card_reference",
                "執行 AI 計算卡 software-only reference 與可重播 episode",
            ),
            self._run_ai_card_reference,
        )
        self.register(
            ActionSpec(
                "read_interface_packet",
                "讀取 AI 計算卡決策包與待驗證項目",
            ),
            self._read_interface_packet,
        )
        self.register(
            ActionSpec(
                "search_hardware_standards",
                "查詢官方硬體與驗證標準來源、版本與适用范围",
            ),
            self._search_hardware_standards,
        )

    def _get_agent(self) -> Any:
        if self._agent_provider is None:
            return None
        try:
            return self._agent_provider()
        except Exception as exc:
            logger.warning("EDA agent provider unavailable: %s", exc)
            return None

    @staticmethod
    def _normalize_result(result: Dict[str, Any]) -> Dict[str, Any]:
        status = str(result.get("status", "")).lower()
        ok = result.get("ok")
        if ok is None:
            ok = status not in {"error", "unavailable"}
        return {"ok": bool(ok), "result": result}

    async def read_state(self) -> Dict[str, Any]:
        agent = self._get_agent()
        if agent is None:
            return {"ok": False, "error": "EDA agent 尚未由 AgentManager 註冊"}
        status = agent.get_status() if hasattr(agent, "get_status") else {}
        return {
            "ok": True,
            "agent_id": getattr(agent, "agent_id", "eda_agent"),
            "status": status,
            "capabilities": list(getattr(agent, "capabilities", [])),
        }

    async def _probe_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        agent = self._get_agent()
        if agent is None:
            return {"ok": False, "error": "EDA agent 尚未由 AgentManager 註冊"}
        return self._normalize_result(await agent.probe_tools())

    async def _run_ai_card_reference(self, params: Dict[str, Any]) -> Dict[str, Any]:
        agent = self._get_agent()
        if agent is None:
            return {"ok": False, "error": "EDA agent 尚未由 AgentManager 註冊"}
        return self._normalize_result(await agent.run_ai_card_reference_experiment())

    async def _read_interface_packet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        agent = self._get_agent()
        if agent is None:
            return {"ok": False, "error": "EDA agent 尚未由 AgentManager 註冊"}
        return self._normalize_result(agent.get_ai_card_interface_packet())

    async def _search_hardware_standards(self, params: Dict[str, Any]) -> Dict[str, Any]:
        agent = self._get_agent()
        if agent is None:
            return {"ok": False, "error": "EDA agent 尚未由 AgentManager 註冊"}
        query = str(params.get("query", "")).strip()
        return self._normalize_result(agent.get_hardware_standards(query))


class AgentWorkspace:
    """代理工作區：上下文樹＋會話管理的統一門面（AI 的單一操作入口）。"""

    def __init__(
        self,
        session_manager: Optional[AppSessionManager] = None,
        view_budget: int = 8000,
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
        root.children.append(self.build_sessions_root())
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
            view_budget=self.tree._budget if hasattr(self, "tree") else 8000,
            children_limit=self.tree._children_limit if hasattr(self, "tree") else 12,
        )

    def build_sessions_root(self) -> ContextNode:
        """應用會話子樹（id 固定 "apps"）——全域上下文樹掛載同一份狀態。"""
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
        return apps_node

    def overview(self, max_depth: int = 3) -> Dict[str, Any]:
        """全貌視圖（唯讀）。"""
        self._rebuild_tree()
        return self.tree.overview(max_depth=max_depth)

    def focus(self, node_id: str) -> Dict[str, Any]:
        """執行器視圖（路徑列＋當層＋白名單指令）。"""
        self._rebuild_tree()
        return self.tree.focus(node_id)

    # ---------- 會話閉環（同時刷新樹） ----------

    async def open_app(
        self, app_id: str, purpose: str = "", source: str = "teaching"
    ) -> Dict[str, Any]:
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

    def mount_app(self, kind: str, app_id: str = "", label: str = "") -> Dict[str, Any]:
        """Mount a whitelisted app kind at runtime (main AI mounts as needed)."""
        key = MOUNT_KIND_ALIASES.get(str(kind or "").strip().lower(), "")
        if not key:
            return {
                "ok": False,
                "error": f"不可掛載種類：{kind}；可用：{sorted(MOUNT_KIND_REGISTRY)}",
            }
        adapter = MOUNT_KIND_REGISTRY[key]()
        if app_id.strip():
            adapter.app_id = app_id.strip()
        if label.strip():
            adapter.label = label.strip()
        result = self.sessions.mount_adapter(adapter, source="workspace")
        self._rebuild_tree()
        return result

    def unmount_app(self, app_id: str) -> Dict[str, Any]:
        result = self.sessions.unmount_adapter(app_id, source="workspace")
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
    eda_agent_provider: Optional[Callable[[], Any]] = None,
) -> AgentWorkspace:
    """以 DI getters 的單例組出預設工作區（能力缺失時降級為空 adapter 也可註冊）。"""
    manager = AppSessionManager(
        adapters={
            "desktop": DesktopAgent(desktop_interaction),
            "browser": BrowserAgent(browser_controller),
            "eda": EdaWorkspaceAdapter(eda_agent_provider),
        },
        log_path=log_path,
        protected_ids={"desktop", "browser", "eda"},
    )
    return AgentWorkspace(session_manager=manager)
