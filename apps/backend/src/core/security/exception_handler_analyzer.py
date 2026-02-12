# =============================================================================
# ANGELA-MATRIX: 異常處理分析工具
# =============================================================================
#
# 職責: 分析和改進代碼中的異常處理
# 安全: 改善錯誤處理和日誌記錄
# 成熟度: L2+ 等級
#
# 功能:
# - 識別裸異常捕獲 (except Exception:)
# - 提供改進建議
# - 生成詳細的錯誤日誌
# - 幫助修復異常處理問題
#
# =============================================================================

import ast
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ExceptionHandlerIssue:
    """異常處理問題"""
    file_path: str
    line_number: int
    exception_type: str
    has_logging: bool
    has_context: bool
    suggestion: str
    severity: str  # 'critical', 'high', 'medium', 'low'


@dataclass
class FileAnalysisResult:
    """文件分析結果"""
    file_path: str
    total_except_blocks: int
    bare_exception_blocks: int
    issues: List[ExceptionHandlerIssue] = field(default_factory=list)


class ExceptionHandlerAnalyzer:
    """異常處理分析器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results: List[FileAnalysisResult] = []
        self.total_files = 0
        self.total_issues = 0

    def analyze_file(self, file_path: Path) -> FileAnalysisResult:
        """
        分析單個文件

        Args:
            file_path: 文件路徑

        Returns:
            FileAnalysisResult: 分析結果
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"無法讀取文件 {file_path}: {e}")
            return FileAnalysisResult(str(file_path), 0, 0)

        # 使用 AST 解析
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"文件 {file_path} 語法錯誤: {e}")
            return FileAnalysisResult(str(file_path), 0, 0)

        result = FileAnalysisResult(str(file_path), 0, 0)
        visitor = ExceptionVisitor(str(file_path), content)
        visitor.visit(tree)

        result.total_except_blocks = visitor.total_except_blocks
        result.bare_exception_blocks = visitor.bare_exception_blocks
        result.issues = visitor.issues

        return result

    def analyze_directory(self, directory: str, pattern: str = "*.py") -> None:
        """
        分析目錄中的所有 Python 文件

        Args:
            directory: 目錄路徑
            pattern: 文件匹配模式
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            logger.error(f"目錄不存在: {directory}")
            return

        python_files = list(dir_path.rglob(pattern))
        self.total_files = len(python_files)

        logger.info(f"開始分析 {self.total_files} 個 Python 文件...")

        for file_path in python_files:
            result = self.analyze_file(file_path)
            self.results.append(result)
            self.total_issues += len(result.issues)

        logger.info(f"分析完成，共發現 {self.total_issues} 個問題")

    def get_critical_issues(self) -> List[ExceptionHandlerIssue]:
        """獲取所有嚴重問題"""
        issues = []
        for result in self.results:
            issues.extend([i for i in result.issues if i.severity == 'critical'])
        return issues

    def get_high_issues(self) -> List[ExceptionHandlerIssue]:
        """獲取所有高優先級問題"""
        issues = []
        for result in self.results:
            issues.extend([i for i in result.issues if i.severity == 'high'])
        return issues

    def print_summary(self) -> None:
        """打印分析摘要"""
        print("\n" + "="*80)
        print("ANGELA 異常處理分析報告")
        print("="*80 + "\n")

        print(f"分析文件數: {self.total_files}")
        print(f"總異常塊數: {sum(r.total_except_blocks for r in self.results)}")
        print(f"裸異常捕獲數: {sum(r.bare_exception_blocks for r in self.results)}")
        print(f"發現問題數: {self.total_issues}")
        print()

        # 按嚴重程度分類
        critical = len(self.get_critical_issues())
        high = len(self.get_high_issues())
        medium = len([i for r in self.results for i in r.issues if i.severity == 'medium'])
        low = len([i for r in self.results for i in r.issues if i.severity == 'low'])

        print("問題分類:")
        print(f"  🔴 嚴重 (Critical): {critical}")
        print(f"  🟠 高優先級 (High): {high}")
        print(f"  🟡 中等 (Medium): {medium}")
        print(f"  🟢 低優先級 (Low): {low}")
        print()

        # 打印有問題的文件
        problematic_files = [r for r in self.results if len(r.issues) > 0]
        if problematic_files:
            print(f"有問題的文件 ({len(problematic_files)} 個):")
            for result in sorted(problematic_files, key=lambda r: len(r.issues), reverse=True):
                print(f"  - {result.file_path}: {len(result.issues)} 個問題")
            print()

        print("="*80)

    def print_detailed_report(self) -> None:
        """打印詳細報告"""
        self.print_summary()

        if self.total_issues == 0:
            print("\n✓ 沒有發現異常處理問題！")
            return

        print("\n詳細問題報告:")
        print("-" * 80)

        for result in sorted(self.results, key=lambda r: len(r.issues), reverse=True):
            if not result.issues:
                continue

            print(f"\n文件: {result.file_path}")
            print(f"  異常塊: {result.total_except_blocks}, 裸異常: {result.bare_exception_blocks}")
            print(f"  問題數: {len(result.issues)}\n")

            for issue in result.issues:
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(issue.severity, '')

                print(f"  {severity_icon} 行 {issue.line_number}: {issue.exception_type}")
                print(f"      建議: {issue.suggestion}")

                if not issue.has_logging:
                    print(f"      ⚠️  缺少錯誤日誌")

                if not issue.has_context:
                    print(f"      ⚠️  缺少上下文信息")

        print("\n" + "="*80)

    def generate_fix_suggestions(self) -> Dict[str, List[str]]:
        """
        生成修復建議

        Returns:
            Dict[str, List[str]]: 按文件分組的修復建議
        """
        suggestions = {}

        for result in self.results:
            if not result.issues:
                continue

            file_suggestions = []
            for issue in result.issues:
                file_suggestions.append(f"行 {issue.line_number}: {issue.suggestion}")

            if file_suggestions:
                suggestions[result.file_path] = file_suggestions

        return suggestions


class ExceptionVisitor(ast.NodeVisitor):
    """AST 訪問器，用於檢測異常處理問題"""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.lines = source_code.split('\n')
        self.total_except_blocks = 0
        self.bare_exception_blocks = 0
        self.issues: List[ExceptionHandlerIssue] = []

    def visit_Try(self, node: ast.Try) -> None:
        """訪問 try 塊"""
        self.total_except_blocks += len(node.handlers)

        for handler in node.handlers:
            self.analyze_exception_handler(handler)

        self.generic_visit(node)

    def analyze_exception_handler(self, handler: ast.ExceptHandler) -> None:
        """分析異常處理器"""
        line_number = handler.lineno

        # 檢查異常類型
        if handler.type is None:
            # 裸 except: (最嚴重)
            exception_type = "bare except:"
            severity = "critical"
            suggestion = "使用具體的異常類型，如 except (ValueError, TypeError) as e:"
        elif isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
            # except Exception: (高優先級)
            exception_type = "except Exception:"
            severity = "high"
            suggestion = "使用更具體的異常類型，如 except (ValueError, KeyError, IOError) as e:"
        else:
            # 其他異常類型（正常）
            return

        self.bare_exception_blocks += 1

        # 檢查是否有日誌記錄
        has_logging = self._has_logging(handler)

        # 檢查是否有上下文信息（異常變量）
        has_context = handler.name is not None

        # 如果沒有日誌記錄，提高嚴重程度
        if not has_logging:
            if severity == "high":
                severity = "critical"
            suggestion += " 並添加錯誤日誌，如 logger.error(f'Error: {e}', exc_info=True)"

        # 如果沒有上下文信息，添加建議
        if not has_context:
            suggestion += " 並捕獲異常對象，如 except Exception as e:"

        issue = ExceptionHandlerIssue(
            file_path=self.file_path,
            line_number=line_number,
            exception_type=exception_type,
            has_logging=has_logging,
            has_context=has_context,
            suggestion=suggestion,
            severity=severity
        )

        self.issues.append(issue)

    def _has_logging(self, handler: ast.ExceptHandler) -> bool:
        """
        檢查異常處理器中是否有日誌記錄

        Args:
            handler: 異常處理器

        Returns:
            bool: 是否有日誌記錄
        """
        # 查找 logging 調用
        for node in ast.walk(handler):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # 檢查 logger.error, logger.warning 等
                    if node.func.attr in ['error', 'warning', 'exception', 'critical', 'info', 'debug']:
                        return True
                elif isinstance(node.func, ast.Name):
                    # 檢查 print 語句（雖然不推薦，但比沒有好）
                    if node.func.id == 'print':
                        return True
        return False


def analyze_exception_handling(project_root: str, directory: Optional[str] = None) -> ExceptionHandlerAnalyzer:
    """
    分析異常處理（便捷函數）

    Args:
        project_root: 項目根目錄
        directory: 要分析的目錄，如果為 None 則分析整個項目

    Returns:
        ExceptionHandlerAnalyzer: 分析器實例
    """
    analyzer = ExceptionHandlerAnalyzer(project_root)

    if directory is None:
        directory = os.path.join(project_root, "apps/backend/src")

    analyzer.analyze_directory(directory)

    return analyzer


if __name__ == "__main__":
    # 測試異常處理分析器
    logging.basicConfig(level=logging.INFO)

    project_root = "/home/cat/桌面/Unified-AI-Project"
    analyzer = analyze_exception_handling(project_root)

    # 打印摘要
    analyzer.print_summary()

    # 打印詳細報告
    if analyzer.total_issues > 0:
        print("\n是否查看詳細報告? [y/N]: ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                analyzer.print_detailed_report()
        except (EOFError, KeyboardInterrupt):
            pass

    # 生成修復建議
    suggestions = analyzer.generate_fix_suggestions()
    if suggestions:
        print("\n" + "="*80)
        print("修復建議")
        print("="*80 + "\n")

        for file_path, file_suggestions in suggestions.items():
            print(f"文件: {file_path}")
            for suggestion in file_suggestions:
                print(f"  - {suggestion}")
            print()

        print("="*80)
        print(f"\n總計: {len(suggestions)} 個文件需要修復")
        print("請手動檢查並修復這些問題")