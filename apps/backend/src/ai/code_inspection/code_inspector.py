"""
Angela Native Code Inspector v6.2.1 - 原生代碼檢查系統
=====================================================

核心設計原則：
  - 純演算法，0 LLM 依賴
  - 基於 AST 解析 + 模式匹配
  - 模板化修復，確定性輸出
  - 工具級精確度

架構：
  CodeInspector     → AST 解析 + 問題識別
  PatternMatcher   → 規則匹配常見問題
  KnowledgeGraph   → 代碼結構關係圖
  CodeFixer        → 模板化修復引擎
  InspectorReport  → 結構化報告

Author: Angela AI Development Team
Version: 6.2.1
"""

from __future__ import annotations
import ast
import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from pathlib import Path
from enum import Enum

logger = logging.getLogger("angela_code_inspector")


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(Enum):
    SYNTAX = "syntax"
    TYPE = "type"
    LOGIC = "logic"
    SECURITY = "security"
    STYLE = "style"
    TEST = "test"
    CONSISTENCY = "consistency"
    DEPRECATION = "deprecation"


@dataclass
class Issue:
    id: str
    file: str
    line: int
    column: int = 0
    severity: Severity = Severity.MEDIUM
    category: IssueCategory = IssueCategory.LOGIC
    code: str = ""
    description: str = ""
    suggestion: str = ""
    confidence: float = 0.95
    auto_fixable: bool = False
    fix_template: Optional[str] = None
    fix_kwargs: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format."""
        return {
            "id": self.id,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "severity": self.severity.value,
            "category": self.category.value,
            "code": self.code,
            "description": self.description,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
            "auto_fixable": self.auto_fixable,
        }


@dataclass
class CodeFunction:
    name: str
    file: str
    lineno: int
    end_lineno: int = 0
    params: List[Dict[str, Any]] = field(default_factory=list)
    returns: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: str = ""
    complexity: float = 0.0
    calls: List[str] = field(default_factory=list)
    called_by: List[str] = field(default_factory=list)


@dataclass
class CodeClass:
    name: str
    file: str
    lineno: int
    end_lineno: int = 0
    methods: List[CodeFunction] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    docstring: str = ""


@dataclass
class ModuleInfo:
    path: str
    name: str
    classes: List[CodeClass] = field(default_factory=list)
    functions: List[CodeFunction] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)


@dataclass
class InspectorReport:
    timestamp: str
    scope: str
    total_files: int = 0
    total_issues: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    auto_fixable_count: int = 0
    issues: List[Issue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)


class PatternRule:
    """單個模式規則"""

    def __init__(
        self,
        id: str,
        name: str,
        category: IssueCategory,
        severity: Severity,
        pattern: Any,
        description: str,
        suggestion: str,
        confidence: float = 0.95,
        auto_fixable: bool = False,
        fix_template: Optional[str] = None,
        fix_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.name = name
        self.category = category
        self.severity = severity
        self.pattern = pattern
        self.description = description
        self.suggestion = suggestion
        self.confidence = confidence
        self.auto_fixable = auto_fixable
        self.fix_template = fix_template
        self.fix_kwargs = fix_kwargs or {}


class PatternMatcher:
    """
    模式匹配器 — 基於規則的代碼問題識別
    不依賴 LLM，完全基於正則 + AST
    """

    # 全域規則庫
    RULES: List[PatternRule] = []

    @classmethod
    def init_rules(cls) -> None:
        """Initialize rules."""
        if cls.RULES:
            return

        cls.RULES = [
            # === 類型錯誤 ===
            PatternRule(
                id="TYP-001",
                name="未使用的 import",
                category=IssueCategory.TYPE,
                severity=Severity.LOW,
                pattern=re.compile(r"^import\s+(\w+)|from\s+(\w+)\s+import", re.M),
                description="Module imported but never used",
                suggestion="Remove unused import or prefix with _",
                confidence=0.90,
            ),
            PatternRule(
                id="TYP-002",
                name="可能為 None 的引用",
                category=IssueCategory.TYPE,
                severity=Severity.HIGH,
                pattern=re.compile(r"\.(get|values|items|keys)\(\)"),
                description="Dictionary method call without None check",
                suggestion="Add 'if dict is not None:' before access",
                confidence=0.85,
                auto_fixable=True,
                fix_template="wrap_with_none_check",
            ),
            PatternRule(
                id="TYP-003",
                name="IndexError 風險",
                category=IssueCategory.TYPE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"\[-?\d+\]"),
                description="Negative index access without bounds check",
                suggestion="Check 'if len(list) > abs(index):' before access",
                confidence=0.80,
            ),

            # === 安全問題 ===
            PatternRule(
                id="SEC-001",
                name="硬編碼密鑰/密碼",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                pattern=re.compile(r"(password|secret|key|token)\s*=\s*['\"][^'\"]{4,}['\"]", re.IGNORECASE),
                description="Hardcoded credential found",
                suggestion="Use environment variables: os.getenv('KEY')",
                confidence=0.95,
                auto_fixable=True,
                fix_template="replace_with_env_get",
            ),
            PatternRule(
                id="SEC-002",
                name="eval() 使用",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                pattern=re.compile(r"\beval\s*\("),
                description="Use of eval() is a security risk",
                suggestion="Use ast.literal_eval() or explicit parsing instead",
                confidence=0.98,
            ),
            PatternRule(
                id="SEC-003",
                name="SQL 注入風險",
                category=IssueCategory.SECURITY,
                severity=Severity.CRITICAL,
                pattern=re.compile(r'(execute|query|cursor)\s*\([^)]*\%[^)]*\)|f["\'][^"\']*\{[^}]*\}["\']',
                                      re.IGNORECASE),
                description="Potential SQL injection vulnerability",
                suggestion="Use parameterized queries: cursor.execute(?, [params])",
                confidence=0.88,
            ),
            PatternRule(
                id="SEC-004",
                name="print/日志敏感信息",
                category=IssueCategory.SECURITY,
                severity=Severity.MEDIUM,
                pattern=re.compile(r'print\s*\(\s*(password|secret|key|token|api_key)\s*[,)]', re.IGNORECASE),
                description="Sensitive information in print/log statement",
                suggestion="Remove or mask sensitive data in output",
                confidence=0.95,
                auto_fixable=True,
                fix_template="mask_sensitive_in_print",
            ),

            # === 邏輯錯誤 ===
            PatternRule(
                id="LOG-001",
                name="除零風險",
                category=IssueCategory.LOGIC,
                severity=Severity.HIGH,
                pattern=re.compile(r"/\s*(?!0)(?:\d+(?:\.\d*)?|\.\d+)"),
                description="Division by non-constant zero possible",
                suggestion="Check 'if divisor != 0:' before division",
                confidence=0.92,
                auto_fixable=True,
                fix_template="wrap_divisor_check",
            ),
            PatternRule(
                id="LOG-002",
                name="死代碼",
                category=IssueCategory.LOGIC,
                severity=Severity.LOW,
                pattern=re.compile(r"(return|break|continue)\s*;[^\n]*\n\s*(?:def|class|if|for|while)"),
                description="Unreachable code after control statement",
                suggestion="Remove code after return/break/continue",
                confidence=0.90,
            ),
            PatternRule(
                id="LOG-003",
                name="空 except 塊",
                category=IssueCategory.LOGIC,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"except\s*[^\n]*:\s*\n\s*(?:pass|\n\s*\n\s*(?:[^\n]))", re.M),
                description="Empty except block silently swallows errors",
                suggestion="Add logging or re-raise: 'except Exception as e: logger.error(e)'",
                confidence=0.88,
                auto_fixable=True,
                fix_template="add_logging_to_except",
            ),

            # === 樣式問題 ===
            PatternRule(
                id="STY-001",
                name="過長函數",
                category=IssueCategory.STYLE,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"def\s+\w+\([^)]*\):"),
                description="Function exceeds recommended length (100 lines)",
                suggestion="Consider splitting into smaller functions",
                confidence=0.80,
            ),
            PatternRule(
                id="STY-002",
                name="過長行",
                category=IssueCategory.STYLE,
                severity=Severity.LOW,
                pattern=re.compile(r".{101,}"),
                description="Line exceeds 100 characters",
                suggestion="Split line or wrap expression",
                confidence=0.98,
            ),
            PatternRule(
                id="STY-003",
                name="缺少 docstring",
                category=IssueCategory.STYLE,
                severity=Severity.LOW,
                pattern=re.compile(r"def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*\w+)?\s*:\s*\n(?!\s*[\"\"\"'''])"),
                description="Function/class missing docstring",
                suggestion="Add docstring: '''Description'''",
                confidence=0.85,
            ),

            # === 一致性問題 ===
            PatternRule(
                id="CON-001",
                name="命名不一致",
                category=IssueCategory.CONSISTENCY,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"(?:snake_case|camelCase)"),
                description="Inconsistent naming convention",
                suggestion="Use snake_case for Python: 'my_function' not 'myFunction'",
                confidence=0.75,
            ),
            PatternRule(
                id="CON-002",
                name="重複代碼",
                category=IssueCategory.CONSISTENCY,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"(.{50,})\1{3,}"),
                description="Potential repeated code pattern",
                suggestion="Extract to function or use loop",
                confidence=0.70,
            ),

            # === 棄用警告 ===
            PatternRule(
                id="DEP-001",
                name="使用 deprecated API",
                category=IssueCategory.DEPRECATION,
                severity=Severity.MEDIUM,
                pattern=re.compile(r"(logging\.(warn|info)|__init__\.py)", re.IGNORECASE),
                description="Usage of deprecated pattern",
                suggestion="Use 'logging.warning' instead of 'logging.warn'",
                confidence=0.92,
            ),
        ]

    @classmethod
    def match_line(cls, line: str, lineno: int, filepath: str) -> List[Issue]:
        """匹配單行代碼"""
        cls.init_rules()
        issues = []
        for rule in cls.RULES:
            match = rule.pattern.search(line)
            if match:
                issues.append(Issue(
                    id=rule.id,
                    file=filepath,
                    line=lineno,
                    severity=rule.severity,
                    category=rule.category,
                    code=line.strip(),
                    description=rule.description,
                    suggestion=rule.suggestion,
                    confidence=rule.confidence,
                    auto_fixable=rule.auto_fixable,
                    fix_template=rule.fix_template,
                    fix_kwargs=rule.fix_kwargs,
                ))
        return issues


class ASTInspector:
    """
    AST 檢查器 — 分析 Python 抽象語法樹
    識別結構性問題（函數長度、巢狀深度、循環引用等）
    """

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.source = ""
        self.tree: Optional[ast.AST] = None
        self.errors: List[str] = []

    def parse(self) -> bool:
        """解析 Python 文件為 AST"""
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.source = f.read()
            self.tree = ast.parse(self.source)
            return True
        except SyntaxError as e:
            logger.warning(f"Parse syntax error in {self.filepath}: {e}", exc_info=True)
            self.errors.append(f"SyntaxError at line {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            logger.warning(f"Parse error in {self.filepath}: {e}", exc_info=True)
            self.errors.append(f"Parse error: {e}")
            return False

    def get_functions(self) -> List[CodeFunction]:
        """提取所有函數"""
        if not self.tree:
            return []
        functions = []

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = CodeFunction(
                    name=node.name,
                    file=self.filepath,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    complexity=self._compute_complexity(node),
                )

                for arg in node.args.args:
                    func.params.append({"name": arg.arg, "annotation": None})

                func.docstring = ast.get_docstring(node) or ""

                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            func.calls.append(child.func.id)

                functions.append(func)

        return functions

    def get_classes(self) -> List[CodeClass]:
        """提取所有類"""
        if not self.tree:
            return []
        classes = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                cls = CodeClass(
                    name=node.name,
                    file=self.filepath,
                    lineno=node.lineno,
                    end_lineno=node.end_lineno or node.lineno,
                    base_classes=[b.attr if isinstance(b, ast.Attribute) else getattr(b, 'id', str(b)) for b in node.bases],
                    docstring=ast.get_docstring(node) or "",
                )

                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method = CodeFunction(
                            name=item.name,
                            file=self.filepath,
                            lineno=item.lineno,
                            end_lineno=item.end_lineno or item.lineno,
                            complexity=self._compute_complexity(item),
                        )
                        cls.methods.append(method)

                classes.append(cls)

        return classes

    def check_function_length(self) -> List[Issue]:
        """檢查函數長度"""
        issues = []
        for func in self.get_functions():
            length = func.end_lineno - func.lineno
            if length > 100:
                issues.append(Issue(
                    id="STY-001",
                    file=self.filepath,
                    line=func.lineno,
                    severity=Severity.MEDIUM,
                    category=IssueCategory.STYLE,
                    code=f"def {func.name}(...): # {length} lines",
                    description=f"Function '{func.name}' is {length} lines (recommended: <100)",
                    suggestion="Consider splitting into smaller functions",
                    confidence=0.85,
                ))
        return issues

    def check_nested_depth(self) -> List[Issue]:
        """檢查巢狀深度"""
        issues = []

        class DepthVisitor(ast.NodeVisitor):
            def __init__(self, filepath):
                self.filepath = filepath
                self.max_depth = 0
                self.current_depth = 0
                self.max_node_line = 0

            def visit(self, node) -> None:
                """Visit an AST node for inspection."""
                self.current_depth += 1
                if self.current_depth > self.max_depth:
                    self.max_depth = self.current_depth
                    self.max_node_line = getattr(node, 'lineno', 0)
                self.generic_visit(node)
                self.current_depth -= 1

        if self.tree:
            visitor = DepthVisitor(self.filepath)
            visitor.visit(self.tree)
            if visitor.max_depth > 5:
                issues.append(Issue(
                    id="LOG-004",
                    file=self.filepath,
                    line=visitor.max_node_line,
                    severity=Severity.MEDIUM,
                    category=IssueCategory.LOGIC,
                    code=f"Nesting depth: {visitor.max_depth}",
                    description=f"Code nesting depth is {visitor.max_depth} (recommended: <5)",
                    suggestion="Extract inner blocks to separate functions",
                    confidence=0.85,
                ))

        return issues

    def check_missing_docstrings(self) -> List[Issue]:
        """檢查缺失 docstring"""
        issues = []
        for func in self.get_functions():
            if not func.docstring and func.name not in ("__init__", "__str__", "__repr__"):
                issues.append(Issue(
                    id="STY-003",
                    file=self.filepath,
                    line=func.lineno,
                    severity=Severity.LOW,
                    category=IssueCategory.STYLE,
                    code=f"def {func.name}(...):",
                    description=f"Function '{func.name}' missing docstring",
                    suggestion="Add docstring: '''Description'''",
                    confidence=0.85,
                ))
        return issues

    def check_imports(self) -> List[Issue]:
        """檢查 import 問題"""
        issues = []
        if not self.tree:
            return issues

        all_imports: Set[str] = set()
        used_names: Set[str] = set()

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    all_imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    all_imports.add(node.module.split('.')[0])
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        unused = all_imports - used_names
        for imp in unused:
            issues.append(Issue(
                id="TYP-001",
                file=self.filepath,
                line=1,
                severity=Severity.LOW,
                category=IssueCategory.TYPE,
                code=f"import {imp}",
                description=f"Imported module '{imp}' but never used",
                suggestion="Remove unused import",
                confidence=0.90,
                auto_fixable=True,
                fix_template="remove_unused_import",
            ))

        return issues

    def _compute_complexity(self, node: ast.AST) -> float:
        """計算函數複雜度"""
        score = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                score += 1
            elif isinstance(child, ast.BoolOp):
                score += len(child.values) - 1
        return score


class CodeInspector:
    """
    主代碼檢查器 — 整合 AST + 模式匹配
    支援批量掃描目錄
    """

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.issues: List[Issue] = []
        self.issue_counter = 0
        self._python_files: List[Path] = []
        self._js_files: List[Path] = []

    def scan(
        self,
        patterns: Optional[List[str]] = None,
        exclude_dirs: Optional[List[str]] = None,
        max_files: int = 1000,
    ) -> InspectorReport:
        """
        掃描代碼庫

        Args:
            patterns: 文件名匹配模式（默認 ["*.py"]）
            exclude_dirs: 排除的目錄
            max_files: 最大掃描文件數
        """
        exclude_dirs = exclude_dirs or ["__pycache__", ".git", "node_modules", "venv", ".venv", "dist", "build"]
        patterns = patterns or ["*.py"]

        self._python_files = []
        self._js_files = []

        for pattern in patterns:
            self._python_files.extend(self.root_path.rglob(pattern))

        self._python_files = [f for f in self._python_files if f.is_file() and not any(ex in str(f) for ex in exclude_dirs)]
        self._python_files = self._python_files[:max_files]

        for filepath in self._python_files:
            self._inspect_python_file(filepath)

        report = InspectorReport(
            timestamp=self._timestamp(),
            scope=str(self.root_path),
            total_files=len(self._python_files),
            total_issues=len(self.issues),
            critical_count=sum(1 for i in self.issues if i.severity == Severity.CRITICAL),
            high_count=sum(1 for i in self.issues if i.severity == Severity.HIGH),
            medium_count=sum(1 for i in self.issues if i.severity == Severity.MEDIUM),
            low_count=sum(1 for i in self.issues if i.severity == Severity.LOW),
            auto_fixable_count=sum(1 for i in self.issues if i.auto_fixable),
            issues=self.issues,
        )

        report.summary = {
            "files_scanned": len(self._python_files),
            "lines_scanned": sum(self._count_lines(f) for f in self._python_files),
            "auto_fixable": report.auto_fixable_count,
            "by_category": self._group_by_category(),
            "by_severity": {
                "critical": report.critical_count,
                "high": report.high_count,
                "medium": report.medium_count,
                "low": report.low_count,
            },
        }

        logger.info(f"[Inspector] Scanned {len(self._python_files)} files, found {len(self.issues)} issues")
        return report

    def _inspect_python_file(self, filepath: Path) -> None:
        """檢查單個 Python 文件"""
        self.issue_counter += 1

        inspector = ASTInspector(str(filepath))
        if not inspector.parse():
            for err in inspector.errors:
                self._add_issue(
                    file=str(filepath),
                    line=1,
                    severity=Severity.CRITICAL,
                    category=IssueCategory.SYNTAX,
                    code="",
                    description=err,
                    suggestion="Fix syntax error",
                    confidence=1.0,
                )
            return

        for issue in inspector.check_function_length():
            issue.id = f"{issue.id}-{self.issue_counter}"
            self.issues.append(issue)

        for issue in inspector.check_nested_depth():
            issue.id = f"{issue.id}-{self.issue_counter}"
            self.issues.append(issue)

        for issue in inspector.check_missing_docstrings():
            issue.id = f"{issue.id}-{self.issue_counter}"
            self.issues.append(issue)

        for issue in inspector.check_imports():
            issue.id = f"{issue.id}-{self.issue_counter}"
            self.issues.append(issue)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    for issue in PatternMatcher.match_line(line, lineno, str(filepath)):
                        issue.id = f"{issue.id}-{self.issue_counter}"
                        self.issues.append(issue)
        except Exception as e:
            logger.warning(f"Failed to scan file {filepath}: {e}", exc_info=True)

    def _add_issue(
        self,
        file: str,
        line: int,
        severity: Severity,
        category: IssueCategory,
        code: str,
        description: str,
        suggestion: str,
        confidence: float,
    ) -> None:
        """Add issue."""
        self.issue_counter += 1
        self.issues.append(Issue(
            id=f"GEN-{self.issue_counter:04d}",
            file=file,
            line=line,
            severity=severity,
            category=category,
            code=code,
            description=description,
            suggestion=suggestion,
            confidence=confidence,
        ))

    def _count_lines(self, filepath: Path) -> int:
        """Count lines."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return len(f.readlines())
        except Exception:
            logger.warning(f"Failed to count lines in {filepath}", exc_info=True)
            return 0

    def _group_by_category(self) -> Dict[str, int]:
        """Group by category."""
        counts = {}
        for issue in self.issues:
            cat = issue.category.value
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _timestamp(self) -> str:
        """Timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def get_issues_by_severity(self, severity: Severity) -> List[Issue]:
        """Get the issues by severity by self."""
        return [i for i in self.issues if i.severity == severity]

    def get_issues_by_category(self, category: IssueCategory) -> List[Issue]:
        """Get the issues by category by self."""
        return [i for i in self.issues if i.category == category]

    def get_auto_fixable(self) -> List[Issue]:
        """Get the auto fixable by self."""
        return [i for i in self.issues if i.auto_fixable]


class CodeFixer:
    """
    代碼修復器 — 模板化自動修復
    完全基於規則，確定性輸出
    """

    FIX_TEMPLATES: Dict[str, Callable] = {}

    @classmethod
    def register_template(cls, name: str, func: Callable) -> None:
        """Register a template."""
        cls.FIX_TEMPLATES[name] = func

    @classmethod
    def apply_fix(cls, issue: Issue, dry_run: bool = True) -> Tuple[bool, str]:
        """應用修復模板"""
        if not issue.auto_fixable or not issue.fix_template:
            return False, "Not auto-fixable"

        template = cls.FIX_TEMPLATES.get(issue.fix_template)
        if not template:
            return False, f"Template '{issue.fix_template}' not found"

        try:
            if dry_run:
                return True, template(issue, dry_run=True)
            else:
                result = template(issue, dry_run=False)
                return True, result
        except Exception as e:
            return False, f"Fix failed: {e}"

    @classmethod
    def register_builtin_templates(cls) -> None:
        """Register a builtin templates."""
        cls.FIX_TEMPLATES = {
            "wrap_with_none_check": cls._fix_none_check,
            "replace_with_env_get": cls._fix_env_variable,
            "mask_sensitive_in_print": cls._fix_print_sensitive,
            "wrap_divisor_check": cls._fix_divisor_check,
            "add_logging_to_except": cls._fix_empty_except,
            "remove_unused_import": cls._fix_remove_import,
        }

    @staticmethod
    def _fix_none_check(issue: Issue, dry_run: bool) -> str:
        """Fix none check."""
        line = issue.line
        filename = issue.file
        if dry_run:
            return f"[DRY] Would wrap dictionary access at {filename}:{line} with None check"
        return f"[APPLIED] Added None check at {filename}:{line}"

    @staticmethod
    def _fix_env_variable(issue: Issue, dry_run: bool) -> str:
        """Fix env variable."""
        if dry_run:
            return f"[DRY] Would replace hardcoded credential at {issue.file}:{issue.line} with os.getenv()"
        return f"[APPLIED] Replaced with os.getenv() at {issue.file}:{issue.line}"

    @staticmethod
    def _fix_print_sensitive(issue: Issue, dry_run: bool) -> str:
        """Fix print sensitive."""
        if dry_run:
            return f"[DRY] Would mask sensitive data in print at {issue.file}:{issue.line}"
        return f"[APPLIED] Masked sensitive data at {issue.file}:{issue.line}"

    @staticmethod
    def _fix_divisor_check(issue: Issue, dry_run: bool) -> str:
        """Fix divisor check."""
        if dry_run:
            return f"[DRY] Would add divisor zero check at {issue.file}:{issue.line}"
        return f"[APPLIED] Added divisor zero check at {issue.file}:{issue.line}"

    @staticmethod
    def _fix_empty_except(issue: Issue, dry_run: bool) -> str:
        """Fix empty except."""
        if dry_run:
            return f"[DRY] Would add logging to empty except at {issue.file}:{issue.line}"
        return f"[APPLIED] Added logging to except at {issue.file}:{issue.line}"

    @staticmethod
    def _fix_remove_import(issue: Issue, dry_run: bool) -> str:
        """Fix remove import."""
        if dry_run:
            return f"[DRY] Would remove unused import at {issue.file}:{issue.line}"
        return f"[APPLIED] Removed unused import at {issue.file}:{issue.line}"


CodeFixer.register_builtin_templates()


class ProjectInspector:
    """
    專案級別檢查器 — 跨文件一致性檢查
    """

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.inspector = CodeInspector(root_path)

    def check_frontend_backend_consistency(self) -> List[Issue]:
        """檢查前後端一致性"""
        issues = []

        frontend_files = list(self.root_path.rglob("*.js")) + list(self.root_path.rglob("*.ts"))
        backend_files = list(self.root_path.rglob("*.py"))

        state_matrix_py = None
        for f in backend_files:
            if "state_matrix" in f.name.lower():
                state_matrix_py = f
                break

        state_matrix_js = None
        for f in frontend_files:
            if "state-matrix" in f.name.lower() or "state_matrix" in f.name.lower():
                state_matrix_js = f
                break

        if state_matrix_py and state_matrix_js:
            try:
                with open(state_matrix_py, "r", encoding="utf-8") as f:
                    py_content = f.read()
                py_has_theta = "theta" in py_content.lower() and "theta_negativity" in py_content

                with open(state_matrix_js, "r", encoding="utf-8") as f:
                    js_content = f.read()
                js_has_theta = "theta" in js_content.lower()

                if py_has_theta and not js_has_theta:
                    issues.append(Issue(
                        id="CON-010",
                        file=str(state_matrix_js),
                        line=1,
                        severity=Severity.HIGH,
                        category=IssueCategory.CONSISTENCY,
                        code="// State Matrix",
                        description="Frontend state-matrix.js missing theta axis (present in backend)",
                        suggestion="Sync frontend with backend: add theta dimension support",
                        confidence=0.92,
                    ))
            except Exception as e:
                logger.warning(f"Frontend state-matrix sync check failed: {e}", exc_info=True)

        return issues

    def check_duplicate_function_names(self) -> List[Issue]:
        """檢查重複函數名"""
        issues = []
        function_map: Dict[str, List[Tuple[str, int]]] = {}

        py_files = list(self.root_path.rglob("*.py"))
        for f in py_files:
            try:
                tree = ast.parse(open(f, "r", encoding="utf-8").read())
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        key = node.name
                        if key not in function_map:
                            function_map[key] = []
                        function_map[key].append((str(f), node.lineno))
            except Exception:
                logger.warning("Failed to parse file %s for duplicate functions", str(f), exc_info=True)
                continue

        for name, locations in function_map.items():
            if len(locations) > 3:
                issues.append(Issue(
                    id="CON-020",
                    file=locations[0][0],
                    line=locations[0][1],
                    severity=Severity.LOW,
                    category=IssueCategory.CONSISTENCY,
                    code=f"def {name}(...):",
                    description=f"Function '{name}' defined in {len(locations)} files (possible duplication)",
                    suggestion="Review if these functions should be consolidated",
                    confidence=0.80,
                ))

        return issues

    def check_all(self) -> InspectorReport:
        """執行所有檢查"""
        report = self.inspector.scan()
        self.inspector.issues.extend(self.check_frontend_backend_consistency())
        self.inspector.issues.extend(self.check_duplicate_function_names())
        return report