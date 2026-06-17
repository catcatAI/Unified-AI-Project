"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
SystemCommandHandler — executes safe system commands (non-destructive).
Uses create_subprocess_exec (no shell) to prevent injection.
"""

import asyncio
import logging
import platform
import shutil
from typing import Optional

from core.i18n.i18n_manager import t

logger = logging.getLogger(__name__)

_TIMEOUT = 15
_MAX_OUTPUT = 4000

_SAFE_COMMANDS = {
    "date", "time", "whoami", "hostname", "pwd", "uname", "uptime",
    "df", "du", "free", "top", "ps", "ls", "dir", "cat", "head",
    "tail", "wc", "echo", "env", "printenv", "which", "where",
    "tasklist", "systeminfo", "ipconfig", "ifconfig", "ping",
    "git", "pnpm",
}


class SystemCommandHandler:
    """Executes safe system commands with output capture."""

    async def handle(self, text: str, intent: str = "system") -> str:
        cmd = self._extract_command(text)
        if not cmd:
            return t("sys_cmd.specify_command")
        parts = cmd.split()
        base_cmd = parts[0].lower() if parts else ""
        if base_cmd not in _SAFE_COMMANDS:
            return t("sys_cmd.unsafe_command", cmd=base_cmd, allowed=", ".join(sorted(_SAFE_COMMANDS)))
        return await self._run(base_cmd, parts)

    def _extract_command(self, text: str) -> Optional[str]:
        import re
        m = re.search(r"```(?:bash|sh|shell|cmd)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        m = re.search(r"`([^`]+)`", text)
        if m:
            return m.group(1).strip()
        prefixes = ["執行", "运行", "執行命令", "运行命令", "run", "execute", "cmd"]
        for p in prefixes:
            if text.lower().startswith(p):
                return text[len(p):].strip().strip(":：").strip()
        return text.strip()

    async def _run(self, base_cmd: str, parts: list) -> str:
        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(
                *parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=_TIMEOUT)
            stdout_str = stdout.decode("utf-8", errors="replace")[:_MAX_OUTPUT]
            stderr_str = stderr.decode("utf-8", errors="replace")[:_MAX_OUTPUT]
            result_parts = []
            if proc.returncode != 0:
                result_parts.append(t("sys_cmd.exit_code", code=proc.returncode))
            if stdout_str:
                result_parts.append(t("sys_cmd.output", output=stdout_str))
            if stderr_str:
                result_parts.append(t("sys_cmd.error", error=stderr_str))
            if not result_parts:
                return t("sys_cmd.complete_no_output")
            return t("sys_cmd.header") + "\n" + "\n".join(result_parts)
        except asyncio.TimeoutError:
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
            return t("sys_cmd.timeout", seconds=_TIMEOUT)
        except Exception as e:
            logger.error(f"SystemCommandHandler error: {e}", exc_info=True)
            return t("sys_cmd.failed", error=str(e))


__all__ = ["SystemCommandHandler"]
