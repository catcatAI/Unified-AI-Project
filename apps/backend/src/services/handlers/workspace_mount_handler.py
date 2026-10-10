"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
WorkspaceMountHandler — mounts/unmounts agent applications on main-AI request.

Lets the main AI attach applications (shell/files whitelisted kinds) to the
agent workspace at runtime so it can operate them (open → act → close):
"把shell掛上" / "掛載文件" / "卸載shell" / "有哪些應用".
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

_UNMOUNT_RES = (
    "卸載",
    "卸下",
    "卸载",
    "unmount",
)


class WorkspaceMountHandler:
    """Handles app mount/unmount/list intents from ChatService."""

    async def handle(self, text: str, intent: str = "app_mount") -> str:
        action = self._parse_action(text)
        if action is None:
            return (
                "（掛載）請說要掛載什麼應用（可用：shell 命令執行、files 文件操作），或卸載哪個。"
            )
        workspace = self._get_workspace()
        if workspace is None:
            return "（掛載）代理工作區不可用。"
        try:
            if action[0] == "inspect":
                return self._inspect(workspace)
            if action[0] == "configure":
                return self._configure(workspace, action[1])
            if action[0] == "list":
                apps = self._available(workspace)
                if not apps:
                    return "（掛載）目前沒有可用應用。"
                lines = [
                    f"{a.get('app_id')}（{a.get('label')}）：{','.join(a.get('commands', []))}"
                    for a in apps
                ]
                return "（掛載）可用應用：\n" + "\n".join(lines)
            if action[0] == "mount":
                result = workspace.mount_app(action[1])
                if isinstance(result, dict) and result.get("ok"):
                    cmds = ",".join(result.get("commands", []))
                    return (
                        f"（掛載）已掛載 {result.get('app_id')}（{result.get('label')}），"
                        f"可用指令：{cmds}。可 open 開啟會話操作。"
                    )
                return f"（掛載）掛載失敗：{(result or {}).get('error', '未知錯誤')}"
            result = workspace.unmount_app(action[1])
            if isinstance(result, dict) and result.get("ok"):
                return f"（掛載）已卸載 {action[1]}。"
            return f"（掛載）卸載失敗：{(result or {}).get('error', '未知錯誤')}"
        except Exception as e:
            logger.warning(f"[WorkspaceMountHandler] failed: {e}", exc_info=True)
            return f"（掛載）執行失敗：{e}"

    def _get_workspace(self) -> Optional[object]:
        try:
            from api.lifespan import get_agent_workspace

            return get_agent_workspace()
        except Exception as exc:
            logger.debug(f"workspace unavailable: {exc}")
            return None

    def _available(self, workspace: object) -> list:
        try:
            if hasattr(workspace, "workspace"):
                sessions = getattr(getattr(workspace, "workspace"), "sessions", None)
            else:
                sessions = getattr(workspace, "sessions", None)
            if sessions is not None and hasattr(sessions, "available_apps"):
                return list(sessions.available_apps())
        except Exception as exc:
            logger.debug(f"available_apps failed: {exc}")
        return []

    def _inspect(self, workspace: object) -> str:
        """Agent self-inspection: mounted apps + open sessions + health."""
        try:
            inner = getattr(workspace, "workspace", workspace)
            sessions = getattr(inner, "sessions", None)
            apps = list(sessions.available_apps()) if sessions is not None else []
            lines = [f"可用應用 {len(apps)} 個："]
            for a in apps:
                record = sessions.get_session(a.get("app_id", "")) if sessions else None
                if record is not None:
                    state = getattr(record, "state", "?")
                    ops = getattr(record, "op_count", 0)
                    lines.append(
                        f"- {a.get('app_id')}（{a.get('label')}）：會話開啟中（{state}，op={ops}）"
                    )
                else:
                    lines.append(f"- {a.get('app_id')}（{a.get('label')}）：未開啟")
            try:
                ov = workspace.overview(max_depth=1)
                lines.append(f"工作區：{str(ov)[:120]}")
            except Exception:
                pass
            return "（自檢）\n" + "\n".join(lines)
        except Exception as e:
            logger.warning(f"[WorkspaceMountHandler] inspect failed: {e}", exc_info=True)
            return f"（自檢）查詢失敗：{e}"

    def _configure(self, workspace: object, target: str) -> str:
        """Compose an agent from modules for a target (puzzle assembly)."""
        from services.agent_workspace.modules import compose_agent, suggest_modules

        modules = suggest_modules(target)
        if not modules:
            return (
                "（配置）看不出要配什麼應用。可用模塊：shell-exec、shell-unity、"
                "shell-eda、files-rw、files-ro。例：配置一個Unity代理。"
            )
        app_id = re.sub(r"[^\w\-]+", "", target.replace(" ", ""))[:24] or "composed"
        try:
            mount = None
            inner = getattr(workspace, "workspace", workspace)
            if hasattr(inner, "compose_app"):
                mount = inner.compose_app
            elif hasattr(workspace, "compose_app"):
                mount = workspace.compose_app
            if mount is None:
                return "（配置）工作區不支援拼裝。"
            result = mount(app_id, modules, target[:20])
            if isinstance(result, dict) and result.get("ok"):
                return (
                    f"（配置）已按模塊拼裝 {app_id}（{'+'.join(modules)}），"
                    f"可用指令：{','.join(result.get('commands', []))}。"
                    "可 open 開啟會話操作。"
                )
            return f"（配置）拼裝失敗：{(result or {}).get('error', '未知錯誤')}"
        except Exception as e:
            logger.warning(f"[WorkspaceMountHandler] configure failed: {e}", exc_info=True)
            return f"（配置）執行失敗：{e}"

    # Info-seeking markers: with these and no action framing, the user wants
    # an explanation (配置文件在哪，怎麼掛載shell), never an action.
    _INFO_VETO = ("在哪", "是什麼", "是什么意思", "怎麼", "怎么", "如何")

    def _parse_action(self, text: str) -> Optional[tuple]:
        t = (text or "").strip()
        # Negated actions never act (不要卸載shell).
        if re.search(r"(不要|不用|別|不想|禁止).{0,4}(卸載|卸载|掛載|挂载|掛上|配置|組裝|拼裝)", t):
            return None

        def _has_veto(s: str) -> bool:
            return any(w in s for w in self._INFO_VETO)

        if re.search(r"(配置|組裝|拼裝|configure|compose)", t, re.IGNORECASE):
            if not _has_veto(t):
                target = re.sub(
                    r"(配置|組裝|拼裝|配一個|configure|compose|一個|一個新的|新的|代理|agent|應用|应用|幫我|帮我|請|请|給我|给我)",
                    "",
                    t,
                    flags=re.IGNORECASE,
                ).strip(" 的了，,：:、")
                return ("configure", target or t)
        if re.search(
            r"(代理狀態|代理健康|代理正常|會話狀態|会话状态|會話開著|会话开着"
            r"|agent status|agent health)",
            t,
            re.IGNORECASE,
        ):
            return ("inspect", "")
        if re.search(r"(有哪些|列出|可用|查看).{0,4}(應用|应用|app)", t, re.IGNORECASE):
            return ("list", "")
        if _has_veto(t):
            return None
        want_unmount = any(k in t for k in _UNMOUNT_RES)
        m = re.search(r"(shell|files|終端|命令行|命令列|終端機|文件|檔案|文件操作)", t)
        kind = m.group(1) if m else ""
        if want_unmount:
            if not kind:
                return ("unmount", "")
            # Resolve alias to app_id via registry (shell/files ids match kinds).
            from services.agent_workspace.agent import MOUNT_KIND_ALIASES

            return ("unmount", MOUNT_KIND_ALIASES.get(kind.strip().lower(), kind))
        if not kind:
            return None
        return ("mount", kind)
