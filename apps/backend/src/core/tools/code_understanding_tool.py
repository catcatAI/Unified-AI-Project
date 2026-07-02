# ANGELA-MATRIX: L0[基础层] [A] L1

"""Code understanding tool for analyzing source code context."""

import ast
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeUnderstandingTool:
    """Analyzes source code to provide context understanding for the AI."""

    def analyze(self, file_path: str) -> Dict[str, Any]:
        """Analyze a source file and return understanding context."""
        path = Path(file_path)
        if not path.is_file():
            return {"file": file_path, "status": "not_found", "error": "File not found"}

        if path.suffix == ".py":
            return self._analyze_python(path)
        return {
            "file": str(path),
            "status": "unknown_type",
            "suffix": path.suffix,
            "size": path.stat().st_size,
        }

    def _analyze_python(self, path: Path) -> Dict[str, Any]:
        """Analyze a Python source file via AST."""
        try:
            source = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("Failed to read %s: %s", path, e, exc_info=True)
            return {"file": str(path), "status": "error", "error": str(e)}

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return {"file": str(path), "status": "syntax_error", "error": str(e)}

        classes: List[Dict[str, Any]] = []
        functions: List[Dict[str, Any]] = []
        imports: List[Dict[str, Any]] = []
        lines = source.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [
                    {
                        "name": n.name,
                        "line": n.lineno,
                        "decorators": [ast.unparse(d) for d in n.decorator_list],
                    }
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [ast.unparse(b) for b in node.bases],
                    "docstring": ast.get_docstring(node),
                    "methods": methods,
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not any(
                    isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
                    if isinstance(parent, ast.ClassDef)
                    and node in ast.walk(parent)
                ):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "docstring": ast.get_docstring(node),
                    })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", None)
                names = [alias.name for alias in node.names]
                imports.append({"module": module, "names": names, "line": node.lineno})

        return {
            "file": str(path),
            "status": "analyzed",
            "language": "python",
            "lines": len(lines),
            "size": path.stat().st_size,
            "imports": imports,
            "classes": classes,
            "functions": functions,
        }


__all__ = ["CodeUnderstandingTool"]
