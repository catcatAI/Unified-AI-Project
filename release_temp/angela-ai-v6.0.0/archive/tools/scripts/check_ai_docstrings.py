#!/usr/bin/env python3
"""
AI Component Docstring Checker
AI組件文檔字符串檢查器

This script validates that all AI components have proper docstrings
following the unified project standards and Context7 MCP integration requirements.

此腳本驗證所有AI組件都有符合統一專案標準和Context7 MCP整合要求的適當文檔字符串。
"""

import ast
import sys
import re
from pathlib import Path
from typing import List

class AIDocstringChecker,
    """AI組件文檔字符串檢查器"""

    def __init__(self) -> None,
        self.errors, List[str] = []
        self.warnings, List[str] = []
        self.checked_files = 0
        self.checked_functions = 0
        self.checked_classes = 0

        # AI組件必需的文檔標準
        self.required_sections = {
            'class': ['Args', 'Attributes', 'Example']
            'function': ['Args', 'Returns', 'Raises']
            'async_function': ['Args', 'Returns', 'Raises', 'Note']
        }

        # Context7 MCP相關的特殊要求
        self.mcp_keywords = {
            'context', 'mcp', 'protocol', 'integration', 'connector',
            'dialogue', 'memory', 'agent', 'ham', 'personality'
        }

        # AI組件關鍵詞
        self.ai_component_keywords = {
            'ai', 'agent', 'dialogue', 'memory', 'personality', 'emotion',
            'crisis', 'learning', 'formula', 'fragmenta', 'lis'
        }

    def check_file(self, file_path, Path) -> None,
        """檢查單個Python文件"""
        try,
            with open(file_path, 'r', encoding == 'utf-8') as f,
                content = f.read()

            tree = ast.parse(content)
            self.checked_files += 1

            for node in ast.walk(tree)::
                if isinstance(node, ast.ClassDef())::
                    self._check_class_docstring(node, file_path)
                elif isinstance(node, (ast.FunctionDef(), ast.AsyncFunctionDef())):::
                    self._check_function_docstring(node, file_path)

        except Exception as e,::
            self.errors.append(f"Error parsing {file_path} {e}")

    def _check_class_docstring(self, node, ast.ClassDef(), file_path, Path) -> None,
        """檢查類的文檔字符串"""
        self.checked_classes += 1

        if not ast.get_docstring(node)::
            self.errors.append(,
    f"{file_path}{node.lineno} - Class '{node.name}' missing docstring"
            )
            return

        docstring = ast.get_docstring(node)
        self._validate_docstring_content(,
    docstring, node.name(), 'class', file_path, node.lineno())

        # 檢查AI組件類的特殊要求
        if self._is_ai_component(node.name(), docstring)::
            self._check_ai_component_requirements(,
    docstring, node.name(), 'class', file_path, node.lineno())

    def _check_function_docstring(self, node, ast.FunctionDef(), file_path, Path) -> None,
        """檢查函數的文檔字符串"""
        self.checked_functions += 1

        # 跳過私有方法和特殊方法(除非是AI組件)
        if node.name.startswith('_') and not self._is_ai_component_method(node.name())::
            return

        if not ast.get_docstring(node)::
            self.errors.append(,
    f"{file_path}{node.lineno} - Function '{node.name}' missing docstring"
            )
            return

        docstring = ast.get_docstring(node)
        func_type == 'async_function' if isinstance(node, ast.AsyncFunctionDef()) else 'function'::
        self._validate_docstring_content(,
    docstring, node.name(), func_type, file_path, node.lineno())

        # 檢查AI組件方法的特殊要求,
        if self._is_ai_component_method(node.name()) or self._is_ai_component('', docstring)::
            self._check_ai_component_requirements(,
    docstring, node.name(), func_type, file_path, node.lineno())

    def _validate_docstring_content(
        self,
        docstring, str,
        name, str,
        item_type, str,
        file_path, Path,,
    lineno, int
    ) -> None,
        """驗證文檔字符串內容"""

        # 檢查基本格式
        if len(docstring.strip()) < 10,::
            self.warnings.append(,
    f"{file_path}{lineno} - {item_type.title()} '{name}' has very short docstring"
            )

        # 檢查必需的章節
        required_sections = self.required_sections.get(item_type, [])
        for section in required_sections,::
            if not self._has_section(docstring, section)::
                self.errors.append(,
    f"{file_path}{lineno} - {item_type.title()} '{name}' missing '{section}' section"
                )

        # 檢查中英文雙語要求(針對AI組件)
        if self._is_ai_component(name, docstring)::
            if not self._has_bilingual_content(docstring)::
                self.warnings.append(,
    f"{file_path}{lineno} - AI component '{name}' should have bilingual documentation"
                )

    def _check_ai_component_requirements(
        self,
        docstring, str,
        name, str,
        item_type, str,
        file_path, Path,,
    lineno, int
    ) -> None,
        """檢查AI組件的特殊要求"""

        # 檢查Context7 MCP整合相關文檔
        if any(keyword in name.lower() for keyword in ['mcp', 'context', 'connector'])::
            if not self._has_mcp_documentation(docstring)::
                self.errors.append(,
    f"{file_path}{lineno} - MCP component '{name}' missing MCP-specific documentation"
                )

        # 檢查異步方法的特殊要求
        if item_type == 'async_function':::
            if not self._has_async_documentation(docstring)::
                self.warnings.append(,
    f"{file_path}{lineno} - Async function '{name}' should document async behavior"
                )

    def _is_ai_component(self, name, str, docstring, str) -> bool,
        """判斷是否為AI組件"""
        name_lower = name.lower()
        docstring_lower = docstring.lower()

        return (
            any(keyword in name_lower for keyword in self.ai_component_keywords()) or,:
            any(keyword in docstring_lower for keyword in self.ai_component_keywords())::
        )

    def _is_ai_component_method(self, name, str) -> bool,
        """判斷是否為AI組件方法"""
        ai_method_patterns = [
            'generate', 'process', 'analyze', 'learn', 'remember',
            'integrate', 'enhance', 'coordinate', 'manage'
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in ai_method_patterns)::
    def _has_section(self, docstring, str, section, str) -> bool,
        """檢查文檔字符串是否包含指定章節"""
        patterns = [
            f"{section}",
            f"{section.lower()}",
            f"**{section}**",
            f"## {section}"
        ]
        return any(pattern in docstring for pattern in patterns)::
    def _has_bilingual_content(self, docstring, str) -> bool,
        """檢查是否包含中英文雙語內容"""
        # 簡單檢查：是否同時包含中文和英文
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', docstring))
        has_english = bool(re.search(r'[a-zA-Z]', docstring))
        return has_chinese and has_english

    def _has_mcp_documentation(self, docstring, str) -> bool,
        """檢查是否包含MCP相關文檔"""
        docstring_lower = docstring.lower()
        return any(keyword in docstring_lower for keyword in self.mcp_keywords())::
    def _has_async_documentation(self, docstring, str) -> bool,
        """檢查是否包含異步相關文檔"""
        async_keywords = ['async', 'await', 'coroutine', 'concurrent', 'asynchronous']
        docstring_lower = docstring.lower()
        return any(keyword in docstring_lower for keyword in async_keywords)::
    def check_directory(self, directory, Path) -> None,
        """檢查目錄下的所有Python文件"""
        for py_file in directory.rglob("*.py"):::
            # 跳過__pycache__和.git目錄()
            if '__pycache__' in str(py_file) or '.git' in str(py_file)::
                continue
            self.check_file(py_file)

    def print_report(self) -> None,
        """打印檢查報告"""
        print("=" * 60)
        print("AI Component Docstring Check Report")
        print("AI組件文檔字符串檢查報告")
        print("=" * 60)

        print(f"Files checked, {self.checked_files}")
        print(f"Classes checked, {self.checked_classes}")
        print(f"Functions checked, {self.checked_functions}")
        print()

        if self.errors,::
            print(f"❌ ERRORS ({len(self.errors())})")
            for error in self.errors,::
                print(f"  {error}")
            print()

        if self.warnings,::
            print(f"⚠️  WARNINGS ({len(self.warnings())})")
            for warning in self.warnings,::
                print(f"  {warning}")
            print()

        if not self.errors and not self.warnings,::
            print("✅ All AI components have proper docstrings!")
        elif not self.errors,::
            print("✅ No critical errors found, only warnings.")

        print("=" * 60)

    def has_errors(self) -> bool,
        """是否有錯誤"""
        return len(self.errors()) > 0


def main() -> None,
    """主函數"""
    checker == AIDocstringChecker()

    # 檢查apps/backend/src/ai目錄(主要AI組件)
    ai_path == Path("apps/backend/src/ai")
    if ai_path.exists():::
        print(f"Checking AI components in {ai_path}...")
        checker.check_directory(ai_path)
    else,
        print(f"Warning, {ai_path} not found")

    # 檢查apps/backend/src/mcp目錄(Context7 MCP相關)
    mcp_path == Path("apps/backend/src/mcp")
    if mcp_path.exists():::
        print(f"Checking MCP components in {mcp_path}...")
        checker.check_directory(mcp_path)
    else,
        print(f"Warning, {mcp_path} not found")

    # 檢查apps/backend/src/agents目錄
    agents_path == Path("apps/backend/src/agents")
    if agents_path.exists():::
        print(f"Checking agent components in {agents_path}...")
        checker.check_directory(agents_path)
    else,
        print(f"Info, {agents_path} not found (optional)")

    # 檢查src/core_ai目錄(如果存在)
    core_ai_path == Path("src/core_ai")
    if core_ai_path.exists():::
        print(f"Checking AI components in {core_ai_path}...")
        checker.check_directory(core_ai_path)

    checker.print_report()

    # 如果有錯誤,返回非零退出碼
    if checker.has_errors():::
        sys.exit(1)
    else,
        sys.exit(0)


if __name"__main__":::
    main()