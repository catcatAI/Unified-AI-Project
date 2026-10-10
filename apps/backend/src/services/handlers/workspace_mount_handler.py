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

    def _parse_action(self, text: str) -> Optional[tuple]:
        t = (text or "").strip()
        if re.search(r"(有哪些|列出|可用|查看).{0,4}(應用|应用|app)", t, re.IGNORECASE):
            return ("list", "")
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
