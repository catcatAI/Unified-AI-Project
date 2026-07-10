"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
CodeExecutionHandler — executes Python code in a restricted sandbox.
"""

import asyncio
import io
import logging
import sys
import threading
import traceback
from typing import Any, Dict, Optional

from core.i18n.i18n_manager import t
from core.utils import safe_error

logger = logging.getLogger(__name__)

_MAX_OUTPUT = 4000
_TIMEOUT = 10
_MAX_TRACEBACK_LINES = 10

_BUILTINS_WHITELIST = {
    "abs", "all", "any", "bool", "chr", "dict", "dir", "enumerate",
    "filter", "float", "format", "frozenset", "getattr", "hasattr",
    "hash", "hex", "id", "int", "isinstance", "issubclass", "iter",
    "len", "list", "map", "max", "min", "next", "oct", "ord", "pow",
    "print", "range", "repr", "reversed", "round", "set", "setattr",
    "slice", "sorted", "str", "sum", "tuple", "type", "zip",
}


class CodeExecutionHandler:
    """Executes Python code snippets in a restricted environment."""

    async def handle(self, text: str, intent: str = "code") -> str:
        code = self._extract_code(text)
        if not code:
            return t("code_exec.specify_code")
        if len(code) > 10000:
            return t("code_exec.code_too_long")
        return await self._execute(code)

    def _extract_code(self, text: str) -> str:
        import re
        m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        m = re.search(r"`([^`]+)`", text)
        if m:
            return m.group(1).strip()
        lines = text.strip().splitlines()
        code_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("import ", "from ", "def ", "class ", "if ", "for ",
                                   "while ", "try:", "with ", "return ", "print(",
                                   "#", "raise ", "assert ", "yield ")) or "=" in stripped or "(" in stripped:
                code_lines.append(line)
            elif code_lines:
                break
        return "\n".join(code_lines).strip() if code_lines else text.strip()

    async def _execute(self, code: str) -> str:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_out = io.StringIO()
        captured_err = io.StringIO()
        restricted_globals: Dict[str, Any] = {"__builtins__": {}}
        for name in _BUILTINS_WHITELIST:
            restricted_globals["__builtins__"][name] = (
                __builtins__[name] if isinstance(__builtins__, dict)
                else getattr(__builtins__, name)
            )

        def _run_exec():
            exec(code, restricted_globals)

        timeout_triggered = threading.Event()
        timer = threading.Timer(_TIMEOUT, timeout_triggered.set)
        try:
            sys.stdout = captured_out
            sys.stderr = captured_err
            await asyncio.wait_for(
                asyncio.to_thread(_run_exec),
                timeout=_TIMEOUT,
            )
            stdout_val = captured_out.getvalue()[:_MAX_OUTPUT]
            stderr_val = captured_err.getvalue()[:_MAX_OUTPUT]
            parts = []
            if stdout_val:
                parts.append(t("code_exec.output", output=stdout_val))
            if stderr_val:
                parts.append(t("code_exec.error", error=stderr_val))
            if not parts:
                return t("code_exec.complete_no_output")
            return t("code_exec.header") + "\n" + "\n".join(parts)
        except asyncio.TimeoutError:
            return t("code_exec.timeout", seconds=_TIMEOUT)
        except Exception as e:
            tb = traceback.format_exc()
            lines = tb.splitlines()
            if len(lines) > _MAX_TRACEBACK_LINES:
                tb = "\n".join(lines[:_MAX_TRACEBACK_LINES]) + f"\n... (後續 {len(lines) - _MAX_TRACEBACK_LINES} 行已省略)"
            if len(tb) > _MAX_OUTPUT:
                tb = tb[:_MAX_OUTPUT] + "\n... (已截斷)"
            logger.warning(f"Code execution error: {e}")
            safe_msg = safe_error(e) if isinstance(e, Exception) else str(e)
            return t("code_exec.execution_error", traceback=safe_msg)
        finally:
            timer.cancel()
            sys.stdout = old_stdout
            sys.stderr = old_stderr


__all__ = ["CodeExecutionHandler"]
