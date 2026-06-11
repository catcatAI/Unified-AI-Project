# =============================================================================
# ANGELA-MATRIX: L6[执行层] β [A] L3+
# =============================================================================
#
# 职责: 代码理解代理，包括代码分析、文档生成、代码审查和修复
# 维度: 涉及认知维度 (β) 的逻辑分析和结构理解
# 安全: 使用 Key A (后端控制) 进行代码安全和隐私保护
# 成熟度: L3+ 等级可以进行复杂的代码理解任务
#
# 能力:
# - analyze_code: 代码分析
# - generate_documentation: 文档生成
# - code_review: 代码审查
# - fix_code: 代码修复
# - explain_code: 代码解释
#
# =============================================================================

import ast
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CodeUnderstandingAgent:
    """Agent for code analysis, review, and explanation."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        logger.info(f"CodeUnderstandingAgent initialized with config: {self.config}")

    def analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """Analyze code and return line_count, language, has_syntax_errors, structure."""
        if not code:
            return {"status": "error", "message": "No code provided", "line_count": 0, "language": language, "has_syntax_errors": False, "structure": {}}
        lines = code.splitlines()
        line_count = len(lines)
        has_syntax_errors = False
        try:
            ast.parse(code)
        except SyntaxError:
            has_syntax_errors = True
        structure = {
            "total_lines": line_count,
            "blank_lines": sum(1 for l in lines if l.strip() == ""),
            "comment_lines": sum(1 for l in lines if l.strip().startswith("#")),
            "code_lines": sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
        }
        logger.info(f"analyze_code: {line_count} lines, language={language}, syntax_errors={has_syntax_errors}")
        return {
            "status": "success",
            "message": f"Analyzed {line_count} lines of {language} code",
            "line_count": line_count,
            "language": language,
            "has_syntax_errors": has_syntax_errors,
            "structure": structure,
        }

    def code_review(self, code: str, language: str) -> Dict[str, Any]:
        """Review code and return issues and suggestions."""
        if not code:
            return {"status": "error", "message": "No code provided", "issues": [], "suggestions": []}
        lines = code.splitlines()
        issues = []
        suggestions = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if len(line) > 100:
                issues.append(f"Line {i}: Line too long ({len(line)} chars, max 100)")
                suggestions.append(f"Line {i}: Consider breaking this line into smaller parts")
            if stripped.endswith(" ") or stripped.endswith("\t"):
                issues.append(f"Line {i}: Trailing whitespace detected")
                suggestions.append(f"Line {i}: Remove trailing whitespace")
            if "\t" in line:
                issues.append(f"Line {i}: Tab character detected")
                suggestions.append(f"Line {i}: Replace tabs with spaces")
        logger.info(f"code_review: {len(issues)} issues found in {language} code")
        return {
            "status": "success",
            "message": f"Reviewed {len(lines)} lines of {language} code, found {len(issues)} issues",
            "issues": issues,
            "suggestions": suggestions,
        }

    def explain_code(self, code: str) -> Dict[str, Any]:
        """Explain code purpose and complexity estimate."""
        if not code:
            return {"status": "error", "message": "No code provided", "purpose": "", "complexity_estimate": ""}
        lines = code.splitlines()
        line_count = len(lines)
        try:
            tree = ast.parse(code)
            node_count = sum(1 for _ in ast.walk(tree))
        except SyntaxError:
            node_count = 0
        if node_count < 5:
            complexity = "Low"
        elif node_count < 20:
            complexity = "Medium"
        else:
            complexity = "High"
        logger.info(f"explain_code: {line_count} lines, complexity={complexity}")
        return {
            "status": "success",
            "message": f"Explained code with {line_count} lines",
            "purpose": f"Code block with {line_count} lines and {node_count} AST nodes",
            "complexity_estimate": complexity,
        }

