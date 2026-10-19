"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
CodeExecutionHandler — executes Python code in a restricted sandbox.
"""

import ast
import asyncio
import io
import logging
import re
import sys
import traceback
from typing import Any, Dict, List, Optional

from core.i18n.i18n_manager import t
from core.security.secure_eval import MAX_POW_EXPONENT, MAX_RANGE_END, MAX_STRING_REPEAT
from core.utils import safe_error

logger = logging.getLogger(__name__)

_MAX_OUTPUT = 4000
_TIMEOUT = 10
_MAX_TRACEBACK_LINES = 10

_BLOCKED_DUNDER_ATTRS = frozenset(
    {
        "__subclasses__",
        "__class__",
        "__bases__",
        "__mro__",
        "__globals__",
        "__code__",
        "__closure__",
        "__defaults__",
        "__import__",
        "__builtins__",
        "__loader__",
        "__spec__",
        "__dict__",
        "__weakref__",
        "__slots__",
        "__qualname__",
        "__init_subclass__",
        "__set_name__",
        "__init__",
        "__del__",
        "__delattr__",
        "__delete__",
        "__format__",
        "__round__",
        "__trunc__",
        "__floor__",
        "__ceil__",
        "__pos__",
        "__neg__",
        "__abs__",
        "__invert__",
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",
        "__floordiv__",
        "__mod__",
        "__pow__",
        "__lshift__",
        "__rshift__",
        "__and__",
        "__or__",
        "__xor__",
        "__getattr__",
        "__getattribute__",
        "__setattr__",
        "__set__",
        "__set_name__",
        "__call__",
        "__len__",
        "__length_hint__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__contains__",
        "__iter__",
        "__next__",
        "__enter__",
        "__exit__",
        "__aenter__",
        "__aexit__",
        "__index__",
        "__int__",
        "__float__",
        "__complex__",
        "__bool__",
        "__hash__",
        "__eq__",
        "__ne__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__repr__",
        "__str__",
        "__bytes__",
        "__copy__",
        "__deepcopy__",
        "__reduce__",
        "__reduce_ex__",
        "__sizeof__",
        "__dir__",
    }
)

_BLOCKED_CALL_NAMES = frozenset(
    {
        "exec",
        "eval",
        "compile",
        "__import__",
        "open",
        "input",
        "breakpoint",
        "exit",
        "quit",
        "help",
        # Attribute-reflection builtins: getattr/setattr with a dunder string
        # argument bypass the AST Attribute-node dunder check (C3 sandbox escape).
        "getattr",
        "setattr",
        "vars",
        "globals",
        "locals",
    }
)

# AST 階段直接拒 import（2026-10-18 稽核）：先前只擋危險模組白名單外全放行，
# 但 exec 的 __builtins__ 無 __import__ —— 任何 import 都會以 NameError
# 必失敗（AST 說允許、執行必炸的死契約）。明示不支援是誠實契約。
# 想跑 math/re/json 等請用內建函式或既有執行通道。


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
            # 常數 range 上限（與 safe_eval 同源）：list(range(10**9)) 可在
            # 10s timeout 內吃掉數十 GB 記憶體——迭代 DoS 與 OOM 同類。
            if node.func.id == "range":
                for arg in node.args:
                    if (
                        isinstance(arg, ast.Constant)
                        and isinstance(arg.value, int)
                        and abs(arg.value) > MAX_RANGE_END
                    ):
                        raise _SandboxViolation(
                            f"range 大小 {arg.value} 超過上限 {MAX_RANGE_END}（防 OOM）"
                        )
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in _BLOCKED_CALL_NAMES:
                raise _SandboxViolation(f"Blocked method call: {node.func.attr}()")
            if node.func.attr.startswith("__") and node.func.attr.endswith("__"):
                raise _SandboxViolation(f"Blocked dunder method call: {node.func.attr}()")
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        # 記憶體擴張守衛（2026-10-18 稽核）：'x'*200_000_000 過 AST、
        # exec 直接配置 200MB = OOM DoS。常數側超限即拒。
        if isinstance(node.op, ast.Mult):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant):
                    if isinstance(side.value, str) and len(side.value) > MAX_STRING_REPEAT:
                        raise _SandboxViolation("字串重複超過上限（防 OOM）")
                    if isinstance(side.value, int) and abs(side.value) > MAX_STRING_REPEAT:
                        raise _SandboxViolation(
                            f"乘法常數 {side.value} 超過上限 {MAX_STRING_REPEAT}（防 OOM）"
                        )
        elif isinstance(node.op, ast.Pow):
            if (
                isinstance(node.right, ast.Constant)
                and isinstance(node.right.value, int)
                and abs(node.right.value) > MAX_POW_EXPONENT
            ):
                raise _SandboxViolation(
                    f"冪次指數 {node.right.value} 超過上限 {MAX_POW_EXPONENT}（防巨整數 DoS）"
                )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            raise _SandboxViolation(f"沙箱不支援 import（執行環境無 __import__）：{alias.name}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise _SandboxViolation(f"沙箱不支援 import（執行環境無 __import__）：{node.module or '.'}")

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in _BLOCKED_CALL_NAMES:
            raise _SandboxViolation(f"Blocked name access: {node.id}")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.generic_visit(node)

    def visit_Starred(self, node: ast.Starred) -> None:
        self.generic_visit(node)


def _parseable(cand: str) -> Optional[str]:
    """Return cand if it parses as an eval expression, else None."""
    try:
        ast.parse(cand, mode="eval")
    except SyntaxError:
        return None
    return cand


def _extract_paren_calls(text: str) -> List[str]:
    """Call expressions with balanced parentheses (supports nesting)."""
    candidates: List[str] = []
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*\s*\(", text):
        start = m.start()
        depth = 0
        i = m.end() - 1
        while i < len(text):
            ch = text[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth != 0:
            continue
        cand = _parseable(text[start : i + 1].strip())
        if cand is not None:
            candidates.append(cand)
    return candidates


def _extract_arith(text: str) -> List[str]:
    """Simple arithmetic like ``1+1`` / ``3*7``."""
    candidates: List[str] = []
    for m in re.finditer(r"\d+(?:\.\d+)?\s*[+\-*/%^]\s*\d+(?:\.\d+)?", text):
        cand = _parseable(m.group(0).strip())
        if cand is not None:
            candidates.append(cand)
    return candidates


def _extract_inline_code(text: str) -> str:
    """Extract a short Python snippet embedded in natural language.

    Handles cases like ``執行 print(42)``, ``運行 1+1``, or nested calls such
    as ``執行 print(getattr((), '__class__'))`` where the user did not use a
    code fence. Scans for balanced-parenthesis call expressions and simple
    arithmetic, keeping only candidates that are themselves valid Python so
    prose is never fed to exec().
    """
    if not text or not text.strip():
        return ""
    candidates = _extract_paren_calls(text) + _extract_arith(text)
    if candidates:
        # Prefer the longest parseable candidate (most likely the real snippet).
        return max(candidates, key=len)
    return ""


def _looks_code_shaped(first_line: str, full_text: str) -> bool:
    """Heuristic: is the text likely a raw Python snippet rather than prose?

    Used only when no fence / inline-code / parseable expression was found,
    to avoid feeding natural language (e.g. "你好嗎") to exec(). Accepts text
    whose first line starts with a Python keyword, or a single short line that
    is predominantly ASCII code characters.
    """
    if not first_line:
        return False
    _KEYWORDS = (
        "import ",
        "from ",
        "def ",
        "class ",
        "if ",
        "elif ",
        "else:",
        "for ",
        "while ",
        "try:",
        "except ",
        "finally:",
        "with ",
        "return",
        "yield",
        "break",
        "continue",
        "pass",
        "del ",
        "global ",
        "nonlocal ",
        "async ",
        "await ",
        "print(",
        "raise ",
        "assert ",
    )
    if first_line.startswith(_KEYWORDS) or "=" in first_line:
        return True
    # Single-line fallback: mostly ASCII / code punctuation, no CJK prose.
    if len(full_text.splitlines()) == 1 and len(first_line) <= 120:
        ascii_chars = sum(1 for ch in first_line if ord(ch) < 128)
        if ascii_chars >= len(first_line) * 0.8:
            return True
    return False


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
        # No code fence / inline code. If the message itself is already
        # multi-line code (or starts with a compound-statement keyword like
        # ``for`` / ``if`` / ``def``), treat it as raw code — inline extraction
        # would otherwise grab just ``range(3)`` out of ``for i in range(3):``.
        stripped_first = text.strip().splitlines()[0].strip() if text.strip() else ""
        if len(text.strip().splitlines()) > 1 or stripped_first.startswith(
            ("for ", "if ", "while ", "def ", "class ", "try:", "with ", "async ", "@")
        ):
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
                            "elif ",
                            "else:",
                            "for ",
                            "while ",
                            "try:",
                            "except ",
                            "finally:",
                            "with ",
                            "return",
                            "yield",
                            "break",
                            "continue",
                            "pass",
                            "del ",
                            "global ",
                            "nonlocal ",
                            "async ",
                            "await ",
                            "@",
                            "print(",
                            "#",
                            "raise ",
                            "assert ",
                        )
                    )
                    or "=" in stripped
                    or "(" in stripped
                ):
                    code_lines.append(line)
                elif code_lines:
                    if not stripped:
                        code_lines.append(line)
                        continue
                    break
            return "\n".join(code_lines).strip() if code_lines else text.strip()
        # Otherwise: short single-line message is natural language around a
        # snippet (e.g. "執行 print(42)" / "運行 1+1"). Extract the longest
        # parseable Python expression instead of feeding the whole sentence
        # (with Chinese words) to exec().
        code = _extract_inline_code(text)
        if code:
            return code
        # Nothing parseable was found — treat the raw text as the snippet only
        # if it is clearly code-shaped (starts with a Python keyword or is a
        # single short line). Prose like "你好嗎" is not executable code.
        stripped_text = text.strip()
        first_line = stripped_text.splitlines()[0].strip() if stripped_text else ""
        if not _looks_code_shaped(first_line, stripped_text):
            return ""
        # Single-line, code-shaped text (e.g. ``import os`` / ``x = 1``).
        return stripped_text

    @staticmethod
    def _restricted_builtins_globals() -> Dict[str, Any]:
        """Build exec globals with whitelist-only builtins."""
        restricted_globals: Dict[str, Any] = {"__builtins__": {}}
        for name in _BUILTINS_WHITELIST:
            restricted_globals["__builtins__"][name] = (
                __builtins__[name]
                if isinstance(__builtins__, dict)
                else getattr(__builtins__, name)
            )
        return restricted_globals

    @staticmethod
    def _build_exec_output(stdout_val: str, stderr_val: str) -> str:
        """Assemble captured stdout/stderr into the i18n response text."""
        parts = []
        if stdout_val:
            parts.append(t("code_exec.output", output=stdout_val))
        if stderr_val:
            parts.append(t("code_exec.error", error=stderr_val))
        if not parts:
            return t("code_exec.complete_no_output")
        return t("code_exec.header") + "\n" + "\n".join(parts)

    @staticmethod
    def _exec_error_response(e: BaseException) -> str:
        """Exception path: traceback 摘要＋記錄＋i18n 錯誤回執。"""
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
        restricted_globals = self._restricted_builtins_globals()

        def _run_exec():
            # Code-execution tool: _validate_code_safety() already vetted the
            # snippet and builtins are whitelist-only — exec is the feature.
            exec(code, restricted_globals)  # nosec B102

        try:
            sys.stdout = captured_out
            sys.stderr = captured_err
            await asyncio.wait_for(
                asyncio.to_thread(_run_exec),
                timeout=_TIMEOUT,
            )
            return self._build_exec_output(
                captured_out.getvalue()[:_MAX_OUTPUT],
                captured_err.getvalue()[:_MAX_OUTPUT],
            )
        except asyncio.TimeoutError:
            return t("code_exec.timeout", seconds=_TIMEOUT)
        except Exception as e:
            return self._exec_error_response(e)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr


__all__ = ["CodeExecutionHandler"]
