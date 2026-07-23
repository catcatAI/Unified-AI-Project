"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
CodeExecutionHandler — executes Python code in a restricted sandbox.
"""

import ast
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

_BLOCKED_DUNDER_ATTRS = frozenset({
    "__subclasses__", "__class__", "__bases__", "__mro__",
    "__globals__", "__code__", "__closure__", "__defaults__",
    "__import__", "__builtins__", "__loader__", "__spec__",
    "__dict__", "__weakref__", "__slots__", "__qualname__",
    "__init_subclass__", "__set_name__", "__init__",
    "__del__", "__delattr__", "__delete__",
    "__format__", "__round__", "__trunc__", "__floor__", "__ceil__",
    "__pos__", "__neg__", "__abs__", "__invert__",
    "__add__", "__sub__", "__mul__", "__truediv__", "__floordiv__",
    "__mod__", "__pow__", "__lshift__", "__rshift__",
    "__and__", "__or__", "__xor__",
    "__getattr__", "__getattribute__",
    "__setattr__", "__set__", "__set_name__",
    "__call__", "__len__", "__length_hint__",
    "__getitem__", "__setitem__", "__delitem__",
    "__contains__", "__iter__", "__next__",
    "__enter__", "__exit__",
    "__aenter__", "__aexit__",
    "__index__", "__int__", "__float__", "__complex__",
    "__bool__", "__hash__", "__eq__", "__ne__",
    "__lt__", "__le__", "__gt__", "__ge__",
    "__repr__", "__str__", "__bytes__",
    "__copy__", "__deepcopy__", "__reduce__", "__reduce_ex__",
    "__sizeof__", "__dir__",
})

_BLOCKED_CALL_NAMES = frozenset({
    "exec", "eval", "compile", "__import__", "open", "input",
    "breakpoint", "exit", "quit", "help",
})

_BLOCKED_IMPORT_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "urllib", "requests",
    "ctypes", "importlib", "code", "codeop",
    "signal", "threading", "multiprocessing",
    "pickle", "shelve", "marshal",
})


class _SandboxViolation(Exception):
    """Raised when code violates sandbox restrictions."""


_BUILTINS_WHITELIST = {
    "abs",
    "all",
    "any",
    "bool",
    "chr",
    "dict",
    "dir",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "getattr",
    "hasattr",
    "hash",
    "hex",
    "id",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "setattr",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
    "zip",
}


class _SafetyChecker(ast.NodeVisitor):
    """AST walker that rejects sandbox-escape patterns."""

    def __init__(self):
        self._depth = 0

    def _check_name(self, node: ast.expr, context: str = "") -> None:
        if isinstance(node, ast.Name) and node.id in _BLOCKED_CALL_NAMES:
            raise _SandboxViolation(f"Blocked call: {node.id}{context}")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in _BLOCKED_DUNDER_ATTRS:
            raise _SandboxViolation(f"Blocked attribute: {node.attr}")
        if node.attr.startswith("__") and node.attr.endswith("__"):
            raise _SandboxViolation(f"Blocked dunder attribute: {node.attr}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self._check_name(node.func, "()")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in _BLOCKED_CALL_NAMES:
                raise _SandboxViolation(f"Blocked method call: {node.func.attr}()")
            if node.func.attr.startswith("__") and node.func.attr.endswith("__"):
                raise _SandboxViolation(f"Blocked dunder method call: {node.func.attr}()")
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in _BLOCKED_IMPORT_MODULES:
                raise _SandboxViolation(f"Blocked import: {alias.name}")
            if alias.name.startswith("_"):
                raise _SandboxViolation(f"Blocked private import: {alias.name}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            root = node.module.split(".")[0]
            if root in _BLOCKED_IMPORT_MODULES:
                raise _SandboxViolation(f"Blocked import: {node.module}")
            if node.level > 0:
                raise _SandboxViolation("Blocked relative import")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _BLOCKED_CALL_NAMES:
            raise _SandboxViolation(f"Blocked name access: {node.id}")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred) -> None:
        self.generic_visit(node)


def _validate_code_safety(code: str) -> None:
    """Parse code and reject sandbox-escape patterns via AST analysis."""
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as e:
        raise _SandboxViolation(f"Syntax error: {e}") from e

    checker = _SafetyChecker()
    for node in ast.walk(tree):
        checker.visit(node)


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
            if (
                stripped.startswith(
                    (
                        "import ",
                        "from ",
                        "def ",
                        "class ",
                        "if ",
                        "for ",
                        "while ",
                        "try:",
                        "with ",
                        "return ",
                        "print(",
                        "#",
                        "raise ",
                        "assert ",
                        "yield ",
                    )
                )
                or "=" in stripped
                or "(" in stripped
            ):
                code_lines.append(line)
            elif code_lines:
                break
        return "\n".join(code_lines).strip() if code_lines else text.strip()

    async def _execute(self, code: str) -> str:
        try:
            _validate_code_safety(code)
        except _SandboxViolation as e:
            logger.warning(f"Code sandbox violation: {e}")
            safe_msg = safe_error(e) if isinstance(e, Exception) else str(e)
            return t("code_exec.execution_error", traceback=safe_msg)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_out = io.StringIO()
        captured_err = io.StringIO()
        restricted_globals: Dict[str, Any] = {"__builtins__": {}}
        for name in _BUILTINS_WHITELIST:
            restricted_globals["__builtins__"][name] = (
                __builtins__[name]
                if isinstance(__builtins__, dict)
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
                tb = (
                    "\n".join(lines[:_MAX_TRACEBACK_LINES])
                    + f"\n... (後續 {len(lines) - _MAX_TRACEBACK_LINES} 行已省略)"
                )
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
