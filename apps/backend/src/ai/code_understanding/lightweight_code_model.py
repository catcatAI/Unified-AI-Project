# ANGELA-MATRIX: L0[基础层] [A] L1

import ast
import os
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .code_analysis_types import CodeAnalysisResult

logger = logging.getLogger(__name__)


class LightweightCodeModel:
    """轻量级代码模型 - 用于基础语法检查和工具文件解析"""

    def __init__(self, tools_directory: str):
        self.tools_directory = tools_directory

    def list_tool_files(self) -> List[str]:
        tool_files = []
        for root, _dirs, files in os.walk(self.tools_directory):
            for file in files:
                if file.endswith(".py") and file not in ("__init__.py", "tool_dispatcher.py"):
                    tool_files.append(os.path.join(root, file))
        return tool_files

    def analyze_tool_file(self, filepath: str) -> Optional[CodeAnalysisResult]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except Exception:
            logger.exception("Failed to parse %s", filepath)
            return None

        classes = []
        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append({"name": node.name, "methods": methods})
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({"name": node.name})

        return CodeAnalysisResult(
            filepath=filepath,
            analysis_timestamp=datetime.now(),
            classes=classes,
            functions=functions,
        )

    def get_tool_structure(self, name: str) -> Optional[Any]:
        tool_files = self.list_tool_files()
        matches = [f for f in tool_files if name in os.path.basename(f)]
        exact = [f for f in matches if os.path.splitext(os.path.basename(f))[0] == name]
        if len(exact) == 1:
            return self.analyze_tool_file(exact[0])
        if len(matches) > 1:
            logger.warning("Ambiguous tool name: %s", name)
        return None
